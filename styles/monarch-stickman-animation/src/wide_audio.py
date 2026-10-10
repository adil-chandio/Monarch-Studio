"""
wide_audio.py — ASMR sound design for the 16:9 long-form hook.
===============================================================
Sibling of make_asmr.py. That file is NOT imported or modified; the handful of
DSP primitives it established are re-stated here so the vertical build and the
landscape build can never break each other.

Palette for this one is deliberately not the money-reel's bright kit:
  * a low D drone that never leaves
  * a frame drum on 1 and 3, sparse at first, insistent by the title card
  * a dry sand shaker on eighths — the single texture that says "savanna"
  * breath-rate wind swells, 0.09 Hz, under everything
  * cue layer locked frame-accurately to the on-screen reveals in wide.py
Nothing above ~9 kHz survives. Every attack is raised-cosine.
"""
import math, os, sys
import numpy as np

SR = 48000
DUR = 53.00
N = int(SR * DUR)
rng = np.random.default_rng(17)
BUF = np.zeros((2, N), dtype=np.float64)    # music bed
SFX = np.zeros((2, N), dtype=np.float64)    # cue bus -> silk reverb
LOG = []

SCENE = [0.000, 6.900, 13.000, 19.200, 24.700, 31.000, 37.300, 45.400]
END = SCENE[1:] + [DUR]
CUTS = SCENE[1:]
BPM = 84.0
SPB = 60.0 / BPM                              # 0.714286 s


# ───────────────────────────────────────────── primitives
def flt(x, lo=0.0, hi=20000.0, n=2):
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
    """Raised-cosine attack, power-law decay. Never a step, so never a click."""
    e = np.ones(n)
    a = max(1, int(atk * SR))
    d = max(1, int(dec * SR))
    a = min(a, n); d = min(d, n)
    e[:a] = 0.5 - 0.5 * np.cos(np.linspace(0, math.pi, a))
    e[n - d:] = np.linspace(1, 0, d) ** curve
    return e


def place(sig, t, gain=1.0, pan=0.0, tag='', bus='sfx'):
    i = int(t * SR)
    if i < 0 or i >= N: return
    n = min(len(sig), N - i)
    l = math.sqrt((1 - pan) / 2) * 1.414
    r = math.sqrt((1 + pan) / 2) * 1.414
    tgt = SFX if bus == 'sfx' else BUF
    tgt[0, i:i + n] += sig[:n] * gain * l
    tgt[1, i:i + n] += sig[:n] * gain * r
    if tag: LOG.append((round(t, 3), tag, round(gain, 3), round(pan, 2)))


def place_st(l, r, t, gain=1.0, tag='', bus='sfx'):
    i = int(t * SR)
    if i < 0 or i >= N: return
    n = min(len(l), N - i)
    tgt = SFX if bus == 'sfx' else BUF
    tgt[0, i:i + n] += l[:n] * gain
    tgt[1, i:i + n] += r[:n] * gain
    if tag: LOG.append((round(t, 3), tag, round(gain, 3), 0.0))


def noise(d):
    return rng.normal(0, 1, int(d * SR))


# ───────────────────────────────────────────── voices
def drum(d=0.62, f0=124, f1=74):
    """Frame drum: a pitched membrane drop plus a dry skin slap."""
    n = int(d * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 11.0)
    body = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t * 5.2)
    skin = flt(noise(d), 180, 2100) * np.exp(-t * 34.0) * 0.5
    x = body * 0.72 + skin * 1.25        # more skin, less boom
    x = flt(x, 62, 6200)
    return x * env(n, 0.0032, d * 0.80, 2.2) * 0.9


def shaker(d=0.15, bright=1.0):
    """Dry seed-pod shaker. Band-limited so it never gets glassy."""
    n = int(d * SR)
    x = flt(noise(d), 3100 * bright, 9000 * bright)
    t = np.arange(n) / SR
    return x * np.exp(-t * 46.0) * env(n, 0.0026, d * 0.9, 2.6)


def wind(d=4.0, f=520):
    n = int(d * SR)
    x = flt(noise(d), 180, f)
    t = np.arange(n) / SR
    return x * (np.sin(math.pi * t / d) ** 1.5)


def drone(freqs, d, amp=1.0):
    """Sustained bowed drone, returned as a TRUE STEREO PAIR.

    v1 built one mono drone and panned it to 0.0. Because the drone carries
    most of the bed's energy the whole mix collapsed to L/R correlation 0.98
    — a widener multiplying a side signal that is identically zero does
    nothing at all. Each channel now gets its own detuning and its own random
    phases, so a side channel actually exists for the widener to work on.

    The spectrum is also lifted an octave: the fundamental is now the second
    partial with only a trace of the true root, because v1 dumped 34 % of all
    energy below 120 Hz and the result was a rumble, not a drone.
    """
    n = int(d * SR)
    t = np.arange(n) / SR
    out = []
    for dets in ((0.9962, 1.0, 1.0031), (0.9972, 1.0008, 1.0045)):
        x = np.zeros(n)
        for k, f in enumerate(freqs):
            for det in dets:
                ph = rng.uniform(0, 6.283)
                x += np.sin(2 * math.pi * f * det * 2 * t + ph) * (0.66 ** k)
                x += np.sin(2 * math.pi * f * det * 3 * t + ph) * 0.34 * (0.66 ** k)
                x += np.sin(2 * math.pi * f * det * t + ph) * 0.22 * (0.66 ** k)
        x /= max(1.0, len(freqs) * 2.6)
        out.append(flt(x, 95, 2400))
    e = (np.sin(math.pi * t / d) ** 1.35) * amp
    return out[0] * e, out[1] * e


def pad(freqs, d, amp=1.0):
    n = int(d * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, f in enumerate(freqs):
        for det in (1.0, 1.004):
            x += np.sin(2 * math.pi * f * det * t + rng.uniform(0, 6.283)) * (0.70 ** k)
    x /= max(1.0, len(freqs) * 1.6)
    x = flt(x, 70, 2600)
    return x * (np.sin(math.pi * t / d) ** 1.6) * amp


def flute(f, d=1.2):
    """Bone-flute-ish: breathy sine with a noise edge and a little scoop."""
    n = int(d * SR)
    t = np.arange(n) / SR
    bend = 1.0 - 0.035 * np.exp(-t * 16.0)
    x = np.sin(2 * math.pi * f * np.cumsum(bend) / SR)
    x += 0.22 * np.sin(2 * math.pi * 2 * f * np.cumsum(bend) / SR)
    br = flt(noise(d), f * 0.8, f * 4.5) * 0.16
    return (x * 0.8 + br) * env(n, 0.055, d * 0.72, 2.0)


def tap(f=1400, d=0.075, bright=0.5):
    n = int(d * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * math.pi * f * t) * np.exp(-t * 58)
    x += flt(noise(d), 900, 4200 + 2600 * bright) * np.exp(-t * 86) * 0.42
    return x * env(n, 0.0022, d * 0.9, 2.4) * 0.6


def whoosh(d=0.52, f0=240, f1=2400, rev=False):
    n = int(d * SR)
    t = np.arange(n) / SR
    u = t / d
    x = flt(noise(d), 160, 6000)
    sweep = f0 * (f1 / f0) ** (1 - u if rev else u)
    mod = np.sin(2 * math.pi * np.cumsum(sweep) / SR) * 0.22
    y = x * (0.35 + 0.65 * (1 - u if rev else u)) + mod
    y = flt(y, 140, 5200)
    return y * env(n, 0.028, d * 0.70, 2.0) * 0.5


def sub(f0=72, f1=40, d=0.80):
    n = int(d * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 6.0)
    x = np.sin(2 * math.pi * np.cumsum(f) / SR)
    return x * env(n, 0.010, d * 0.86, 2.4) * 0.9


def riser(d=1.10, f0=170, f1=1150):
    n = int(d * SR)
    t = np.arange(n) / SR
    u = t / d
    f = f0 * (f1 / f0) ** u
    x = np.sin(2 * math.pi * np.cumsum(f) / SR) * 0.30
    x += flt(noise(d), 300, 1000 + 3600 * u.mean()) * 0.5 * u
    return x * (u ** 1.7) * env(n, 0.05, 0.05, 1.0) * 0.55


def cloth(d=0.20):
    n = int(d * SR)
    t = np.arange(n) / SR
    return flt(noise(d), 500, 3000) * np.exp(-t * 22) * env(n, 0.012, d * .8, 2) * .5


def footfall(d=0.22, soft=1.0):
    """Sand footfall — the ASMR signature of this film."""
    n = int(d * SR)
    t = np.arange(n) / SR
    grit = flt(noise(d), 900, 5200) * np.exp(-t * 30.0) * 0.55
    body = flt(noise(d), 60, 420) * np.exp(-t * 26.0) * 0.8
    return (grit + body) * env(n, 0.0035, d * 0.85, 2.3) * 0.5 * soft


# ───────────────────────────────────────────── bed
# Dorian-flavoured minor, rooted on D. One chord per beat of the script.
CH = [(73.42, 110.00, 146.83),      # 1 Dm   the chase
      (73.42, 110.00, 146.83),      # 2 Dm   no weapons
      (77.78, 116.54, 155.56),      # 3 Eb   the heat   (semitone lift = dread)
      (73.42,  98.00, 146.83),      # 4 Dsus the question
      (87.31, 130.81, 174.61),      # 5 F    the skin   (relative major = relief)
      (77.78, 116.54, 155.56),      # 6 Eb   the lock
      (98.00, 146.83, 196.00),      # 7 G    the curve
      (73.42, 110.00, 146.83)]      # 8 Dm   the proof


def build_bed():
    # continuous low drone, re-articulated at every cut
    for i, st in enumerate(SCENE):
        d = END[i] - st + 0.9
        dl, dr = drone(CH[i], d, 0.115)
        place_st(dl, dr, st - 0.25, 1.0, f'drone{i+1}', 'bed')
        # a trace of the true root, kept quiet — the only thing in the bed
        # that is allowed to live below 120 Hz
        place(pad([CH[i][0]], d * 0.9, 0.030), st - 0.15, 1.0, 0.0,
              f'root{i+1}', 'bed')
        place(pad([f * 4 for f in CH[i]], d * 0.85, 0.060), st + 0.1, 1.0,
              0.34 * (1 if i % 2 else -1), f'pad{i+1}', 'bed')

    # wind: 0.09 Hz swells, hard left/right alternating
    t = 0.0
    k = 0
    while t < DUR:
        place(wind(5.4, 420 + 180 * (k % 3)), t, 0.030,
              0.55 if k % 2 else -0.55, '', 'bed')
        t += 3.6
        k += 1

    # frame drum: sparse, then on every 1 and 3 from the title card on
    beat = 0
    t = 0.0
    while t < DUR - 0.2:
        bar = beat // 4
        pos = beat % 4
        heavy = (pos == 0)
        if t < 19.2:
            hit = (pos == 0 and bar % 2 == 0)
            g = 0.12
        elif t < 37.3:
            hit = (pos == 0 or pos == 2)
            g = 0.16 if heavy else 0.085
        else:
            hit = (pos == 0 or pos == 2)
            g = 0.19 if heavy else 0.10
        if hit and t > 1.2:
            place(drum(0.62 if heavy else 0.42, 124 if heavy else 108),
                  t, g, 0.17 if (beat // 4) % 2 == 0 else -0.17, 'drum', 'bed')
        beat += 1
        t = beat * SPB

    # sand shaker on eighths, panned in a slow figure-of-eight
    e = 0
    t = 0.0
    while t < DUR - 0.2:
        if t > 3.0:
            acc = (e % 4 == 0)
            g = 0.094 if acc else 0.050
            if t > 37.3: g *= 1.22
            place(shaker(0.14 if acc else 0.11, 1.0 if acc else 0.86),
                  t + (0.004 if e % 2 else 0.0), g,
                  0.62 * math.sin(e * 0.37), '', 'bed')
        e += 1
        t = e * SPB / 2

    # bone flute: one phrase per act, answering the narration, never under it
    for st, f, d in ((5.90, 293.66, 0.95), (18.10, 311.13, 0.95),
                     (23.60, 220.00, 1.05), (36.20, 349.23, 1.00),
                     (51.40, 293.66, 1.45)):
        place(flute(f, d), st, 0.085, -0.18, 'flute', 'bed')


# ───────────────────────────────────────────── transitions
def build_transitions():
    for i, c in enumerate(CUTS):
        pan = 0.5 if i % 2 == 0 else -0.5
        place(whoosh(0.50, 220, 2300), c - 0.30, 0.17, pan, f'cut{i+1}')
        place(sub(96, 54, 0.60), c - 0.015, 0.13, 0.0, f'cut_sub{i+1}')
        place(cloth(0.22), c + 0.02, 0.10, -pan, '')
    # riser into the title card and into the proof
    place(riser(1.15, 160, 1080), 19.20 - 1.15, 0.16, 0.0, 'riser_title')
    place(riser(0.95, 180, 980), 45.40 - 0.95, 0.13, 0.0, 'riser_proof')


# ───────────────────────────────────────────── cues, locked to wide.py
def build_cues():
    S = SCENE

    def at(i, lt): return S[i] + lt

    # — S1 the chase: a running footfall bed under the whole beat
    t = 0.18
    step = 0
    while t < 6.55:
        place(footfall(0.22, 1.0 if step % 2 == 0 else 0.86), t,
              0.085 * min(1.0, 0.45 + t / 3.0), 0.30 * math.sin(step * 1.1),
              'step' if step == 0 else '')
        step += 1
        t += 60.0 / 168.0                     # 168 steps/min — a real jog cadence
    place(tap(900, 0.10), at(0, 0.55), 0.10, 0.45, 's1_quarry')
    place(whoosh(0.34, 300, 1500), at(0, 2.10), 0.09, 0.0, 's1_gap')
    place(tap(1250, 0.085), at(0, 3.50), 0.12, 0.0, 's1_chip')

    # — S2 the objects: two refusals, two keeps
    for lt, keep in ((0.70, False), (1.05, False), (1.55, True), (1.90, True)):
        place(cloth(0.20), at(1, lt), 0.11, -0.3 + 0.2 * lt, '')
        if keep:
            place(tap(1500, 0.09, 0.8), at(1, lt + 0.08), 0.13, 0.22, 's2_keep')
        else:
            place(sub(132, 74, 0.30), at(1, lt + 0.26), 0.09, -0.25, 's2_strike')
    place(tap(1250, 0.085), at(1, 3.30), 0.12, 0.0, 's2_chip')

    # — S3 the heat: the number lands, the mercury climbs
    place(sub(108, 56, 0.80), at(2, 0.75), 0.15, 0.0, 's3_number')
    n = int(1.1 * SR)
    climb = flt(noise(1.1), 400, 3400) * np.linspace(0, 1, n) ** 2.0
    place(climb * env(n, 0.08, 0.35, 2.0), at(2, 1.55), 0.075, 0.2, 's3_mercury')
    place(tap(1250, 0.085), at(2, 3.40), 0.12, 0.0, 's3_chip')

    # — S4 the question: the title is the loudest cue in the film
    place(sub(102, 52, 0.90), at(3, 0.55), 0.17, 0.0, 's4_title')
    place(tap(2100, 0.11, 1.0), at(3, 1.15), 0.10, 0.1, 's4_sub')
    place(tap(1250, 0.085), at(3, 2.70), 0.12, 0.0, 's4_chip')

    # — S5 the skin: 380 glands stippling in, as a fine granular wash
    for i in range(46):
        u = i / 45
        place(shaker(0.085, 1.25), at(4, 0.85 + u * 2.3),
              0.020 + 0.016 * (1 - u), 0.6 * math.sin(i * 0.9), '')
    place(tap(1700, 0.09), at(4, 1.10), 0.09, -0.2, 's5_counter')
    place(sub(112, 60, 0.55), at(4, 3.30), 0.10, 0.0, 's5_bars')

    # — S6 the lock: the gait pulse IS the point, so it is audible
    #   kudu fires every 1/2.4 s; the human row fires on every second one
    for k in range(11):
        tt = at(5, 1.30 + k * (1.0 / 2.4))
        if tt > END[5] - 0.3: break
        place(drum(0.30, 150, 86), tt, 0.105, 0.42, 's6_kudu' if k == 0 else '')
        if k % 2 == 0:
            place(tap(760, 0.10, 0.4), tt + 0.012, 0.085, -0.42,
                  's6_human' if k == 0 else '')
    place(sub(106, 58, 0.62), at(5, 2.40), 0.11, 0.0, 's6_pant')
    place(tap(1250, 0.085), at(5, 3.50), 0.12, 0.0, 's6_chip')

    # — S7 the curve: two lines drawing, pitched apart
    for nm, lt0, f0_, f1_, pan in (('kudu', 1.15, 300, 980, 0.40),
                                   ('man', 1.55, 260, 330, -0.40)):
        nn = int(2.4 * SR)
        tt = np.arange(nn) / SR
        u = tt / 2.4
        f = f0_ * (f1_ / f0_) ** u
        x = np.sin(2 * math.pi * np.cumsum(f) / SR) * 0.30
        x += flt(noise(2.4), 1200, 5000) * 0.22
        place(x * env(nn, 0.10, 0.5, 1.8), at(6, lt0), 0.055, pan, f's7_{nm}')
    place(tap(1250, 0.085), at(6, 4.60), 0.12, 0.0, 's7_chip')

    # — S8 the proof: two numbers, then the aphorism
    place(sub(106, 58, 0.70), at(7, 0.75), 0.12, -0.35, 's8_hunter')
    place(sub(118, 64, 0.70), at(7, 1.15), 0.13, 0.35, 's8_oryx')
    place(tap(1250, 0.085), at(7, 2.30), 0.11, 0.0, 's8_chip')
    place(sub(100, 50, 0.88), at(7, 4.00), 0.15, 0.0, 's8_aph1')
    place(sub(96, 46, 1.10), at(7, 4.90), 0.16, 0.0, 's8_aph2')


# ───────────────────────────────────────────── space
def silk(buf, wet=0.28):
    """Short, dark, diffuse tail. Taps are prime-spaced so nothing flutters."""
    out = buf.copy()
    taps = [(0.0131, .50), (0.0193, .44), (0.0271, .38), (0.0379, .32),
            (0.0533, .27), (0.0727, .22), (0.1013, .17), (0.1399, .13),
            (0.1933, .10), (0.2663, .075), (0.3671, .055), (0.5051, .038)]
    acc = np.zeros_like(buf)
    for k, (dt, g) in enumerate(taps):
        i = int(dt * SR)
        if i >= buf.shape[1]: break
        sgn = 1 if k % 2 == 0 else -1
        acc[0, i:] += buf[0, :-i] * g * (1.0 + 0.10 * sgn)
        acc[1, i:] += buf[1, :-i] * g * (1.0 - 0.10 * sgn)
    acc[0] = flt(acc[0], 180, 4200)
    acc[1] = flt(acc[1], 180, 4200)
    return out * (1 - wet * 0.42) + acc * wet


def main():
    build_bed()
    build_transitions()
    build_cues()

    wet = silk(SFX, 0.28)
    mix = BUF + wet

    # bus shaping: tame the low mud, keep a little air, widen
    mix[0] = flt(mix[0], 46, 15000)
    mix[1] = flt(mix[1], 46, 15000)
    # low-shelf cut: v1 measured 34 % of all energy under 120 Hz
    for c in (0, 1):
        mix[c] -= flt(mix[c], 0, 155, 2) * 0.58
    mid = (mix[0] + mix[1]) * 0.5
    side = (mix[0] - mix[1]) * 0.5
    side = flt(side, 170, 16000) * 2.60
    air = flt(mid, 6200, 16000) * 1.70
    pres = flt(mid, 2400, 5200) * 0.42
    mix = np.vstack([mid + side + air + pres, mid - side + air + pres])

    peak = np.max(np.abs(mix))
    mix = mix / max(peak, 1e-9) * 0.72
    # soft knee, no hard clip anywhere
    mix = np.tanh(mix * 1.18) / math.tanh(1.18)

    # 40 ms fades so the file itself can never click
    f = int(0.040 * SR)
    mix[:, :f] *= np.linspace(0, 1, f) ** 2
    mix[:, -f:] *= np.linspace(1, 0, f) ** 2

    os.makedirs('/home/user/build', exist_ok=True)
    import wave
    pcm = (np.clip(mix.T, -1, 1) * 32767).astype('<i2')
    with wave.open('/home/user/build/wide_bed.wav', 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())

    LOG.sort()
    with open('/home/user/WIDE_AUDIO_LEDGER.csv', 'w') as fh:
        fh.write('t,tag,gain,pan\n')
        for r in LOG:
            fh.write(','.join(str(x) for x in r) + '\n')
    rms = float(np.sqrt(np.mean(mix ** 2)))
    print(f'bed written  {DUR}s  events={len(LOG)}  rms={20*math.log10(rms):.1f} dBFS'
          f'  peak={20*math.log10(np.max(np.abs(mix))):.1f} dBFS')


if __name__ == '__main__':
    main()
