#!/usr/bin/env python3
"""Assemble the master: concat render segments → two-pass loudnorm (−14 LUFS / TP −1, resample AFTER) → mux → measure.
  python3 build.py --segs ../render/seg_a.mp4 ../render/seg_b.mp4 --mix ../audio/mix.wav --out ../render/gravity-of-the-phone_master.mp4
"""
import argparse, json, pathlib, re, subprocess, sys
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()


def run(cmd, capture=True):
    p = subprocess.run(cmd, capture_output=capture, text=True)
    if p.returncode != 0:
        print(p.stderr[-2000:]); raise SystemExit(f"ffmpeg failed: {' '.join(cmd[:6])}...")
    return p


def concat(segs, out):
    lst = out.parent / "concat.txt"
    lst.write_text("".join(f"file '{pathlib.Path(s).resolve()}'\n" for s in segs))
    run([FF, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)])


def _read_wav(path):
    import wave, numpy as np
    w = wave.open(str(path)); n = w.getnframes(); sr = w.getframerate(); ch = w.getnchannels()
    x = np.frombuffer(w.readframes(n), dtype="<i2").reshape(-1, ch).astype(float) / 32767
    return x, sr


def _write_wav(path, x, sr):
    import wave, numpy as np
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(x.shape[1]); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


def true_peak_limit(x, sr, ceiling_db=-1.3, lookahead=0.0025, release=0.09):
    """Linear-phase-ish lookahead true-peak limiter: preserves macro dynamics (LRA), tames transients."""
    import numpy as np
    from scipy.ndimage import minimum_filter1d
    from scipy.signal import resample_poly
    ceil = 10 ** (ceiling_db / 20)
    # true peak via 4x oversampling of the stereo max
    up = resample_poly(x, 4, 1, axis=0)
    tp = np.max(np.abs(up), axis=1).reshape(-1, 4).max(1)[:len(x)]
    g_needed = np.minimum(1.0, ceil / np.maximum(tp, 1e-9))
    L = max(1, int(lookahead * sr))
    g_min = minimum_filter1d(g_needed, size=2 * L + 1, mode="nearest")
    g = np.empty_like(g_min)
    cur, a = 1.0, float(np.exp(-1.0 / (release * sr)))
    for n in range(len(g_min)):
        v = g_min[n]
        cur = v if v < cur else a * cur + (1 - a) * v
        g[n] = cur
    return x * g[:, None], float(20 * np.log10(g.min() + 1e-9))


def master_linear(mix, out, I=-14.0, TP=-1.0):
    """Gain to −14 LUFS, then true-peak limit, then re-measure and trim the gain once more (no dynamic loudnorm)."""
    import numpy as np
    x, sr = _read_wav(mix)
    tmp = out.with_name("tmp_master.wav")
    gain_db = 0.0
    for it in range(5):
        y = x * 10 ** (gain_db / 20)
        y, gr = true_peak_limit(y, sr, ceiling_db=TP - 0.3)
        _write_wav(tmp, y, sr)
        m = measure(tmp)
        print(f"master pass {it}: gain {gain_db:+.2f} dB  limiter GR {gr:.1f} dB  ->  {m}")
        if abs(m["lufs"] - I) < 0.15 and m["true_peak_db"] <= TP:
            break
        gain_db += (I - m["lufs"])
    tmp.replace(out)
    return m


def loudnorm(mix, out, I=-14.0, TP=-1.0, LRA=11.0):
    p = subprocess.run([FF, "-v", "info", "-i", str(mix), "-af", f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    j = json.loads(p.stderr[p.stderr.rfind("{"):p.stderr.rfind("}") + 1])
    print("pass1", {k: j[k] for k in ("input_i", "input_tp", "input_lra", "input_thresh")})
    flt = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
           f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true:print_format=summary")
    run([FF, "-y", "-v", "error", "-i", str(mix), "-af", flt, "-ar", "48000", "-c:a", "pcm_s16le", str(out)])
    return j


def measure(path):
    p = subprocess.run([FF, "-v", "info", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    tail = p.stderr[p.stderr.rfind("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1))
    lra = float(re.search(r"LRA:\s+(-?[\d.]+) LU", tail).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail).group(1))
    d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", p.stderr)
    dur = int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3))
    return dict(lufs=I, true_peak_db=tp, lra=lra, duration_s=round(dur, 3))


def mux(video, audio, out):
    run([FF, "-y", "-v", "error", "-i", str(video), "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segs", nargs="+", required=True)
    ap.add_argument("--mix", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    silent = out.with_name(out.stem + "_silent.mp4")
    concat(a.segs, silent)
    master_wav = out.with_name(out.stem + "_audio.wav")
    master_linear(pathlib.Path(a.mix), master_wav)
    mux(silent, master_wav, out)
    m = measure(out)
    # AAC overshoot guard: if the encoded true peak pokes above −1 dBTP, trim the WAV and re-mux
    if m["true_peak_db"] > -1.0:
        x, sr = _read_wav(master_wav)
        _write_wav(master_wav, x * 10 ** ((-1.05 - m["true_peak_db"]) / 20), sr)
        mux(silent, master_wav, out)
        m = measure(out)
    print("measured", m)
    (out.parent / "measured.json").write_text(json.dumps(m, indent=1))


if __name__ == "__main__":
    main()
