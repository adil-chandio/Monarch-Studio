#!/usr/bin/env python3
"""
CHAOS · NEXT FILM — v3 score.

100% generated here (numpy). No sample library, no reference audio, no third-party
music. The rhythm is driven by the same measured cut list the picture uses, so
sound and picture breathe together.

Output: v3/score/score_raw.wav  (48 kHz, stereo, 24-bit)  -> loudnorm to -14.5 LUFS
"""
from __future__ import annotations

import json
import math
import struct
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SHOTLIST = HERE / "SHOTLIST_3D.json"
OUTDIR = HERE / "score"
SR = 48000
FPS = 30

rng = np.random.default_rng(20261026)


# ------------------------------------------------------------------ helpers ---
def env_exp(n, decay, sr=SR):
    t = np.arange(n) / sr
    return np.exp(-t / decay)


def place(buf, sig, start, gain=1.0, pan=0.0):
    """Mix a mono signal into a stereo buffer at sample offset `start`."""
    if start >= buf.shape[1]:
        return
    n = min(len(sig), buf.shape[1] - start)
    if n <= 0:
        return
    l = math.sqrt(0.5 * (1.0 - pan))
    r = math.sqrt(0.5 * (1.0 + pan))
    buf[0, start:start + n] += sig[:n] * gain * l
    buf[1, start:start + n] += sig[:n] * gain * r


def kick(sr=SR, dur=0.34, f0=118.0, f1=42.0):
    n = int(sr * dur)
    t = np.arange(n) / sr
    f = f1 + (f0 - f1) * np.exp(-t / 0.045)
    ph = 2 * np.pi * np.cumsum(f) / sr
    body = np.sin(ph) * np.exp(-t / 0.13)
    click = np.exp(-t / 0.004) * 0.35
    return np.tanh((body + click) * 1.6) * 0.9


def sub_boom(sr=SR, dur=1.6, f=38.0):
    n = int(sr * dur)
    t = np.arange(n) / sr
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.55)
    s += 0.4 * np.sin(2 * np.pi * (f * 1.5) * t) * np.exp(-t / 0.30)
    return np.tanh(s * 1.8) * 0.85


def hat(sr=SR, dur=0.055, bright=0.92):
    n = int(sr * dur)
    x = rng.normal(0, 1, n)
    # cheap high-pass: first difference, twice
    x = np.diff(np.diff(x, prepend=0), prepend=0)
    return x * env_exp(n, 0.012) * bright * 0.25


def clang(sr=SR, dur=0.9, f=1180.0):
    n = int(sr * dur)
    t = np.arange(n) / sr
    out = np.zeros(n)
    for k, (mult, amp, dec) in enumerate(((1.0, 1.0, 0.42), (2.37, 0.55, 0.26),
                                          (3.91, 0.32, 0.18), (5.13, 0.18, 0.12))):
        out += amp * np.sin(2 * np.pi * f * mult * t + k) * np.exp(-t / dec)
    noise = rng.normal(0, 0.35, n) * env_exp(n, 0.05)
    return np.tanh((out + noise) * 0.8) * 0.5


def riser(sr=SR, dur=2.2, f0=300.0, f1=6500.0):
    n = int(sr * dur)
    t = np.arange(n) / sr
    sweep = np.sin(2 * np.pi * (f0 * (f1 / f0) ** (t / dur)) * t)
    noise = rng.normal(0, 1, n)
    noise = np.diff(noise, prepend=0)
    shape = (t / dur) ** 2.2
    return (0.5 * sweep + 0.6 * noise * 0.3) * shape * 0.5


def pluck(freq, sr=SR, dur=0.5):
    n = int(sr * dur)
    t = np.arange(n) / sr
    sig = np.zeros(n)
    for h in range(1, 9):
        sig += (1.0 / h) * np.sin(2 * np.pi * freq * h * t) * np.exp(-t / (0.30 / h))
    return sig * 0.30


def drone(sr=SR, dur=44.4):
    n = int(sr * dur)
    t = np.arange(n) / sr
    base = 55.0
    sig = np.zeros(n)
    for mult, amp in ((1.0, 0.55), (1.5, 0.30), (2.0, 0.18), (3.0, 0.10), (4.02, 0.06)):
        det = 1.0 + 0.0015 * np.sin(2 * np.pi * 0.07 * t * (1 + mult * 0.1))
        sig += amp * np.sin(2 * np.pi * base * mult * det * t)
    lfo = 0.55 + 0.45 * np.sin(2 * np.pi * (1 / 22.0) * t - 1.2)
    sig *= lfo
    # slow open/close arc: quiet in the opening, dense at the climax
    arc = np.interp(t, [0, 9, 16, 29, 33, 42.5, 44.4], [0.35, 0.5, 0.75, 0.6, 0.95, 0.5, 0.0])
    return sig * arc * 0.22


def reverb(x, sr=SR, decay=0.55, mix=0.30):
    n_ir = int(sr * decay)
    t = np.arange(n_ir) / sr
    ir = rng.normal(0, 1, n_ir) * np.exp(-t / (decay * 0.35))
    ir[: int(0.01 * sr)] *= np.linspace(0, 1, int(0.01 * sr))
    ir /= np.abs(ir).sum() ** 0.5
    wet = np.zeros_like(x)
    for ch in range(2):
        wet[ch] = np.convolve(x[ch], ir, mode="same")[: x.shape[1]]
    return x * (1 - mix) + wet * mix


# ------------------------------------------------------------------- build ---
def main() -> int:
    doc = json.loads(SHOTLIST.read_text())
    shots = doc["shots"]
    frames = doc["frames"]
    dur = frames / FPS
    n = int(SR * dur)
    buf = np.zeros((2, n), dtype=np.float64)

    # 1. the bed
    d = drone()
    buf[0, : len(d)] += d
    buf[1, : len(d)] += np.roll(d, int(0.011 * SR)) * 0.96

    cut_frames = [s["f0"] for s in shots if s["f0"] > 0]
    a3 = [s for s in shots if s["act"] == "A3"]
    a5 = [s for s in shots if s["act"] == "A5"]

    # 2. heartbeat: quarter-note kick through acts 2-5 (107 BPM), stops for the card
    beat = 60.0 / 107.0
    b = 280 / FPS
    while b < 1275 / FPS:
        s0 = int(b * SR)
        g = 0.50 if b > 489 / FPS else 0.32
        place(buf, kick(), s0, g)
        b += beat

    # 3. off-beat hats on the 16th grid where the cut density is high
    step = beat / 4
    t = 489 / FPS
    while t < 1275 / FPS:
        if int(t * FPS) % 2 == 0:
            place(buf, hat(), int(t * SR), 0.55 if t > 987 / FPS else 0.34,
                  pan=0.35 if int(t * 100) % 2 else -0.35)
        t += step

    # 4. metal clangs so the rapid cutting is audible, not just visible
    for i, s in enumerate(a5):
        if i % 2 == 0:
            place(buf, clang(f=rng.uniform(760, 1900)), int(s["f0"] / FPS * SR),
                  0.42, pan=rng.uniform(-0.6, 0.6))
    for i, s in enumerate(a3):
        if i % 7 == 3:
            place(buf, clang(f=rng.uniform(1400, 2600), dur=0.5),
                  int(s["f0"] / FPS * SR), 0.20, pan=rng.uniform(-0.7, 0.7))

    # 5. risers into the two big reveals, impacts on the act boundaries
    for start_s, length in ((489 / FPS - 2.0, 2.0), (987 / FPS - 2.4, 2.4),
                            (876 / FPS - 1.3, 1.3)):
        place(buf, riser(dur=length), int(start_s * SR), 0.55)
    for f in (289, 489, 876, 987, 1040, 1275):
        place(buf, sub_boom(), int((f / FPS - 0.02) * SR), 0.62)
        place(buf, kick(dur=0.5, f0=140, f1=36), int(f / FPS * SR), 0.75)

    # 6. motif: minor arpeggio (A-C-E) that only lives in the masked act
    notes = [220.0, 261.63, 329.63, 261.63]
    for i, s in enumerate(a3):
        if i % 5 == 0:
            f = notes[(i // 5) % len(notes)]
            place(buf, pluck(f), int(s["f0"] / FPS * SR), 0.30,
                  pan=(-0.4 if i % 2 else 0.4))

    # 7. blade reveal sting (frame 1036) and end-card shimmer
    place(buf, clang(f=2400, dur=1.8), int(1036 / FPS * SR), 0.55)
    place(buf, riser(dur=1.6, f0=800, f1=9000), int((1275 / FPS - 1.6) * SR), 0.40)
    place(buf, sub_boom(dur=2.4, f=34.0), int(1275 / FPS * SR), 0.55)

    # 8. space + glue
    buf = reverb(buf, mix=0.26, decay=0.7)
    peak = np.abs(buf).max()
    buf = buf / peak * 0.88
    buf = np.tanh(buf * 1.15) * 0.86
    # hard limit the last dB so the encoder never overshoots
    lim = np.abs(buf) > 0.89
    buf[lim] = np.sign(buf[lim]) * 0.89

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / "score_raw.wav"
    pcm = (np.clip(buf.T, -1, 1) * 8388607).astype(np.int32)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(pcm.astype("<i4").tobytes()[:, :3].tobytes() if False else
                      b"".join(struct.pack("<i", int(v))[:3] for v in pcm.reshape(-1)))
    print(f"SCORE ok  {out}  dur={dur:.2f}s  peak={np.abs(buf).max():.3f}  rms_db="
          f"{20*np.log10(np.sqrt((buf**2).mean())+1e-12):.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
