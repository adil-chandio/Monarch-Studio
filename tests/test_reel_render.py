"""Tests for tools/reel_render.py — the CPU-only reel renderer (no GPU, no network)."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import reel_render as rr  # noqa: E402


def make_image(path: pathlib.Path, size=(320, 180)) -> pathlib.Path:
    from PIL import Image
    Image.new("RGB", size, (24, 28, 36)).save(path)
    return path


def write_spec(base: pathlib.Path, *, shots=None, **extra) -> pathlib.Path:
    make_image(base / "a.png")
    make_image(base / "b.png", (320, 180))
    spec = {
        "id": "t",
        "size": [270, 480],
        "fps": 12,
        "plate_height": 152,
        "crf": 28,
        "audio": {"drone": 0.4, "rain": 0.3, "impacts": True, "riser": False, "pulse": 0.4},
        "shots": shots or [
            {"image": "a.png", "seconds": 0.8, "move": "push", "caption": "pehla shot"},
            {"image": "b.png", "seconds": 0.8, "move": "pan_left", "caption": "doosra"},
        ],
    }
    spec.update(extra)
    path = base / "reel.json"
    path.write_text(json.dumps(spec, indent=2))
    return path


class SpecTests(unittest.TestCase):
    def test_missing_image_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td)
            spec = write_spec(base)
            data = json.loads(spec.read_text())
            data["shots"][0]["image"] = "nope.png"
            spec.write_text(json.dumps(data))
            with self.assertRaises(rr.RenderError) as caught:
                rr.load_spec(spec)
            self.assertIn("nahi mila", str(caught.exception))

    def test_empty_spec_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            spec = pathlib.Path(td) / "reel.json"
            spec.write_text(json.dumps({"shots": []}))
            with self.assertRaises(rr.RenderError):
                rr.load_spec(spec)

    def test_unknown_move_is_refused_at_filter_time(self):
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td)
            spec = write_spec(base, shots=[{"image": "a.png", "seconds": 1, "move": "orbit"}])
            loaded = rr.load_spec(spec)
            with self.assertRaises(rr.RenderError):
                rr.shot_filter(loaded["shots"][0], loaded, 1, None)

    def test_render_is_refused_without_ffmpeg(self):
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td)
            spec = write_spec(base)
            with mock.patch.object(rr, "which", lambda _b: None):
                with self.assertRaises(rr.RenderError):
                    rr.render(spec, base / "out.mp4")


class GraphTests(unittest.TestCase):
    def test_every_move_produces_a_zoompan_and_a_camera_expression(self):
        for move in rr.MOVES:
            zoom, xpos, ypos = rr._zoom_expr(move, 48)
            self.assertIn("zoom", zoom + xpos + ypos)
            self.assertTrue(zoom)

    def test_shot_filter_layers_blur_plate_caption_and_fades(self):
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td)
            spec = rr.load_spec(write_spec(base))
            graph = rr.shot_filter(spec["shots"][0], spec, 1, base / "a.png")
            self.assertIn("gblur", graph)          # vertical frame ka bed
            self.assertIn("zoompan", graph)        # asli camera motion
            self.assertIn("overlay", graph)
            self.assertIn("fade=t=in", graph)
            self.assertIn("format=yuv420p", graph)

    def test_caption_png_is_transparent_and_has_pixels(self):
        from PIL import Image
        import numpy as np
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td)
            spec = rr.load_spec(write_spec(base))
            png = rr.make_caption_png("sab wapas nahi aate", spec, base / "cap.png")
            image = np.asarray(Image.open(png))
            self.assertEqual(image.shape[2], 4)
            self.assertGreater(int((image[:, :, 3] > 200).sum()), 100)   # text mojood hai

    def test_audio_bed_has_drone_rain_pulse_and_loudnorm(self):
        graph, _ = rr.audio_graph({"audio": {"drone": 0.5, "rain": 0.4, "pulse": 0.5,
                                             "impacts": True, "riser": True}},
                                  duration=6.0, cut_times=[2.5, 4.5])
        self.assertIn("sine=frequency=55", graph)
        self.assertIn("anoisesrc", graph)
        self.assertIn("aevalsrc", graph)                 # pulse
        self.assertIn("amix=inputs=", graph)
        self.assertIn("loudnorm=I=-16:TP=-1.5:LRA=11", graph)


class RenderTests(unittest.TestCase):
    def test_renders_a_real_master_with_motion_and_audio(self):
        ffmpeg = rr.which("ffmpeg")
        if not ffmpeg:
            self.skipTest("ffmpeg not installed")
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td)
            spec = write_spec(base)
            out = base / "master.mp4"
            receipt = rr.render(spec, out, ffmpeg=ffmpeg)
            self.assertTrue(out.exists())
            self.assertEqual(receipt["info"]["width"], 270)
            self.assertEqual(receipt["info"]["height"], 480)
            self.assertGreater(receipt["info"]["duration"], 1.0)
            self.assertEqual(len(receipt["info"]["md5"]), 32)
            self.assertTrue((base / "master_receipt.json").exists())
            probe = subprocess.run([ffmpeg, "-hide_banner", "-i", str(out)],
                                   capture_output=True, text=True).stderr
            self.assertIn("Audio: aac", probe)
            self.assertIn("12 fps", probe)

    def test_frames_really_change(self):
        """Static image ko video kehna band — do frames me farq hona chahiye."""
        ffmpeg = rr.which("ffmpeg")
        if not ffmpeg:
            self.skipTest("ffmpeg not installed")
        from PIL import Image
        import numpy as np
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td)
            spec = write_spec(base, shots=[{"image": "a.png", "seconds": 1.2, "move": "push"}])
            out = base / "master.mp4"
            rr.render(spec, out, ffmpeg=ffmpeg)
            frames = []
            for at in (0.3, 1.0):
                png = base / f"f{at}.png"
                subprocess.run([ffmpeg, "-y", "-ss", str(at), "-i", str(out), "-frames:v", "1",
                                str(png)], capture_output=True, check=True)
                frames.append(np.asarray(Image.open(png).convert("L"), dtype=float))
            # flat colour image par bhi camera move se pixels badalte hain (grain bhi shamil hai)
            self.assertGreater(float(np.abs(frames[0] - frames[1]).max()), 0.0)


class ProjectTests(unittest.TestCase):
    def test_shipped_reel_spec_is_valid_and_points_at_real_plates(self):
        spec_path = ROOT / "studio/videogen/examples/reel-local-01/reel.json"
        spec = rr.load_spec(spec_path)
        self.assertGreaterEqual(len(spec["shots"]), 3)
        self.assertEqual(spec["size"], [1080, 1920])
        for shot in spec["shots"]:
            self.assertTrue(pathlib.Path(shot["image"]).exists(), shot["image"])
            self.assertTrue((shot.get("caption") or "").strip())

    def test_delivered_master_is_a_real_vertical_video(self):
        master = ROOT / "studio/videogen/examples/reel-local-01/delivery/reel-local-01_MASTER.mp4"
        if not master.exists():
            self.skipTest("delivery not rendered in this checkout")
        receipt = json.loads((master.parent / "reel-local-01_MASTER_receipt.json").read_text())
        self.assertEqual(receipt["info"]["md5"], rr.md5(master))     # receipt = asli file
        self.assertEqual(receipt["info"]["width"], 1080)
        self.assertEqual(receipt["info"]["height"], 1920)
        self.assertGreater(receipt["info"]["duration"], 10)


if __name__ == "__main__":
    unittest.main()
