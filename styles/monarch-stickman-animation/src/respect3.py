"""
respect2.py — "LOG AAPKI IZZAT KYUN NAHI KARTE" v2: the voice flows (75.2 s, no padding),
the picture changes every 2-3 s, and no two neighbouring transitions are alike.

Built ON respect.py (the nine chapter scenes keep their phrase-locked props) and adds:
  * SHOTS   — 33 shots: each chapter is split at its phrase onsets into 3-5 shots; a shot is
              either the chapter scene itself, a RE-FRAME of it (world dolly/offset about the
              floor line, UI static — ledger 53) or an INSERT (a new close-up / metaphor
              composition: the bowed room, the crowd of HAANs, the 3-D rule numeral, the sound
              ring, the clock, the pings, the spine, the eyes, the break, the scale, the rising
              heads, the flat-line, the recap carousel, the end card).
  * TRANSITIONS — a library of 14 full-frame transitions (cube turn H/V, zoom-through, whip
              H/V, iris, slices, ink reveal, signature wedge, card push, spin-zoom, light sweep,
              blur dissolve, doors, shatter).  Both neighbours are rendered during the overlap,
              so every transition is a true A->B composite; the chapter wedge offset remains a
              continuous function of t (ledger 50); edges are always filled (no black slivers).
  * timeline_respect2 (voice 90 % of the runtime; chapter breaths 0.55-0.70 s).

Pure function of t.  CLI:  respect2.py A B out.mp4 | still T | contact t1 t2 ...
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_respect2 as TL2
import respect as R
import toon as T
import shade as S
import hybrid as HY
import power as PW
import power2 as P2
from clean import (W, H, FPS, PAPER, PAPER_D, SOFT, INK, GY, PAY_Y, cl, fl, e_out, e_io, e_back, F,
                   line, fbox, fcirc, tickmark, shadow, payoff, phys)
from power import mix, blend, p_power, p_calm, p_flinch, glance, ring, cross, caption_fit
from power2 import hero, on_paper, wedge_ends, wedge_y, backdrop, pulse, glow_tick
from respect import (ACC, chrome, camera, wx, silhouette, shaft, dust, hero_layer, card, pill, room, payoff_fit,
                     paste_rgba, DARK)

# ── re-point respect.py at the v2 timeline (its scene functions read these module globals)
for _n in ('SCENE_START', 'SCENE_END', 'DUR_TOTAL', 'VO_AT', 'LEAD', 'PHRASES', 'NAMES'):
    setattr(R, _n, getattr(TL2, _n))
R.TL = TL2
R.NF = int(round(TL2.DUR_TOTAL * FPS))
R.CUTS = list(TL2.CUTS)
SCENE_START, SCENE_END, DUR_TOTAL, VO_AT, LEAD, PHRASES = (TL2.SCENE_START, TL2.SCENE_END, TL2.DUR_TOTAL,
                                                           TL2.VO_AT, TL2.LEAD, TL2.PHRASES)
NF = R.NF
OUT_DEFAULT = '/home/user/shade_respect_v2.mp4'
scene_at = R.scene_at                      # P2.scene_at / wedge_drop already point at respect.py's


# ---------------------------------------------------------------- v3 enhancements (SHADE_ENH=1, default on)
# Grade: soft S-curve, warm highlights / cool shadows, vignette. Punch: a short camera pop on every
# voice onset and every cut, so the picture hits the beat. Both are switchable for A/B against v2.
ENH = os.environ.get('SHADE_ENH', '1') == '1'
PUNCH_AMP = float(os.environ.get('SHADE_PUNCH', '0.016'))
_VIG = None


def _grade(arr):
    global _VIG
    if _VIG is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 1.414
        _VIG = (1.0 - 0.20 * np.clip(r, 0, 1) ** 2.2)[..., None].astype(np.float32)
    x = arr.astype(np.float32) / 255.0
    lum = (0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2])[..., None]
    s = x + 0.10 * (x - 0.5) * (1.0 - np.abs(2.0 * x - 1.0))
    hi = np.clip((lum - 0.55) / 0.45, 0, 1)[..., 0]
    lo = np.clip((0.35 - lum) / 0.35, 0, 1)[..., 0]
    s[..., 0] *= 1.0 + 0.03 * hi
    s[..., 2] *= 1.0 - 0.04 * hi + 0.035 * lo
    s *= _VIG
    return s * 255.0


_BEATS = None  # built on first use (BOUNDS is defined further down)


def _punch(t):
    global _BEATS
    if _BEATS is None:
        _BEATS = sorted(set([SCENE_START[i] + LEAD[i] for i in range(len(SCENE_START))] + list(BOUNDS)))
    best = 0.0
    for b in _BEATS:
        d = t - b
        if 0.0 <= d < 0.6:
            best = max(best, math.exp(-d / 0.11))
    return PUNCH_AMP * best


def vt(si, k):
    return LEAD[si] + PHRASES[si][k]


def abs_t(si, k):
    return SCENE_START[si] + vt(si, k)


# ═══════════════════════════════════════════════ inserts (new compositions)
def _paste(base, sp, x, y):
    """alpha-composite a sprite at (x, y) with cropping on every side."""
    x, y = int(round(x)), int(round(y))
    sx = sy = 0
    if x < 0: sx, x = -x, 0
    if y < 0: sy, y = -y, 0
    ex, ey = min(sp.width, sx + base.width - x), min(sp.height, sy + base.height - y)
    if ex <= sx or ey <= sy:
        return
    base.alpha_composite(sp.crop((sx, sy, ex, ey)), (x, y))


def ink_line(d, words, y, sz, hot, acc, p, rise=44, maxw=W - 160, x=W / 2):
    """clean.line in ink on the paper half, measured: never wider than maxw."""
    f = F(sz, 800)
    wdt = sum(f.getlength(w) for w in words) + f.getlength(' ') * (len(words) - 1)
    if wdt > maxw:
        sz = max(52, int(sz * maxw / wdt))
    line(d, words, x, y, sz, 800, INK, hot, acc, p, rise)


def ins_question(d, u, si, acc, t, par, lt):
    """S1c — the question, close: SHADE fills the dark half, turns his head to the lens."""
    shaft(d, t, 300, 300, 30)
    dust(d, t, 100, 1000, 120, 1000, 100, par=par)
    silhouette(d, 190, 520, 33, T.p_think, lt, head_t=16, blur=3, alpha=.6, par=par)
    hx, hs = 690, 790
    pose = dict(phys(S.p_pocket, lt))
    turn = e_io(cl(u / .8))
    pose['yaw'] = pose['yaw'] * (1 - turn)
    pose['head'] = pose['head'] - 10 * (1 - turn)
    glow = .55 + .65 * turn + .35 * pulse(u, 1.2, .9)
    lay, _ = hero_layer(lt, hx, hs, pose, 'determined' if turn > .5 else 'neutral', reflect=.12, glow=glow,
                        look=(-.6 * (1 - turn), .1))
    d._image.alpha_composite(lay)
    HY.headline(d, ['IZZAT'], W / 2, 318, 124, {0}, si, cl(u / .55), 46)
    HY.headline(d, ['KYUN', 'NAHI?'], W / 2, 436, 96, None, si, cl((u - .18) / .55), 42)


def ins_nod(d, u, si, acc, t, par, lt):
    """S2b — 'har baat par haan': close on the nodding head; every HAAN pops out of it, big."""
    hx, hs = 400, 720
    pose = dict(phys(S.p_pocket, lt))
    pose['yaw'] = pose['yaw'] - 16
    nod = 0.0
    for ht in R.HAAN_T:
        q = (lt - LEAD[si] - ht + .25) / .45
        if 0 < q < 1:
            nod = math.sin(q * math.pi) * 10
    pose['head_t'] = pose.get('head_t', 0) + nod
    silhouette(d, 960, 560, 34, T.p_think, lt, head_t=-3, blur=1.5, alpha=.85, flip=True, par=par)
    hero(d, lt, hx, hs, pose, 'sly', look=(.9, .1), glow=.85 - .25 * cl(u / 2.5) + .15 * nod / 10)
    for n, ht in enumerate(R.HAAN_T):
        q = cl((lt - LEAD[si] - ht) / .8)
        if q <= 0:
            continue
        e = e_io(q)
        x = hx + 120 + 520 * e
        y = GY - hs * .95 + 60 - 160 * math.sin(math.pi * q) + 420 * e
        card(d, x, y, 'HAAN', acc, min(1, q * 3), 34 - 8 * e, 170 - 40 * e, (1 - q) * .4 * (1 if n % 2 else -1), int(255 * (1 - .55 * q)))
    HY.headline(d, ['HAR', 'BAAT', 'PAR'], W / 2, 330, 104, None, si, cl(u / .5), 44)
    HY.headline(d, ['HAAN'], W / 2, 446, 100, {0}, si, cl((u - .15) / .5), 40)


def ins_lift(d, u, si, acc, t, par, lt):
    """S3a — the turn in slow motion, close: the head lifts, the eyes ignite, the dark warms."""
    k = e_io(cl((u - .25) / 1.5))
    shaft(d, t, 560, 420, 18 + 50 * k)
    dust(d, t, 120, 980, 120, 1100, 80 + 100 * k, par=par)
    hx, hs = W / 2, 820
    pose = mix(phys(T.p_sad, lt), phys(p_power, lt), k)
    glow = .2 + 1.2 * k
    blink = (1 - e_out(cl((u - .5) / 1.0), 2.0)) if u < 1.6 else None
    lay, _ = hero_layer(lt, hx, hs, pose, 'neutral' if k < .5 else 'determined', reflect=.14 * k, glow=glow, blink=blink)
    d._image.alpha_composite(lay)
    if k > 0:                                                      # two pale beams open with the eyes
        hy = GY - hs * .905
        for sx in (-1, 1):
            d.line([(hx + sx * hs * .034, hy), (hx + sx * 140 * k, hy + 420 * k)],
                   fill=S.GLOW_C + (int(70 * k * (0.6 + 0.4 * math.sin(t * 5))),), width=2)
    HY.headline(d, ['IZZAT'], W / 2, 318, 118, None, si, cl(u / .6), 46)
    HY.headline(d, ['MAANGI', 'NAHI', 'JAATI'], W / 2, 432, 80, {1}, si, cl((u - .2) / .6), 42)


def ins_bowed(d, u, si, acc, t, par, lt):
    """S1b — the room from his eyes: three big bowed heads, none lifts (counter-light, no eyes)."""
    for i, (x, s, pf, flip, blur, ph) in enumerate(((250, 620, T.p_think, False, 1.5, 0.0),
                                                     (600, 700, T.p_idle, True, 1.0, .9),
                                                     (930, 640, T.p_think, True, 1.5, 1.7))):
        silhouette(d, x + 12 * math.sin(t * .6 + ph), s, 30 + i, pf, lt + ph, head_t=16 + 2 * math.sin(t + ph),
                   blur=blur, alpha=.86, flip=flip, par=par)
    shaft(d, t, 540, 300, 26)
    dust(d, t, 100, 1000, 120, 1000, 90, par=par)
    HY.headline(d, ['KOI', 'SAR'], W / 2, 330, 112, {1}, si, cl(u / .5), 44)
    HY.headline(d, ['NAHI', 'UTHATA'], W / 2, 446, 86, None, si, cl((u - .15) / .5), 40)


def ins_crowd(d, u, si, acc, t, par, lt):
    """S2d — 'jo sab ka hai, kisi ka nahi': a grid of identical nodding figures; he is one of them."""
    rows = ((GY - 420, .62, 2.0, .55), (GY - 200, .80, 1.2, .70), (GY, 1.00, 0.0, .85))
    for r, (yb, sc, blur, al) in enumerate(rows):
        n = 5 - r
        for i in range(n):
            x = W / 2 + (i - (n - 1) / 2) * (300 * sc) + 10 * math.sin(t * .8 + i)
            q = cl((u - .08 * (r * 5 + i)) / .35)
            if q <= 0:
                continue
            nod = 7 * math.sin(t * 5.2 + i * 1.3 + r)
            s = 330 * sc
            sp = R.sil_sprite(40 + r * 10 + i, T.p_idle, max(48, int(round(s / 16.0)) * 16), int(round(nod / 2)) * 2,
                              int(lt * 6) % 12, blur, bool(i % 2))
            sq = max(48, int(round(s / 16.0)) * 16)
            if sq != int(s):
                f_ = s / sq
                sp = sp.resize((max(1, int(sp.width * f_)), max(1, int(sp.height * f_))), Image.BILINEAR)
            sp = sp.copy()
            sp.putalpha(sp.getchannel('A').point(lambda v, a=al * q: int(v * a)))
            paste_rgba(d._image, sp, x - .92 * s, yb + par[1] * (1 - sc) - 1.30 * s)
    # the hero in the front row, same nod, but his glow is nearly out
    hx, hs = W / 2 + 10 * math.sin(t * .8 + 1), 330
    pose = dict(phys(S.p_pocket, lt))
    pose['head_t'] = pose.get('head_t', 0) + 7 * math.sin(t * 5.2 + 1.3 + 2)
    hero(d, lt, hx, hs, pose, 'neutral', glow=.30 + .1 * math.sin(t * 3), p=cl(u / .4))
    HY.headline(d, ['SAB', 'KA'], W / 2, 330, 112, None, si, cl(u / .5), 44)
    HY.headline(d, ['KISI', 'KA', 'NAHI'], W / 2, 446, 86, {2}, si, cl((u - .9) / .5), 40)


def ins_numeral(d, u, si, acc, t, par, lt, num, words, hot):
    """Rule title card: an extruded 3-D numeral turning in the dark, the rule words in ink on the
    paper under it, the hero small and centred below (poster layout: RULE / numeral / words / hero)."""
    p = cl(u / .55)
    k = e_back(p, 1.6)
    cx, cy = W / 2 + 60 * (1 - k), 560
    ang = (1 - e_out(p, 2.0)) * 1.1 + .06 * math.sin(t * 1.3)
    f = F(int(300 * max(.3, k)), 800)
    depth = 26
    for i in range(depth, 0, -1):
        sh = i / depth
        col = tuple(int(c * (.22 + .5 * (1 - sh))) for c in HY.hot(si))
        d.text((cx + i * math.cos(ang + .6) * 1.4, cy + i * 1.1), num, font=f, fill=col, anchor='mm')
    d.text((cx, cy), num, font=f, fill=HY.hot(si), anchor='mm')
    d.text((cx - 4, cy - 4), num, font=f, fill=(255, 255, 255, int(70 * p)), anchor='mm')
    HY.headline(d, ['RULE'], W / 2, 300, 74, None, si, cl((u - .05) / .45), 36)
    # the words: ink on paper (the seam never rises above y 1065 at any x), measured to W - 160
    ink_line(d, words, 1130, 96, hot, acc, cl((u - .25) / .55), maxw=700, x=440)
    hero(d, lt, 930 + 70 * (1 - e_io(cl(u / .8))), 300, phys(S.p_pocket, lt), 'determined',
         glow=.9 + .3 * pulse(u, .3, .8), look=(-.5, -.2), p=cl((u - .1) / .5))
    dust(d, t, 100, 1000, 120, 900, 70, par=par)


def ins_ring(d, u, si, acc, t, par, lt):
    """S4c — 'ek jumla, sahi waqt par': one word, one expanding sound ring in silence."""
    hx, hs = W / 2, 600
    pose = blend(S.p_arms_cross, T.p_present, lt, 0.0, .6, 1.12) if u > .1 else phys(S.p_arms_cross, lt)
    lay, _ = hero_layer(lt, hx, hs, pose, 'determined' if u < 1.1 else 'proud', reflect=.14,
                        glow=.9 + .5 * pulse(u, .35, 1.0))
    d._image.alpha_composite(lay)
    my = GY - hs * .86
    for n in range(4):
        q = ((u - .35) / 1.6 - n * .22)
        if 0 < q < 1:
            r = 40 + 560 * e_out(q, 1.6)
            a = int(170 * (1 - q) ** 1.3)
            d.ellipse([hx - r, my - r * .62, hx + r, my + r * .62], outline=acc + (a,), width=max(2, int(10 * (1 - q))))
    HY.headline(d, ['EK', 'JUMLA'], W / 2, 330, 118, {1}, si, cl(u / .5), 44)
    HY.headline(d, ['SAHI', 'WAQT', 'PAR'], W / 2, 446, 80, None, si, cl((u - .85) / .5), 40)


def ins_turnroom(d, u, si, acc, t, par, lt):
    """S4d — 'poora kamra sunta hai': the room's heads turn to him, one after the other."""
    heads = [12 - 20 * e_io(cl((u - i * .14) / .5)) for i in range(5)]
    eyes = [e_out(cl((u - i * .14 - .25) / .4), 2.0) * .8 for i in range(5)]
    k = .94 + .05 * cl(u / 2.2)
    room(d, lt, t, k, par, heads, eyes)
    shaft(d, t, 760, 360, 30 + 20 * cl(u / 1.5))
    dust(d, t, 300, 1060, 120, 1200, 110, par=par)
    hero(d, lt, wx(760, k), 440 * k, phys(p_power, lt), 'proud', glow=1.05 + .2 * math.sin(t * 2), look=(0, 0))
    HY.headline(d, ['POORA', 'KAMRA'], W / 2, 330, 112, None, si, cl(u / .5), 44)
    HY.headline(d, ['SUNTA', 'HAI'], W / 2, 446, 86, {0}, si, cl((u - .2) / .5), 40)


def ins_clock(d, u, si, acc, t, par, lt):
    """S5b — a big clock on the dark, its hour hand snapping forward while a price tag climbs."""
    cx, cy = W / 2, 700
    r = 300
    for i in range(12):
        a = i * math.pi / 6
        d.line([(cx + (r - 26) * math.cos(a), cy + (r - 26) * math.sin(a)), (cx + r * math.cos(a), cy + r * math.sin(a))],
               fill=(190, 186, 190, 200), width=8 if i % 3 == 0 else 4)
    d.ellipse([cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10], outline=(170, 166, 170, 170), width=8)
    steps = int(u / .32)
    ang = -math.pi / 2 + steps * .52 + .52 * e_out(cl((u - steps * .32) / .12), 2.0)
    d.line([(cx, cy), (cx + (r - 70) * math.cos(ang), cy + (r - 70) * math.sin(ang))], fill=HY.hot(si), width=14)
    mang = -math.pi / 2 + u * 2.6
    d.line([(cx, cy), (cx + (r - 40) * math.cos(mang), cy + (r - 40) * math.sin(mang))], fill=(220, 216, 220), width=6)
    d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=HY.hot(si))
    for n in range(steps + 1):                                     # the price rises a step per hour
        q = cl((u - n * .32) / .3)
        if q <= 0 or n > 5:
            continue
        y = 1280 - n * 46
        d.rounded_rectangle([W / 2 - 150, y, W / 2 + 150, y + 40], 8, fill=PAPER_D if y > wedge_y(W / 2, t) + 30 else HY.DARK_L,
                            outline=acc, width=3)
        d.text((W / 2, y + 20), f'{n + 1} GHANTA = {("", "MEHNGA", "AUR MEHNGA", "KEEMTI", "NAAYAB", "AAPKA")[min(n, 5)]}',
               font=F(22, 800), fill=acc, anchor='mm')
    HY.headline(d, ['WAQT'], W / 2, 300, 110, {0}, si, cl(u / .5), 44)


def ins_pings(d, u, si, acc, t, par, lt):
    """S5c/d — 'jo har waqt available hai': a figure yanked by three pings; then SHADE, still,
    the pings bounce off his glow."""
    yank = u < 1.55
    if yank:
        x = 300 + 60 * math.sin(u * 9.0) + 40 * math.sin(u * 13.0)
        silhouette(d, x, 470, 50, T.p_present, lt, head_t=-8 + 10 * math.sin(u * 11), blur=1.2, alpha=.85, par=par)
        for n, (px_, py_, ph) in enumerate(((120, 700, 0.0), (520, 640, .5), (330, 520, 1.0))):
            q = (u * 1.6 + ph) % 1.0
            rr = 14 + 60 * q
            d.ellipse([px_ - rr, py_ - rr, px_ + rr, py_ + rr], outline=acc + (int(220 * (1 - q)),), width=5)
            d.line([(px_, py_), (x, GY - 470 * .9)], fill=acc + (int(90 * (1 - q)),), width=3)
        HY.headline(d, ['ZAROORI'], W / 2, 330, 112, None, si, cl(u / .5), 44)
        HY.headline(d, ['NAHI', 'LAGTA'], W / 2, 446, 86, {0}, si, cl((u - .15) / .5), 40)
    hx, hs = 760, 540
    v = cl((u - 1.3) / .4)
    if v > 0:
        pose = phys(S.p_pocket, lt)
        glow = 1.0 + .4 * pulse(u, 2.0, .9)
        hero(d, lt, hx, hs, pose, 'proud' if u > 2.0 else 'determined', glow=glow, p=v)
        for n in range(3):                                         # pings hit the glow and die
            q = ((u - 1.7) / 1.3 - n * .25)
            if 0 < q < 1:
                a0 = -2.4 + n * .7
                rr = 220 * (1 - e_out(q, 1.6))
                px_ = hx + rr * math.cos(a0) - 140 * (1 - q)
                py_ = GY - hs * .7 + rr * math.sin(a0)
                r2 = 10 + 10 * q
                d.ellipse([px_ - r2, py_ - r2, px_ + r2, py_ + r2], outline=acc + (int(220 * (1 - q)),), width=4)
        if u > 1.6:
            HY.headline(d, ['APNI', 'MARZI'], W / 2, 330, 112, {1}, si, cl((u - 1.6) / .5), 44)
            HY.headline(d, ['SE'], W / 2, 446, 86, None, si, cl((u - 1.75) / .5), 40)


def ins_meter(d, u, si, acc, t, par, lt):
    """S6b — 'har haan ki keemat izzat se katti hai': an IZZAT meter drains a notch per HAAN."""
    bx, by, bw, bh = 170, 700, 740, 64
    d.rounded_rectangle([bx - 6, by - 6, bx + bw + 6, by + bh + 6], 18, outline=(200, 196, 200, 220), width=5)
    n = min(6, int(u / .42))
    lvl = 1.0 - .15 * n - .15 * e_out(cl((u - n * .42) / .25), 2.0) * (n < 6)
    d.rounded_rectangle([bx, by, bx + bw * max(.04, lvl), by + bh], 14, fill=HY.hot(si))
    d.text((bx, by - 30), 'IZZAT', font=F(30, 800), fill=HY.PAPER_ON_DARK, anchor='lm')
    for i in range(n + 1):
        q = cl((u - i * .42) / .3)
        if q <= 0 or i > 5:
            continue
        x = bx + 60 + i * 120 + 12 * math.sin(t * 3 + i)
        y = by + 150 + 30 * (1 - e_out(q, 2.0))
        card(d, x, y, 'HAAN', (140, 132, 138), q, 24, 108, (.1 if i % 2 else -.1), int(255 * min(1, q * 2)))
    hx, hs = 740, 520
    pose = dict(phys(S.p_pocket, lt))
    pose['head_t'] = pose.get('head_t', 0) + 6 * max(0, math.sin((u % .42) / .42 * math.pi)) * (n < 6)
    hero(d, lt, hx, hs, pose, 'neutral', glow=.9 - .09 * n, look=(.4, .1))
    HY.headline(d, ['HAR', 'HAAN', 'KI'], W / 2, 330, 104, None, si, cl(u / .5), 44)
    HY.headline(d, ['KEEMAT'], W / 2, 446, 90, {0}, si, cl((u - .15) / .5), 40)


def ins_spine(d, u, si, acc, t, par, lt):
    """S7b — 'seedhi kamar': a close profile, a guide line snaps from bent to straight."""
    hx, hs = W / 2 - 60, 780
    k = e_out(cl((u - .15) / .55), 2.4)
    pose = mix(phys(T.p_sad, lt), phys(p_calm, lt), k)
    lay, _ = hero_layer(lt, hx, hs, pose, 'determined' if k > .5 else 'neutral', reflect=0, glow=.6 + .6 * k, look=(.3, .2))
    d._image.alpha_composite(lay)
    # the guide: a bent polyline straightening into a vertical
    pts = []
    for i in range(9):
        q = i / 8
        bend = (1 - k) * 110 * math.sin(q * math.pi)
        pts.append((hx + 210 + bend, GY - hs * .22 - q * hs * .70))
    d.line(pts, fill=HY.hot(si) + (int(230 * cl(u / .3)),), width=7, joint='curve')
    if k >= 1:
        d.ellipse([pts[-1][0] - 10, pts[-1][1] - 10, pts[-1][0] + 10, pts[-1][1] + 10], fill=HY.hot(si))
    HY.headline(d, ['SEEDHI'], W / 2, 330, 112, None, si, cl(u / .5), 44)
    HY.headline(d, ['KAMAR'], W / 2, 446, 90, {0}, si, cl((u - .12) / .5), 40)


def ins_walk(d, u, si, acc, t, par, lt):
    """S7c — 'dheemi chaal': a slow tracking shot, motion trails, the floor sliding under him."""
    hx, hs = 420 + 60 * e_io(cl(u / 1.1)), 560
    for n in range(4, 0, -1):                                      # ghost trails
        gp = phys(T.p_walk, (lt - n * .07) * .55)
        lay, _ = hero_layer(lt - n * .07, hx - n * 34, hs, gp, 'neutral', glow=0.0)
        lay.putalpha(lay.getchannel('A').point(lambda v, a=.16 - n * .03: int(v * a)))
        d._image.alpha_composite(lay)
    lay, _ = hero_layer(lt, hx, hs, phys(T.p_walk, lt * .55), 'determined', reflect=.16, glow=1.0)
    d._image.alpha_composite(lay)
    for i in range(7):                                             # floor marks slide left
        x = (i * 180 - (u * 160) % 180) + 20
        y0 = GY + 30 + i % 2 * 14
        if y0 > wedge_y(x, t) + 40:
            d.line([(x, y0), (x + 70, y0)], fill=(150, 142, 130), width=4)
    HY.headline(d, ['DHEEMI'], W / 2, 330, 112, None, si, cl(u / .5), 44)
    HY.headline(d, ['CHAAL'], W / 2, 446, 90, {0}, si, cl((u - .12) / .5), 40)


def ins_eyes(d, u, si, acc, t, par, lt):
    """S7d — 'nazar aankhon mein': the hood fills the dark half (clipped at the seam), the eyes
    ignite, a thin flare runs across them; the paper half stays clean for the caption."""
    hs = 1500
    lay, _ = hero_layer(lt, W / 2, hs, phys(p_power, lt), 'determined', glow=.45 + .85 * e_out(cl((u - .2) / .5), 2.0))
    ld = ImageDraw.Draw(lay, 'RGBA')
    ey = GY - hs * .905
    fl_ = e_out(cl((u - .45) / .5), 2.0) * (1 - .5 * cl((u - 1.2) / .6))
    if fl_ > 0:                                                    # anamorphic flare across the eyes
        for ww, aa in ((22, 26), (10, 60), (3, 150)):
            ld.line([(W / 2 - 760 * fl_, ey), (W / 2 + 760 * fl_, ey)], fill=S.GLOW_C + (int(aa * fl_),), width=ww)
    lay = lay.transform((W, H), Image.AFFINE, (1, 0, 0, 0, 1, -(380 - ey)), Image.BILINEAR)   # eyes land at y ~ 470 (rig offset measured)
    yl, yr = wedge_ends(t)
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon([(0, 0), (W, 0), (W, yr - 2), (0, yl - 2)], fill=255)
    from PIL import ImageChops
    lay.putalpha(ImageChops.multiply(lay.getchannel('A'), m))
    d._image.alpha_composite(lay)
    ink_line(d, ['NAZAR', 'AANKHON', 'MEIN'], 1130, 84, {1}, acc, cl(u / .5))


def ins_break(d, u, si, acc, t, par, lt):
    """S8b — 'ek tooti baat sau sach maar deti hai': a paper plate SACH cracks and falls apart in
    slow motion while a hundred small ticks go grey."""
    cx, cy = W / 2, 760
    br = cl((u - .9) / .5)
    for n in range(100):
        i, j = n % 10, n // 10
        q = cl((u - n * .012) / .3)
        if q <= 0:
            continue
        x, y = 160 + i * 84, 1000 + j * 36
        col = acc if br <= 0 else tuple(int(c * (1 - br) + 130 * br) for c in acc)
        if y > wedge_y(x, t) + 30:
            tickmark(d, x, y, 8, col, min(1, q * 1.3), 4)
    # the plate: whole, then four pieces separating with rotation
    pcs = ((-1, -1, -.4, -.06), (1, -1, .5, .05), (-1, 1, -.6, -.08), (1, 1, .7, .07))
    rr = 230 * e_back(cl(u / .5), 1.4)
    for sx, sy, vx, rot in pcs:
        off = 160 * e_out(br, 1.8)
        ox, oy = sx * off * .7 + vx * off, sy * off + 90 * br * br
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay, 'RGBA')
        ld.pieslice([cx - rr, cy - rr, cx + rr, cy + rr],
                    {(-1, -1): 180, (1, -1): 270, (1, 1): 0, (-1, 1): 90}[(sx, sy)],
                    {(-1, -1): 270, (1, -1): 360, (1, 1): 90, (-1, 1): 180}[(sx, sy)],
                    fill=(236, 232, 222, 255), outline=INK + (255,), width=5)
        if br > 0:
            lay = lay.rotate(rot * br * 57.3, center=(cx, cy), resample=Image.BILINEAR)
        _paste(d._image, lay, ox, oy)
    if rr > 30:
        d.text((cx, cy - 40 * br), 'SACH', font=F(int(min(96, rr * .4)), 800), fill=INK + (int(255 * (1 - br)),), anchor='mm')
    if br > 0:
        for n in range(6):                                         # the crack flashes once
            a = n * 1.05 + .3
            l_ = 60 + 180 * e_out(br, 1.5)
            d.line([(cx, cy), (cx + l_ * math.cos(a), cy + l_ * math.sin(a))], fill=HY.hot(si) + (int(220 * (1 - br)),), width=4)
    HY.headline(d, ['EK', 'TOOTI', 'BAAT'], W / 2, 330, 96, {1}, si, cl(u / .5), 44)
    HY.headline(d, ['SAU', 'SACH'], W / 2, 446, 86, None, si, cl((u - .6) / .5), 40)


def ins_scale(d, u, si, acc, t, par, lt):
    """S8c — 'aapka lafz, aapki keemat': a balance; a paper LAFZ outweighs a gold stack."""
    cx, cy = W / 2, 620
    tilt = -.18 * e_io(cl((u - .5) / .8))
    d.line([(cx, cy), (cx, cy + 420)], fill=(200, 196, 200), width=10)
    d.polygon([(cx - 150, cy + 430), (cx + 150, cy + 430), (cx, cy + 390)], fill=(200, 196, 200))
    L = 330
    ax, ay = cx - L * math.cos(tilt), cy - L * math.sin(tilt)
    bx, by = cx + L * math.cos(tilt), cy + L * math.sin(tilt)
    d.line([(ax, ay), (bx, by)], fill=HY.hot(si), width=12)
    for px_, py_ in ((ax, ay), (bx, by)):
        d.line([(px_, py_), (px_ - 70, py_ + 150)], fill=(200, 196, 200), width=4)
        d.line([(px_, py_), (px_ + 70, py_ + 150)], fill=(200, 196, 200), width=4)
        d.rounded_rectangle([px_ - 110, py_ + 150, px_ + 110, py_ + 172], 8, fill=(200, 196, 200))
    q = cl(u / .5)
    card(d, ax, ay + 110, 'LAFZ', INK, q, 34, 190, tilt)
    for i in range(3):                                             # the gold stack on the other pan
        r = cl((u - .2 - i * .1) / .4)
        if r > 0:
            d.rounded_rectangle([bx - 70, by + 130 - i * 22 - 20 * r, bx + 70, by + 150 - i * 22 - 20 * r + 18], 6,
                                fill=(214, 170, 60), outline=(120, 90, 20), width=3)
    hero(d, lt, 800, 440, phys(p_power, lt), 'proud', glow=1.0 + .3 * pulse(u, .9, .9), look=(-.4, .1), p=cl(u / .4))
    HY.headline(d, ['AAPKA', 'LAFZ'], W / 2, 300, 104, {1}, si, cl(u / .5), 44)
    HY.headline(d, ['AAPKI', 'KEEMAT'], W / 2, 410, 84, None, si, cl((u - .9) / .5), 40)


def ins_heads(d, u, si, acc, t, par, lt):
    """S9b — 'aur sab sar uthate hain': the bowed heads of shot 1b lift, eyes open, one by one."""
    for i, (x, s, pf, flip, blur, ph) in enumerate(((250, 620, T.p_think, False, 1.5, 0.0),
                                                     (600, 700, T.p_idle, True, 1.0, .9),
                                                     (930, 640, T.p_think, True, 1.5, 1.7))):
        q = cl((u - .1 - i * .3) / .6)
        silhouette(d, x + 12 * math.sin(t * .6 + ph), s, 30 + i, pf, lt + ph, head_t=16 - 24 * e_io(q),
                   blur=blur, alpha=.86, flip=flip, eyes=e_out(cl((q - .5) / .5), 2.0), par=par)
    shaft(d, t, 540, 300 + 120 * cl(u / 1.5), 30 + 30 * cl(u / 1.5))
    dust(d, t, 100, 1000, 120, 1000, 120, par=par)
    HY.headline(d, ['SAB', 'SAR'], W / 2, 330, 112, None, si, cl(u / .5), 44)
    HY.headline(d, ['UTHATE', 'HAIN'], W / 2, 446, 86, {0}, si, cl((u - .15) / .5), 40)


def ins_flatline(d, u, si, acc, t, par, lt):
    """S9c — 'izzat shor nahi, khamoshi hai': a loud waveform settles into one straight line."""
    calm = e_io(cl((u - 1.4) / 1.0))
    y0 = 760
    pts = []
    for i in range(0, W + 1, 12):
        q = i / W
        amp = (1 - calm) * (90 * math.sin(q * 31 + t * 9) + 50 * math.sin(q * 71 - t * 13)) * (0.5 + 0.5 * math.sin(q * math.pi))
        pts.append((i, y0 + amp))
    d.line(pts, fill=HY.hot(si) + (235,), width=6, joint='curve')
    hx, hs = W / 2, 620
    lay, _ = hero_layer(lt, hx, hs, phys(p_power, lt), 'proud', reflect=.14, glow=1.0 + .25 * calm)
    d._image.alpha_composite(lay)
    HY.headline(d, ['IZZAT', 'SHOR', 'NAHI'], W / 2, 330, 96, {1}, si, cl(u / .5), 44)
    HY.headline(d, ['KHAMOSHI', 'HAI'], W / 2, 446, 86, {0}, si, cl((u - 1.5) / .5), 40)


def ins_carousel(d, u, si, acc, t, par, lt):
    """S9d — 'paanch rules aaj se': the five rules on a turning 3-D ring."""
    cx, cy = W / 2, 720
    rot = u * .9
    items = []
    for i, w in enumerate(R.RECAP):
        a = rot + i * 2 * math.pi / 5
        z = math.cos(a)
        items.append((z, cx + 380 * math.sin(a), cy + 40 * z, w, i))
    for z, x, y, w, i in sorted(items):
        sc = .62 + .38 * (z + 1) / 2
        al = int(110 + 145 * (z + 1) / 2)
        q = cl((u - i * .1) / .4)
        if q <= 0:
            continue
        qq = e_q(q)
        sc *= .55 + .45 * qq
        al = int(al * qq)
        f = F(int(42 * sc), 800)
        tw_ = f.getlength(w) + 60 * sc
        col = tuple(int(c * (0.45 + .55 * (z + 1) / 2) * (.3 + .7 * qq)) for c in HY.hot(si))
        d.rounded_rectangle([x - tw_ / 2, y - 40 * sc, x + tw_ / 2, y + 40 * sc], 14, fill=HY.DARK_L + (al,), outline=col, width=4)
        d.text((x, y + 1), w, font=f, fill=HY.PAPER_ON_DARK + (al,), anchor='mm')
        d.text((x - tw_ / 2 + 18 * sc, y - 40 * sc - 16 * sc), f'0{i + 1}', font=F(int(20 * sc), 800), fill=col, anchor='lm')
    hero(d, lt, W / 2, 380, phys(p_power, lt), 'proud', glow=1.0, p=cl(u / .4))
    HY.headline(d, ['PAANCH', 'RULES'], W / 2, 300, 104, {0}, si, cl(u / .5), 44)
    HY.headline(d, ['AAJ', 'SE'], W / 2, 410, 84, None, si, cl((u - .4) / .5), 40)


def ins_endcard(d, u, si, acc, t, par, lt):
    """S9e — FOLLOW / SAVE: two 3-D buttons press themselves, the hero gives a nod, end card."""
    hero(d, lt, W / 2, 520, phys(p_power, lt), 'proud', glow=1.0 + .2 * math.sin(t * 2.2), p=1.0)
    for i, (lbl, x, t0) in enumerate((('FOLLOW', W / 2 - 230, .2), ('SAVE', W / 2 + 230, .75))):
        q = cl((u - t0) / .5)
        if q <= 0:
            continue
        press = pulse(u, t0 + .5, .5)
        dy = 10 * press
        y = 1040
        d.rounded_rectangle([x - 180, y - 60 + 12, x + 180, y + 60 + 12], 30, fill=(0, 0, 0, 90))
        d.rounded_rectangle([x - 180, y - 60 + dy, x + 180, y + 60 + dy], 30, fill=HY.hot(si) if i == 0 else HY.DARK_L,
                            outline=HY.hot(si), width=5)
        d.text((x, y + dy), lbl, font=F(44, 800), fill=HY.PAPER_ON_DARK if i else (20, 18, 22), anchor='mm')
        if press > 0:
            rr = 60 + 140 * press
            d.ellipse([x - rr, y - rr * .5, x + rr, y + rr * .5], outline=HY.hot(si) + (int(160 * (1 - press)),), width=4)
    HY.headline(d, ['FOLLOW', 'KARO'], W / 2, 300, 100, {0}, si, cl(u / .5), 44)
    HY.headline(d, ['AUR', 'SAVE', 'KARO'], W / 2, 410, 80, {1}, si, cl((u - .5) / .5), 40)
    q = cl((u - 1.9) / .6)
    if q > 0:
        payoff_fit(d, ['KAL', 'PHIR', 'DEKHNA', 'PADEGA'], q, acc, {1})


# ═══════════════════════════════════════════════ the shot list
# (chapter, clip-local start phrase index or explicit time, kind, payload)
#   kind 'scene'  -> the chapter scene as is
#   kind 'insert' -> an insert fn (u = seconds since the shot started)
def _shots():
    sh = []

    def add(si, lt0, kind, payload=None, cap=True):
        sh.append(dict(si=si, t0=round(SCENE_START[si] + lt0, 3), kind=kind, payload=payload, cap=cap))

    # 1 HOOK
    add(0, 0.0, 'scene')
    add(0, vt(0, 1), 'insert', ins_bowed)
    add(0, vt(0, 2), 'insert', ins_question)
    add(0, vt(0, 3) - .30, 'scene')                  # the sweep (TD .60) ENDS on the payoff beat, so the pop lands after it
    # 2 VILLAIN
    add(1, 0.0, 'scene')
    add(1, vt(1, 1), 'insert', ins_nod)
    add(1, vt(1, 2), 'scene')
    add(1, vt(1, 3), 'insert', ins_crowd)
    # 3 TURN
    add(2, 0.0, 'insert', ins_lift)
    add(2, vt(2, 1), 'scene')
    # 4 RULE 1
    add(3, 0.0, 'insert', lambda d, u, si, acc, t, par, lt: ins_numeral(d, u, si, acc, t, par, lt, '1', ['KAM', 'BOLO'], {0}))
    add(3, vt(3, 2), 'scene')
    add(3, vt(3, 4), 'insert', ins_ring)
    add(3, vt(3, 6), 'insert', ins_turnroom)
    # 5 RULE 2
    add(4, 0.0, 'insert', lambda d, u, si, acc, t, par, lt: ins_numeral(d, u, si, acc, t, par, lt, '2', ['WAQT', 'MEHNGA'], {1}))
    add(4, vt(4, 2), 'insert', ins_clock)
    add(4, vt(4, 4), 'insert', ins_pings)
    # 6 RULE 3
    add(5, 0.0, 'insert', lambda d, u, si, acc, t, par, lt: ins_numeral(d, u, si, acc, t, par, lt, '3', ['NA', 'KAHO'], {0}))
    add(5, vt(5, 2), 'insert', ins_meter)
    add(5, vt(5, 3) - .25, 'scene')
    # 7 RULE 4
    add(6, 0.0, 'insert', lambda d, u, si, acc, t, par, lt: ins_numeral(d, u, si, acc, t, par, lt, '4', ['KHUD', 'KO', 'SAMBHALO'], {2}))
    add(6, vt(6, 2), 'insert', ins_spine)
    add(6, vt(6, 3), 'insert', ins_walk)
    add(6, vt(6, 4), 'insert', ins_eyes)
    add(6, vt(6, 5), 'scene')
    # 8 RULE 5
    add(7, 0.0, 'insert', lambda d, u, si, acc, t, par, lt: ins_numeral(d, u, si, acc, t, par, lt, '5', ['JO', 'KAHO', 'WOH', 'KARO'], {3}))
    add(7, vt(7, 2), 'insert', ins_break)
    add(7, vt(7, 3), 'insert', ins_scale)
    # 9 PAYOFF
    add(8, 0.0, 'scene')
    add(8, vt(8, 2), 'insert', ins_heads)
    add(8, vt(8, 3), 'insert', ins_flatline)
    add(8, vt(8, 5), 'insert', ins_carousel)
    add(8, vt(8, 7), 'insert', ins_endcard)
    for i, s in enumerate(sh):
        s['t1'] = sh[i + 1]['t0'] if i + 1 < len(sh) else DUR_TOTAL
    return sh


SHOTS = _shots()
BOUNDS = [s['t0'] for s in SHOTS[1:]]

# ═══════════════════════════════════════════════ transition library  (A, B: uint8 HxWx3; p in (0,1))
_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)
_DARK = np.array(DARK, dtype=np.uint8)
_rs = np.random.RandomState(5)
_INK = np.asarray(Image.fromarray((_rs.rand(11, 6) * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BICUBIC)
                  .filter(ImageFilter.GaussianBlur(22)).resize((W, H), Image.BILINEAR)).astype(np.float32)
_INK = (_INK - _INK.min()) / (_INK.max() - _INK.min() + 1e-6)


def _sm(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def e_q(p):
    """Quintic ease (zero velocity AND zero acceleration at both ends): the motion energy of a
    transition ramps over >= 3 frames, so no step inside it is larger than the cut cap (gate trans_jerk_max < 8)."""
    p = min(1.0, max(0.0, p))
    return p * p * p * (p * (p * 6 - 15) + 10)


def _coeffs(src, dst):
    m = []
    for (x, y), (X, Y) in zip(dst, src):
        m.append([x, y, 1, 0, 0, 0, -X * x, -X * y])
        m.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
    A = np.array(m, dtype=np.float64)
    b = np.array(src, dtype=np.float64).reshape(8)
    return tuple(np.linalg.solve(A, b))


def _persp(img, quad):
    """Map the full image onto `quad` (4 dest points: tl, tr, br, bl) on a DARK canvas."""
    coeffs = _coeffs([(0, 0), (W, 0), (W, H), (0, H)], quad)
    return img.transform((W, H), Image.PERSPECTIVE, coeffs, Image.BILINEAR, fillcolor=DARK)


def _shade(arr, k):
    return (arr.astype(np.float32) * k).astype(np.uint8)


def _hblur(img, amt):
    if amt < 1:
        return img
    w2 = max(8, int(W / (1 + amt)))
    return img.resize((w2, H), Image.BILINEAR).resize((W, H), Image.BILINEAR)


def _vblur(img, amt):
    if amt < 1:
        return img
    h2 = max(8, int(H / (1 + amt)))
    return img.resize((W, h2), Image.BILINEAR).resize((W, H), Image.BILINEAR)


def _gblur(img, r):
    if r < .5:
        return img
    s = max(1, int(r / 2))
    return img.resize((W // s, H // s), Image.BILINEAR).filter(ImageFilter.GaussianBlur(r / s)).resize((W, H), Image.BILINEAR)


def _zoom(img, z, cx=W / 2, cy=H / 2):
    iz = 1 / z
    return img.transform((W, H), Image.AFFINE, (iz, 0, cx - cx * iz, 0, iz, cy - cy * iz), Image.BILINEAR, fillcolor=DARK)


def _mask_mix(A, B, m):
    m = m[..., None].astype(np.float32)
    return (A.astype(np.float32) * (1 - m) + B.astype(np.float32) * m).astype(np.uint8)


def tr_cube_h(A, B, p, acc):
    e = e_q(p)
    ia, ib = Image.fromarray(A), Image.fromarray(B)
    xa = W * (1 - e)                                   # A's right edge (shared cube edge)
    sq = .22 * e                                       # perspective squeeze at the far edge
    qa = [(0 - 160 * e, H * .5 * sq * 0), (xa, H * sq * .5), (xa, H - H * sq * .5), (0 - 160 * e, H)]
    qb = [(xa, H * (.22 * (1 - e)) * .5), (W + 160 * (1 - e), 0), (W + 160 * (1 - e), H), (xa, H - H * (.22 * (1 - e)) * .5)]
    fa = np.asarray(_persp(ia, qa)); fb = np.asarray(_persp(ib, qb))
    xs = _XX
    out = np.where((xs < xa)[..., None], _shade(fa, 1 - .30 * e), _shade(fb, .70 + .30 * e))
    seam = np.exp(-np.abs(xs - xa) / 10.0)[..., None] * 90 * math.sin(math.pi * p)
    return np.clip(out.astype(np.float32) + seam * np.array(acc, dtype=np.float32) / 160, 0, 255).astype(np.uint8)


def tr_cube_v(A, B, p, acc):
    e = e_q(p)
    ia, ib = Image.fromarray(A), Image.fromarray(B)
    ya = H * (1 - e)
    sq = .22 * e
    qa = [(W * sq * .5, 0 - 200 * e), (W - W * sq * .5, 0 - 200 * e), (W, ya), (0, ya)]
    sb = .22 * (1 - e)
    qb = [(0, ya), (W, ya), (W - W * sb * .5, H + 200 * (1 - e)), (W * sb * .5, H + 200 * (1 - e))]
    fa = np.asarray(_persp(ia, qa)); fb = np.asarray(_persp(ib, qb))
    out = np.where((_YY < ya)[..., None], _shade(fa, 1 - .30 * e), _shade(fb, .70 + .30 * e))
    seam = np.exp(-np.abs(_YY - ya) / 10.0)[..., None] * 90 * math.sin(math.pi * p)
    return np.clip(out.astype(np.float32) + seam * np.array(acc, dtype=np.float32) / 160, 0, 255).astype(np.uint8)


def tr_zoom_through(A, B, p, acc):
    e = e_io(p)
    ia = _gblur(_zoom(Image.fromarray(A), 1 + 1.1 * e, W / 2, 760), 14 * e)
    ib = _gblur(_zoom(Image.fromarray(B), 1 + .45 * (1 - e), W / 2, 760), 10 * (1 - e))
    k = _sm((p - .3) / .4)
    return (np.asarray(ia).astype(np.float32) * (1 - k) + np.asarray(ib).astype(np.float32) * k).astype(np.uint8)


def tr_whip_h(A, B, p, acc):
    e = e_q(p)
    amt = 22 * math.sin(math.pi * p)
    ia = _hblur(Image.fromarray(A), amt); ib = _hblur(Image.fromarray(B), amt)
    off = int(W * e)
    out = np.empty_like(A)
    if off < W:
        out[:, :W - off] = np.asarray(ia)[:, off:]
    if off > 0:
        out[:, W - off:] = np.asarray(ib)[:, :off]
    return out


def tr_whip_v(A, B, p, acc):
    e = e_q(p)
    amt = 22 * math.sin(math.pi * p)
    ia = _vblur(Image.fromarray(A), amt); ib = _vblur(Image.fromarray(B), amt)
    off = int(H * e)
    out = np.empty_like(A)
    if off < H:
        out[:H - off] = np.asarray(ia)[off:]
    if off > 0:
        out[H - off:] = np.asarray(ib)[:off]
    return out


def tr_iris(A, B, p, acc):
    e = e_q(p)
    cx, cy = W / 2, 820
    r = 1260 * math.sqrt(e)                           # area grows with e_q (uniform coverage rate); 1226 px reaches the far corners
    dist = np.sqrt((_XX - cx) ** 2 + (_YY - cy) ** 2)
    m = _sm((r - dist) / 90.0 + .5)
    out = _mask_mix(A, B, m)
    ringm = np.exp(-((dist - r) ** 2) / (2 * 22.0 ** 2)) * math.sin(math.pi * p)
    return np.clip(out.astype(np.float32) + ringm[..., None] * np.array(acc, dtype=np.float32) * .9, 0, 255).astype(np.uint8)


def tr_slices(A, B, p, acc):
    out = B.copy()
    n = 7
    hgt = H // n + 1
    for i in range(n):
        y0, y1 = i * hgt, min(H, (i + 1) * hgt)
        q = e_io(cl((p - i * .06) / .64))
        off = int(W * q) * (1 if i % 2 == 0 else -1)
        if abs(off) >= W:
            continue
        if off >= 0:
            out[y0:y1, off:] = A[y0:y1, :W - off]
        else:
            out[y0:y1, :W + off] = A[y0:y1, -off:]
    return out


def tr_ink(A, B, p, acc):
    thr = -.12 + 1.24 * e_io(p)
    m = _sm((thr - _INK) / .10 + .5)
    out = _mask_mix(A, B, m)
    edge = np.exp(-((_INK - thr) ** 2) / (2 * .018 ** 2))
    return (out.astype(np.float32) * (1 - .45 * edge[..., None])).astype(np.uint8)


def tr_wedge(A, B, p, acc, t=0.0):
    yl, yr = wedge_ends(t)
    mslope = (yr - yl) / W
    s = _YY - mslope * _XX                            # distance field parallel to the seam
    Hb = H + abs(mslope) * W
    c = (Hb + 60) - (Hb + 120) * e_q(p)               # s spans [0, Hb]: the edge crosses the frame over the WHOLE duration
    m = _sm((s - c) / 110.0 + .5)                     # soft edge (110 px): a hard edge over a row of dark figures is a one-frame step
    out = _mask_mix(A, B, m)
    # soft leading band (gaussian, not a hard stripe): a hard 84 px stripe at ~170 px/frame was itself a motion step
    band = np.exp(-((s - c - 36.0) ** 2) / (2 * 26.0 ** 2)) * .55 * math.sin(math.pi * min(1.0, max(0.0, p))) ** .5
    tint = np.array(acc, dtype=np.float32) * .6 + np.array(PAPER, dtype=np.float32) * .4
    arr = out.astype(np.float32)
    arr = arr * (1 - band[..., None]) + tint * band[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


def tr_card_push(A, B, p, acc):
    """Card push, horizontal: B pushes A off to the left, a soft shadow rides the leading edge.
    (The first v2 build used a vertical push: B's dark top slid over A's bright paper and the frame
    mean dipped 18/frame — horizontal keeps both halves' dark/paper structure, so Δluma stays small.)"""
    e = e_io(p)
    ia = np.asarray(_zoom(Image.fromarray(_shade(A, 1 - .25 * e)), 1 - .05 * e))
    ib = np.asarray(_zoom(Image.fromarray(B), .94 + .06 * e))
    off = int(W * (1 - e))                                         # x where B starts
    out = np.empty_like(A)
    if off > 0:
        out[:, :off] = ia[:, W - off:]
    if off < W:
        out[:, off:] = ib[:, :W - off]
        left = max(0, off - 70)
        if off > left:
            ramp = np.linspace(.45, 1.0, off - left)[::-1]
            out[:, left:off] = (out[:, left:off].astype(np.float32) * (1 - .55 * (1 - ramp))[None, :, None]).astype(np.uint8)
    return out


def tr_spin(A, B, p, acc):
    e = e_io(p)
    ia = Image.fromarray(A).rotate(-7 * e, resample=Image.BILINEAR, fillcolor=DARK, center=(W / 2, 820))
    ia = _zoom(ia, 1 + .25 * e, W / 2, 820)
    ib = Image.fromarray(B).rotate(5 * (1 - e), resample=Image.BILINEAR, fillcolor=DARK, center=(W / 2, 820))
    ib = _zoom(ib, 1 + .18 * (1 - e), W / 2, 820)
    k = _sm((p - .25) / .5)
    return (np.asarray(ia).astype(np.float32) * (1 - k) + np.asarray(ib).astype(np.float32) * k).astype(np.uint8)


def tr_light_sweep(A, B, p, acc):
    k = e_q(p)
    out = A.astype(np.float32) * (1 - k) + B.astype(np.float32) * k
    s = (_XX + _YY * .55) / (W + H * .55)
    c = -.2 + 1.4 * e_q(p)
    beam = np.exp(-((s - c) ** 2) / (2 * .045 ** 2)) * 70 * math.sin(math.pi * p)
    return np.clip(out + beam[..., None], 0, 255).astype(np.uint8)


def tr_blur_dissolve(A, B, p, acc):
    e = e_io(p)
    ia = _gblur(_zoom(Image.fromarray(A), 1 + .07 * e), 9 * e)
    ib = _gblur(_zoom(Image.fromarray(B), 1.07 - .07 * e), 9 * (1 - e))
    k = _sm((p - .2) / .6)
    return (np.asarray(ia).astype(np.float32) * (1 - k) + np.asarray(ib).astype(np.float32) * k).astype(np.uint8)


def tr_doors(A, B, p, acc):
    e = e_q(p)
    ib = np.asarray(_zoom(Image.fromarray(B), 1.1 - .1 * e))
    out = ib.copy()
    half = W // 2
    off = int(half * e)
    if off < half:
        out[:, :half - off] = A[:, off:half]
        out[:, half + off:] = A[:, half:W - off]
    g = np.exp(-np.minimum(np.abs(_XX - (half - off)), np.abs(_XX - (half + off))) / 12.0) * 110 * math.sin(math.pi * p)
    return np.clip(out.astype(np.float32) + g[..., None] * np.array(acc, dtype=np.float32) / 170, 0, 255).astype(np.uint8)


_TILES = [(i, j) for j in range(12) for i in range(6)]
_TRND = np.random.RandomState(21).rand(len(_TILES), 3)


def tr_shatter(A, B, p, acc):
    base = Image.fromarray(B)
    ia = Image.fromarray(A)
    tw_, th_ = W // 6, H // 12
    cx0, cy0 = W / 2, 760
    for n, (i, j) in enumerate(_TILES):
        x0, y0 = i * tw_, j * th_
        dcx, dcy = x0 + tw_ / 2 - cx0, y0 + th_ / 2 - cy0
        dist = math.hypot(dcx, dcy) / 1200.0
        q = cl((p - dist * .45) / .55)
        if q >= 1:
            continue
        tile = ia.crop((x0, y0, x0 + tw_, y0 + th_)).convert('RGBA')
        if q > 0:
            e = q * q
            ang = (_TRND[n][0] - .5) * 90 * q
            tile = tile.rotate(ang, resample=Image.BILINEAR, expand=True)
            sc = 1 - .35 * q
            tile = tile.resize((max(2, int(tile.width * sc)), max(2, int(tile.height * sc))), Image.BILINEAR)
            dx = dcx * 1.6 * e + (_TRND[n][1] - .5) * 300 * e
            dy = dcy * 1.6 * e + 900 * e * e
            x0, y0 = x0 + dx - (tile.width - tw_) / 2, y0 + dy - (tile.height - th_) / 2
            tile.putalpha(tile.getchannel('A').point(lambda v, a=1 - q: int(v * a)))
        base.paste(tile, (int(x0), int(y0)), tile)
    return np.asarray(base)


TRANS = {'cube_h': tr_cube_h, 'cube_v': tr_cube_v, 'zoom': tr_zoom_through, 'whip_h': tr_whip_h, 'whip_v': tr_whip_v,
         'iris': tr_iris, 'slices': tr_slices, 'ink': tr_ink, 'wedge': tr_wedge, 'card': tr_card_push, 'spin': tr_spin,
         'sweep': tr_light_sweep, 'blur': tr_blur_dissolve, 'doors': tr_doors, 'shatter': tr_shatter}
# one per boundary (32), chosen by hand: chapter cuts get the big ones, phrase cuts the quick ones,
# the same kind never within 4 boundaries, the shatter sits on "ek tooti baat".
PLAN = (['zoom', 'whip_h', 'sweep', 'cube_h']            # S1: room>bowed>question>payoff | cut -> S2
        + ['blur', 'whip_v', 'iris', 'wedge']            # S2: nods>close nod>laugh>crowd | cut -> S3
        + ['zoom', 'doors']                              # S3: lift>ray+rules          | cut -> S4
        + ['spin', 'whip_h', 'slices', 'cube_v']         # S4: numeral>loud one>ring>room turns | cut -> S5
        + ['ink', 'blur', 'card']                        # S5: numeral>clock>pings     | cut -> S6
        + ['whip_v', 'zoom', 'iris']                     # S6: numeral>meter>stamp     | cut -> S7
        + ['sweep', 'whip_h', 'whip_v', 'slices', 'cube_h']  # S7: numeral>spine>walk>eyes>jism | cut -> S8
        + ['shatter', 'ink', 'wedge']                    # S8: numeral>break>scale     | cut -> S9
        + ['blur', 'card', 'doors', 'zoom'])             # S9: room>heads>flatline>carousel>endcard
assert len(PLAN) == len(BOUNDS), (len(PLAN), len(BOUNDS))
TD = {'cube_h': .60, 'cube_v': .60, 'zoom': .40, 'whip_h': .50, 'whip_v': .50, 'iris': .56, 'slices': .46, 'ink': .50,
      'wedge': .64, 'card': .50, 'spin': .46, 'sweep': .60, 'blur': .50, 'doors': .60, 'shatter': .70}


# ═══════════════════════════════════════════════ frame assembly
def shot_at(t):
    k = max(i for i, s in enumerate(SHOTS) if t >= s['t0'] - 1e-6)
    return k


def shot_frame(k, t, par):
    """One shot rendered as a full RGBA canvas (backdrop + layer + chrome), evaluated at absolute t
    (so neighbours continue naturally through a transition)."""
    s = SHOTS[k]
    si = s['si']
    lt = t - SCENE_START[si]
    u = t - s['t0']
    acc = ACC[si]
    cv = backdrop(t, si, acc)
    if s['kind'] == 'scene':
        lay = R.scene_img(si, max(0.0, lt), t, par)
    else:
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay, 'RGBA')
        s['payload'](d, max(0.0, u), si, acc, t, par, max(0.0, lt))
        # captions follow the voice in every shot
        for t0, t1, txt, hot in R.CAPS[si]:
            t0, t1 = t0 + LEAD[si], t1 + LEAD[si]
            if t0 <= lt < t1:
                words = txt.split()
                f = F(50, 600)
                wdt = sum(f.getlength(w) for w in words) + f.getlength(' ') * (len(words) - 1)
                caption_fit(d, words, (lt - t0) / (t1 - t0), acc, hot)
                break
    cv.alpha_composite(lay)
    d = ImageDraw.Draw(cv, 'RGBA')
    chrome(d, t, si, acc)
    return np.asarray(cv.convert('RGB'))


def render(i):
    t = i / FPS
    k = shot_at(t)
    si, lt = scene_at(t)
    dur = SCENE_END[si] - SCENE_START[si]
    z, px, py = camera(t, si, lt, dur)
    if ENH:
        z = z * (1.0 + _punch(t))
    par = (-px * .5, -py * .5)
    # transition window around the next / previous boundary
    arr = None
    for b_i, b in enumerate(BOUNDS):
        td = TD[PLAN[b_i]]
        if b - td / 2 <= t < b + td / 2:
            p = (t - (b - td / 2)) / td
            A = shot_frame(b_i, t, par)
            B = shot_frame(b_i + 1, t, par)
            fn = TRANS[PLAN[b_i]]
            acc = ACC[SHOTS[b_i + 1]['si']]
            arr = fn(A, B, p, acc, t) if PLAN[b_i] == 'wedge' else fn(A, B, p, acc)
            break
    if arr is None:
        arr = shot_frame(k, t, par)
    frame = Image.fromarray(arr)
    iz = 1.0 / z
    ox = (W - W * iz) * .5 + px
    oy = (H - H * iz) * .5 + py
    assert ox >= 0 and ox + W * iz <= W and oy >= 0 and oy + H * iz <= H, (i, z, px, py)
    frame = frame.transform((W, H), Image.AFFINE, (iz, 0, ox, 0, iz, oy), Image.BICUBIC)
    out = (_grade(np.asarray(frame)) if ENH else np.asarray(frame).astype(np.float32)) + R.C._GRAIN
    return np.clip(out, 0, 255).astype(np.uint8)


def shard(a, b, path):
    import imageio_ffmpeg, time
    FF = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [FF, '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(a, b):
        p.stdin.write(render(i).tobytes())
        if (i - a) % 50 == 49:
            el = time.time() - t0
            print(f'[{a}:{b}] {i - a + 1}/{b - a} {el:.0f}s eta {el / (i - a + 1) * (b - i - 1):.0f}s', flush=True)
    p.stdin.close()
    p.wait()
    assert p.returncode == 0, p.returncode


if __name__ == '__main__':
    os.makedirs('/home/user/build', exist_ok=True)
    if sys.argv[1] == 'still':
        t = float(sys.argv[2])
        Image.fromarray(render(int(round(t * FPS)))).save('/home/user/build/still_respect2.png')
    elif sys.argv[1] == 'shots':
        for i, s in enumerate(SHOTS):
            nm = s['payload'].__name__ if callable(s['payload']) else s['kind']
            print(f"{i:2d} S{s['si'] + 1} {s['t0']:7.3f}-{s['t1']:7.3f} {s['t1'] - s['t0']:5.2f}s {s['kind']:6s} {nm}"
                  + (f"  -> {PLAN[i]}" if i < len(PLAN) else ''))
    elif sys.argv[1] == 'contact':
        ts = [float(x) for x in sys.argv[2:]]
        cols = min(6, len(ts))
        rows = (len(ts) + cols - 1) // cols
        cw, ch = 270, 480
        sheet = Image.new('RGB', (cols * cw, rows * (ch + 26)), (20, 20, 22))
        dd = ImageDraw.Draw(sheet)
        for n, t in enumerate(ts):
            im = Image.fromarray(render(int(round(t * FPS)))).resize((cw, ch), Image.LANCZOS)
            x, y = (n % cols) * cw, (n // cols) * (ch + 26)
            sheet.paste(im, (x, y))
            dd.text((x + 6, y + ch + 6), f'{t:.2f}s', fill=(230, 230, 230))
        sheet.save('/home/user/build/contact_respect2.png')
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        shard(a, b, sys.argv[3])
