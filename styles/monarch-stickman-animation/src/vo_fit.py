"""
vo_fit.py — tighten the pauses inside each VO clip WITHOUT time-stretching.

The 37 s build re-fitted the voice with atempo 1.35–1.53 (the RE-FIT LAW). The
long-form build learned the better rule: never stretch the narration — cut the
picture to the voice. This short sits between the two: the lines are recorded
with 0.4–0.6 s phrase pauses, so each internal pause is capped at PAUSE_MAX and
the head/tail air is trimmed. Every speech sample is left exactly as recorded.

    python3 src/vo_fit.py            -> assets/p{1..6}_fit.wav + prints a table
"""
import json, subprocess, sys
import numpy as np
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000
THR_DB = -34.0          # same silencedetect threshold the episode build used
MIN_SIL = 0.16          # a gap shorter than this is articulation, not a pause
PAUSE_MAX = 0.30        # natural phrase pause after tightening
HEAD, TAIL = 0.040, 0.090
XF = int(0.008 * SR)    # 8 ms raised-cosine crossfade at every cut


def load(path):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1',
                          '-ar', str(SR), '-'], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def silences(x):
    """(start, end) sample pairs where the 10 ms RMS stays under THR_DB."""
    hop = int(0.010 * SR)
    n = len(x) // hop
    rms = np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    quiet = db < THR_DB
    out, i = [], 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if (j - i) * hop >= MIN_SIL * SR:
                out.append((i * hop, j * hop))
            i = j
        else:
            i += 1
    return out


def crossfade_join(a, b):
    if len(a) < XF or len(b) < XF:
        return np.concatenate([a, b])
    w = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, XF))
    mid = a[-XF:] * (1 - w) + b[:XF] * w
    return np.concatenate([a[:-XF], mid, b[XF:]])


def fit(x):
    sil = silences(x)
    n = len(x)
    # head / tail
    s0 = 0
    if sil and sil[0][0] == 0:
        s0 = max(0, sil[0][1] - int(HEAD * SR))
    e0 = n
    if sil and sil[-1][1] >= n - int(0.02 * SR):
        e0 = min(n, sil[-1][0] + int(TAIL * SR))
    inner = [(a, b) for a, b in sil if a > s0 and b < e0]
    out = np.zeros(0)
    cur = s0
    removed = 0.0
    for a, b in inner:
        keep = int(PAUSE_MAX * SR)
        gap = b - a
        if gap <= keep:
            continue
        cut = gap - keep
        # cut from the centre of the pause, keep half the retained air each side
        ca = a + keep // 2
        cb = ca + cut
        out = crossfade_join(out, x[cur:ca]) if len(out) else x[cur:ca].copy()
        cur = cb
        removed += cut / SR
    out = crossfade_join(out, x[cur:e0]) if len(out) else x[cur:e0].copy()
    # tiny fades at the clip edges so nothing clicks on adelay
    f = int(0.006 * SR)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    return out, removed, (n - (e0 - s0)) / SR


def main():
    rows = []
    for i in range(1, 7):
        src = f'/home/user/assets/p{i}.mp3'
        x = load(src)
        y, removed, edge = fit(x)
        dst = f'/home/user/assets/p{i}_fit.wav'
        pcm = (np.clip(y, -1, 1) * 32767).astype(np.int16)
        import wave
        with wave.open(dst, 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        rows.append(dict(clip=f'p{i}', raw=round(len(x) / SR, 3), fit=round(len(y) / SR, 3),
                         pauses_cut=round(removed, 3), edges_cut=round(edge, 3)))
    tot_raw = sum(r['raw'] for r in rows)
    tot_fit = sum(r['fit'] for r in rows)
    print(f"{'clip':5} {'raw':>7} {'fit':>7} {'pauses':>7} {'edges':>7}")
    for r in rows:
        print(f"{r['clip']:5} {r['raw']:7.3f} {r['fit']:7.3f} {r['pauses_cut']:7.3f} {r['edges_cut']:7.3f}")
    print(f"total {tot_raw:7.3f} {tot_fit:7.3f}")
    json.dump(rows, open('/home/user/build/vo_fit.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
