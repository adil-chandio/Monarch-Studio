#!/usr/bin/env python3
"""
CHAOS 04 — beat map. Turns the reference into numbers you can cut against.

argv[1] = reference video
argv[2] = output json path
argv[3] = output prefix for the fine contact sheets (optional)

Emits, for every 0.25 s:
  lum      mean 0..255 luma
  mot      frame-to-frame abs diff (0..255) on 96x170 gray
  red      red-channel excess  (R - (G+B)/2), normalised 0..1
  teal     blue/green dominance, same idea
Plus:
  soft_cuts  local maxima of motion (whip transitions / cuts) with strength
  flashes    frames where lum jumps hard (strobe hits)
  acts       segments split on long low-motion valleys
"""
import json
import os
import subprocess
import sys

import numpy as np

SRC = sys.argv[1]
OUTJ = sys.argv[2]
PREFIX = sys.argv[3] if len(sys.argv) > 3 else None
FPS = 8            # analysis rate
W, H = 96, 170


def probe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())


def frames(path, w, h, fps, pix="rgb24", ch=3):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf",
                        "fps=%s,scale=%d:%d,format=%s" % (fps, w, h, pix),
                        "-f", "rawvideo", "-"], capture_output=True)
    n = len(r.stdout) // (w * h * ch)
    return np.frombuffer(r.stdout[: n * w * h * ch], dtype=np.uint8).reshape(n, h, w, ch), n


dur = probe_dur(SRC)
rgb, n = frames(SRC, W, H, FPS)
f = rgb.astype(np.float32)
lum = f.mean(axis=3)                       # n,h,w
luma_mean = lum.mean(axis=(1, 2))
mot = np.zeros(n)
mot[1:] = np.abs(np.diff(lum, axis=0)).mean(axis=(1, 2))
red = (f[:, :, :, 0] - (f[:, :, :, 1] + f[:, :, :, 2]) / 2).mean(axis=(1, 2)) / 255.0
teal = ((f[:, :, :, 1] + f[:, :, :, 2]) / 2 - f[:, :, :, 0]).mean(axis=(1, 2)) / 255.0

t = np.arange(n) / FPS
series = [{"t": round(float(t[i]), 2), "lum": round(float(luma_mean[i]), 1),
           "mot": round(float(mot[i]), 2), "red": round(float(red[i]), 3),
           "teal": round(float(teal[i]), 3)} for i in range(n)]

# soft cuts: local maxima of motion above a floor, min 0.6 s apart
thr = max(6.0, float(np.percentile(mot[1:], 88)))
cand = [i for i in range(1, n - 1) if mot[i] > thr and mot[i] >= mot[i - 1] and mot[i] >= mot[i + 1]]
cuts = []
for i in cand:
    if not cuts or (t[i] - cuts[-1]["t"]) > 0.6:
        cuts.append({"t": round(float(t[i]), 2), "strength": round(float(mot[i]), 1)})

# flashes: luminance jump > 12 in one analysis step
flash = []
for i in range(1, n):
    d = luma_mean[i] - luma_mean[i - 1]
    if abs(d) > 12:
        if not flash or (t[i] - flash[-1]["t"]) > 0.4:
            flash.append({"t": round(float(t[i]), 2), "delta": round(float(d), 1)})

# acts: valleys where motion stays low for > 1.2 s
low = mot < max(3.0, float(np.percentile(mot[1:], 25)))
valleys = []
run = 0
for i in range(n):
    if low[i]:
        run += 1
    else:
        if run >= int(1.2 * FPS):
            valleys.append(round(float(t[i - run]), 2))
        run = 0
bounds = [0.0] + [v for v in valleys if 1.0 < v < dur - 1.0] + [dur]
acts = []
for i in range(len(bounds) - 1):
    a, b = bounds[i], bounds[i + 1]
    if b - a < 0.8:
        continue
    i0, i1 = int(a * FPS), max(int(a * FPS) + 1, int(b * FPS))
    seg_l = luma_mean[i0:i1]
    seg_m = mot[i0:i1]
    seg_r = red[i0:i1]
    seg_t = teal[i0:i1]
    acts.append({
        "start": round(a, 2), "end": round(b, 2), "len": round(b - a, 2),
        "lum": round(float(seg_l.mean()), 1),
        "lum_min": round(float(seg_l.min()), 1), "lum_max": round(float(seg_l.max()), 1),
        "mot": round(float(seg_m.mean()), 2), "mot_max": round(float(seg_m.max()), 2),
        "red": round(float(seg_r.mean()), 3), "teal": round(float(seg_t.mean()), 3),
        "cuts": len([c for c in cuts if a <= c["t"] < b]),
    })

report = {
    "source": os.path.basename(SRC), "duration_s": round(dur, 3),
    "analysis_fps": FPS, "frames_analysed": n,
    "soft_cut_threshold": round(thr, 2),
    "soft_cuts": cuts, "soft_cut_count": len(cuts),
    "flashes": flash, "flash_count": len(flash),
    "acts": acts,
    "overall": {
        "lum": round(float(luma_mean.mean()), 1),
        "mot": round(float(mot[1:].mean()), 2),
        "red": round(float(red.mean()), 3),
        "teal": round(float(teal.mean()), 3),
        "cut_rate_per_s": round(len(cuts) / dur, 3),
    },
    "series": series,
}
with open(OUTJ, "w") as fh:
    json.dump(report, fh, indent=1)

if PREFIX:
    for name, a, b in (("A", 0.0, 20.0), ("B", 20.0, dur)):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-vf",
                        "trim=start=%.2f:end=%.2f,setpts=PTS-STARTPTS,fps=%.4f,"
                        "scale=240:426,drawtext=text='%%{pts\\:hms}':x=8:y=8:fontsize=20:"
                        "fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=5,"
                        "tile=4x3" % (a, b, 12 / max(0.5, b - a)),
                        "-frames:v", "1", "-q:v", "6", "%s_%s.jpg" % (PREFIX, name)],
                       capture_output=True)

print("DONE", json.dumps({"acts": len(acts), "cuts": len(cuts), "flashes": len(flash),
                          "overall": report["overall"]})[:600])
for a in acts:
    print("ACT %5.2f-%5.2f  len %5.2f  lum %5.1f  mot %5.2f  red %.3f teal %.3f  cuts %d"
          % (a["start"], a["end"], a["len"], a["lum"], a["mot"], a["red"], a["teal"], a["cuts"]))
