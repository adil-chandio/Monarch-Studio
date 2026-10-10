"""
respect.py — 90 s vertical short "LOG AAPKI IZZAT KYUN NAHI KARTE" (9 chapters).

Built ON power2.py (SHADE hero on the toon rig + hybrid charcoal/paper split + two-tone
slanted swipe + dissolve-under-wipe) and adds the cinematic layer the user asked for:

  * a ROOM: far-plane silhouettes (SHADE's own rig flattened to one tone, blurred for
    depth of field, cached per pose bucket), pulled with a 0.5x parallax against the pans
  * a DOLLY: the world (hero + room + props) scales about the floor line while the UI
    stays, so the push-ins go past the camera's safe-area ceiling without moving text
  * a LIGHT SHAFT with dust motes that live only in the dark half, a slow-motion TURN
    (head lift + eye ignition + wedge flood), floor reflections, particle blow-aways
  * the wedge offset is a continuous function of t across every cut (a 160 px jump under
    the band would be a 15-luma step), eased inside the receiving scene instead

Everything is a pure function of t; shards are bit-identical.  CLI:
  respect.py A B out.mp4   render frames [A, B)      respect.py still T    one PNG
  respect.py contact t1 t2 ...                        build/contact_respect.png
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toon as T
import clean as C
import shade as S
import hybrid as HY
import power as PW
import power2 as P2
from clean import (W, H, FPS, PAPER, PAPER_D, SOFT, INK, GY, PAY_Y,
                   cl, fl, e_out, e_io, e_back, F, tw, line, fbox, fcirc, fpoly, stroke,
                   tickmark, shadow, payoff, phys)
from power import (mix, blend, p_power, p_calm, p_flinch, glance, ring, cross, caption_fit,
                   TDUR, TLAG, RED)
from power2 import hero, on_paper, wedge_ends, wedge_y, backdrop, pulse, glow_tick, swipe, MARGIN
import timeline_respect as TL
from timeline_respect import SCENE_START, SCENE_END, DUR_TOTAL, VO_AT, NAMES, LEAD, PHRASES

DARK, POD = HY.DARK, HY.PAPER_ON_DARK
NF = int(round(DUR_TOTAL * FPS))
CUTS = list(TL.CUTS)
CHAPTER = NAMES
OUT_DEFAULT = '/home/user/shade_respect_90s.mp4'

# ───────────────────────────────────────────── palette (9 chapters)
ACC = [(178, 44, 32),      # 1 hook       coral
       (104, 78, 150),     # 2 villain    dusty violet
       (146, 100, 12),     # 3 turn       gold
       (28, 82, 190),      # 4 kam bolo   blue
       (14, 112, 80),      # 5 waqt       emerald
       (168, 30, 58),      # 6 na         crimson
       (86, 54, 194),      # 7 kamar      violet
       (166, 74, 14),      # 8 lafz       amber
       (146, 100, 12)]     # 9 payoff     gold (the earned colour closes the loop)
ACC_HI = [tuple(min(255, int(c * 1.34 + 22)) for c in a) for a in ACC]
HY.HOT = [HY._lighten_to(a, DARK) for a in ACC_HI]      # hot words on the dark, >= 4.8:1
P2.ACC = ACC                                           # swipe() reads the next accent from here


# ───────────────────────────────────────────── timeline hooks into power2
def scene_at(t):
    si = max(k for k in range(9) if t >= SCENE_START[k])
    return si, t - SCENE_START[si]


def wedge_drop(t):
    """Continuous across cuts: every scene starts where the previous one ended."""
    si, lt = scene_at(t)
    if si == 0:                                   # the dim room
        return 260.0 + 6.0 * math.sin(t * .9)
    if si == 1:                                   # the same dim room (the pile needs the paper; measured)
        return 260.0
    if si == 2:                                   # the turn: light floods as the eyes ignite
        return 260.0 - 420.0 * e_io(cl((lt - .6) / 2.0))
    if si == 3:                                   # settle to the resting split
        return -160.0 * (1 - e_io(cl(lt / 1.2)))
    if si == 5:                                   # the NA stamp: the dark flinches once
        u = cl((lt - (LEAD[5] + 5.23)) / .55)
        return -56.0 * math.sin(math.pi * u)
    if si == 8:                                   # the lit room
        return -210.0 * e_io(cl((lt - 1.0) / 3.0))
    return 0.0


P2.scene_at = scene_at
P2.wedge_drop = wedge_drop


def chrome(d, t, si, acc):
    y = 142
    d.rounded_rectangle([64, y - 3, W - 64, y + 3], 3, fill=HY.CHROME_TRACK)
    fxp = 64 + (W - 128) * cl(t / DUR_TOTAL)
    hi = HY.hot(si)
    d.rounded_rectangle([64, y - 3, fxp, y + 3], 3, fill=hi)
    d.ellipse([fxp - 9, y - 9, fxp + 9, y + 9], fill=hi)
    d.text((64, 198), f'{si + 1:02d}', font=F(34, 800), fill=hi, anchor='lm')
    d.text((108, 199), f'/ 09   {CHAPTER[si]}', font=F(26, 600), fill=(168, 164, 158), anchor='lm')


# ───────────────────────────────────────────── camera (v9 rig, 9 scenes) + dolly
Z0 = 1.020
AMP = (.022, .016, .020, .016, .020, .016, .020, .016, .022)


def _tri(x):
    return 4 * abs(x - math.floor(x + .5)) - 1


def camera(t, si, lt, dur):
    u = cl(lt / dur)
    ramp = .15 * e_io(u) + .85 * u
    if si % 2: ramp = 1.0 - ramp
    z = Z0 + AMP[si] * ramp + math.exp(-lt * 6.4) * math.sin(lt * 16.5) * .0040
    px = 7.0 * _tri(t / 9.0)
    py = 9.0 * _tri(t / 13.0 + .37)
    return z, px, py


def dolly(si, lt):
    """World scale about (W/2, GY): the push-ins the camera's safe area cannot give."""
    if si == 0:
        return .930 + .070 * (.2 * e_io(cl(lt / 9.0)) + .8 * cl(lt / 9.0))
    if si == 2:
        return 1.0 + .060 * cl((lt - .6) / 6.0)
    if si == 8:
        return .920 + .080 * cl(lt / 8.0)
    return 1.0


def wx(x, k):
    return W / 2 + (x - W / 2) * k


# ───────────────────────────────────────────── cinematic primitives
def paste_rgba(base, sp, x, y):
    """alpha_composite with a negative-safe destination."""
    x, y = int(x), int(y)
    sx = sy = 0
    if x < 0: sx, x = -x, 0
    if y < 0: sy, y = -y, 0
    if sx or sy:
        sp = sp.crop((sx, sy, sp.width, sp.height))
    if sp.width <= 0 or sp.height <= 0 or x >= base.width or y >= base.height:
        return
    base.alpha_composite(sp, (x, y))


_SIL = {}
_SIL_MAX = 72                                    # ~1 MB per sprite: the cache stays under ~80 MB per shard
SIL_TONE = (96, 92, 100)


def sil_sprite(fig, pose_fn, s, head_t, bucket, blur, flip):
    """Cached far-plane sprite (full alpha). Keys are quantised upstream so a dolly or a
    slow head lift cannot grow the cache without bound (ledger 52)."""
    key = (fig, s, head_t, bucket, blur, flip)
    sp = _SIL.get(key)
    if sp is not None:
        return sp
    tw_, th_ = int(1.84 * s) + 4, int(1.50 * s) + 4
    tile = Image.new('RGBA', (tw_, th_), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile, 'RGBA')
    pose = dict(pose_fn(bucket / 6.0))
    pose['head_t'] = pose.get('head_t', 0) + head_t
    S.shade(td, 0.92 * s, 1.30 * s, s, pose, 'neutral', glow=0.0, blink=1.0, flip=flip)
    sp = Image.new('RGBA', tile.size, SIL_TONE + (0,))
    sp.putalpha(tile.getchannel('A'))
    if blur:
        sp = sp.filter(ImageFilter.GaussianBlur(blur))
    while len(_SIL) >= _SIL_MAX:
        _SIL.pop(next(iter(_SIL)))
    _SIL[key] = sp
    return sp


def silhouette(d, x, s, fig, pose_fn, lt, head_t=0, blur=3, alpha=.72, flip=False, eyes=0.0, par=(0, 0)):
    """A far-plane figure: SHADE's rig flattened to one tone, cached per 1/6 s pose
    bucket (the breathing loops every 2 s), blurred for depth of field. The sprite is built
    at a size quantised to 16 px and resampled to the exact size; head angles are quantised
    to 2 degrees; alpha is applied at paste time, so none of them multiplies the cache."""
    bucket = int(lt * 6) % 12
    sq = max(48, int(round(s / 16.0)) * 16)
    sp = sil_sprite(fig, pose_fn, sq, int(round(head_t / 2.0)) * 2, bucket, blur, flip)
    if sq != int(s):
        f = s / sq
        sp = sp.resize((max(1, int(sp.width * f)), max(1, int(sp.height * f))), Image.BILINEAR)
    if alpha < .999:
        sp = sp.copy()
        sp.putalpha(sp.getchannel('A').point(lambda v: int(v * alpha)))
    x = x + par[0]
    y = GY + par[1]
    shadow(d, x, y + 6, s * .15, int(40 * alpha), 0)
    paste_rgba(d._image, sp, x - 0.92 * s, y - 1.30 * s)
    if eyes > 0:                                   # they notice him: two pale points
        hy = y - s * (1 - 1 / S.SP['head_c'] if 'head_c' in S.SP else .905)
        ex = x + (s * .02 if not flip else -s * .02)
        for sx in (-1, 1):
            r = 3.2 * eyes
            d.ellipse([ex + sx * s * .034 - r, hy - r, ex + sx * s * .034 + r, hy + r],
                      fill=S.GLOW_C + (int(200 * eyes),))


def shaft(d, t, cx, spread, alpha, col=(250, 246, 236)):
    """A soft light shaft from the top edge; quarter-res blur, so it costs ~6 ms."""
    if alpha <= 0:
        return
    lay = Image.new('RGBA', (W // 4, H // 4), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    sway = 26 * math.sin(t * .37)
    pts = [((cx + sway) / 4 - 12, -8), ((cx + sway) / 4 + 12, -8),
           ((cx + spread + sway * .4) / 4, H / 4 + 8), ((cx - spread + sway * .4) / 4, H / 4 + 8)]
    ld.polygon(pts, fill=col + (int(alpha),))
    lay = lay.filter(ImageFilter.GaussianBlur(16)).resize((W, H), Image.BILINEAR)
    d._image.alpha_composite(lay)


_MOTES = np.random.RandomState(7).rand(44, 5)


def dust(d, t, x0, x1, y0, y1, alpha=150, col=(236, 232, 228), par=(0, 0)):
    """Dust in the dark half only (the paper half has no air to catch the light)."""
    for m in _MOTES:
        x = x0 + (x1 - x0) * ((m[0] + .010 * t * math.sin(m[3] * 6.28 + t * .3)) % 1.0) + par[0]
        y = y0 + (y1 - y0) * ((m[1] - .016 * t * (0.5 + m[2])) % 1.0) + par[1]
        if y > wedge_y(x, t) - 26:
            continue
        r = 1.4 + 2.4 * m[4]
        a = alpha * (0.40 + 0.60 * abs(math.sin(t * 1.7 + m[3] * 7)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (int(a),))


def hero_layer(lt, x, s, pose, ex, reflect=0.0, **kw):
    """Draw the hero on his own layer so he can be reflected on the floor."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay, 'RGBA')
    j = hero(ld, lt, x, s, pose, ex, **kw)
    if reflect > 0:
        top = int(GY - s * 1.12)
        band = lay.crop((0, top, W, GY)).transpose(Image.FLIP_TOP_BOTTOM)
        hgt = 112
        band = band.crop((0, 0, W, hgt)).filter(ImageFilter.GaussianBlur(2.2))
        grad = Image.linear_gradient('L').resize((W, hgt)).transpose(Image.FLIP_TOP_BOTTOM)
        a = band.getchannel('A')
        a = Image.fromarray((np.asarray(a).astype(np.float32) * np.asarray(grad).astype(np.float32)
                             / 255 * reflect).astype(np.uint8))
        band.putalpha(a)
        lay.alpha_composite(band, (0, GY + 2))
    return lay, j


def card(d, x, y, txt, acc, p=1.0, sz=26, w=None, rot=0.0, alpha=255):
    """A paper tag: readable on both halves (paper face, ink outline + ink text)."""
    if p <= 0:
        return
    k = e_back(cl(p), 1.5)
    f = F(sz, 800)
    w = w or (f.getlength(txt) + 36)
    h = sz + 26
    hw, hh = w / 2 * k, h / 2 * k
    if rot:
        c, s_ = math.cos(rot), math.sin(rot)
        pts = [(x + c * dx - s_ * dy, y + s_ * dx + c * dy) for dx, dy in
               ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
        d.polygon(pts, fill=PAPER_D + (alpha,), outline=INK + (alpha,), width=4)
    else:
        d.rounded_rectangle([x - hw, y - hh, x + hw, y + hh], 10, fill=PAPER_D + (alpha,),
                            outline=INK + (alpha,), width=4)
    if k > .6:
        d.text((x, y + 1), txt, font=F(int(sz * min(1, k)), 800), fill=acc + (alpha,), anchor='mm')


def pill(d, x, y, txt, acc, p):
    if p <= 0:
        return
    k = e_back(cl(p), 1.4)
    f = F(32, 800)
    w = (f.getlength(txt) + 96) * k
    h = 74 * k
    d.rounded_rectangle([x - w / 2 + 6, y - h / 2 + 8, x + w / 2 + 6, y + h / 2 + 8], h / 2,
                        fill=(0, 0, 0, 40))
    d.rounded_rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], h / 2, fill=acc)
    if k > .5:
        d.text((x, y + 1), txt, font=f, fill=PAPER, anchor='mm')
    # bookmark tab
    bx = x + w / 2 + 34
    d.polygon([(bx - 14, y - 28), (bx + 14, y - 28), (bx + 14, y + 28), (bx, y + 14), (bx - 14, y + 28)],
              fill=INK)


# ───────────────────────────────────────────── the room (S1 + S9 share it)
ROOM = [  # x, size, pose, flip, blur
    (150, 340, T.p_idle, False, 5),
    (330, 300, T.p_think, True, 6),
    (590, 290, T.p_idle, True, 6),
    (905, 330, T.p_think, False, 5),
    (1000, 380, S.p_pocket_both, True, 4),
]


def room(d, lt, t, k, par, heads, eyes=None, skip=()):
    for i, (x, s, pf, flip, blur) in enumerate(ROOM):
        if i in skip:
            continue
        silhouette(d, wx(x, k), s * k, i, pf, lt + i * .37, head_t=heads[i], blur=blur, flip=flip,
                   eyes=(eyes[i] if eyes else 0.0), par=par)


# ───────────────────────────────────────────── captions (clip-local; LEAD added in scene_img)
CAPS = [
    [(0.00, 1.25, 'KAMRE MEIN AATE HO', {0}), (1.33, 2.80, 'KOI SAR NAHI UTHATA', {0}),
     (2.88, 4.90, 'LOG AAPKI IZZAT KYUN NAHI KARTE?', {2})],
    [(0.00, 2.40, 'AAP SAB KO KHUSH KARNA CHAHTE HO', {3}), (2.50, 3.90, 'HAR BAAT PAR HAAN', {3}),
     (3.99, 5.50, 'HAR MAZAAK PAR HANSI', {3}), (5.59, 6.60, 'JO SAB KA HAI', {1})],
    [(0.00, 1.60, 'IZZAT MAANGI NAHI JAATI', {1}), (1.70, 2.55, 'KAMAI JAATI HAI', {0}),
     (2.63, 3.45, 'PAANCH RULES', {0})],
    [(0.00, 1.68, 'RULE 1 KAM BOLO', {2}), (1.77, 5.20, 'JO HAR WAQT BOLTA HAI USKI BAAT SASTI', {5}),
     (6.16, 7.10, 'SAHI WAQT PAR', {0}), (7.22, 9.40, 'POORA KAMRA SUNTA HAI', {0})],
    [(0.00, 2.42, 'RULE 2 APNA WAQT MEHNGA KARO', {3}), (2.52, 4.10, 'JO HAR WAQT AVAILABLE HAI', {3}),
     (4.22, 5.70, 'WOH KABHI ZAROORI NAHI LAGTA', {2})],
    [(0.00, 2.20, 'RULE 3 NA KEHNA SEEKHO', {2}), (2.31, 5.10, 'HAR HAAN KI KEEMAT IZZAT SE KATTI HAI', {5}),
     (5.23, 6.35, 'EK SAAF NA', {2})],
    [(0.00, 1.90, 'RULE 4 KHUD KO SAMBHALO', {3}), (2.01, 2.90, 'SEEDHI KAMAR', {0}),
     (3.01, 3.85, 'DHEEMI CHAAL', {0}), (3.95, 5.05, 'NAZAR AANKHON MEIN', {0}),
     (6.69, 8.70, 'ZUBAAN BAAD MEIN', {0})],
    [(0.00, 2.55, 'RULE 5 JO KAHO WOH KARO', {2}), (2.65, 5.70, 'EK TOOTI BAAT SAU SACH MAAR DETI HAI', {1})],
    [(0.00, 1.15, 'AB WAHI KAMRA', {2}), (1.25, 2.52, 'AAP ANDAR AATE HO', {0}),
     (2.62, 4.00, 'AUR SAB SAR UTHATE HAIN', {2}), (4.13, 5.64, 'IZZAT SHOR NAHI', {1}),
     (5.74, 6.67, 'KHAMOSHI HAI', {0}), (6.77, 8.26, 'PAANCH RULES AAJ SE', {0}),
     (8.36, 10.16, 'FOLLOW KARO AUR SAVE KARO', {0, 3}), (10.26, 12.40, 'KAL PHIR DEKHNA PADEGA', {0})],
]


def payoff_fit(d, words, p, acc, hot):
    """clean.payoff with a measured fit: the line never exceeds W - 120 px."""
    if p <= 0:
        return
    f = F(84, 800)
    wdt = sum(f.getlength(w) for w in words) + f.getlength(' ') * (len(words) - 1)
    sz = 84 if wdt <= W - 120 else max(56, int(84 * (W - 120) / wdt))
    line(d, words, W / 2, PAY_Y, sz, 800, INK, hot, acc, p, 28)


def vt(si, k):
    """Scene-local time of phrase k of this scene's VO clip."""
    return LEAD[si] + PHRASES[si][k]


# ───────────────────────────────────────────── 1  HOOK  — the room ignores him
def s1(d, lt, acc, t, par):
    k = dolly(0, lt)
    heads = [12, 10, 13, 9, 11]
    room(d, lt, t, k, par, heads)
    shaft(d, t, 880, 340, 34)
    dust(d, t, 300, 1060, 120, 1200, 130, par=par)
    # SHADE at the door, right, far; pocket stance; eyes open in the dark 0.3-0.8
    hx, hs = wx(760, k), 470 * k
    pose = dict(phys(S.p_pocket, lt))
    if vt(0, 1) < lt < vt(0, 1) + 1.2:                        # "koi sar nahi uthata": he looks around
        u = (lt - vt(0, 1)) / 1.2
        pose['head'] = pose['head'] - 14 * math.sin(u * math.pi)
    eo = e_out(cl((lt - .30) / .50), 2.0)
    glow = .25 + .55 * eo + .30 * pulse(lt, vt(0, 3), .8)
    ex = 'neutral' if lt < vt(0, 2) else 'determined'
    lk = glance(lt, vt(0, 1), 1.3, -1.0, .15)
    hero(d, lt, hx, hs, pose, ex, look=lk, glow=glow, blink=(1 - eo) if lt < .9 else None)
    HY.headline(d, ['IZZAT'], W / 2, 318, 124, {0}, 0, cl((lt - vt(0, 2)) / .60), 46)
    HY.headline(d, ['KYUN', 'NAHI?'], W / 2, 436, 96, None, 0, cl((lt - vt(0, 2) - .18) / .60), 42)
    payoff(d, ['JAWAB', 'KADWA', 'HAI'], cl((lt - vt(0, 3)) / .55), acc, {1})


# ───────────────────────────────────────────── 2  VILLAIN — he nods to everyone, HAAN tags pile up
HAAN_T = [2.50, 3.05, 3.55, 3.99, 4.40, 4.85, 5.20]           # clip-local spawn times


def s2(d, lt, acc, t, par):
    HY.headline(d, ['SAB', 'KO', 'KHUSH'], W / 2, 348, 112, {2}, 1, cl(lt / .55), 42)
    # three listeners on the right, closer than the room (less blur)
    for i, (x, s, pf, flip, blur) in enumerate(((850, 400, T.p_idle, True, 3), (1010, 440, T.p_think, True, 2),
                                                 (690, 330, T.p_idle, True, 4))):
        silhouette(d, x, s, 10 + i, pf, lt + i * .5, head_t=-2, blur=blur, flip=flip, par=par)
    dust(d, t, 100, 700, 120, 900, 90, par=par)
    hx, hs = 400, 540
    pose = dict(phys(S.p_pocket, lt))
    nod = 0.0
    for k_, ht in enumerate(HAAN_T):                           # a nod per HAAN
        u = (lt - LEAD[1] - ht + .25) / .45
        if 0 < u < 1:
            nod = math.sin(u * math.pi) * 9
    pose['head_t'] = pose.get('head_t', 0) + nod
    pose['yaw'] = pose['yaw'] - 12                               # turned to them
    grey = cl((lt - vt(1, 1)) / 4.0)                             # the glow drains as he pleases
    glow = (1.0 - .62 * grey) + .12 * nod / 9
    ex = 'sly' if lt < vt(1, 3) else 'neutral'
    hero(d, lt, hx, hs, pose, ex, look=(.8, .1), glow=glow)
    # HAAN tags: born at his head, float to the pile at the lower right
    for n, ht in enumerate(HAAN_T):
        u = cl((lt - LEAD[1] - ht) / .9)
        if u <= 0:
            continue
        x0, y0 = hx + 40, GY - hs * .92
        px_, py_ = 760 + (n % 3) * 96, 1200 - (n // 3) * 60
        e = e_io(u)
        x = x0 + (px_ - x0) * e
        y = y0 + (py_ - y0) * e - 120 * math.sin(math.pi * u)
        rot = (1 - u) * .5 * (1 if n % 2 else -1) + (.06 if n % 2 else -.06)
        if u >= 1:
            on_paper(x - 60, y - 26, t, 'haan tag')
        card(d, x, y, 'HAAN', acc, min(1, u * 3), 26, 118, rot)
    payoff(d, ['KISI', 'KA', 'NAHI'], cl((lt - vt(1, 4)) / .55), acc, {2})


# ───────────────────────────────────────────── 3  TURN  — slow motion: the head lifts, the eyes ignite
def s3(d, lt, acc, t, par):
    k = dolly(2, lt)
    u = e_io(cl((lt - .6) / 2.0))                                # the turn itself
    shaft(d, t, 560, 420, 20 + 44 * u)
    dust(d, t, 120, 980, 120, 1100, 90 + 90 * u, par=par)
    hx, hs = W / 2, 600 * k
    pose = mix(phys(T.p_sad, lt), phys(p_power, lt), u)
    glow = .25 + 1.15 * u + .45 * pulse(lt, vt(2, 1), .9) + .25 * pulse(lt, vt(2, 3), .6)
    ex = 'neutral' if u < .5 else ('determined' if lt < vt(2, 2) else 'proud')
    blink = (1 - e_out(cl((lt - .9) / 1.1), 2.0)) if lt < 2.2 else None
    lay, _ = hero_layer(lt, hx, hs, pose, ex, reflect=.14 * u, glow=glow, blink=blink)
    d._image.alpha_composite(lay)
    # a ray crosses the seam on "kamai"
    rp = cl((lt - vt(2, 1)) / 1.1)
    if 0 < rp < 1:
        yl, yr = wedge_ends(t)
        x = -200 + 1480 * e_io(rp)
        y = yl + (yr - yl) * (x / W)
        for rr, aa in ((90, 22), (54, 40), (26, 70)):
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=S.GLOW_C + (int(aa * math.sin(math.pi * rp)),))
    HY.headline(d, ['IZZAT'], W / 2, 318, 118, None, 2, cl((lt - .2) / .60), 46)
    HY.headline(d, ['KAMAI', 'JAATI', 'HAI'], W / 2, 432, 84, {0}, 2, cl((lt - vt(2, 1) + .1) / .60), 42)
    # five chips in the dark under the headline: "paanch rules"
    for i in range(5):
        q = cl((lt - vt(2, 2) - i * .11) / .45)
        if q > 0:
            glow_tick(d, 300 + i * 120, 560, q, pulse(lt, vt(2, 3), .8), acc)
    payoff_fit(d, ['5', 'RULES', 'AAJ', 'SE'], cl((lt - vt(2, 3)) / .55), acc, {0, 2, 3})


# ───────────────────────────────────────────── 4  RULE 1 — kam bolo
def s4(d, lt, acc, t, par):
    HY.headline(d, ['KAM', 'BOLO'], W / 2, 348, 124, {0}, 3, cl(lt / .55), 42)
    # the loud one: left, sharp-ish, word bubbles rising and dying
    silhouette(d, 250, 430, 20, T.p_present, lt, head_t=-4, blur=1.5, alpha=.80, par=par)
    talk0, talk1 = vt(3, 2), vt(3, 4)
    if talk0 - .3 < lt < talk1 + .6:
        for n in range(9):
            u = ((lt - talk0) / 1.6 + n * .173) % 1.0
            if not (talk0 <= lt <= talk1 + .4):
                continue
            x = 300 + 70 * math.sin(n * 2.1) + 150 * u
            y = GY - 430 * .98 - 30 - 230 * u
            r = (30 + 14 * math.sin(n * 1.7)) * (1 - u) ** 1.2
            if r > 3:
                a = int(210 * (1 - u) ** .5)
                d.ellipse([x - r, y - r, x + r, y + r], fill=PAPER_D + (a,), outline=INK + (a,), width=3)
                if r > 14:
                    for q in range(3):
                        d.ellipse([x - 14 + q * 12, y - 3, x - 8 + q * 12, y + 3], fill=SOFT + (a,))
    dust(d, t, 100, 1000, 120, 900, 80, par=par)
    # SHADE: arms crossed, silent; "ek jumla": one open hand, one bold bubble
    hx, hs = 720, 540
    j1 = vt(3, 4)
    pose = blend(S.p_arms_cross, T.p_present, lt, j1, .6, 1.12) if lt >= j1 - .05 else phys(S.p_arms_cross, lt)
    if lt > j1 + 1.9:
        pose = blend(T.p_present, S.p_arms_cross, lt, j1 + 1.9, .7, 1.05)
    glow = .85 + .35 * pulse(lt, j1, .8) + .25 * pulse(lt, vt(3, 6), .8)
    ex = 'sly' if lt < vt(3, 2) else ('determined' if lt < j1 else 'proud')
    hero(d, lt, hx, hs, pose, ex, look=(-.7, .05) if lt < j1 else (0, 0), glow=glow)
    bp = cl((lt - j1 - .15) / .4)
    if bp > 0:
        k = e_back(bp, 1.5)
        bx, by = 760, GY - hs * 1.04 - 90
        bw, bh = 190 * k, 86 * k
        d.rounded_rectangle([bx - bw, by - bh, bx + bw, by + bh], 26, fill=PAPER_D, outline=INK, width=5)
        d.polygon([(bx - 60, by + bh - 2), (bx - 20, by + bh - 2), (bx - 70, by + bh + 40)], fill=PAPER_D, outline=INK)
        d.rounded_rectangle([bx - bw * .62, by - 12, bx + bw * .62, by + 12], 8, fill=acc)
    # "poora kamra sunta hai": two listeners lean in at the right edge
    lp = cl((lt - vt(3, 6)) / .7)
    if lp > 0:
        silhouette(d, 1040 + 40 * (1 - e_io(lp)), 360, 21, T.p_idle, lt, head_t=-6, blur=4, alpha=.7 * lp, flip=True, par=par)
    payoff(d, ['EK', 'JUMLA'], cl((lt - j1) / .55), acc, {0})


# ───────────────────────────────────────────── 5  RULE 2 — apna waqt mehnga karo
def s5(d, lt, acc, t, par):
    HY.headline(d, ['WAQT', 'MEHNGA'], W / 2, 348, 116, {1}, 4, cl(lt / .55), 42)
    # far clock, parallax 0.5x: a faint ring with a slow hand
    cx, cy = 820 + par[0] * 2, 760 + par[1] * 2
    d.ellipse([cx - 230, cy - 230, cx + 230, cy + 230], outline=(150, 146, 150, 70), width=10)
    ang = -math.pi / 2 + lt * .55
    d.line([(cx, cy), (cx + 190 * math.cos(ang), cy + 190 * math.sin(ang))], fill=(150, 146, 150, 90), width=8)
    dust(d, t, 100, 1000, 120, 900, 80, par=par)
    hx, hs = 400, 540
    pose = dict(phys(S.p_pocket, lt))
    buzz0, buzz1 = vt(4, 3), vt(4, 4) + .9
    buzzing = buzz0 <= lt < buzz1
    # he only glances at the phone, then back to the lens
    lk = glance(lt, buzz0 + .15, 1.4, .35, .9)
    glow = .95 + .30 * pulse(lt, vt(4, 5), .8)
    ex = 'sly' if lt < buzz0 else ('determined' if lt < vt(4, 5) else 'proud')
    hero(d, lt, hx, hs, pose, ex, look=lk, glow=glow)
    # the phone at the right hip
    px_, py_ = hx + hs * .17, GY - hs * .50
    sh = (math.sin(lt * 70) * 4) if buzzing else 0
    d.rounded_rectangle([px_ - 24 + sh, py_ - 46, px_ + 24 + sh, py_ + 46], 9, fill=(22, 22, 26), outline=(70, 70, 78), width=3)
    scr = S.GLOW_T if buzzing else (40, 40, 48)
    d.rounded_rectangle([px_ - 17 + sh, py_ - 38, px_ + 17 + sh, py_ + 32], 5, fill=scr)
    if buzzing:
        for n in range(1, 4):
            a = int(160 * (0.5 + 0.5 * math.sin(lt * 14 - n)))
            d.arc([px_ - 30 - n * 16 + sh, py_ - 46 - n * 16, px_ + 30 + n * 16 + sh, py_ + 46 + n * 16],
                  200, 340, fill=acc + (a,), width=4)
    # the price of the hour climbs: a paper tag with a bar
    tp_ = cl((lt - vt(4, 1)) / .5)
    if tp_ > 0:
        bx, by = 840, 1050
        on_paper(bx - 150, by - 60, t, 'waqt tag')
        card(d, bx, by - 20, '1 GHANTA', acc, tp_, 28, 300)
        bar = cl((lt - vt(4, 2)) / 3.4)
        d.rounded_rectangle([bx - 130, by + 34, bx + 130, by + 58], 8, fill=PAPER_D, outline=INK, width=4)
        if bar > 0:
            d.rounded_rectangle([bx - 126, by + 38, bx - 126 + 252 * e_out(bar, 2.0), by + 54], 6, fill=acc)
    payoff(d, ['APNI', 'MARZI', 'SE'], cl((lt - vt(4, 5)) / .55), acc, {1})


# ───────────────────────────────────────────── 6  RULE 3 — na kaho
_WIND = np.random.RandomState(3).rand(6, 3)


def s6(d, lt, acc, t, par):
    HY.headline(d, ['NA', 'KAHO'], W / 2, 348, 124, {0}, 5, cl(lt / .55), 42)
    dust(d, t, 100, 1000, 120, 900, 80, par=par)
    st = vt(5, 3)                                                # the stamp
    # a pile of HAAN tags (already paid for), blown away by the stamp
    for n in range(6):
        px_, py_ = 300 + (n % 3) * 104 + (n // 3) * 30, 1140 - (n // 3) * 66
        q = cl((lt - vt(5, 2) - n * .12) / .4)
        if q <= 0:
            continue
        fx, fy, rot, al = px_, py_, (.05 if n % 2 else -.05), 255
        if lt > st + .08:
            w = (lt - st - .08)
            fx = px_ + (260 + 320 * _WIND[n][0]) * w + 60 * w * w
            fy = py_ - (120 + 260 * _WIND[n][1]) * w + 420 * w * w
            rot = rot + (2.5 + 3 * _WIND[n][2]) * w
            al = int(255 * (1 - cl(w / 1.1)))
        if al <= 0:
            continue
        if lt <= st + .08:
            on_paper(fx - 52, fy - 26, t, 'haan pile')
        card(d, fx, fy, 'HAAN', (120, 112, 118), q, 24, 104, rot, al)
    # SHADE: right, the open palm says it
    hx, hs = 730, 540
    pose = blend(S.p_pocket, p_flinch, lt, st - .25, .5, 1.1) if lt > st - .3 else phys(S.p_pocket, lt)
    if lt > st + 1.3:
        pose = blend(p_flinch, p_power, lt, st + 1.3, .7, 1.1)
    glow = .9 + .45 * pulse(lt, st, .7)
    ex = 'determined' if lt < st + 1.3 else 'proud'
    hero(d, lt, hx, hs, pose, ex, glow=glow)
    sp = cl((lt - st) / .32)
    if sp > 0:                                                   # the NA stamp slams
        k = 1.6 - .6 * e_out(sp, 3.0)
        sx, sy = 470, 1040
        if sp >= 1:                                              # resting stamp sits on paper (slam frames cross the seam by design)
            on_paper(sx - 150, sy - 70, t, 'na stamp')
        d.rounded_rectangle([sx - 140 * k, sy - 62 * k, sx + 140 * k, sy + 62 * k], 18, outline=acc, width=int(12 * k))
        d.text((sx, sy + 4), 'NA', font=F(int(78 * k), 800), fill=acc, anchor='mm')
        if sp >= 1 and lt < st + .9:                             # impact dust
            w = (lt - st - .32) / .58
            for n in range(10):
                a = n * .628
                r = 40 + 170 * e_out(w, 2.0)
                rr = 5 * (1 - w)
                d.ellipse([sx + r * math.cos(a) - rr, sy + 62 + r * math.sin(a) * .35 - rr,
                           sx + r * math.cos(a) + rr, sy + 62 + r * math.sin(a) * .35 + rr], fill=acc + (int(200 * (1 - w)),))
    # "bina safai ke": the excuse bubble, struck through
    ep = cl((lt - vt(5, 4)) / .4)
    if ep > 0:
        k = e_back(ep, 1.4)
        bx, by = 430, 1150
        on_paper(bx - 110, by - 34, t, 'excuse bubble')
        d.rounded_rectangle([bx - 108 * k, by - 32 * k, bx + 108 * k, by + 32 * k], 22, fill=PAPER_D, outline=INK, width=4)
        for i in range(3):
            d.ellipse([bx - 36 + i * 36 - 7, by - 7, bx - 36 + i * 36 + 7, by + 7], fill=SOFT)
        cross(d, bx, by, 60, acc, cl((lt - vt(5, 4) - .3) / .3), 10)
    payoff(d, ['BINA', 'SAFAI', 'KE'], cl((lt - vt(5, 4)) / .55), acc, {0})


# ───────────────────────────────────────────── 7  RULE 4 — kamar seedhi, dheemi chaal, nazar
def s7(d, lt, acc, t, par):
    HY.headline(d, ['KAMAR', 'SEEDHI'], W / 2, 348, 116, {1}, 6, cl(lt / .55), 42)
    dust(d, t, 100, 1000, 120, 900, 80, par=par)
    t_sp, t_wk, t_eye = vt(6, 2), vt(6, 3), vt(6, 4)
    # position: slumped at the left, the slow walk carries him to the right third
    wk = cl((lt - t_wk) / 1.9)
    hx = 330 + 380 * e_io(wk)
    hs = 540
    if lt < t_sp:
        pose = phys(T.p_sad, lt)
    elif lt < t_wk:
        pose = blend(T.p_sad, p_calm, lt, t_sp, .55, 1.16)
    elif wk < 1:
        pose = mix(phys(p_calm, lt), phys(T.p_walk, lt * .72), math.sin(math.pi * wk))
    else:
        pose = blend(T.p_walk, p_power, lt, t_wk + 1.9, .7, 1.08) if lt < t_wk + 3.0 else phys(p_power, lt)
    glow = .55 + .45 * cl((lt - t_sp) / .8) + .40 * pulse(lt, t_eye, .9)
    ex = 'neutral' if lt < t_sp else ('determined' if lt < t_eye else 'proud')
    lk = (.5, .4) if lt < t_eye - .1 else (0, 0)
    lay, j = hero_layer(lt, hx, hs, pose, ex, reflect=.16, glow=glow, look=lk)
    d._image.alpha_composite(lay)
    # the spine: an accent line draws itself up his back on "seedhi kamar"
    spp = cl((lt - t_sp) / .5)
    if 0 < spp and lt < t_wk + .6:
        a = int(230 * (1 - cl((lt - t_wk) / .6)))
        x0, y0 = hx - 6, GY - hs * .46
        x1, y1 = hx - 2, GY - hs * .95
        e = e_out(spp, 2.0)
        d.line([(x0, y0), (x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)], fill=acc + (a,), width=6)
        d.ellipse([x0 + (x1 - x0) * e - 8, y0 + (y1 - y0) * e - 8, x0 + (x1 - x0) * e + 8, y0 + (y1 - y0) * e + 8], fill=acc + (a,))
    # "nazar aankhon mein": a thin eye-line to the lens
    ep = pulse(lt, t_eye, 1.2)
    if ep > 0:
        hy = GY - hs * .905
        for sx in (-1, 1):
            d.line([(hx + sx * 22, hy), (hx + sx * 60, hy + 150)], fill=S.GLOW_C + (int(90 * ep),), width=2)
    payoff_fit(d, ['JISM', 'PEHLE', 'BOLTA', 'HAI'], cl((lt - vt(6, 5)) / .55), acc, {0})


# ───────────────────────────────────────────── 8  RULE 5 — lafz pakka
_SHARD = np.random.RandomState(11).rand(100, 3)


def s8(d, lt, acc, t, par):
    HY.headline(d, ['LAFZ', 'PAKKA'], W / 2, 348, 124, {0}, 7, cl(lt / .55), 42)
    dust(d, t, 100, 1000, 120, 900, 80, par=par)
    t_grid, t_break, t_seal = vt(7, 1), vt(7, 2), vt(7, 3)
    # 100 small true words, then one broken one scatters them
    gx0, gy0, st = 150, 1010, 30
    for n in range(100):
        i, j = n % 10, n // 10
        q = cl((lt - t_grid - n * .009) / .3)
        if q <= 0:
            continue
        x, y = gx0 + i * st, gy0 + j * st
        a = 255
        if lt > t_break + .3:
            w = lt - t_break - .3
            x += (_SHARD[n][0] - .5) * 900 * w
            y += (_SHARD[n][1] - .3) * 700 * w + 300 * w * w
            a = int(255 * (1 - cl(w / .9)))
        if a <= 0:
            continue
        if n == 0 and lt <= t_break + .3:
            on_paper(gx0 - 14, gy0 - 14, t, 'sach grid')
        tickmark(d, x, y, 9, acc + (a,) if a < 255 else acc, min(1, q * 1.3), 4)
    bp = cl((lt - t_break) / .35)
    if bp > 0 and lt < t_seal + .2:
        k = e_back(bp, 1.5)
        bx, by = 300, 1060
        on_paper(bx - 90, by - 40, t, 'broken word')
        card(d, bx, by, 'LAFZ', (120, 112, 118), 1.0, 30, 170, -.08, int(255 * (1 - cl((lt - t_seal + .4) / .4))))
        d.line([(bx - 20, by - 44), (bx + 6, by - 6), (bx - 10, by + 8), (bx + 22, by + 44)], fill=INK, width=5)
    sp = cl((lt - t_seal) / .4)
    if sp > 0:                                                   # the wax seal
        k = e_back(sp, 1.5)
        sx, sy = 420, 1080
        on_paper(sx - 96 * k, sy - 96 * k, t, 'seal')
        for rr, aa in ((130, 26), (112, 40)):
            d.ellipse([sx - rr * k, sy - rr * k, sx + rr * k, sy + rr * k], fill=acc + (int(aa * pulse(lt, t_seal + .2, 1.0)),))
        fcirc(d, sx, sy, 92 * k, acc, 6)
        d.ellipse([sx - 74 * k, sy - 74 * k, sx + 74 * k, sy + 74 * k], outline=PAPER, width=3)
        if k > .5:
            d.text((sx, sy + 2), 'LAFZ', font=F(int(34 * k), 800), fill=PAPER, anchor='mm')
    hx, hs = 790, 540
    pose = blend(S.p_pocket, S.p_arms_cross, lt, t_break - .1, .6, 1.1) if lt > t_break - .15 else phys(S.p_pocket, lt)
    if lt > t_seal - .1:
        pose = blend(S.p_arms_cross, p_power, lt, t_seal - .1, .7, 1.1)
    glow = .9 + .3 * pulse(lt, t_seal, .9)
    ex = 'sly' if lt < t_break else ('determined' if lt < t_seal else 'proud')
    hero(d, lt, hx, hs, pose, ex, look=(-.6, .3) if t_break < lt < t_seal else (0, 0), glow=glow)
    payoff_fit(d, ['AAPKA', 'LAFZ', 'AAPKI', 'KEEMAT'], cl((lt - t_seal) / .55), acc, {1, 3})


# ───────────────────────────────────────────── 9  PAYOFF — the same room turns
RECAP = ('KAM BOLO', 'WAQT', 'NA', 'KAMAR', 'LAFZ')


def s9(d, lt, acc, t, par):
    k = dolly(8, lt)
    t_in, t_heads, t_still = vt(8, 1), vt(8, 2), vt(8, 3)
    heads, eyes = [], []
    for i in range(5):
        q = cl((lt - t_heads - i * .17) / .55)
        heads.append(12 - 16 * e_io(q))
        eyes.append(e_out(cl((lt - t_heads - i * .17 - .3) / .5), 2.0))
    room(d, lt, t, k, par, heads, eyes)
    shaft(d, t, 880, 340 + 160 * cl((lt - t_still) / 2.0), 34 + 36 * cl((lt - t_still) / 2.0))
    dust(d, t, 300, 1060, 120, 1200, 130, par=par)
    # he walks in from the right and stops at the room's centre-right
    wk = cl((lt - t_in + .2) / 1.5)
    hx = wx(930 - 190 * e_io(wk), k)
    hs = 500 * k
    if wk <= 0:
        pose = phys(T.p_walk, lt * .72)
    elif wk < 1:
        pose = mix(phys(T.p_walk, lt * .72), phys(p_power, lt), e_io(cl((wk - .55) / .45)))
    else:
        pose = phys(p_power, lt)
    glow = .9 + .35 * pulse(lt, t_heads, 1.0) + .25 * pulse(lt, vt(8, 4), .8)
    ex = 'determined' if lt < t_still else 'proud'
    lay, _ = hero_layer(lt, hx, hs, pose, ex, reflect=.12, glow=glow, look=(0, 0))
    d._image.alpha_composite(lay)
    HY.headline(d, ['IZZAT'], W / 2, 318, 118, None, 8, cl((lt - t_still) / .60), 46)
    HY.headline(d, ['KHAMOSHI', 'HAI'], W / 2, 432, 84, {0}, 8, cl((lt - t_still - .15) / .60), 42)
    # five recap boxes on the paper
    rp = cl((lt - vt(8, 5)) / .5)
    if rp > 0:
        for i in range(5):
            q = cl((rp * 1.5 - i * .14) / .6)
            if q <= 0:
                continue
            kk = e_back(q, 1.5)
            cx = 140 + i * 105 + fl(lt, i + 4, 2.2)
            cy = 1004 + fl(lt, i + 8, 3.0)
            hw = 30 * kk
            on_paper(cx - hw, cy - hw, t, 'recap box')
            fbox(d, cx - hw, cy - hw, cx + hw, cy + hw, 9, PAPER, 5)
            tickmark(d, cx, cy, 17, acc, cl(q * 1.6 - .4), 8)
            if q > .6:
                d.text((cx, cy + 56), RECAP[i], font=F(20, 700), fill=(88, 82, 74), anchor='mm')
    pill(d, W / 2 - 30, 1364, 'FOLLOW  ·  SAVE', (120, 82, 10), cl((lt - vt(8, 7)) / .5))


SCENES = [s1, s2, s3, s4, s5, s6, s7, s8, s9]


def scene_img(si, lt, t, par):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, 'RGBA')
    SCENES[si](d, lt, ACC[si], t, par)
    on_paper(W / 2, PAY_Y - 70, t, 'payoff line')
    for t0, t1, txt, hot in CAPS[si]:
        t0, t1 = t0 + LEAD[si], t1 + LEAD[si]
        if t0 <= lt < t1:
            words = txt.split()
            f = F(50, 600)
            wdt = sum(f.getlength(w) for w in words) + f.getlength(' ') * (len(words) - 1)
            sz = 50 if wdt <= PW.CAP_MAX_W else max(40, int(50 * PW.CAP_MAX_W / wdt))
            on_paper(W / 2 - wdt * sz / 100 - 12, PW.CAP_Y_P - 30, t, 'caption ' + txt)
            caption_fit(d, words, (lt - t0) / (t1 - t0), ACC[si], hot)
            break
    return im


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
    dur = SCENE_END[si] - SCENE_START[si]
    z, px, py = camera(t, si, lt, dur)
    par = (-px * .5, -py * .5)                      # far plane moves half as much as the frame

    cv = backdrop(t, show, acc)
    lay = scene_img(show, slt, t, par)
    if tp is not None and tp < .5:
        fa = 1 - e_io(cl(tp / .5))
        lay.putalpha(lay.getchannel('A').point(lambda v: int(v * fa)))
    cv.alpha_composite(lay)
    d = ImageDraw.Draw(cv, 'RGBA')
    chrome(d, t, show, acc)
    if tp is not None:
        swipe(d, tp, tk, t)

    frame = cv.convert('RGB')
    iz = 1.0 / z
    ox = (W - W * iz) * .5 + px
    oy = (H - H * iz) * .5 + py
    assert ox >= 0 and ox + W * iz <= W and oy >= 0 and oy + H * iz <= H, (i, z, px, py)
    frame = frame.transform((W, H), Image.AFFINE, (iz, 0, ox, 0, iz, oy), Image.BICUBIC)
    arr = np.asarray(frame).astype(np.float32) + C._GRAIN
    return np.clip(arr, 0, 255).astype(np.uint8)


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
    if sys.argv[1] == 'still':
        t = float(sys.argv[2])
        Image.fromarray(render(int(round(t * FPS)))).save('/home/user/build/still_respect.png')
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
        sheet.save('/home/user/build/contact_respect.png')
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        shard(a, b, sys.argv[3])
