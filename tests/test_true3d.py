from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "styles" / "monarch-face-chaos" / "true3d"
spec = importlib.util.spec_from_file_location("wf04_3d_review_gate", SOURCE / "review_gate.py")
assert spec and spec.loader
review_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review_gate)


class True3DReviewTests(unittest.TestCase):
    def test_official_canonical_geometry_has_pinned_hash(self) -> None:
        data = (SOURCE / "canonical_face_model.obj").read_bytes()
        blob = b"blob " + str(len(data)).encode() + b"\0" + data
        self.assertEqual(hashlib.sha1(blob).hexdigest(), "0e666d1c4e75949d1639c2bcf347a38da4834164")
        self.assertEqual(sum(l.startswith(b"v ") for l in data.splitlines()), 468)
        self.assertEqual(sum(l.startswith(b"f ") for l in data.splitlines()), 898)

    def test_missing_model_cannot_be_released(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            result = review_gate.check(Path(d), None)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["checks"]["head_is_3d_geometry"])
        self.assertFalse(result["checks"]["explicit_user_review_current_mesh"])

    def test_structural_pass_is_not_user_visual_approval(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            face = p / "monarch_face_v5.obj"
            # Synthetic closed-depth geometry -- not the private character model.
            face.write_text("".join(f"v {i/1000:.3f} {i/4000:.3f} 0\n" for i in range(468))
                            + "f 1 2 3\n" * 898)
            digest = hashlib.sha256(face.read_bytes()).hexdigest()
            (p / "model_manifest.json").write_text(json.dumps({
                "mesh_sha256": digest, "vertices": 468, "triangles": 898,
            }))
            (p / "monarch_face_v5_albedo.png").write_bytes(b"stand-in")
            for name in ("coat", "shirt", "lapels", "hair_front", "hair_back", "skin"):
                (p / f"{name}.obj").write_text("v 0 0 0\n")
            rejected = review_gate.check(p, None)
            self.assertTrue(all(v for k, v in rejected["checks"].items()
                                if k != "explicit_user_review_current_mesh"))
            self.assertEqual(rejected["status"], "BLOCKED")

            review = p / "review.json"
            review.write_text(json.dumps({
                "approved_by_user": True,
                "face_mesh_sha256": "incorrect-mesh",
                **{k: True for k in review_gate.REQUIRED_REVIEW},
            }))
            self.assertEqual(review_gate.check(p, review)["status"], "BLOCKED")
            content = json.loads(review.read_text())
            content["face_mesh_sha256"] = digest
            content["cinematic_visual_quality"] = False
            review.write_text(json.dumps(content))
            self.assertEqual(review_gate.check(p, review)["status"], "BLOCKED")
            content["cinematic_visual_quality"] = True
            review.write_text(json.dumps(content))
            self.assertEqual(review_gate.check(p, review)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
