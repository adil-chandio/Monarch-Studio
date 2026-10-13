"""prep_vo_kutta.py — fit the four KUTTA voice clips so the voice flows (no dead gaps).

Input : /home/user/build/kutta/vo/k{1..4}.wav  (TTS, voice-03, ur-PK)
Output: /home/user/build/kutta/vo/fit_k{1..4}.wav (48 kHz mono)
        /home/user/build/kutta/vo/timing.json   (clip lengths + caption windows, clip-local seconds)

Rules (measured on the clips, not guessed):
  * leading silence cut to 0.05 s, trailing to 0.05 s
  * every inner pause longer than 0.22 s is shortened to 0.22 s (the sentence breath the SHADE clips used)
  * caption chunks are split at the largest remaining pauses (chunk count per clip is fixed here)
"""
import json, os, wave
import numpy as np

SRC = '/home/user/build/kutta/vo'
SR = 48000
CHUNKS = [1, 3, 1, 2]           # caption chunks per clip (matches kutta2.CAPS)
KEEP_GAP = 0.22
EDGE = 0.05


def read_mono(p):
    w = wave.open(p)
    sr, n = w.getframerate(), w.getnframes()
    a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    return a, sr


def write_mono(p, a, sr=SR):
    pcm = (np.clip(a, -1, 1) * 32767).astype(np.int16)
    w = wave.open(p, 'wb')
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes(pcm.tobytes())
    w.close()


def runs(voiced, hop):
    """speech runs and pauses in hop units."""
    segs, cur = [], None
    for i, v in enumerate(voiced):
        if v and cur is None:
            cur = i
        if not v and cur is not None:
            segs.append((cur, i)); cur = None
    if cur is not None:
        segs.append((cur, len(voiced)))
    return segs


def fit_one(a, sr):
    # up-sample to 48k first (linear, fine for a voice clip)
    x_old = np.linspace(0, 1, len(a))
    x_new = np.linspace(0, 1, int(len(a) * SR / sr))
    a = np.interp(x_new, x_old, a).astype(np.float32)
    hop = int(SR * .01)
    win = int(SR * .03)
    r = np.array([np.sqrt(np.mean(a[i:i + win] ** 2) + 1e-12) for i in range(0, len(a) - win, hop)])
    db = 20 * np.log10(r + 1e-9)
    voiced = db > db.max() - 30
    segs = runs(voiced, 1)
    first, last = segs[0][0], segs[-1][1]
    # speech spans in seconds (hop = 10 ms)
    spans = [(s * .01, e * .01) for s, e in segs]
    # cut the outer silence, then shorten long inner pauses
    t0 = max(0.0, first * .01 - EDGE)
    t1 = min(len(a) / SR, last * .01 + EDGE)
    pieces, out_spans = [], []
    cursor = t0
    out_t = 0.0
    for k, (s, e) in enumerate(spans):
        s_, e_ = max(s, t0), min(e, t1)
        if e_ <= s_:
            continue
        if k > 0:
            gap_in = s - spans[k - 1][1]
            keep = min(gap_in, KEEP_GAP)
            pieces.append(np.zeros(int(keep * SR), np.float32))
            out_t += keep
        pieces.append(a[int(s_ * SR):int(e_ * SR)])
        out_spans.append((round(out_t + (s_ - s_), 3), round(out_t + (e_ - s_), 3)))
        out_t += e_ - s_
    pieces.append(np.zeros(int(EDGE * SR), np.float32))
    out_t += EDGE
    fit = np.concatenate(pieces)
    # recompute the speech spans on the fitted clip (exact, for captions)
    fwin = int(SR * .03)
    fr = np.array([np.sqrt(np.mean(fit[i:i + fwin] ** 2) + 1e-12) for i in range(0, len(fit) - fwin, hop)])
    fdb = 20 * np.log10(fr + 1e-9)
    fsegs = runs(fdb > fdb.max() - 30, 1)
    fspans = [(s * .01, e * .01) for s, e in fsegs]
    return fit, fspans, out_t


def chunk_windows(fspans, n_chunks):
    """split the speech spans into n_chunks at the largest pauses; return (start, end) per chunk."""
    if n_chunks == 1 or len(fspans) == 1:
        return [(fspans[0][0], fspans[-1][1])]
    gaps = [(fspans[i + 1][0] - fspans[i][1], i) for i in range(len(fspans) - 1)]
    cut_after = sorted(i for _, i in sorted(gaps, reverse=True)[:n_chunks - 1])
    wins, start_i = [], 0
    for ci in cut_after + [len(fspans) - 1]:
        wins.append((fspans[start_i][0], fspans[ci][1]))
        start_i = ci + 1
    return wins


def main():
    timing = {'clips': [], 'captions': []}
    for i in range(4):
        a, sr = read_mono(f'{SRC}/k{i + 1}.wav')
        fit, fspans, dur = fit_one(a, sr)
        write_mono(f'{SRC}/fit_k{i + 1}.wav', fit)
        wins = chunk_windows(fspans, CHUNKS[i])
        timing['clips'].append(round(len(fit) / SR, 3))
        timing['captions'].append([[round(s, 3), round(e, 3)] for s, e in wins])
        print(f'k{i + 1}: raw {len(a) / sr:.2f}s -> fit {len(fit) / SR:.2f}s  speech {fspans[0][0]:.2f}-{fspans[-1][1]:.2f}  '
              f'chunks {[(round(s, 2), round(e, 2)) for s, e in wins]}')
    json.dump(timing, open(f'{SRC}/timing.json', 'w'), indent=1)
    print('timing ->', f'{SRC}/timing.json', timing['clips'])


if __name__ == '__main__':
    main()
