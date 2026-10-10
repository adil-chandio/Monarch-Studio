#!/usr/bin/env python3
"""
audio_window.py — WF-03 · THE WINDOW (film #2) — score + sound design + voice mix, synthesized from the picture's
event list (data/events_window.json written by film_window.py --events). 48 kHz stereo, −16.5 LUFS film mix.

Own DNA (≠ THE SHADOW): D minor → D major (Picardy third at the amber window), 72 BPM, felt piano + music-box bells
(one bell per window) + warm pad + muted bass pulse for the work montage + string swell at dawn.
World: rain in two perspectives (exterior patter / interior muffled + drops on the glass), room tone that never
breathes out, a bedroom clock that ticks until 88.0 and never again, phone thumb-taps, bed creak, wood-floor steps,
chores foley (sheets, water + plates, papers, sneakers), dawn birds, lamp click, the couple's kitchen behind glass,
a chair creak, running steps + breath, red-line stings, typewriter clicks from the events text, 10 VO clips (voice-03).
"""
import os, sys, json, math, subprocess, argparse
import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audio_shadow as A0  # noqa: E402  (instrument + mix primitives, measurement, limiter, normalize)
from audio_shadow import (SR, db, lp, hp, bp, env_bp, tsec, Mix, pad, thump, boom, click, stab, riser,  # noqa: E402
                          load_wav_mono, measure_lufs, write_wav, normalize)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
WF = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, 'build', 'wf03_window')
BPM = 72.0
BEAT = 60.0 / BPM
rng = np.random.default_rng(11)
N = {'D2': 73.42, 'F2': 87.31, 'G2': 98.0, 'A2': 110.0, 'Bb2': 116.54, 'C3': 130.81, 'D3': 146.83, 'F3': 174.61,
     'F#3': 185.0, 'G3': 196.0, 'A3': 220.0, 'Bb3': 233.08, 'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'E4': 329.63,
     'F4': 349.23, 'F#4': 369.99, 'G4': 392.0, 'A4': 440.0, 'Bb4': 466.16, 'C5': 523.25, 'C#5': 554.37, 'D5': 587.33,
     'E5': 659.26, 'F5': 698.46, 'F#5': 739.99, 'G5': 783.99, 'A5': 880.0, 'C6': 1046.5, 'D6': 1174.66, 'F#6': 1479.98}


# ───────────────────────────────────────────── instruments (new for this film)
def felt(f0, dur=3.6, vel=1.0):
    """felt piano: soft 8 ms attack, few partials, dark top, slow decay"""
    n = int(dur * SR)
    t = tsec(n)
    out = np.zeros(n, np.float32)
    for h in range(1, 6):
        amp = 1.0 / h ** 1.9
        out += amp * np.sin(2 * math.pi * f0 * h * t * (1 + 0.0003 * h * h)) * np.exp(-t * (1.1 + 0.8 * h))
    out *= 1 - np.exp(-t * 120)
    out = lp(out, 1800, 2)
    thud = lp(rng.standard_normal(int(0.03 * SR)).astype(np.float32), 400) * np.exp(-tsec(int(0.03 * SR)) * 120)
    out[:len(thud)] += thud * 0.12
    return (out * vel * 0.26).astype(np.float32)


def bell(f0, dur=2.6, vel=1.0):
    """music-box bell: fundamental + inharmonic 2.76× partial, instant attack, long clean decay"""
    n = int(dur * SR)
    t = tsec(n)
    s = np.sin(2 * math.pi * f0 * t) * np.exp(-t * 1.9)
    s += 0.35 * np.sin(2 * math.pi * f0 * 2.76 * t) * np.exp(-t * 6.5)
    s += 0.12 * np.sin(2 * math.pi * f0 * 5.4 * t) * np.exp(-t * 14)
    s *= 1 - np.exp(-t * 2500)
    return (s * vel * 0.16).astype(np.float32)


def pluck(f0, dur=0.7, vel=1.0):
    """muted bass pluck (work-montage pulse)"""
    n = int(dur * SR)
    t = tsec(n)
    s = np.sin(2 * math.pi * f0 * t) * np.exp(-t * 7) + 0.4 * np.sin(2 * math.pi * f0 * 2 * t) * np.exp(-t * 16)
    s += 0.25 * lp(rng.standard_normal(n).astype(np.float32), 700) * np.exp(-t * 90)
    s *= 1 - np.exp(-t * 600)
    return (s * vel * 0.5).astype(np.float32)


def strings(freqs, dur, fc=1400.0, attack=3.0, release=3.0, gain=1.0):
    """bowed-ish ensemble: detuned saw-like partial stacks, slow bow attack, wide"""
    n = int(dur * SR)
    t = tsec(n)
    L = np.zeros(n, np.float32)
    R = np.zeros(n, np.float32)
    for f in freqs:
        for det, dst in ((-0.004, L), (0.0035, R), (-0.0012, R), (0.0015, L)):
            ph = 2 * math.pi * f * (1 + det) * t + 0.003 * f * np.sin(2 * math.pi * 5.1 * t + det * 300) / 5.1
            for h in range(1, 9):
                dst += (1.0 / h) * np.sin(h * ph + h * 0.7)
    e = np.minimum(1 - np.exp(-t / attack * 3), 1.0) * np.clip((dur - t) / release, 0, 1)
    L, R = lp(L, fc, 2) * e, lp(R, fc, 2) * e
    return (np.stack([L, R], 1) * (gain * 0.010)).astype(np.float32)


# ───────────────────────────────────────────── foley
def tick(kind=0):
    """clock: tick (kind 0) / tock (kind 1) — tiny mechanical transient"""
    n = int(0.03 * SR)
    t = tsec(n)
    f = 3200 if kind == 0 else 2600
    s = hp(rng.standard_normal(n).astype(np.float32), 1800) * np.exp(-t * 500)
    s += 0.5 * np.sin(2 * math.pi * f * t) * np.exp(-t * 350)
    return (s * 0.35).astype(np.float32)


def tap():
    """thumb on a phone screen: soft, dull, short"""
    n = int(0.04 * SR)
    t = tsec(n)
    s = bp(rng.standard_normal(n).astype(np.float32), 900, 3200) * np.exp(-t * 260)
    return (s * 0.3).astype(np.float32)


def creak(dur=0.45, f=160.0):
    """bed / chair creak: frequency-wobbling buzz under a noise band"""
    n = int(dur * SR)
    t = tsec(n)
    fm = f * (1 + 0.25 * np.sin(2 * math.pi * 3.0 * t) * (1 - t / dur))
    ph = 2 * math.pi * np.cumsum(fm) / SR
    s = (signal.sawtooth(ph) * 0.4 + bp(rng.standard_normal(n).astype(np.float32), 500, 2500) * 0.4)
    e = np.sin(math.pi * np.clip(t / dur, 0, 1)) ** 0.7
    return (lp(s * e, 2600) * 0.32).astype(np.float32)


def woodstep(hard=0.5):
    """bare foot / sock on a wooden floor: dull thud + short board resonance"""
    n = int(0.3 * SR)
    t = tsec(n)
    s = lp(rng.standard_normal(n).astype(np.float32), 500 + 900 * hard) * np.exp(-t * 32)
    s += 0.9 * np.sin(2 * math.pi * (90 + 30 * hard) * t) * np.exp(-t * 36)
    s += 0.15 * bp(rng.standard_normal(n).astype(np.float32), 900, 2500) * np.exp(-t * 90) * hard
    return (s * 0.45).astype(np.float32)


def runstep(wet=0.5):
    """sneaker on wet asphalt: slap + splash grit"""
    n = int(0.22 * SR)
    t = tsec(n)
    noise = rng.standard_normal(n).astype(np.float32)
    s = bp(noise, 200, 1600) * np.exp(-t * 40)
    s += 0.7 * np.sin(2 * math.pi * 85 * t) * np.exp(-t * 45)
    s += wet * 0.5 * bp(noise, 2500, 8000) * np.exp(-t * 55) * (1 - np.exp(-t * 400))
    return (s * 0.5).astype(np.float32)


def breath(inhale=True, dur=0.5):
    n = int(dur * SR)
    t = tsec(n)
    f1, f2 = (600, 2600) if inhale else (300, 1500)
    s = bp(rng.standard_normal(n).astype(np.float32), f1, f2)
    e = np.sin(math.pi * np.clip(t / dur, 0, 1)) ** (1.4 if inhale else 0.9)
    return (s * e * 0.22).astype(np.float32)


def fabric(dur=0.5):
    n = int(dur * SR)
    t = tsec(n)
    s = bp(rng.standard_normal(n).astype(np.float32), 400, 3200)
    e = np.sin(math.pi * np.clip(t / dur, 0, 1)) ** 1.3 * (1 + 0.5 * np.sin(2 * math.pi * 9 * t))
    return (s * e * 0.28).astype(np.float32)


def clink(f=2900.0):
    n = int(0.35 * SR)
    t = tsec(n)
    s = np.sin(2 * math.pi * f * t) * np.exp(-t * 18) + 0.5 * np.sin(2 * math.pi * f * 1.48 * t) * np.exp(-t * 30)
    s += 0.2 * hp(rng.standard_normal(n).astype(np.float32), 3000) * np.exp(-t * 200)
    return (s * 0.3).astype(np.float32)


def water(dur):
    """tap running into a steel sink: bright noise with 2 modulations, chunk-safe (short)"""
    n = int(dur * SR)
    t = tsec(n)
    s = bp(rng.standard_normal(n).astype(np.float32), 700, 6000)
    m = 1 + 0.25 * np.sin(2 * math.pi * 13 * t) + 0.15 * np.sin(2 * math.pi * 31 * t + 1)
    e = np.minimum(1, t / 0.25) * np.clip((dur - t) / 0.3, 0, 1)
    return (s * m * e * 0.2).astype(np.float32)


def paper():
    n = int(0.28 * SR)
    t = tsec(n)
    s = bp(rng.standard_normal(n).astype(np.float32), 1200, 6000)
    e = np.sin(math.pi * np.clip(t / 0.28, 0, 1)) ** 2 * (1 + 0.6 * np.sin(2 * math.pi * 23 * t))
    return (s * e * 0.25).astype(np.float32)


def scuff():
    n = int(0.2 * SR)
    t = tsec(n)
    s = bp(rng.standard_normal(n).astype(np.float32), 600, 4000) * np.exp(-t * 25)
    s += 0.5 * np.sin(2 * math.pi * 1400 * t * (1 - 0.5 * t / 0.2)) * np.exp(-t * 40) * 0.4
    return (s * 0.3).astype(np.float32)


def lamp_click():
    n = int(0.08 * SR)
    t = tsec(n)
    s = hp(rng.standard_normal(n).astype(np.float32), 1500) * np.exp(-t * 220)
    s += 0.8 * np.sin(2 * math.pi * 1100 * t) * np.exp(-t * 300)
    s[int(0.03 * SR):] += 0.5 * np.sin(2 * math.pi * 900 * t[:n - int(0.03 * SR)]) * np.exp(-t[:n - int(0.03 * SR)] * 250)
    return (s * 0.6).astype(np.float32)


def chirp():
    """one bird syllable: fast FM sweep, 60–140 ms"""
    dur = 0.06 + 0.08 * rng.random()
    n = int(dur * SR)
    t = tsec(n)
    f0 = 2600 + 1400 * rng.random()
    sweep = f0 * (1 + 0.25 * np.sin(2 * math.pi * (8 + 10 * rng.random()) * t) + 0.3 * (t / dur) * (rng.random() - 0.5))
    ph = 2 * math.pi * np.cumsum(sweep) / SR
    s = np.sin(ph) * np.sin(math.pi * t / dur) ** 1.5
    return (s * 0.18).astype(np.float32)


def sting(dur=0.7):
    """red-line sting: reversed noise swell → low thud + dissonant C# bell"""
    n = int(dur * SR)
    t = tsec(n)
    sw = lp(rng.standard_normal(n).astype(np.float32), 1500) * (t / dur) ** 2.5
    out = np.zeros(n + int(1.2 * SR), np.float32)
    out[:n] += sw * 0.6
    th = thump(52, 0.9, 0.2)
    out[n:n + len(th)] += th * 0.8
    b = bell(N['C#5'], 1.2, 0.5)
    out[n:n + len(b)] += b
    return out


def phone_off():
    """tiny capacitor-whine falling into silence"""
    n = int(0.25 * SR)
    t = tsec(n)
    f = 4200 * np.exp(-t * 12)
    ph = 2 * math.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 14)
    return (s * 0.12).astype(np.float32)


def drop_sine(f0=80.0, f1=38.0, dur=1.3):
    n = int(dur * SR)
    t = tsec(n)
    f = f0 * (f1 / f0) ** (t / dur)
    ph = 2 * math.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t * 2.2) * 0.8).astype(np.float32)


def air(dur=1.6):
    """soft air-swell for a push-in (no whoosh): slow band of filtered noise"""
    n = int(dur * SR)
    t = tsec(n)
    s = bp(rng.standard_normal(n).astype(np.float32), 300, 1800)
    e = np.sin(math.pi * np.clip(t / dur, 0, 1)) ** 2
    return (s * e * 0.25).astype(np.float32)


def voice_process(a):
    """hp 85 · de-ess 5–9 kHz (env clamped ≥0 — the film #1 version could go NaN on filter ringing) · level to −20 dBFS RMS · soft knee"""
    a = hp(a, 85)
    s_band = bp(a, 5000, 9000)
    env = np.maximum(lp(np.abs(s_band), 40), 0.0)
    red = np.minimum(1.0, 0.012 / (env + 1e-6)) ** 0.6
    a = a - s_band * (1 - red)
    rms = np.sqrt(np.mean(a * a)) + 1e-9
    a = a * (db(-20) / rms)
    a = np.tanh(a * 1.4) / 1.4
    f = int(0.02 * SR)
    a[:f] *= np.linspace(0, 1, f)
    a[-f:] *= np.linspace(1, 0, f)
    return a.astype(np.float32)


# ───────────────────────────────────────────── perspective schedule
def rain_schedule(shots):
    """per-shot (exterior, interior) rain gains → breakpoint lists with 0.12 s ramps at the cuts"""
    EXT = {0: (0, 1), 1: (0, 1), 2: (1, 0), 3: (1, 0), 4: (1, 0), 5: (0.5, 0), 6: (1, 0), 7: (1, 0), 8: (1, 0), 9: (1, 0),
           10: (1, 0), 11: (1, 0), 12: (0, 1), 13: (0.7, 0.5), 14: (0.3, 0.2), 15: (1.2, 0), 16: (1.2, 0), 17: (1.2, 0),
           18: (1.2, 0), 19: (1.0, 0), 20: (0, 1), 21: (0, 1), 22: (1.0, 0), 23: (0, 1.15), 24: (0, 1.3), 25: (0, 1.3),
           26: (0, 1.1), 27: (0, 0.6), 28: (0, 0.9), 29: (0, 0.7), 30: (0, 0.9), 31: (0, 0.9), 32: (0.5, 0), 33: (0, 0.6),
           34: (0.8, 0), 35: (0.8, 0), 36: (0.55, 0), 37: (0.25, 0), 38: (0.22, 0), 39: (0, 0.3), 40: (0, 0.3),
           41: (0.18, 0), 42: (0, 0), 43: (0, 0), 44: (0, 0)}
    ext, inn = [], []
    for s in shots:
        gx, gi = EXT[s['i']]
        t0, t1 = s['t0'], s['t1']
        ext += [(t0 + 0.06, gx), (t1 - 0.06, gx)]
        inn += [(t0 + 0.06, gi), (t1 - 0.06, gi)]
    return ext, inn


# ───────────────────────────────────────────── build
def build(ev, out_wav, vo_paths):
    total = ev['duration']
    M = Mix(total)
    n = M.n
    cuts = ev['cuts']
    shots = ev['shots']
    vo = ev['vo']
    light = {d['what']: d['t'] for d in ev['light']}
    PHONE_OFF, WIN_OFF, LAMP_ON, AMBER = light['phone_off'], light['own_window_off'], light['lamp_on'], light['own_window_amber']
    CLOCK_STOP = 88.0
    bed = M.bus.setdefault('bed', np.zeros((n, 2), np.float32))

    # 1 · room tone + two rain perspectives + dawn air  (chunked, float32)
    ext_pts, in_pts = rain_schedule(shots)
    rt_pts = [(0, 1), (141.6, 1), (146.0, 0.6), (total - 1.6, 0.6), (total - 0.1, 0), (total, 0)]
    dawn_pts = [(0, 0), (123.0, 0), (126.0, 1), (141.6, 1), (144.0, 0), (total, 0)]
    sos_rt = signal.butter(2, 300 / (SR / 2), 'low', output='sos')
    sos_ext = signal.butter(2, [900 / (SR / 2), 7000 / (SR / 2)], 'band', output='sos')
    sos_in = signal.butter(2, [250 / (SR / 2), 1500 / (SR / 2)], 'band', output='sos')
    sos_pat = signal.butter(1, 14 / (SR / 2), 'low', output='sos')
    sos_dawn = signal.butter(2, [1500 / (SR / 2), 5000 / (SR / 2)], 'band', output='sos')
    zi = {k: signal.sosfilt_zi(s_) * 0 for k, s_ in (('rtL', sos_rt), ('rtR', sos_rt), ('exL', sos_ext), ('exR', sos_ext),
                                                     ('inL', sos_in), ('inR', sos_in), ('paL', sos_pat), ('paR', sos_pat),
                                                     ('dwL', sos_dawn), ('dwR', sos_dawn))}
    CH = SR * 4
    for i0 in range(0, n, CH):
        i1 = min(n, i0 + CH)
        m = i1 - i0
        tt = np.arange(i0, i1, dtype=np.float64) / SR
        g_rt = np.interp(tt, [p[0] for p in rt_pts], [p[1] for p in rt_pts]) * db(-45)
        g_ex = np.interp(tt, [p[0] for p in ext_pts], [p[1] for p in ext_pts]) * db(-33)
        g_in = np.interp(tt, [p[0] for p in in_pts], [p[1] for p in in_pts]) * db(-35)
        g_dw = np.interp(tt, [p[0] for p in dawn_pts], [p[1] for p in dawn_pts]) * db(-50)
        for ch, (kr, ke, ki, kp, kd) in enumerate((('rtL', 'exL', 'inL', 'paL', 'dwL'), ('rtR', 'exR', 'inR', 'paR', 'dwR'))):
            w = rng.standard_normal(m)
            rt, zi[kr] = signal.sosfilt(sos_rt, w, zi=zi[kr])
            w2 = rng.standard_normal(m)
            ex, zi[ke] = signal.sosfilt(sos_ext, w2, zi=zi[ke])
            pat, zi[kp] = signal.sosfilt(sos_pat, rng.standard_normal(m), zi=zi[kp])
            pat = 1 + 0.9 * np.clip(pat * 12, -0.9, 2.0)          # patter: slow random density modulation
            inn, zi[ki] = signal.sosfilt(sos_in, w2, zi=zi[ki])
            dw, zi[kd] = signal.sosfilt(sos_dawn, rng.standard_normal(m), zi=zi[kd])
            bed[i0:i1, ch] += (rt * g_rt + ex * pat * g_ex + inn * pat * g_in * 1.6 + dw * g_dw).astype(np.float32)
    # drops on the glass (interior perspective only; denser at the window 82–92.9)
    tdrop = 0.3
    while tdrop < total:
        gi = float(np.interp(tdrop, [p[0] for p in in_pts], [p[1] for p in in_pts]))
        if gi > 0.05:
            d_ = clink(1800 + 1400 * rng.random())[:int(0.12 * SR)] * np.exp(-tsec(int(0.12 * SR)) * 40)
            M.place('bed', d_, tdrop, db(-36 + rng.uniform(-6, 2)) * gi, rng.uniform(-0.7, 0.7))
        tdrop += rng.exponential(0.9 if not (82 < tdrop < 92.9) else 0.45) + 0.15

    # 2 · sub drone — D2 (73.4 Hz) under the dark, with the drops at the lights
    e_sub = [(0, 0), (6.6, 0), (9.0, 0.5), (12.6, 0.8), (16.4, 0.6), (20.2, 0.7), (42.4, 0.9), (45.7, 1.0), (45.75, 0.0),
             (46.5, 0.0), (48.0, 0.6), (69.3, 0.6), (PHONE_OFF, 0.7), (PHONE_OFF + 0.05, 0.0), (WIN_OFF, 0.0), (WIN_OFF + 0.4, 0.5),
             (83.6, 0.5), (CLOCK_STOP, 0.6), (CLOCK_STOP + 0.1, 0.0), (94.2, 0.0), (103.6, 0.4), (123.6, 0.4), (131.0, 0.2),
             (141.6, 0.2), (146.6, 0.0), (total, 0)]
    for i0 in range(0, n, CH):
        i1 = min(n, i0 + CH)
        tt = np.arange(i0, i1, dtype=np.float64) / SR
        es = np.interp(tt, [p[0] for p in e_sub], [p[1] for p in e_sub])
        sub = np.sin(2 * math.pi * 73.42 * tt) * (1 + 0.15 * np.sin(2 * math.pi * 0.07 * tt)) * es
        sub = (sub * db(-22) * 0.7071).astype(np.float32)
        bed[i0:i1, 0] += sub
        bed[i0:i1, 1] += sub

    # 3 · harmony — pads / strings  (D minor world → Bb major lit room → D MAJOR at the amber window)
    M.place_st('bed', pad([N['D3'], N['A3']], 20.2 - 16.9 + 2.5, fc=520, attack=1.8, release=2.5, gain=0.9), 16.9)
    M.place_st('bed', pad([N['D3'], N['F3'], N['A3']], 42.4 - 20.2 + 0.4, fc=560, attack=2.5, release=1.2, gain=1.0), 20.2)
    M.place_st('bed', pad([N['Bb2'], N['F3'], N['D4']], 63.9 - 46.5, fc=640, attack=1.6, release=2.5, gain=1.15), 46.5)
    M.place_st('bed', pad([N['A2'], N['E4']], PHONE_OFF - 63.9, fc=520, attack=2.0, release=0.15, gain=0.9), 63.9)
    M.place_st('bed', pad([N['A4'], N['D5']], CLOCK_STOP - 83.6 + 1.6, fc=1500, attack=4.0, release=1.6, gain=0.5), 83.6)
    M.place_st('bed', pad([N['D3'], N['A3'], N['D4']], 103.6 - 93.0, fc=600, attack=1.2, release=1.5, gain=0.95), 93.0)
    M.place_st('bed', strings([N['D3'], N['F3'], N['A3']], 108.4 - 103.6 + 0.6, fc=1100, attack=2.6, release=0.8, gain=1.0), 103.6)
    M.place_st('bed', strings([N['F3'], N['A3'], N['C4']], 111.6 - 108.4 + 0.5, fc=1200, attack=1.2, release=0.8, gain=0.9), 108.4)
    M.place_st('bed', strings([N['Bb2'], N['D3'], N['F3'], N['Bb3']], 118.4 - 111.6 + 0.5, fc=1250, attack=1.5, release=0.8, gain=1.0), 111.6)
    M.place_st('bed', strings([N['C3'], N['E4'], N['G4']], AMBER - 118.4, fc=1500, attack=1.4, release=0.25, gain=1.25), 118.4)
    M.place_st('bed', strings([N['D3'], N['F#3'], N['A3'], N['D4'], N['F#4']], 135.0 - AMBER, fc=2000, attack=0.6, release=2.0, gain=1.6), AMBER)
    M.place_st('bed', strings([N['D3'], N['A3'], N['D4'], N['F#4'], N['A4']], 141.6 - 135.0 + 1.0, fc=2200, attack=1.0, release=2.5, gain=1.7), 135.0)
    M.place_st('bed', pad([N['D3'], N['F#3'], N['A3']], 150.8 - 141.6, fc=700, attack=2.0, release=4.5, gain=1.0), 141.6)

    # 4 · bells — one bell per window (the count), the window motifs, the dawn arpeggios
    cnt = ev['counter'][0]
    scale = [N['D5'], N['F5'], N['A5'], N['C6'], N['D6']]
    for k in range(cnt['n0'], cnt['n1']):
        tb = cnt['t'] + cnt['dur'] * (k / max(1, cnt['n1'] - 1)) ** 0.85
        M.place('bed', bell(scale[k % 5] * (2 if k > 20 else 1), 1.6, 0.35 + 0.02 * k), tb, db(-22), rng.uniform(-0.8, 0.8))
    for t0, notes in ((20.2, ['A5', 'F5', 'D5']), (27.3, ['G5', 'E5', 'C5']), (33.3, ['F5', 'D5', 'Bb4'])):
        for j, nt in enumerate(notes):
            M.place('bed', bell(N[nt], 2.4, 0.7), t0 + 0.35 + j * BEAT * 0.75, db(-20), 0.25 * (j - 1))
    M.place('bed', bell(N['D5'], 3.0, 0.8), 16.95, db(-19))                       # title
    M.place('bed', bell(N['D5'], 2.6, 0.6), 12.65, db(-22))                       # his window (blue)
    M.place('bed', bell(N['D5'], 2.6, 0.8), LAMP_ON + 0.05, db(-19))              # lamp on
    for j, nt in enumerate(['D5', 'F#5', 'A5', 'D6']):                            # amber window → arpeggio (major)
        M.place('bed', bell(N[nt], 3.2, 0.8), AMBER + 0.1 + j * BEAT * 0.5, db(-19), 0.25 * (j - 1.5))
    for t0 in (126.0, 129.4, 132.8, 136.2, 139.6):                               # dawn arpeggios
        for j, nt in enumerate(['D5', 'F#5', 'A5', 'F#6' if t0 > 134 else 'D6']):
            M.place('bed', bell(N[nt], 3.0, 0.55), t0 + j * BEAT * 0.5, db(-23), 0.3 * (j - 1.5))
    M.place('bed', bell(N['D6'], 4.0, 0.6), 146.95, db(-23))                      # end card 2

    # 5 · felt piano — bass notes under the windows, answers on the white lines, the decision, the cards
    for t0, nt, v in ((12.6, 'D3', 0.7), (20.25, 'D3', 0.75), (27.35, 'C3', 0.7), (33.35, 'Bb2', 0.75), (38.4, 'A2', 0.6),
                      (46.55, 'Bb2', 0.7), (53.6, 'F4', 0.6), (57.6, 'E4', 0.6), (61.0, 'D4', 0.65), (63.95, 'A2', 0.6),
                      (89.05, 'D3', 0.8), (93.1, 'D4', 0.6), (93.1 + BEAT, 'A4', 0.5), (97.1, 'F3', 0.6), (99.6, 'C3', 0.6),
                      (101.9, 'G3', 0.6), (118.45, 'C3', 0.6), (141.9, 'D4', 0.6), (141.9 + 0.02, 'A4', 0.45), (150.8, 'D3', 0.5)):
        M.place('bed', felt(N[nt], 4.0, v), t0, db(-15), 0.0)
    # 6 · work pulse — muted bass pluck on the beat 94.2 → 121.3 (8ths from DAY 1), bass line D–F–C–G–Bb–C
    roots = [(94.2, 'D2'), (97.1, 'F2'), (99.6, 'C3'), (101.9, 'G2'), (103.6, 'D2'), (108.4, 'F2'), (111.6, 'Bb2'), (118.4, 'C3')]
    tb = 94.2
    while tb < AMBER - 0.05:
        root = [r for r in roots if r[0] <= tb + 1e-6][-1][1]
        eighth = tb >= 103.6
        M.place('bed', pluck(N[root], 0.6, 0.9 if not eighth else 0.75), tb, db(-18 + (3 if tb >= 118.4 else 0)))
        tb += BEAT if not eighth else BEAT / 2
    # 7 · montage drive (42.4 → 45.7): quickening plucks + riser → red card: stab + 0.35 s hole
    tb = 42.4
    k = 0
    while tb < 45.7 - 0.05:
        M.place('bed', pluck(N['D2'], 0.4, 0.8 + 0.05 * k), tb, db(-16))
        tb += max(0.16, 0.5 * 0.86 ** k)
        k += 1
    M.place('bed', riser(3.2), 45.7 - 3.2, db(-20))
    M.place('bed', stab(), 45.7, db(-17))
    for c in cuts:
        if 42.4 < c < 45.7 + 0.01:
            M.place('bed', boom(0.5), c, db(-25))
    mont = [d['t'] for d in ev['text'] if d['kind'] == 'readout' and 42.4 <= d['t'] < 45.7]
    for tm in mont:
        M.place('bed', click(), tm, db(-24), 0.3)

    # 8 · the clock — tick/tock at 1 Hz in the bedroom, louder after the phone dies, stops dead at 88.0
    bedroom = [(0, 6.6), (38.1, 42.4), (66.3, CLOCK_STOP)]
    tc = 0.0
    k = 0
    while tc < CLOCK_STOP - 0.01:
        if any(a <= tc < b for a, b in bedroom):
            g = -32 if tc < PHONE_OFF else -29
            if 82.0 <= tc:
                g = -27
            M.place('bed', tick(k % 2), tc, db(g + rng.uniform(-1, 1)), -0.55)
        tc += 1.0
        k += 1
    # 9 · the phone — thumb taps while he scrolls; the tiny death at 71.45
    for a, b in ((0.4, 6.4), (38.3, 39.8), (69.5, PHONE_OFF - 0.3)):
        tt_ = a + rng.uniform(0, 0.4)
        while tt_ < b:
            M.place('bed', tap(), tt_, db(-30 + rng.uniform(-3, 2)), 0.1)
            tt_ += rng.uniform(0.45, 1.2)
    M.place('bed', phone_off(), PHONE_OFF, db(-26))
    # 10 · the lights — his window goes dark (sub drop), the lamp (click + warm bloom), the amber window (bloom)
    M.place('bed', drop_sine(80, 36, 1.4), WIN_OFF, db(-18))
    M.place('bed', lamp_click(), LAMP_ON - 0.02, db(-21))
    M.place_st('bed', pad([N['D4'], N['A4']], 1.6, fc=900, attack=0.05, release=1.3, gain=0.9), LAMP_ON)
    M.place_st('bed', pad([N['D4'], N['F#4'], N['A4']], 2.4, fc=1200, attack=0.15, release=2.0, gain=1.1), AMBER)
    # 11 · push-ins: air swells (no whooshes); window interiors behind glass
    for c in (20.2, 27.3, 33.3):
        M.place('bed', air(1.9), c - 0.2, db(-30))
    for c in (46.5, 51.6, 55.1, 58.9):
        M.place('bed', air(1.4), c - 0.1, db(-33))
    # the runner's treadmill / stretching breath (B4), the couple's plates (I3), the keyboard (D5) — muffled by glass
    for tt_ in np.arange(23.3, 27.2, 0.42):
        M.place('bed', lp(runstep(0.0), 900), tt_, db(-34), -0.2)
    for tt_ in (30.0, 30.9, 32.2, 32.9):
        M.place('bed', lp(clink(2600 + 500 * rng.random()), 2500), tt_, db(-33), 0.2)
    for tt_ in np.arange(35.5, 38.0, 0.11):
        if rng.random() < 0.7:
            M.place('bed', lp(click(), 3000), tt_, db(-36 + rng.uniform(-3, 2)), 0.15)
    # the couple's kitchen on DAY 23 (water + a plate) behind glass, their heads turn; his steps pass left → right
    M.place('bed', lp(water(4.0), 2500), 112.0, db(-36))
    M.place('bed', lp(clink(2700), 2500), 113.0, db(-34), 0.1)
    for j in range(int(2.6 * 2 * 2.1) + 1):
        ts_ = 113.8 + j * (1 / 4.2)
        u = (ts_ - 113.8) / 2.6
        M.place('bed', runstep(0.6), ts_, db(-23 - 8 * abs(u - 0.5)), float(np.clip(-0.9 + 1.8 * u, -0.9, 0.9)))
    # 12 · the hero — bed creak, stand, wood-floor steps to the glass, hands on the sill, turn-away steps
    M.place('bed', creak(0.6, 150), 78.25, db(-26))
    M.place('bed', woodstep(0.6), 79.5, db(-25), -0.3)
    for ts_, pn in ((80.2, -0.2), (80.9, 0.0), (81.6, 0.15)):
        M.place('bed', woodstep(0.5), ts_, db(-27 + rng.uniform(-1, 1)), pn)
        M.place('bed', creak(0.3, 210), ts_ + 0.05, db(-38))
    M.place('bed', fabric(0.35), 82.05, db(-33))
    M.place('bed', woodstep(0.7), 90.5, db(-28), 0.2)
    for ts_, pn in ((91.72, 0.1), (92.14, -0.1), (92.56, -0.3)):
        M.place('bed', woodstep(0.5), ts_, db(-27 + rng.uniform(-1, 1)), pn)
    # breath at the glass (he breathes on it — the reflection shot), quiet
    for ts_, inh in ((84.2, True), (85.0, False), (87.0, True), (87.9, False)):
        M.place('bed', breath(inh, 0.7 if inh else 0.9), ts_, db(-36), 0.0)
    # 13 · chores — sheets, water + plates, papers, sneakers
    for ts_ in (94.55, 95.3, 96.1, 96.75):
        M.place('bed', fabric(0.55), ts_, db(-23 + rng.uniform(-2, 1)), rng.uniform(-0.3, 0.3))
    M.place('bed', water(99.6 - 97.1 - 0.2), 97.15, db(-24))
    for ts_, f in ((97.9, 2900), (98.55, 3300), (99.2, 2700)):
        M.place('bed', clink(f), ts_, db(-24), 0.1)
    for ts_ in (99.95, 100.6, 101.25, 101.7):
        M.place('bed', paper(), ts_, db(-25 + rng.uniform(-2, 1)), 0.2)
    for ts_ in (102.15, 102.75, 103.25):
        M.place('bed', scuff(), ts_, db(-24), -0.2)
    M.place('bed', woodstep(0.4), 103.4, db(-30), -0.1)
    # 14 · DAY 1 run — steps from the animation phase (1.35 Hz cycle, 2 contacts), louder as he nears, breath
    for j in range(int(4.8 * 2 * 1.35) + 1):
        ts_ = 103.6 + j / 2.7
        u = (ts_ - 103.6) / 4.8
        M.place('bed', runstep(0.8), ts_, db(-30 + 10 * u), 0.08 * (-1) ** j)
    for j in range(5):
        ts_ = 104.0 + j * 0.74 * 1.3
        M.place('bed', breath(True, 0.4), ts_, db(-32 + 6 * j / 4), 0)
        M.place('bed', breath(False, 0.45), ts_ + 0.48, db(-30 + 6 * j / 4), 0)
    # 15 · DAY 40 — the deskman's chair creak as he stands, his palm on the glass
    M.place('bed', creak(0.7, 190), 119.45, db(-27), 0.1)
    M.place('bed', tap(), 120.55, db(-29), 0.1)
    # 16 · dawn birds (123.6 → 141.6), sparse, far, panned
    tb_ = 124.2
    while tb_ < 141.0:
        pn = rng.uniform(-0.8, 0.8)
        for j in range(rng.integers(2, 6)):
            M.place('bed', chirp(), tb_ + j * rng.uniform(0.09, 0.2), db(-33 + rng.uniform(-4, 2)), pn)
        tb_ += 1.4 + rng.exponential(1.6)
    # 17 · red lines: stings; white answers: nothing but the felt notes (already placed); typewriter clicks from the text
    for d in ev['text']:
        if d['kind'] == 'villain':
            M.place('bed', sting(0.55), d['t'] - 0.55, db(-20))
    for d in ev['text']:
        if d.get('cps', 0) and d['cps'] < 60 and d['kind'] in ('villain', 'answer'):
            for k_, ch_ in enumerate(d['txt']):
                tk = d['t'] + k_ / d['cps']
                if ch_ == ' ' or any(abs(tk - c) < 0.1 for c in cuts):
                    continue
                M.place('bed', click(), tk, db(-26 + rng.uniform(-2, 2)) * (0.8 if d['kind'] == 'answer' else 1.0), 0.3)
    # 18 · hard cuts: soft tick-booms on the main structural cuts only (never inside a chore or a dialogue hold)
    for c in (6.6, 16.4, 38.1, 46.5, 63.9, 69.3, 74.6, 77.0, 89.0, 92.9, 103.6, 123.6, 131.0, 141.6):
        M.place('bed', boom(1.0), c, db(-29))
    # the clock stop: nothing — the absence is the event; a tiny hole in the bed for 0.25 s
    i0, i1 = int(CLOCK_STOP * SR), int((CLOCK_STOP + 0.25) * SR)
    bed[i0:i1] *= env_bp([(0, 0.35), (0.2, 0.35), (0.25, 1.0)], i1 - i0)[:, None]
    # the red card hole (45.7 → 46.05)
    i0, i1 = int((45.72) * SR), int((46.08) * SR)
    bed[i0:i1] *= env_bp([(0, 0.15), (0.28, 0.15), (0.36, 1.0)], i1 - i0)[:, None]

    # 19 · voice — 10 clips, untrimmed (timeline aligned to the clip starts), processed, centred
    vo_sig = {}
    for vid, path in vo_paths.items():
        a = voice_process(load_wav_mono(path))
        vo_sig[vid] = a
        M.place('vo', a, vo[vid], db(0.0), 0.0)
    duck = np.ones(n, np.float32)
    for vid, a in vo_sig.items():
        i0 = int(vo[vid] * SR)
        duck[max(0, i0):i0 + len(a)] = db(-5)
    ar_ = math.exp(-1.0 / (0.9 * SR))
    rel = signal.lfilter([1 - ar_], [1, -ar_], duck).astype(np.float32)
    duck = np.minimum(duck, rel)
    del rel
    aa = math.exp(-1.0 / (0.25 * SR))
    att = signal.lfilter([1 - aa], [1, -aa], duck[::-1])[::-1].astype(np.float32)
    duck = np.minimum(duck, att).astype(np.float32)
    del att

    bed *= duck[:, None]
    del duck
    bed += M.bus['vo']
    del M.bus['vo']
    np.tanh(bed * 1.1, out=bed)
    bed *= (1 / 1.1)
    i0 = int((total - 1.5) * SR)
    bed[i0:] *= np.linspace(1, 0, n - i0, dtype=np.float32)[:, None]
    write_wav(out_wav, bed)
    return out_wav


def decode_vo():
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    paths = {}
    for i in range(1, 11):
        src = os.path.join(WF, 'vo', f'vo{i:02d}.mp3')
        dst = os.path.join(BUILD, f'vo{i:02d}.wav')
        if not os.path.exists(dst):
            subprocess.run([ff, '-y', '-loglevel', 'error', '-i', src, '-ac', '1', '-ar', str(SR), '-c:a', 'pcm_s16le', dst], check=True)
        paths[f'vo{i:02d}'] = dst
    return paths


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--events', default=os.path.join(WF, 'data', 'events_window.json'))
    ap.add_argument('--out', default=os.path.join(BUILD, 'mix.wav'))
    args = ap.parse_args()
    os.makedirs(BUILD, exist_ok=True)
    ev = json.load(open(args.events))
    vo_paths = decode_vo()
    raw = build(ev, os.path.join(BUILD, 'mix_raw.wav'), vo_paths)
    stats = normalize(raw, args.out)
    json.dump(stats, open(os.path.join(BUILD, 'mix_stats.json'), 'w'))
    print('mix →', args.out, stats)
