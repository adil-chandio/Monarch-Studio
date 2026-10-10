"""
make_asmr_respect2.py — sound-design bed for IZZAT v2 (75.19 s, 33 shots, 32 distinct transitions).

What changed against make_asmr_respect.py (the user's notes on v1):
  * NO continuous noise floor (the `room` + `hiss` layers are gone — that was the "radio" sound) and NO
    0.6 s pulse/hat/shaker grid. The air in the bed-only passages now comes from the cues themselves.
  * One matched cue per transition KIND (32 boundaries, 15 kinds — respect2.PLAN is the single source of
    truth), built from new voices: braam, reverse swell, glass ting, metal ring, paper slide, doppler
    whoosh, impact, heartbeat, shatter burst. No identical cue twice in a row.
  * The chapter payoff bell is no longer the same 784 Hz chime nine times: every chapter gets its own
    payoff instrument.
  * Pads, plucks (per-chapter arpeggio, different pattern per chapter) and the swells in the VO holes stay.

Outputs  build/asmr_bed_respect2.wav  +  ASMR_RESPECT2_LEDGER.csv
"""
import math, os, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_asmr as M
import make_asmr_power as P
import timeline_respect2 as TL

SR = M.SR
DUR = TL.DUR_TOTAL
N = int(SR * DUR)
VO_FILES = [f'r{i + 1}_fit.wav' for i in range(9)]

M.DUR, M.N = DUR, N
M.BUF = np.zeros((2, N), dtype=np.float64)
M.SFX = np.zeros((2, N), dtype=np.float64)
M.LOG = []
M.SCENE = list(TL.SCENE_START)
M.END = list(TL.SCENE_END)
M.CUTS = M.SCENE[1:]
M.SPB = 0.600
M.CHORDS = [(110.00, 146.83, 174.61),           # 1 hook      Dm
            (116.54, 146.83, 174.61),           # 2 villain   Bb (unease)
            (130.81, 174.61, 220.00),           # 3 turn      F  (lift)
            (146.83, 174.61, 220.00),           # 4 rule 1    Dm (home)
            (116.54, 146.83, 174.61),           # 5 rule 2    Bb
            (130.81, 164.81, 196.00),           # 6 rule 3    C
            (146.83, 196.00, 233.08),           # 7 rule 4    Gm
            (130.81, 174.61, 220.00),           # 8 rule 5    F
            (146.83, 174.61, 220.00)]           # 9 payoff    Dm (resolves)
P.N, P.DUR, P.VO_FILES, P.S = N, DUR, VO_FILES, M.SCENE
P.TL = TL

place, place_st = M.place, M.place_st
pop, tap, chime, whoosh, sub, thud = M.pop, M.tap, M.chime, M.whoosh, M.sub, M.thud
riser, cloth, shimmer, pluck, flt, env = M.riser, M.cloth, M.shimmer, M.pluck, M.flt, M.env
air = P.air
rng = M.rng
S = M.SCENE


def at(si, lt):
    return S[si] + lt


def vo(si, k):
    return TL.VO_AT[si] + TL.PHRASES[si][k]


# ───────────────────────────────────────────── new voices (all band-limited, never click)
def braam(d=1.3, f0=55.0):
    """Cinematic low swell: detuned saw-ish stack, slow attack, dark. Used ONCE (the hero's entrance)."""
    n = int(SR * d)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, (m, g) in enumerate(((1, .9), (1.007, .7), (2, .45), (2.996, .3), (4.01, .18), (6, .08))):
        x += np.sin(2 * np.pi * f0 * m * t + k) * g
    sw = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.3
    return flt(x * sw, lo=48, hi=1900) * 0.5


def rswell(d=0.8, f=330.0):
    """Reverse swell: a tone + air that grows into the cut and stops dead."""
    n = int(SR * d)
    t = np.arange(n) / SR
    k = (t / d) ** 2.2
    tone = (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.01 * t)) * k
    nz = flt(rng.normal(0, 1, n), lo=900, hi=6500) * k * .6
    x = (tone * .5 + nz) * np.minimum(1, (d - t) / 0.012)
    return flt(x, hi=8000)


def ting(f=1760.0, d=0.9):
    """Glass ting: inharmonic, short, bright."""
    n = int(SR * d)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, (m, g) in enumerate(((1, 1), (2.76, .5), (5.4, .25), (8.93, .1))):
        x += np.sin(2 * np.pi * f * m * t) * g * np.exp(-(3 + 4 * k) * t)
    return flt(x * env(n, 0.002, d * .5, 1.5), lo=600, hi=14000) * 0.7


def metal(f=330.0, d=1.6):
    """Metal ring: inharmonic partials, long decay, a touch of beating."""
    n = int(SR * d)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, (m, g) in enumerate(((1, 1), (1.5, .5), (2.62, .45), (3.9, .3), (5.26, .18), (7.1, .09))):
        x += np.sin(2 * np.pi * f * m * t) * g * np.exp(-(1.8 + 1.2 * k) * t)
        x += np.sin(2 * np.pi * f * m * 1.003 * t) * g * .4 * np.exp(-(1.8 + 1.2 * k) * t)
    return flt(x * env(n, 0.003, d * .6, 1.3), lo=200, hi=12000) * 0.55


def paper(d=0.42):
    """Paper slide: filtered noise with a slide envelope (rises, drags, stops)."""
    n = int(SR * d)
    t = np.arange(n) / SR
    k = t / d
    e = np.sin(np.pi * k) ** .7 * (1 - .4 * k)
    return flt(rng.normal(0, 1, n) * e, lo=700, hi=7000) * 0.8


def doppler(d=0.5, f0=400.0, f1=3200.0):
    """Whip: band sweeps up fast, then falls away — a pass-by, not a swell."""
    n = int(SR * d)
    t = np.arange(n) / SR
    k = t / d
    out = np.zeros(n)
    seg = 12
    x = rng.normal(0, 1, n)
    for i in range(seg):
        a, b = int(n * i / seg), int(n * (i + 1) / seg)
        kk = k[a:b].mean()
        c = f0 + (f1 - f0) * math.sin(math.pi * min(kk / .55, 1) * .5) ** 2 if kk < .55 else f1 - (f1 - f0 * 1.5) * (kk - .55) / .45
        out[a:b] = flt(x[a:b] * np.hanning(b - a) ** .3, lo=max(120, c * .45), hi=c)
    sw = np.sin(np.pi * k) ** .9 * (1 - .35 * k)
    return flt(out * sw, hi=8500)


def impact(d=0.6):
    """Hit: thud + noise burst + sub tail, one body."""
    n = int(SR * d)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 95 * np.exp(-14 * t) * t) * np.exp(-9 * t)
    x += flt(rng.normal(0, 1, n), lo=300, hi=5000) * np.exp(-28 * t) * .5
    x += np.sin(2 * np.pi * 52 * t) * np.exp(-5 * t) * .5
    return flt(x * env(n, 0.003, d * .5, 2.4), lo=40, hi=6000) * 0.8


def heartbeat(d=0.5):
    """Two soft chest thumps (lub-dub)."""
    n = int(SR * d)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 58 * t) * np.exp(-26 * t)
    t2 = np.clip(t - 0.16, 0, None)
    x += np.sin(2 * np.pi * 52 * t2) * np.exp(-30 * t2) * .7 * (t > 0.16)
    return flt(x, lo=40, hi=320)


def glass_burst(d=0.9):
    """Shatter: dense micro-tings falling in pitch, bright air."""
    n = int(SR * d)
    out = np.zeros(n)
    for _ in range(46):
        g = int(SR * rng.uniform(0.02, 0.07))
        p = int(rng.uniform(0, 1) ** 1.6 * (n - g))
        tt = np.arange(g) / SR
        f = rng.uniform(1800, 6800)
        out[p:p + g] += np.sin(2 * np.pi * f * tt) * np.hanning(g) * rng.uniform(.3, 1)
    out += flt(rng.normal(0, 1, n), lo=3000, hi=10000) * np.exp(-6 * np.arange(n) / SR) * .35
    return flt(out, lo=1200, hi=14000) * 0.5


def click(f=2600.0):
    """Mechanical click (iris blades, strip edges)."""
    n = int(SR * 0.035)
    t = np.arange(n) / SR
    return flt(np.sin(2 * np.pi * f * t) * np.exp(-180 * t) + rng.normal(0, .3, n) * np.exp(-260 * t), lo=900, hi=9000)


def pad2(freqs, d, amp=1.0):
    """v2 pad: the v9 pad is two sines per note (fundamental + 0.22 x 2nd) -> ~95 % of its energy sits in
    120-500 Hz, and without the v1 hiss/room floor the whole mix tipped over the 58 % low-mid gate.
    Five partials (1 .. 5) low-passed at 2.6 kHz and a quiet x8 'glass' partial with a slow LFO."""
    n = int(SR * d)
    t = np.arange(n) / SR
    L = np.zeros(n); R = np.zeros(n)
    lfo = .5 + .5 * np.sin(2 * np.pi * t / 5.3)
    for i, f in enumerate(freqs):
        for det, tgt in ((-0.14, 'L'), (0.00, 'B'), (0.17, 'R')):
            w = np.zeros(n)
            for m, g in ((1, 1.0), (2, .36), (3, .24), (4, .16), (5, .10)):
                w += g * np.sin(2 * np.pi * m * (f + det) * t + m)
            w += .07 * np.sin(2 * np.pi * 8 * (f + det) * t) * lfo
            w = w / (i + 1.7)
            if tgt in ('L', 'B'): L += w
            if tgt in ('R', 'B'): R += w
    a = np.minimum(1, t / 0.9) * np.minimum(1, (d - t) / 1.1)
    a = np.clip(a, 0, 1) ** 1.2
    return flt(L * a, hi=2600) * amp * 0.085, flt(R * a, hi=2600) * amp * 0.085


# ───────────────────────────────────────────── music bed: pads + per-chapter plucks, no grid, no floor
PLUCK_PATTERN = {3: (0, 1, 2, 1), 4: (2, 0, 1, 0), 5: (0, 2, 1, 2), 6: (1, 0, 2, 0), 7: (2, 1, 0, 1)}
PLUCK_STEP = {3: 0.90, 4: 1.20, 5: 0.75, 6: 0.90, 7: 1.05}


def build_music():
    for i, (st, en) in enumerate(zip(M.SCENE, M.END)):
        d = en - st + 0.9
        L, R = pad2(M.CHORDS[i], d, 1.0 if i else 0.75)
        place_st(L, R, max(0.0, st - 0.25), 0.80, f'pad{i+1}')          # v1 dropped pad1 (t<0 -> return) and the hiss hid it
    for si in (3, 4, 5, 6, 7):
        base = M.CHORDS[si]
        t = M.SCENE[si] + 1.1
        j = 0
        pat = PLUCK_PATTERN[si]
        while t < M.END[si] - 0.6:
            mul = 4 if si != 4 else 2                              # S5 (waqt) an octave lower: clock-like
            place(pluck(base[pat[j % 4]] * mul, 0.55), t, 0.050, -0.45 + 0.9 * ((j % 3) / 2), 'arp', 'mus')
            t += PLUCK_STEP[si]; j += 1
    # S2 villain: a slow heartbeat under the "haan" chapter — diegetic, not a grid
    t = M.SCENE[1] + 0.9
    while t < M.END[1] - 1.0:
        place(heartbeat(), t, 0.11, 0.0, 'heart', 'mus')
        t += 1.15


# ───────────────────────────────────────────── transitions: one matched cue per kind
def tr_cue(kind, b, td, k):
    """kind -> a layered cue around boundary b (transition spans b-td/2 .. b+td/2)."""
    a = b - td / 2
    if kind == 'zoom':
        place(riser(td + .15, 240, 1400), a - .08, 0.11, 0.0, 'zoom_rise')
        place(sub(80, 44, 0.5), b, 0.10, 0.0, 'zoom_sub')
        place(air(0.12, 4000, 9500), b, 0.20, 0.2, 'zoom_air')
        place(ting(2093 if k % 2 else 2637, 0.6), b + .02, 0.045, 0.3, 'zoom_ting')
    elif kind == 'whip_h':
        place(doppler(td + .16, 350, 3600), a - .04, 0.30, -0.6, 'whip_pass')
        place(air(0.22, 3500, 9000, 0.03), a, 0.26, 0.5, 'whip_air')
        place(tap(520, 0.09, 0.3), b + .02, 0.09, 0.4, 'whip_land')
    elif kind == 'whip_v':
        place(doppler(td + .16, 600, 5200), a - .04, 0.26, 0.3, 'whipv_pass')
        place(air(0.20, 4500, 10500, 0.02), a + .02, 0.26, -0.4, 'whipv_air')
        place(thud(0.26), b + .01, 0.09, 0.0, 'whipv_land')
    elif kind == 'sweep':
        place(rswell(td + .2, 392 if k % 2 else 523), a - .2, 0.14, -0.3, 'sweep_swell')
        place(whoosh(td + .1, 300, 3400), a, 0.20, -0.5, 'sweep_light')
        place(ting(3136, 1.2), b, 0.06, 0.4, 'sweep_glass')
        place(shimmer(1.1, 6200), b + .05, 0.12, 0.2, 'sweep_dust')
    elif kind in ('cube_h', 'cube_v'):
        hi = kind == 'cube_v'
        place(whoosh(td + .1, 200, 1400, rev=hi), a, 0.16, 0.5 if hi else -0.5, 'cube_turn')
        place(pluck(110 if not hi else 146.8, 0.5), a + .05, 0.09, 0.0, 'cube_low')
        place(impact(0.5), b + td * .35, 0.16, 0.0, 'cube_lock')
        place(air(0.10, 4200, 9500), b + td * .35, 0.22, -0.3 if hi else 0.3, 'cube_flick')
        place(metal(220 if not hi else 294, 1.2), b + td * .36, 0.045, 0.2, 'cube_ring')
    elif kind == 'blur':
        place(rswell(td + .25, 220), a - .25, 0.10, 0.0, 'blur_swell')
        place(air(0.45, 2500, 8000, 0.12), a, 0.20, 0.0, 'blur_breath')
        place(chime(1174.7 if k % 2 else 987.8, 1.4), b + .05, 0.055, -0.2, 'blur_focus')
    elif kind == 'iris':
        place(click(3000), a, 0.16, -0.3, 'iris_click')
        place(whoosh(td, 900, 3800), a + .02, 0.16, 0.0, 'iris_open')
        place(ting(1568, 1.0), b + .03, 0.07, 0.3, 'iris_glass')
        place(click(2200), b + td / 2 - .02, 0.12, 0.3, 'iris_click2')
    elif kind == 'wedge':
        place(paper(td + .1), a, 0.30, 0.4, 'wedge_paper')
        place(sub(72, 46, 0.5), b, 0.09, 0.0, 'wedge_sub')
        place(tap(1100, 0.06, 0.5), b + .03, 0.11, -0.3, 'wedge_tap')
        place(shimmer(0.8, 5400), b + .06, 0.11, 0.3, 'wedge_dust')
    elif kind == 'doors':
        place(whoosh(td * .8, 500, 2800), a, 0.18, -0.6, 'door_l')
        place(whoosh(td * .8, 500, 2800), a + .03, 0.18, 0.6, 'door_r')
        place(impact(0.6), b + td * .32, 0.17, -0.25, 'door_slam_l')
        place(impact(0.6), b + td * .32 + .04, 0.14, 0.25, 'door_slam_r')
        place(metal(165, 1.8), b + td * .33, 0.06, 0.0, 'door_ring')
        place(air(0.16, 3800, 9800), b + td * .33, 0.20, 0.0, 'door_air')
    elif kind == 'spin':
        place(doppler(td + .25, 300, 4200), a - .05, 0.26, -0.5, 'spin_pass')
        place(whoosh(td, 2400, 400, rev=True), a + td * .3, 0.14, 0.5, 'spin_tail')
        place(sub(90, 48, 0.5), b, 0.08, 0.0, 'spin_sub')
        place(shimmer(1.0, 6800), b, 0.12, 0.0, 'spin_dust')
    elif kind == 'slices':
        for i in range(5):
            place(click(1800 + i * 350), a + i * td * .18, 0.14, -0.5 + i * .25, 'slice_click')
            place(air(0.06, 4000, 10000), a + i * td * .18 + .01, 0.12, -0.5 + i * .25, 'slice_air')
        place(tap(700, 0.08, 0.3), b + td / 2, 0.09, 0.0, 'slice_land')
    elif kind == 'ink':
        for i in range(4):
            place(pop(170 + i * 40, 0.26, 0.7), a + i * td * .22, 0.17, -0.4 + i * .27, 'ink_bubble')
        place(whoosh(td + .2, 1600, 250, rev=True), a - .05, 0.10, 0.0, 'ink_bleed')
        place(air(0.30, 2000, 7000, 0.10), b, 0.12, 0.0, 'ink_wash')
    elif kind == 'card':
        place(paper(td * .8), a, 0.26, -0.3, 'card_slide')
        place(air(0.10, 4500, 10000), a + td * .5, 0.18, 0.3, 'card_flick')
        place(thud(0.30), b + td * .4, 0.12, 0.0, 'card_land')
        place(ting(2349, 0.7), b + td * .42, 0.04, 0.2, 'card_ting')
    elif kind == 'shatter':
        place(tap(380, 0.14, 0.2), a - .05, 0.15, 0.0, 'shatter_crack')
        place(glass_burst(1.0), a + .02, 0.26, 0.0, 'shatter_glass')
        place(impact(0.7), a + .03, 0.15, 0.0, 'shatter_hit')
        place(air(0.6, 3500, 10500, 0.03), a + .05, 0.22, 0.3, 'shatter_air')
        place(sub(70, 40, 0.8), a + .03, 0.11, 0.0, 'shatter_sub')


def build_transitions():
    import respect2 as Q                                           # single source of truth for the plan
    prev = None
    for k, (b, kind) in enumerate(zip(Q.BOUNDS, Q.PLAN)):
        assert kind != prev, (k, kind)
        tr_cue(kind, b, Q.TD[kind], k)
        prev = kind


# ───────────────────────────────────────────── word-locked cues (v1 cues, varied payoffs)
PAYOFF = {  # per-chapter payoff instrument: never the same bell twice
    0: lambda t: place(chime(784, 1.4), t, 0.07, 0.0, 'payoff_bell'),
    1: lambda t: place(ting(1318.5, 1.2), t, 0.06, 0.2, 'payoff_glass'),
    2: lambda t: place(metal(440, 1.8), t, 0.06, -0.2, 'payoff_metal'),
    3: lambda t: place(pluck(1174.7, 0.9), t, 0.07, 0.2, 'payoff_pluck'),
    4: lambda t: place(ting(1568, 1.3), t, 0.055, -0.2, 'payoff_glass_hi'),
    5: lambda t: place(chime(659.3, 1.6), t, 0.065, 0.2, 'payoff_chime_lo'),
    6: lambda t: (place(shimmer(1.2, 5600), t, 0.10, 0.0, 'payoff_shimmer'), place(chime(880, 1.2), t + .05, 0.05, 0.0, 'payoff_bell_hi')),
    7: lambda t: place(metal(523.3, 1.6), t, 0.055, 0.2, 'payoff_metal_hi'),
    8: lambda t: place(chime(784, 2.4), t, 0.065, 0.0, 'end_bell'),
}


def title(si, n=3, lt=0.0):
    f0 = 430 + si * 32
    for i in range(n):
        place(pop(f0 + i * 80, 0.16), at(si, lt + i * 0.09), 0.26, -0.3 + i * (0.6 / max(1, n - 1)), 'title')


def payoff_pops(si, k, n=3):
    for i in range(n):
        place(pop(600 + i * 70 + si * 10, 0.15), vo(si, k) + i * 0.13, 0.22, -0.3 + i * (0.6 / max(1, n - 1)), 'payoff')
    PAYOFF[si](vo(si, k) + 0.02)


def build_cues():
    # ---- 1 HOOK
    place(whoosh(0.70, 200, 1800), 0.00, 0.26, 0.0, 'open')
    for i in range(4):
        place(tap(240, 0.14, 0.14), 0.30 + i * 0.26, 0.08, 0.45 - i * 0.05, 'step')
    place(shimmer(1.6, 3600), 0.30, 0.06, 0.3, 'eyes_open')
    for i in range(3):
        place(cloth(0.22), at(0, 1.6 + i * 1.1), 0.06, -0.5 + i * 0.3, 'murmur')
    for i, lt in enumerate((0.00, 0.18)):
        place(pop(430 + i * 90, 0.17), vo(0, 2) + lt, 0.28, -0.18 + i * .36, 'title')
    payoff_pops(0, 3)

    # ---- 2 VILLAIN
    title(1)
    for n, ht in enumerate((2.50, 3.05, 3.55, 3.99, 4.40, 4.85, 5.20)):
        place(cloth(0.18), TL.VO_AT[1] + ht + 0.05, 0.10, -0.2, 'nod')
        place(tap(1500 - n * 60, 0.06, 0.5), TL.VO_AT[1] + ht + 0.9, 0.09, 0.35, 'tag_land')
    place(whoosh(0.9, 700, 180, rev=True), vo(1, 3), 0.08, 0.0, 'drain')
    payoff_pops(1, 4)

    # ---- 3 TURN
    place(riser(2.2, 150, 900), at(2, 0.4), 0.10, 0.0, 'turn_riser')
    place(sub(60, 110, 0.9), vo(2, 1) - 0.1, 0.14, 0.0, 'ignite_sub')
    place(shimmer(2.2, 4200), vo(2, 1), 0.11, 0.2, 'ignite')
    place(whoosh(0.9, 400, 2600), vo(2, 1) + 0.1, 0.16, -0.4, 'ray')
    place(chime(587.3, 1.8), vo(2, 1) + 0.05, 0.08, 0.15, 'ignite_bell')
    for i in range(5):
        place(pop(520 + i * 50, 0.14), vo(2, 2) + i * 0.11, 0.22, -0.4 + i * 0.2, 'chip')
    payoff_pops(2, 3, 4)

    # ---- 4 KAM BOLO
    title(3, 2)
    t = vo(3, 2); k = 0
    while t < vo(3, 4) - 0.1:
        place(tap(700 + (k % 5) * 90, 0.05, 0.25), t, 0.05 - 0.004 * (k % 5), -0.45, 'babble')
        t += 0.19; k += 1
    place(thud(0.30), vo(3, 4), 0.14, 0.3, 'one_word')
    place(pop(360, 0.22), vo(3, 4) + 0.15, 0.26, 0.3, 'bubble')
    place(chime(659, 1.5), vo(3, 4) + 0.18, 0.07, 0.3, 'bubble_bell')
    place(cloth(0.30), vo(3, 6), 0.10, 0.5, 'lean_in')
    for i in range(2):
        place(pop(600 + i * 70, 0.15), vo(3, 4) + i * 0.14, 0.24, -0.3 + i * .6, 'payoff')
    PAYOFF[3](vo(3, 6) + 0.05)

    # ---- 5 WAQT
    title(4, 2)
    t = at(4, 0.3)
    while t < M.END[4] - 0.3:
        place(tap(1800, 0.04, 0.5), t, 0.035, 0.45, 'clock')
        t += 1.0
    t = vo(4, 3)
    while t < vo(4, 4) + 0.9:
        place(sub(95, 30, 0.22), t, 0.09, -0.2, 'buzz')
        place(tap(2400, 0.05, 0.7), t, 0.04, -0.2, 'buzz_tick')
        t += 0.42
    place(pop(300, 0.22), vo(4, 1), 0.24, 0.42, 'tag')
    for i in range(6):
        place(tap(1100 + i * 90, 0.05, 0.4), vo(4, 2) + 0.2 + i * 0.5, 0.055, 0.42, 'bar_tick')
    payoff_pops(4, 5)

    # ---- 6 NA
    title(5, 2)
    for n in range(6):
        place(tap(1400 - n * 50, 0.06, 0.5), vo(5, 2) + n * 0.12 + 0.3, 0.09, -0.35, 'pile')
    st = vo(5, 3)
    place(whoosh(0.30, 2200, 600, rev=True), st - 0.22, 0.14, -0.3, 'stamp_up')
    place(impact(0.5), st + 0.30, 0.24, -0.3, 'stamp')
    place(whoosh(0.9, 500, 3200), st + 0.36, 0.20, 0.2, 'blow_away')
    place(air(0.6, 3000, 9000, 0.05), st + 0.40, 0.22, 0.4, 'paper_scatter')
    place(pop(330, 0.2), vo(5, 4), 0.22, -0.3, 'excuse')
    place(whoosh(0.26, 1100, 2600), vo(5, 4) + 0.3, 0.14, -0.3, 'cross')
    payoff_pops(5, 4)

    # ---- 7 KAMAR
    title(6, 2)
    place(riser(0.55, 300, 1400), vo(6, 2), 0.10, -0.3, 'spine')
    place(chime(880, 1.4), vo(6, 2) + 0.45, 0.07, -0.3, 'spine_bell')
    for i in range(4):
        place(tap(230, 0.16, 0.12), vo(6, 3) + 0.1 + i * 0.47, 0.10, -0.3 + i * 0.22, 'slow_step')
        place(cloth(0.16), vo(6, 3) + 0.12 + i * 0.47, 0.05, -0.3 + i * 0.22, 'step_cloth')
    place(shimmer(1.6, 5000), vo(6, 4), 0.10, 0.0, 'eye_line')
    place(rswell(0.9, 440), vo(6, 4) - 0.6, 0.07, 0.0, 'eye_swell')
    payoff_pops(6, 5, 4)

    # ---- 8 LAFZ
    title(7, 2)
    for n in range(12):
        place(tap(1500 + (n % 4) * 120, 0.04, 0.5), vo(7, 1) + n * 0.075, 0.05, -0.4, 'tick')
    place(tap(420, 0.12, 0.2), vo(7, 2) + 0.05, 0.16, -0.3, 'crack')
    place(cloth(0.20), vo(7, 2) + 0.08, 0.10, -0.3, 'crack_cloth')
    place(whoosh(0.8, 700, 3400), vo(7, 2) + 0.32, 0.18, 0.0, 'break')
    place(air(0.5, 3500, 9500, 0.04), vo(7, 2) + 0.35, 0.18, 0.2, 'break_air')
    place(thud(0.36), vo(7, 3) + 0.22, 0.20, -0.3, 'seal')
    place(sub(64, 52, 0.5), vo(7, 3) + 0.22, 0.12, 0.0, 'seal_sub')
    place(chime(523.3, 1.9), vo(7, 3) + 0.26, 0.08, -0.2, 'seal_bell')
    payoff_pops(7, 3, 4)

    # ---- 9 PAYOFF: the braam (once), steps in, heads turn, the still, recap, pill
    place(braam(1.5, 55), at(8, -0.35), 0.22, 0.0, 'braam')
    for i in range(5):
        place(tap(240, 0.14, 0.14), at(8, 0.4 + i * 0.3), 0.09, 0.45 - i * 0.1, 'step_in')
    for i in range(5):
        place(cloth(0.24), vo(8, 2) + i * 0.17, 0.09, -0.5 + i * 0.25, 'head_turn')
        place(shimmer(0.9, 5600), vo(8, 2) + 0.3 + i * 0.17, 0.045, -0.5 + i * 0.25, 'notice')
    place(whoosh(1.4, 900, 160, rev=True), vo(8, 3), 0.07, 0.0, 'still')
    for i, lt in enumerate((0.00, 0.15)):
        place(pop(430 + i * 90, 0.17), vo(8, 3) + lt, 0.26, -0.18 + i * .36, 'title')
    for i in range(5):
        place(pop(500 + i * 55, 0.15), vo(8, 5) + i * 0.125, 0.22, -0.4 + i * 0.2, 'recap')
    place(whoosh(0.46, 260, 2200), vo(8, 7), 0.18, 0.0, 'pill')
    place(chime(659, 1.8), vo(8, 7) + 0.05, 0.08, 0.1, 'pill_bell')
    place(tap(1800, 0.05, 0.6), vo(8, 8) + 0.1, 0.07, 0.3, 'save')
    PAYOFF[8](vo(8, 9) + 0.4)
    # the 1.85 s tail is bed-only: dust + a last glass ting so the room stays alive until the cut
    tl = TL.VO_AT[8] + TL.VO_LEN[8] if hasattr(TL, 'VO_LEN') else DUR - 1.85
    place(air(1.5, 3200, 9500, 0.10), tl + 0.1, 0.07, 0.0, 'tail_air')
    place(shimmer(1.3, 5200), tl + 0.25, 0.06, -0.2, 'tail_shimmer')
    place(ting(2093, 1.2), tl + 0.55, 0.035, 0.25, 'tail_ting')


def main():
    build_music()
    build_transitions()
    build_cues()
    holes = P.vo_holes()
    print('VO holes >=0.5 s:', holes)
    P.build_swells(holes)

    mix = M.BUF + M.silk(M.SFX, wet=0.34)
    M_ = (mix[0] + mix[1]) * .5
    S_ = (mix[0] - mix[1]) * .5
    S_ = flt(S_, lo=150, hi=16000) * 2.30
    mix = np.vstack([M_ + S_, M_ - S_])
    for ch in (0, 1):
        mix[ch] += flt(mix[ch], lo=6500, hi=17000) * 0.95
    for ch in (0, 1):
        mix[ch] = flt(mix[ch], lo=28, hi=14500, n=2)
    pk = np.abs(mix).max()
    mix = np.tanh(mix / max(pk, 1e-9) * 1.05) * 0.74
    print(f'peak {pk:.4f}  events {len(M.LOG)}')

    out = (np.clip(mix.T, -1, 1) * 32767).astype(np.int16)
    with wave.open('/home/user/build/asmr_bed_respect2.wav', 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(out.tobytes())
    with open('/home/user/ASMR_RESPECT2_LEDGER.csv', 'w') as f:
        f.write('t,tag,gain,pan\n')
        for r in sorted(M.LOG):
            f.write(','.join(str(x) for x in r) + '\n')
    print('wrote build/asmr_bed_respect2.wav', out.shape)


if __name__ == '__main__':
    os.makedirs('/home/user/build', exist_ok=True)
    main()
