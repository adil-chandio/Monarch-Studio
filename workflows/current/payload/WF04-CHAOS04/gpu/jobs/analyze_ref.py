#!/usr/bin/env python3
"""
CHAOS 04 — reference forensic analyser (runs on the Colab T4 box).

Input : path to the reference .mp4 (argv[1])
Output: written next to the bridge folder:
  REF_FORENSIC.json   every number, no guessing
  ref_sheet.jpg       8-frame contact sheet (for eyeball check)
  ref_frames/*.jpg    the 8 keyframes at 360x640

What it measures
  container/codec/fps/frames/size/bitrate
  scene cuts (grayscale frame-diff at 10 fps, adaptive threshold)
  per-shot: length, brightness, contrast, saturation, motion energy, palette
  audio: integrated loudness (EBU R128), true peak, silence gaps
"""
import json
import os
import subprocess
import sys

W = "/content/chaos_work"
OUT = os.environ.get("CHAOS_OUT", W)
BRIDGE = os.environ.get("CHAOS_BRIDGE", OUT)
os.makedirs(BRIDGE + "/ref_frames", exist_ok=True)

SRC = sys.argv[1]
report = {"source": os.path.basename(SRC), "bytes": os.path.getsize(SRC)}


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def ffprobe(path):
    r = sh(["ffprobe", "-v", "error", "-print_format", "json",
            "-show_format", "-show_streams", path])
    return json.loads(r.stdout)


def decode_gray(path, w, h, fps):
    import numpy as np
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf",
                        "fps=%s,scale=%d:%d,format=gray" % (fps, w, h),
                        "-f", "rawvideo", "-"], capture_output=True)
    buf = r.stdout
    n = len(buf) // (w * h)
    return np.frombuffer(buf[: n * w * h], dtype=np.uint8).reshape(n, h, w), n


def decode_rgb(path, w, h, fps):
    import numpy as np
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf",
                        "fps=%s,scale=%d:%d,format=rgb24" % (fps, w, h),
                        "-f", "rawvideo", "-"], capture_output=True)
    buf = r.stdout
    n = len(buf) // (w * h * 3)
    return np.frombuffer(buf[: n * w * h * 3], dtype=np.uint8).reshape(n, h, w, 3), n


try:
    import numpy as np
    pr = ffprobe(SRC)
    fmt = pr["format"]
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    a = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
    report["format"] = {
        "duration_s": round(float(fmt["duration"]), 3),
        "bitrate_mbps": round(int(fmt["bit_rate"]) / 1e6, 2),
        "container": fmt.get("format_name"),
    }
    report["video"] = {
        "codec": v.get("codec_name"),
        "profile": v.get("profile"),
        "width": v["width"], "height": v["height"],
        "fps": v.get("r_frame_rate"),
        "avg_fps": v.get("avg_frame_rate"),
        "frames": int(v.get("nb_frames") or 0),
        "pix_fmt": v.get("pix_fmt"),
        "bitrate_mbps": round(int(v.get("bit_rate", 0) or 0) / 1e6, 2),
    }
    if a:
        report["audio"] = {
            "codec": a.get("codec_name"), "channels": a.get("channels"),
            "sample_rate": a.get("sample_rate"),
            "bitrate_kbps": int(a.get("bit_rate", 0) or 0) // 1000,
        }
    else:
        report["audio"] = None

    # ---- cuts -------------------------------------------------------------
    g, n = decode_gray(SRC, 96, 170, 10)
    g = g.astype(np.int16)
    d = np.abs(np.diff(g, axis=0)).mean(axis=(1, 2))
    thr = max(8.0, float(np.percentile(d, 97)) * 1.6)
    cuts = [round((i + 1) / 10.0, 2) for i, x in enumerate(d) if x > thr]
    merged = []
    for c in cuts:
        if not merged or c - merged[-1] > 0.35:
            merged.append(c)
    dur = report["format"]["duration_s"]
    bounds = [0.0] + merged + [dur]
    shots = []
    rgb, rn = decode_rgb(SRC, 64, 114, 5)
    for i in range(len(bounds) - 1):
        t0, t1 = bounds[i], bounds[i + 1]
        if t1 - t0 < 0.25:
            continue
        i0, i1 = int(t0 * 5), max(int(t0 * 5) + 1, int(t1 * 5))
        seg = rgb[i0:i1].astype(np.float32)
        if not len(seg):
            continue

        mean = seg.mean(axis=(0, 1, 2))
        mx = seg.max(axis=-1)
        mn = seg.min(axis=-1)
        sat = (mx - mn) / np.maximum(mx, 1)
        lum = seg.mean(axis=-1)
        gseg = g[i0:i1].astype(np.float32)
        motion = float(np.abs(np.diff(gseg, axis=0)).mean()) if len(gseg) > 1 else 0.0
        q = (seg[:, :, :].reshape(-1, 3) // 32 * 32).astype(int)
        keys = q[:, 0] * 65536 + q[:, 1] * 256 + q[:, 2]
        vals, cnt = np.unique(keys, return_counts=True)
        top = vals[np.argsort(-cnt)[:3]]
        pal = ["#%02x%02x%02x" % (k // 65536, (k // 256) % 256, k % 256) for k in top]
        shots.append({
            "start": round(t0, 2), "end": round(t1, 2),
            "len": round(t1 - t0, 2),
            "lum": round(float(lum.mean()), 1),
            "contrast": round(float(lum.std()), 1),
            "sat": round(float(sat.mean()), 3),
            "motion": round(motion, 2),
            "rgb": [round(float(x), 1) for x in mean],
            "palette": pal,
        })
    report["cuts"] = {"threshold": round(thr, 2), "count": len(merged),
                      "times": merged}
    report["shots"] = shots
    if shots:
        lens = [s["len"] for s in shots]
        report["summary"] = {
            "shots": len(shots),
            "mean_shot_s": round(sum(lens) / len(lens), 2),
            "median_shot_s": round(float(np.median(lens)), 2),
            "min_shot_s": min(lens), "max_shot_s": max(lens),
            "mean_lum": round(sum(s["lum"] for s in shots) / len(shots), 1),
            "mean_sat": round(sum(s["sat"] for s in shots) / len(shots), 3),
            "mean_motion": round(sum(s["motion"] for s in shots) / len(shots), 2),
            "motion_p10": round(float(np.percentile([s["motion"] for s in shots], 10)), 2),
            "motion_p90": round(float(np.percentile([s["motion"] for s in shots], 90)), 2),
        }

    # ---- audio ------------------------------------------------------------
    if a:
        r = subprocess.run(["ffmpeg", "-v", "info", "-i", SRC, "-af",
                            "ebur128=peak=true", "-f", "null", "-"],
                           capture_output=True, text=True)
        txt = r.stderr[-4000:]
        loud = {}
        for line in txt.splitlines():
            s = line.strip()
            if s.startswith("I:") and "LUFS" in s:
                loud["integrated_lufs"] = float(s.split()[1])
            if s.startswith("LRA:") and "LU" in s:
                loud["lra"] = float(s.split()[1])
            if s.startswith("Peak:") and "dBFS" in s:
                loud["true_peak_dbfs"] = float(s.split()[1])
        report["loudness"] = loud
        r2 = sh(["ffmpeg", "-v", "info", "-i", SRC, "-af",
                 "silencedetect=noise=-35dB:d=0.4", "-f", "null", "-"])
        gaps = []
        cur = None
        for line in r2.stderr.splitlines():
            if "silence_start" in line:
                cur = round(float(line.split("silence_start:")[1].split()[0]), 2)
            elif "silence_end" in line and cur is not None:
                end = round(float(line.split("silence_end:")[1].split()[0]), 2)
                gaps.append([cur, end, round(end - cur, 2)])
                cur = None
        report["silence_gaps"] = gaps[:30]

    # ---- visuals ----------------------------------------------------------
    picks = [int(x * (dur - 0.4) * 24) for x in
             (0.02, 0.14, 0.28, 0.40, 0.52, 0.66, 0.80, 0.94)]
    for i, fr in enumerate(picks):
        sh(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-vf",
            "select=eq(n\\,%d),scale=360:-2" % fr, "-vsync", "0", "-frames:v", "1",
            "-q:v", "4", "%s/ref_frames/f%02d.jpg" % (BRIDGE, i)])

    report["ok"] = True
except Exception as e:
    import traceback
    traceback.print_exc()
    report["ok"] = False
    report["error"] = "%s: %s" % (type(e).__name__, e)

with open(BRIDGE + "/REF_FORENSIC.json", "w") as f:
    json.dump(report, f, indent=1)
print("DONE", json.dumps({k: report.get(k) for k in
                          ("ok", "format", "video", "summary", "loudness")})[:900])
