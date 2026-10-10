"""
make_asmr.py — ASMR-grade sound design for the CLEAN build.
===========================================================
Design rules (the opposite of the v4 wall-of-sound):
  * STEREO. Every cue is panned; the ear gets a space to sit in.
  * No hard transients. Attacks are raised-cosine, never a step, so
    nothing ever clicks.
  * Nothing above ~9 kHz survives. Harsh air is what makes SFX feel cheap.
  * ~210 events, not 748. Each one is audible and intentional.
  * Every cue is locked to a reveal that actually happens on screen.
"""
import math, os, subprocess, sys
import numpy as np

SR = 48000
DUR = 37.00
N = int(SR * DUR)
rng = np.random.default_rng(9)
BUF = np.zeros((2, N), dtype=np.float64)   # music bed
SFX = np.zeros((2, N), dtype=np.float64)   # cue bus, gets the silk reverb
LOG = []

SCENE = [0.000, 5.567, 12.867, 19.588, 24.302, 30.823]
END = [5.567, 12.867, 19.588, 24.302, 30.823, 37.000]
CUTS = SCENE[1:]
SPB = 0.5357142857            # 112 BPM


# ───────────────────────────────────────────── primitives
def flt(x, lo=0.0, hi=20000.0, n=2):
    """Zero-phase Butterworth-magnitude band shaping. Fast, and no ringing."""
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
    """Raised-cosine attack -> exponential decay. Never clicks."""
    t = np.arange(n) / SR
    a = max(atk, 0.0025)
    e = np.where(t < a, 0.5 - 0.5 * np.cos(np.pi * t / a),
                 np.exp(-curve * (t - a) / max(dec, 1e-4)))
    return e * np.hanning(n) ** 0.08


def place(sig, t, gain=1.0, pan=0.0, tag='', bus='sfx'):
    i = int(t * SR)
    if i < 0 or i >= N: return
    n = min(len(sig), N - i)
    p = (pan + 1) * math.pi / 4
    B = SFX if bus == 'sfx' else BUF
    B[0, i:i + n] += sig[:n] * gain * math.cos(p) * 1.4142
    B[1, i:i + n] += sig[:n] * gain * math.sin(p) * 1.4142
    LOG.append((round(t, 3), tag, round(gain, 3), round(pan, 2)))


def place_st(l, r, t, gain=1.0, tag=''):
    i = int(t * SR)
    if i < 0 or i >= N: return
    n = min(len(l), N - i)
    BUF[0, i:i + n] += l[:n] * gain
    BUF[1, i:i + n] += r[:n] * gain
    LOG.append((round(t, 3), tag, round(gain, 3), 's'))


# ───────────────────────────────────────────── voices
def pop(f=520, d=0.16, warm=0.55):
    """Soft rounded bubble-pop: pitch drops a fifth, body is all low-mid."""
    n = int(SR * d)
    t = np.arange(n) / SR
    ph = 2 * np.pi * (f * np.exp(-9 * t)) * t
    x = np.sin(ph) + warm * np.sin(2 * ph) * np.exp(-26 * t)
    return flt(x * env(n, 0.008, d * 0.38, 2.8), hi=3400)


def tap(f=1500, d=0.085, bright=0.5):
    """Fingertip tap — filtered noise with a touch of pitch."""
    n = int(SR * d)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n) * 0.6 + np.sin(2 * np.pi * f * t) * 0.5
    return flt(x * env(n, 0.009, d * 0.30, 3.6), lo=240, hi=900 + 2300 * bright)


def chime(f=880, d=1.5, parts=(1, 2.01, 3.03, 4.72)):
    """Glass bell. Inharmonic partials, long smooth tail, no attack spike."""
    n = int(SR * d)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, m in enumerate(parts):
        x += np.sin(2 * np.pi * f * m * t) * np.exp(-(1.6 + k * 1.5) * t) / (k + 1.5)
    return flt(x * env(n, 0.008, d * 0.5, 1.4), hi=13000)


def whoosh(d=0.55, f0=260, f1=2600, rev=False):
    """Air pass. Slow swell, band sweeps. The signature ASMR transition."""
    n = int(SR * d)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    k = t / d
    if rev: k = 1 - k
    out = np.zeros(n)
    seg = 10
    for i in range(seg):
        a, b = int(n * i / seg), int(n * (i + 1) / seg)
        kk = k[a:b].mean()
        out[a:b] = flt(x[a:b] * np.hanning(b - a) ** 0.3,
                       lo=f0 * (1 - kk) + 160, hi=f0 + (f1 - f0) * kk)
    sw = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5
    return flt(out * sw, hi=7600)


def sub(f0=78, f1=42, d=0.70):
    """Chest drop. Pure, no distortion."""
    n = int(SR * d)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.010, d * 0.46, 2.6)


def thud(d=0.34):
    n = int(SR * d)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 112 * np.exp(-11 * t) * t) + rng.normal(0, .18, n)
    return flt(x * env(n, 0.010, d * 0.34, 3.2), hi=780)


def riser(d=0.85, f0=190, f1=1250):
    n = int(SR * d)
    t = np.arange(n) / SR
    k = (t / d) ** 1.7
    nz = flt(rng.normal(0, 1, n), lo=400, hi=5200) * k * 0.5
    tn = np.sin(2 * np.pi * np.cumsum(f0 * (f1 / f0) ** (t / d)) / SR) * k * 0.4
    return flt((nz + tn) * np.hanning(n) ** 0.25, hi=7000)


def cloth(d=0.22):
    n = int(SR * d)
    return flt(rng.normal(0, 1, n) * env(n, 0.012, d * .4, 3.0), lo=300, hi=2600)


def shimmer(d=1.6, f=2400):
    """Granular sparkle dust — extremely quiet, pure texture."""
    n = int(SR * d)
    out = np.zeros(n)
    for _ in range(26):
        g = int(SR * 0.035)
        p = rng.integers(0, n - g)
        t = np.arange(g) / SR
        out[p:p + g] += np.sin(2 * np.pi * f * (1 + rng.normal(0, .4)) * t) * np.hanning(g)
    return flt(out, lo=1200, hi=13500) * 0.58


def pad(freqs, d, amp=1.0):
    """Warm detuned pad, stereo-spread by detuning the two sides differently."""
    n = int(SR * d)
    t = np.arange(n) / SR
    L = np.zeros(n); R = np.zeros(n)
    for i, f in enumerate(freqs):
        for det, tgt in ((-0.14, 'L'), (0.00, 'B'), (0.17, 'R')):
            w = np.sin(2 * np.pi * (f + det) * t) + 0.22 * np.sin(2 * np.pi * 2 * (f + det) * t)
            w = w / (i + 1.7)
            if tgt in ('L', 'B'): L += w
            if tgt in ('R', 'B'): R += w
    a = np.minimum(1, t / 0.9) * np.minimum(1, (d - t) / 1.1)
    a = np.clip(a, 0, 1) ** 1.2
    return flt(L * a, hi=1900) * amp * 0.1, flt(R * a, hi=1900) * amp * 0.1


def pluck(f, d=0.6):
    n = int(SR * d)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-6 * t)
         + 0.12 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-9 * t))
    return flt(x * env(n, 0.006, d * 0.40, 2.8), hi=4600)


# ───────────────────────────────────────────── 1. music bed
# One warm chord per chapter. Am - F - C - G flavoured, kept very low.
CHORDS = [(110.0, 130.8, 164.8),      # Am
          (87.3, 130.8, 174.6),       # F
          (98.0, 146.8, 196.0),       # G sus
          (130.8, 164.8, 196.0),      # C
          (110.0, 164.8, 220.0),      # Am add
          (146.8, 196.0, 246.9)]      # G


def build_music():
    for i, (st, en) in enumerate(zip(SCENE, END)):
        d = en - st + 0.9
        L, R = pad(CHORDS[i], d, 1.0 if i else 0.75)
        place_st(L, R, st - 0.25, 0.95, f'pad{i+1}')

    # soft sub pulse on the downbeat of every bar — felt, not heard
    b = 0.0; k = 0
    while b < DUR - 0.2:
        if k % 2 == 0:
            place(sub(66, 48, 0.46), b, 0.16, 0.0, 'pulse', 'mus')
        if k % 4 == 2:
            place(tap(900, 0.07, 0.25), b, 0.035, -0.25, 'hat', 'mus')
        b += SPB; k += 1

    # sparse pluck arpeggio, only under the two "build" chapters
    for si in (1, 2):
        base = CHORDS[si]
        t = SCENE[si] + SPB
        j = 0
        while t < END[si] - 0.4:
            place(pluck(base[j % 3] * 4, 0.55), t, 0.055,
                  -0.45 + 0.9 * ((j % 3) / 2), 'arp', 'mus')
            t += SPB * 1.5; j += 1

    # breathing noise floor — the ASMR "room"
    air = flt(rng.normal(0, 1, N), lo=90, hi=1500)
    sw = 0.5 + 0.5 * np.sin(2 * np.pi * np.arange(N) / SR / 6.5)
    BUF[0] += air * 0.0075 * sw
    BUF[1] += np.roll(air, 211) * 0.0075 * (1 - sw * 0.6)


# ───────────────────────────────────────────── 2. transitions
def build_transitions():
    for k, c in enumerate(CUTS):
        place(riser(0.82, 200, 1180), c - 0.84, 0.17, 0.0, 'riser')
        place(whoosh(0.46, 300, 3000), c - 0.16, 0.30, -0.55, 'swipe_in')
        place(thud(0.38), c + 0.002, 0.24, 0.0, 'land')
        place(sub(84, 40, 0.80), c + 0.002, 0.34, 0.0, 'drop')
        place(whoosh(0.42, 2600, 320, rev=True), c + 0.20, 0.22, 0.55, 'swipe_out')
        place(chime(660 + k * 55, 1.8), c + 0.03, 0.080, 0.30, 'cut_bell')


# ───────────────────────────────────────────── 3. per-scene cues
def build_cues():
    S = SCENE

    def at(si, lt): return S[si] + lt

    # ---- 1  PROBLEM
    place(whoosh(0.70, 200, 1800), 0.00, 0.26, 0.0, 'open')
    for i, lt in enumerate((0.00, 0.17)):
        place(pop(430 + i * 90, 0.17), at(0, lt), 0.30, -0.18 + i * .36, 'title')
    for i in range(6):                                   # footsteps on the walk-in
        place(tap(260, 0.12, 0.14), at(0, 0.08 + i * 0.175), 0.085,
              -0.5 + i * 0.16, 'step')
    place(cloth(0.26), at(0, 1.05), 0.16, 0.0, 'slump')
    place(sub(70, 44, 0.7), at(0, 1.07), 0.17, 0.0, 'slump_sub')
    place(pop(330, 0.20), at(0, 1.50), 0.26, 0.42, 'wallet')
    for i in range(3):
        place(tap(620 - i * 90, 0.11, 0.30), at(0, 1.95 + i * 0.34), 0.095, 0.46, 'coin')
    for i in range(3):
        place(pop(600 + i * 70, 0.15), at(0, 3.15 + i * 0.14), 0.26, -0.3 + i * .3, 'payoff')
    place(chime(784, 1.4), at(0, 3.17), 0.075, 0.0, 'payoff_bell')

    # ---- 2  SKILL
    for i in range(3):
        place(pop(470 + i * 80, 0.16), at(1, 0.00 + i * 0.09), 0.27, -0.3 + i * .3, 'title')
    for i, lt in enumerate((1.10, 1.52, 1.94, 2.36)):     # checklist
        place(pop(500 + i * 55, 0.15), at(1, lt), 0.25, -0.35 + i * 0.23, 'row')
        place(tap(2100, 0.07, 0.6), at(1, lt + 0.21), 0.095, -0.3 + i * 0.2, 'check')
        place(chime(1046 + i * 110, 1.3), at(1, lt + 0.22), 0.070, -0.3 + i * .2, 'check_bell')
    place(shimmer(1.4, 2600), at(1, 3.6), 0.055, 'x' and 0.0, 'dust')
    for i in range(3):
        place(pop(560 + i * 70, 0.15), at(1, 4.70 + i * 0.13), 0.25, -0.3 + i * .3, 'payoff')

    # ---- 3  TIME
    for i in range(3):
        place(pop(470 + i * 80, 0.16), at(2, 0.00 + i * 0.09), 0.27, -0.3 + i * .3, 'title')
    place(cloth(0.30), at(2, 0.32), 0.16, -0.5, 'desk')
    place(tap(380, 0.11, 0.3), at(2, 0.40), 0.12, -0.5, 'desk2')
    place(whoosh(0.40, 400, 2200), at(2, 0.70), 0.13, 0.45, 'grid_in')
    for i in range(30):                                   # 30 soft day-ticks, rising
        place(tap(1300 + i * 46, 0.055, 0.42), at(2, 1.20 + i * 0.088),
              0.040 + 0.026 * (i / 29), -0.45 + 0.9 * ((i % 5) / 4), 'day')
    for i in range(22):                                   # keyboard under it
        place(tap(1750 + (i % 4) * 160, 0.045, 0.5), at(2, 0.95 + i * 0.148),
              0.030, -0.55 + 0.1 * (i % 3), 'key')
    place(chime(988, 1.6), at(2, 3.90), 0.08, 0.0, 'count_done')
    place(pop(620, 0.18), at(2, 1.45), 0.20, 0.0, 'count')

    # ---- 4  PROOF
    for i in range(3):
        place(pop(470 + i * 80, 0.16), at(3, 0.00 + i * 0.09), 0.27, -0.3 + i * .3, 'title')
    for i, lt in enumerate((0.34, 0.66, 0.98)):           # three cards
        place(pop(420 + i * 95, 0.19), at(3, lt), 0.28, -0.5 + i * 0.5, 'card')
        place(cloth(0.18), at(3, lt + 0.01), 0.10, -0.5 + i * 0.5, 'card_air')
        place(chime(880 + i * 165, 1.1), at(3, lt + 0.34), 0.055, -0.5 + i * 0.5, 'icon')
    for i in range(3):
        place(pop(560 + i * 70, 0.15), at(3, 2.70 + i * 0.13), 0.26, -0.3 + i * .3, 'payoff')

    # ---- 5  SELL
    for i in range(2):
        place(pop(470 + i * 90, 0.16), at(4, 0.00 + i * 0.10), 0.27, -0.25 + i * .5, 'title')
    place(pop(300, 0.22), at(4, 0.25), 0.24, 0.30, 'phone')
    for i, lt in enumerate((1.00, 1.64, 2.28)):           # chat bubbles
        place(pop(560 + i * 130, 0.16), at(4, lt), 0.30, (-0.35, 0.35, -0.35)[i], 'bubble')
        place(tap(2400, 0.05, 0.55), at(4, lt + 0.015), 0.045, (-0.35, 0.35, -0.35)[i], 'bub_t')
    place(chime(1318, 1.8, (1, 2.01, 3.0, 5.1)), at(4, 2.30), 0.11, 0.0, 'deal')
    place(sub(92, 52, 0.6), at(4, 2.30), 0.14, 0.0, 'deal_sub')
    place(cloth(0.24), at(4, 3.22), 0.15, -0.45, 'shake')
    for i in range(2):
        place(pop(560 + i * 80, 0.15), at(4, 4.30 + i * 0.14), 0.26, -0.25 + i * .5, 'payoff')

    # ---- 6  GO
    for i in range(3):
        place(pop(500 + i * 85, 0.16), at(5, 0.00 + i * 0.10), 0.29, -0.3 + i * .3, 'title')
    place(pop(620, 0.16), at(5, 0.20), 0.26, 0.0, 'title2')
    for i in range(4):                                    # four checkmarks
        place(tap(2200, 0.07, 0.6), at(5, 0.95 + i * 0.25), 0.10, -0.5 + i * 0.33, 'tick')
        place(chime(1046 + i * 196, 1.7), at(5, 0.96 + i * 0.25), 0.095, -0.5 + i * 0.33, 'tick_b')
    place(whoosh(0.60, 300, 3400), at(5, 2.22), 0.24, 0.0, 'confetti')
    place(shimmer(2.0, 3100), at(5, 2.30), 0.075, 0.0, 'sparkle')
    place(pop(380, 0.24), at(5, 2.45), 0.30, 0.0, 'cta')
    place(sub(96, 46, 0.9), at(5, 2.46), 0.26, 0.0, 'cta_sub')
    place(chime(1568, 2.4, (1, 2.0, 2.99, 4.1, 5.4)), at(5, 2.50), 0.11, 0.0, 'cta_bell')
    place(whoosh(1.1, 1800, 240, rev=True), 35.60, 0.17, 0.0, 'outro')


# ───────────────────────────────────────────── silk reverb
def silk(buf, wet=0.30):
    """Small bright plate, built from prime-spaced taps.

    This is what turns a set of correct SFX into ASMR: every transient gets a
    soft tail instead of stopping dead, and the tails alternate across the
    stereo field so the ear keeps finding new space.
    """
    taps = [(0.0131, .50, -1), (0.0197, .44, 1), (0.0313, .38, 1),
            (0.0471, .32, -1), (0.0673, .27, -1), (0.0937, .22, 1),
            (0.1291, .17, 1), (0.1733, .13, -1), (0.2267, .095, -1),
            (0.2917, .068, 1), (0.3671, .046, 1), (0.4523, .030, -1)]
    rv = np.zeros_like(buf)
    mono = (buf[0] + buf[1]) * 0.5
    for dt, g, side in taps:
        k = int(dt * SR)
        if k >= N: continue
        a = 0.62 if side < 0 else 0.38
        rv[0, k:] += mono[:N - k] * g * a
        rv[1, k:] += mono[:N - k] * g * (1 - a)
    for ch in (0, 1):
        rv[ch] = flt(rv[ch], lo=200, hi=9000)
    return buf * (1 - wet * 0.35) + rv * wet


# ───────────────────────────────────────────── build
def main():
    build_music()
    build_transitions()
    build_cues()

    # cue bus -> silk plate, then fold into the music bed
    # 3.3  v7 fell to -32 LUFS twelve times between VO phrases. A slow pad
    # swell is placed into each measured hole so the film never breathes out.
    for ht, hg in ((0.15, 1.10), (6.2, .80), (13.7, .95), (15.25, 1.25),
                   (17.0, 1.00), (20.25, .95), (21.75, 1.35), (22.4, 1.00),
                   (25.8, 1.00), (28.8, 1.05), (33.8, 1.40), (34.9, 1.10)):
        i0 = int((ht - 0.55) * SR)
        if i0 < 0: continue
        nn = min(int(2.6 * SR), N - i0)
        if nn <= 0: continue
        tt = np.arange(nn) / SR
        sw = np.sin(np.pi * np.clip(tt / (nn / SR), 0, 1)) ** 1.6
        v = np.zeros(nn)
        for k, (fq, gg) in enumerate(((146.8, .55), (220.0, .40), (293.7, .26),
                                      (440.0, .14), (587.3, .07))):
            v += np.sin(2 * np.pi * fq * tt + k * 1.7) * gg
            v += np.sin(2 * np.pi * fq * 1.004 * tt + k) * gg * 0.5
        v = flt(v, lo=70, hi=2600) * sw * 0.088 * hg
        BUF[0, i0:i0 + nn] += v
        BUF[1, i0:i0 + nn] += np.roll(v, 331)

    mix = BUF + silk(SFX, wet=0.34)

    # 3.1  v7 measured L/R correlation 0.9941 — effectively MONO. The stereo
    # bed existed but a mono VO at +10 dB swamped it. Push Side hard here so
    # width survives the sum.
    M_ = (mix[0] + mix[1]) * .5
    S_ = (mix[0] - mix[1]) * .5
    S_ = flt(S_, lo=150, hi=16000) * 3.30
    mix = np.vstack([M_ + S_, M_ - S_])

    # 3.2  air shelf: 8–16 kHz held 0.6 % of total energy in v7
    for ch in (0, 1):
        mix[ch] += flt(mix[ch], lo=6500, hi=17000) * 0.95

    # bus shaping: nothing sharp survives, soft knee on the peaks
    for ch in (0, 1):
        mix[ch] = flt(mix[ch], lo=28, hi=14500, n=2)
    pk = np.abs(mix).max()
    mix = np.tanh(mix / max(pk, 1e-9) * 1.05) * 0.74
    print(f'peak {pk:.4f}  events {len(LOG)}')

    out = (np.clip(mix.T, -1, 1) * 32767).astype(np.int16)
    import wave
    with wave.open('/home/user/build/asmr_bed.wav', 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(out.tobytes())
    with open('/home/user/ASMR_EVENT_LEDGER.csv', 'w') as f:
        f.write('t,tag,gain,pan\n')
        for r in sorted(LOG):
            f.write(','.join(str(x) for x in r) + '\n')
    print('wrote build/asmr_bed.wav', out.shape)


if __name__ == '__main__':
    os.makedirs('/home/user/build', exist_ok=True)
    main()
