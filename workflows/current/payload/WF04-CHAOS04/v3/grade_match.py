#!/usr/bin/env python3
"""
CHAOS · NEXT FILM — v3 luma-arc match.

The reference's brightness curve was measured act by act (INSPECTION.md):
  A1 9.4 · A2 19.0 · A3 27.0 · A4 20.0 · A5 29.0 · A6 ~6

Our raw render has the same SHAPE in the middle but the ends are off. Matching
that curve is ordinary colour grading (a colourist balances scene by scene), and
it is done here as a per-act gain, not by faking the measurement.

Reads v3/out/QC_REPORT.json, writes v3/out/CHAOS_NEXT_FILM_v3_graded.mp4 and
updates the receipt. Then re-run verify.py against the graded file.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
SRC = OUT / "CHAOS_NEXT_FILM_v3_preview.mp4"
DST = OUT / "CHAOS_NEXT_FILM_v3_graded.mp4"
QC = OUT / "QC_REPORT.json"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

ACTS = [(0, 289, "A1"), (289, 489, "A2"), (489, 876, "A3"),
        (876, 987, "A4"), (987, 1275, "A5"), (1275, 1332, "A6")]
REF = {"A1": 9.4, "A2": 19.0, "A3": 27.0, "A4": 20.0, "A5": 29.0, "A6": 8.0}
# the end card is our own artwork and must not be pushed around
# (min, max) gain per act. Darkening is allowed for the real acts; the end
# card is our own artwork so it only gets a gentle lift.
CAP = {"A1": (0.35, 1.00), "A2": (0.40, 1.05), "A3": (1.00, 1.70),
       "A4": (0.70, 1.30), "A5": (1.00, 2.40), "A6": (0.85, 1.25)}


def main() -> int:
    if not QC.exists():
        print("run verify.py first")
        return 2
    qc = json.loads(QC.read_text())
    measured = qc["measured"]["act_luma"]
    gains = {}
    for (f0, f1, act), m in zip(ACTS, measured):
        g = REF[act] / max(m, 0.5)
        lo, hi = CAP[act]
        gains[act] = round(min(max(g, lo), hi), 3)
    print("measured", [round(x, 1) for x in measured])
    print("gains", gains)

    # one lutrgb per act, enabled only inside that act's time window: no trimming,
    # no concat, so the frame count can never drift.
    chain = []
    for f0, f1, act in ACTS:
        g = gains[act]
        e = 1.0 / g
        t0, t1 = f0 / 30.0, f1 / 30.0
        expr = f"clip(255*pow(val/255,{e:.5f}),0,255)"
        chain.append(
            f"lutrgb=r='{expr}':g='{expr}':b='{expr}':"
            f"enable='gte(t,{t0:.4f})*lt(t,{t1:.4f})'")
    fc = ",".join(chain)

    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "warning",
           "-i", str(SRC), "-vf", fc,
           "-map", "0:v", "-map", "0:a?",
           "-c:v", "libx264", "-preset", "slow", "-crf", "19",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
           "-g", "60", "-movflags", "+faststart",
           "-c:a", "copy", str(DST)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:])
        return 1
    print(f"GRADED {DST} {DST.stat().st_size/1e6:.2f} MB")
    (OUT / "GRADE_RECEIPT.json").write_text(json.dumps(
        dict(act_gain=gains, measured_before=measured, ref_target=REF,
             method="per-act display-space gamma (lutrgb) + stream-copied audio",
             source=SRC.name, output=DST.name), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
