#!/usr/bin/env python3
"""
CHAOS · NEXT FILM — v3 assembly.

Takes the 1332 rendered frames (288x512 preview render + our own end card),
assembles them at the delivery spec and muxes our score.

Delivery spec (locked):
  1080x1920 · 30 fps · H.264 crf 19 · yuv420p · AAC 48 kHz · faststart
  audio loudness target -14.5 LUFS integrated, true peak <= -1.5 dBFS
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
RENDER = HERE / "render" / "animatic"
CARD = HERE / "card"
FRAMES = HERE / "frames"
OUT = HERE / "out"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SPEC = dict(w=1080, h=1920, fps=30, crf=19, abr="320k", i="-14.5", tp="-1.5", lra="11")


def link_frames() -> int:
    FRAMES.mkdir(parents=True, exist_ok=True)
    for f in FRAMES.glob("f_*.png"):
        f.unlink()
    n = 0
    for src_dir, lo, hi in ((RENDER, 0, 1275), (CARD, 1275, 1332)):
        for i in range(lo, hi):
            src = src_dir / f"f_{i:04d}.png"
            if not src.exists():
                continue
            (FRAMES / f"f_{i:04d}.png").symlink_to(src)
            n += 1
    return n


def main() -> int:
    n = link_frames()
    missing = [i for i in range(1332) if not (FRAMES / f"f_{i:04d}.png").exists()]
    print(f"frames linked: {n}/1332  missing={len(missing)}")
    if missing:
        print("MISSING sample:", missing[:20])
        if len(missing) > 0:
            return 2

    OUT.mkdir(parents=True, exist_ok=True)
    mp4 = OUT / "CHAOS_NEXT_FILM_v3_preview.mp4"
    vf = (
        f"scale={SPEC['w']}:{SPEC['h']}:flags=lanczos,"
        "unsharp=5:5:0.55:5:5:0.0,"
        "eq=contrast=1.05:brightness=-0.012:saturation=1.05,"
        "vignette=PI/4.6,"
        "noise=alls=5:allf=t+u,"
        "format=yuv420p"
    )
    af = (f"loudnorm=I={SPEC['i']}:TP={SPEC['tp']}:LRA={SPEC['lra']}:print_format=summary")
    cmd = [
        FFMPEG, "-y", "-hide_banner", "-loglevel", "warning",
        "-framerate", str(SPEC["fps"]), "-i", str(FRAMES / "f_%04d.png"),
        "-i", str(HERE / "score" / "score_raw.wav"),
        "-vf", vf, "-af", af,
        "-c:v", "libx264", "-preset", "slow", "-crf", str(SPEC["crf"]),
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
        "-g", "60", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", SPEC["abr"], "-ar", "48000", "-ac", "2",
        "-shortest", str(mp4),
    ]
    print("ENCODE:", " ".join(cmd[:6]), "...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stderr[-2500:] if r.stderr else "", flush=True)
    if r.returncode != 0:
        print("ENCODE_FAILED", r.returncode)
        return 1
    size = mp4.stat().st_size
    receipt = dict(
        schema_version=2, kind="wf04_chaos_v3_preview", task="WF04-3D-PLAN",
        file=mp4.name, bytes=size, spec=SPEC,
        frames=1332, duration_s=44.4,
        source_frames="288x512 Cycles CPU render (v3/chaos_scene.py) + PIL end card",
        audio="v3/score.py procedural score (no sample library, no reference audio)",
        note=("Preview assembly at delivery spec. Picture detail is limited by the "
              "288x512 render grid; the 1080 render is the same scene at full res."),
    )
    (OUT / "PREVIEW_RECEIPT.json").write_text(json.dumps(receipt, indent=1))
    print(f"ASSEMBLED {mp4}  {size/1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
