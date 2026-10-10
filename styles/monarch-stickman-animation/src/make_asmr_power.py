"""
make_asmr_power.py — ASMR bed for the 42 s "POWERFUL MAN" short.
=================================================================
Same instrument as v9 (make_asmr.py is imported and re-used verbatim: voices,
place(), pad(), silk(), the music bed and transition recipe, the mastering
chain) — only the *song* changes:

  * timeline 42.000 s, six chapters from timeline_power.py
  * 100 BPM (SPB 0.600) — the v9 bed ran 112; the squat reps and the
    ten-second countdown sit on a slower grid
  * D minor: Dm Bb F C Gm Dm (v9 was A minor); the hole-swell voicing in v9
    was already D-rooted, so it rings in key here without a change
  * ~190 cues, every one locked to a reveal that actually happens in power.py
  * pad swells are no longer hard-coded: the VO gaps are MEASURED from the
    fitted VO files and a swell is dropped into every gap >= 0.5 s (the five scene breaths + the tail)

Outputs  build/asmr_bed_power.wav  +  ASMR_POWER_LEDGER.csv
"""
import math, os, sys, wave
import numpy as np
sys.path.insert(0, '/home/user/src')
import make_asmr as M
import timeline_power as TL

SR = M.SR
DUR = TL.DUR_TOTAL
VO_FILES = [f'p{i + 1}_fit.wav' for i in range(6)]
N = int(SR * DUR)

# ---- re-point the module globals the v9 primitives read at call time
M.DUR, M.N = DUR, N
M.BUF = np.zeros((2, N), dtype=np.float64)
M.SFX = np.zeros((2, N), dtype=np.float64)
M.LOG = []
M.SCENE = list(TL.SCENE_START)
M.END = list(TL.SCENE_END)
M.CUTS = M.SCENE[1:]
M.SPB = 0.600                                   # 100 BPM
M.CHORDS = [(110.00, 146.83, 174.61),           # Dm   A2 D3 F3
            (116.54, 146.83, 174.61),           # Bb   Bb2 D3 F3
            (130.81, 174.61, 220.00),           # F    C3 F3 A3
            (130.81, 164.81, 196.00),           # C    C3 E3 G3
            (146.83, 196.00, 233.08),           # Gm   D3 G3 Bb3
            (146.83, 174.61, 220.00)]           # Dm   D3 F3 A3  (resolves up)
# (measured: a D2 73 Hz root put 46 % of the bed-only energy under 120 Hz; gate < 48 %
#  with no margin. Nothing below 110 Hz in the pads now.)

place, place_st = M.place, M.place_st
pop, tap, chime, whoosh, sub, thud = M.pop, M.tap, M.chime, M.whoosh, M.sub, M.thud
riser, cloth, shimmer, pluck, flt = M.riser, M.cloth, M.shimmer, M.pluck, M.flt
S = M.SCENE


def at(si, lt):
    return S[si] + lt


def air(d=0.07, lo=4200, hi=9200, atk=0.006):
    """Breath of air: band-limited noise, raised-cosine edges. The v9 `tap`
    voice is capped at 3.2 kHz, so it cannot carry the 4-8 kHz band."""
    n = int(SR * d)
    return flt(M.rng.normal(0, 1, n) * M.env(n, atk, d * 0.45, 3.0), lo=lo, hi=hi)


# ───────────────────────────────────────────── music bed (v9 recipe, re-balanced)
def build_music():
    for i, (st, en) in enumerate(zip(M.SCENE, M.END)):
        d = en - st + 0.9
        L, R = M.pad(M.CHORDS[i], d, 1.0 if i else 0.75)
        place_st(L, R, st - 0.25, 0.80, f'pad{i+1}')
    b = 0.0; k = 0
    while b < DUR - 0.2:
        if k % 2 == 0:
            place(sub(66, 48, 0.46), b, 0.10, 0.0, 'pulse', 'mus')          # v9 .16
        if k % 4 == 2:
            place(tap(900, 0.07, 0.25), b, 0.035, -0.25, 'hat', 'mus')
        if k % 2 == 1:                                                     # shaker on the off-beats
            place(air(0.075, 4400, 9000), b, 0.050 if k % 4 == 1 else 0.035,
                  -0.35 + 0.7 * ((k % 3) / 2), 'shaker', 'mus')
        b += M.SPB; k += 1
    for si in (1, 2):                                                      # plucks under the build chapters
        base = M.CHORDS[si]
        t = M.SCENE[si] + M.SPB
        j = 0
        while t < M.END[si] - 0.4:
            place(pluck(base[j % 3] * 4, 0.55), t, 0.055, -0.45 + 0.9 * ((j % 3) / 2), 'arp', 'mus')
            t += M.SPB * 1.5; j += 1
    nz = M.rng.normal(0, 1, N)                                             # the ASMR "room", v9 + an air band
    room = flt(nz, lo=90, hi=1500)
    hiss = flt(nz, lo=4000, hi=11000)
    sw = 0.5 + 0.5 * np.sin(2 * np.pi * np.arange(N) / SR / 6.5)
    M.BUF[0] += room * 0.0075 * sw + hiss * 0.0062 * (0.7 + 0.3 * sw)
    M.BUF[1] += np.roll(room, 211) * 0.0075 * (1 - sw * 0.6) + np.roll(hiss, 173) * 0.0062 * (1 - 0.3 * sw)


# ───────────────────────────────────────────── transitions
# v9 recipe with two measured corrections: the sub "drop" and the thud were
# 49.6 % of the bed-only energy below 120 Hz (gate < 48 %), and the cut carried
# 1.4 % air (gate > 10 %). Drop/thud trimmed, a paper-flick and a 5.2 kHz
# shimmer added on the swipe.
def build_transitions():
    for k, c in enumerate(M.CUTS):
        place(riser(0.82, 200, 1180), c - 0.84, 0.15, 0.0, 'riser')
        place(whoosh(0.46, 300, 3000), c - 0.16, 0.30, -0.55, 'swipe_in')
        place(air(0.34, 3000, 9000, 0.05), c - 0.14, 0.42, -0.35, 'swipe_air')
        place(thud(0.38), c + 0.002, 0.11, 0.0, 'land')
        place(sub(84, 40, 0.80), c + 0.002, 0.08, 0.0, 'drop')
        place(air(0.10, 4500, 9500), c + 0.004, 0.20, 0.25, 'paper_flick')
        place(shimmer(1.1, 5200), c + 0.02, 0.15, 0.35, 'cut_shimmer')
        place(shimmer(0.9, 7000), c + 0.05, 0.12, -0.30, 'cut_shimmer_hi')
        place(whoosh(0.42, 2600, 320, rev=True), c + 0.20, 0.22, 0.55, 'swipe_out')
        place(chime(660 + k * 55, 1.8), c + 0.03, 0.080, 0.30, 'cut_bell')


def build_air_unused():
    """A soft shaker on the off-beats across the whole film (mus bus, −33 dB):
    ASMR-quiet, but it is what keeps 4–8 kHz alive under a 92 % voice."""
    b = M.SPB * 0.5; k = 0
    while b < DUR - 0.3:
        g = 0.022 if k % 2 == 0 else 0.014
        place(tap(5600 + (k % 4) * 300, 0.07, 0.85), b, g, -0.35 + 0.7 * ((k % 3) / 2), 'shaker', 'mus')
        b += M.SPB; k += 1


# ───────────────────────────────────────────── per-scene cues (word-locked)
def build_cues():
    # ---- 1  HOOK  — walk-in, slump, dumbbell crossed out, rise, 4 habits
    place(whoosh(0.70, 200, 1800), 0.00, 0.26, 0.0, 'open')
    for i, lt in enumerate((0.00, 0.17)):
        place(pop(430 + i * 90, 0.17), at(0, lt), 0.30, -0.18 + i * .36, 'title')
    for i in range(6):                                           # footsteps
        place(tap(260, 0.12, 0.14), at(0, 0.08 + i * 0.175), 0.085, -0.5 + i * 0.16, 'step')
    place(cloth(0.26), at(0, 1.30), 0.15, 0.0, 'slump')
    place(sub(70, 44, 0.7), at(0, 1.32), 0.16, 0.0, 'slump_sub')
    place(pop(300, 0.22), at(0, 1.82), 0.26, 0.42, 'dumbbell')
    place(thud(0.30), at(0, 1.84), 0.14, 0.42, 'dumbbell_land')
    place(whoosh(0.30, 900, 2400), at(0, 2.55), 0.18, 0.42, 'cross_a')
    place(whoosh(0.26, 1100, 2600), at(0, 2.71), 0.16, 0.42, 'cross_b')
    place(cloth(0.30), at(0, 3.32), 0.16, 0.0, 'rise')
    place(sub(60, 92, 0.60), at(0, 3.34), 0.14, 0.0, 'rise_sub')
    for i in range(4):                                           # habit boxes
        place(pop(500 + i * 55, 0.15), at(0, 3.42 + i * 0.125), 0.24, 0.30 + i * 0.08, 'box')
    for i in range(3):
        place(pop(600 + i * 70, 0.15), at(0, 4.62 + i * 0.14), 0.26, -0.3 + i * .3, 'payoff')
    place(chime(784, 1.4), at(0, 4.64), 0.075, 0.0, 'payoff_bell')

    # ---- 2  JISM  — three squats, ring fills 0 -> 20 min, flex
    for i in range(2):
        place(pop(470 + i * 80, 0.16), at(1, 0.00 + i * 0.09), 0.27, -0.3 + i * .6, 'title')
    REP, T0 = 0.90, 0.75
    for k in range(3):
        place(cloth(0.28), at(1, T0 + REP * (k + 0.46)), 0.13, -0.30, 'squat_down')
        place(sub(64, 46, 0.42), at(1, T0 + REP * (k + 0.50)), 0.12, 0.0, 'squat_sub')
        place(tap(340, 0.10, 0.18), at(1, T0 + REP * (k + 0.98)), 0.085, -0.30, 'squat_up')
    place(pop(330, 0.20), at(1, 0.97), 0.26, 0.42, 'ring')
    for i in range(4):                                           # ring quarter-ticks
        place(tap(1100 + i * 140, 0.07, 0.35), at(1, 1.30 + i * 0.52), 0.065, 0.42, 'ring_tick')
    place(whoosh(0.46, 260, 2200), at(1, 3.45), 0.20, 0.0, 'flex')
    place(chime(587.3, 1.6), at(1, 3.50), 0.07, 0.15, 'flex_bell')
    for i in range(3):
        place(pop(600 + i * 70, 0.15), at(1, 3.67 + i * 0.14), 0.26, -0.3 + i * .3, 'payoff')
    place(chime(784, 1.4), at(1, 3.69), 0.075, 0.0, 'payoff_bell')

    # ---- 3  DIMAGH — book opens, pages turn, stack of ten, 3,650 counter
    for i in range(3):
        place(pop(470 + i * 80, 0.16), at(2, 0.00 + i * 0.09), 0.27, -0.3 + i * .3, 'title')
    place(cloth(0.24), at(2, 0.40), 0.15, -0.30, 'book_open')
    for k in range(8):                                           # page turns
        place(tap(1900, 0.06, 0.65), at(2, 1.10 + k * 0.55), 0.055, -0.30, 'page')
    for i in range(10):                                          # the stack
        place(pop(430 + i * 38, 0.14), at(2, 1.17 + i * 0.13), 0.20, 0.45, 'book')
    place(tap(700, 0.09, 0.3), at(2, 2.77), 0.09, 0.45, 'x365')
    place(shimmer(1.4, 2200), at(2, 3.40), 0.07, 0.2, 'count_shimmer')
    for i in range(9):                                           # counter roll
        place(tap(1300 + i * 60, 0.05, 0.4), at(2, 3.42 + i * 0.14), 0.07 - i * 0.004, 0.1, 'count_tick')
    for i in range(3):
        place(pop(600 + i * 70, 0.15), at(2, 4.66 + i * 0.14), 0.24, -0.3 + i * .3, 'payoff')
    place(chime(784, 1.4), at(2, 4.68), 0.075, 0.0, 'payoff_bell')

    # ---- 4  CONTROL — trigger burst, flinch, breathe, ten seconds drain, tick
    for i in range(2):
        place(pop(470 + i * 80, 0.16), at(3, 0.00 + i * 0.09), 0.27, -0.3 + i * .6, 'title')
    place(pop(190, 0.26, 0.3), at(3, 2.08), 0.30, 0.40, 'trigger')
    place(thud(0.36), at(3, 2.08), 0.22, 0.40, 'trigger_thud')
    place(whoosh(0.22, 1600, 3200), at(3, 2.09), 0.14, 0.40, 'trigger_air')
    place(cloth(0.22), at(3, 2.12), 0.15, -0.10, 'flinch')
    place(whoosh(0.9, 900, 180, rev=True), at(3, 2.70), 0.09, 0.0, 'breathe_in')
    place(pop(330, 0.20), at(3, 2.92), 0.24, 0.42, 'ring')
    for i in range(10):                                          # ten seconds
        place(tap(1150, 0.05, 0.3), at(3, 3.10 + i * 0.185), 0.06, 0.42 - (i % 2) * 0.12, 'second')
    place(chime(880, 1.6), at(3, 4.96), 0.08, 0.3, 'tick_bell')
    for i in range(3):
        place(pop(600 + i * 70, 0.15), at(3, 5.17 + i * 0.14), 0.26, -0.3 + i * .3, 'payoff')
    place(chime(784, 1.4), at(3, 5.19), 0.075, 0.0, 'payoff_bell')

    # ---- 5  VALUE — scale swings in, +1 +1 +1, tilt, DO wins
    for i in range(2):
        place(pop(470 + i * 80, 0.16), at(4, 0.00 + i * 0.09), 0.27, -0.3 + i * .6, 'title')
    place(whoosh(0.40, 320, 2000), at(4, 1.00), 0.18, 0.30, 'scale_in')
    place(tap(2400, 0.12, 0.5), at(4, 1.18), 0.07, 0.30, 'scale_metal')
    for i in range(3):
        place(pop(520 + i * 80, 0.15), at(4, 2.47 + i * 0.50), 0.22, -0.35, 'plus_one')
        place(tap(1700 + i * 150, 0.06, 0.5), at(4, 2.49 + i * 0.50), 0.05, -0.35, 'plus_one_tap')
    place(tap(800, 0.10, 0.3), at(4, 4.32), 0.09, -0.15, 'cross')
    place(whoosh(1.20, 240, 760), at(4, 4.42), 0.11, 0.25, 'tilt_creak')
    place(sub(58, 40, 0.9), at(4, 4.60), 0.13, 0.0, 'tilt_sub')
    place(chime(880, 1.6), at(4, 5.97), 0.08, 0.40, 'do_bell')
    for i in range(3):
        place(pop(600 + i * 70, 0.15), at(4, 5.92 + i * 0.14), 0.26, -0.3 + i * .3, 'payoff')
    place(chime(784, 1.4), at(4, 5.94), 0.075, 0.0, 'payoff_bell')

    # ---- 6  GO — four ticks, cheer, pill, confetti, bookmark
    for i in range(3):
        place(pop(470 + i * 80, 0.16), at(5, 0.00 + i * 0.09), 0.27, -0.3 + i * .3, 'title')
    place(pop(560, 0.16), at(5, 0.20), 0.26, 0.0, 'title_karo')
    for i, st in enumerate((.09, .98, 1.84, 2.82)):
        place(pop(520 + i * 60, 0.15), at(5, st + 0.02), 0.24, -0.55 + i * 0.37, 'tick')
        place(tap(1500 + i * 120, 0.07, 0.4), at(5, st + 0.05), 0.07, -0.55 + i * 0.37, 'tick_tap')
    place(whoosh(0.55, 220, 2400), at(5, 4.72), 0.22, 0.0, 'cheer')
    place(sub(66, 96, 0.55), at(5, 4.74), 0.15, 0.0, 'cheer_sub')
    for i in range(10):                                          # confetti scatter
        place(tap(1400 + (i * 97) % 500, 0.06, 0.5), at(5, 5.46 + i * 0.085 + (i % 3) * 0.02),
              0.045, -0.6 + 1.2 * ((i * 7) % 10) / 9, 'confetti')
    place(thud(0.34), at(5, 5.78), 0.18, 0.0, 'pill_land')
    place(chime(880, 2.0), at(5, 5.80), 0.085, 0.0, 'pill_bell')
    place(shimmer(1.6, 2600), at(5, 6.05), 0.07, 0.3, 'sheen')
    place(pop(400, 0.18), at(5, 6.92), 0.24, 0.55, 'bookmark')
    place(tap(2100, 0.08, 0.5), at(5, 6.96), 0.06, 0.55, 'bookmark_tap')
    place(chime(1174.7, 2.2), at(5, 8.16), 0.06, 0.0, 'outro_bell')     # D6 on the button


# ───────────────────────────────────────────── measured VO holes -> pad swells
def vo_holes(min_gap=0.50, thr_db=-38.0, win=0.05):
    env = np.zeros(N)
    for i, nm in enumerate(VO_FILES):
        with wave.open(f'/home/user/assets/{nm}', 'rb') as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
        i0 = int(TL.VO_AT[i] * SR)
        n = min(len(x), N - i0)
        env[i0:i0 + n] = np.maximum(env[i0:i0 + n], np.abs(x[:n]))
    hop = int(win * SR)
    nb = N // hop
    rms = np.sqrt((env[:nb * hop].reshape(nb, hop) ** 2).mean(1))
    quiet = rms < 10 ** (thr_db / 20)
    holes, k = [], 0
    while k < nb:
        if quiet[k]:
            j = k
            while j < nb and quiet[j]:
                j += 1
            g0, g1 = k * win, j * win
            if g1 - g0 >= min_gap:
                holes.append((round(g0, 2), round(g1, 2)))
            k = j
        else:
            k += 1
    return holes


def build_swells(holes):
    for g0, g1 in holes:
        L = g1 - g0
        c = (g0 + g1) / 2
        dur = max(2.2, L + 1.0)
        hg = float(np.clip(0.80 + 0.25 * L, 0.80, 1.40))
        i0 = int((c - dur / 2) * SR)
        if i0 < 0:
            dur += i0 / SR; i0 = 0
        nn = min(int(dur * SR), N - i0)
        if nn <= 0:
            continue
        tt = np.arange(nn) / SR
        sw = np.sin(np.pi * np.clip(tt / (nn / SR), 0, 1)) ** 1.6
        v = np.zeros(nn)
        for k, (fq, gg) in enumerate(((146.8, .55), (220.0, .40), (293.7, .26),
                                      (440.0, .14), (587.3, .07))):
            v += np.sin(2 * np.pi * fq * tt + k * 1.7) * gg
            v += np.sin(2 * np.pi * fq * 1.004 * tt + k) * gg * 0.5
        v = flt(v, lo=110, hi=2600) * sw * 0.048 * hg
        M.BUF[0, i0:i0 + nn] += v
        M.BUF[1, i0:i0 + nn] += np.roll(v, 331)
        M.LOG.append((round(i0 / SR, 3), f'swell_{L:.2f}s', round(hg, 3), 's'))


# ───────────────────────────────────────────── build
def main():
    build_music()
    build_transitions()
    build_cues()
    holes = vo_holes()
    print('VO holes >=0.5 s:', holes)
    build_swells(holes)

    mix = M.BUF + M.silk(M.SFX, wet=0.34)
    M_ = (mix[0] + mix[1]) * .5
    S_ = (mix[0] - mix[1]) * .5
    S_ = flt(S_, lo=150, hi=16000) * 3.30
    mix = np.vstack([M_ + S_, M_ - S_])
    for ch in (0, 1):
        mix[ch] += flt(mix[ch], lo=6500, hi=17000) * 0.95
    for ch in (0, 1):
        mix[ch] = flt(mix[ch], lo=28, hi=14500, n=2)
    pk = np.abs(mix).max()
    mix = np.tanh(mix / max(pk, 1e-9) * 1.05) * 0.74
    print(f'peak {pk:.4f}  events {len(M.LOG)}')

    out = (np.clip(mix.T, -1, 1) * 32767).astype(np.int16)
    with wave.open('/home/user/build/asmr_bed_power.wav', 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(out.tobytes())
    with open('/home/user/ASMR_POWER_LEDGER.csv', 'w') as f:
        f.write('t,tag,gain,pan\n')
        for r in sorted(M.LOG):
            f.write(','.join(str(x) for x in r) + '\n')
    print('wrote build/asmr_bed_power.wav', out.shape)


if __name__ == '__main__':
    os.makedirs('/home/user/build', exist_ok=True)
    main()
