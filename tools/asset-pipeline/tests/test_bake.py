import json
import os
import unittest
from pathlib import Path

import numpy as np

from valis_asset import bake as B
from valis_asset.glb import Glb, GlbError

GLB = os.environ.get("VALIS_GLB", "")
OVERRIDES = Path(__file__).resolve().parents[1] / "clip_overrides.json"


def axis_quat(deg, axis=(0, 0, 1)):
    h = np.radians(deg) / 2
    a = np.array(axis, dtype=float)
    return np.array([*(a * np.sin(h)), np.cos(h)])


class QuatMath(unittest.TestCase):
    def test_quantise_roundtrip_is_sub_tenth_degree(self):
        rng = np.random.default_rng(1)
        q = B._normalize(rng.normal(size=(500, 4)))
        back = B.dequantize_quats(B.quantize_quats(q))
        self.assertLess(float(B.angle_between(q, back).max()), 0.1)

    def test_quantise_canonical_sign(self):
        q = B.quantize_quats(np.array([[0.0, 0.0, 0.0, -1.0]]))
        self.assertGreaterEqual(int(q[0, 3]), 0)

    def test_slerp_midpoint(self):
        times = np.array([0.0, 1.0])
        q = np.stack([axis_quat(0), axis_quat(90)])
        mid = B.slerp_sample(times, q, np.array([0.5]))[0]
        self.assertAlmostEqual(float(B.angle_between(mid, axis_quat(45))), 0.0, places=3)

    def test_slerp_takes_short_path(self):
        times = np.array([0.0, 1.0])
        q = np.stack([axis_quat(10), -axis_quat(30)])  # same rotation as +30 deg
        mid = B.slerp_sample(times, q, np.array([0.5]))[0]
        self.assertAlmostEqual(float(B.angle_between(mid, axis_quat(20))), 0.0, places=3)

    def test_slerp_clamps_outside_range(self):
        times = np.array([0.0, 1.0])
        q = np.stack([axis_quat(0), axis_quat(90)])
        out = B.slerp_sample(times, q, np.array([-1.0, 2.0]))
        self.assertAlmostEqual(float(B.angle_between(out[1], axis_quat(90))), 0.0, places=3)
        self.assertAlmostEqual(float(B.angle_between(out[0], axis_quat(0))), 0.0, places=3)


class Grouping(unittest.TestCase):
    def test_every_known_target_has_a_group(self):
        expect = {
            "eyeBlink_L": "BLINK", "eyeLookUp_R": "GAZE", "eyeSquint_L": "LID", "eyeWide_R": "LID",
            "browInnerUp_L": "BROW", "mouthPucker": "MOUTH", "viseme_aa": "VISEME",
        }
        for name, g in expect.items():
            self.assertEqual(B.morph_group(name), g)

    def test_unknown_target_fails_loudly(self):
        with self.assertRaises(GlbError):
            B.morph_group("cheekPuff")

    def test_float_joint_detection(self):
        for n in ("upperLeg_L", "foot_R", "ear_2_L", "tail_3"):
            self.assertTrue(B._is_float_joint(n))
        for n in ("head", "hand_L", "chest"):
            self.assertFalse(B._is_float_joint(n))


class GlbReader(unittest.TestCase):
    def test_rejects_garbage(self):
        with self.assertRaises(GlbError):
            Glb(b"not a glb at all, definitely")


@unittest.skipUnless(GLB and Path(GLB).exists(), "set VALIS_GLB to the real VALIS_rigged.glb")
class RealAsset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.glb = Glb.load(GLB)
        cls.index, cls.payload = B.bake(cls.glb, B.BakeConfig(overrides=json.loads(OVERRIDES.read_text())))

    def test_rig_contract(self):
        self.assertEqual(len(self.index["joints"]), 27)
        self.assertEqual({k: len(v) for k, v in self.index["morphs"].items()}, {"VALIS_body": 26, "VALIS_mouth": 6})
        for required in ("root", "hips", "head", "neck", "tail_3", "ear_2_R", "hand_L"):
            self.assertIn(required, self.index["joints"])

    def test_clip_inventory(self):
        self.assertEqual(len(self.index["clips"]), 48)
        names = {c["name"] for c in self.index["clips"]}
        for n in ("idle", "wave_right", "nod", "tail_wag", "ear_twitch", "expression_happy"):
            self.assertIn(n, names)

    def test_loop_count_matches_measurement(self):
        self.assertEqual(sum(c["loopable"] for c in self.index["clips"]), 14)

    def test_float_joints_never_in_default_masks(self):
        joints = self.index["joints"]
        for c in self.index["clips"]:
            if c["name"] in ("tail_wag", "ear_twitch"):
                continue
            for j in c["meaningfulMask"]:
                self.assertFalse(B._is_float_joint(joints[j]), (c["name"], joints[j]))

    def test_overrides_apply(self):
        c = next(c for c in self.index["clips"] if c["name"] == "tail_wag")
        self.assertEqual([self.index["joints"][j] for j in c["meaningfulMask"]], ["tail_1", "tail_2", "tail_3"])

    def test_payload_offsets_in_bounds_and_aligned(self):
        for c in self.index["clips"]:
            for j in c["joints"]:
                for k in ("rotation", "translation", "scale"):
                    if k in j:
                        self.assertEqual(j[k]["offset"] % 4, 0)
                        self.assertLessEqual(j[k]["offset"], len(self.payload))

    def test_rotation_decode_matches_source(self):
        c = next(c for c in self.index["clips"] if c["name"] == "wave_right")
        j = max(c["joints"], key=lambda e: e["rangeDeg"])
        q16 = B.read_array(self.index, self.payload, j["rotation"], np.int16).reshape(-1, 4)
        self.assertEqual(len(q16), c["frames"])
        back = B.dequantize_quats(q16)
        self.assertGreater(float(B.angle_between(back, back[0:1]).max()), 3.0)

    def test_clip_morph_meshes_are_names_declared_in_index(self):
        # The Android runtime resolves clip morph tracks by mesh *name*; a numeric node index broke loading once.
        declared = set(self.index["morphs"])
        for c in self.index["clips"]:
            for m in c["morphs"]:
                self.assertIsInstance(m["mesh"], str, c["name"])
                self.assertIn(m["mesh"], declared, c["name"])

    def test_bake_is_deterministic(self):
        i2, p2 = B.bake(self.glb, B.BakeConfig(overrides=json.loads(OVERRIDES.read_text())))
        self.assertEqual(p2, self.payload)
        self.assertEqual(json.dumps(i2), json.dumps(self.index))


if __name__ == "__main__":
    unittest.main()
