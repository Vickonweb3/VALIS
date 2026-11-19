"""Bake VALIS clips into `valis_anim.v1` (json index + binary payload).

Why this exists (measured on VALIS_rigged.glb): every clip keys the full rig,
so a clip cannot be layered as-is. The bake resamples to a fixed rate, records
which joints genuinely move (the meaningful mask), splits face morph weights
into channel groups, and flags which clips loop seamlessly.
"""
from __future__ import annotations

import json
import math
import re
import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import FORMAT
from .glb import Animation, Channel, Glb, GlbError

FPS = 30
LOOP_ROT_TOL_DEG = 5.0
LOOP_POS_TOL = 0.01
MASK_ROT_MIN_DEG = 3.0
SCALE_MIN_DEV = 0.02
TRANS_MIN_RANGE = 0.001
MORPH_MIN_RANGE = 0.02

# Joints that float along in every full-rig take; excluded from masks unless overridden.
FLOAT_PATTERNS = (r"^(upperLeg|lowerLeg|foot)_[LR]$", r"^ear_\d_[LR]$", r"^tail_\d$")

GROUPS: tuple[tuple[str, str], ...] = (
    (r"^eyeBlink_", "BLINK"),
    (r"^eyeLook", "GAZE"),
    (r"^eye(Squint|Wide)_", "LID"),
    (r"^brow", "BROW"),
    (r"^mouth", "MOUTH"),
    (r"^viseme_", "VISEME"),
)


def morph_group(name: str) -> str:
    for pat, group in GROUPS:
        if re.match(pat, name):
            return group
    raise GlbError(f"morph target '{name}' has no channel group")


# --- quaternion helpers -------------------------------------------------
def _normalize(q: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(q, axis=-1, keepdims=True)
    return q / np.where(n == 0, 1, n)


def slerp_sample(times: np.ndarray, q: np.ndarray, t: np.ndarray, step: bool = False) -> np.ndarray:
    """Sample quaternion keys (xyzw) at times t. Handles hemisphere continuity."""
    q = _normalize(q.astype(np.float64))
    for i in range(1, len(q)):
        if np.dot(q[i], q[i - 1]) < 0:
            q[i] = -q[i]
    idx = np.clip(np.searchsorted(times, t, side="right") - 1, 0, len(times) - 1)
    if step or len(times) == 1:
        return q[idx]
    nxt = np.minimum(idx + 1, len(times) - 1)
    span = times[nxt] - times[idx]
    a = np.where(span > 0, (t - times[idx]) / np.where(span > 0, span, 1), 0.0)[:, None]
    a = np.clip(a, 0, 1)
    q0, q1 = q[idx], q[nxt]
    dot = np.clip(np.sum(q0 * q1, axis=1, keepdims=True), -1.0, 1.0)
    theta = np.arccos(dot)
    s = np.sin(theta)
    near = s < 1e-6
    w0 = np.where(near, 1 - a, np.sin((1 - a) * theta) / np.where(near, 1, s))
    w1 = np.where(near, a, np.sin(a * theta) / np.where(near, 1, s))
    return _normalize(w0 * q0 + w1 * q1)


def lerp_sample(times: np.ndarray, v: np.ndarray, t: np.ndarray, step: bool = False) -> np.ndarray:
    idx = np.clip(np.searchsorted(times, t, side="right") - 1, 0, len(times) - 1)
    if step or len(times) == 1:
        return v[idx].astype(np.float64)
    nxt = np.minimum(idx + 1, len(times) - 1)
    span = times[nxt] - times[idx]
    a = np.clip(np.where(span > 0, (t - times[idx]) / np.where(span > 0, span, 1), 0.0), 0, 1)[:, None]
    return v[idx] * (1 - a) + v[nxt] * a


def angle_between(q0: np.ndarray, q1: np.ndarray) -> np.ndarray:
    """Angle in degrees between rotations (arrays of xyzw), sign-agnostic."""
    d = np.abs(np.clip(np.sum(q0 * q1, axis=-1), -1.0, 1.0))
    return np.degrees(2.0 * np.arccos(d))


def quantize_quats(q: np.ndarray) -> np.ndarray:
    """float (F,4) xyzw -> int16, canonical sign (w>=0)."""
    q = _normalize(q.copy())
    q[q[:, 3] < 0] *= -1
    return np.round(q * 32767.0).astype(np.int16)


def dequantize_quats(q16: np.ndarray) -> np.ndarray:
    return _normalize(q16.astype(np.float64) / 32767.0)


# --- baking -------------------------------------------------------------
@dataclass
class BakeConfig:
    fps: int = FPS
    overrides: dict | None = None


def _is_float_joint(name: str) -> bool:
    return any(re.match(p, name) for p in FLOAT_PATTERNS)


def bake(glb: Glb, cfg: BakeConfig | None = None) -> tuple[dict, bytes]:
    cfg = cfg or BakeConfig()
    joints = glb.joint_nodes()
    jname = [glb.node_name(n) for n in joints]
    jindex = {n: i for i, n in enumerate(joints)}
    morphs = glb.morph_names()
    mesh_nodes = sorted(morphs)
    payload = bytearray()

    def put(arr: np.ndarray) -> dict:
        while len(payload) % 4:
            payload.append(0)
        off = len(payload)
        payload.extend(arr.tobytes(order="C"))
        return {"offset": off, "count": int(arr.size)}

    clips = []
    for anim in glb.animations():
        clips.append(_bake_clip(anim, joints, jname, jindex, morphs, cfg, put))

    index = {
        "format": FORMAT,
        "fps": cfg.fps,
        "joints": jname,
        "morphs": {glb.node_name(n): morphs[n] for n in mesh_nodes},
        "groups": sorted({g for _, g in GROUPS}),
        "encoding": {
            "rotation": "int16 xyzw /32767, w>=0, renormalise on decode",
            "translation": "float32 xyz per frame (only joints that move)",
            "scale": "float32 xyz per frame (only joints deviating >= %.2f)" % SCALE_MIN_DEV,
            "morph": "uint16 weight /65535 per frame per kept target",
        },
        "clips": clips,
    }
    return index, bytes(payload)


def _bake_clip(anim: Animation, joints, jname, jindex, morphs, cfg, put) -> dict:
    dur = anim.duration
    frames = max(2, int(round(dur * cfg.fps)) + 1)
    t = np.arange(frames, dtype=np.float64) / cfg.fps
    t = np.minimum(t, dur if dur > 0 else 0.0)

    rot: dict[int, np.ndarray] = {}
    pos: dict[int, np.ndarray] = {}
    scl: dict[int, np.ndarray] = {}
    wts: dict[int, np.ndarray] = {}
    for ch in anim.channels:
        step = ch.interpolation == "STEP"
        if ch.path == "rotation" and ch.node in jindex:
            rot[ch.node] = slerp_sample(ch.times, ch.values, t, step)
        elif ch.path == "translation" and ch.node in jindex:
            pos[ch.node] = lerp_sample(ch.times, ch.values, t, step)
        elif ch.path == "scale" and ch.node in jindex:
            scl[ch.node] = lerp_sample(ch.times, ch.values, t, step)
        elif ch.path == "weights" and ch.node in morphs:
            wts[ch.node] = lerp_sample(ch.times, ch.values, t, step)

    joint_out, moving, max_loop_rot, max_loop_pos = [], [], 0.0, 0.0
    for n, q in sorted(rot.items(), key=lambda kv: jindex[kv[0]]):
        ji = jindex[n]
        rng = float(np.max(angle_between(q, q[0:1])))
        max_loop_rot = max(max_loop_rot, float(angle_between(q[-1], q[0])))
        entry = {"joint": ji, "rotation": put(quantize_quats(q)), "rangeDeg": round(rng, 3)}
        if n in pos:
            p = pos[n]
            max_loop_pos = max(max_loop_pos, float(np.linalg.norm(p[-1] - p[0])))
            if float(np.ptp(p, axis=0).max()) >= TRANS_MIN_RANGE:
                entry["translation"] = put(p.astype(np.float32))
        if n in scl and float(np.abs(scl[n] - 1.0).max()) >= SCALE_MIN_DEV:
            entry["scale"] = put(scl[n].astype(np.float32))
        joint_out.append(entry)
        if rng >= MASK_ROT_MIN_DEG:
            moving.append(ji)

    morph_out = []
    for n in sorted(wts):
        names = morphs[n]
        w = wts[n]
        by_group: dict[str, list[int]] = {}
        for ti, name in enumerate(names):
            if float(np.ptp(w[:, ti])) >= MORPH_MIN_RANGE or float(w[:, ti].max()) >= MORPH_MIN_RANGE:
                by_group.setdefault(morph_group(name), []).append(ti)
        for group in sorted(by_group):
            cols = by_group[group]
            q = np.round(np.clip(w[:, cols], 0, 1) * 65535).astype(np.uint16)
            morph_out.append({"mesh": n, "group": group, "targets": cols, "weights": put(q)})

    meaningful = [j for j in moving if not _is_float_joint(jname[j])]
    clip = {
        "name": anim.name,
        "duration": round(dur, 4),
        "frames": frames,
        "loopable": bool(max_loop_rot <= LOOP_ROT_TOL_DEG and max_loop_pos <= LOOP_POS_TOL),
        "loopErrorDeg": round(max_loop_rot, 3),
        "movingJoints": moving,
        "meaningfulMask": meaningful,
        "joints": joint_out,
        "morphs": morph_out,
    }
    ov = (cfg.overrides or {}).get(anim.name)
    if ov:
        if "mask" in ov:
            clip["meaningfulMask"] = [jname.index(j) for j in ov["mask"]]
        clip["tags"] = ov.get("tags", [])
    return clip


def write(index: dict, payload: bytes, outdir: str | Path) -> tuple[Path, Path]:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    jp, bp = out / f"{FORMAT}.json", out / f"{FORMAT}.bin"
    jp.write_text(json.dumps(index, indent=1, sort_keys=False) + "\n")
    bp.write_bytes(payload)
    return jp, bp


def read_array(index: dict, payload: bytes, ref: dict, dtype) -> np.ndarray:
    return np.frombuffer(payload, dtype=dtype, count=ref["count"], offset=ref["offset"])
