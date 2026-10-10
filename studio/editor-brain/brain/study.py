#!/usr/bin/env python3
"""
brain/study.py — measured study of a reference video (any mp4).

    python3 brain/study.py <video.mp4> --name <slug> --out <dir> [--chapters "0:title,40:title,..."]

Writes <dir>/<slug>_metrics.json, <dir>/<slug>_shots.csv, <dir>/<slug>_sheet_N.jpg (one tile per shot),
<dir>/<slug>_key_<t>.jpg (full-res key frames at chapter starts) and prints a summary.
Needs numpy, pillow, scipy, imageio-ffmpeg.  Streaming decode — memory stays flat (~60 MB for 3 min).
"""
import argparse, json, os, subprocess, sys, math, csv
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
from scipy import signal

FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 192, 108           # analysis raster
TW, TH = 64, 36           # stored thumbs


def probe(path):
    out = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    dur = 0.0; fps = 30.0; wh = (0, 0)
    for line in out.splitlines():
        if "Duration:" in line:
            t = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = t.split(":"); dur = int(h) * 3600 + int(m) * 60 + float(s)
        if "Video:" in line:
            import re
            m = re.search(r"(\d{3,5})x(\d{3,5})", line)
            if m: wh = (int(m.group(1)), int(m.group(2)))
            m = re.search(r"([\d.]+) fps", line)
            if m: fps = float(m.group(1))
    return dur, fps, wh


def decode_video(path):
    cmd = [FF, "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-vf", f"scale={W}:{H}:flags=area", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10 ** 7)
    n = W * H * 3
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        yield np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    p.stdout.close(); p.wait()


def video_pass(path):
    prev = None
    luma, mad, hist_d, white, sat, warm, thumbs = [], [], [], [], [], [], []
    prev_hist = None
    for fr in decode_video(path):
        f = fr.astype(np.float32)
        g = 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]
        luma.append(float(g.mean()))
        if prev is None:
            mad.append(0.0)
        else:
            mad.append(float(np.abs(g - prev).mean()))
        h, _ = np.histogram(g, bins=32, range=(0, 255)); h = h / h.sum()
        hist_d.append(0.0 if prev_hist is None else float(0.5 * np.abs(h - prev_hist).sum()))
        white.append(float((g > 225).mean()))
        mx = f.max(axis=2); mn = f.min(axis=2)
        sat.append(float(((mx - mn) / (mx + 1e-3)).mean()))
        warm.append(float((f[..., 0] - f[..., 2]).mean()))
        thumbs.append(np.asarray(Image.fromarray(fr).resize((TW, TH), Image.BOX)))
        prev, prev_hist = g, h
    return (np.array(luma), np.array(mad), np.array(hist_d), np.array(white),
            np.array(sat), np.array(warm), np.stack(thumbs))


def detect_cuts(mad, hist_d, fps, luma=None, thumbs=None):
    """Hard cuts (adaptive to the film's own motion floor), dips to black, and slow dissolves.
    Dark films (mean luma < 40) produce small frame differences, so thresholds scale with the median MAD."""
    n = len(mad)
    med = float(np.median(mad[1:])) if n > 1 else 0.3
    thr = max(3.0, 8.0 * med)
    cuts = []
    last = -100
    k = int(fps)
    for t in range(1, n):
        if t - last < 5:
            continue
        lo, hi = max(0, t - k), min(n, t + k)
        base = np.median(np.concatenate([mad[lo:t], mad[t + 1:hi]])) if hi - lo > 4 else 0
        dl = abs(float(luma[t] - luma[t - 1])) if luma is not None else 0.0
        if mad[t] > thr and mad[t] > 4.0 * (base + 0.3) and (hist_d[t] > 0.05 or dl > 8):
            cuts.append((t, "hard")); last = t
    # dips to black (luma < 3 for >= 2 frames) — one transition per run, placed at the run start
    if luma is not None:
        blk = luma < 3
        i = 0
        while i < n:
            if blk[i]:
                j = i
                while j < n and blk[j]:
                    j += 1
                if j - i >= 2 and i > 0:
                    cuts = [c for c in cuts if not (i - 3 <= c[0] <= j + 3)]
                    cuts.append((i, "dip_black"))
                i = j
            else:
                i += 1
    # slow dissolves: change across 15 frames large while no single frame jumps
    if thumbs is not None:
        th = thumbs.astype(np.float32)
        g = 0.2126 * th[..., 0] + 0.7152 * th[..., 1] + 0.0722 * th[..., 2]
        D = np.zeros(n)
        for t in range(8, n - 8):
            D[t] = np.abs(g[t + 7] - g[t - 8]).mean()
        dthr = max(6.0, 15.0 * med)
        taken = sorted(c[0] for c in cuts)
        t = 8
        dips = [c[0] for c in cuts if c[1] == "dip_black"]
        while t < n - 8:
            near = any(abs(t - c) <= 15 for c in taken) or any(0 <= t - d_ <= 30 for d_ in dips)
            spread = float((np.abs(g[t + 7] - g[t - 8]) > 6).mean()) if D[t] > dthr else 0.0
            if (not near) and D[t] > dthr and spread > 0.25 and mad[t - 7:t + 8].max() < 3.5 and D[t] >= D[max(0, t - 10):t + 11].max():
                cuts.append((t, "dissolve")); taken.append(t); t += 15
            else:
                t += 1
    cuts.sort(key=lambda c: c[0])
    merged = []
    for c in cuts:
        if merged and c[0] - merged[-1][0] < 6:
            continue
        merged.append(c)
    return merged


def shots_from_cuts(cuts, n, fps):
    bounds = [0] + [c[0] for c in cuts] + [n]
    kinds = ["start"] + [c[1] for c in cuts]
    shots = []
    for i in range(len(bounds) - 1):
        a, b = bounds[i], bounds[i + 1]
        shots.append({"i": i, "f0": a, "f1": b, "t0": a / fps, "t1": b / fps, "dur": (b - a) / fps, "in": kinds[i]})
    return shots


def palette(thumbs, k=4):
    px = thumbs.reshape(-1, 3).astype(np.float32)
    if len(px) > 6000:
        px = px[np.random.RandomState(0).choice(len(px), 6000, replace=False)]
    # simple k-means
    cent = px[np.random.RandomState(1).choice(len(px), k, replace=False)]
    for _ in range(12):
        d = ((px[:, None, :] - cent[None]) ** 2).sum(-1)
        lab = d.argmin(1)
        for j in range(k):
            if (lab == j).any():
                cent[j] = px[lab == j].mean(0)
    cnt = np.bincount(lab, minlength=k) / len(px)
    order = np.argsort(-cnt)
    return [{"rgb": [int(round(v)) for v in cent[j]], "share": round(float(cnt[j]), 3)} for j in order]


def audio_pass(path, dur):
    # loudness via ebur128
    out = subprocess.run([FF, "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    lufs = lra = tp = None
    tail = out[-2500:]
    import re
    m = re.search(r"I:\s*(-?[\d.]+) LUFS", tail);  lufs = float(m.group(1)) if m else None
    m = re.search(r"LRA:\s*(-?[\d.]+) LU", tail);   lra = float(m.group(1)) if m else None
    m = re.search(r"Peak:\s*(-?[\d.]+) dBFS", tail); tp = float(m.group(1)) if m else None
    sr = 24000
    raw = subprocess.run([FF, "-v", "error", "-i", path, "-f", "s16le", "-acodec", "pcm_s16le", "-ac", "2", "-ar", str(sr), "-"],
                         capture_output=True).stdout
    st = np.frombuffer(raw, np.int16).reshape(-1, 2).astype(np.float32) / 32768.0
    mono = st.mean(1)
    win = int(sr * 0.1)
    nwin = len(mono) // win
    rms = np.sqrt((mono[:nwin * win].reshape(nwin, win) ** 2).mean(1) + 1e-12)
    rms_db = 20 * np.log10(rms)
    l = st[:nwin * win, 0].reshape(nwin, win); r = st[:nwin * win, 1].reshape(nwin, win)
    corr = np.array([np.corrcoef(a, b)[0, 1] if a.std() > 1e-4 and b.std() > 1e-4 else 1.0 for a, b in zip(l, r)])
    # STFT bands
    f, t, Z = signal.stft(mono, fs=sr, nperseg=2048, noverlap=1024)
    P = np.abs(Z) ** 2
    def band(a, b):
        m = (f >= a) & (f < b)
        return P[m].sum(0)
    tot = P.sum(0) + 1e-9
    bands = {"sub_20_120": band(20, 120) / tot, "lowmid_120_500": band(120, 500) / tot,
             "voice_300_3000": band(300, 3000) / tot, "presence_2000_5000": band(2000, 5000) / tot,
             "air_8000_12000": band(8000, 12000) / tot}
    # onsets via spectral flux (half-wave rectified)
    S = np.sqrt(P)
    flux = np.maximum(S[:, 1:] - S[:, :-1], 0).sum(0)
    flux = flux / (flux.max() + 1e-9)
    hop = 1024 / sr
    # peak pick
    thr = np.convolve(flux, np.ones(31) / 31, mode="same") * 1.6 + 0.02
    peaks = [i for i in range(1, len(flux) - 1) if flux[i] > thr[i] and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]]
    onsets = [round(i * hop, 2) for i in peaks]
    # tempo from autocorrelation of flux (60–180 BPM)
    fl = flux - flux.mean()
    ac = np.correlate(fl, fl, mode="full")[len(fl) - 1:]
    ac /= (ac[0] + 1e-9)
    lags = np.arange(len(ac)) * hop
    m = (lags > 60 / 180) & (lags < 60 / 60)
    bpm = float(60 / lags[m][np.argmax(ac[m])]) if m.any() else None
    return {"lufs": lufs, "lra": lra, "true_peak_dbfs": tp, "sr": sr, "rms_db": rms_db, "corr": corr,
            "band_t": t, "bands": bands, "onsets": onsets, "bpm_estimate": bpm, "dur": len(mono) / sr}


def sheet(path, shots, fps, out, slug, cols=5, tile=(384, 216), per=30):
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    files = []
    for s0 in range(0, len(shots), per):
        chunk = shots[s0:s0 + per]
        rows = math.ceil(len(chunk) / cols)
        img = Image.new("RGB", (cols * tile[0], rows * (tile[1] + 26)), (12, 12, 12))
        d = ImageDraw.Draw(img)
        for j, s in enumerate(chunk):
            tm = (s["t0"] + s["t1"]) / 2
            fn = f"/tmp/_tile_{j}.jpg"
            subprocess.run([FF, "-v", "error", "-y", "-ss", f"{tm:.3f}", "-i", path, "-frames:v", "1",
                            "-vf", f"scale={tile[0]}:{tile[1]}", "-q:v", "4", fn])
            try:
                im = Image.open(fn).convert("RGB")
            except Exception:
                im = Image.new("RGB", tile, (40, 0, 0))
            x = (j % cols) * tile[0]; y = (j // cols) * (tile[1] + 26)
            img.paste(im, (x, y))
            d.text((x + 6, y + tile[1] + 4), f"#{s['i']}  {s['t0']:.2f}s  {s['dur']:.2f}s  {s['in']}", fill=(235, 235, 235), font=font)
        fn = os.path.join(out, f"{slug}_sheet_{s0 // per + 1}.jpg")
        img.save(fn, quality=82); files.append(fn)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--name", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--chapters", default="")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    dur, fps, wh = probe(a.video)
    print(f"[study] {a.video}: {dur:.2f}s {fps}fps {wh}")
    luma, mad, hist_d, white, sat, warm, thumbs = video_pass(a.video)
    n = len(luma)
    cuts = detect_cuts(mad, hist_d, fps, luma=luma, thumbs=thumbs)
    shots = shots_from_cuts(cuts, n, fps)
    for s in shots:
        a0, a1 = s["f0"], s["f1"]
        s["luma"] = round(float(luma[a0:a1].mean()), 1)
        s["motion"] = round(float(mad[a0 + 1:a1].mean()) if a1 - a0 > 1 else 0.0, 2)
        s["white_pk"] = round(float(white[a0:a1].max()), 3)
        s["sat"] = round(float(sat[a0:a1].mean()), 3)
        s["warm"] = round(float(warm[a0:a1].mean()), 1)
        s["palette"] = palette(thumbs[a0:a1:max(1, (a1 - a0) // 8)])
    durs = np.array([s["dur"] for s in shots])
    au = audio_pass(a.video, dur)
    # chapters
    chapters = []
    if a.chapters:
        items = [c.split(":", 1) for c in a.chapters.split(",")]
        for i, (t0, title) in enumerate(items):
            t0 = float(t0); t1 = float(items[i + 1][0]) if i + 1 < len(items) else dur
            f0, f1 = int(t0 * fps), int(t1 * fps)
            sh = [s for s in shots if s["t0"] >= t0 - 0.01 and s["t0"] < t1]
            w0, w1 = int(t0 * 10), int(t1 * 10)
            on = [o for o in au["onsets"] if t0 <= o < t1]
            chapters.append({"title": title, "t0": t0, "t1": t1, "shots": len(sh),
                             "median_shot": round(float(np.median([s["dur"] for s in sh])), 2) if sh else None,
                             "luma": round(float(luma[f0:f1].mean()), 1), "motion": round(float(mad[f0:f1].mean()), 2),
                             "rms_db": round(float(au["rms_db"][w0:w1].mean()), 1), "onsets_per_s": round(len(on) / (t1 - t0), 2)})
    bt = au["band_t"]
    def bmean(k, t0=0, t1=None):
        t1 = t1 or dur
        m = (bt >= t0) & (bt < t1)
        return round(float(au["bands"][k][m].mean()), 4)
    metrics = {
        "video": os.path.basename(a.video), "duration_s": round(dur, 2), "fps": fps, "size": wh, "frames": n,
        "shots": len(shots), "hard_cuts": sum(1 for c in cuts if c[1] == "hard"), "dips_to_black": sum(1 for c in cuts if c[1] == "dip_black"), "dissolves": sum(1 for c in cuts if c[1] == "dissolve"),
        "shot_len": {"median": round(float(np.median(durs)), 2), "mean": round(float(durs.mean()), 2), "p10": round(float(np.percentile(durs, 10)), 2),
                      "p90": round(float(np.percentile(durs, 90)), 2), "max": round(float(durs.max()), 2), "min": round(float(durs.min()), 2),
                      "over_3s": int((durs > 3).sum()), "over_5s": int((durs > 5).sum()), "under_1s": int((durs < 1).sum())},
        "luma": {"mean": round(float(luma.mean()), 1), "p10": round(float(np.percentile(luma, 10)), 1), "p90": round(float(np.percentile(luma, 90)), 1),
                 "dark_frames_lt30": round(float((luma < 30).mean()), 3), "black_frames_lt6": round(float((luma < 6).mean()), 3)},
        "motion": {"mean_mad": round(float(mad[1:].mean()), 2), "still_frames_lt0_5": round(float((mad[1:] < 0.5).mean()), 3),
                   "p90": round(float(np.percentile(mad[1:], 90)), 2)},
        "saturation_mean": round(float(sat.mean()), 3), "warm_bias_mean": round(float(warm.mean()), 1),
        "white_text_frames_gt0_04": round(float((white > 0.04).mean()), 3),
        "audio": {"lufs": au["lufs"], "lra": au["lra"], "true_peak_dbfs": au["true_peak_dbfs"], "bpm_estimate": round(au["bpm_estimate"], 1) if au["bpm_estimate"] else None,
                  "onsets_total": len(au["onsets"]), "onsets_per_s": round(len(au["onsets"]) / dur, 2),
                  "rms_db_mean": round(float(au["rms_db"].mean()), 1), "rms_db_p10": round(float(np.percentile(au["rms_db"], 10)), 1),
                  "rms_db_p90": round(float(np.percentile(au["rms_db"], 90)), 1), "silence_lt_minus50_share": round(float((au["rms_db"] < -50).mean()), 3),
                  "stereo_corr_mean": round(float(np.nanmean(au["corr"])), 3),
                  "bands_mean": {k: bmean(k) for k in au["bands"]}},
        "chapters": chapters,
        "cuts": [{"f": c[0], "t": round(c[0] / fps, 2), "kind": c[1]} for c in cuts],
    }
    # per-10 s timeline for luma / motion / rms
    tl = []
    for t0 in range(0, int(dur), 10):
        f0, f1 = int(t0 * fps), min(n, int((t0 + 10) * fps)); w0, w1 = t0 * 10, min(len(au["rms_db"]), (t0 + 10) * 10)
        tl.append({"t": t0, "luma": round(float(luma[f0:f1].mean()), 1), "motion": round(float(mad[f0:f1].mean()), 2),
                   "rms_db": round(float(au["rms_db"][w0:w1].mean()), 1), "cuts": sum(1 for c in cuts if f0 <= c[0] < f1),
                   "white": round(float(white[f0:f1].max()), 3), "voice_band": bmean("voice_300_3000", t0, t0 + 10)})
    metrics["timeline_10s"] = tl
    with open(os.path.join(a.out, f"{a.name}_metrics.json"), "w") as fh:
        json.dump(metrics, fh, indent=1)
    with open(os.path.join(a.out, f"{a.name}_shots.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["i", "t0", "t1", "dur", "in", "luma", "motion", "white_pk", "sat", "warm", "pal1", "pal2", "pal3"])
        for s in shots:
            w.writerow([s["i"], f"{s['t0']:.2f}", f"{s['t1']:.2f}", f"{s['dur']:.2f}", s["in"], s["luma"], s["motion"], s["white_pk"], s["sat"], s["warm"]] +
                       [str(p["rgb"]) for p in s["palette"][:3]])
    files = sheet(a.video, shots, fps, a.out, a.name)
    for ch in chapters:
        subprocess.run([FF, "-v", "error", "-y", "-ss", f"{ch['t0'] + 1.0:.2f}", "-i", a.video, "-frames:v", "1", "-q:v", "3",
                        os.path.join(a.out, f"{a.name}_key_{int(ch['t0']):03d}.jpg")])
    print(json.dumps({k: metrics[k] for k in ["duration_s", "shots", "hard_cuts", "dips_to_black", "dissolves", "shot_len", "luma", "motion", "saturation_mean", "warm_bias_mean", "white_text_frames_gt0_04", "audio"]}, indent=1))
    for ch in chapters:
        print(ch)
    print("sheets:", files)


if __name__ == "__main__":
    main()
