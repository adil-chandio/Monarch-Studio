"""
fx.py — PREMIUM MOTION-GRAPHICS TOOLKIT  (v4 "elite" pass)
===========================================================
Everything the v2 renderer did not have:
  * a THEME system — each scene owns a colour identity, and the grade,
    the background wash, the particles and the HUD all follow it
  * kinetic captions (word-by-word, beat-locked, theme-highlighted)
  * ambient bokeh particle field, beat-reactive
  * corner HUD brackets, progress rail, scene chips  — the "pro" furniture
  * counters, progress rings, chips, confetti, light sweeps
  * 9 transitions instead of 5, including glitch-slice and zoom-punch
  * a real colour grade: shadow tint, highlight roll-off, halation,
    constant subtle chromatic aberration, theme vignette

All of it is a pure function of t, so sharded rendering stays bit-identical.
"""
import math, sys
sys.path.insert(0, '/home/user/src')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from stickbase import (W, H, FPS, CHALK, GOLD, CYAN, MINT, RED, PINK,
                       clamp, out_back, out_cubic, out_expo, in_cubic, ease, hsh,
                       poly, circ, arc, box, star, ft, text_img, put, write,
                       MARKER, HAND, CAVEAT)

# ───────────────────────────────────────────────────── extra palette
VIOLET = (168, 128, 255)
ORANGE = (255, 148, 72)
LIME   = (186, 255, 92)
ICE    = (198, 232, 255)
STEEL  = (126, 142, 174)

SPB = 60.0 / 112.0            # seconds per beat — matches the score exactly


def beat_phase(t):
    return (t % SPB) / SPB


def beat_pulse(t, sharp=6.0):
    """1.0 on the beat, decaying to 0 before the next one."""
    return math.exp(-sharp * beat_phase(t))


def bar_phase(t, bars=4):
    return (t % (SPB * bars)) / (SPB * bars)


# ───────────────────────────────────────────────────── THE THEME SYSTEM
# Each scene is a colour chapter. The film reads as one deliberate journey
# from cold-red panic to warm-gold payoff.
THEME = [
    dict(name='PROBLEM', key=RED,    sec=(255, 138, 118), third=VIOLET,
         wash=((255, 62, 68, .30), (96, 62, 170, .17)),
         shadow=(16, -4, -2), high=(12, 2, -8), vig=(40, 8, 16), heat=.00),
    dict(name='SKILL',   key=CYAN,   sec=ICE,            third=VIOLET,
         wash=((44, 186, 255, .30), (132, 92, 255, .15)),
         shadow=(-10, 0, 18), high=(-2, 6, 14), vig=(8, 24, 48), heat=.06),
    dict(name='GRIND',   key=VIOLET, sec=MINT,           third=CYAN,
         wash=((150, 104, 255, .28), (86, 250, 190, .14)),
         shadow=(2, -6, 16), high=(6, 4, 10), vig=(26, 14, 48), heat=.12),
    dict(name='CREATE',  key=PINK,   sec=ORANGE,         third=GOLD,
         wash=((255, 110, 196, .28), (255, 158, 72, .16)),
         shadow=(14, -4, 8), high=(16, 4, -2), vig=(46, 14, 34), heat=.26),
    dict(name='SELL',    key=MINT,   sec=GOLD,           third=CYAN,
         wash=((104, 250, 178, .27), (255, 198, 70, .17)),
         shadow=(-4, 8, 4), high=(14, 10, -6), vig=(14, 38, 26), heat=.40),
    dict(name='PAYOFF',  key=GOLD,   sec=ORANGE,         third=LIME,
         wash=((255, 194, 60, .32), (255, 132, 60, .18)),
         shadow=(14, 6, -8), high=(22, 12, -14), vig=(48, 30, 6), heat=.62),
]
KEY = [th['key'] for th in THEME]
SEC = [th['sec'] for th in THEME]


def lerp_col(a, b, k):
    k = clamp(k)
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


# ───────────────────────────────────────────────────── background wash
BW, BH = 180, 320
_by, _bx = np.mgrid[0:BH, 0:BW].astype(np.float32)
_BASE_GLOW = np.exp(-(((_bx - BW * .5) ** 2 + (_by - BH * .5) ** 2) / (2 * 155.0 ** 2)))[..., None]


def _blobs(t, th, scale=1.0):
    out = np.zeros((BH, BW, 3), np.float32)
    for i, (r, g, b, amp) in enumerate(th['wash']):
        col = np.array([r, g, b], np.float32)
        cx = BW * (.5 + (.36 if i == 0 else -.40) * math.sin(t * (.55 - i * .18) + i))
        cy = BH * ((.30 if i == 0 else .72) + .15 * math.cos(t * (.42 + i * .1) + i))
        s = 90.0 - i * 12
        out += np.exp(-(((_bx - cx) ** 2 + (_by - cy) ** 2) / (2 * s * s)))[..., None] * col * (amp * scale)
    return out


def theme_wash(t, si, si2=None, mix=0.0, pulse=0.0):
    """Animated gradient wash in the scene's theme colour, beat-reactive."""
    a = _blobs(t, THEME[si])
    if si2 is not None and mix > 0:
        a = a * (1 - mix) + _blobs(t, THEME[si2]) * mix
    th = THEME[si2] if (si2 is not None and mix > .5) else THEME[si]
    a += _BASE_GLOW * np.array([58, 68, 108], np.float32) * (.19 + .07 * pulse)
    a += _BASE_GLOW * np.array(th['key'], np.float32) * (.07 * pulse)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGB').resize((W, H), Image.BICUBIC)


# ───────────────────────────────────────────────────── ambient particles
_PT = []
for i in range(54):
    _PT.append(dict(x=hsh(i * 3.11), y=hsh(i * 7.37), r=3 + hsh(i * 1.9) * 13,
                    sp=.016 + hsh(i * 2.7) * .055, ph=hsh(i * 5.1) * 6.28,
                    sw=14 + hsh(i * 4.3) * 52, kind=i % 7))


def particles(cv, t, th, amount=1.0, pulse=0.0):
    """Floating bokeh + dust in the theme colour. Reads as depth and polish."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    kc, sc = th['key'], th['sec']
    for p in _PT:
        y = ((p['y'] - t * p['sp']) % 1.18) * (H + 260) - 130
        x = p['x'] * W + math.sin(t * .7 + p['ph']) * p['sw']
        if y < -40 or y > H + 40:
            continue
        r = p['r'] * (1 + .22 * pulse)
        col = kc if p['kind'] < 3 else (sc if p['kind'] < 5 else ICE)
        a = int((26 + 42 * hsh(p['ph'])) * amount)
        if p['kind'] == 6:
            d.line([(x, y - r * 2), (x, y + r * 2)], fill=col + (a,), width=2)
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=col + (a,))
    cv.alpha_composite(lay.filter(ImageFilter.GaussianBlur(2.4)))


# ───────────────────────────────────────────────────── premium furniture
def corner_hud(cv, t, th, p=1.0):
    """Animated corner brackets — the single cheapest 'this is a pro edit' cue."""
    if p <= 0:
        return
    d = ImageDraw.Draw(cv)
    col = th['key']
    L = 86 * out_cubic(p)
    g = 46 + 5 * math.sin(t * 2.0)
    a = int(150 * p)
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        cx = g if sx > 0 else W - g
        cy = 172 if sy > 0 else H - 150
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col + (a,), width=5)
        d.line([(cx, cy), (cx, cy + sy * L)], fill=col + (a,), width=5)
        d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=col + (int(a * 1.5),))


def progress_rail(cv, t, total, cuts, th, si):
    """Top progress rail with chapter ticks and a travelling glow head."""
    d = ImageDraw.Draw(cv)
    x0, x1, y = 58, W - 58, 104
    d.rounded_rectangle([x0, y - 6, x1, y + 6], 6, fill=(255, 255, 255, 34))
    fx = x0 + (x1 - x0) * clamp(t / total)
    # chapter segments, each in its own theme colour
    prev = x0
    for k in range(6):
        seg_end = x0 + (x1 - x0) * ((cuts[k] if k < len(cuts) else total) / total)
        end = min(seg_end, fx)
        if end > prev:
            d.rounded_rectangle([prev, y - 6, end, y + 6], 6, fill=THEME[k]['key'] + (236,))
        prev = seg_end
        if prev > fx:
            break
    for c in cuts:
        x = x0 + (x1 - x0) * c / total
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 255, 255, 200))
    gl = Image.new('RGBA', (90, 90), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([24, 24, 66, 66], fill=th['key'] + (255,))
    cv.alpha_composite(gl.filter(ImageFilter.GaussianBlur(9)), (int(fx - 45), int(y - 45)))
    d.ellipse([fx - 10, y - 10, fx + 10, y + 10], fill=(255, 255, 255, 255))


def scene_chip(cv, si, lt, th, total_steps=4):
    """Top-right step chip with a fill ring. Replaces the flat v2 'STEP n/4'."""
    if si == 0 or si == 5:
        return
    p = clamp(lt / .4)
    if p <= 0:
        return
    k = out_back(p, 2.0)
    cx, cy = W - 148, 206
    d = ImageDraw.Draw(cv)
    r = 56 * k
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(10, 14, 22, 170),
              outline=th['key'] + (70,), width=3)
    sweep = clamp((lt - .25) / .7)
    d.arc([cx - r + 7, cy - r + 7, cx + r - 7, cy + r - 7], -90, -90 + 360 * (si / total_steps) * sweep,
          fill=th['key'] + (255,), width=7)
    if p > .5:
        write(cv, str(si), cx, cy - 2, 50, th['key'], MARKER, p=1)
        write(cv, f'/ {total_steps}', cx, cy + 74, 26, (168, 180, 206), HAND, p=1)


def label_tag(cv, txt, x, y, p, col, size=30, pad=26):
    """Small outlined pill, used for theme names and micro-labels."""
    if p <= 0:
        return
    k = out_back(min(1, p * 2.2), 2.2)
    a = clamp(p * 3)
    f = ft(HAND, size)
    tw = f.getlength(txt)
    lw, lh = int(tw + pad * 2), int(size * 1.9)
    lay = Image.new('RGBA', (lw + 8, lh + 8), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    dd.rounded_rectangle([4, 4, lw, lh], lh / 2, fill=col + (40,), outline=col + (235,), width=3)
    dd.text((lw / 2 + 2, lh / 2 + 2), txt, font=f, fill=col + (255,), anchor='mm')
    if k < .99:
        lay = lay.resize((max(2, int(lay.width * k)), max(2, int(lay.height * k))), Image.BILINEAR)
    if a < .99:
        lay.putalpha(lay.getchannel('A').point(lambda v: int(v * a)))
    cv.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))


# ───────────────────────────────────────────────────── kinetic captions
_CAP_F = {}


def _capfont(sz):
    if sz not in _CAP_F:
        _CAP_F[sz] = ft(MARKER, sz)
    return _CAP_F[sz]


def caption(cv, txt, p, y, th, size=58, hot=None):
    """Word-by-word kinetic subtitle on a dark pill.
    p = 0..1 across the line; `hot` = index of the word to burn in theme colour."""
    if p <= 0:
        return
    words = txt.split()
    n = len(words)
    f = _capfont(size)
    sp = f.getlength(' ')
    ws = [f.getlength(w) for w in words]
    total = sum(ws) + sp * (n - 1)
    pad = 40
    lw, lh = int(total + pad * 2), int(size * 1.95)
    lay = Image.new('RGBA', (lw + 10, lh + 10), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    # shell grows in first
    shell = clamp(p * 4)
    sw = int(lw * (0.18 + 0.82 * out_back(shell, 1.6)))
    dd.rounded_rectangle([(lw - sw) / 2 + 5, 5, (lw + sw) / 2 + 5, lh + 5], lh / 2,
                         fill=(8, 11, 18, 212), outline=th['key'] + (int(190 * shell),), width=4)
    x = pad + 5
    for i, w in enumerate(words):
        wp = clamp((p - .12 - i * (.62 / max(1, n))) / .22)
        if wp > 0:
            col = th['key'] if (hot is not None and i == hot) else (240, 245, 253)
            dy = (1 - out_back(wp, 2.6)) * 22
            aa = int(255 * clamp(wp * 2))
            dd.text((x + ws[i] / 2, lh / 2 + 5 + dy), w, font=f, fill=col + (aa,), anchor='mm')
        x += ws[i] + sp
    a = 1 - clamp((p - .92) / .08)
    if a < .99:
        lay.putalpha(lay.getchannel('A').point(lambda v: int(v * a)))
    cv.alpha_composite(lay, (int(W / 2 - lay.width / 2), int(y - lay.height / 2)))


# ───────────────────────────────────────────────────── counters & rings
def counter(cv, val, x, y, size, col, p=1.0, prefix='', suffix='', font=MARKER, rot=0.):
    """Odometer-ish number. Draws the digits with a slight per-digit offset so
    a changing value feels mechanical rather than static."""
    if p <= 0:
        return
    txt = f'{prefix}{val:,}{suffix}'
    write(cv, txt, x, y, int(size * (0.86 + 0.14 * out_back(clamp(p * 3), 2.2))), col, font, rot=rot, p=1)


def ring(d, cx, cy, r, p, col, w=12, start=-90, bg=True):
    if bg:
        d.arc([cx - r, cy - r, cx + r, cy + r], 0, 360, fill=col + (46,), width=w)
    if p > 0:
        d.arc([cx - r, cy - r, cx + r, cy + r], start, start + 360 * clamp(p), fill=col + (255,), width=w)


def glow_underline(cv, x0, x1, y, p, col, h=12):
    if p <= 0:
        return
    xx = x0 + (x1 - x0) * out_expo(p)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    dd.rounded_rectangle([x0, y - h / 2, xx, y + h / 2], h / 2, fill=col + (255,))
    cv.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(cv).rounded_rectangle([x0, y - h / 2, xx, y + h / 2], h / 2, fill=col + (240,))


# ───────────────────────────────────────────────────── bursts
def confetti(cv, t, p, th, cx=None, cy=None, n=34):
    if p <= 0 or p >= 1:
        return
    cx = W / 2 if cx is None else cx
    cy = H * .45 if cy is None else cy
    d = ImageDraw.Draw(cv)
    cols = [th['key'], th['sec'], th['third'], CHALK]
    for i in range(n):
        a = hsh(i * 1.37) * 6.2832
        sp = 300 + hsh(i * 2.91) * 720
        r = sp * out_expo(p)
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a) * .8 + 420 * p * p
        s = (9 + hsh(i * 3.7) * 13) * (1 - p * .45)
        rot = hsh(i * 4.4) * 6.28 + t * 7
        aa = int(235 * (1 - p) ** .8)
        c = cols[i % 4] + (aa,)
        dx, dy = math.cos(rot) * s, math.sin(rot) * s
        d.polygon([(x - dx, y - dy), (x + dy * .5, y - dx * .5),
                   (x + dx, y + dy), (x - dy * .5, y + dx * .5)], fill=c)


def light_sweep(cv, p, col=(255, 255, 255), width=.16, strength=92, ang=.34):
    """A broad diagonal light band crossing the frame. Premium, cheap, effective."""
    if p <= 0 or p >= 1:
        return
    sw, sh = W // 6, H // 6
    xs = np.linspace(0, 1, sw)[None, :]
    ys = np.linspace(0, 1, sh)[:, None]
    band = np.exp(-(((xs + ang * ys) - p * (1 + ang) * 1.25) ** 2) / (2 * width ** 2))
    a = (band * strength).clip(0, 255).astype(np.uint8)
    m = Image.fromarray(a, 'L').resize((W, H), Image.BILINEAR)
    lay = Image.new('RGBA', (W, H), col + (0,))
    lay.putalpha(m)
    cv.alpha_composite(lay)


def radial_burst(cv, cx, cy, p, col, n=26, r0=140, r1=760, w=9):
    if p <= 0 or p >= 1:
        return
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    k = out_expo(p)
    a = int(210 * (1 - p) ** 1.3)
    for i in range(n):
        ang = math.radians(i * (360 / n) + hsh(i) * 8)
        ra = r0 + (r1 - r0) * k
        rb = ra + 90 + hsh(i * 2.2) * 200
        ca, sa = math.cos(ang), math.sin(ang)
        d.line([(cx + ra * ca, cy + ra * sa), (cx + rb * ca, cy + rb * sa)],
               fill=col + (a,), width=max(2, int(w * (1 - p))))
    cv.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1.8)))


def shock_ring(cv, cx, cy, p, col, maxr=620, w=14, rings=3):
    if p <= 0 or p >= 1:
        return
    d = ImageDraw.Draw(cv)
    for k in range(rings):
        pp = clamp(p - k * .12)
        if pp <= 0:
            continue
        r = maxr * out_expo(pp)
        a = int(215 * (1 - pp) ** 1.5 * (1 - k * .28))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col + (a,),
                  width=max(2, int(w * (1 - pp))))


# ───────────────────────────────────────────────────── transitions (9)
MW, MH = W // 2, H // 2
_my, _mx = np.mgrid[0:MH, 0:MW].astype(np.float32)
_ANG = np.arctan2(_my - MH * .62, _mx - MW * .5)
_RAD = np.sqrt((_mx - MW * .5) ** 2 + (_my - MH * .62) ** 2)


def trans_mask(kind, p):
    """white = incoming scene."""
    if kind == 0:        # ink-blob iris
        wob = 1 + .16 * np.sin(_ANG * 5) + .08 * np.sin(_ANG * 9 + 1.3)
        m = (_RAD < (p ** 1.25) * 700 * wob).astype(np.float32)
    elif kind == 1:      # paint strokes sweeping down
        m = np.zeros((MH, MW), np.float32)
        cols = 7
        b = [int(round(i * MW / cols)) for i in range(cols + 1)]
        for c in range(cols):
            pp = clamp((p - c * .05) / .72)
            m[:, b[c]:b[c + 1]] = (_my[:, b[c]:b[c + 1]] < MH * pp * 1.3 + 40 * math.sin(c * 2.1))
    elif kind == 2:      # eraser wipe, noisy edge
        noise = 26 * np.sin(_my * .06) + 18 * np.sin(_my * .013 + 2)
        m = (_mx < (p * 1.3 - .15) * MW + noise).astype(np.float32)
    elif kind == 3:      # vertical zip from centre
        m = (np.abs(_my - MH * .5) < p ** .85 * MH * .75).astype(np.float32)
    elif kind == 4:      # diagonal whip
        m = ((_mx * .6 + _my * .4) < p * (MW * .6 + MH * .4) * 1.15).astype(np.float32)
    elif kind == 5:      # GLITCH slice — horizontal bands snap across out of order
        m = np.zeros((MH, MW), np.float32)
        bands = 16
        for bi in range(bands):
            y0, y1 = int(bi * MH / bands), int((bi + 1) * MH / bands)
            off = hsh(bi * 2.7)
            pp = clamp((p - off * .34) / .62)
            dirn = 1 if bi % 2 == 0 else -1
            edge = pp * MW * 1.25
            if dirn > 0:
                m[y0:y1] = (_mx[y0:y1] < edge)
            else:
                m[y0:y1] = (_mx[y0:y1] > MW - edge)
    elif kind == 6:      # ZOOM-PUNCH — circle out of the centre, very fast
        m = (_RAD < (out_expo(p) ** .7) * 1250).astype(np.float32)
    elif kind == 7:      # barn doors
        m = (np.abs(_mx - MW * .5) > MW * .5 * (1 - p ** .8)).astype(np.float32)
    else:                # 8 — radial clock wipe
        a = (np.arctan2(_my - MH * .5, _mx - MW * .5) + math.pi) / (2 * math.pi)
        m = (a < p).astype(np.float32)
    img = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8), 'L')
    return img.filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)


def trans_edge(layer, kind, p, col):
    """The bright leading edge that sells the wipe."""
    d = ImageDraw.Draw(layer)
    a = int(210 * (1 - abs(p - .5) * 1.1))
    if kind == 0:
        r = p ** 1.25 * 1400
        d.ellipse([W / 2 - r, H * .62 - r, W / 2 + r, H * .62 + r], outline=col + (a,), width=11)
    elif kind == 2:
        x = (p * 1.3 - .15) * W
        d.line([(x, 0), (x, H)], fill=CHALK + (a,), width=13)
    elif kind == 3:
        hh = p ** .85 * H * .75
        d.line([(0, H / 2 - hh), (W, H / 2 - hh)], fill=col + (a,), width=9)
        d.line([(0, H / 2 + hh), (W, H / 2 + hh)], fill=col + (a,), width=9)
    elif kind == 4:
        xx = p * (W * .6 + H * .4) * 1.15
        d.line([(xx / .6, 0), ((xx - H * .4) / .6, H)], fill=col + (a,), width=14)
    elif kind == 5:
        for bi in range(16):
            y0 = int(bi * H / 16)
            off = hsh(bi * 2.7)
            pp = clamp((p - off * .34) / .62)
            x = pp * W * 1.25
            xx = x if bi % 2 == 0 else W - x
            d.line([(xx, y0), (xx, y0 + H // 16)], fill=col + (a,), width=7)
    elif kind == 6:
        r = (out_expo(p) ** .7) * 2500
        d.ellipse([W / 2 - r, H * .62 - r, W / 2 + r, H * .62 + r], outline=col + (a,), width=16)
    elif kind == 7:
        xx = W * .5 * (1 - p ** .8)
        d.line([(W / 2 - xx, 0), (W / 2 - xx, H)], fill=col + (a,), width=10)
        d.line([(W / 2 + xx, 0), (W / 2 + xx, H)], fill=col + (a,), width=10)


# ───────────────────────────────────────────────────── post / grade
_VY, _VX = np.mgrid[0:H, 0:W].astype(np.float32)
_VR = np.sqrt(((_VX - W / 2) / (W / 2)) ** 2 + ((_VY - H / 2) / (H / 2)) ** 2)
_VMASK = np.clip(1.06 - .30 * _VR ** 2.1, 0, 1.12)[..., None]
_VEDGE = np.clip((_VR - .62) / .70, 0, 1)[..., None] ** 1.6
_LUMW = np.array([.299, .587, .114], np.float32)


def bloom(arr, amount=.55, thr=160):
    small = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    a = np.clip(np.asarray(small).astype(np.float32) - thr, 0, None) * (255 / (255 - thr))
    b = Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))
    b2 = b.filter(ImageFilter.GaussianBlur(34))
    up = (np.asarray(b.resize((W, H), Image.BILINEAR)).astype(np.float32) * .62 +
          np.asarray(b2.resize((W, H), Image.BILINEAR)).astype(np.float32) * .55)
    return arr + up * amount


def halation(arr, th, amount=.30):
    """Warm bleed around the brightest marks — the 'filmic' tell."""
    small = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).resize((W // 6, H // 6), Image.BILINEAR)
    a = np.clip(np.asarray(small).astype(np.float32) - 198, 0, None)
    b = Image.fromarray((a * 1.4).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(20))
    up = np.asarray(b.resize((W, H), Image.BILINEAR)).astype(np.float32)
    tintc = np.array(th['sec'], np.float32) / 255.0
    return arr + up * tintc * amount


def grade(arr, th, mix=1.0, th2=None, k2=0.0):
    """Shadow/highlight split tone in the scene theme + filmic roll-off."""
    sh = np.array(th['shadow'], np.float32)
    hi = np.array(th['high'], np.float32)
    vg = np.array(th['vig'], np.float32)
    if th2 is not None and k2 > 0:
        sh = sh * (1 - k2) + np.array(th2['shadow'], np.float32) * k2
        hi = hi * (1 - k2) + np.array(th2['high'], np.float32) * k2
        vg = vg * (1 - k2) + np.array(th2['vig'], np.float32) * k2
    lum = (arr @ _LUMW)[..., None] / 255.0
    arr = arr + ((1 - lum) * sh + lum * hi) * mix
    arr = arr + _VEDGE * vg * .85          # coloured edge glow
    x = np.clip(arr / 255., 0, 1)
    x = x * x * (3 - 2 * x) * .34 + x * .66      # gentle S-curve
    x = np.clip(x * 1.035 - .012, 0, 1)
    return x * 255.


def chroma(arr, px):
    if px < .25:
        return arr
    s = int(px)
    if s < 1:
        return arr
    arr[..., 0] = np.roll(arr[..., 0], s, axis=1)
    arr[..., 2] = np.roll(arr[..., 2], -s, axis=1)
    return arr


def vignette(arr):
    return arr * _VMASK
