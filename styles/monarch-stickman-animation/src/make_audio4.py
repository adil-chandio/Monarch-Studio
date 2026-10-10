"""v4 soundtrack: playful doodle bed + cinematic transition hits + full cartoon SFX (37s)."""
import sys, math, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
sys.path.insert(0, '/home/user/src')
from timeline import SCENE_START, DUR_TOTAL

SR = 48000
N = int(SR * DUR_TOTAL)
rng = np.random.default_rng(31)
L = np.zeros(N); R = np.zeros(N)
CUTS = SCENE_START[1:]

def lp(x, f, o=4): return sosfilt(butter(o, min(f, 23000) / 24000, 'low', output='sos'), x)
def hp(x, f, o=4): return sosfilt(butter(o, max(f, 20) / 24000, 'high', output='sos'), x)
def bp(x, a, b, o=4): return sosfilt(butter(o, [max(a, 20) / 24000, min(b, 23000) / 24000], 'band', output='sos'), x)

def _ir(sec=1.6, dec=5.0, damp=7000):
    n = int(SR * sec)
    x = rng.normal(0, 1, n) * np.exp(-dec * np.linspace(0, 1, n))
    x = lp(x, damp); x[:int(.012 * SR)] = 0
    return x / (np.abs(x).max() + 1e-9) * .5
IR = _ir(); IR_BIG = _ir(2.6, 3.2, 6000)

def rev(x, mix=.2, big=False):
    k = IR_BIG if big else IR
    w = fftconvolve(x, k)[:len(x)]
    w *= (np.abs(x).max() + 1e-9) / (np.abs(w).max() + 1e-9)
    return x * (1 - mix) + w * mix

def add(x, at, pan=.5, g=1.0):
    i = int(at * SR)
    if i >= N: return
    if i < 0: x = x[-i:]; i = 0
    n = min(len(x), N - i)
    a = pan * np.pi / 2
    L[i:i + n] += x[:n] * math.cos(a) * 1.2 * g
    R[i:i + n] += x[:n] * math.sin(a) * 1.2 * g

# ---------------------------------------------------------- instruments
def kick(d=.42, g=.85):
    t = np.arange(int(SR * d)) / SR
    f = 46 + 95 * np.exp(-32 * t)
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-8 * t) * 1.6) * g

def sub808(d=1.1, f=44, slide=None, g=.6):
    t = np.arange(int(SR * d)) / SR
    fa = np.full(len(t), float(f))
    if slide: fa = f + (slide - f) * np.exp(-9 * t)
    x = np.sin(2 * np.pi * np.cumsum(fa) / SR) + .16 * np.sin(4 * np.pi * np.cumsum(fa) / SR)
    return np.tanh(x * np.minimum(1, t * 55) * np.exp(-1.6 * t) * 1.3) * g

def shaker(d=.07, g=.13):
    t = np.arange(int(SR * d)) / SR
    return hp(rng.normal(0, 1, len(t)), 7000) * np.exp(-45 * t) * g

def woodblock(f=900, d=.14, g=.3):
    t = np.arange(int(SR * d)) / SR
    return rev((np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.4 * t)) * np.exp(-38 * t) * g, .18)

def clap(d=.3, g=.3):
    t = np.arange(int(SR * d)) / SR
    x = np.zeros(len(t))
    for dl, gg in [(0, 1), (.01, .8), (.021, .6)]:
        k = int(dl * SR)
        x[k:] += (bp(rng.normal(0, 1, len(t)), 1200, 5200) * np.exp(-26 * t))[:len(t) - k] * gg
    return rev(x * g, .26)

def marimba(f, d=.45, g=.22):
    t = np.arange(int(SR * d)) / SR
    x = (np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-18 * t) +
         .2 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-30 * t))
    return rev(x * np.exp(-6.5 * t) * np.minimum(1, t * 900) * g, .22)

def pizz(f, d=.3, g=.2):
    t = np.arange(int(SR * d)) / SR
    x = sum(2 * ((t * f * (1 + dd)) % 1) - 1 for dd in (-.004, .004)) / 2
    return lp(x, 1800) * np.exp(-11 * t) * np.minimum(1, t * 700) * g

def whistle(f, d=.5, g=.16):
    t = np.arange(int(SR * d)) / SR
    vib = 1 + .012 * np.sin(2 * np.pi * 5.5 * t)
    env = np.minimum(1, t * 14) * np.minimum(1, (d - t) * 9) * np.exp(-.6 * t)
    return rev(np.sin(2 * np.pi * f * vib * t) * env * g, .3)

# ---------------------------------------------------------- SFX
def pencil(d=.35, g=.28):
    n = int(SR * d); t = np.linspace(0, 1, n)
    flut = .55 + .45 * np.sin(2 * np.pi * (38 + 25 * t) * np.linspace(0, d, n))
    return bp(rng.normal(0, 1, n), 1800, 9000) * flut * np.sin(np.pi * t) ** .8 * g

def pop(f0=650, d=.12, g=.3):
    t = np.arange(int(SR * d)) / SR
    f = f0 * (1 + 2.4 * np.exp(-55 * t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-26 * t) * g

def ding(f=1760, d=.6, g=.22):
    t = np.arange(int(SR * d)) / SR
    x = sum(np.sin(2 * np.pi * f * m * t) * np.exp(-dc * t) * gg
            for m, gg, dc in [(1, 1, 5), (2.01, .5, 8), (3.01, .25, 12)])
    return rev(x * np.minimum(1, t * 2000) * g, .35)

def boing(d=.45, g=.3):
    t = np.arange(int(SR * d)) / SR
    f = 420 * np.exp(-4 * t) + 90
    vib = 1 + .5 * np.sin(2 * np.pi * 11 * t) * np.exp(-3 * t)
    return np.sin(2 * np.pi * np.cumsum(f * vib) / SR) * np.exp(-6 * t) * g

def swish(d=.4, g=.3, up=True):
    n = int(SR * d); t = np.linspace(0, 1, n)
    nz = rng.normal(0, 1, n); out = np.zeros(n)
    ch, st = 18, max(1, n // 18)
    for i in range(ch):
        a, b = i * st, (i + 1) * st if i < ch - 1 else n
        pp = i / (ch - 1); pp = pp if up else 1 - pp
        c = float(np.clip(380 * (26 ** pp), 280, 14000))
        pre = max(0, a - 1800)
        out[a:b] = bp(nz[pre:b], c * .6, c * 1.75)[a - pre:][:b - a]
    return out * np.sin(np.pi * t) ** 1.2 * g

def impact(d=1.9, g=.85):
    t = np.arange(int(SR * d)) / SR
    boom = np.sin(2 * np.pi * (78 * np.exp(-3.4 * t) + 33) * t) * np.exp(-2.8 * t)
    sub = np.sin(2 * np.pi * 36 * t) * np.exp(-3.2 * t) * .8
    crack = hp(rng.normal(0, 1, len(t)), 2600) * np.exp(-24 * t) * .45
    rum = lp(rng.normal(0, 1, len(t)), 160) * np.exp(-4.5 * t) * .6
    return np.tanh(rev(boom + sub + crack + rum, .35, True) * 1.2) * g

def riser(d=1.0, g=.3):
    n = int(SR * d); t = np.linspace(0, 1, n)
    f = 170 * (14 ** (t ** 1.3))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * t ** 2
    nz = bp(rng.normal(0, 1, n), 1500, 12000) * t ** 3
    trem = .6 + .4 * np.sin(2 * np.pi * (5 + 20 * t) * np.linspace(0, d, n))
    return (x * .4 + nz * .75) * trem * g

def rev_cym(d=.9, g=.3):
    n = int(SR * d); t = np.linspace(0, 1, n)
    return rev(hp(rng.normal(0, 1, n), 5000) * t ** 3, .4, True) * g

def coin_clink(f=2100, g=.2):
    t = np.arange(int(SR * .4)) / SR
    x = sum(np.sin(2 * np.pi * f * m * t) * np.exp(-dc * t) * gg
            for m, gg, dc in [(1, 1, 9), (1.9, .6, 13), (3.4, .3, 18)])
    return rev(x * np.minimum(1, t * 3000) * g, .3)

def register(g=.3):
    t = np.arange(int(SR * .9)) / SR
    bell = sum(np.sin(2 * np.pi * f * t) * np.exp(-6 * t) for f in (1318, 1760, 2093)) / 3
    ka = bp(rng.normal(0, 1, len(t)), 500, 4000) * np.exp(-40 * t) * .7
    return rev((bell + ka) * g, .3)

def firework(g=.26):
    t = np.arange(int(SR * .8)) / SR
    crack = hp(rng.normal(0, 1, len(t)), 3500) * np.exp(-30 * t)
    tail = hp(rng.normal(0, 1, len(t)), 6000) * np.exp(-5 * t) * .35
    return rev((crack + tail) * g, .4, True)

def typing(n=8, start=0.0, g=.16):
    for i in range(n):
        t = np.arange(int(SR * .05)) / SR
        add(hp(rng.normal(0, 1, len(t)), 3000) * np.exp(-90 * t) * g,
            start + i * .11 + float(rng.uniform(0, .02)), .5 + float(rng.uniform(-.2, .2)))

def tick_tock(start, count, step=.5, g=.14):
    for i in range(count):
        add(woodblock(1200 if i % 2 == 0 else 950, .1, g), start + i * step, .5 + (.12 if i % 2 else -.12))

# ---------------------------------------------------------- music bed
BPM = 112.0; SPB = 60 / BPM
NOTE = lambda n: 440.0 * 2 ** ((n - 9) / 12)
CHORDS = [(-12, [0, 4, 7]), (-7, [7, 11, 14]), (-10, [3, 7, 10]),
          (-5, [5, 9, 12]), (-7, [7, 11, 14]), (-12, [0, 4, 7])]
MELODY = [0, 4, 7, 12, 11, 7, 4, 2]

t = 0.0; i = 0
while t < DUR_TOTAL:
    si = max(k for k in range(6) if t >= SCENE_START[k])
    broot, triad = CHORDS[si]
    beat = i % 4
    add(kick(.42, .78 if beat in (0, 2) else .5), t, .5)
    if beat == 2:
        add(clap(.3, .26), t, .5)
    for j in range(2):
        add(shaker(.07, .12 if j else .16), t + j * SPB / 2, .62 if j else .38)
    if beat == 0:
        add(sub808(1.0, NOTE(broot) / 2, None, .34), t, .5)
    if i % 2 == 0:
        add(pizz(NOTE(broot + 12), .3, .16), t + SPB / 2, .35)
    for k, iv in enumerate(triad):
        add(marimba(NOTE(broot + 12 + iv), .45, .14), t + k * SPB / 4, .35 + k * .15)
    if i % 4 == 3:
        add(woodblock(1400, .12, .18), t + SPB * .75, .7)
    t += SPB; i += 1

for si in range(6):
    s0 = SCENE_START[si] + .8
    broot, _ = CHORDS[si]
    for k in range(4):
        add(whistle(NOTE(broot + 24 + MELODY[(si * 2 + k) % len(MELODY)]), .42, .11),
            s0 + k * SPB, .5 + .2 * math.sin(k))

# ---------------------------------------------------------- transition FX
for ci, c in enumerate(CUTS):
    add(riser(.85, .3), c - .85, .5)
    add(rev_cym(.8, .28), c - .8, .6 if ci % 2 else .4)
    add(swish(.5, .38, True), c - .3, .15 if ci % 2 == 0 else .85)
    add(impact(1.6, .62 + .06 * ci), c, .5)
    add(sub808(1.0, 40, 90, .42), c, .5)
    add(swish(.45, .3, False), c + .02, .85 if ci % 2 == 0 else .15)
    add(pencil(.5, .3), c + .06, .45)
    add(pop(520, .13, .26), c + .1, .5)

S1, S2, S3, S4, S5, S6 = SCENE_START
add(impact(2.0, .8), 0.0, .5)
add(pencil(.5, .3), .5, .45)

# S1
for k, dt in enumerate([1.1, 1.5]):
    add(pop(620 + k * 140, .12, .22), S1 + dt, .35 + k * .3)
add(ding(1320, .7, .2), S1 + 1.75, .62)
for k, dt in enumerate([1.95, 2.2, 2.45]):
    add(pop(700 + k * 160, .12, .24), S1 + dt, .3 + k * .2)
add(impact(1.3, .5), S1 + 2.9, .5)
add(ding(1760, .8, .22), S1 + 2.95, .5)
add(swish(.4, .22, True), S1 + 3.6, .3)
# S2
typing(16, S2 + .7, .14)
for k, dt in enumerate([1.5, 1.9, 2.3, 2.7]):
    add(pop(640 + k * 120, .12, .26), S2 + dt, .25)
    add(ding(1760 + k * 180, .5, .17), S2 + dt + .16, .3)
add(pencil(.45, .22), S2 + 1.1, .72)
for k in range(7):
    add(coin_clink(2400 + k * 110, .07), S2 + 1.6 + k * .4, .75)
add(pencil(.4, .2), S2 + 4.35, .5)
add(ding(2093, .6, .16), S2 + 4.6, .5)
# S3
tick_tock(S3 + 1.0, 10, .45, .13)
for k in range(30):
    add(pencil(.12, .13), S3 + 1.62 + k * .1, .5 + .3 * math.sin(k))
    if k % 5 == 4: add(pop(820, .09, .13), S3 + 1.66 + k * .1, .6)
typing(12, S3 + 2.3, .12)
add(impact(1.4, .5), S3 + 4.5, .5)
add(ding(1568, .9, .24), S3 + 4.55, .5)
# S4
for k, dt in enumerate([.35, .8, 1.25]):
    add(pencil(.42, .26), S4 + dt, .25 + k * .25)
    add(pop(560 + k * 140, .13, .26), S4 + dt + .4, .25 + k * .25)
    add(ding(1900 + k * 160, .45, .14), S4 + dt + .55, .25 + k * .25)
add(swish(.4, .26, True), S4 + 2.95, .5)
add(impact(1.2, .45), S4 + 3.05, .5)
# S5
for k, dt in enumerate([1.3, 2.0, 2.7]):
    add(pop(700 + k * 90, .12, .28), S5 + dt, .3 if k % 2 == 0 else .7)
    add(ding(1480 + k * 220, .45, .15), S5 + dt + .12, .5)
for k in range(3):
    add(pop(500 + k * 110, .12, .22), S5 + 3.45 + k * .25, .25 + k * .25)
add(swish(.35, .22, True), S5 + 2.95, .5)
add(boing(.4, .22), S5 + 4.25, .5)
add(impact(1.5, .6), S5 + 4.62, .5)
add(register(.34), S5 + 4.7, .5)
for k in range(5):
    add(coin_clink(1900 + k * 150, .2), S5 + 4.9 + k * .16, .4 + k * .08)
# S6
add(impact(2.2, .8), S6 + .3, .5)
add(sub808(1.4, 38, 100, .5), S6 + .3, .5)
add(swish(.9, .3, True), S6 + .05, .5)
for k in range(12):
    add(coin_clink(1700 + (k % 5) * 240, .14), S6 + .3 + k * .36, .2 + (k % 4) * .2)
for k in range(9):
    add(boing(.3, .12), S6 + .55 + k * .58, .5)
for k, dt in enumerate([1.2, 1.5, 1.8, 2.1]):
    add(pop(760 + k * 120, .12, .24), S6 + dt, .2 + k * .2)
    add(ding(1976 + k * 150, .5, .16), S6 + dt + .12, .5)
add(pencil(.5, .26), S6 + 2.6, .5)
add(ding(2637, 1.0, .24), S6 + 2.7, .5)
for k in range(7):
    add(firework(.22), S6 + 2.95 + k * .12, .2 + (k % 3) * .3)
add(impact(1.8, .7), S6 + 4.6, .5)
add(rev_cym(1.0, .3), S6 + 4.3, .5)

# ---------------------------------------------------------- master
mix = np.stack([L, R])
# sidechain pump off the 4-on-the-floor grid
pump = np.ones(N)
tt = 0.0
while tt < DUR_TOTAL:
    i0 = int(tt * SR); n = int(.3 * SR)
    env = 1 - .3 * np.exp(-np.linspace(0, 1, n) * 7) * (1 - np.linspace(0, 1, n) ** .4)
    seg = min(n, N - i0)
    if seg > 0: pump[i0:i0 + seg] = np.minimum(pump[i0:i0 + seg], env[:seg])
    tt += SPB
mix *= pump[None, :] * .8 + .2
mix = np.stack([hp(mix[0], 32), hp(mix[1], 32)])
m = (mix[0] + mix[1]) / 2; sd = (mix[0] - mix[1]) / 2
sd += hp(sd, 3000) * .45
mix = np.stack([m + sd, m - sd])
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix = mix / (np.abs(mix).max() + 1e-9) * .93
pcm = (np.clip(mix.T, -1, 1) * 32767).astype('<i2')
with wave.open('/home/user/build/music4.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('music4.wav', pcm.shape)
