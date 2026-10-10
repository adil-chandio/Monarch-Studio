"""
make_asmr_respect.py — ASMR / sound-design bed for the 90 s "IZZAT" short.

Same instrument as the POWER bed (make_asmr.py voices via make_asmr_power.py: pads with
nothing under 110 Hz, pulse/hat/shaker grid, swipe recipe, air band, swells in the VO holes).
Only the chord plan (9 chapters) and the word-locked cues are new.

Outputs  build/asmr_bed_respect.wav  +  ASMR_RESPECT_LEDGER.csv
"""
import math, os, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_asmr as M
import make_asmr_power as P                     # re-pointing helpers + voices (import side effects are harmless)
import timeline_respect as TL

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
riser, cloth, shimmer, pluck, flt = M.riser, M.cloth, M.shimmer, M.pluck, M.flt
air = P.air
S = M.SCENE


def at(si, lt):
    return S[si] + lt


def vo(si, k):
    """Absolute time of phrase k of clip si."""
    return TL.VO_AT[si] + TL.PHRASES[si][k]


def build_music():
    for i, (st, en) in enumerate(zip(M.SCENE, M.END)):
        d = en - st + 0.9
        L, R = M.pad(M.CHORDS[i], d, 1.0 if i else 0.75)
        place_st(L, R, st - 0.25, 0.80, f'pad{i+1}')
    b = 0.0; k = 0
    while b < DUR - 0.2:
        if k % 2 == 0:
            place(sub(66, 48, 0.46), b, 0.10, 0.0, 'pulse', 'mus')
        if k % 4 == 2:
            place(tap(900, 0.07, 0.25), b, 0.035, -0.25, 'hat', 'mus')
        if k % 2 == 1:
            place(air(0.075, 4400, 9000), b, 0.050 if k % 4 == 1 else 0.035,
                  -0.35 + 0.7 * ((k % 3) / 2), 'shaker', 'mus')
        b += M.SPB; k += 1
    for si in (3, 4, 5, 6, 7):                                     # plucks under the rule chapters
        base = M.CHORDS[si]
        t = M.SCENE[si] + M.SPB
        j = 0
        while t < M.END[si] - 0.4:
            place(pluck(base[j % 3] * 4, 0.55), t, 0.050, -0.45 + 0.9 * ((j % 3) / 2), 'arp', 'mus')
            t += M.SPB * 1.5; j += 1
    nz = M.rng.normal(0, 1, N)
    room = flt(nz, lo=90, hi=1500)
    hiss = flt(nz, lo=4000, hi=11000)
    sw = 0.5 + 0.5 * np.sin(2 * np.pi * np.arange(N) / SR / 6.5)
    M.BUF[0] += room * 0.0075 * sw + hiss * 0.0082 * (0.7 + 0.3 * sw)          # hiss .0062 in POWER: the 5 s bed-only tail lowered the bed's 4-8 k share under 10 %
    M.BUF[1] += np.roll(room, 211) * 0.0075 * (1 - sw * 0.6) + np.roll(hiss, 173) * 0.0082 * (1 - 0.3 * sw)


def build_cues():
    # ---- 1 HOOK: the room — footsteps at the door, murmur, eyes open, headline, payoff
    place(whoosh(0.70, 200, 1800), 0.00, 0.26, 0.0, 'open')
    for i in range(4):
        place(tap(240, 0.14, 0.14), 0.30 + i * 0.26, 0.08, 0.45 - i * 0.05, 'step')
    place(shimmer(1.6, 3600), 0.30, 0.06, 0.3, 'eyes_open')
    for i in range(3):                                           # the room murmurs, not to him
        place(cloth(0.22), at(0, 1.6 + i * 1.1), 0.06, -0.5 + i * 0.3, 'murmur')
    for i, lt in enumerate((0.00, 0.18)):
        place(pop(430 + i * 90, 0.17), vo(0, 2) + lt, 0.28, -0.18 + i * .36, 'title')
    for i in range(3):
        place(pop(600 + i * 70, 0.15), vo(0, 3) + i * 0.14, 0.24, -0.3 + i * .3, 'payoff')
    place(chime(784, 1.4), vo(0, 3) + 0.02, 0.07, 0.0, 'payoff_bell')

    # ---- 2 VILLAIN: every HAAN is a nod (cloth) + a tag landing (paper tap)
    for i in range(3):
        place(pop(470 + i * 80, 0.16), at(1, 0.00 + i * 0.09), 0.27, -0.3 + i * .3, 'title')
    for n, ht in enumerate((2.50, 3.05, 3.55, 3.99, 4.40, 4.85, 5.20)):
        place(cloth(0.18), TL.VO_AT[1] + ht + 0.05, 0.10, -0.2, 'nod')
        place(tap(1500 - n * 60, 0.06, 0.5), TL.VO_AT[1] + ht + 0.9, 0.09, 0.35, 'tag_land')
    place(whoosh(0.9, 700, 180, rev=True), vo(1, 3), 0.08, 0.0, 'drain')
    for i in range(3):
        place(pop(600 + i * 70, 0.15), vo(1, 4) + i * 0.14, 0.24, -0.3 + i * .3, 'payoff')
    place(chime(784, 1.4), vo(1, 4) + 0.02, 0.07, 0.0, 'payoff_bell')

    # ---- 3 TURN: slow riser into the head lift, ignition shimmer, ray, five chips, payoff
    place(riser(2.2, 150, 900), at(2, 0.4), 0.10, 0.0, 'turn_riser')
    place(sub(60, 110, 0.9), vo(2, 1) - 0.1, 0.14, 0.0, 'ignite_sub')
    place(shimmer(2.2, 4200), vo(2, 1), 0.11, 0.2, 'ignite')
    place(whoosh(0.9, 400, 2600), vo(2, 1) + 0.1, 0.16, -0.4, 'ray')
    place(chime(587.3, 1.8), vo(2, 1) + 0.05, 0.08, 0.15, 'ignite_bell')
    for i in range(5):
        place(pop(520 + i * 50, 0.14), vo(2, 2) + i * 0.11, 0.22, -0.4 + i * 0.2, 'chip')
    for i in range(4):
        place(pop(600 + i * 60, 0.15), vo(2, 3) + i * 0.12, 0.24, -0.3 + i * .2, 'payoff')
    place(chime(784, 1.6), vo(2, 3) + 0.02, 0.08, 0.0, 'payoff_bell')

    # ---- 4 KAM BOLO: babble pops that die, one clean word, the room leans
    for i in range(2):
        place(pop(470 + i * 80, 0.16), at(3, 0.00 + i * 0.09), 0.27, -0.3 + i * .6, 'title')
    t = vo(3, 2)
    k = 0
    while t < vo(3, 4) - 0.1:
        place(tap(700 + (k % 5) * 90, 0.05, 0.25), t, 0.05 - 0.004 * (k % 5), -0.45, 'babble')
        t += 0.19; k += 1
    place(thud(0.30), vo(3, 4), 0.14, 0.3, 'one_word')
    place(pop(360, 0.22), vo(3, 4) + 0.15, 0.26, 0.3, 'bubble')
    place(chime(659, 1.5), vo(3, 4) + 0.18, 0.07, 0.3, 'bubble_bell')
    place(cloth(0.30), vo(3, 6), 0.10, 0.5, 'lean_in')
    for i in range(2):
        place(pop(600 + i * 70, 0.15), vo(3, 4) + i * 0.14, 0.24, -0.3 + i * .6, 'payoff')

    # ---- 5 WAQT: a far clock tick, the phone buzz he ignores, the tag, the bar
    for i in range(2):
        place(pop(470 + i * 80, 0.16), at(4, 0.00 + i * 0.09), 0.27, -0.3 + i * .6, 'title')
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
    for i in range(3):
        place(pop(600 + i * 70, 0.15), vo(4, 5) + i * 0.14, 0.24, -0.3 + i * .3, 'payoff')
    place(chime(784, 1.4), vo(4, 5) + 0.02, 0.07, 0.0, 'payoff_bell')

    # ---- 6 NA: the pile lands, the stamp slams, the tags blow away, the excuse crossed out
    for i in range(2):
        place(pop(470 + i * 80, 0.16), at(5, 0.00 + i * 0.09), 0.27, -0.3 + i * .6, 'title')
    for n in range(6):
        place(tap(1400 - n * 50, 0.06, 0.5), vo(5, 2) + n * 0.12 + 0.3, 0.09, -0.35, 'pile')
    st = vo(5, 3)
    place(whoosh(0.30, 2200, 600, rev=True), st - 0.22, 0.14, -0.3, 'stamp_up')
    place(thud(0.42), st + 0.30, 0.26, -0.3, 'stamp')
    place(sub(70, 48, 0.6), st + 0.30, 0.14, 0.0, 'stamp_sub')
    place(whoosh(0.9, 500, 3200), st + 0.36, 0.20, 0.2, 'blow_away')
    place(air(0.6, 3000, 9000, 0.05), st + 0.40, 0.22, 0.4, 'paper_scatter')
    place(pop(330, 0.2), vo(5, 4), 0.22, -0.3, 'excuse')
    place(whoosh(0.26, 1100, 2600), vo(5, 4) + 0.3, 0.14, -0.3, 'cross')
    for i in range(3):
        place(pop(600 + i * 70, 0.15), vo(5, 4) + i * 0.14, 0.24, -0.3 + i * .3, 'payoff')
    place(chime(784, 1.4), vo(5, 4) + 0.02, 0.07, 0.0, 'payoff_bell')

    # ---- 7 KAMAR: the spine draws (riser + chime), slow steps, the eye-line shimmer
    for i in range(2):
        place(pop(470 + i * 80, 0.16), at(6, 0.00 + i * 0.09), 0.27, -0.3 + i * .6, 'title')
    place(riser(0.55, 300, 1400), vo(6, 2), 0.10, -0.3, 'spine')
    place(chime(880, 1.4), vo(6, 2) + 0.45, 0.07, -0.3, 'spine_bell')
    for i in range(4):
        place(tap(230, 0.16, 0.12), vo(6, 3) + 0.1 + i * 0.47, 0.10, -0.3 + i * 0.22, 'slow_step')
        place(cloth(0.16), vo(6, 3) + 0.12 + i * 0.47, 0.05, -0.3 + i * 0.22, 'step_cloth')
    place(shimmer(1.6, 5000), vo(6, 4), 0.10, 0.0, 'eye_line')
    for i in range(4):
        place(pop(600 + i * 60, 0.15), vo(6, 5) + i * 0.12, 0.24, -0.3 + i * .2, 'payoff')
    place(chime(784, 1.4), vo(6, 5) + 0.02, 0.07, 0.0, 'payoff_bell')

    # ---- 8 LAFZ: 100 ticks ripple, one crack, the shatter, the wax seal
    for i in range(2):
        place(pop(470 + i * 80, 0.16), at(7, 0.00 + i * 0.09), 0.27, -0.3 + i * .6, 'title')
    for n in range(12):
        place(tap(1500 + (n % 4) * 120, 0.04, 0.5), vo(7, 1) + n * 0.075, 0.05, -0.4, 'tick')
    place(tap(420, 0.12, 0.2), vo(7, 2) + 0.05, 0.16, -0.3, 'crack')
    place(cloth(0.20), vo(7, 2) + 0.08, 0.10, -0.3, 'crack_cloth')
    place(whoosh(0.8, 700, 3400), vo(7, 2) + 0.32, 0.18, 0.0, 'shatter')
    place(air(0.5, 3500, 9500, 0.04), vo(7, 2) + 0.35, 0.18, 0.2, 'shatter_air')
    place(thud(0.36), vo(7, 3) + 0.22, 0.20, -0.3, 'seal')
    place(sub(64, 52, 0.5), vo(7, 3) + 0.22, 0.12, 0.0, 'seal_sub')
    place(chime(523.3, 1.9), vo(7, 3) + 0.26, 0.08, -0.2, 'seal_bell')
    for i in range(4):
        place(pop(600 + i * 60, 0.15), vo(7, 3) + i * 0.12, 0.24, -0.3 + i * .2, 'payoff')

    # ---- 9 PAYOFF: footsteps in, the room turns (five cloths), the still, recap pops, the pill
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
    place(chime(784, 2.4), vo(8, 9) + 0.4, 0.06, 0.0, 'end_bell')
    # the tail (84.9-90.0) is bed-only: keep the air alive so the room never dies before the picture does
    place(air(4.6, 3200, 9500, 0.08), 85.0, 0.075, 0.0, 'tail_air')
    for i in range(3):
        place(shimmer(1.4, 5200 + i * 600), 85.6 + i * 1.4, 0.055, -0.3 + i * 0.3, 'tail_shimmer')
    for i in range(5):
        place(tap(1800, 0.05, 0.6), 85.3 + i * 0.9, 0.035, 0.3 - i * 0.15, 'tail_tick')


def main():
    build_music()
    P.build_transitions()
    build_cues()
    holes = P.vo_holes()
    print('VO holes >=0.5 s:', holes)
    P.build_swells(holes)

    mix = M.BUF + M.silk(M.SFX, wet=0.34)
    M_ = (mix[0] + mix[1]) * .5
    S_ = (mix[0] - mix[1]) * .5
    S_ = flt(S_, lo=150, hi=16000) * 2.30          # 3.30 in POWER; this bed has less VO share (75 %) and wider cues, 2.30 lands lr_corr ~.68
    mix = np.vstack([M_ + S_, M_ - S_])
    for ch in (0, 1):
        mix[ch] += flt(mix[ch], lo=6500, hi=17000) * 0.95
    for ch in (0, 1):
        mix[ch] = flt(mix[ch], lo=28, hi=14500, n=2)
    pk = np.abs(mix).max()
    mix = np.tanh(mix / max(pk, 1e-9) * 1.05) * 0.74
    print(f'peak {pk:.4f}  events {len(M.LOG)}')

    out = (np.clip(mix.T, -1, 1) * 32767).astype(np.int16)
    with wave.open('/home/user/build/asmr_bed_respect.wav', 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(out.tobytes())
    with open('/home/user/ASMR_RESPECT_LEDGER.csv', 'w') as f:
        f.write('t,tag,gain,pan\n')
        for r in sorted(M.LOG):
            f.write(','.join(str(x) for x in r) + '\n')
    print('wrote build/asmr_bed_respect.wav', out.shape)


if __name__ == '__main__':
    os.makedirs('/home/user/build', exist_ok=True)
    main()
