"""Minimal, dependency-light GLB 2.0 reader (numpy only).

Only what the baker needs: node tree, skins, mesh morph target names and
animation samplers. It validates structure and raises GlbError on anything
unexpected instead of guessing.
"""
from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_COMPONENT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
_TYPE_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


class GlbError(ValueError):
    pass


@dataclass
class Channel:
    node: int
    path: str  # translation | rotation | scale | weights
    times: np.ndarray
    values: np.ndarray
    interpolation: str


@dataclass
class Animation:
    name: str
    channels: list[Channel] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return max((float(c.times[-1]) for c in self.channels if len(c.times)), default=0.0)


class Glb:
    def __init__(self, data: bytes):
        if len(data) < 20 or data[:4] != b"glTF":
            raise GlbError("not a GLB file")
        version, length = struct.unpack_from("<II", data, 4)
        if version != 2 or length > len(data):
            raise GlbError("unsupported or truncated GLB")
        off, self.doc, self.bin = 12, None, b""
        while off + 8 <= length:
            clen, ctype = struct.unpack_from("<II", data, off)
            chunk = data[off + 8 : off + 8 + clen]
            if ctype == 0x4E4F534A:
                self.doc = json.loads(chunk)
            elif ctype == 0x004E4942 and not self.bin:
                self.bin = chunk
            off += 8 + clen
        if self.doc is None:
            raise GlbError("missing JSON chunk")

    @classmethod
    def load(cls, path: str | Path) -> "Glb":
        return cls(Path(path).read_bytes())

    def accessor(self, index: int) -> np.ndarray:
        a = self.doc["accessors"][index]
        if "bufferView" not in a:
            raise GlbError(f"accessor {index} has no bufferView (sparse not supported)")
        if a.get("sparse"):
            raise GlbError(f"accessor {index} is sparse")
        bv = self.doc["bufferViews"][a["bufferView"]]
        dt = np.dtype(_COMPONENT[a["componentType"]])
        n = _TYPE_COUNT[a["type"]]
        stride = bv.get("byteStride", 0)
        base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        count = a["count"]
        if stride and stride != dt.itemsize * n:
            raw = np.frombuffer(self.bin, dtype=np.uint8, count=stride * count, offset=base).reshape(count, stride)
            out = np.ascontiguousarray(raw[:, : dt.itemsize * n]).view(dt).reshape(count, n)
        else:
            out = np.frombuffer(self.bin, dtype=dt, count=count * n, offset=base).reshape(count, n)
        if a.get("normalized"):
            info = np.iinfo(dt)
            out = np.maximum(out.astype(np.float32) / float(info.max), -1.0)
        return out.astype(np.float32) if dt != np.float32 else out.copy()

    # --- rig -----------------------------------------------------------
    def joint_nodes(self, skin: int = 0) -> list[int]:
        return list(self.doc["skins"][skin]["joints"])

    def node_name(self, i: int) -> str:
        return self.doc["nodes"][i].get("name", f"node{i}")

    def parents(self) -> dict[int, int]:
        p: dict[int, int] = {}
        for i, n in enumerate(self.doc["nodes"]):
            for c in n.get("children", []):
                p[c] = i
        return p

    def morph_names(self) -> dict[int, list[str]]:
        """node index -> morph target names, for nodes whose mesh has targets."""
        out: dict[int, list[str]] = {}
        for i, n in enumerate(self.doc["nodes"]):
            if "mesh" not in n:
                continue
            mesh = self.doc["meshes"][n["mesh"]]
            names = (mesh.get("extras") or {}).get("targetNames")
            if names is None:
                names = (n.get("extras") or {}).get("targetNames")
            if names:
                out[i] = list(names)
        return out

    def animations(self) -> list[Animation]:
        result = []
        for ai, a in enumerate(self.doc.get("animations", [])):
            anim = Animation(a.get("name", f"anim{ai}"))
            for ch in a["channels"]:
                s = a["samplers"][ch["sampler"]]
                interp = s.get("interpolation", "LINEAR")
                if interp not in ("LINEAR", "STEP"):
                    raise GlbError(f"{anim.name}: interpolation {interp} not supported")
                t = self.accessor(s["input"]).reshape(-1)
                v = self.accessor(s["output"])
                path = ch["target"]["path"]
                node = ch["target"]["node"]
                if path == "weights":
                    v = v.reshape(len(t), -1)
                anim.channels.append(Channel(node, path, t, v, interp))
            result.append(anim)
        return result
