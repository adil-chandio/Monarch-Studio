"""
wide_full_audio.py — score + sound design for the full 4:23 episode.
=====================================================================
Sibling of wide_audio.py (53 s hook). Neither that file nor make_asmr.py is
imported or modified; the primitives are re-stated so the three builds can
never break each other.

TWO THINGS THAT MATTER OVER FOUR MINUTES THAT DID NOT OVER FIFTY SECONDS
------------------------------------------------------------------------
1. DYNAMIC ARC. A bed that is equally dense for 263 s is wallpaper, and the
   ear stops hearing it inside a minute. Every act gets a different
   instrumentation, and Act 4 — the argument — drops almost to silence so the
   contested evidence lands as seriously as it deserves.

       ACT 1  THE CHASE          drone + sparse drum + shaker + footfalls
       ACT 2  THE MACHINE        drone + clinical pulse, NO drum   (clean)
       ACT 3  THE HUNT           full drum on 1 and 3, shaker up, footfalls
       ACT 4  THE ARGUMENT       drone only + single taps          (bare)
       ACT 5  WHAT YOU INHERITED everything returns, resolving major

2. CUES ARE READ OUT OF THE PICTURE, NOT RE-TYPED. The cue layer imports
   wide_full and walks its actual scene table, so every reveal time in the
   audio is by construction the same number the renderer used. Hand-copying
   ~200 cue times across two files is how sync rot starts.

Memory note: at 263.5 s a stereo float64 buffer is 202 MB and the reverb
needs three of them. Everything here is float32 and the reverb runs one
channel at a time — the first attempt at a long bed swapped the box.
"""
import math, os, sys, wave
import numpy as np

sys.path.insert(0, '/home/user/src')
import wide_full as WF

SR = 48000
DUR = WF.DUR_TOTAL                     # 263.5
N = int(SR * DUR)
rng = np.random.default_rng(23)
BUF = np.zeros((2, N), dtype=np.float32)
SFX = np.zeros((2, N), dtype=np.float32)
LOG = []

SCENE = WF.SCENE_START
END = WF.SCENE_END
CUTS = WF.CUTS
NS = WF.NS
ACT_OF = WF.ACT_OF
BPM = 84.0
SPB = 60.0 / BPM

ACT_SPAN = {}
for a in (1, 2, 3, 4, 5):
    idx = [i for i in range(NS) if ACT_OF[i] == a]
    ACT_SPAN[a] = (SCENE[idx[0]], END[idx[-1]])


# ───────────────────────────────────────────── primitives
def flt(x, lo=0.0, hi=20000.0, n=2):
    x = np.asarray(x, dtype=np.float64)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if hi < 20000:
        g = g / np.sqrt(1 + (f / hi) ** (2 * n))
    if lo > 0:
        r = np.maximum(f, 1e-6) / lo
        g = g * (r ** n / np.sqrt(1 + r ** (2 * n)))
    return np.fft.irfft(X * g, len(x))


def env(n, atk, dec, curve=3.0):
    e = np.ones(n)
    a = min(max(1, int(atk * SR)), n)
    dd = min(max(1, int(dec * SR)), n)
    e[:a] = 0.5 - 0.5 * np.cos(np.linspace(0, math.pi, a))
    e[n - dd:] = np.linspace(1, 0, dd) ** curve
    return e


def noise(d):
    return rng.normal(0, 1, int(d * SR))


def place(sig, t, gain=1.0, pan=0.0, tag='', bus='sfx'):
    i = int(t * SR)
    if i < 0 or i >= N: return
    n = min(len(sig), N - i)
    l = math.sqrt((1 - pan) / 2) * 1.414
    r = math.sqrt((1 + pan) / 2) * 1.414
    tgt = SFX if bus == 'sfx' else BUF
    s32 = np.asarray(sig[:n], dtype=np.float32)
    tgt[0, i:i + n] += s32 * np.float32(gain * l)
    tgt[1, i:i + n] += s32 * np.float32(gain * r)
    if tag: LOG.append((round(t, 3), tag, round(gain, 3), round(pan, 2)))


def place_st(l, r, t, gain=1.0, tag='', bus='sfx'):
    i = int(t * SR)
    if i < 0 or i >= N: return
    n = min(len(l), N - i)
    tgt = SFX if bus == 'sfx' else BUF
    tgt[0, i:i + n] += np.asarray(l[:n], dtype=np.float32) * np.float32(gain)
    tgt[1, i:i + n] += np.asarray(r[:n], dtype=np.float32) * np.float32(gain)
    if tag: LOG.append((round(t, 3), tag, round(gain, 3), 0.0))


# ───────────────────────────────────────────── voices
def drum(d=0.62, f0=124, f1=74):
    n = int(d * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 11.0)
    body = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t * 5.2)
    skin = flt(noise(d), 180, 2100) * np.exp(-t * 34.0) * 0.5
    x = flt(body * 0.72 + skin * 1.25, 62, 6200)
    return x * env(n, 0.0032, d * 0.80, 2.2) * 0.9


def shaker(d=0.15, bright=1.0):
    n = int(d * SR); t = np.arange(n) / SR
    x = flt(noise(d), 3100 * bright, 9000 * bright)
    return x * np.exp(-t * 46.0) * env(n, 0.0026, d * 0.9, 2.6)


def wind(d=4.0, f=520):
    n = int(d * SR); t = np.arange(n) / SR
    return flt(noise(d), 180, f) * (np.sin(math.pi * t / d) ** 1.5)


def drone(freqs, d, amp=1.0):
    """True stereo: independent detuning and phases per channel, fundamental
    lifted an octave. A widener cannot widen a side channel that is zero."""
    n = int(d * SR); t = np.arange(n) / SR
    out = []
    for dets in ((0.9962, 1.0, 1.0031), (0.9972, 1.0008, 1.0045)):
        x = np.zeros(n)
        for k, f in enumerate(freqs):
            for det in dets:
                ph = rng.uniform(0, 6.283)
                x += np.sin(2 * math.pi * f * det * 2 * t + ph) * (0.66 ** k)
                x += np.sin(2 * math.pi * f * det * 3 * t + ph) * .34 * (0.66 ** k)
                x += np.sin(2 * math.pi * f * det * t + ph) * .22 * (0.66 ** k)
        x /= max(1.0, len(freqs) * 2.6)
        out.append(flt(x, 95, 2400))
    e = (np.sin(math.pi * t / d) ** 1.35) * amp
    return out[0] * e, out[1] * e


def pad(freqs, d, amp=1.0):
    n = int(d * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for k, f in enumerate(freqs):
        for det in (1.0, 1.004):
            x += np.sin(2 * math.pi * f * det * t + rng.uniform(0, 6.283)) * (0.70 ** k)
    x /= max(1.0, len(freqs) * 1.6)
    return flt(x, 70, 2600) * (np.sin(math.pi * t / d) ** 1.6) * amp


def flute(f, d=1.2):
    n = int(d * SR); t = np.arange(n) / SR
    bend = 1.0 - 0.035 * np.exp(-t * 16.0)
    x = np.sin(2 * math.pi * f * np.cumsum(bend) / SR)
    x += 0.22 * np.sin(2 * math.pi * 2 * f * np.cumsum(bend) / SR)
    br = flt(noise(d), f * 0.8, f * 4.5) * 0.16
    return (x * 0.8 + br) * env(n, 0.055, d * 0.72, 2.0)


def tap(f=1400, d=0.075, bright=0.5):
    n = int(d * SR); t = np.arange(n) / SR
    x = np.sin(2 * math.pi * f * t) * np.exp(-t * 58)
    x += flt(noise(d), 900, 4200 + 2600 * bright) * np.exp(-t * 86) * 0.42
    return x * env(n, 0.0022, d * 0.9, 2.4) * 0.6


def chime(f=880, d=1.3, parts=(1, 2.01, 3.03, 4.72)):
    n = int(d * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for k, p in enumerate(parts):
        x += np.sin(2 * math.pi * f * p * t) * (0.62 ** k) * np.exp(-t * (2.0 + k * 1.4))
    return flt(x, 200, 7000) * env(n, 0.006, d * 0.85, 2.2) * 0.45


def whoosh(d=0.52, f0=240, f1=2400, rev=False):
    n = int(d * SR); t = np.arange(n) / SR; u = t / d
    x = flt(noise(d), 160, 6000)
    sweep = f0 * (f1 / f0) ** (1 - u if rev else u)
    mod = np.sin(2 * math.pi * np.cumsum(sweep) / SR) * 0.22
    y = flt(x * (0.35 + 0.65 * (1 - u if rev else u)) + mod, 140, 5200)
    return y * env(n, 0.028, d * 0.70, 2.0) * 0.5


def sub(f0=96, f1=54, d=0.70):
    n = int(d * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 6.0)
    x = np.sin(2 * math.pi * np.cumsum(f) / SR)
    return x * env(n, 0.010, d * 0.86, 2.4) * 0.9


def riser(d=1.10, f0=170, f1=1150):
    n = int(d * SR); t = np.arange(n) / SR; u = t / d
    f = f0 * (f1 / f0) ** u
    x = np.sin(2 * math.pi * np.cumsum(f) / SR) * 0.30
    x += flt(noise(d), 300, 2800) * 0.5 * u
    return x * (u ** 1.7) * env(n, 0.05, 0.05, 1.0) * 0.55


def cloth(d=0.20):
    n = int(d * SR); t = np.arange(n) / SR
    return flt(noise(d), 500, 3000) * np.exp(-t * 22) * env(n, .012, d * .8, 2) * .5


def footfall(d=0.22, soft=1.0):
    n = int(d * SR); t = np.arange(n) / SR
    grit = flt(noise(d), 900, 5200) * np.exp(-t * 30.0) * 0.55
    body = flt(noise(d), 60, 420) * np.exp(-t * 26.0) * 0.8
    return (grit + body) * env(n, 0.0035, d * 0.85, 2.3) * 0.5 * soft


# ───────────────────────────────────────────── harmony
DM  = (73.42, 110.00, 146.83)      # Dm      home
EB  = (77.78, 116.54, 155.56)      # Eb      dread, a semitone up
DSUS= (73.42,  98.00, 146.83)      # Dsus4   unresolved — the argument
F_  = (87.31, 130.81, 174.61)      # F       relief / revelation
G_  = (98.00, 146.83, 196.00)      # G       lift
BB  = (116.54, 174.61, 233.08)     # Bb      the pay-off

ACT_CHORDS = {1: [DM, DM, EB, DSUS, F_, EB, G_, DM],
              2: [F_, DM, F_, G_, F_, DM],
              3: [EB, DM, EB, DM, EB, DM, EB, DM, EB, DM, DSUS],
              4: [DSUS, DSUS, DSUS, DSUS, DSUS, DM],
              5: [F_, BB, F_]}
CHORD = []
for a in (1, 2, 3, 4, 5):
    CHORD += ACT_CHORDS[a]
assert len(CHORD) == NS, (len(CHORD), NS)

# per-act instrumentation
DRUM_ON = {1: 'sparse', 2: 'pulse', 3: 'full', 4: 'off', 5: 'full'}
SHAKE_G = {1: 1.20, 2: 0.52, 3: 1.50, 4: 0.00, 5: 1.08}
DRONE_G = {1: 0.115, 2: 0.100, 3: 0.108, 4: 0.088, 5: 0.120}


# ───────────────────────────────────────────── bed
def build_bed():
    for i in range(NS):
        a = ACT_OF[i]
        d = END[i] - SCENE[i] + 0.9
        dl, dr = drone(CHORD[i], d, DRONE_G[a])
        place_st(dl, dr, SCENE[i] - 0.25, 1.0, f'drone{i+1}', 'bed')
        place(pad([CHORD[i][0]], d * 0.9, 0.028), SCENE[i] - 0.15, 1.0, 0.0,
              '', 'bed')
        place(pad([f * 4 for f in CHORD[i]], d * 0.85,
                  0.060 if a != 4 else 0.030), SCENE[i] + 0.1, 1.0,
              0.34 * (1 if i % 2 else -1), '', 'bed')

    # wind under everything, 0.09 Hz, alternating sides
    t, k = 0.0, 0
    while t < DUR:
        place(wind(5.4, 420 + 180 * (k % 3)), t, 0.030,
              0.55 if k % 2 else -0.55, '', 'bed')
        t += 3.6; k += 1

    # drum, per act
    beat, t = 0, 0.0
    while t < DUR - 0.2:
        a = ACT_OF[max(k for k in range(NS) if t >= SCENE[k])]
        mode = DRUM_ON[a]
        pos = beat % 4
        bar = beat // 4
        hit, g = False, 0.0
        if mode == 'sparse':
            hit = (pos == 0 and bar % 2 == 0); g = 0.13
        elif mode == 'pulse':
            hit = (pos == 0 and bar % 2 == 0); g = 0.075
        elif mode == 'full':
            hit = (pos == 0 or pos == 2)
            g = 0.185 if pos == 0 else 0.100
            if a == 3:
                # the hunt tightens as it goes
                u = (t - ACT_SPAN[3][0]) / (ACT_SPAN[3][1] - ACT_SPAN[3][0])
                g *= 0.80 + 0.45 * max(0.0, min(1.0, u))
        if hit and t > 1.2:
            place(drum(0.62 if pos == 0 else 0.42, 124 if pos == 0 else 108),
                  t, g, 0.17 if bar % 2 == 0 else -0.17, '', 'bed')
        beat += 1
        t = beat * SPB

    # sand shaker on eighths
    e, t = 0, 0.0
    while t < DUR - 0.2:
        a = ACT_OF[max(k for k in range(NS) if t >= SCENE[k])]
        gm = SHAKE_G[a]
        if t > 3.0 and gm > 0:
            acc = (e % 4 == 0)
            g = (0.094 if acc else 0.050) * gm
            place(shaker(0.14 if acc else 0.11, 1.0 if acc else 0.86),
                  t + (0.004 if e % 2 else 0.0), g,
                  0.62 * math.sin(e * 0.37), '', 'bed')
        e += 1
        t = e * SPB / 2

    # footfalls: the chase and the hunt only
    for t0, t1, cad in ((0.18, 6.55, 168.0), (117.3, 126.0, 150.0),
                        (154.9, 160.5, 162.0), (185.4, 191.2, 112.0)):
        t, step = t0, 0
        while t < t1:
            place(footfall(0.22, 1.0 if step % 2 == 0 else 0.86), t,
                  0.080, 0.30 * math.sin(step * 1.1), '')
            step += 1
            t += 60.0 / cad

    # bone flute, one phrase per act door
    for st, f, d in ((5.90, 293.66, 0.95), (23.60, 220.00, 1.05),
                     (51.60, 293.66, 1.10), (85.20, 349.23, 1.00),
                     (115.40, 311.13, 1.05), (160.00, 293.66, 0.95),
                     (193.60, 220.00, 1.20), (235.60, 349.23, 1.10),
                     (261.20, 293.66, 1.60)):
        place(flute(f, d), st, 0.085, -0.18, 'flute', 'bed')


# ───────────────────────────────────────────── transitions
def build_transitions():
    for i, c in enumerate(CUTS):
        a = ACT_OF[i + 1]
        newact = ACT_OF[i] != ACT_OF[i + 1]
        pan = 0.5 if i % 2 == 0 else -0.5
        place(whoosh(0.50, 220, 2300), c - 0.30, 0.17 if not newact else 0.22,
              pan, f'cut{i+1}')
        place(sub(96, 54, 0.60), c - 0.015, 0.13 if not newact else 0.19,
              0.0, '')
        place(cloth(0.22), c + 0.02, 0.10, -pan, '')
        if newact:
            place(riser(1.05, 165, 1020), c - 1.05, 0.15, 0.0, f'act{a}_riser')
            place(chime(392.0, 1.8), c + 0.04, 0.085, 0.10, f'act{a}_open')


# ───────────────────────────────────────────── cues, READ FROM THE PICTURE
def build_cues():
    # Act 1 keeps the hook's own cue plan
    S = SCENE
    def at(i, lt): return S[i] + lt
    place(tap(900, 0.10), at(0, 0.55), 0.10, 0.45, 's1_quarry')
    place(whoosh(0.34, 300, 1500), at(0, 2.10), 0.09, 0.0, '')
    place(tap(1250, 0.085), at(0, 3.50), 0.12, 0.0, '')
    for lt, keep in ((0.70, False), (1.05, False), (1.55, True), (1.90, True)):
        place(cloth(0.20), at(1, lt), 0.11, -0.3 + 0.2 * lt, '')
        if keep: place(tap(1500, 0.09, 0.8), at(1, lt + 0.08), 0.13, 0.22, '')
        else:    place(sub(132, 74, 0.30), at(1, lt + 0.26), 0.09, -0.25, '')
    place(tap(1250, 0.085), at(1, 3.30), 0.12, 0.0, '')
    place(sub(108, 56, 0.80), at(2, 0.75), 0.15, 0.0, '')
    nn = int(1.1 * SR)
    place(flt(noise(1.1), 400, 3400) * np.linspace(0, 1, nn) ** 2.0
          * env(nn, 0.08, 0.35, 2.0), at(2, 1.55), 0.075, 0.2, '')
    place(tap(1250, 0.085), at(2, 3.40), 0.12, 0.0, '')
    place(sub(102, 52, 0.90), at(3, 0.55), 0.17, 0.0, 's4_title')
    place(tap(2100, 0.11, 1.0), at(3, 1.15), 0.10, 0.1, '')
    place(tap(1250, 0.085), at(3, 2.70), 0.12, 0.0, '')
    for i in range(46):
        u = i / 45
        place(shaker(0.085, 1.25), at(4, 0.85 + u * 2.3),
              0.020 + 0.016 * (1 - u), 0.6 * math.sin(i * 0.9), '')
    place(tap(1700, 0.09), at(4, 1.10), 0.09, -0.2, '')
    place(sub(112, 60, 0.55), at(4, 3.30), 0.10, 0.0, '')
    for k in range(11):
        tt = at(5, 1.30 + k * (1.0 / 2.4))
        if tt > END[5] - 0.3: break
        place(drum(0.30, 150, 86), tt, 0.105, 0.42, '')
        if k % 2 == 0: place(tap(760, 0.10, 0.4), tt + 0.012, 0.085, -0.42, '')
    place(sub(106, 58, 0.62), at(5, 2.40), 0.11, 0.0, '')
    place(tap(1250, 0.085), at(5, 3.50), 0.12, 0.0, '')
    for nm, lt0, f0_, f1_, pan in (('kudu', 1.15, 300, 980, 0.40),
                                   ('man', 1.55, 260, 330, -0.40)):
        n2 = int(2.4 * SR); tt = np.arange(n2) / SR; u = tt / 2.4
        f = f0_ * (f1_ / f0_) ** u
        x = np.sin(2 * math.pi * np.cumsum(f) / SR) * 0.30
        x += flt(noise(2.4), 1200, 5000) * 0.22
        place(x * env(n2, 0.10, 0.5, 1.8), at(6, lt0), 0.055, pan, '')
    place(tap(1250, 0.085), at(6, 4.60), 0.12, 0.0, '')
    place(sub(106, 58, 0.70), at(7, 0.75), 0.12, -0.35, '')
    place(sub(118, 64, 0.70), at(7, 1.15), 0.13, 0.35, '')
    place(tap(1250, 0.085), at(7, 2.30), 0.11, 0.0, '')
    place(sub(100, 50, 0.88), at(7, 4.00), 0.15, 0.0, '')
    place(sub(96, 46, 1.10), at(7, 4.90), 0.16, 0.0, '')

    # ── Acts 2–5: walk wide_full's actual scene table
    for bi, c in enumerate(WF.BODY):
        si = bi + 8
        t0 = SCENE[si]
        lay = c['L'].__name__
        place(tap(1150, 0.09, 0.6), t0 + 0.12, 0.085, 0.0, '')   # headline

        if lay == 'L_triple':
            for i, (_, keep) in enumerate(c['items']):
                tt = t0 + 0.75 + i * 0.40
                if keep:
                    place(chime(659.3, 1.1), tt, 0.085, 0.18, '')
                    place(tap(1600, 0.09, .9), tt + .30, 0.10, 0.18, '')
                else:
                    place(cloth(0.20), tt, 0.10, -0.26, '')
                    place(sub(138, 78, 0.28), tt + 0.30, 0.085, -0.26, '')
        elif lay == 'L_anatomy':
            place(chime(523.3, 1.4), t0 + 0.70, 0.075, 0.30, '')
            place(whoosh(0.34, 320, 1400), t0 + 1.10, 0.075, 0.22, '')
            for i in range(len(c.get('lines', []))):
                place(tap(1350 + i * 110, 0.075, .5), t0 + 1.75 + i * 0.35,
                      0.070, 0.26, '')
            if c.get('big'):
                place(sub(104, 56, 0.72), t0 + 2.30, 0.135, 0.0, '')
        elif lay == 'L_bignum':
            place(sub(104, 54, 0.88), t0 + 0.55, 0.165, 0.0, '')
            place(tap(1500, 0.085), t0 + 1.25, 0.085, -0.12, '')
            if c.get('sub'):
                place(tap(1050, 0.08, .4), t0 + 1.70, 0.065, 0.14, '')
        elif lay == 'L_timeline':
            place(whoosh(0.56, 200, 1900), t0 + 0.45, 0.105, -0.30, '')
            for i, m in enumerate(c['marks']):
                tt = t0 + 0.95 + i * 0.38
                if m[3]:
                    place(chime(784.0, 1.5), tt, 0.095, 0.0, '')
                    place(sub(110, 60, 0.55), tt, 0.105, 0.0, '')
                else:
                    place(tap(980, 0.075, .35), tt, 0.070,
                          -0.34 + 0.22 * i, '')
            if c.get('note'):
                place(sub(98, 52, 0.80), t0 + 2.90, 0.125, 0.0, '')
        elif lay == 'L_stage':
            if c.get('phrase'):
                place(sub(102, 54, 0.78), t0 + c.get('phrase_at', 1.6),
                      0.140, 0.0, '')
            for k in c.get('kudus', []):
                if k[2]:
                    for q in range(5):
                        place(footfall(0.18, 0.5), t0 + 0.9 + q * 0.26,
                              0.045, 0.42, '')
        elif lay == 'L_paper':
            place(cloth(0.26), t0 + 0.55, 0.14, 0.0, '')
            place(sub(120, 68, 0.42), t0 + 0.58, 0.085, 0.0, '')
            for i in range(2):
                place(tap(1250, 0.07, .4), t0 + 1.25 + i * 0.22, 0.055, 0.1, '')
            place(drum(0.46, 112, 68), t0 + 2.45, 0.145, 0.0, 'stamp')
        elif lay == 'L_list':
            for i, r in enumerate(c['rows']):
                tt = t0 + 0.80 + i * 0.42
                mk = r.get('mark', 'dot')
                if mk == 'cross':
                    place(sub(134, 76, 0.30), tt, 0.105, -0.22, '')
                    place(cloth(0.18), tt, 0.085, -0.22, '')
                elif mk == 'tick':
                    place(chime(698.5, 1.0), tt, 0.080, 0.20, '')
                else:
                    place(tap(1300, 0.08, .5), tt, 0.080, -0.10 + 0.08 * i, '')
            if c.get('quote'):
                place(chime(440.0, 2.0), t0 + 0.80 + len(c['rows']) * 0.42
                      + 0.35, 0.090, 0.0, '')
        elif lay == 'L_statement':
            for i in range(len(c['lines'])):
                place(sub(100 - i * 6, 52, 0.85),
                      t0 + c.get('at', .45) + i * 0.70, 0.150, 0.0, '')

        if c.get('chip'):
            place(tap(1250, 0.085), t0 + c.get('chip_at', 0.9), 0.105, 0.0, '')


# ───────────────────────────────────────────── space
def silk_inplace(buf, wet=0.26):
    """Prime-spaced early reflections, one channel at a time. Building the
    whole stereo tail at once needed ~600 MB at this length."""
    taps = [(0.0131, .50), (0.0193, .44), (0.0271, .38), (0.0379, .32),
            (0.0533, .27), (0.0727, .22), (0.1013, .17), (0.1399, .13),
            (0.1933, .10), (0.2663, .075), (0.3671, .055), (0.5051, .038)]
    for ch in (0, 1):
        acc = np.zeros(buf.shape[1], dtype=np.float32)
        for k, (dt, g) in enumerate(taps):
            i = int(dt * SR)
            if i >= buf.shape[1]: break
            sgn = 1 if k % 2 == 0 else -1
            w = g * (1.0 + (0.10 * sgn if ch == 0 else -0.10 * sgn))
            acc[i:] += buf[ch, :-i] * np.float32(w)
        acc = flt(acc, 180, 4200).astype(np.float32)
        buf[ch] = buf[ch] * np.float32(1 - wet * 0.42) + acc * np.float32(wet)
        del acc
    return buf


def main():
    global BUF, SFX
    print('building bed…', flush=True)
    build_bed()
    print('transitions…', flush=True)
    build_transitions()
    print('cues…', flush=True)
    build_cues()
    print(f'{len(LOG)} logged events; reverb…', flush=True)
    silk_inplace(SFX, 0.26)
    BUF += SFX
    SFX = None   # free ~100 MB before the M/S stage

    mix = BUF
    for c in (0, 1):
        mix[c] = flt(mix[c], 46, 15000).astype(np.float32)
        mix[c] -= flt(mix[c], 0, 155, 2).astype(np.float32) * np.float32(0.58)
    mid = (mix[0] + mix[1]) * np.float32(0.5)
    side = (mix[0] - mix[1]) * np.float32(0.5)
    side = flt(side, 170, 16000).astype(np.float32) * np.float32(2.60)
    air = flt(mid, 6200, 16000).astype(np.float32) * np.float32(1.70)
    pres = flt(mid, 2400, 5200).astype(np.float32) * np.float32(0.42)
    # 4-8 kHz shine: the hook's air band sat at 6.2 k+, which left the full
    # episode's 4-8 k share at 7.8 % in the delivered mix (gate wants >10 %).
    shine = flt(mid, 4000, 8000).astype(np.float32) * np.float32(0.45)
    out = np.vstack([mid + side + air + pres + shine,
                     mid - side + air + pres + shine])
    del mid, side, air, pres, shine

    peak = float(np.max(np.abs(out)))
    out *= np.float32(0.72 / max(peak, 1e-9))
    out = np.tanh(out * 1.18) / math.tanh(1.18)
    f = int(0.040 * SR)
    out[:, :f] *= np.linspace(0, 1, f) ** 2
    out[:, -f:] *= np.linspace(1, 0, f) ** 2

    os.makedirs('/home/user/build', exist_ok=True)
    pcm = (np.clip(out.T, -1, 1) * 32767).astype('<i2')
    with wave.open('/home/user/build/full_bed.wav', 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    LOG.sort()
    with open('/home/user/FULL_AUDIO_LEDGER.csv', 'w') as fh:
        fh.write('t,tag,gain,pan\n')
        for r in LOG: fh.write(','.join(str(x) for x in r) + '\n')
    rms = float(np.sqrt(np.mean(out.astype(np.float64) ** 2)))
    print(f'bed {DUR}s  events={len(LOG)}  rms={20*math.log10(rms):.1f} dBFS '
          f'peak={20*math.log10(float(np.max(np.abs(out)))):.1f} dBFS')


if __name__ == '__main__':
    main()
