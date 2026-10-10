"""
power.py — "POWERFUL MAN KAISE BANE" · 42 s · 1080x1920 · 30 fps
=================================================================
Same engine as the shipped money short (clean.py + toon.py 3D rig), new film.
Everything generic is imported from clean.py; only the scenes, the chrome, the
timeline and the camera rig live here.

What is new on top of v9 (each one is a measured v9 weakness, see VIDEO_POWER_NOTES.md §1):
  * pose BLENDING — v9 hard-switched poses (`p_point if lt > .9 else p_think`);
    every pose change here is a 0.5–0.7 s eased blend with overshoot
  * six new poses on the v9 3D contract: squat cycle, double-biceps flex,
    hands-on-hips power stance, reading, calm breathing, flinch
  * eye-line: the hero LOOKS at the prop the viewer should read next (law 6)
  * camera: zoom floor Z0 (v9 dipped to z 0.990 on odd scenes -> black
    slivers), linear-dominant ramp + triangle pans (no zero-velocity frames)
  * the voice is not time-stretched; the picture is cut to the voice
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '/home/user/src')
import toon as T
from toon import toon
import clean as C
from clean import (W, H, FPS, PAPER, PAPER_D, SOFT, INK, ACC, ACC_HI, GY, PAY_Y, CAP_Y,
                   cl, fl, e_out, e_io, e_back, F, tw, line, fbox, fcirc, fpoly, stroke,
                   tickmark, shadow, backdrop, caption, payoff, phys)
from timeline_power import SCENE_START, SCENE_END, DUR_TOTAL, VO_AT, NAMES

NF = int(round(FPS * DUR_TOTAL))          # 1260
CUTS = SCENE_START[1:]
TDUR, TLAG = 0.46, 0.050
CHAPTER = ['HOOK', 'JISM', 'DIMAGH', 'CONTROL', 'VALUE', 'GO']
RED = ACC[0]

# calm = eyes shut, mouth soft. Additive: toon.EXPR gains a key, nothing changes.
T.EXPR['calm'] = dict(brow=None, eye='closed', mouth='flat', mw=.40)
T.EXPR['calm_smile'] = dict(brow=None, eye='closed', mouth='smile', mw=.50)

# ───────────────────────────────────────────── pose blending
_DEF = dict(lean=0, twist=0, pelvis=0, tilt=0, sway=0, sh_up=0, head=0, head_t=0, yaw=0,
            al=-14, az_l=0, el=-5, ef_l=8, ar=14, az_r=0, er=5, ef_r=8,
            ll=-4, lz_l=0, kl=2, lr=4, lz_r=0, kr=2, _bob=0.0, _br=0.0, _hv=0.0)


def mix(a, b, k):
    """Channel-wise blend of two solved poses. Strings (hand styles) switch at
    the midpoint. k is expected to be already eased."""
    k = cl(k)
    if k <= 0: return a
    if k >= 1: return b
    o = {}
    for key in set(a) | set(b):
        va, vb = a.get(key, _DEF.get(key)), b.get(key, _DEF.get(key))
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            o[key] = va + (vb - va) * k
        else:
            o[key] = vb if k >= .5 else va
    return o


def blend(fa, fb, t, t0, d=0.6, s=1.10, **kb):
    """Pose A until t0, eased (with a little overshoot) into pose B over d s."""
    pa = phys(fa, t)
    pb = phys(fb, t, **kb) if kb else phys(fb, t)
    return mix(pa, pb, e_back(cl((t - t0) / d), s))


# ───────────────────────────────────────────── new poses (v9 contract)
def p_power(t):
    """Hands on hips, chest open, chin up, feet wide. The 'arrived' stance."""
    br = math.sin(t * 1.9)
    w = math.sin(t * .43)
    return dict(yaw=9 + w * 1.5, lean=-1.8, twist=-1.5 * w, sh_up=-0.006,
                sway=0.006 * w, tilt=-1.2 * w, pelvis=1.0 * w,
                head=-3.6 + math.sin(t * .7) * .8, head_t=2.5,
                al=-44, az_l=4, el=88, ef_l=5,
                ar=44, az_r=4, er=-88, ef_r=5,
                ll=-10, lz_l=0, kl=2, lr=10, lz_r=0, kr=2,
                hl='fist', hr='fist', _br=br * 1.3)


def p_flex(t):
    """Double biceps. Forearms fold UP (abd + eabd = -168 deg), fists closed."""
    j = math.sin(t * 5.0) * 2
    return dict(yaw=6, lean=-2.2, sh_up=0.006, head=1.5, head_t=0,
                al=-98 - j, az_l=10, el=-70, ef_l=0,
                ar=98 + j, az_r=10, er=70, ef_r=0,
                ll=-9, lz_l=0, kl=3, lr=9, lz_r=0, kr=3,
                hl='fist', hr='fist', _br=math.sin(t * 2.2))


def p_squat(t, q=0.0):
    """q = 0 standing tall, 1 = bottom of the squat. The thigh swings forward
    (sagittal), the knee folds so the shin stays a little ahead of vertical
    (knee over toe), the torso counter-leans to keep the mass over the feet,
    and the arms come forward for balance."""
    thigh = 92 * q
    shin = 15 * q
    return dict(yaw=62, lean=20 * q, head=-14 * q, head_t=0, twist=0,
                al=-12, az_l=74 * q, el=-6, ef_l=12,
                ar=12, az_r=74 * q, er=6, ef_r=12,
                ll=-11, lz_l=thigh, kl=thigh - shin,
                lr=11, lz_r=thigh, kr=thigh - shin,
                hl='fist', hr='fist', _br=math.sin(t * 2.2))


def squat_feet_shift(q, s):
    """Horizontal drift of the feet (toward the camera, projected through the
    62 deg yaw) so the hero can be re-anchored and the feet stay planted."""
    thigh, shin = math.radians(92 * q), math.radians(15 * q)
    z = T.P['leg_u'] * math.sin(thigh) + T.P['leg_l'] * math.sin(shin)
    return z * math.sin(math.radians(62)) * s


def p_read(t):
    """Book held at chest height: upper arms forward, forearms rising toward
    the lens, head tilted down to the page."""
    o = math.sin(t * .8)
    return dict(yaw=24, lean=3, twist=4, tilt=-2, pelvis=2, sway=0.008,
                head=11 + o * .8, head_t=4,
                al=-16, az_l=40, el=2, ef_l=70,
                ar=16, az_r=40, er=-2, ef_r=70,
                ll=-4, lz_l=0, kl=3, lr=5, lz_r=0, kr=4,
                hl='open', hr='open', _br=math.sin(t * 2.0))


def p_calm(t):
    """Still, arms loose, slow deep breathing — the chest rises on a 5 s cycle."""
    br = math.sin(t * 1.25)
    return dict(yaw=6, lean=-0.5, sh_up=-0.004 + 0.004 * br, head=1.5, head_t=0,
                al=-9, az_l=2, el=-3, ef_l=6, ar=9, az_r=2, er=3, ef_r=6,
                ll=-6, lz_l=0, kl=2, lr=6, lz_r=0, kr=2,
                hl='relax', hr='relax', _br=br * 1.4)


def p_flinch(t):
    """Startled: weight back, shoulders up, hands half-raised."""
    return dict(yaw=10, lean=-7, sh_up=0.014, head=-6, head_t=-4,
                al=-34, az_l=34, el=-6, ef_l=48, ar=34, az_r=34, er=6, ef_r=48,
                ll=-7, lz_l=-2, kl=6, lr=9, lz_r=0, kr=3,
                hl='open', hr='open', _br=0.0)


# ───────────────────────────────────────────── hero with eye-line + joints
def hero(d, lt, x, s, pose, expr, p=1.0, flip=False, bob=0.0, look=(0, 0)):
    """Same contact shadows as clean.hero, plus `look` and the joint dict."""
    if p <= 0: return None
    sc = s * (0.90 + 0.10 * e_back(cl(p * 1.6), 1.6))
    lift = bob + pose.get('_bob', 0.0) * sc
    shadow(d, x, GY + 8, sc * .165, 66, lift)
    shadow(d, x, GY + 5, sc * .070, 104, lift * 1.5)
    return toon(d, x, GY - lift, sc, pose, expr, flip=flip, look=look, blink=T.blink_at(lt))


def glance(lt, t0, d=1.4, dx=1.0, dy=0.2):
    """Eyes flick toward (dx, dy) at t0 and drift back over d seconds."""
    u = (lt - t0) / d
    if u < 0 or u > 1: return (0, 0)
    k = e_out(cl(u * 4), 2.5) * (1 - e_io(cl((u - .55) / .45)))
    return (dx * k, dy * k)


# ───────────────────────────────────────────── shared props
def ring(d, cx, cy, r, p, acc, w=22, track=(226, 219, 203)):
    """Progress ring: full soft track, accent arc sweeping clockwise from 12."""
    d.ellipse([cx - r - w / 2, cy - r - w / 2, cx + r + w / 2, cy + r + w / 2], fill=INK)
    d.ellipse([cx - r + w / 2 + 6, cy - r + w / 2 + 6, cx + r - w / 2 - 6, cy + r - w / 2 - 6],
              fill=PAPER)
    bb = [cx - r, cy - r, cx + r, cy + r]
    d.arc(bb, 0, 360, fill=track, width=w)
    if p > 0:
        d.arc(bb, -90, -90 + 360 * cl(p), fill=acc, width=w)
        a = math.radians(-90 + 360 * cl(p))
        ex, ey = cx + math.cos(a) * r, cy + math.sin(a) * r
        d.ellipse([ex - w / 2, ey - w / 2, ex + w / 2, ey + w / 2], fill=acc)


def cross(d, cx, cy, s, col, p=1.0, w=10):
    if p <= 0: return
    k1, k2 = cl(p * 2), cl(p * 2 - 1)
    stroke(d, [(cx - s, cy - s), (cx - s + 2 * s * k1, cy - s + 2 * s * k1)], col, w)
    if k2 > 0:
        stroke(d, [(cx + s, cy - s), (cx + s - 2 * s * k2, cy - s + 2 * s * k2)], col, w)


def book(d, hl, hr, acc, flip_p=0.0):
    """An OPEN hardback held between the two hand joints: two page panels in a
    shallow V around a spine, cover peeking out below. `flip_p` draws a page
    mid-turn."""
    (x0, y0), (x1, y1) = hl, hr
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 - 10
    hw = max(74, abs(x1 - x0) * .60 + 34)
    hh = hw * .68
    lift = hh * .22                                   # outer edges rise: the V
    cover = [(cx - hw - 8, cy - hh + 8 - lift), (cx, cy - hh + 22), (cx + hw + 8, cy - hh + 8 - lift),
             (cx + hw + 8, cy + hh * .40 - lift), (cx, cy + hh * .40 + 14), (cx - hw - 8, cy + hh * .40 - lift)]
    fpoly(d, cover, acc, 6)
    for sx in (-1, 1):                                # two pages
        page = [(cx + sx * 6, cy - hh + 24), (cx + sx * (hw - 2), cy - hh + 12 - lift),
                (cx + sx * (hw - 2), cy + hh * .40 - 6 - lift), (cx + sx * 6, cy + hh * .40 + 4)]
        d.polygon(page, fill=(252, 250, 244), outline=(196, 188, 172))
        for k in range(4):                            # text lines following the page slant
            f = (k + 1) / 5.5
            ya = cy - hh + 24 + (hh * .40 + 4 - (-hh + 24)) * f
            yb = cy - hh + 12 - lift + (hh * .40 - 6 - lift - (-hh + 12 - lift)) * f
            d.line([(cx + sx * 16, ya), (cx + sx * (hw - 18), yb)], fill=(206, 198, 182), width=3)
    d.line([(cx, cy - hh + 22), (cx, cy + hh * .40 + 14)], fill=(176, 168, 152), width=4)
    if 0 < flip_p < 1:                                # turning page arcs from right to left
        a = math.pi * flip_p
        px = cx + math.cos(a) * (hw - 10)
        top = cy - hh + 14 - lift * abs(math.cos(a)) - math.sin(a) * 34
        d.polygon([(cx, cy - hh + 22), (px, top), (px, cy + hh * .40 - 4 - lift * abs(math.cos(a)) - math.sin(a) * 14),
                   (cx, cy + hh * .40 + 10)], fill=(255, 253, 248), outline=(190, 182, 166))


# ───────────────────────────────────────────── chrome / captions
def chrome(d, t, si, acc):
    y = 142
    d.rounded_rectangle([64, y - 3, W - 64, y + 3], 3, fill=(222, 215, 199))
    fxp = 64 + (W - 128) * cl(t / DUR_TOTAL)
    d.rounded_rectangle([64, y - 3, fxp, y + 3], 3, fill=acc)
    d.ellipse([fxp - 9, y - 9, fxp + 9, y + 9], fill=acc)
    d.text((64, 198), f'{si + 1:02d}', font=F(34, 800), fill=acc, anchor='lm')
    d.text((108, 199), f'/ 06   {CHAPTER[si]}', font=F(26, 600), fill=SOFT, anchor='lm')


# ───────────────────────────────────────────── 1  HOOK   (6.376 s, VO at 0.30)
#   0.34 "Powerful man banna hai?"   1.80 "Taqat muscles se nahi"
#   3.36 "aadaton se aati hai"       4.59 "Yeh chaar aadatein pakdo"
def s1(d, lt, acc):
    line(d, ['POWERFUL'], W / 2, 318, 124, 800, acc, None, acc, cl((lt + .25) / .60), 46)
    line(d, ['BANNA', 'HAI?'], W / 2, 436, 96, 800, INK, None, acc, cl((lt + .05) / .60), 42)
    # walk in, slump, then — on "aadaton" — stand tall
    wk = cl(lt / 1.05)
    x = 250 + (W / 2 - 250) * e_io(wk)
    if wk < 1:
        pose, ex = phys(T.p_walk, lt), 'worried'
    else:
        pose = blend(T.p_sad, p_power, lt, 3.30, .70, 1.16)
        ex = 'sad' if lt < 3.42 else ('determined' if lt < 4.55 else 'proud')
    # eyes flick to the dumbbell when it lands, then to the habit row
    lk = glance(lt, 1.85, 1.1, .9, -.3) if lt < 3.3 else glance(lt, 3.45, 1.2, .9, .1)
    hero(d, lt, x, 546, pose, ex, look=lk)

    # the one prop cluster: dumbbell (crossed) -> four habit boxes (ticked)
    dp = cl((lt - 1.80) / .45)
    if dp > 0:
        k = e_back(dp, 1.6)
        bx, by = 820 + fl(lt, 1, 3.2), 690 + fl(lt, 3, 4.0)
        stroke(d, [(bx - 92 * k, by), (bx + 92 * k, by)], INK, 14)
        for sx in (-1, 1):
            fbox(d, bx + sx * 112 * k - 34, by - 58, bx + sx * 112 * k + 34, by + 58, 10, PAPER_D, 6)
            fbox(d, bx + sx * 158 * k - 18, by - 40, bx + sx * 158 * k + 18, by + 40, 8, PAPER_D, 6)
        cross(d, bx, by, 96, RED, cl((lt - 2.55) / .34), 14)
    hp = cl((lt - 3.40) / .5)
    if hp > 0:
        for i in range(4):
            q = cl((hp * 1.5 - i * .14) / .6)
            if q <= 0: continue
            k = e_back(q, 1.5)
            cx = 686 + i * 92 + fl(lt, i + 4, 2.2)
            cy = 900 + fl(lt, i + 8, 3.0)
            hw = 36 * k
            fbox(d, cx - hw, cy - hw, cx + hw, cy + hw, 10, PAPER, 6)
            tickmark(d, cx, cy, 20, acc, cl(q * 1.6 - .4), 9)
    payoff(d, ['4', 'AADATEIN'], cl((lt - 4.60) / .55), acc, {0})


# ───────────────────────────────────────────── 2  JISM   (5.986 s, VO at 0.05)
#   0.09 "Pehli aadat"  0.96 "roz subah bees minute jism ko tapao"
#   3.63 "Jism mazboot"  4.57 "toh dimagh mazboot"
def s2(d, lt, acc):
    line(d, ['JISM', 'TAPAO'], W / 2, 348, 118, 800, INK, {0}, acc, cl(lt / .55), 42)
    hx, hs = 300, 500
    # three squats (0.75 -> 3.45), then an eased rise into the double-biceps flex
    REP, T0, NREP = 0.90, 0.75, 3
    if lt < T0:
        pose = blend(T.p_idle, lambda t: p_squat(t, 0.0), lt, 0.0, .4)
        q = 0.0
    elif lt < T0 + REP * NREP:
        ph = (lt - T0) / REP
        q = (0.5 - 0.5 * math.cos(2 * math.pi * ph)) ** 1.15
        pose = phys(p_squat, lt, q=q)
    else:
        q = 0.0
        pose = blend(lambda t: p_squat(t, 0.0), p_flex, lt, T0 + REP * NREP, .62, 1.22)
    ex = 'focus' if lt < T0 + REP * NREP else ('determined' if lt < 4.55 else 'grin')
    lk = glance(lt, 1.0, 1.0, .9, -.2)
    hero(d, lt, hx - squat_feet_shift(q, hs), hs, pose, ex, cl(lt / .4), look=lk)

    # the one prop: the 20-minute ring
    rp = cl((lt - .95) / .40)
    if rp > 0:
        k = e_back(rp, 1.4)
        cx, cy = 760 + fl(lt, 2, 3.0), 760 + fl(lt, 5, 3.6)
        r = 150 * k
        fill = cl((lt - 1.30) / 2.10)
        ring(d, cx, cy, r, fill, acc, int(22 * k))
        if rp > .6:
            n = int(round(20 * e_out(fill, 1.4)))
            d.text((cx, cy - 16), str(n), font=F(int(96 * k), 800), fill=INK, anchor='mm')
            d.text((cx, cy + 56), 'MIN', font=F(int(34 * k), 700), fill=acc, anchor='mm')
    payoff(d, ['JISM', '=', 'DIMAGH'], cl((lt - 3.65) / .55), acc, {2}, 80)


# ───────────────────────────────────────────── 3  DIMAGH   (6.986 s, VO at 0.05)
#   0.09 "Dusri aadat"  1.09 "roz das page padho"  2.71 "Saal ke"
#   3.41 "teen hazaar page"  4.79 "Jaanne wala hi kamra chalata hai"
def s3(d, lt, acc):
    line(d, ['10', 'PAGE', 'ROZ'], W / 2, 348, 118, 800, INK, {0}, acc, cl(lt / .55), 42)
    pose = blend(T.p_idle, p_read, lt, 0.35, .6, 1.08)
    ex = 'neutral' if lt < .6 else 'focus'
    j = hero(d, lt, 290, 480, pose, ex, cl(lt / .4))
    if j is not None and lt > .55:
        fp = ((lt - 1.1) / .55) % 1.0 if lt > 1.1 else 0.0
        book(d, j['hand_l'], j['hand_r'], acc, fp if fp < .55 else 0.0)

    # the one prop: a stack of ten books growing (one per day), then the count
    for i in range(10):
        p = cl((lt - 1.15 - i * .13) / .40)
        if p <= 0: continue
        k = e_back(p, 1.5)
        bx = 760 + ((i % 3) - 1) * 9 + fl(lt, i, 1.6, .9)
        by = 1000 - i * 36
        hw, hh = 128 * k, 15
        col = acc if i % 3 == 0 else (PAPER_D if i % 3 == 1 else (214, 206, 190))
        fbox(d, bx - hw, by - hh, bx + hw, by + hh, 6, col, 5)
        if p > .8:
            d.line([(bx - hw + 22, by), (bx + hw - 22, by)],
                   fill=INK if col != acc else PAPER, width=3)
    lb = cl((lt - 2.75) / .4)
    if lb > 0:
        d.text((760, 1058), 'x 365 DIN', font=F(34, 700), fill=SOFT, anchor='mm')
    hp = cl((lt - 3.40) / .4)
    if hp > 0:
        n = int(3650 * e_out(cl((lt - 3.40) / 1.25), 1.6))
        line(d, [f'{n:,}', 'PAGE', '/', 'SAAL'], W / 2, PAY_Y, 84, 800, INK, {0}, acc, hp, 28)


# ───────────────────────────────────────────── 4  CONTROL   (6.720 s, VO at 0.05)
#   0.09 "Teesri aadat"  1.02 "self-control"  2.10 "Gussa aaye"
#   2.97 "das second chup"  3.97 "Jo khud ko jeete"  5.20 "woh sab jeet leta hai"
def s4(d, lt, acc):
    line(d, ['SELF', 'CONTROL'], W / 2, 348, 118, 800, INK, {1}, acc, cl(lt / .55), 42)
    hx = 330
    if lt < 2.10:
        pose = phys(T.p_idle, lt)
        ex = 'neutral'
    elif lt < 2.62:
        pose = blend(T.p_idle, p_flinch, lt, 2.10, .22, 1.35)
        ex = 'shock'
    else:
        pose = blend(p_flinch, p_calm, lt, 2.62, .75, 1.04)
        ex = 'shock' if lt < 2.80 else ('calm' if lt < 5.05 else ('calm_smile' if lt < 5.45 else 'determined'))
    lk = glance(lt, 2.12, .5, 1.0, -.4)
    hero(d, lt, hx, 500, pose, ex, cl(lt / .4), look=lk)

    # the trigger: a red burst "!!!" that cracks in, then dissolves as he breathes
    tp = cl((lt - 2.08) / .18)
    if tp > 0:
        fade = 1 - cl((lt - 2.75) / .55)
        if fade > 0:
            k = e_back(tp, 1.9)
            cx, cy = 720, 690
            pts = []
            for i in range(16):
                a = i * math.pi / 8 + lt * .4
                r = (142 if i % 2 == 0 else 96) * k
                pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * .86))
            d.polygon(pts, fill=RED + (int(255 * fade),), outline=INK + (int(255 * fade),), width=6)
            d.text((cx, cy + 4), '!!!', font=F(int(92 * k), 800),
                   fill=(255, 255, 255, int(255 * fade)), anchor='mm')
    # the one motion graphic: a 10-second ring draining to zero
    rp = cl((lt - 2.90) / .4)
    if rp > 0:
        k = e_back(rp, 1.4)
        cx, cy = 740 + fl(lt, 2, 2.6), 800 + fl(lt, 5, 3.0)
        drain = cl((lt - 3.10) / 1.85)
        ring(d, cx, cy, 150 * k, 1 - drain, acc, int(22 * k))
        if rp > .6:
            n = int(math.ceil(10 * (1 - drain) - 1e-6))
            d.text((cx, cy - 16), str(n), font=F(int(96 * k), 800), fill=INK, anchor='mm')
            d.text((cx, cy + 56), 'SECOND', font=F(int(30 * k), 700), fill=acc, anchor='mm')
            if drain >= 1:
                tickmark(d, cx + 118 * k, cy - 112 * k, 26, acc, cl((lt - 4.95) / .35), 11)
    payoff(d, ['KHUD', 'KO', 'JEETO'], cl((lt - 5.15) / .55), acc, {2})


# ───────────────────────────────────────────── 5  VALUE   (7.016 s, VO at 0.05)
#   0.09 "Chauthi aadat"  1.03 "apni value banao"  2.44 "Ek skill"  3.29 "roz behtar"
#   4.26 "Powerful aadmi mangta nahi"  5.99 "deta hai"
def s5(d, lt, acc):
    line(d, ['VALUE', 'BANAO'], W / 2, 348, 118, 800, INK, {0}, acc, cl(lt / .55), 42)
    pose = blend(T.p_idle, T.p_present, lt, 0.95, .6, 1.10) if lt < 4.2 \
        else blend(T.p_present, lambda t: T.p_point(t, up=False, right=True), lt, 4.25, .55, 1.12)
    if lt > 5.95:
        pose = blend(lambda t: T.p_point(t, up=False, right=True), T.p_hold, lt, 5.95, .5, 1.1)
    ex = 'neutral' if lt < 1.0 else ('talk' if lt < 4.2 else ('determined' if lt < 5.95 else 'happy'))
    lk = glance(lt, 1.15, 1.3, .9, -.2) if lt < 4 else glance(lt, 4.3, 1.6, .9, .0)
    hero(d, lt, 262, 470, pose, ex, cl(lt / .4), look=lk)

    # the one prop: a balance — MANGO on the left pan, DO on the right; DO wins
    sp = cl((lt - 1.00) / .5)
    if sp > 0:
        k = e_back(sp, 1.3)
        cx, cy = 736 + fl(lt, 1, 2.4), 980 + fl(lt, 4, 2.0)
        tilt = -math.radians(13) * e_io(cl((lt - 4.40) / 1.30))
        # post + base
        fbox(d, cx - 70 * k, cy - 6, cx + 70 * k, cy + 10, 6, PAPER_D, 6)
        fbox(d, cx - 11, cy - 300 * k, cx + 11, cy, 6, PAPER_D, 6)
        bl = 230 * k
        c_, s_ = math.cos(tilt), math.sin(tilt)
        top = (cx, cy - 300 * k)
        pl = (top[0] - bl * c_, top[1] - bl * s_)
        pr = (top[0] + bl * c_, top[1] + bl * s_)
        stroke(d, [pl, pr], INK, 12)
        fcirc(d, top[0], top[1], 16, acc, 5)
        for (px, py), label, col, win in ((pl, 'MANGO', PAPER, False), (pr, 'DO', acc, True)):
            drop = 70 if not win else 70
            d.line([(px, py), (px - 58, py + drop)], fill=INK, width=5)
            d.line([(px, py), (px + 58, py + drop)], fill=INK, width=5)
            fbox(d, px - 92, py + drop, px + 92, py + drop + 54, 14, col, 6)
            d.text((px, py + drop + 27), label, font=F(32, 800),
                   fill=INK if not win else (255, 255, 255), anchor='mm')
            if win:
                tickmark(d, px + 70, py + drop - 34, 22, acc, cl((lt - 5.95) / .35), 10)
            else:
                cross(d, px - 70, py + drop - 34, 20, RED, cl((lt - 4.30) / .35), 10)
    # "+1" badges — one skill, a little better every day — rise from the hand
    for i in range(3):
        bp = (lt - 2.45 - i * .50) / 1.10
        if 0 < bp < 1:
            k = e_out(bp, 2.0)
            bx = 372 + i * 22 + math.sin(bp * 6 + i) * 8
            by = 780 - k * 230
            a = int(255 * (1 - cl((bp - .70) / .30)))
            d.rounded_rectangle([bx - 46, by - 26, bx + 46, by + 26], 26, fill=acc + (a,))
            d.text((bx, by + 1), '+1', font=F(30, 800), fill=(255, 255, 255, a), anchor='mm')
    payoff(d, ['MANGTA', 'NAHI,', 'DETA', 'HAI'], cl((lt - 5.90) / .55), acc, {2}, 76)


# ───────────────────────────────────────────── 6  GO   (8.916 s, VO at 0.05)
#   0.09 Jism  0.98 dimagh  1.84 control  2.82 value  3.52 "bas chaar"
#   4.21 "Aaj se"  4.77 "shuru"  5.60 "Follow karo part two ke liye"  6.92 "aur save karna mat bhoolna"
def s6(d, lt, acc):
    line(d, ['AAJ', 'SE', 'SHURU'], W / 2, 330, 120, 800, INK, {2}, acc, cl(lt / .42), 46)
    line(d, ['KARO'], W / 2, 454, 120, 800, acc, None, acc, cl((lt - .18) / .42), 46)

    for i, (nm, st) in enumerate((('JISM', .09), ('DIMAGH', .98), ('CONTROL', 1.84), ('VALUE', 2.82))):
        p = cl((lt - st) / .4)
        if p <= 0: continue
        x = 170 + i * 247
        yv = 596 + fl(lt, i, 5.2)
        tickmark(d, x, yv, 28, acc, cl(p * 1.8), 11)
        d.text((x, yv + 86), nm, font=F(34, 700), fill=INK, anchor='mm')

    # power stance through the recap, cheer on "shuru", then the pill lands
    if lt < 4.70:
        pose = phys(p_power, lt)
        bob = 0.0
    else:
        pose = blend(p_power, T.p_cheer, lt, 4.70, .55, 1.25)
        bob = abs(math.sin(lt * 4.6)) * 26 * e_out(cl((lt - 4.70) / .6), 2)
    ex = 'proud' if lt < 4.70 else 'grin'
    hero(d, lt, W / 2, 445, pose, ex, cl(lt / .3), bob=bob)

    # confetti: 26 pieces, 3 shapes, per-piece 3D tumble (v9 recipe)
    cp = cl((lt - 5.40) / 2.9)
    if 0 < cp < 1:
        fade = 1 - cl((cp - .74) / .26)
        for i in range(26):
            a = (i * 0.2417) % 6.283
            r = (250 + (i % 7) * 104) * e_out(cp, 2.0)
            x = W / 2 + math.cos(a) * r * 1.12
            y = PAY_Y - 180 - math.sin(a) * r * .80 + cp * cp * 190
            sp = 1.0 + (i % 3) * .55
            tum = lt * (3.1 + (i % 5) * .9) + i
            sq = abs(math.cos(tum))
            col = acc if i % 3 else (INK if i % 6 == 1 else ACC[4])
            al = int(236 * fade)
            w0 = (13 + (i % 4) * 5) * sp
            h0 = w0 * (0.34 + 0.66 * sq)
            if i % 7 == 3:
                d.ellipse([x - w0 * .5, y - h0 * .5, x + w0 * .5, y + h0 * .5], fill=col + (al,))
            elif i % 7 == 5:
                d.line([(x - w0, y - h0 * 1.5), (x + w0 * .5, y + h0 * 1.5)],
                       fill=col + (int(al * .55),), width=max(2, int(h0 * .5)))
            else:
                th = tum * .7
                c_, s_ = math.cos(th), math.sin(th)
                pts = [(x + (dxx * c_ - dyy * s_), y + (dxx * s_ + dyy * c_) * (0.3 + 0.7 * sq))
                       for dxx, dyy in ((-w0 * .5, -h0 * .5), (w0 * .5, -h0 * .5),
                                        (w0 * .5, h0 * .5), (-w0 * .5, h0 * .5))]
                d.polygon(pts, fill=col + (al,))
    # follow pill (drawn AFTER the confetti so the copy is never covered)
    fp = cl((lt - 5.55) / .5)
    if fp > 0:
        k = e_back(fp, 1.12)
        wdt = 348 * k
        fbox(d, W / 2 - wdt, PAY_Y - 58 * k, W / 2 + wdt, PAY_Y + 58 * k, 58, acc, 7)
        if fp > .5:
            sh = ((lt - 6.05) * 0.62) % 1.6
            if 0 <= sh <= 1.0:
                sx = W / 2 - wdt + sh * wdt * 2
                for q in range(-30, 31, 6):
                    aq = int(46 * (1 - abs(q) / 32))
                    d.line([(sx + q, PAY_Y - 54), (sx + q - 26, PAY_Y + 54)],
                           fill=(255, 255, 255, aq), width=8)
            d.text((W / 2, PAY_Y + 2), 'FOLLOW FOR PART 2', font=F(42, 800),
                   fill=(255, 255, 255), anchor='mm')
    # bookmark — "save karna mat bhoolna"
    bp = cl((lt - 6.90) / .45)
    if bp > 0:
        k = e_back(bp, 1.6)
        bx, by = W / 2 + 348 + 70, PAY_Y + fl(lt, 7, 3.0)
        pul = 1 + .05 * math.sin((lt - 6.9) * 9) * (1 - cl((lt - 7.9) / .6))
        hw, hh = 30 * k * pul, 44 * k * pul
        pts = [(bx - hw, by - hh), (bx + hw, by - hh), (bx + hw, by + hh),
               (bx, by + hh * .45), (bx - hw, by + hh)]
        fpoly(d, pts, acc, 6)


SCENES = [s1, s2, s3, s4, s5, s6]
CAPS = [
    [(0.40, 1.75, 'POWERFUL MAN BANNA HAI?', {0}), (1.85, 3.30, 'TAQAT MUSCLES SE NAHI', {1}),
     (3.40, 4.50, 'AADATON SE AATI HAI', {0}), (4.60, 6.20, 'YEH CHAAR AADATEIN PAKDO', {1})],
    [(0.15, 0.95, 'PEHLI AADAT', {0}), (1.00, 3.55, 'ROZ SUBAH 20 MINUTE JISM KO TAPAO', {2}),
     (3.65, 5.80, 'JISM MAZBOOT TOH DIMAGH MAZBOOT', {3})],
    [(0.15, 1.05, 'DUSRI AADAT', {0}), (1.10, 2.65, 'ROZ 10 PAGE PADHO', {1}),
     (2.75, 4.70, 'SAAL KE 3650 PAGE', {2}), (4.80, 6.80, 'JAANNE WALA HI KAMRA CHALATA HAI', {0})],
    [(0.15, 0.98, 'TEESRI AADAT', {0}), (1.05, 2.05, 'SELF CONTROL', {1}),
     (2.12, 3.90, 'GUSSA AAYE? 10 SECOND CHUP', {2}), (4.00, 6.50, 'JO KHUD KO JEETE WOH SAB JEET LETA HAI', {3})],
    [(0.15, 0.98, 'CHAUTHI AADAT', {0}), (1.05, 2.40, 'APNI VALUE BANAO', {1}),
     (2.48, 4.20, 'EK SKILL ROZ BEHTAR', {1}), (4.30, 6.80, 'POWERFUL AADMI MANGTA NAHI DETA HAI', {4})],
    [(0.15, 3.45, 'JISM DIMAGH CONTROL VALUE', {0}), (3.55, 5.45, 'BAS CHAAR AAJ SE SHURU', {1})],
]


CAP_MAX_W = W - 2 * 72                      # caption safe width (72 px side margins)
CAP_Y_P = 1440                              # v9 1452; measured under this camera the glyph bottom (+25) reached Y 1523 -> 1497 now


def caption_fit(d, words, p, acc, hot=None, y=CAP_Y_P):
    """clean.caption with a measured fit: five of this film's captions mirror
    full VO sentences and run 1028-1162 px at the v9 size 50 (frame 1080).
    The size is scaled so the line sits inside CAP_MAX_W, floor 40 px."""
    if p <= 0:
        return
    f = F(50, 600)
    wdt = sum(f.getlength(w) for w in words) + f.getlength(' ') * (len(words) - 1)
    sz = 50 if wdt <= CAP_MAX_W else max(40, int(50 * CAP_MAX_W / wdt))
    fade = 1 - cl((p - .90) / .10)
    line(d, words, W / 2, y, sz, 600, (88, 82, 74), hot, acc, cl(p * 1.9) * fade, 16)


def scene_img(si, lt):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, 'RGBA')
    SCENES[si](d, lt, ACC[si])
    for t0, t1, txt, hot in CAPS[si]:
        if t0 <= lt < t1:
            caption_fit(d, txt.split(), (lt - t0) / (t1 - t0), ACC[si], hot)
            break
    return im


# ───────────────────────────────────────────── camera (ledger 32/33 rig, vertical)
Z0 = 1.020                                  # zoom floor: 10 px x / 19 px y of pan headroom (pans are 7 / 9)
AMP = (.020, .024, .016, .024, .020, .024)   # measured: z_max 1.044 keeps the caption bottom at Y<=1497 (safe line 1500)


def _tri(x):
    return 4 * abs(x - math.floor(x + .5)) - 1


def camera(t, si, lt, dur):
    u = cl(lt / dur)
    ramp = .15 * e_io(u) + .85 * u          # linear-dominant: velocity never reaches zero
    if si % 2: ramp = 1.0 - ramp            # odd scenes pull back, even push in
    z = Z0 + AMP[si] * ramp + math.exp(-lt * 6.4) * math.sin(lt * 16.5) * .0040
    px = 7.0 * _tri(t / 9.0)                # constant-speed triangle pans, never a sine apex
    py = 9.0 * _tri(t / 13.0 + .37)
    return z, px, py


def render(i):
    t = i / FPS
    si = max(k for k in range(6) if t >= SCENE_START[k])
    lt = t - SCENE_START[si]

    tp, tk = None, si
    for k, c in enumerate(CUTS):
        cc = c + TLAG
        if cc - TDUR / 2 <= t < cc + TDUR / 2:
            tp = (t - cc + TDUR / 2) / TDUR
            tk = k
            break
    show = si if tp is None else (tk if tp < .5 else tk + 1)
    slt = t - SCENE_START[show]
    if tp is not None and tp < .5:
        slt = SCENE_END[tk] - SCENE_START[tk] - .001
    acc = ACC[show]

    cv = backdrop(t, show, acc).convert('RGBA')
    cv.alpha_composite(scene_img(show, slt))
    d = ImageDraw.Draw(cv, 'RGBA')
    chrome(d, t, show, acc)

    if tp is not None:                      # tinted swipe, one transition type (v9)
        nacc = ACC[tk + 1]
        tint = tuple(int(nacc[q] * .18 + PAPER[q] * .82) for q in range(3))
        glow = tuple(int(nacc[q] * .40 + PAPER[q] * .60) for q in range(3))
        e = e_io(tp)
        top = H - 2 * H * e
        d.rectangle([0, top + H * .044, W, top + H], fill=tint)
        d.rectangle([0, top + H * .026, W, top + H * .044], fill=glow)
        d.rectangle([0, top + H * .007, W, top + H * .026], fill=nacc)
        d.rectangle([0, top, W, top + H * .007], fill=INK)

    frame = cv.convert('RGB')
    dur = SCENE_END[si] - SCENE_START[si]
    z, px, py = camera(t, si, lt, dur)
    iz = 1.0 / z
    ox = (W - W * iz) * .5 + px
    oy = (H - H * iz) * .5 + py
    # ledger 32: the sampled rectangle must never leave the source
    assert ox >= 0 and ox + W * iz <= W and oy >= 0 and oy + H * iz <= H, (i, z, px, py)
    frame = frame.transform((W, H), Image.AFFINE, (iz, 0, ox, 0, iz, oy), Image.BICUBIC)
    arr = np.asarray(frame).astype(np.float32) + C._GRAIN
    return np.clip(arr, 0, 255).astype(np.uint8)


def shard(a, b, path):
    import imageio_ffmpeg, time
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs('/home/user/build', exist_ok=True)
    p = subprocess.Popen([ff, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'faster',
                          '-crf', '16', '-pix_fmt', 'yuv420p', '-g', '30', path],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    for i in range(a, b):
        p.stdin.write(render(i).tobytes())
        k = i - a + 1
        if k % 50 == 0:
            el = time.time() - t0
            print(f'[{a}:{b}] {k}/{b-a} {el:.0f}s eta {el/k*(b-a-k):.0f}s', flush=True)
    p.stdin.close(); p.wait()
    print(f'[{a}:{b}] DONE', flush=True)


if __name__ == '__main__':
    if len(sys.argv) == 4:
        shard(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
    elif len(sys.argv) == 3 and sys.argv[1] == 'still':
        # python3 src/power.py still <t>  -> build/still_<t>.png
        tt = float(sys.argv[2])
        Image.fromarray(render(int(round(tt * FPS)))).save(f'/home/user/build/still_{tt:.2f}.png')
        print('ok')
