#!/usr/bin/env python3
"""
audio_shadow.py — WF-03 · THE SHADOW — score + sound design + voice mix, all synthesized from the picture's
event list (build/wf03_film/events.json written by film_shadow.py). 48 kHz stereo, −16.5 LUFS film mix.

layers: room tone (never breathes out) · sub drone · cello-ish pad (A minor) · piano motif (90 BPM)
        · heartbeat pulse + riser (montage/climax) · footsteps (from the animation) · typewriter clicks
        · lantern whump / huff / crackle · hard-cut booms · flash impact · 3 voice lines (ducked bed)
"""
import os, sys, json, math, re, subprocess, argparse
import numpy as np
from scipy import signal

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
BUILD = os.path.join(ROOT, 'build', 'wf03_film')
BPM = 90.0
BEAT = 60.0 / BPM
A = {'A1': 55.0, 'E2': 82.41, 'A2': 110.0, 'C3': 130.81, 'E3': 164.81, 'A3': 220.0, 'C4': 261.63, 'D4': 293.66,
     'E4': 329.63, 'G4': 392.0, 'A4': 440.0, 'C5': 523.25, 'E5': 659.26}
rng = np.random.default_rng(3)


def db(x):
    return 10 ** (x / 20)


def lp(x, fc, order=2):
    sos = signal.butter(order, min(fc, SR / 2 - 100) / (SR / 2), 'low', output='sos')
    return signal.sosfilt(sos, x).astype(np.float32)


def hp(x, fc, order=2):
    sos = signal.butter(order, max(fc, 10) / (SR / 2), 'high', output='sos')
    return signal.sosfilt(sos, x).astype(np.float32)


def bp(x, f1, f2, order=2):
    sos = signal.butter(order, [f1 / (SR / 2), min(f2, SR / 2 - 100) / (SR / 2)], 'band', output='sos')
    return signal.sosfilt(sos, x).astype(np.float32)


def env_bp(points, n):
    """breakpoint envelope: [(t, v), ...] → array of n samples"""
    t = np.arange(n) / SR
    ts = [p[0] for p in points]
    vs = [p[1] for p in points]
    return np.interp(t, ts, vs).astype(np.float32)


def tsec(n):
    return np.arange(n, dtype=np.float32) / SR


class Mix:
    def __init__(self, total):
        self.n = int(total * SR)
        self.bus = {}

    def place(self, bus, sig, t, gain=1.0, pan=0.0):
        b = self.bus.setdefault(bus, np.zeros((self.n, 2), np.float32))
        i0 = int(t * SR)
        if i0 >= self.n or i0 + len(sig) <= 0:
            return
        if i0 < 0:
            sig = sig[-i0:]
            i0 = 0
        sig = sig[:self.n - i0]
        th = (pan + 1) * math.pi / 4
        b[i0:i0 + len(sig), 0] += sig * gain * math.cos(th)
        b[i0:i0 + len(sig), 1] += sig * gain * math.sin(th)

    def place_st(self, bus, sig2, t, gain=1.0):
        b = self.bus.setdefault(bus, np.zeros((self.n, 2), np.float32))
        i0 = int(t * SR)
        if i0 < 0:
            sig2 = sig2[-i0:]
            i0 = 0
        sig2 = sig2[:self.n - i0]
        b[i0:i0 + len(sig2)] += sig2 * gain


# ───────────────────────────────────────────── instruments
def piano(f0, dur=3.2, vel=1.0, bright=1.0):
    n = int(dur * SR)
    t = tsec(n)
    out = np.zeros(n, np.float32)
    for h in range(1, 8):
        amp = (1.0 / h ** (1.25 + 0.35 * (1 - bright))) * (1 if h % 2 else 0.75)
        out += amp * np.sin(2 * math.pi * f0 * h * t * (1 + 0.0004 * h * h)) * np.exp(-t * (1.6 + 0.9 * h))
    out *= 1 - np.exp(-t * 900)                 # 1 ms attack
    hammer = lp(rng.standard_normal(int(0.012 * SR)).astype(np.float32), 2500) * np.exp(-tsec(int(0.012 * SR)) * 350)
    out[:len(hammer)] += hammer * 0.25
    out *= vel * 0.22
    return out


def pad(freqs, dur, fc=700.0, attack=2.5, release=3.0, gain=1.0, vib=0.004):
    n = int(dur * SR)
    t = tsec(n)
    L = np.zeros(n, np.float32)
    R = np.zeros(n, np.float32)
    for f in freqs:
        for det, dst in ((-0.0028, L), (0.0031, R), (0.0, L), (0.0, R)):
            ph = 2 * math.pi * f * (1 + det) * t + vib * f * np.sin(2 * math.pi * 4.7 * t + det * 100) / 4.7
            for h in range(1, 13):
                dst += (1.0 / h) * np.sin(h * ph + h * 0.3) * (0.5 if det == 0 else 0.35)
    e = np.minimum(1 - np.exp(-t / attack * 3), 1.0) * np.minimum(1.0, np.maximum(0.0, (dur - t) / release))
    L, R = lp(L, fc, 2) * e, lp(R, fc, 2) * e
    st = np.stack([L, R], 1) * (gain * 0.012)
    return st


def thump(f=58.0, dur=0.5, click=0.3):
    n = int(dur * SR)
    t = tsec(n)
    s = np.sin(2 * math.pi * f * t * (1 + 0.8 * np.exp(-t * 18))) * np.exp(-t * 9)
    s += click * lp(rng.standard_normal(n).astype(np.float32), 900) * np.exp(-t * 60)
    return (s * 0.9).astype(np.float32)


def boom(dur=1.4):
    n = int(dur * SR)
    t = tsec(n)
    s = np.sin(2 * math.pi * 46 * t * (1 + 0.5 * np.exp(-t * 6))) * np.exp(-t * 3.2)
    s += 0.6 * lp(rng.standard_normal(n).astype(np.float32), 180) * np.exp(-t * 5)
    return (s * 0.8).astype(np.float32)


def footstep(slow=False):
    dur = 0.22 if not slow else 0.4
    n = int(dur * SR)
    t = tsec(n)
    noise = rng.standard_normal(n).astype(np.float32)
    s = bp(noise, 180, 1400 if not slow else 900) * np.exp(-t * (38 if not slow else 16))
    s += 0.9 * np.sin(2 * math.pi * 75 * t) * np.exp(-t * 40)
    s += 0.25 * bp(noise, 2000, 6000) * np.exp(-t * 120)   # grit
    return (s * (0.55 if not slow else 0.45)).astype(np.float32)


def click():
    n = int(0.05 * SR)
    t = tsec(n)
    s = hp(rng.standard_normal(n).astype(np.float32), 2500) * np.exp(-t * 300)
    s += 0.5 * np.sin(2 * math.pi * 1900 * t) * np.exp(-t * 180)
    return (s * 0.5).astype(np.float32)


def stab():
    n = int(0.6 * SR)
    t = tsec(n)
    s = lp(rng.standard_normal(n).astype(np.float32), 500) * np.exp(-t * 14)
    s += 0.8 * np.sin(2 * math.pi * 190 * t * (1 + 0.3 * np.exp(-t * 20))) * np.exp(-t * 10)
    s += 0.5 * np.sin(2 * math.pi * 55 * t) * np.exp(-t * 6)
    return (s * 0.9).astype(np.float32)


def whump():
    n = int(0.9 * SR)
    t = tsec(n)
    noise = rng.standard_normal(n).astype(np.float32)
    swell = lp(noise, 420) * np.exp(-((t - 0.16) / 0.11) ** 2)
    s = swell + 0.7 * np.sin(2 * math.pi * 88 * t) * np.exp(-t * 7) * (t > 0.12)
    tick = hp(noise, 4000) * np.exp(-(t - 0.14).clip(0) * 400) * (t > 0.14)
    return (s * 0.8 + tick * 0.15).astype(np.float32)


def huff():
    n = int(0.9 * SR)
    t = tsec(n)
    s = bp(rng.standard_normal(n).astype(np.float32), 300, 1800) * np.exp(-t * 6) * (1 - np.exp(-t * 80))
    return (s * 0.5).astype(np.float32)


def crackle():
    n = int(0.04 * SR)
    t = tsec(n)
    s = hp(rng.standard_normal(n).astype(np.float32), 1800) * np.exp(-t * (150 + rng.random() * 300))
    return (s * (0.4 + 0.6 * rng.random())).astype(np.float32)


def riser(dur):
    n = int(dur * SR)
    t = tsec(n)
    noise = rng.standard_normal(n).astype(np.float32)
    out = np.zeros(n, np.float32)
    segs = 12
    for i in range(segs):
        a, b = int(i * n / segs), int((i + 1) * n / segs)
        f1 = 120 * 2 ** (2.6 * i / segs)
        out[a:b] = bp(noise[a:b], f1, f1 * 3.2)
    e = (t / dur) ** 2.2
    return (out * e * 0.6).astype(np.float32)


def heartbeat(level):
    n = int(0.5 * SR)
    t = tsec(n)
    s = np.sin(2 * math.pi * 52 * t) * np.exp(-t * 16)
    s += 0.75 * np.sin(2 * math.pi * 48 * (t - 0.17).clip(0)) * np.exp(-(t - 0.17).clip(0) * 18) * (t > 0.17)
    s += 0.2 * lp(rng.standard_normal(n).astype(np.float32), 300) * np.exp(-t * 40)
    return (s * level).astype(np.float32)


# ───────────────────────────────────────────── voice
def load_wav_mono(path):
    import wave
    w = wave.open(path, 'rb')
    sw, nch, sr = w.getsampwidth(), w.getnchannels(), w.getframerate()
    raw = w.readframes(w.getnframes())
    w.close()
    assert sw == 2 and sr == SR, (sw, sr)
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    if nch > 1:
        a = a.reshape(-1, nch).mean(1)
    return a


def trim(a, thr_db=-45, pad=0.04):
    thr = db(thr_db)
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    i0, i1 = max(0, idx[0] - int(pad * SR)), min(len(a), idx[-1] + int(pad * SR * 4))
    return a[i0:i1]


def voice_process(a):
    a = hp(a, 85)
    # de-ess: compress 5–9 kHz band
    s_band = bp(a, 5000, 9000)
    env = lp(np.abs(s_band), 40)
    red = np.minimum(1.0, 0.012 / (env + 1e-6)) ** 0.6
    a = a - s_band * (1 - red)
    # gentle compression toward −20 dBFS RMS
    rms = np.sqrt(np.mean(a * a)) + 1e-9
    a = a * (db(-20) / rms)
    a = np.tanh(a * 1.4) / 1.4
    f = int(0.02 * SR)
    a[:f] *= np.linspace(0, 1, f)
    a[-f:] *= np.linspace(1, 0, f)
    return a.astype(np.float32)


# ───────────────────────────────────────────── measurement
def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def measure_lufs(path):
    out = subprocess.run([ffmpeg(), '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    tail = out[out.rfind('Summary:'):]
    I = float(re.search(r'I:\s+(-?[\d.]+) LUFS', tail).group(1))
    lra = float(re.search(r'LRA:\s+(-?[\d.]+) LU', tail).group(1))
    tp = float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', tail).group(1))
    return I, lra, tp


def write_wav(path, st):
    import wave
    w = wave.open(path, 'wb')
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    CH = SR * 10
    for i0 in range(0, len(st), CH):
        w.writeframes((np.clip(st[i0:i0 + CH], -1, 1) * 32767).astype(np.int16).tobytes())
    w.close()


# ───────────────────────────────────────────── build
def build(ev, out_wav, vo_paths):
    total = ev['total'] + 0.4
    M = Mix(total)
    n = M.n
    cuts = ev['cuts']
    main_cuts = [c for c in cuts if not (ev['montage'][0] - 0.01 < c < ev['climax'][1] + 0.01)]
    lamp_on1, lamp_off1, lamp_on2 = 3.333, 39.5, 57.042
    wall = ev['wall_touch']
    lift, setdown, end_card = ev['lift'], ev['setdown'], ev['end_card']
    vo = {v['id']: v['t'] for v in ev['vo']}

    # 1 · room tone — constant, decorrelated, never breathes out (fades only in the last 1.5 s)  [chunked, float32]
    # 2 · sub drone 55 Hz (+ 41.2 Hz E1 in the dark), slow LFO                                   [chunked, float32]
    e_sub_pts = [(0, 0), (lamp_on1, 0), (lamp_on1 + 8, 0.55), (lamp_off1 - 1, 0.7), (lamp_off1, 0.9), (lamp_on2, 1.0),
                 (ev['montage'][0], 0.8), (ev['climax'][1], 1.0), (ev['climax'][1] + 0.05, 0.25), (wall - 0.7, 0.9),
                 (wall, 0.0), (wall + 0.5, 0.6), (wall + 17, 0.35), (lift, 0.5), (end_card - 1, 0.4), (end_card + 3.5, 0.0), (total, 0)]
    e_E_pts = [(0, 0), (lamp_off1, 0), (lamp_off1 + 2, 1), (lamp_on2 - 0.5, 1), (lamp_on2 + 1.5, 0), (total, 0)]
    rt_pts = [(0, 1), (total - 1.6, 1), (total - 0.1, 0), (total, 0)]
    sos = signal.butter(2, 380 / (SR / 2), 'low', output='sos')
    ziL = signal.sosfilt_zi(sos) * 0
    ziR = signal.sosfilt_zi(sos) * 0
    bed = M.bus.setdefault('bed', np.zeros((n, 2), np.float32))
    CH = SR * 4
    for i0 in range(0, n, CH):
        i1 = min(n, i0 + CH)
        tt = np.arange(i0, i1, dtype=np.float64) / SR
        nl, ziL = signal.sosfilt(sos, rng.standard_normal(i1 - i0), zi=ziL)
        nr, ziR = signal.sosfilt(sos, rng.standard_normal(i1 - i0), zi=ziR)
        g = np.interp(tt, [p[0] for p in rt_pts], [p[1] for p in rt_pts]) * db(-44)
        bed[i0:i1, 0] += (nl * g).astype(np.float32)
        bed[i0:i1, 1] += (nr * g).astype(np.float32)
        es = np.interp(tt, [p[0] for p in e_sub_pts], [p[1] for p in e_sub_pts])
        eE = np.interp(tt, [p[0] for p in e_E_pts], [p[1] for p in e_E_pts])
        sub = np.sin(2 * math.pi * 55.0 * tt) * (1 + 0.18 * np.sin(2 * math.pi * 0.09 * tt)) * es + np.sin(2 * math.pi * 41.2 * tt + 0.7) * eE * 0.9
        sub = (sub * db(-19) * 0.7071).astype(np.float32)
        bed[i0:i1, 0] += sub
        bed[i0:i1, 1] += sub

    # 3 · pad — A minor, four passages
    M.place_st('bed', pad([A['A2'], A['E3']], lamp_off1 - 13.5, fc=520, attack=4, release=3, gain=0.9), 13.5)
    M.place_st('bed', pad([A['A2'], A['E3']], wall - 0.6 - (lamp_on2 + 1.5), fc=760, attack=3, release=0.5, gain=1.6), lamp_on2 + 1.5)
    M.place_st('bed', pad([A['A2'], A['E3'], A['C4']], 17.0, fc=900, attack=0.4, release=5, gain=2.0), wall + 0.45)
    M.place_st('bed', pad([A['A2'], A['E3'], A['A3']], end_card - (wall + 20) + 2.5, fc=620, attack=5, release=4, gain=1.1), wall + 20)
    # bright swell into the flash (pad rising)
    M.place_st('bed', pad([A['A2'], A['E3']], 1.2, fc=1800, attack=1.1, release=0.1, gain=2.4), wall - 1.25)

    # 4 · piano motif (90 BPM)  M = A3 C4 E4 D4 on beats 0 1 2 3.5
    def motif(t0, notes, beats, vel=0.8, bright=1.0):
        for nt, bt in zip(notes, beats):
            M.place('bed', piano(A[nt], vel=vel * (0.9 + 0.2 * rng.random()), bright=bright), t0 + bt * BEAT, 1.3, 0.08 * rng.standard_normal())
    motif(14.2, ['A3', 'C4', 'E4', 'D4'], [0, 1, 2, 3.5], 0.7)
    motif(24.4, ['A3', 'C4', 'E4', 'D4'], [0, 1, 2, 3.5], 0.75)
    motif(33.6, ['A3', 'C4', 'E4', 'C4'], [0, 1, 2, 3.5], 0.7)
    motif(46.0, ['E4'], [0], 0.55, 0.6)
    motif(53.8, ['A3'], [0], 0.5, 0.6)
    motif(61.6, ['A4', 'C5', 'E5', 'D4'], [0, 1, 2, 3.5], 0.7)
    for i, t0 in enumerate(np.arange(ev['montage'][0] + 0.3, ev['climax'][0] - 0.5, 4 * BEAT)):
        motif(t0, ['A3', 'C4', 'E4', 'D4'], [0, 1, 2, 3.5], 0.65 + 0.08 * i, 1.0)
    motif(ev['climax'][0], ['E4', 'E4', 'E4'], [0, 0.5, 1.0], 0.8)
    motif(wall + 0.5, ['E4', 'D4', 'C4', 'A3'], [0, 1, 2, 3.5], 0.85, 0.8)
    motif(wall + 6.5, ['A3'], [0], 0.6, 0.6)
    motif(lift + 2.0, ['A3', 'C4', 'E4'], [0, 1, 2], 0.6, 0.7)
    motif(setdown + 1.2, ['E4', 'A4'], [0, 1.5], 0.6, 0.7)
    motif(end_card + 0.8, ['A3'], [0], 0.5, 0.5)

    # 5 · heartbeat pulse (montage → climax), riser, hard stop at the climax end
    m0, m1 = ev['montage'][0], ev['climax'][1]
    tb = m0
    while tb < m1 - 0.05:
        lvl = 0.25 + 0.75 * (tb - m0) / (m1 - m0)
        M.place('bed', heartbeat(lvl), tb, db(-19))
        tb += BEAT if tb < ev['climax'][0] else BEAT / 2
    M.place('bed', riser(5.0), m1 - 5.0, db(-23))

    # 6 · footsteps from the animation
    for s in ev['steps']:
        slow = ev['climax'][1] < s['t'] < wall
        M.place('bed', footstep(slow), s['t'], db(-21 + rng.uniform(-2, 1.5)), float(np.clip(s['u'] * 0.7, -0.6, 0.6)))

    # 7 · typewriter clicks (skip the ones that are only a shot-start reveal) + red-card stabs
    last = -1
    for c in ev['clicks']:
        if any(abs(c - k) < 0.1 for k in cuts) or c - last < 0.03:
            continue
        M.place('bed', click(), c, db(-24 + rng.uniform(-2, 2)), 0.35)
        last = c
    for j, c in enumerate(cuts):
        if ev['climax'][0] - 0.01 < c < ev['climax'][1] - 0.01 and j % 2 == 0:
            M.place('bed', stab(), c, db(-20))

    # 8 · lantern: whump on, huff off, crackle while lit
    M.place('bed', whump(), lamp_on1 - 0.15, db(-18))
    M.place('bed', whump(), lamp_on2 - 0.12, db(-17))
    M.place('bed', huff(), lamp_off1 - 0.45, db(-22))
    for (a, b) in ((lamp_on1 + 0.5, lamp_off1 - 0.3), (lamp_on2 + 0.5, end_card - 7.5)):
        tc = a
        while tc < b:
            M.place('bed', crackle(), tc, db(-40 + rng.uniform(-4, 2)), -0.5 if tc < lift else 0.2)
            tc += 0.25 + rng.exponential(0.7)

    # 9 · hard-cut booms (main cuts only; montage cuts get a softer tick-boom)
    for c in main_cuts:
        if c < 1 or abs(c - wall) < 0.01:
            continue
        M.place('bed', boom(), c, db(-25 + rng.uniform(-2, 1)))
    for c in cuts:
        if ev['montage'][0] < c < ev['climax'][0] + 0.01:
            M.place('bed', boom(0.6), c, db(-30))

    # 10 · the touch: reverse swell → impact → half a second of near silence
    rs_n = int(0.8 * SR)
    rsw = lp(rng.standard_normal(rs_n).astype(np.float32), 1200) * (tsec(rs_n) / 0.8) ** 3
    M.place('bed', rsw, wall - 0.8, db(-22))
    M.place('bed', thump(44, 1.2, 0.5), wall, db(-16))
    M.place('bed', click(), wall, db(-20))
    # lamp pick-up / set-down handling foley
    M.place('bed', thump(120, 0.25, 0.8), lift - 0.1, db(-26))
    M.place('bed', crackle(), lift, db(-24))
    M.place('bed', thump(110, 0.3, 0.9), setdown, db(-24))
    M.place('bed', click(), setdown + 0.02, db(-28))

    # 11 · voice
    vo_sig = {}
    for vid, path in vo_paths.items():
        a = voice_process(trim(load_wav_mono(path)))
        vo_sig[vid] = a
        M.place('vo', a, vo[vid], db(0.0), 0.0)
    # bed ducking under the voice (−5 dB; 0.25 s attack, 0.9 s release) — one-pole smoothing, O(n), float32
    duck = np.ones(n, np.float32)
    for vid, a in vo_sig.items():
        i0 = int(vo[vid] * SR)
        i1 = i0 + len(a)
        duck[max(0, i0):i1] = db(-5)
    ar_ = math.exp(-1.0 / (0.9 * SR))
    rel = signal.lfilter([1 - ar_], [1, -ar_], duck).astype(np.float32)            # slow rise after the voice (release)
    duck = np.minimum(duck, rel)
    aa = math.exp(-1.0 / (0.25 * SR))
    att = signal.lfilter([1 - aa], [1, -aa], duck[::-1])[::-1].astype(np.float32)   # smooth dive before the voice (attack)
    duck = np.minimum(duck, att).astype(np.float32)
    del rel, att

    # ── master (in place)
    bed = M.bus['bed']
    bed *= duck[:, None]
    del duck
    if 'vo' in M.bus:
        bed += M.bus['vo']
        del M.bus['vo']
    # the half second of near-silence right after the touch
    i0, i1 = int((wall + 0.02) * SR), int((wall + 0.42) * SR)
    bed[i0:i1] *= env_bp([(0, 0.08), (0.3, 0.08), (0.4, 1.0)], i1 - i0)[:, None]
    # soft limiter + final 1.5 s fade to digital silence
    np.tanh(bed * 1.1, out=bed)
    bed *= (1 / 1.1)
    i0 = int((total - 1.5) * SR)
    bed[i0:] *= np.linspace(1, 0, n - i0, dtype=np.float32)[:, None]
    write_wav(out_wav, bed)
    return out_wav


def limiter(a, thr_db=-1.5, look_ms=5.0, rel_ms=80.0):
    """transparent peak limiter: look-ahead min-filter gain + one-pole release (in place)"""
    from scipy.ndimage import minimum_filter1d
    thr = db(thr_db)
    env = np.maximum(np.abs(a[:, 0]), np.abs(a[:, 1]))
    g = np.minimum(1.0, thr / np.maximum(env, 1e-6)).astype(np.float32)
    del env
    w = int(look_ms * SR / 1000)
    g = minimum_filter1d(g, size=2 * w + 1, mode='nearest')
    ar_ = math.exp(-1.0 / (rel_ms * SR / 1000))
    rel = signal.lfilter([1 - ar_], [1, -ar_], g).astype(np.float32)
    g = np.minimum(g, rel)
    del rel
    a *= g[:, None]
    return float(np.mean(g < 0.999)) * 100.0      # % of samples under gain reduction


def normalize(in_wav, out_wav, target=-16.5):
    I, lra, tp = measure_lufs(in_wav)
    g = target - I
    print(f'pre-norm I={I:.2f} LUFS  LRA={lra:.1f}  TP={tp:.2f} dBTP → gain {g:+.2f} dB')
    a = load_stereo(in_wav)
    a *= db(g)
    pct = limiter(a)
    write_wav(out_wav, a)
    I2, lra2, tp2 = measure_lufs(out_wav)
    if abs(I2 - target) > 0.15:                      # one correction pass
        a *= db(target - I2)
        pct = max(pct, limiter(a))
        write_wav(out_wav, a)
        I2, lra2, tp2 = measure_lufs(out_wav)
    print(f'post-norm I={I2:.2f} LUFS  LRA={lra2:.1f}  TP={tp2:.2f} dBTP  limiter active {pct:.3f}% of samples')
    return dict(lufs=I2, lra=lra2, true_peak=tp2, limiter_pct=round(pct, 3))


def load_stereo(path):
    import wave
    w = wave.open(path, 'rb')
    raw = w.readframes(w.getnframes())
    nch = w.getnchannels()
    w.close()
    return np.frombuffer(raw, np.int16).astype(np.float32).reshape(-1, nch) / 32768


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--events', default=os.path.join(BUILD, 'events.json'))
    ap.add_argument('--out', default=os.path.join(BUILD, 'mix.wav'))
    args = ap.parse_args()
    ev = json.load(open(args.events))
    vo_paths = {f'vo{i}': os.path.join(BUILD, f'vo{i}.wav') for i in (1, 2, 3)}
    raw = build(ev, os.path.join(BUILD, 'mix_raw.wav'), vo_paths)
    stats = normalize(raw, args.out)
    json.dump(stats, open(os.path.join(BUILD, 'mix_stats.json'), 'w'))
    print('mix →', args.out, stats)
