"""CHAOS 04 — our own score. 120 BPM, cut to the same measured grid as the picture.

Nothing sampled, nothing borrowed: every sound is synthesised here.

    python3 chaos04/score.py --out build/score_48k.wav
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import wave
from pathlib import Path

import numpy as np

SR = 48000
DUR = 44.40          # 1332 frames @ 30 fps — matches the picture exactly
BEAT = 0.5           # 120 BPM
BAR = BEAT * 4

# the measured grid
FLASH = [9.12, 9.62, 13.12, 16.25, 16.75, 17.25, 17.75, 18.50, 19.25, 20.50,
         21.00, 21.50, 22.12, 22.62, 23.12, 23.75, 24.25, 25.12, 25.62, 26.25,
         26.75, 27.25, 28.00, 28.50, 29.12, 31.12, 32.12, 32.88, 33.50, 34.12,
         34.62, 35.12, 35.75, 36.25, 36.75, 37.38, 37.88, 38.38, 39.38, 39.88]
CUTS = [16.25, 17.25, 18.00, 18.62, 19.38, 20.50, 24.38, 25.50, 26.25, 27.62,
        28.88, 32.88, 34.12, 34.88, 35.75, 36.50, 39.50]
SILENCE = [(40.34, 40.93), (42.10, DUR)]

DROP = 16.25
FINAL = 39.50
EMBLEM = 40.93

rng = np.random.default_rng(20261027)
N = int(DUR * SR)
L = np.zeros(N)
R = np.zeros(N)


def add(sig, t, gain=1.0, pan=0.0):
    """Place a mono signal at time t with constant-power pan (-1..1)."""
    i = int(t * SR)
    if i >= N:
        return
    j = min(N, i + len(sig))
    seg = sig[: j - i] * gain
    lg = math.cos((pan + 1) * math.pi / 4)
    rg = math.sin((pan + 1) * math.pi / 4)
    L[i:j] += seg * lg
    R[i:j] += seg * rg


def env(n, attack=0.002, decay=0.3, power=2.0):
    t = np.arange(n) / SR
    a = np.clip(t / max(1e-6, attack), 0, 1)
    d = np.exp(-t / max(1e-6, decay / 4)) * np.exp(-(t / max(1e-6, decay)) ** power)
    return a * d


def saw(freq, n, harmonics=8, phase=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for h in range(1, harmonics + 1):
        if freq * h > SR * 0.45:
            break
        out += np.sin(2 * np.pi * freq * h * t + phase * h) / (h ** 1.35)
    return out


def noise(n):
    return rng.standard_normal(n)


def highpass(sig, taps=17):
    """Cheap FIR high-pass (delta - moving average)."""
    k = np.ones(taps) / taps
    return sig - np.convolve(sig, k, mode="same")


def lowpass(sig, taps=33):
    k = np.ones(taps) / taps
    return np.convolve(sig, k, mode="same")


def kick(dur=0.42, f0=132.0, f1=46.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.035)
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * np.exp(-t / 0.19)
    click = highpass(noise(n), 9) * np.exp(-t / 0.004) * 0.35
    return np.tanh((body + click) * 1.6)


def sub_boom(dur=1.6, f=44.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.5)
    rumble = lowpass(noise(n), 129) * np.exp(-t / 0.28) * 0.5
    return np.tanh((body + rumble) * 1.9)


def snare(dur=0.22):
    n = int(dur * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 186 * t) * np.exp(-t / 0.055)
    snap = highpass(noise(n), 7) * np.exp(-t / 0.075)
    return np.tanh((snap * 0.9 + body * 0.35) * 1.7)


def hat(dur=0.055, open_=False):
    n = int(dur * SR * (3 if open_ else 1))
    t = np.arange(n) / SR
    return highpass(noise(n), 5) * np.exp(-t / (0.10 if open_ else 0.022))


def clank(dur=0.7, base=420.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    parts = (np.sin(2 * np.pi * base * t) * 0.6
             + np.sin(2 * np.pi * base * 2.41 * t) * 0.35
             + np.sin(2 * np.pi * base * 3.87 * t) * 0.22
             + np.sin(2 * np.pi * base * 5.19 * t) * 0.12)
    return (parts * np.exp(-t / 0.16) + highpass(noise(n), 7) * np.exp(-t / 0.05) * 0.3)


def riser(dur, f0=180.0, f1=3800.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    shape = (t / dur) ** 2.2
    tone = np.sin(2 * np.pi * (f0 + (f1 - f0) * shape) * t) * 0.35
    air = highpass(noise(n), 3) * shape * 0.5
    return (tone + air) * (0.25 + 0.75 * shape)


def reverse_swell(dur=0.9, f=110.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) * 0.5 + highpass(noise(n), 5) * 0.45
    return s * (t / dur) ** 2.6


def pad(freqs, dur, attack=0.6, release=1.2, gain=0.16):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        det = 1.0 + 0.0015 * rng.standard_normal()
        for h, w in ((1, 1.0), (2, 0.42), (3, 0.22), (4, 0.11), (5, 0.06)):
            out += w * np.sin(2 * np.pi * f * h * det * t + rng.uniform(0, 6.28))
    a = np.clip(t / attack, 0, 1)
    r = np.clip((dur - t) / max(0.05, release), 0, 1)
    return out * a * r * gain / max(1, len(freqs))


# D minor
D1, D2, D3, D4 = 36.71, 73.42, 146.83, 293.66
F3, A3, Bb2, C3, G2, G3, A2 = 174.61, 220.0, 116.54, 130.81, 98.0, 196.0, 110.0

# ---------------------------------------------------------------- arrangement
# 0.0 - 9.12 : room tone, drone, distant weight
add(pad([D1, D2, A2], 9.6, attack=1.4, release=0.6, gain=0.5), 0.0)
add(sub_boom(2.2, 41.0), 0.0, 0.55)
add(sub_boom(2.0, 43.0), 2.0, 0.30)
add(clank(1.1, 300.0), 0.35, 0.16, -0.5)
add(clank(1.0, 470.0), 3.10, 0.12, 0.55)
add(sub_boom(1.8, 46.0), 4.0, 0.42)
add(kick(), 4.0, 0.5)
add(hat(0.05), 4.0, 0.10, 0.4)
add(reverse_swell(1.3, 96.0), 6.6, 0.5, 0.1)
add(sub_boom(1.8, 40.0), 6.9, 0.45)
add(kick(), 7.05, 0.45)
add(clank(1.2, 340.0), 8.4, 0.18, -0.35)
add(reverse_swell(0.9, 120.0), 8.2, 0.55)

# 9.12 : first hit on the measured flash
add(sub_boom(2.0, 44.0), 9.12, 0.72)
add(kick(), 9.12, 0.72)
add(clank(1.4, 260.0), 9.12, 0.22, -0.2)
add(pad([D2, F3, A3], 4.0, attack=0.05, release=1.0, gain=0.22), 9.12)

# 9.12 - 13.25 : half-time pulse, then a riser into the act break
for t in (9.62, 11.12, 12.12):
    add(kick(), t, 0.62)
    add(hat(0.05), t, 0.12, 0.3)
add(snare(), 10.12, 0.24, 0.18)
add(snare(), 12.62, 0.28, 0.18)
add(riser(2.9, 160, 5200), 10.35, 0.5)
add(reverse_swell(1.2, 80.0), 12.05, 0.6)
add(sub_boom(1.6, 40.0), 13.12, 0.66)
add(kick(), 13.12, 0.7)
add(pad([D2, A2, D3], 3.1, attack=0.4, release=0.8, gain=0.24), 13.25)

# 13.25 - 16.25 : quiet menace then the drop
for t in (14.25, 15.25):
    add(kick(), t, 0.5)
    add(hat(0.04), t, 0.09, -0.4)
add(snare(), 14.75, 0.22)
add(riser(2.6, 220, 7200), 13.7, 0.62)
add(reverse_swell(1.1, 130.0), 15.15, 0.62)
# snare roll into the drop
t = 15.25
step = 0.25
while t < DROP - 0.01:
    add(snare(), t, 0.16 + 0.12 * (t - 15.25) / 1.0, 0.05)
    t += step
    step = max(0.0625, step * 0.82)

# ---------------------------------------------------------------- the drop
add(sub_boom(2.4, 38.0), DROP, 0.92)
add(kick(), DROP, 0.92)
add(clank(1.6, 210.0), DROP, 0.28)
add(pad([D2, D2 * 2, F3, A3, D4], 3.6, attack=0.02, release=1.6, gain=0.30), DROP)


def groove(t0, t1, kicks, snares, hats16=False, clank_every=2.0, bass=True,
           four=False, density=1.0):
    bar_t = t0
    bar = 0
    while bar_t < t1 - 1e-6:
        # kick pattern inside the bar
        if four:
            for b in range(4):
                t = bar_t + b * BEAT
                if t < t1:
                    add(kick(), t, 0.82)
        else:
            for b in kicks:
                t = bar_t + b * BEAT
                if t < t1:
                    add(kick(), t, 0.88 if b in (0,) else 0.74)
        for b in snares:
            t = bar_t + b * BEAT
            if t < t1:
                add(snare(), t, 0.30 * density, 0.12)
        # hats
        subdiv = 4 if hats16 else 2
        for s in range(4 * subdiv):
            t = bar_t + s * (BEAT / subdiv)
            if t >= t1:
                break
            accent = 0.16 if s % subdiv == 0 else 0.09
            add(hat(0.04, open_=(s == 3 * subdiv)), t, accent * density,
                -0.35 if s % 2 else 0.35)
        # bass
        if bass:
            pattern = [(0.0, D2, 0.42), (0.75, D2, 0.3), (1.5, F3 / 2, 0.34),
                       (2.0, D2, 0.3), (2.75, C3 / 2, 0.3), (3.25, Bb2 / 2, 0.34)]
            for off, f, g in pattern:
                t = bar_t + off
                if t < t1:
                    n = int(0.34 * SR)
                    s = saw(f, n, 7) * env(n, 0.004, 0.34, 2.4)
                    add(s, t, g * 0.9)
        if clank_every and (bar * BAR) % clank_every < 1e-6:
            add(clank(0.9, 240.0 + 40 * (bar % 3)), bar_t + 0.25, 0.13,
                -0.6 if bar % 2 else 0.6)
        bar_t += BAR
        bar += 1


# A 16.25-20.50 : half-time
groove(16.25, 20.50, kicks=[0.0, 2.5], snares=[1.0, 3.0], hats16=False,
       clank_every=2.0)
# B 20.50-24.38 : sixteenths open up
groove(20.50, 24.38, kicks=[0.0, 1.75, 2.5], snares=[1.0, 3.0], hats16=True,
       clank_every=1.0)
# C 24.38-28.88 : four to the floor
groove(24.38, 28.88, kicks=[], snares=[0.5, 2.5], hats16=True, four=True,
       clank_every=1.0, density=1.15)
# D 28.88-32.88 : breakdown, no kick, pressure builds
add(pad([D2, F3, A3, C3], 4.0, attack=0.8, release=0.4, gain=0.26), 28.88)
t = 28.88
while t < 32.88 - 1e-6:
    add(snare(), t, 0.10 + 0.10 * (t - 28.88) / 4.0, 0.2)
    add(hat(0.05, open_=True), t + 0.25, 0.10, -0.3)
    t += 0.25
add(riser(2.4, 200, 6400), 30.4, 0.5)
add(reverse_swell(1.2, 70.0), 31.5, 0.6)
# E 32.88-39.50 : double-time climax
add(sub_boom(1.8, 40.0), 32.88, 0.8)
add(kick(), 32.88, 0.88)
groove(32.88, 39.50, kicks=[], snares=[1.0, 3.0, 3.5], hats16=True, four=True,
       clank_every=0.5, density=1.3)
# measured cut hits on top of the climax
for t in (34.12, 34.88, 35.75, 36.50):
    add(kick(), t, 0.86)
    add(clank(1.0, 300.0), t, 0.20, 0.5 if t % 1 else -0.5)
    add(sub_boom(1.2, 42.0), t, 0.55)
for t in (37.38, 37.88, 38.38):
    add(reverse_swell(0.45, 90.0), t - 0.45, 0.45)
add(reverse_swell(1.2, 60.0), 38.2, 0.7)

# ---------------------------------------------------------------- out
add(sub_boom(2.6, 36.0), FINAL, 1.0)
add(kick(), FINAL, 0.95)
add(clank(2.0, 180.0), FINAL, 0.30)
add(pad([D1, D2, A2], 2.4, attack=0.02, release=1.6, gain=0.34), FINAL)
add(highpass(noise(int(0.9 * SR)), 3) * np.exp(-np.arange(int(0.9 * SR)) / SR / 0.3),
    FINAL, 0.34)

# emblem: swell, hit, and one held chord
add(reverse_swell(0.34, 150.0), EMBLEM - 0.34, 0.6)
add(sub_boom(1.4, 46.0), EMBLEM, 0.8)
add(kick(0.5, 120, 52), EMBLEM, 0.7)
add(clank(1.6, 520.0), EMBLEM, 0.22, 0.35)
add(pad([D3, F3, A3, D4], 1.15, attack=0.01, release=0.5, gain=0.30), EMBLEM)
add(reverse_swell(0.5, 220.0), 41.6, 0.30)

# ---------------------------------------------------------------- mix
mixL, mixR = L.copy(), R.copy()
# cheap ping-pong on the metallic layer + air
dly = int(0.25 * SR)
for i in range(dly, N):
    mixR[i] += mixL[i - dly] * 0.11
mixL = np.convolve(mixL, [0.6, 0.4], mode="same")
mixR = np.convolve(mixR, [0.6, 0.4], mode="same")
mix = np.stack([mixL, mixR], axis=1)
mix = np.tanh(mix * 1.25)
# hard silence, exactly as measured
for a, b in SILENCE:
    i, j = int(a * SR), min(N, int(b * SR))
    fade = int(0.004 * SR)
    mix[i:j] = 0.0
    if i - fade > 0:
        mix[i - fade:i] *= np.linspace(1, 0, fade)[:, None]
peak = np.max(np.abs(mix))
mix = mix / max(1e-9, peak) * 0.89
mix = mix.astype(np.float32)


def write_wav(path: Path, data: np.ndarray, sr: int):
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(data, -1, 1)
    pcm = (pcm * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="build/score_48k.wav")
    args = ap.parse_args()
    out = Path(args.out)
    write_wav(out, mix, SR)
    report = dict(
        path=str(out), seconds=round(N / SR, 3), sr=SR, bpm=120,
        grid_flashes=len(FLASH), grid_cuts=len(CUTS),
        silence=[[round(a, 3), round(b, 3)] for a, b in SILENCE],
        pre_normalise_peak=float(peak), out_bytes=out.stat().st_size,
        note="loudness is conformed to -13.9 LUFS / -0.3 dBTP in encode.py",
    )
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
