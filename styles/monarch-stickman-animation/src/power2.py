"""
power2.py — "POWERFUL MAN KAISE BANE" · SHADE remake · 42 s · 1080x1920 · 30 fps
==================================================================================
Same film as power.py (same script, same fitted VO, same timeline, same camera
rig, same caption contract, same ASMR bed and mux) with three things replaced:

  * HERO  — the stickman is replaced by SHADE (src/shade.py): the hooded black
            suit on the toon 3D rig.  Every pose generator of power.py/toon.py
            is reused unchanged (blend/mix, squat cycle, flex, power stance,
            reading, calm, flinch, present, point, cheer) — only hero() differs.
  * LOOK  — the hybrid backdrop (src/hybrid.py): paper/ink engine below, a
            charcoal wedge above the character's diagonal.  Chrome + headlines
            sit on the dark in paper-coloured extruded type; props, payoff and
            captions stay ink-on-paper BELOW the line (asserted every frame,
            >= 40 px under the live wedge).
  * BEATS — the diagonal is a character, not a frame:
            S1  the frame opens almost all dark; the eyes light up first, then
                the smirk, then "the light arrives" (the wedge lifts 400 px) on
                "Powerful man banna hai?"; on "muscles se nahi" he shakes his
                head at the dumbbell before the habits tick in
            S2  a paper-toned sun rises out of the seam on "roz subah"; the
                eyes flare on the flex
            S3  the eyes brighten with every page counted; on "kamra chalata
                hai" he lifts his chin from the book to the lens
            S4  "Gussa aaye": the eyes flash RED and the dark SURGES down over
                him; he closes his eyes and the dark recedes as the 10-second
                ring drains — control = the dark pulling back
            S5  the "+1" badges rise from the paper into the dark
            S6  the four habits switch on as glowing ticks inside his dark;
                on "shuru" the dark flinches back once and the eyes flare
Transitions: the v9 tinted swipe, now slanted parallel to the seam and
two-toned (paper tint over paper, charcoal tint over the wedge) so the luma
step per frame stays where v1 measured it (gate max_dluma < 8).
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, '/home/user/src')
import toon as T
import clean as C
import shade as S
import hybrid as HY
import power as PW
from clean import (W, H, FPS, PAPER, PAPER_D, SOFT, INK, ACC, ACC_HI, GY, PAY_Y,
                   cl, fl, e_out, e_io, e_back, F, tw, line, fbox, fcirc, fpoly, stroke,
                   tickmark, shadow, caption, payoff, phys)
from power import (mix, blend, p_power, p_flex, p_squat, p_read, p_calm, p_flinch, glance,
                   ring, cross, book, CAPS, caption_fit, camera, NF, CUTS, TDUR, TLAG, CHAPTER, RED)
from timeline_power import SCENE_START, SCENE_END, DUR_TOTAL, VO_AT, NAMES

DARK, DARK_L, POD = HY.DARK, HY.DARK_L, HY.PAPER_ON_DARK
MARGIN = 40                                  # ink-on-paper elements stay this far under the wedge
OUT_DEFAULT = '/home/user/shade_power_42s.mp4'


# ───────────────────────────────────────────── the diagonal as a character
def scene_at(t):
    si = max(k for k in range(6) if t >= SCENE_START[k])
    return si, t - SCENE_START[si]


def wedge_drop(t):
    """Scene-driven vertical offset of the whole split (positive = more dark)."""
    si, lt = scene_at(t)
    if si == 0:      # the light arrives: 400 px of extra dark lifts on "Powerful man banna hai?"
        return 400.0 * (1 - e_io(cl((lt - .50) / .85)))
    if si == 3:      # anger: the dark surges down over him, then recedes as he counts 10 -> 0
        return 260.0 * e_out(cl((lt - 2.08) / .36), 2.0) * (1 - e_io(cl((lt - 2.85) / 2.25)))
    if si == 5:      # "shuru": the dark flinches back once
        u = cl((lt - 4.74) / .60)
        return -44.0 * math.sin(math.pi * u)
    return 0.0


_wedge_ends0 = HY.wedge_ends                 # the resting drift (±28 / ±22 px, two slow periods)


def wedge_ends(t):
    yl, yr = _wedge_ends0(t)
    dr = wedge_drop(t)
    return yl + dr, yr + dr


HY.wedge_ends = wedge_ends                   # hybrid.wedge_y() now follows the scene offsets too


def wedge_y(x, t):
    yl, yr = wedge_ends(t)
    return yl + (yr - yl) * (x / W)


def on_paper(x, ytop, t, what):
    """Build-time contract: an ink-on-paper element's top edge at x must sit
    >= MARGIN px under the live wedge."""
    wy = wedge_y(x, t)
    assert ytop >= wy + MARGIN, (what, round(x), round(ytop), round(wy, 1), round(t, 3))


# ───────────────────────────────────────────── backdrop (hybrid, cached sheets)
_SHEET = {}
_LIFT = None


def _sheet(si, acc):
    """The static part of the dark half for a scene: charcoal + top-left lift +
    a whisper of the scene accent.  Masked by the live wedge every frame."""
    global _LIFT
    if si in _SHEET:
        return _SHEET[si]
    if _LIFT is None:
        g = Image.new('L', (W // 8, H // 8), 0)
        ImageDraw.Draw(g).ellipse([-W // 16, -H // 16, W // 10, H // 10], fill=255)
        _LIFT = g.filter(ImageFilter.GaussianBlur(28)).resize((W, H), Image.BILINEAR).point(lambda v: int(v * .55))
    lay = Image.new('RGBA', (W, H), DARK + (255,))
    lay.paste(Image.new('RGBA', (W, H), DARK_L + (255,)), (0, 0), _LIFT)
    ab = Image.new('RGBA', (W // 4, H // 4), (0, 0, 0, 0))
    ImageDraw.Draw(ab).ellipse([W // 4 * .55 - 190, -120, W // 4 * .55 + 190, 260], fill=acc + (26,))
    lay.alpha_composite(ab.filter(ImageFilter.GaussianBlur(40)).resize((W, H), Image.BILINEAR))
    _SHEET[si] = lay
    return lay


def backdrop(t, si, acc):
    bg = C.backdrop(t, si, acc).convert('RGBA')
    yl, yr = wedge_ends(t)
    lay = _sheet(si, acc).copy()
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).polygon([(0, 0), (W, 0), (W, yr), (0, yl)], fill=255)
    lay.putalpha(mask)
    bg.alpha_composite(lay)
    # the seam: a soft accent glow (quarter-res blur) and a hairline
    sd = Image.new('RGBA', (W // 4, H // 4), (0, 0, 0, 0))
    ImageDraw.Draw(sd).line([(0, yl / 4), (W / 4, yr / 4)], fill=acc + (120,), width=4)
    bg.alpha_composite(sd.filter(ImageFilter.GaussianBlur(2.4)).resize((W, H), Image.BILINEAR))
    ImageDraw.Draw(bg, 'RGBA').line([(0, yl), (W, yr)], fill=acc + (235,), width=4)
    return bg


# ───────────────────────────────────────────── hero = SHADE on the toon rig
RED_EYES = dict(GLOW=(255, 122, 96), GLOW_T=(255, 64, 40), GLOW_C=(255, 170, 150))


def hero(d, lt, x, s, pose, expr, p=1.0, flip=False, bob=0.0, look=(0, 0), glow=1.0,
         blink=None, eyes=None):
    """power.hero with SHADE: same contact shadows, same pop-in, same joint
    dict; plus face glow level, an explicit blink (eye opening) and an eye
    tint override (the red flash in S4)."""
    if p <= 0:
        return None
    sc = s * (0.90 + 0.10 * e_back(cl(p * 1.6), 1.6))
    lift = bob + pose.get('_bob', 0.0) * sc
    shadow(d, x, GY + 8, sc * .165, 66, lift)
    shadow(d, x, GY + 5, sc * .070, 104, lift * 1.5)
    bl = T.blink_at(lt) if blink is None else blink
    keep = None
    if eyes:
        keep = {k: getattr(S, k) for k in eyes}
        for k, v in eyes.items():
            setattr(S, k, v)
    try:
        j = S.shade(d, x, GY - lift, sc, pose, expr, look=look, blink=bl, flip=flip, glow=glow)
    finally:
        if keep:
            for k, v in keep.items():
                setattr(S, k, v)
    return j


def squat_shift(q, s):
    """power.squat_feet_shift with SHADE's leg lengths."""
    thigh, shin = math.radians(92 * q), math.radians(15 * q)
    z = S.SP['leg_u'] * math.sin(thigh) + S.SP['leg_l'] * math.sin(shin)
    return z * math.sin(math.radians(62)) * s


def p_read2(t):
    """power.p_read re-fitted to SHADE's smaller head: hands lower (less elbow
    fold), chin further down, so the open book sits under the face, never on it."""
    o = math.sin(t * .8)
    return dict(yaw=24, lean=3, twist=4, tilt=-2, pelvis=2, sway=0.008,
                head=18 + o * .8, head_t=4,
                al=-16, az_l=52, el=2, ef_l=14,
                ar=16, az_r=52, er=-2, ef_r=14,
                ll=-4, lz_l=0, kl=3, lr=5, lz_r=0, kr=4,
                hl='open', hr='open', _br=math.sin(t * 2.0))


def book2(d, hl, hr, acc, flip_p=0.0):
    """power.book at SHADE scale: the panel width follows the hand spacing
    at .48 (+12) instead of .60 (+34), so the top edge clears the chin."""
    (x0, y0), (x1, y1) = hl, hr
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 - 4
    hw = max(60, abs(x1 - x0) * .48 + 12)
    hh = hw * .68
    lift = hh * .22
    cover = [(cx - hw - 8, cy - hh + 8 - lift), (cx, cy - hh + 22), (cx + hw + 8, cy - hh + 8 - lift),
             (cx + hw + 8, cy + hh * .40 - lift), (cx, cy + hh * .40 + 14), (cx - hw - 8, cy + hh * .40 - lift)]
    fpoly(d, cover, acc, 6)
    for sx in (-1, 1):
        page = [(cx + sx * 6, cy - hh + 24), (cx + sx * (hw - 2), cy - hh + 12 - lift),
                (cx + sx * (hw - 2), cy + hh * .40 - 6 - lift), (cx + sx * 6, cy + hh * .40 + 4)]
        d.polygon(page, fill=(252, 250, 244), outline=(196, 188, 172))
        for k in range(4):
            f = (k + 1) / 5.5
            ya = cy - hh + 24 + (hh * .40 + 4 - (-hh + 24)) * f
            yb = cy - hh + 12 - lift + (hh * .40 - 6 - lift - (-hh + 12 - lift)) * f
            d.line([(cx + sx * 16, ya), (cx + sx * (hw - 18), yb)], fill=(206, 198, 182), width=3)
    d.line([(cx, cy - hh + 22), (cx, cy + hh * .40 + 14)], fill=(176, 168, 152), width=4)
    if 0 < flip_p < 1:
        a = math.pi * flip_p
        px = cx + math.cos(a) * (hw - 10)
        top = cy - hh + 14 - lift * abs(math.cos(a)) - math.sin(a) * 34
        d.polygon([(cx, cy - hh + 22), (px, top), (px, cy + hh * .40 - 4 - lift * abs(math.cos(a)) - math.sin(a) * 14),
                   (cx, cy + hh * .40 + 10)], fill=(255, 253, 248), outline=(190, 182, 166))


def p_read_up(t):
    """The reading pose with the chin lifted to the lens (end of S3)."""
    o = math.sin(t * .8)
    return dict(yaw=18, lean=0, twist=3, tilt=-1, pelvis=2, sway=0.008,
                head=-5 + o * .6, head_t=-6,
                al=-16, az_l=48, el=2, ef_l=10,
                ar=16, az_r=48, er=-2, ef_r=10,
                ll=-4, lz_l=0, kl=3, lr=5, lz_r=0, kr=4,
                hl='open', hr='open', _br=math.sin(t * 2.0))


def pulse(lt, t0, d=.5):
    """0 -> 1 -> 0 hump of length d starting at t0 (eye flares)."""
    u = (lt - t0) / d
    return math.sin(math.pi * u) if 0 < u < 1 else 0.0


# ───────────────────────────────────────────── props that live ON the dark
def sunrise(d, t, x, p, acc, r=66):
    """A paper-toned disc rising out of the paper into the dark, clipped to the
    seam (S2 "roz subah").  Built in the seam's frame so the clip is exact."""
    if p <= 0:
        return
    yl, yr = wedge_ends(t)
    th = math.atan2(yr - yl, W)
    e1 = (math.cos(th), math.sin(th))                 # along the seam
    e2 = (e1[1], -e1[0])                              # toward the dark side (screen up-left)
    foot = (x, yl + (yr - yl) * x / W)
    k = e_out(p, 2.2)
    h = r * 1.05 - (r * 1.05 + r * .58) * k           # centre distance below the line

    def cap(rr, col):
        if h >= rr - 3:
            return
        f0 = math.asin(max(-1.0, min(1.0, (3 + h) / rr)))
        pts = []
        for i in range(29):
            f = f0 + (math.pi - 2 * f0) * i / 28
            u, v = rr * math.cos(f), -h + rr * math.sin(f)
            pts.append((foot[0] + u * e1[0] + v * e2[0], foot[1] + u * e1[1] + v * e2[1]))
        d.polygon(pts, fill=col)

    for rr, aa in ((r * 1.9, 14), (r * 1.5, 18), (r * 1.22, 24)):
        cap(rr, acc + (aa,))
    cap(r, POD + (250,))


def glow_tick(d, x, y, p, flare, acc):
    """A habit switching on inside the dark: soft halo + glowing tick."""
    if p <= 0:
        return
    for rr, aa in ((60, 16), (44, 24), (28, 34)):
        a = int((aa + 60 * flare) * cl(p * 2))
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=S.GLOW_T + (a,))
    tickmark(d, x, y, 22, S.GLOW, cl(p * 1.8), 9)


# ───────────────────────────────────────────── 1  HOOK   (6.376 s, VO at 0.30)
#   0.34 "Powerful man banna hai?"   1.80 "Taqat muscles se nahi"
#   3.36 "aadaton se aati hai"       4.59 "Yeh chaar aadatein pakdo"
def s1(d, lt, acc, t):
    HY.headline(d, ['POWERFUL'], W / 2, 318, 124, {0}, 0, cl((lt - .30) / .60), 46)
    HY.headline(d, ['BANNA', 'HAI?'], W / 2, 436, 96, None, 0, cl((lt - .50) / .60), 42)
    hx, hs = 470, 580
    # eyes open in the dark (0.10-0.45), smirk at 0.55, the light arrives 0.50-1.35 (wedge_drop);
    # "muscles se nahi": a slow head-shake at the dumbbell; 3.30: pocket stance -> power stance
    if lt < 3.30:
        pose = dict(phys(S.p_pocket, lt))
        if 1.78 < lt < 2.78:
            u = (lt - 1.78) / 1.0
            sw = math.sin(u * math.pi * 2) * (1 - .35 * u)
            pose['yaw'] = pose['yaw'] + 8 * sw
            pose['head_t'] = pose.get('head_t', 0) + 7 * sw
    else:
        pose = blend(S.p_pocket, p_power, lt, 3.30, .70, 1.16)
    eyes_open = e_out(cl((lt - .10) / .35), 2.0)
    blink = (1 - eyes_open) if lt < .60 else None
    ex = 'neutral' if lt < .55 else ('sly' if lt < 1.80 else ('determined' if lt < 3.42 else 'proud'))
    glow = .30 + .70 * eyes_open + .35 * pulse(lt, 3.36, .7) + .25 * pulse(lt, 4.60, .6)
    lk = glance(lt, 1.85, 1.1, .9, .25) if lt < 3.3 else glance(lt, 3.45, 1.2, .9, .3)
    hero(d, lt, hx, hs, pose, ex, look=lk, glow=glow, blink=blink)

    # the one prop cluster: dumbbell (crossed) -> four habit boxes (ticked) — on the paper
    dp = cl((lt - 1.80) / .45)
    if dp > 0:
        k = e_back(dp, 1.6)
        bx, by = 870 + fl(lt, 1, 3.2), 870 + fl(lt, 3, 4.0)
        on_paper(bx - 176 * k, by - 58, t, 's1 dumbbell')
        stroke(d, [(bx - 92 * k, by), (bx + 92 * k, by)], INK, 14)
        for sx in (-1, 1):
            fbox(d, bx + sx * 112 * k - 34, by - 58, bx + sx * 112 * k + 34, by + 58, 10, PAPER_D, 6)
            fbox(d, bx + sx * 158 * k - 18, by - 40, bx + sx * 158 * k + 18, by + 40, 8, PAPER_D, 6)
        cross(d, bx, by, 96, RED, cl((lt - 2.55) / .34), 14)
    hp = cl((lt - 3.40) / .5)
    if hp > 0:
        for i in range(4):
            q = cl((hp * 1.5 - i * .14) / .6)
            if q <= 0:
                continue
            k = e_back(q, 1.5)
            cx = 722 + i * 92 + fl(lt, i + 4, 2.2)
            cy = 1004 + fl(lt, i + 8, 3.0)
            hw = 36 * k
            on_paper(cx - hw, cy - hw, t, 's1 habit box')
            fbox(d, cx - hw, cy - hw, cx + hw, cy + hw, 10, PAPER, 6)
            tickmark(d, cx, cy, 20, acc, cl(q * 1.6 - .4), 9)
    payoff(d, ['4', 'AADATEIN'], cl((lt - 4.60) / .55), acc, {0})


# ───────────────────────────────────────────── 2  JISM   (5.986 s, VO at 0.05)
#   0.09 "Pehli aadat"  0.96 "roz subah bees minute jism ko tapao"
#   3.63 "Jism mazboot"  4.57 "toh dimagh mazboot"
def s2(d, lt, acc, t):
    HY.headline(d, ['JISM', 'TAPAO'], W / 2, 348, 118, {0}, 1, cl(lt / .55), 42)
    sunrise(d, t, 880, cl((lt - .96) / 1.5), acc)
    hx, hs = 340, 540
    REP, T0, NREP = 0.90, 0.75, 3
    if lt < T0:
        pose = blend(T.p_idle, lambda tt: p_squat(tt, 0.0), lt, 0.0, .4)
        q = 0.0
    elif lt < T0 + REP * NREP:
        ph = (lt - T0) / REP
        q = (0.5 - 0.5 * math.cos(2 * math.pi * ph)) ** 1.15
        pose = phys(p_squat, lt, q=q)
    else:
        q = 0.0
        pose = blend(lambda tt: p_squat(tt, 0.0), p_flex, lt, T0 + REP * NREP, .62, 1.22)
    tf = T0 + REP * NREP
    ex = 'focus' if lt < tf else ('determined' if lt < 4.55 else 'grin')
    glow = 1.0 + .35 * e_io(cl((lt - tf) / .6)) + .25 * pulse(lt, 4.57, .6)
    lk = glance(lt, 1.0, 1.0, .9, .1)
    hero(d, lt, hx - squat_shift(q, hs), hs, pose, ex, cl(lt / .4), look=lk, glow=glow)

    # the one prop: the 20-minute ring (self-contained paper disc)
    rp = cl((lt - .95) / .40)
    if rp > 0:
        k = e_back(rp, 1.4)
        cx, cy = 800 + fl(lt, 2, 3.0), 960 + fl(lt, 5, 3.6)
        r = 150 * k
        on_paper(cx - r, cy - r, t, 's2 ring')
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
def s3(d, lt, acc, t):
    HY.headline(d, ['10', 'PAGE', 'ROZ'], W / 2, 348, 118, {0}, 2, cl(lt / .55), 42)
    if lt < 4.75:
        pose = blend(T.p_idle, p_read2, lt, 0.35, .6, 1.08)
    else:
        pose = blend(p_read2, p_read_up, lt, 4.75, .55, 1.10)
    ex = 'neutral' if lt < .6 else ('focus' if lt < 4.85 else 'proud')
    cnt = e_out(cl((lt - 3.40) / 1.25), 1.6)
    glow = .95 + .35 * cnt + .25 * pulse(lt, 4.80, .7)
    lk = (0, .35) if .6 < lt < 4.75 else (0, .35 * (1 - e_io(cl((lt - 4.75) / .5))))
    j = hero(d, lt, 320, 520, pose, ex, cl(lt / .4), look=lk, glow=glow)
    if j is not None and lt > .55:
        fp = ((lt - 1.1) / .55) % 1.0 if lt > 1.1 else 0.0
        book2(d, j['hand_l'], j['hand_r'], acc, fp if fp < .55 else 0.0)

    # the one prop: a stack of ten books growing (one per day), then the count
    for i in range(10):
        p = cl((lt - 1.15 - i * .13) / .40)
        if p <= 0:
            continue
        k = e_back(p, 1.5)
        bx = 800 + ((i % 3) - 1) * 9 + fl(lt, i, 1.6, .9)
        by = 1110 - i * 32
        hw, hh = 128 * k, 15
        on_paper(bx - hw, by - hh, t, 's3 stack')
        col = acc if i % 3 == 0 else (PAPER_D if i % 3 == 1 else (214, 206, 190))
        fbox(d, bx - hw, by - hh, bx + hw, by + hh, 6, col, 5)
        if p > .8:
            d.line([(bx - hw + 22, by), (bx + hw - 22, by)],
                   fill=INK if col != acc else PAPER, width=3)
    lb = cl((lt - 2.75) / .4)
    if lb > 0:
        d.text((800, 1172), 'x 365 DIN', font=F(34, 700), fill=SOFT, anchor='mm')
    hp = cl((lt - 3.40) / .4)
    if hp > 0:
        n = int(3650 * cnt)
        line(d, [f'{n:,}', 'PAGE', '/', 'SAAL'], W / 2, PAY_Y, 84, 800, INK, {0}, acc, hp, 28)


# ───────────────────────────────────────────── 4  CONTROL   (6.720 s, VO at 0.05)
#   0.09 "Teesri aadat"  1.02 "self-control"  2.10 "Gussa aaye"
#   2.97 "das second chup"  3.97 "Jo khud ko jeete"  5.20 "woh sab jeet leta hai"
def s4(d, lt, acc, t):
    HY.headline(d, ['SELF', 'CONTROL'], W / 2, 348, 118, {1}, 3, cl(lt / .55), 42)
    hx, hs = 350, 540
    if lt < 2.10:
        pose = phys(T.p_idle, lt)
        ex = 'neutral'
    elif lt < 2.62:
        pose = blend(T.p_idle, p_flinch, lt, 2.10, .22, 1.35)
        ex = 'angry'
    else:
        pose = blend(p_flinch, p_calm, lt, 2.62, .75, 1.04)
        ex = 'angry' if lt < 2.80 else ('calm' if lt < 5.05 else ('calm_smile' if lt < 5.45 else 'determined'))
    # the red flash: eyes go red with the surge, fade back as the lids close
    rk = e_out(cl((lt - 2.08) / .14), 2.0) * (1 - cl((lt - 2.72) / .25))
    eyes = None
    if rk > 0:
        eyes = {k: tuple(int(S.__dict__[k][q] + (v[q] - S.__dict__[k][q]) * rk) for q in range(3))
                for k, v in RED_EYES.items()}
    glow = 1.0 + .5 * rk + .3 * pulse(lt, 5.45, .6)
    lk = glance(lt, 2.12, .5, 1.0, -.2)
    hero(d, lt, hx, hs, pose, ex, cl(lt / .4), look=lk, glow=glow, eyes=eyes)

    # the trigger: a red burst "!!!" cracks in (inside the surge), dissolves as he breathes
    tp = cl((lt - 2.08) / .18)
    if tp > 0:
        fade = 1 - cl((lt - 2.75) / .55)
        if fade > 0:
            k = e_back(tp, 1.9)
            cx, cy = 700, 830
            pts = []
            for i in range(16):
                a = i * math.pi / 8 + lt * .4
                r = (142 if i % 2 == 0 else 96) * k
                pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * .86))
            d.polygon(pts, fill=RED + (int(255 * fade),), outline=(255, 214, 200, int(230 * fade)), width=6)
            d.text((cx, cy + 4), '!!!', font=F(int(92 * k), 800),
                   fill=(255, 255, 255, int(255 * fade)), anchor='mm')
    # the one motion graphic: a 10-second ring draining to zero (paper disc, may sit in the surge)
    rp = cl((lt - 2.90) / .4)
    if rp > 0:
        k = e_back(rp, 1.4)
        cx, cy = 800 + fl(lt, 2, 2.6), 980 + fl(lt, 5, 3.0)
        drain = cl((lt - 3.10) / 1.85)
        ring(d, cx, cy, 150 * k, 1 - drain, acc, int(22 * k))
        if rp > .6:
            n = int(math.ceil(10 * (1 - drain) - 1e-6))
            d.text((cx, cy - 16), str(n), font=F(int(96 * k), 800), fill=INK, anchor='mm')
            d.text((cx, cy + 56), 'SECOND', font=F(int(30 * k), 700), fill=acc, anchor='mm')
            if drain >= 1:
                on_paper(cx + 118 * k - 26, cy - 112 * k - 26, t, 's4 tick')
                tickmark(d, cx + 118 * k, cy - 112 * k, 26, acc, cl((lt - 4.95) / .35), 11)
    payoff(d, ['KHUD', 'KO', 'JEETO'], cl((lt - 5.15) / .55), acc, {2})


# ───────────────────────────────────────────── 5  VALUE   (7.016 s, VO at 0.05)
#   0.09 "Chauthi aadat"  1.03 "apni value banao"  2.44 "Ek skill"  3.29 "roz behtar"
#   4.26 "Powerful aadmi mangta nahi"  5.99 "deta hai"
def s5(d, lt, acc, t):
    HY.headline(d, ['VALUE', 'BANAO'], W / 2, 348, 118, {0}, 4, cl(lt / .55), 42)
    hx, hs = 290, 510
    pose = blend(T.p_idle, T.p_present, lt, 0.95, .6, 1.10) if lt < 4.2 \
        else blend(T.p_present, lambda tt: T.p_point(tt, up=False, right=True), lt, 4.25, .55, 1.12)
    if lt > 5.95:
        pose = blend(lambda tt: T.p_point(tt, up=False, right=True), T.p_hold, lt, 5.95, .5, 1.1)
    ex = 'neutral' if lt < 1.0 else ('talk' if lt < 4.2 else ('determined' if lt < 5.95 else 'happy'))
    glow = 1.0 + .2 * sum(pulse(lt, 2.45 + i * .5, .5) for i in range(3)) + .3 * pulse(lt, 5.99, .7)
    lk = glance(lt, 1.15, 1.3, .9, .2) if lt < 4 else glance(lt, 4.3, 1.6, .9, .1)
    hero(d, lt, hx, hs, pose, ex, cl(lt / .4), look=lk, glow=glow)

    # the one prop: a balance — MANGO on the left pan, DO on the right; DO wins
    sp = cl((lt - 1.00) / .5)
    if sp > 0:
        k = e_back(sp, 1.3)
        cx, cy = 780 + fl(lt, 1, 2.4), 1140 + fl(lt, 4, 2.0)
        tilt = -math.radians(13) * e_io(cl((lt - 4.40) / 1.30))
        bl = 180 * k                                   # pans at x 600 / 960: clear of the pointing hand and of the zoomed right edge
        on_paper(cx - bl, cy - 300 * k - 16, t, 's5 balance')
        fbox(d, cx - 70 * k, cy - 6, cx + 70 * k, cy + 10, 6, PAPER_D, 6)
        fbox(d, cx - 11, cy - 300 * k, cx + 11, cy, 6, PAPER_D, 6)
        c_, s_ = math.cos(tilt), math.sin(tilt)
        top = (cx, cy - 300 * k)
        pl = (top[0] - bl * c_, top[1] - bl * s_)
        pr = (top[0] + bl * c_, top[1] + bl * s_)
        stroke(d, [pl, pr], INK, 12)
        fcirc(d, top[0], top[1], 16, acc, 5)
        for (px, py), label, col, win in ((pl, 'MANGO', PAPER, False), (pr, 'DO', acc, True)):
            drop = 70
            d.line([(px, py), (px - 52, py + drop)], fill=INK, width=5)
            d.line([(px, py), (px + 52, py + drop)], fill=INK, width=5)
            fbox(d, px - 80, py + drop, px + 80, py + drop + 54, 14, col, 6)
            d.text((px, py + drop + 27), label, font=F(32, 800),
                   fill=INK if not win else (255, 255, 255), anchor='mm')
            if win:
                tickmark(d, px + 62, py + drop - 34, 22, acc, cl((lt - 5.95) / .35), 10)
            else:
                cross(d, px - 62, py + drop - 34, 20, RED, cl((lt - 4.30) / .35), 10)
    # "+1" badges — one skill, a little better every day — rise from the hand into the dark
    for i in range(3):
        bp = (lt - 2.45 - i * .50) / 1.10
        if 0 < bp < 1:
            k = e_out(bp, 2.0)
            bx = 404 + i * 22 + math.sin(bp * 6 + i) * 8
            by = 800 - k * 250
            a = int(255 * (1 - cl((bp - .70) / .30)))
            d.rounded_rectangle([bx - 46, by - 26, bx + 46, by + 26], 26, fill=acc + (a,))
            d.text((bx, by + 1), '+1', font=F(30, 800), fill=(255, 255, 255, a), anchor='mm')
    payoff(d, ['MANGTA', 'NAHI,', 'DETA', 'HAI'], cl((lt - 5.90) / .55), acc, {2}, 76)


# ───────────────────────────────────────────── 6  GO   (8.916 s, VO at 0.05)
#   0.09 Jism  0.98 dimagh  1.84 control  2.82 value  3.52 "bas chaar"
#   4.21 "Aaj se"  4.77 "shuru"  5.60 "Follow karo part two ke liye"  6.92 "aur save karna mat bhoolna"
RECAP = (('JISM', .09), ('DIMAGH', .98), ('CONTROL', 1.84), ('VALUE', 2.82))


def s6(d, lt, acc, t):
    HY.headline(d, ['AAJ', 'SE', 'SHURU'], W / 2, 318, 104, {2}, 5, cl(lt / .42), 42)
    HY.headline(d, ['KARO'], W / 2, 426, 104, {0}, 5, cl((lt - .18) / .42), 42)

    # the four habits switch on inside his dark
    for i, (nm, st) in enumerate(RECAP):
        p = cl((lt - st) / .4)
        if p <= 0:
            continue
        x, y = 130 + i * 160, 574
        assert y + 70 <= wedge_y(x + 70, t) - 30, ('s6 recap in the dark', i, round(t, 3))
        glow_tick(d, x, y, p, max(0.0, 1 - (lt - st) / .6), acc)
        d.text((x, y + 50), nm, font=F(30, 700), fill=POD + (int(255 * cl(p * 1.5)),), anchor='mm')

    # power stance through the recap, cheer on "shuru", then the pill lands
    if lt < 4.70:
        pose = phys(p_power, lt)
        bob = 0.0
    else:
        pose = blend(p_power, T.p_cheer, lt, 4.70, .55, 1.25)
        bob = abs(math.sin(lt * 4.6)) * 26 * e_out(cl((lt - 4.70) / .6), 2)
    ex = 'proud' if lt < 4.70 else 'grin'
    glow = 1.0 + .4 * pulse(lt, 4.74, .8) + .15 * e_io(cl((lt - 4.7) / .6))
    hero(d, lt, W / 2, 500, pose, ex, cl(lt / .3), bob=bob, glow=glow)

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


def scene_img(si, lt, t):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, 'RGBA')
    SCENES[si](d, lt, ACC[si], t)
    if si != 0 or lt > 1.40:                                 # payoff zone (S1 has none before the lift)
        on_paper(W / 2, PAY_Y - 70, t, 'payoff line')
    for t0, t1, txt, hot in CAPS[si]:
        if t0 <= lt < t1:
            words = txt.split()
            f = F(50, 600)
            wdt = sum(f.getlength(w) for w in words) + f.getlength(' ') * (len(words) - 1)
            sz = 50 if wdt <= PW.CAP_MAX_W else max(40, int(50 * PW.CAP_MAX_W / wdt))
            on_paper(W / 2 - wdt * sz / 100 - 12, PW.CAP_Y_P - 30, t, 'caption ' + txt)   # left end
            caption_fit(d, words, (lt - t0) / (t1 - t0), ACC[si], hot)
            break
    return im


def swipe(d, tp, tk, t):
    """v9 tinted swipe, slanted parallel to the seam and two-toned: every band
    element has a paper variant below the wedge line and a charcoal variant
    above it, so crossing the dark zone is not a luma step (measured: the
    single-tone stripes stepped +7 when they entered the wedge in one frame)."""
    nacc = ACC[tk + 1]
    mixc = lambda a, b, k: tuple(int(a[q] * k + b[q] * (1 - k)) for q in range(3))
    tint_p, tint_d = mixc(nacc, PAPER, .18), mixc(nacc, DARK, .06)
    glow_p, glow_d = mixc(nacc, PAPER, .40), mixc(nacc, DARK, .30)
    ink_p, ink_d = INK, mixc(nacc, DARK, .12)
    yl, yr = wedge_ends(t)
    m = (yr - yl) / W
    Hb = H + abs(m) * W
    e = e_io(tp)
    c = Hb - 2 * Hb * e                       # leading edge at x = 0

    def band(lo, hi, col_p, col_d):
        # all edges are parallel to the seam, so "above the wedge" is simply offset < yl
        if min(hi, yl) > lo:
            d.polygon([(0, lo), (W, lo + m * W), (W, min(hi, yl) + m * W), (0, min(hi, yl))], fill=col_d)
        if hi > max(lo, yl):
            d.polygon([(0, max(lo, yl)), (W, max(lo, yl) + m * W), (W, hi + m * W), (0, hi)], fill=col_p)

    band(c + H * .044, c + Hb, tint_p, tint_d)
    band(c + H * .026, c + H * .044, glow_p, glow_d)
    band(c + H * .007, c + H * .026, nacc, nacc)
    band(c, c + H * .007, ink_p, ink_d)


def render(i):
    t = i / FPS
    si, lt = scene_at(t)

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

    cv = backdrop(t, show, acc)
    lay = scene_img(show, slt, t)
    if tp is not None and tp < .5:
        # measured: SHADE is a 7 % dark mass; the diagonal band crossing him in one frame
        # stepped the mean luma 11.4 (gate < 8). The outgoing layer dissolves over the
        # band's first half instead, so the step is spread across 7 frames.
        fa = 1 - e_io(cl(tp / .5))
        lay.putalpha(lay.getchannel('A').point(lambda v: int(v * fa)))
    cv.alpha_composite(lay)
    d = ImageDraw.Draw(cv, 'RGBA')
    HY.chrome(d, t, show, acc, DUR_TOTAL, CHAPTER)
    if tp is not None:
        swipe(d, tp, tk, t)

    frame = cv.convert('RGB')
    dur = SCENE_END[si] - SCENE_START[si]
    z, px, py = camera(t, si, lt, dur)
    iz = 1.0 / z
    ox = (W - W * iz) * .5 + px
    oy = (H - H * iz) * .5 + py
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
        tt = float(sys.argv[2])
        os.makedirs('/home/user/build', exist_ok=True)
        Image.fromarray(render(int(round(tt * FPS)))).save(f'/home/user/build/still_{tt:.2f}.png')
        print('ok')
    elif len(sys.argv) >= 2 and sys.argv[1] == 'contact':
        # python3 src/power2.py contact [t1 t2 ...] -> build/contact_shade.png (4 columns)
        ts = [float(v) for v in sys.argv[2:]] or [0.2, 0.9, 2.3, 4.9, 7.6, 10.2, 14.0, 17.0,
                                                   21.6, 23.3, 27.5, 31.6, 34.2, 36.9, 39.6, 41.5]
        cols = 4
        rows = (len(ts) + cols - 1) // cols
        sc = 0.25
        sheet = Image.new('RGB', (int(W * sc) * cols, int(H * sc) * rows), (20, 20, 22))
        for n, tt in enumerate(ts):
            fr = Image.fromarray(render(int(round(tt * FPS)))).resize((int(W * sc), int(H * sc)), Image.LANCZOS)
            ImageDraw.Draw(fr).text((8, 8), f't={tt:.2f}', fill=(255, 80, 80))
            sheet.paste(fr, ((n % cols) * int(W * sc), (n // cols) * int(H * sc)))
        os.makedirs('/home/user/build', exist_ok=True)
        sheet.save('/home/user/build/contact_shade.png')
        print('ok', len(ts))
