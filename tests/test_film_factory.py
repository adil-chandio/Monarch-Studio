"""Tests for tools/film_factory.py — srt/kit/card parts (no GPU, no network)."""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import film_factory as ff  # noqa: E402

SPEC = ROOT / "studio/films/stick-i2v/film/film_clips.json"


def small_spec() -> dict:
    spec = json.loads(SPEC.read_text())
    spec["clips"] = "/tmp/none"
    spec["voice_dir"] = str(ff.VOICE)
    spec["scenes"] = spec["scenes"][:3]
    return spec


class SrtTimeTest(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(ff.srt_time(0), "00:00:00,000")
        self.assertEqual(ff.srt_time(3.5), "00:00:03,500")
        self.assertEqual(ff.srt_time(61.25), "00:01:01,250")
        self.assertEqual(ff.srt_time(3725.004), "01:02:05,004")


class SubtitlesTest(unittest.TestCase):
    def test_captions_and_timing(self):
        spec = small_spec()
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "subs.srt"
            ff.subtitles(spec, out)
            text = out.read_text(encoding="utf-8")
        self.assertIn("1\n00:00:00,000 --> 00:00:02,950", text)
        self.assertIn(spec["scenes"][0]["caption"], text)
        # teesra scene pehle do ke baad shuru hota hai
        start = sum(float(s.get("seconds") or 3.0) for s in spec["scenes"][:2])
        self.assertIn(ff.srt_time(start).rsplit(",", 1)[0], text)
        self.assertEqual(text.count("-->"), 3)


class KitTest(unittest.TestCase):
    def test_kit_markdown(self):
        spec = small_spec()
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "kit.md"
            ff.kit(out, "Powerful Personality", spec,
                   {"teaser_11s.mp4": "8.8 MB", "cover.jpg": "/tmp/cover.jpg"})
            text = out.read_text(encoding="utf-8")
        self.assertIn("# Powerful Personality", text)
        self.assertIn("Scenes:** 3", text)
        self.assertIn("teaser_11s.mp4", text)
        self.assertIn("Beat sheet", text)
        self.assertIn(spec["scenes"][0]["caption"], text)


class WrapTest(unittest.TestCase):
    def test_wrap_respects_width(self):
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (10, 10))
        draw = ImageDraw.Draw(img)
        font = ff._font("Montserrat-VF.ttf", 40)
        lines = ff._wrap(draw, "POWERFUL PERSONALITY FOR EVERY SINGLE DAY", font, 700)
        self.assertGreaterEqual(len(lines), 2)
        for line in lines:
            self.assertLessEqual(draw.textlength(line, font=font), 700 + 1)


if __name__ == "__main__":
    unittest.main()
