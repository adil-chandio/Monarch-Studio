#!/usr/bin/env python3
"""
Builds one small contact sheet from the reference so a human/agent can *see* the
structure without shipping 1300 frames around.

argv[1] = reference video
argv[2] = output jpeg path
argv[3] = start seconds (default 0)
argv[4] = end seconds   (default whole file)
argv[5] = grid, default 4x3

Every tile is time-stamped, so cuts can be read straight off the sheet.
"""
import json
import os
import subprocess
import sys

SRC = sys.argv[1]
OUT = sys.argv[2]
T0 = sys.argv[3] if len(sys.argv) > 3 else "0"
T1 = sys.argv[4] if len(sys.argv) > 4 else ""
GRID = sys.argv[5] if len(sys.argv) > 5 else "4x3"
cols, rows = (int(x) for x in GRID.split("x"))
tiles = cols * rows


def probe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


dur = probe_dur(SRC)
t0 = float(T0)
t1 = float(T1) if T1 else dur
span = max(0.4, t1 - t0)
tw, th = 240, 426          # per tile; sheet = 960x1278 for 4x3

vf = (
    "trim=start=%.3f:end=%.3f,setpts=PTS-STARTPTS," % (t0, t1)
    + "fps=%.4f," % (tiles / span)
    + "scale=%d:%d," % (tw, th)
    + "drawtext=text='%{pts\\:hms}':x=8:y=8:fontsize=22:fontcolor=white:"
      "box=1:boxcolor=black@0.6:boxborderw=6,"
    + "tile=%s" % GRID
)
cmd = ["ffmpeg", "-v", "error", "-y", "-i", SRC, "-vf", vf,
       "-frames:v", "1", "-q:v", "6", OUT]
r = subprocess.run(cmd, capture_output=True, text=True)
info = {"out": OUT, "bytes": os.path.getsize(OUT) if os.path.exists(OUT) else 0,
        "t0": t0, "t1": t1, "grid": GRID, "ok": r.returncode == 0,
        "err": (r.stderr or "")[-300:]}
print(json.dumps(info))
