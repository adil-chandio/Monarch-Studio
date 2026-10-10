#!/usr/bin/env python3
"""
film_shadow.py — WF-03 · Monarch Noir Film · film #1 "THE SHADOW" (trigger NOIRGO, topic FEAR)
Timeline (single source of truth for picture AND audio events) + fast per-frame renderer.
1920×1080 · 24 fps · ≈157 s · 34 shots · hard cuts + dip-to-black only · camera never still.

usage:
  python3 film_shadow.py --preview            → build/wf03_film/preview_sheet.jpg (mid-frame of every shot)
  python3 film_shadow.py --frame 47.3         → build/wf03_film/frame_47.3.jpg
  python3 film_shadow.py --events events.json → all audio events (cuts, steps, clicks, lamp, flash, vo)
  python3 film_shadow.py --render out.mp4     → silent picture master (progress on stdout)
"""
import os, sys, math, json, time, argparse, functools, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import noir as N
import toon as T
import shade as S

W, H, FPS = 1920, 1080, 24
ROOT = N.ROOT
OUTDIR = os.path.join(ROOT, 'build', 'wf03_film')
os.makedirs(OUTDIR, exist_ok=True)
HM = 1.8                              # hero height in metres → readout = HM · k
LAMP = (-0.75, 0.34, 540)             # the lantern on the floor (u, z, radius) — acts 1–3
WIDE = dict(y_j=760, s_near=1120)
LIGHT_GAIN = 0.85                     # film exposure vs look sheet (target setup luma ≈ 22–28)
BONE, RED = N.BONE, N.RED
GREY = (150, 146, 138)
FLASHCOL = np.array([255, 238, 205], np.float32)

# ───────────────────────────────────────────────────────────── helpers
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(e):
    e = clamp(e)
    return e * e * (3 - 2 * e)


def seg(t, t0, t1):
    """smoothstep progress of t between t0 and t1"""
    return ease((t - t0) / (t1 - t0)) if t1 > t0 else (1.0 if t >= t0 else 0.0)


def lin(t, t0, t1):
    return clamp((t - t0) / (t1 - t0)) if t1 > t0 else (1.0 if t >= t0 else 0.0)


def lerp(a, b, e):
    return a + (b - a) * e


def lerp_pose(pa, pb, e):
    out = {}
    for k in set(pa) | set(pb):
        va, vb = pa.get(k), pb.get(k)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            out[k] = va + (vb - va) * e
        else:
            out[k] = vb if (vb is not None and (e >= 0.5 or va is None)) else va
    return out


def env(t, t_in, t_out, fi=0.5, fo=0.4):
    """text alpha envelope 0..1"""
    if t < t_in or t > t_out:
        return 0.0
    return min(lin(t, t_in, t_in + fi), 1 - lin(t, t_out - fo, t_out))


def typed(t, t_in, text, cps=15.0):
    n = int(max(0.0, t - t_in) * cps)
    return text[:n]


def metres(z, lz):
    return HM * (1 - lz) / max(z - lz, 0.02)


def flick(t, depth=1.0):
    return 1 + depth * (0.030 * math.sin(2 * math.pi * 6.1 * t) + 0.020 * math.sin(2 * math.pi * 9.7 * t + 1.3)
                        + 0.015 * math.sin(2 * math.pi * 15.3 * t + 2.1) + 0.012 * math.sin(2 * math.pi * 0.37 * t))


def gutter(t):
    """the flame nearly dying (insert shot)"""
    g = 0.72 + 0.28 * math.sin(2 * math.pi * 0.9 * t) * math.sin(2 * math.pi * 2.7 * t + 0.4)
    return g * flick(t, 2.2)


# ───────────────────────────────────────────────────────────── poses
def p_crouch(t, tight=1.0):
    """kneeling small in the corner, legs folded under, hands up in front of the chest (shielding)"""
    br = math.sin(t * 1.9)
    return dict(yaw=12, lean=-14 * tight, twist=0, sh_up=-0.014 + 0.004 * br, head=10 + 4 * tight, head_t=-6,
                al=-18, az_l=58 + 2 * br, ef_l=86, el=-6, ar=18, az_r=58 - 2 * br, ef_r=86, er=6,
                ll=-10, lz_l=88 + 12 * tight, kl=160 + 10 * tight, lr=10, lz_r=88 + 12 * tight, kr=160 + 10 * tight,
                sway=0.0, tilt=0, pelvis=0)


def p_sit(t):
    """sitting against the wall beside the lantern, knees up, forearms resting on the knees, head up"""
    br = math.sin(t * 1.6)
    return dict(yaw=12, lean=-3, twist=0, sh_up=0.003 * br, head=-2 + 0.8 * br, head_t=0,
                al=-16, az_l=45, ef_l=55, el=-6, ar=16, az_r=45, ef_r=55, er=6,
                ll=-9, lz_l=92, kl=150, lr=9, lz_r=88, kr=150, sway=0.0, tilt=0, pelvis=0)


def p_wall(t):
    p = dict(T.p_idle(t))
    p.update(ar=118, ef_r=12, az_r=10, head=-4, head_t=0, lean=1.5)
    return p


def p_reach(t, e):
    return lerp_pose(T.p_idle(t), p_wall(t), e)


def p_bend(t, e, side='l'):
    p = dict(T.p_idle(t))
    q = dict(p)
    if side == 'l':
        q.update(lean=-24, head=12, head_t=0, al=-66, az_l=34, ef_l=4, el=-8, ar=14, az_r=8, ef_r=22,
                 kl=36, kr=36, lz_l=24, lz_r=24, sway=0, tilt=0, pelvis=0)
    else:
        q.update(lean=22, head=12, head_t=0, ar=64, az_r=34, ef_r=4, er=8, al=-14, az_l=8, ef_l=22,
                 kl=36, kr=36, lz_l=24, lz_r=24, sway=0, tilt=0, pelvis=0)
    return lerp_pose(p, q, e)


def p_carry(t_eff):
    p = dict(T.p_walk(t_eff))
    p.update(al=-10, az_l=36, ef_l=5, el=-4)       # left hand carries the lantern
    return p


def p_hold_still(t):
    p = dict(T.p_idle(t))
    p.update(al=-10, az_l=36, ef_l=5, el=-4)
    return p


def walk_pose(ph):
    return dict(T.p_walk(ph / 6.6))


# ───────────────────────────────────────────────────────────── state builders
def base_state():
    return dict(rs=1.0, anchor=(0.5, 0.5), pan=(0.0, 0.0), scene=dict(WIDE), hero=None, lamp=None,
                ambient=1.0, f=1.0, halo=True, shaft=None, dust=0.0, shadow_alpha=1.0, lines=[], villain=[],
                readout=None, flash=0.0, fade=1.0, halation=0.18, vignette=0.55, walk_ph=None)


def hero(u, z, pose, yaw, expr='neutral', flip=False, size=1.0, lit_floor=0.0, show=True):
    return dict(u=u, z=z, pose=pose, yaw=yaw, expr=expr, flip=flip, size=size, lit_floor=lit_floor, show=show)


def lamp_floor(power=1.0, uz=None, carried=None):
    u, z, r = (uz or LAMP)
    return dict(u=u, z=z, r=r, power=power, carried=carried)


def line(text, a, cx=960, cy=985, size=44, italic=False, col=BONE):
    return (text, cx, cy, size, italic, col, a)


def vil(text, x, y, size=44, a=1.0):
    return (text, x, y, size, a)


# ───────────────────────────────────────────────────────────── shots
SHOTS = []            # (name, dur, fn, fade_in, fade_out)


def shot(name, dur, fade_in=0.0, fade_out=0.0):
    def deco(fn):
        SHOTS.append((name, dur, fn, fade_in, fade_out))
        return fn
    return deco


@shot('S01 card', 3.0)
def s01(tl, T_):
    st = base_state()
    st.update(ambient=0.0, halation=0.0, vignette=0.25)
    st['lines'] = [line('Every night, it was there.', env(tl, 0.5, 9, fi=0.7), 960, 540, 50)]
    return st


@shot('S02 wide — the light comes up', 10.0)
def s02(tl, T_):
    st = base_state()
    ramp = lin(tl, 0.0, 1.6)
    catch = ramp * (0.55 + 0.45 * flick(tl, 4.0 * (1 - ramp) + 1.0))
    p = dict(T.p_idle(T_))
    p.update(head_t=14)                              # looking back at the wall
    st['hero'] = hero(-0.22, 0.50, p, 38, 'sad')
    st['lamp'] = lamp_floor(min(1.0, catch))
    st['f'] = 1.0
    st.update(rs=lerp(1.0, 1.045, tl / 10.0), anchor=(0.42, 0.42))
    st['readout'] = (metres(0.50, LAMP[1]) * lin(tl, 0.2, 1.9), 0.85 * lin(tl, 0.2, 0.8))
    st['lines'] = [line('It was always bigger than him.', env(tl, 4.0, 9.6))]
    return st


@shot('S03 medium — he stops looking', 8.5)
def s03(tl, T_):
    st = base_state()
    p = dict(T.p_idle(T_))
    e = seg(tl, 1.8, 4.6)
    p.update(head_t=lerp(16, -8, e), head=p['head'] + 7 * e)
    st['hero'] = hero(-0.22, 0.50, p, 38, 'sad')
    st['lamp'] = lamp_floor(1.0)
    st['f'] = flick(T_)
    st.update(rs=lerp(1.55, 1.62, tl / 8.5), anchor='head', pan=(0.0, 90.0))
    st['readout'] = (metres(0.50, LAMP[1]), 0.85)
    st['lines'] = [line('He stopped looking at the wall.', env(tl, 2.2, 8.1))]
    return st


@shot('S04 the corner', 7.5)
def s04(tl, T_):
    st = base_state()
    e = seg(tl, 2.4, 5.2)
    p = lerp_pose(T.p_sad(T_), p_crouch(T_, 0.8), e)
    st['hero'] = hero(0.0, 0.455, p, lerp(-30, -50, e), 'sad')
    st['lamp'] = lamp_floor(1.0)
    st['f'] = flick(T_)
    st.update(rs=lerp(1.0, 1.04, tl / 7.5), anchor=(0.62, 0.5))
    st['readout'] = (metres(0.455, LAMP[1]), 0.85)
    st['villain'] = [vil(typed(tl, 1.6, 'stay.'), 1330, 300, 48),
                     vil(typed(tl, 4.6, 'not yet.'), 1420, 380, 40, 0.85)]
    return st


@shot('S05 insert — the flame gutters', 2.5)
def s05(tl, T_):
    st = base_state()
    st['hero'] = hero(0.0, 0.455, p_crouch(T_, 0.8), -50, 'sad')
    st['lamp'] = lamp_floor(1.0)
    st['f'] = gutter(tl)
    st.update(rs=lerp(2.7, 2.85, tl / 2.5), anchor='lamp', pan=(0.0, -40.0), halation=0.26)
    return st


@shot('S06 small', 8.0, fade_out=0.6)
def s06(tl, T_):
    st = base_state()
    st['hero'] = hero(0.0, 0.455, p_crouch(T_, 1.0), -50, 'sad')
    st['lamp'] = lamp_floor(1.0)
    st['f'] = flick(T_)
    st.update(rs=lerp(1.0, 1.05, tl / 8.0), anchor=(0.62, 0.52))
    st['readout'] = (metres(0.455, LAMP[1]), 0.85)
    st['lines'] = [line('He learned to make himself small.', env(tl, 1.0, 7.4))]
    st['villain'] = [vil('stay.', 1330, 300, 48, 0.8), vil('not yet.', 1420, 380, 40, 0.7),
                     vil(typed(tl, 4.5, 'what if.'), 1270, 470, 56)]
    return st


@shot('S07 lights out', 8.4, fade_in=0.3)
def s07(tl, T_):
    st = base_state()
    st['hero'] = hero(0.0, 0.455, p_crouch(T_, 1.0), -50, 'sad', lit_floor=0.22)
    st['lamp'] = lamp_floor(0.05)
    st['ambient'] = 0.35
    st['f'] = flick(T_, 3.0)
    st.update(rs=lerp(1.0, 1.03, tl / 8.4), anchor=(0.62, 0.52), halation=0.1)
    st['readout'] = (None, 0.6)
    st['lines'] = [line('In the dark, it could be any size.', env(tl, 1.2, 8.0), italic=True, size=42)]
    return st


@shot('S08 dark — close', 8.5)
def s08(tl, T_):
    st = base_state()
    st['hero'] = hero(0.0, 0.455, p_crouch(T_, 1.0), -50, 'sad', lit_floor=0.22)
    st['lamp'] = lamp_floor(0.05)
    st['ambient'] = 0.35
    st['f'] = flick(T_, 3.0)
    st.update(rs=lerp(1.9, 2.0, tl / 8.5), anchor='head', pan=(60.0, 40.0), halation=0.1)
    st['readout'] = (None, 0.6)
    st['lines'] = [line('That was the worst part.', env(tl, 0.8, 5.2))]
    return st


@shot('S09 relight', 8.0)
def s09(tl, T_):
    st = base_state()
    fl = 1.0 if 0.30 <= tl < 0.30 + 2 / FPS else 0.0
    ramp = lin(tl, 0.35, 1.7)
    power = ramp * (0.6 + 0.4 * flick(tl, 3.0 * (1 - ramp) + 1))
    e = seg(tl, 1.6, 3.6)
    p = lerp_pose(p_crouch(T_, 1.0), T.p_idle(T_), e)
    st['hero'] = hero(0.0, 0.455, p, lerp(-50, 8, e), 'neutral' if e > 0.5 else 'sad', lit_floor=0.22 * (1 - ramp))
    st['lamp'] = lamp_floor(min(1.0, power))
    st['ambient'] = lerp(0.35, 1.0, ramp)
    st['flash'] = fl * 0.55
    st.update(rs=lerp(1.0, 1.035, tl / 8.0), anchor=(0.6, 0.5))
    st['readout'] = (metres(0.455, LAMP[1]) * lin(tl, 0.5, 2.0), 0.85)
    st['lines'] = [line('So he lit it again.', env(tl, 2.5, 7.6))]
    return st


@shot('S10 one step — back view', 9.5)
def s10(tl, T_):
    st = base_state()
    e = seg(tl, 3.0, 4.1)
    ph = math.pi * e
    z = lerp(0.50, 0.545, e)
    if 3.0 <= tl <= 4.1:
        p = walk_pose(ph)
        st['walk_ph'] = ph
    else:
        p = dict(T.p_idle(T_))
        p = lerp_pose(p, walk_pose(0.0), 0.0 if tl < 3.0 else 0.0)
    if tl > 4.1:
        p = lerp_pose(walk_pose(math.pi), T.p_idle(T_), seg(tl, 4.1, 5.0))
    st['hero'] = hero(-0.15, z, p, 168, 'calm')
    st['lamp'] = lamp_floor(1.0)
    st['f'] = flick(T_)
    st.update(rs=lerp(1.0, 1.05, tl / 9.5), anchor=(0.46, 0.45))
    st['readout'] = (metres(z, LAMP[1]), 0.85)
    st['lines'] = [line('Not brave.  One step.', env(tl, 1.0, 8.6))]
    return st


# montage: (dur, z0, z1, framing)
MONTAGE = [(1.7, 0.56, 0.59, 'mid'), (1.6, 0.61, 0.635, 'legs'), (1.5, 0.66, 0.685, 'low'), (1.4, 0.71, 0.73, 'close'),
           (1.3, 0.76, 0.78, 'back34'), (1.2, 0.80, 0.815, 'wide'), (1.1, 0.84, 0.855, 'legs'), (0.9, 0.87, 0.88, 'close')]
WALK_RATE = 0.55 * 6.6            # rad/s of gait phase (≈1.16 footfalls/s)
_m_t0 = [None]


def montage_fn(i, dur, z0, z1, framing):
    def fn(tl, T_):
        st = base_state()
        ph = WALK_RATE * (T_ - MONT_T0)
        z = lerp(z0, z1, tl / dur)
        yaw = 168 if framing != 'back34' else 150
        st['hero'] = hero(-0.15 + 0.02 * i, z, walk_pose(ph), yaw, 'calm')
        st['walk_ph'] = ph
        st['lamp'] = lamp_floor(1.0)
        st['f'] = flick(T_)
        if framing == 'wide':
            st.update(rs=lerp(1.0, 1.04, tl / dur), anchor=(0.47, 0.45))
        elif framing == 'legs':
            st.update(rs=lerp(2.4, 2.5, tl / dur), anchor='feet')
        elif framing == 'low':
            st['scene'] = dict(y_j=840, s_near=1120)
            st.update(rs=lerp(1.08, 1.12, tl / dur), anchor=(0.47, 0.75))
        elif framing == 'close':
            st.update(rs=lerp(2.0, 2.1, tl / dur), anchor='hero')
        elif framing == 'mid':                      # v1 fix: M1 must not match S10's size (jump cut) — medium tracking
            st.update(rs=lerp(1.32, 1.36, tl / dur), anchor='hero', pan=(0.0, -40.0))
        else:
            st.update(rs=lerp(1.45, 1.5, tl / dur), anchor='hero', pan=(0.0, -60.0))
        st['readout'] = (metres(z, LAMP[1]), 0.85)
        return st
    return fn


MONT_T0 = 3.0 + 10.0 + 8.5 + 7.5 + 2.5 + 8.0 + 8.4 + 8.5 + 8.0 + 9.5    # start of the montage (abs s)
for _i, (_d, _z0, _z1, _fr) in enumerate(MONTAGE):
    SHOTS.append((f'M{_i + 1} {_fr}', _d, montage_fn(_i, _d, _z0, _z1, _fr), 0.0, 0.0))

CLIMAX = [('hero', None), ('red', 'stay.'), ('hero', None), ('red', 'not yet.'), ('reach', None), ('red2', None)]


def climax_fn(j, kind, word):
    def fn(tl, T_):
        st = base_state()
        if kind in ('hero', 'reach'):
            ph = WALK_RATE * (T_ - MONT_T0)
            z = 0.885 + 0.004 * j
            p = walk_pose(ph) if kind == 'hero' else p_reach(T_, 0.35 + 0.3 * tl / 0.4)
            st['hero'] = hero(-0.03, z, p, 170, 'calm')
            st['walk_ph'] = ph if kind == 'hero' else None
            st['lamp'] = lamp_floor(1.0)
            st['f'] = flick(T_, 1.6)
            st.update(rs=2.1 if kind == 'hero' else 2.3, anchor='hero', pan=(0.0, 30.0))
            st['readout'] = (metres(z, LAMP[1]), 0.85)
        else:
            st.update(ambient=0.0, halation=0.0, vignette=0.2)
            jit = (math.sin(T_ * 97) * 3, math.cos(T_ * 71) * 2)
            if kind == 'red':
                st['villain'] = [vil(word, 960 - 140 + jit[0], 470 + jit[1], 120)]
            else:
                st['villain'] = [vil('what if.', 700 + jit[0], 400 + jit[1], 110), vil('turn back.', 820 - jit[0], 560 + jit[1], 96, 0.9)]
        return st
    return fn


for _j, (_k, _w) in enumerate(CLIMAX):
    SHOTS.append((f'C{_j + 1} {_k}', 0.4, climax_fn(_j, _k, _w), 0.0, 0.0))

SHAFT = ((1560, -40), (1180, 760), 120, 0.55)    # 1× canvas coords; scaled by rs at render time


@shot('S12 the walk — shaft + dust', 11.5)
def s12(tl, T_):
    st = base_state()
    rate = 0.36 * 6.6
    ph = WALK_RATE * (MONT_T0 + 10.7 + 2.4 - MONT_T0) + rate * tl
    z = lerp(0.885, 0.95, lin(tl, 0.0, 10.5))
    st['hero'] = hero(-0.02, z, walk_pose(ph), 160, 'calm')
    st['walk_ph'] = ph
    st['lamp'] = lamp_floor(1.0)
    st['f'] = flick(T_)
    st['shaft'] = SHAFT
    st['dust'] = 1.0
    st.update(rs=lerp(1.0, 1.04, tl / 11.5), anchor=(0.5, 0.5))
    st['readout'] = (metres(z, LAMP[1]), 0.85)
    st['lines'] = [line('Every step, it shrank.', env(tl, 1.5, 7.4))]
    return st


@shot('S13 insert — the hand', 2.0)
def s13(tl, T_):
    st = base_state()
    e = 0.55 + 0.45 * lin(tl, 0.0, 1.9)
    st['hero'] = hero(0.0, 0.975, p_reach(T_, e), 172, 'calm')
    st['lamp'] = lamp_floor(1.0)
    st['f'] = flick(T_)
    st.update(rs=lerp(2.4, 2.5, tl / 2.0), anchor='hand')
    st['readout'] = (metres(0.975, LAMP[1]), 0.85)
    return st


@shot('S14 the wall', 12.4)
def s14(tl, T_):
    st = base_state()
    st['hero'] = hero(0.0, 0.99, p_wall(T_), 172, 'calm')
    st['lamp'] = lamp_floor(1.0)
    st['f'] = flick(T_)
    st['flash'] = max(0.0, 1.0 - tl / 0.28) ** 1.6 if tl < 0.28 else 0.0
    st.update(rs=lerp(1.32, 1.42, tl / 12.4), anchor='hero', pan=(70.0, -40.0))
    st['readout'] = (metres(0.99, LAMP[1]), 0.85)
    st['lines'] = [line('When he touched the wall, the shadow was exactly his size.', env(tl, 2.5, 11.6), 960, 940, 40)]
    return st


@shot('S15 it grew back', 8.0)
def s15(tl, T_):
    st = base_state()
    e_turn = seg(tl, 0.5, 2.0)
    yaw = lerp(172, 20, e_turn)
    if tl < 3.0:
        p = lerp_pose(p_wall(T_), T.p_idle(T_), seg(tl, 0.2, 1.4))
        z = 0.99
        st['walk_ph'] = None
    else:
        ph = WALK_RATE * (tl - 3.0)
        p = lerp_pose(T.p_idle(T_), walk_pose(ph), seg(tl, 3.0, 3.5))
        z = lerp(0.99, 0.78, lin(tl, 3.0, 8.0))
        st['walk_ph'] = ph
    st['hero'] = hero(lerp(0.0, -0.08, lin(tl, 3.0, 8.0)), z, p, yaw, 'calm')
    st['lamp'] = lamp_floor(1.0)
    st['f'] = flick(T_)
    st.update(rs=lerp(1.0, 1.03, tl / 8.0), anchor=(0.5, 0.45))
    st['readout'] = (metres(z, LAMP[1]), 0.85)
    st['lines'] = [line('It grew back the moment he walked away.', env(tl, 1.5, 7.6))]
    return st


@shot('S16 he picks up the light', 8.0)
def s16(tl, T_):
    st = base_state()
    walk_e = lin(tl, 0.0, 3.4)
    z = lerp(0.78, 0.46, walk_e)
    u = lerp(-0.08, -0.60, walk_e)
    if tl < 3.4:
        ph = WALK_RATE * (5.0 + tl)
        p = walk_pose(ph)
        st['walk_ph'] = ph
        yaw = 20
    else:
        p = T.p_idle(T_)
        yaw = lerp(20, -38, seg(tl, 3.4, 4.2))
    bend = seg(tl, 3.8, 4.9) * (1 - seg(tl, 5.5, 6.6))
    if tl >= 3.4:
        p = lerp_pose(walk_pose(WALK_RATE * 8.4), p_bend(T_, bend, 'l'), seg(tl, 3.4, 3.9))   # v1 fix: the walk→stand pop (one-frame pose jump at 3.4) is now a 0.5 s settle
        if tl >= 5.5:
            p = lerp_pose(p, p_hold_still(T_), seg(tl, 5.5, 6.6))
    lift = seg(tl, 5.1, 5.9)   # v1 fix: pick-up 0.5 → 0.8 s (the lamp + its pool moved 17 px/frame in the medium framing)
    st['hero'] = hero(u, z, p, yaw, 'calm')
    st['lamp'] = lamp_floor(1.0, carried=('l', lift) if tl >= 5.2 else None)
    st['f'] = flick(T_)
    st['shadow_alpha'] = 1.0 - lift
    st.update(rs=lerp(1.50, 1.26, walk_e) - 0.02 * lin(tl, 3.4, 8.0), anchor=(0.22, 0.62))   # v1 fix: S15→S16 was a same-size jump cut — opens as a medium (1.5×), dollies out with his approach to 1.26 so the pick-up fits
    st['readout'] = (metres(z, LAMP[1]) if lift < 0.5 else None, 0.85 * (1 - lin(tl, 6.2, 7.2)))
    st['lines'] = [line('It was never about him.  It was about where he stood.', env(tl, 1.0, 7.6), 960, 985, 40)]
    return st


@shot('S17 he carries it to the wall', 8.5)
def s17(tl, T_):
    st = base_state()
    e = lin(tl, 0.6, 6.4)
    z = lerp(0.46, 0.90, e)
    u = lerp(-0.60, -0.40, e)
    if tl < 0.6:
        p = p_hold_still(T_)
        yaw = lerp(-38, 165, seg(tl, 0.0, 0.6))
        st['walk_ph'] = None
    elif tl < 6.4:
        ph = WALK_RATE * (tl - 0.6)
        p = p_carry(ph / 6.6)
        yaw = 165
        st['walk_ph'] = ph
    else:
        yaw = 165
        p = p_hold_still(T_)
        st['walk_ph'] = None
    setdown = seg(tl, 6.6, 7.4) * (1 - seg(tl, 7.9, 8.5))
    if tl >= 6.6:
        p = p_bend(T_, setdown, 'l')
        p.update(al=lerp(-10, -66, setdown), az_l=36, ef_l=5)
    put = seg(tl, 7.2, 7.5)
    st['hero'] = hero(u, z, p, yaw, 'calm')
    st['lamp'] = lamp_floor(1.0, uz=(-0.26, 0.955, 540), carried=('l', 1.0 - put))
    st['f'] = flick(T_)
    st.update(rs=lerp(1.0, 1.03, tl / 8.5), anchor=(0.42, 0.48))
    st['lines'] = [line('So he put the light where the fear was.', env(tl, 1.0, 6.6))]
    return st


@shot('S18 final wide', 6.0, fade_out=0.6)
def s18(tl, T_):
    st = base_state()
    e = seg(tl, 0.5, 2.6)
    p = lerp_pose(T.p_idle(T_), p_sit(T_), e)
    st['hero'] = hero(-0.42, 0.93, p, lerp(60, 34, e), 'calm')
    st['lamp'] = lamp_floor(1.0, uz=(-0.26, 0.955, 540))
    st['f'] = flick(T_)
    st.update(rs=lerp(1.25, 1.3, tl / 6.0), anchor='hero', pan=(0.0, -120.0))
    st['lines'] = [line('Fear is a shadow.', env(tl, 1.5, 5.8))]
    return st


@shot('S19 quote', 6.5, fade_in=0.3)
def s19(tl, T_):
    st = base_state()
    st.update(ambient=0.0, halation=0.0, vignette=0.25)
    st['lines'] = [line('Walk toward it — and it is exactly your size.', env(tl, 0.5, 6.3, fi=0.7), 960, 540, 46, italic=True)]
    return st


@shot('S20 end card', 7.0, fade_out=1.5)
def s20(tl, T_):
    st = base_state()
    st.update(ambient=0.0, halation=0.0, vignette=0.25)
    st['lines'] = [line('WALK TOWARD IT.', env(tl, 0.0, 9, fi=0.6), 960, 500, 72),
                   line('THE SHADOW  —  a short film about a long shadow', env(tl, 1.0, 9), 960, 592, 30, italic=True, col=GREY),
                   line('a monarch noir film', env(tl, 2.0, 9), 960, 646, 24, col=GREY)]
    return st


# absolute timeline
STARTS = []
_t = 0.0
for _nm, _d, _fn, _fi, _fo in SHOTS:
    STARTS.append(_t)
    _t += _d
TOTAL = _t
assert abs(STARTS[SHOTS.index(next(s for s in SHOTS if s[0].startswith('M1')))] - MONT_T0) < 1e-6, 'montage start drift'

VO = [('vo1', STARTS[7] + 3.4, "You can't measure what you won't look at."),
      ('vo2', STARTS[[s[0] for s in SHOTS].index('S12 the walk — shaft + dust')] + 7.8, 'Keep walking.'),
      ('vo3', STARTS[[s[0] for s in SHOTS].index('S19 quote')] + 0.8, 'Fear is a shadow. Walk toward it — and it is exactly your size.')]


def shot_at(T_):
    for i in range(len(SHOTS) - 1, -1, -1):
        if T_ >= STARTS[i] - 1e-9:
            return i
    return 0


def state_at(T_):
    i = shot_at(T_)
    name, dur, fn, fi, fo = SHOTS[i]
    tl = T_ - STARTS[i]
    st = fn(tl, T_)
    fade = 1.0
    if fi > 0:
        fade *= lin(tl, 0.0, fi)
    if fo > 0:
        fade *= 1 - lin(tl, dur - fo, dur)
    st['fade'] = fade
    st['_shot'] = i
    st['_tl'] = tl
    return st


# ───────────────────────────────────────────────────────────── renderer
XS, YS = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
_r = np.sqrt(((XS / W) - 0.5) ** 2 + ((YS / H) - 0.5) ** 2) / 0.7071
VIGN = {}
GRAIN = None
DUST_K = None
DUST_P = None


def init_fx(seed=7):
    global GRAIN, DUST_K, DUST_P
    rng = np.random.default_rng(seed)
    GRAIN = [rng.normal(0, 2.4, (H, W)).astype(np.float32) for _ in range(6)]
    k = np.arange(-7, 8, dtype=np.float32)
    DUST_K = np.exp(-(k[None, :] ** 2 + k[:, None] ** 2) / 7.0).astype(np.float32)
    DUST_P = rng.random((160, 4)).astype(np.float32)   # t-param, perp offset, speed, phase


def vignette(v):
    if v not in VIGN:
        VIGN[v] = (1 - v * _r ** 2.4).astype(np.float32)
    return VIGN[v]


@functools.lru_cache(maxsize=96)
def FONT(path, size, var=None):
    return N.font(path, size, var)


def crop_origin(st, sc, J, lamp_xy, rs):
    cw, ch = W * rs, H * rs
    a = st['anchor']
    px, py = st['pan']
    if isinstance(a, tuple):
        ox, oy = (cw - W) * a[0], (ch - H) * a[1]
    elif a == 'hero' and J:
        ox, oy = J['hipc'][0] - W * 0.5, J['hctr'][1] - H * 0.24
    elif a == 'head' and J:
        ox, oy = J['hctr'][0] - W * 0.5, J['hctr'][1] - H * 0.42
    elif a == 'feet' and J:
        fy = max(J['ftl'][1], J['ftr'][1])
        ox, oy = J['hipc'][0] - W * 0.5, fy - H * 0.86
    elif a == 'hand' and J:
        ox, oy = J['har'][0] - W * 0.55, J['har'][1] - H * 0.42
    elif a == 'lamp' and lamp_xy:
        ox, oy = lamp_xy[0] - W * 0.5, lamp_xy[1] - H * 0.56
    else:
        ox, oy = (cw - W) * 0.5, (ch - H) * 0.5
    ox = clamp(ox + px * rs, 0, cw - W)
    oy = clamp(oy + py * rs, 0, ch - H)
    return ox, oy


def hero_sprite(J, K, KS, s, light, expr, lit):
    pts = [v for v in J.values() if isinstance(v, tuple) and len(v) == 2]
    m = s * 0.34 + 24
    bx, by = int(min(p[0] for p in pts) - m), int(min(p[1] for p in pts) - m)
    ex, ey = int(max(p[0] for p in pts) + m), int(max(p[1] for p in pts) + m)
    bw, bh = max(2, ex - bx), max(2, ey - by)
    layer = Image.new('RGBA', (bw * 2, bh * 2), (0, 0, 0, 0))
    J2 = {k: ((v[0] - bx) * 2, (v[1] - by) * 2) if isinstance(v, tuple) and len(v) == 2 else v for k, v in J.items()}
    N.draw_hero(layer, J2, K, KS, s * 2, ((light[0] - bx) * 2, (light[1] - by) * 2), expr=expr, scarf=True)
    spr = layer.resize((bw, bh), Image.LANCZOS)
    if lit != 1.0:
        arr = np.asarray(spr).astype(np.float32)
        arr[..., :3] *= lit
        spr = Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGBA')
    return spr, (bx, by)


def lantern_sprite(lsz, power):
    s2 = 2
    L = int(lsz * 1.0 * s2)
    cw, ch = int(lsz * 1.3 * s2) * 2, int(lsz * 3.4 * s2)
    im = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lx, ly = cw / 2, ch - lsz * 0.6 * s2
    l = lsz * s2
    body = (18, 16, 14, 255)
    gl = min(1.0, power + 0.2)
    d.rounded_rectangle([lx - l * 0.46, ly - l * 1.05, lx + l * 0.46, ly + l * 0.5], radius=l * 0.12, fill=body)
    d.rounded_rectangle([lx - l * 0.30, ly - l * 0.80, lx + l * 0.30, ly + l * 0.28], radius=l * 0.06,
                        fill=(int(255 * gl), int(226 * gl), int(185 * gl), 255))
    for bx in (-0.12, 0.12):
        d.line([(lx + bx * l * 2, ly - l * 0.8), (lx + bx * l * 2, ly + l * 0.28)], fill=body, width=max(2, int(l * 0.05)))
    d.line([(lx, ly - l * 1.05), (lx, ly - l * 1.3)], fill=body, width=max(2, int(l * 0.09)))
    d.arc([lx - l * 0.42, ly - l * 1.9, lx + l * 0.42, ly - l * 1.1], 190, 350, fill=body, width=max(2, int(l * 0.07)))
    spr = im.resize((cw // s2, ch // s2), Image.LANCZOS)
    return spr, (lx / s2, ly / s2)


def paste_rgba(base, spr, x, y):
    """alpha-composite spr onto base (RGBA) at float (x, y) — crops negative offsets."""
    x, y = int(round(x)), int(round(y))
    if x < 0 or y < 0:
        cx, cy = max(0, -x), max(0, -y)
        if cx >= spr.width or cy >= spr.height:
            return
        spr = spr.crop((cx, cy, spr.width, spr.height))
        x, y = max(0, x), max(0, y)
    if x >= base.width or y >= base.height:
        return
    base.alpha_composite(spr, dest=(x, y))


def add_patch(img, cx, cy, kern, gain):
    r = kern.shape[0] // 2
    x0, y0 = int(cx) - r, int(cy) - r
    x1, y1 = x0 + kern.shape[1], y0 + kern.shape[0]
    sx0, sy0 = max(0, -x0), max(0, -y0)
    sx1, sy1 = kern.shape[1] - max(0, x1 - W), kern.shape[0] - max(0, y1 - H)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    img[max(0, y0):max(0, y0) + (sy1 - sy0), max(0, x0):max(0, x0) + (sx1 - sx0)] += (kern[sy0:sy1, sx0:sx1] * gain)[..., None]


def soft_ellipse_mul(img, cx, cy, rx, ry, strength, blur):
    """multiply img by (1 - strength·soft ellipse) using a local patch"""
    pad = int(blur * 3 + 4)
    x0, y0 = int(cx - rx - pad), int(cy - ry - pad)
    x1, y1 = int(cx + rx + pad) + 1, int(cy + ry + pad) + 1
    x0c, y0c, x1c, y1c = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if x1c <= x0c or y1c <= y0c:
        return
    m = Image.new('L', (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(m).ellipse([cx - rx - x0, cy - ry - y0, cx + rx - x0, cy + ry - y0], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(m, np.float32)[y0c - y0:y1c - y0, x0c - x0:x1c - x0] / 255
    img[y0c:y1c, x0c:x1c] *= (1 - strength * a)[..., None]


def render_frame(T_, grain_i=0, st=None):
    st = st or state_at(T_)
    rs = float(st['rs'])
    N.SS = rs
    sc = N.Scene(**st['scene'])
    hz = st['hero']
    J = K = KS = None
    s = 0.0
    if hz and hz['show']:
        s = sc.scale(hz['z']) * hz['size']
        pose = dict(hz['pose'])
        pose['yaw'] = hz['yaw']
        K, J, KS = N.solve(sc.x(hz['u'], hz['z']), sc.feet_y(hz['z']), s, pose, hz['flip'])
    lp = st['lamp']
    lamp_xy = None
    lsz = 0.0
    lz = None
    if lp:
        lz = lp['z']
        lsz = 58 * rs * (0.3 / lz) ** 0.9
        floor_xy = (sc.x(lp['u'], lp['z']), sc.feet_y(lp['z']) - 26 * rs * (0.3 / lz) ** 0.9)
        lamp_xy = floor_xy
        if lp['carried'] and J:
            side, e = lp['carried']
            hand = J['hal'] if side == 'l' else J['har']
            hz_z = hz['z']
            hand_lamp = (hand[0], hand[1] + lsz * 1.25)
            lamp_xy = (lerp(floor_xy[0], hand_lamp[0], e), lerp(floor_xy[1], hand_lamp[1], e))
            lz = lerp(lp['z'], hz_z + 0.05, e)
    ox, oy = crop_origin(st, sc, J, lamp_xy, rs)
    xs, ys = XS + np.float32(ox), YS + np.float32(oy)
    y_j = sc.y_j
    wall = ys < y_j
    # shadow on the wall (homothety about the lamp), only when the lamp is behind the hero
    sh = None
    k = None
    if J and lp and lp['power'] > 0.02 and st['shadow_alpha'] > 0 and lz is not None and hz['z'] - lz > 0.03:
        k = min((1.0 - lz) / (hz['z'] - lz), 2.2)
        tdx = -math.copysign(s * 0.14, lamp_xy[0] - J['hipc'][0])     # body thickness: the shadow peeks out away from the lamp
        Jsh = {kk: (v[0] - ox + tdx, v[1] - oy) if isinstance(v, tuple) and len(v) == 2 else v for kk, v in J.items()}
        sh = N.shadow_mask((W, H), Jsh, K, KS, s, (lamp_xy[0] - ox, lamp_xy[1] - oy), k, anchor_y=y_j - oy)
        sh *= st['shadow_alpha']
    # ── plate
    amb = st['ambient']
    img = np.where(wall[..., None], N.WALL * amb, N.FLOOR * amb).astype(np.float32)
    jl = (ys >= y_j) & (ys < y_j + 2 * rs)
    img[jl] = N.WALL * 1.9 * amb
    if lp and lp['power'] > 0:
        g = LIGHT_GAIN * lp['power'] * st['f']
        lx, ly = lamp_xy
        lr = lp['r']
        wash = np.exp(-((xs - lx) / (lr * rs * 1.9)) ** 2) * np.exp(-np.abs(y_j - ys) / (420 * rs)) * (g * 0.125)
        wash *= wall
        li = N.point_light(xs, ys, lx, ly, lr * rs * 0.8, g * 0.24)
        if sh is not None:
            cut = 1.0 - 0.93 * sh * wall
            wash *= cut
            li *= cut
            img *= (1.0 - 0.55 * sh * wall * min(1.0, lp['power'] * 1.2))[..., None]
        pl = N.point_light(xs, ys, lx, ly + 10 * rs, lr * rs * 0.75, g * 0.30, aniso=0.26)
        pl = np.where(wall, pl * 0.1, pl)
        lum = wash + li + pl
        if st['halo']:
            lum += N.point_light(xs, ys, lx, ly - lsz * 0.25, lsz * 2.4, 1.0) * (0.55 * lp['power'] * st['f'])
        img += N.AMBER[None, None, :] * lum[..., None]
    if st['shaft'] is not None:
        (x0, y0), (x1, y1), hw, power = st['shaft']
        x0, y0, x1, y1 = x0 * rs, y0 * rs, x1 * rs, y1 * rs
        vx, vy = x1 - x0, y1 - y0
        ln = math.hypot(vx, vy) + 1e-6
        t = ((xs - x0) * vx + (ys - y0) * vy) / (ln * ln)
        perp = np.abs((xs - x0) * vy - (ys - y0) * vx) / ln
        half = hw * rs * (0.35 + 0.95 * t.clip(0, 1))
        shf = np.exp(-(perp / (half + 1)) ** 2 * 2.0) * (t > 0) * (t < 1.15) * (1 - 0.65 * t.clip(0, 1))
        img += np.array([220, 190, 150], np.float32)[None, None, :] * (shf * power * (0.9 + 0.1 * st['f']))[..., None]
        if st['dust'] > 0:
            hm = float(half.mean())
            for i in range(DUST_P.shape[0]):
                a, b, c, d = DUST_P[i]
                tt = (a + 0.012 * T_ * (0.5 + c)) % 1.0
                pp = (b - 0.5) * 2.2 + 0.08 * math.sin(T_ * (0.7 + d) + i)
                px = x0 + vx * tt + (-vy / ln) * pp * hm
                py = y0 + vy * tt + (vx / ln) * pp * hm
                if px >= ox - 8 and px < ox + W + 8 and py >= oy - 8 and py < oy + H + 8:
                    tw = 0.5 + 0.5 * math.sin(T_ * (2.1 + 3 * d) + i * 1.7)
                    add_patch(img, px - ox, py - oy, DUST_K, 95 * power * st['dust'] * (0.35 + 0.65 * c) * tw)
    base = None
    if J:
        # contact shadow under the feet (+ long floor shadow toward the camera when the light is in front)
        fy = sc.feet_y(hz['z'])
        soft_ellipse_mul(img, J['hipc'][0] - ox, fy - oy, s * 0.22, s * 0.035, 0.7, 8 * rs)
        if lp and lz is not None and lz >= hz['z'] - 0.03 and lp['power'] > 0.02:
            soft_ellipse_mul(img, J['hipc'][0] - ox, fy - oy + s * 0.28, s * 0.20, s * 0.30, 0.45 * lp['power'], 14 * rs)
    base = Image.fromarray(img.clip(0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    if J:
        light = lamp_xy or (ox + W * 0.5, oy - 200)
        if lp and lp['power'] > 0:
            dd = math.hypot(J['hipc'][0] - light[0], J['hipc'][1] - light[1]) / (lp['r'] * rs)
            lit = (0.55 + 0.45 / (1 + 0.9 * dd * dd)) * (st['f'] ** 0.5)
            lit = lit * min(1.0, lp['power'] * 1.6 + hz['lit_floor'] / 1.0)
            lit = max(lit, hz['lit_floor'])
        else:
            lit = max(0.12, hz['lit_floor'])
        spr, (bx, by) = hero_sprite(J, K, KS, s, light, hz['expr'], lit)
        paste_rgba(base, spr, bx - ox, by - oy)
    if lp and lp['power'] > 0 and lsz > 3:
        spr, (ax, ay) = lantern_sprite(lsz, lp['power'])
        paste_rgba(base, spr, lamp_xy[0] - ox - ax, lamp_xy[1] - oy - ay)
    # ── screen-space type
    if st['lines'] or st['villain'] or st['readout'] is not None:
        txt = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(txt)
        for (text, cx, cy, size, italic, col, a) in st['lines']:
            if a <= 0.002 or not text:
                continue
            f = FONT(N.F_SERIF_I if italic else N.F_SERIF, size)
            w = d.textlength(text, font=f)
            d.text((cx - w / 2, cy - size * 0.6), text, font=f, fill=tuple(col) + (int(255 * a),))
        for (text, x, y, size, a) in st['villain']:
            if not text or a <= 0:
                continue
            f = FONT(N.F_TYPE, size)
            jx, jy = math.sin(T_ * 131.0) * 0.8, math.cos(T_ * 97.0) * 0.8
            d.text((x + 3 + jx, y + 2 + jy), text, font=f, fill=RED + (int(255 * a * 0.35),))
            d.text((x + jx, y + jy), text, font=f, fill=RED + (int(255 * a),))
        if st['readout'] is not None:
            val, a = st['readout']
            if a > 0.002:
                fm, fl = FONT(N.F_SANS, 20, 'Medium'), FONT(N.F_SANS, 20, 'Light')
                A = int(255 * a)
                d.text((64, 48), 'SHADOW', font=fm, fill=BONE + (A,))
                d.text((182, 48), ('--  m' if val is None else f'{val:.1f} m'), font=fl, fill=BONE + (A,))
                if val is not None:
                    bar = max(2, int(min(val, 9.9) / 7.0 * 220))
                    d.rectangle([64, 78, 64 + bar, 79], fill=BONE + (int(A * 0.7),))
        base.alpha_composite(txt)
    # ── finish
    a = np.asarray(base.convert('RGB'), np.float32)
    a *= vignette(st['vignette'])[..., None]
    if st['halation'] > 0:
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGB')
        small = im.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4.5)).resize((W, H), Image.BILINEAR)
        a += (np.asarray(small, np.float32) - 60).clip(0, None) * st['halation']
    gi = GRAIN[grain_i % len(GRAIN)]
    sh_x, sh_y = (grain_i * 37) % W, (grain_i * 53) % H
    a += np.roll(gi, (sh_y, sh_x), axis=(0, 1))[..., None]
    if st['flash'] > 0:
        a = a * (1 - st['flash']) + FLASHCOL[None, None, :] * st['flash']
    if st['fade'] < 1.0:
        a *= st['fade']
    return a.clip(0, 255).astype(np.uint8), dict(k=k, s=s / rs, ox=ox, oy=oy)


# ───────────────────────────────────────────────────────────── events (audio)
def events():
    ev = dict(fps=FPS, total=TOTAL, shots=[dict(name=n, t0=STARTS[i], dur=d) for i, (n, d, _, _, _) in enumerate(SHOTS)],
              cuts=[STARTS[i] for i in range(1, len(SHOTS))], steps=[], clicks=[], vo=[dict(id=i, t=t, text=x) for i, t, x in VO],
              lamp=[], flash=[], dips=[], readout=[])
    last_n = None
    nfr = int(TOTAL * FPS)
    prev_power, prev_vis = 0.0, {}
    for fi in range(nfr):
        T_ = fi / FPS
        st = state_at(T_)
        ph = st.get('walk_ph')
        if ph is not None:
            n = math.floor((ph - math.pi / 2) / math.pi)
            if last_n is not None and n > last_n:
                hz = st['hero']
                ev['steps'].append(dict(t=round(T_, 3), u=hz['u'], z=hz['z'], side=int(n % 2)))
            last_n = n
        else:
            last_n = None
        # typewriter clicks: a new character appeared
        for (text, x, y, size, a) in st['villain']:
            key = (st['_shot'], x // 50, y // 50)
            n = len(text)
            if prev_vis.get(key, 0) < n and size < 100:
                ev['clicks'].append(round(T_, 3))
            prev_vis[key] = n
        p = st['lamp']['power'] if st['lamp'] else 0.0
        if p > 0.2 and prev_power <= 0.2:
            ev['lamp'].append(dict(t=round(T_, 3), on=True))
        if p <= 0.2 and prev_power > 0.2:
            ev['lamp'].append(dict(t=round(T_, 3), on=False))
        prev_power = p
        if st['flash'] > 0.5 and (not ev['flash'] or T_ - ev['flash'][-1] > 1.0):
            ev['flash'].append(round(T_, 3))
        if st['fade'] < 0.02 and (not ev['dips'] or T_ - ev['dips'][-1] > 1.0):
            ev['dips'].append(round(T_, 3))
        if fi % FPS == 0 and st['readout'] is not None:
            ev['readout'].append(dict(t=T_, m=None if st['readout'][0] is None else round(st['readout'][0], 2)))
    ev['montage'] = [MONT_T0, MONT_T0 + 10.7]
    ev['climax'] = [MONT_T0 + 10.7, MONT_T0 + 10.7 + 2.4]
    ev['wall_touch'] = STARTS[[s[0] for s in SHOTS].index('S14 the wall')]
    ev['lift'] = STARTS[[s[0] for s in SHOTS].index('S16 he picks up the light')] + 5.4
    ev['setdown'] = STARTS[[s[0] for s in SHOTS].index('S17 he carries it to the wall')] + 7.4
    ev['end_card'] = STARTS[-1]
    return ev


# ───────────────────────────────────────────────────────────── main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--frame', type=float)
    ap.add_argument('--events')
    ap.add_argument('--render')
    ap.add_argument('--t0', type=float, default=0.0)
    ap.add_argument('--t1', type=float)
    ap.add_argument('--metrics')
    args = ap.parse_args()
    init_fx()
    print(f'timeline: {len(SHOTS)} shots, {TOTAL:.1f} s; montage@{MONT_T0}; VO at', [round(t, 1) for _, t, _ in VO], flush=True)
    if args.events:
        json.dump(events(), open(args.events, 'w'), indent=1)
        print('events →', args.events)
    if args.frame is not None:
        fr, info = render_frame(args.frame)
        p = os.path.join(OUTDIR, f'frame_{args.frame:.2f}.jpg')
        Image.fromarray(fr).save(p, quality=92)
        print(p, N.measure(fr), info)
    if args.preview:
        t0 = time.time()
        frames = []
        for i, (name, dur, fn, fi, fo) in enumerate(SHOTS):
            T_ = STARTS[i] + dur * 0.55
            fr, info = render_frame(T_, i)
            m = N.measure(fr)
            print(f'{name:34s} t={T_:6.1f} luma {m["luma"]:5.1f} dark {m["dark_lt30"]:.2f} chroma {m["chroma"]:4.1f} k {info["k"] and round(info["k"], 2)}  {time.time() - t0:.0f}s', flush=True)
            frames.append((f'{name}  t={T_:.1f}s  L{m["luma"]:.0f} D{m["dark_lt30"]:.2f}', fr))
        cw, ch, lb = 640, 360, 30
        cols = 4
        rows = math.ceil(len(frames) / cols)
        sheet = Image.new('RGB', (cw * cols, (ch + lb) * rows), (18, 18, 20))
        d = ImageDraw.Draw(sheet)
        f = FONT(N.F_SANS, 16, 'Medium')
        for i, (label, fr) in enumerate(frames):
            r, c = divmod(i, cols)
            sheet.paste(Image.fromarray(fr).resize((cw, ch), Image.LANCZOS), (c * cw, r * (ch + lb) + lb))
            d.text((c * cw + 8, r * (ch + lb) + 7), label, font=f, fill=(225, 222, 214))
        p = os.path.join(OUTDIR, 'preview_sheet.jpg')
        sheet.save(p, quality=86)
        print('preview →', p, f'{time.time() - t0:.0f}s')
    if args.render:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        t1 = args.t1 if args.t1 is not None else TOTAL
        n0, n1 = int(round(args.t0 * FPS)), int(round(t1 * FPS))
        cmd = [ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
               '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'film',
               '-x264-params', 'aq-mode=3:aq-strength=1.1:keyint=48:min-keyint=24', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', args.render]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        t0 = time.time()
        per_shot = {}
        errors = []
        last = np.zeros((H, W, 3), np.uint8)
        for fi in range(n0, n1):
            T_ = fi / FPS
            st = state_at(T_)
            try:
                fr, info = render_frame(T_, fi, st)
                last = fr
            except Exception as ex:          # never lose a 40-minute render to one bad frame: repeat the previous frame, log it
                print(f'!! frame {fi} t={T_:.3f} failed: {ex!r}', flush=True)
                fr = last
                errors.append(dict(frame=fi, t=T_, err=repr(ex)))
            proc.stdin.write(fr.tobytes())
            if fi % 6 == 0:
                m = N.measure(fr)
                d = per_shot.setdefault(st['_shot'], dict(name=SHOTS[st['_shot']][0], n=0, luma=0.0, dark=0.0, chroma=0.0, p99=0.0, lmin=999, lmax=0))
                d['n'] += 1
                d['luma'] += m['luma']
                d['dark'] += m['dark_lt30']
                d['chroma'] += m['chroma']
                d['p99'] += m['p99']
                d['lmin'] = min(d['lmin'], m['luma'])
                d['lmax'] = max(d['lmax'], m['luma'])
            if fi % 48 == 0:
                el = time.time() - t0
                done = fi - n0 + 1
                print(f'frame {fi}/{n1}  t={T_:6.1f}s  {SHOTS[st["_shot"]][0][:28]:28s}  {el / done:.2f}s/f  ETA {(n1 - fi) * el / done / 60:.1f} min', flush=True)
        proc.stdin.close()
        proc.wait()
        for d in per_shot.values():
            for kk in ('luma', 'dark', 'chroma', 'p99'):
                d[kk] = round(d[kk] / max(1, d['n']), 2)
        mp = args.metrics or (args.render + '.metrics.json')
        json.dump(dict(total=TOTAL, shots=list(per_shot.values()), render_seconds=round(time.time() - t0), errors=errors), open(mp, 'w'), indent=1)
        print('render done →', args.render, f'{(time.time() - t0) / 60:.1f} min; metrics →', mp)


if __name__ == '__main__':
    main()
