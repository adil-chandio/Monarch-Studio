"""STICKMAN v2 — maxed out: 3D marker type, animated parallax BG, ink/paint/eraser
transitions, comic VFX, camera moves, bloom + grade. 37s vertical."""
import math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, '/home/user/src')
from stickbase import (W, H, FPS, CHALK, GOLD, CYAN, MINT, RED, PINK, BOARD, VIGN, GRAIN,
                   clamp, out_back, out_cubic, out_expo, in_cubic, ease, hsh, TQ,
                   poly, circ, arc, box, squiggle, arrow, star, tick, cross, coin, laptop,
                   play_btn, speech, stick, pose_sad, pose_type, pose_point, pose_walk,
                   pose_shake, pose_dance, pose_cheer, ft, text_img, put, write,
                   MARKER, HAND, CAVEAT, _bullet)
from timeline import SCENE_START, SCENE_END, DUR_TOTAL

NF = int(FPS * DUR_TOTAL)
OUT = '/home/user/build/stick2_silent.mp4'
rng = np.random.default_rng(77)
ACCENT = [RED, CYAN, MINT, PINK, GOLD, GOLD]
CUTS = SCENE_START[1:]

# ===================================================== 3D marker type
class T3:
    _c = {}
    def __init__(self, txt, size, col, fontp=MARKER, depth=16, dvec=(.45, .95), glow_a=120):
        f = ft(fontp, size)
        bb = f.getbbox(txt)
        pad = 70 + depth
        iw, ih = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
        pos = (pad - bb[0], pad - bb[1])
        m = Image.new('L', (iw, ih), 0)
        ImageDraw.Draw(m).text(pos, txt, font=f, fill=255)
        mo = Image.new('L', (iw, ih), 0)
        ImageDraw.Draw(mo).text(pos, txt, font=f, fill=255, stroke_width=6, stroke_fill=255)
        img = Image.new('RGBA', (iw, ih), (0, 0, 0, 0))
        gl = Image.new('RGBA', (iw, ih), col + (0,))
        gl.putalpha(mo.filter(ImageFilter.GaussianBlur(26)).point(lambda v: min(255, int(v * 1.8 * glow_a / 255))))
        img.alpha_composite(gl)
        side = tuple(max(0, int(c * .34)) for c in col)
        for i in range(depth, 0, -1):
            k = i / depth
            c = tuple(int(s * (.45 + .55 * (1 - k))) for s in side)
            lay = Image.new('RGBA', (iw, ih), c + (255,)); lay.putalpha(mo)
            img.alpha_composite(ImageChops.offset(lay, int(dvec[0] * i), int(dvec[1] * i)))
        dark = Image.new('RGBA', (iw, ih), (10, 13, 19, 255)); dark.putalpha(mo)
        img.alpha_composite(dark)
        face = Image.new('RGBA', (iw, ih), col + (255,)); face.putalpha(m)
        img.alpha_composite(face)
        self.img, self.size = img, (iw, ih)
        self._ma = np.asarray(m, np.float32) / 255.0

    def sweep(self, phase, width=.14, strength=215):
        iw, ih = self.size
        xs = np.linspace(0, 1, iw)[None, :]; ys = np.linspace(0, 1, ih)[:, None]
        band = np.exp(-((xs + .3 * ys - phase * 1.6) ** 2) / (2 * width ** 2))
        a = (band * self._ma * strength).clip(0, 255).astype(np.uint8)
        sw = Image.new('RGBA', (iw, ih), (255, 255, 255, 0)); sw.putalpha(Image.fromarray(a, 'L'))
        out = self.img.copy(); out.alpha_composite(sw); return out


def t3(key, *a, **k):
    if key not in T3._c:
        T3._c[key] = T3(*a, **k)
        if len(T3._c) > 50: T3._c.pop(next(iter(T3._c)))
    return T3._c[key]


def w3(cv, obj, cx, cy, p=1., scale=1., rot=0., sq=0., sweep=None, alpha=None, pop=True):
    """p drives a squash-pop entry"""
    if p <= 0: return
    e = out_back(p, 2.4) if pop else clamp(p)
    sc = scale * (0.4 + 0.6 * e)
    a = clamp(p * 3) if alpha is None else alpha
    img = obj.sweep(sweep) if sweep is not None and 0 <= sweep <= 1.4 else obj.img
    wsq = 1 + sq
    im = img.resize((max(2, int(img.width * sc * wsq)), max(2, int(img.height * sc / max(.2, wsq)))), Image.BILINEAR)
    if rot: im = im.rotate(rot, Image.BICUBIC, expand=True)
    if a < .99:
        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    cv.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

# ===================================================== animated background
BW, BH = 180, 320
_by, _bx = np.mgrid[0:BH, 0:BW].astype(np.float32)
def wash(t, si, si2=None, mix=0.0):
    c1 = np.array(ACCENT[si], np.float32)
    if si2 is not None:
        c1 = c1 * (1 - mix) + np.array(ACCENT[si2], np.float32) * mix
    base = np.zeros((BH, BW, 3), np.float32)
    def g(cx, cy, s, col, amp):
        return np.exp(-(((_bx - cx) ** 2 + (_by - cy) ** 2) / (2 * s * s)))[..., None] * col * amp
    base += g(BW * (.5 + .34 * math.sin(t * .55)), BH * (.3 + .16 * math.cos(t * .4)), 88, c1, .26)
    base += g(BW * (.5 - .4 * math.sin(t * .37 + 1)), BH * (.72 + .12 * math.sin(t * .5)), 78,
              np.array(CYAN, np.float32), .12)
    base += g(BW * .5, BH * .5, 150, np.array([60, 70, 110], np.float32), .18)
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), 'RGB').resize((W, H), Image.BICUBIC)


def build_doodles():
    lay = Image.new('RGBA', (W, H + 600), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(46):
        x = hsh(i * 3.1) * W; y = hsh(i * 7.7) * (H + 600)
        s = 18 + hsh(i * 2.3) * 34
        col = [CHALK, GOLD, CYAN, MINT, PINK][i % 5] + (34,)
        k = i % 5
        if k == 0: circ(d, (x, y), s, col, 4, 1, i, 0, 2, 16)
        elif k == 1: star(d, x, y, s, col, 1, 0, i, 4)
        elif k == 2:
            f = ft(MARKER, int(s * 2.4)); d.text((x, y), '$', font=f, fill=col, anchor='mm')
        elif k == 3: poly(d, [(x - s, y + s), (x, y - s), (x + s, y + s)], col, 4, 1, i, 0, 2)
        else: squiggle(d, x - s, y, x + s, col, 4, 1, i, 0, 2, 5, 8)
    return lay
DOODLES = build_doodles()

def build_grid():
    lay = Image.new('RGBA', (W, H + 240), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for x in range(0, W, 135): d.line([(x, 0), (x, H + 240)], fill=(255, 255, 255, 9), width=2)
    for y in range(0, H + 240, 135): d.line([(0, y), (W, y)], fill=(255, 255, 255, 9), width=2)
    return lay
GRID = build_grid()

# ===================================================== comic VFX
def speed_lines(cv, p, col=CHALK, n=30, inner=420, cx=None, cy=None):
    if p <= .02: return
    cx = cx or W / 2; cy = cy or H / 2
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(n):
        a = i * (360 / n) + hsh(i) * 6
        r0 = inner + hsh(i * 2.1) * 140
        r1 = r0 + 260 + hsh(i * 3.3) * 420
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        d.line([(cx + r0 * ca, cy + r0 * sa), (cx + r1 * ca, cy + r1 * sa)],
               fill=col + (int(150 * p),), width=int(3 + hsh(i * 5) * 7))
    cv.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1.6)))

def shockwave(cv, cx, cy, p, col=GOLD, maxr=620, w=12):
    if p <= 0 or p >= 1: return
    d = ImageDraw.Draw(cv)
    r = maxr * out_expo(p)
    a = int(220 * (1 - p) ** 1.5)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col + (a,), width=max(2, int(w * (1 - p))))
    r2 = r * .72
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=col + (int(a * .5),), width=max(2, int(w * .6 * (1 - p))))

def comic_burst(cv, cx, cy, p, txt='BOOM!', col=GOLD, size=78, r=200):
    if p <= 0 or p > 1: return
    d = ImageDraw.Draw(cv)
    k = out_back(min(1, p * 2.2), 2.6) * (1 - clamp((p - .7) / .3))
    pts = []
    for i in range(18):
        rr = r * k * (1.0 if i % 2 == 0 else .62)
        a = math.radians(i * 20 + p * 30)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    if k > .05:
        d.polygon(pts, fill=col + (46,))
        poly(d, pts, col, 8, 1, 3.3, int(p * 10), 2.2, closed=True)
        write(cv, txt, cx, cy, int(size * k), col, MARKER, rot=-6, p=1)

def dust(cv, x, y, p, n=12, col=CHALK, spread=120):
    if p <= 0 or p >= 1: return
    d = ImageDraw.Draw(cv)
    for i in range(n):
        a = hsh(i * 1.7) * 6.28
        r = spread * out_expo(p) * (.4 + hsh(i * 2.9))
        rr = max(1.5, 9 * (1 - p))
        xx, yy = x + r * math.cos(a), y + r * math.sin(a) * .7 - 40 * p
        d.ellipse([xx - rr, yy - rr, xx + rr, yy + rr], fill=col + (int(170 * (1 - p)),))

def sparkle(cv, x, y, p, col=GOLD, s=26):
    if p <= 0 or p >= 1: return
    d = ImageDraw.Draw(cv)
    k = math.sin(p * math.pi)
    ss = s * k
    d.line([(x - ss, y), (x + ss, y)], fill=col + (230,), width=5)
    d.line([(x, y - ss), (x, y + ss)], fill=col + (230,), width=5)
    d.line([(x - ss * .6, y - ss * .6), (x + ss * .6, y + ss * .6)], fill=col + (150,), width=3)
    d.line([(x - ss * .6, y + ss * .6), (x + ss * .6, y - ss * .6)], fill=col + (150,), width=3)

def flame(d, x, y, s, t, col=GOLD, p=1.):
    w = 1 + .12 * math.sin(t * 9)
    pts = [(x, y - s * 1.5 * w), (x + s * .55, y - s * .5), (x + s * .3, y - s * .75),
           (x + s * .45, y + s * .2), (x - s * .45, y + s * .2), (x - s * .3, y - s * .7),
           (x - s * .55, y - s * .45)]
    poly(d, pts, col, 6, p, 9.1, int(t * 12), 2, closed=True)

def crown(d, x, y, s, col=GOLD, p=1.):
    pts = [(x - s, y + s * .5), (x - s, y - s * .5), (x - s * .5, y), (x, y - s * .8),
           (x + s * .5, y), (x + s, y - s * .5), (x + s, y + s * .5)]
    poly(d, pts, col, 7, p, 11.3, 0, 1.6, closed=True)

def badge(cv, txt, x, y, p, col=MINT, size=40):
    """floating motion-graphics pill"""
    if p <= 0 or p >= 1: return
    k = out_back(min(1, p * 3), 2.4)
    a = 1 - clamp((p - .6) / .4)
    f = ft(HAND, size)
    tw = f.getlength(txt)
    lay = Image.new('RGBA', (int(tw) + 120, size * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([20, size * .6, tw + 100, size * 2.2], 26, fill=col + (46,), outline=col + (235,), width=4)
    d.text(((tw + 120) / 2, size * 1.4), txt, font=f, fill=col + (255,), anchor='mm')
    if k != 1: lay = lay.resize((max(2, int(lay.width * k)), max(2, int(lay.height * k))), Image.BILINEAR)
    lay.putalpha(lay.getchannel('A').point(lambda v: int(v * a)))
    cv.alpha_composite(lay, (int(x - lay.width / 2), int(y - 60 * p - lay.height / 2)))

def trail_stick(d, x, y, s, posef, lt, col, w, seed, tq, p, face, n=2, dt=.055):
    for i in range(n, 0, -1):
        a = .16 * (1 - i / (n + 1))
        c = tuple(int(c0 * (.35 + a * 2)) for c0 in col)
        stick(d, x, y, s, posef(lt - i * dt), c, max(3, w - 3), seed + i, tq, p, None)
    return stick(d, x, y, s, posef(lt), col, w, seed, tq, p, face)

def highlighter(d, x0, x1, y, p, col=GOLD, h=46):
    if p <= 0: return
    xx = x0 + (x1 - x0) * out_expo(p)
    d.rounded_rectangle([x0, y - h / 2, xx, y + h / 2], h / 2, fill=col + (60,))

def circle_mark(d, cx, cy, rx, ry, p, col=RED, w=8, tq=0):
    """hand-drawn ellipse drawn around something"""
    pts = [(cx + rx * math.cos(math.radians(a)) * (1 + .04 * math.sin(a / 24)),
            cy + ry * math.sin(math.radians(a))) for a in range(-80, 320, 10)]
    poly(d, pts, col, w, p, 13.7, tq, 2.6)

# ===================================================== scenes (content layers)
def hud(cv, t, tq):
    d = ImageDraw.Draw(cv)
    d.rounded_rectangle([60, 96, W - 60, 108], 6, fill=(255, 255, 255, 46))
    w = (W - 120) * clamp(t / DUR_TOTAL)
    d.rounded_rectangle([60, 96, 60 + w, 108], 6, fill=GOLD + (240,))
    d.ellipse([60 + w - 13, 89, 60 + w + 13, 115], fill=GOLD + (255,))
    for c in CUTS:
        x = 60 + (W - 120) * c / DUR_TOTAL
        d.ellipse([x - 5, 97, x + 5, 107], fill=(255, 255, 255, 170))
    si = max(k for k in range(6) if t >= SCENE_START[k])
    if 0 < si < 5:
        d.rounded_rectangle([W - 330, 140, W - 60, 214], 22, fill=(0, 0, 0, 90),
                            outline=ACCENT[si] + (220,), width=4)
        write(cv, f'STEP {si}/4', W - 195, 177, 44, ACCENT[si], HAND, p=1)
    write(cv, '@YOURHANDLE', W / 2, H - 86, 40, (190, 198, 215), HAND, p=1)

def scene1(cv, lt, tq):
    d = ImageDraw.Draw(cv)
    gy = 1530
    poly(d, [(100, gy), (W - 100, gy)], (120, 132, 155), 7, clamp(lt / .22), 21, tq)
    w_in = clamp(lt / .85)
    x = -160 + (W / 2 - 80 + 160) * out_cubic(w_in)
    if w_in < 1:
        st = trail_stick(d, x, gy, 600, pose_walk, lt, CHALK, 10, 31, tq, 1, 'neutral', 2)
        dust(cv, x - 80, gy, (lt % .4) / .4, 6, (150, 160, 180), 70)
    else:
        st = stick(d, W / 2 - 80, gy, 600, pose_sad(lt - .85), CHALK, 10, 31, tq, 1, 'sad')
    w3(cv, t3('s1a', 'JEEB KHALI?', 118, CHALK, MARKER, 16), W / 2, 330, clamp((lt - .5) / .45),
       rot=-2.5, sq=.14 * (1 - clamp((lt - .5) / .45)), sweep=(lt - 1.1) / 1.4)
    squiggle(d, 250, 420, 830, RED, 9, clamp((lt - .95) / .4), 7, tq)
    if .5 < lt < .95: speed_lines(cv, (1 - (lt - .5) / .45) * .8, CHALK, 26, 520)
    # rain cloud over head
    cp = clamp((lt - 1.1) / .5)
    if cp > 0:
        cxx, cyy = W / 2 - 80, 760
        for k, (ox, oy, rr) in enumerate([(-70, 10, 56), (0, -16, 70), (72, 8, 52)]):
            circ(d, (cxx + ox, cyy + oy), rr, (168, 178, 200), 7, clamp(cp * 2 - k * .2), 41 + k, tq, 2.4, 20)
        for k in range(5):
            dp = ((lt * 1.3 + k * .27) % 1.0)
            if cp > .7:
                poly(d, [(cxx - 70 + k * 36, cyy + 70 + dp * 90), (cxx - 74 + k * 36, cyy + 100 + dp * 90)],
                     CYAN, 5, 1, 45 + k, tq, 1.2)
    arc(d, (st['hip'][0] - 54, st['hip'][1] + 30), 26, 0, 180, CHALK, 7, clamp((lt - 1.2) / .4), 46, tq)
    arc(d, (st['hip'][0] + 54, st['hip'][1] + 30), 26, 0, 180, CHALK, 7, clamp((lt - 1.3) / .4), 47, tq)
    p2 = clamp((lt - 1.5) / .45)
    if p2 > 0:
        speech(d, W / 2 + 268, 900, 310, 190, (-.4, 1), p2, CHALK, tq, 51)
        w3(cv, t3('s1b', 'Rs 0', 92, RED, MARKER, 12), W / 2 + 268, 890, clamp((lt - 1.75) / .4), rot=-4)
        sparkle(cv, W / 2 + 420, 820, clamp((lt - 1.9) / .7), RED, 30)
    for i, (dx, dy, dl) in enumerate([(-320, 720, 1.9), (350, 580, 2.15), (-240, 500, 2.4)]):
        pq = clamp((lt - dl) / .4)
        write(cv, '?', W / 2 + dx, dy + math.sin(lt * 2 + i) * 16, 112, CYAN, MARKER,
              rot=-10 + i * 9, p=pq, pop=True)
    p3 = clamp((lt - 2.9) / .5)
    if p3 > 0:
        shockwave(cv, W / 2, 1690, clamp((lt - 2.9) / .8), GOLD, 520, 14)
        w3(cv, t3('s1c', 'PURA PLAN', 100, GOLD, MARKER, 18), W / 2, 1690, p3, rot=1.5,
           sweep=(lt - 3.3) / 1.2)
        write(cv, '4 STEPS ME', W / 2, 1800, 62, MINT, HAND, p=clamp((lt - 3.3) / .5))
        badge(cv, 'FREE', W / 2 + 330, 1660, clamp((lt - 3.5) / 1.5), MINT, 38)
    if lt > 3.6:
        flame(d, 150, 1700, 44, lt, GOLD, clamp((lt - 3.6) / .4))
        flame(d, W - 150, 1700, 44, lt + 1, RED, clamp((lt - 3.75) / .4))

def scene2(cv, lt, tq):
    d = ImageDraw.Draw(cv)
    write(cv, '1', 150, 296, 150, GOLD, HAND, rot=-6, p=clamp(lt / .22), pop=True)
    circ(d, (150, 290), 98, GOLD, 8, clamp((lt - .05) / .28), 81, tq, 3.0, 30)
    w3(cv, t3('s2t', 'SKILL SEEKHO', 92, CHALK, MARKER, 14), W / 2 + 110, 290,
       clamp((lt - .07) / .3), rot=-1.5, sweep=(lt - .9) / 1.3)
    for i, (txt, st) in enumerate([('DESIGN', 1.5), ('VIDEO EDIT', 1.9), ('CODING', 2.3), ('AI TOOLS', 2.7)]):
        p = clamp((lt - st) / .6)
        _bullet(cv, d, tq, 150, 520 + i * 105, txt, p, i)
        if 0 < p < 1: sparkle(cv, 150, 520 + i * 105, p, MINT, 30)
        if p > .5: badge(cv, '+1', 560, 520 + i * 105, clamp((lt - st - .3) / 1.1), MINT, 32)
    bp = clamp((lt - 1.4) / 2.8)
    bx, by = 830, 620
    circ(d, (bx, by), 92 + 5 * math.sin(lt * 4), PINK, 8, clamp((lt - 1.1) / .5), 101, tq, 2.6, 26)
    for i in range(5):
        arc(d, (bx - 42 + i * 21, by - 10 + (i % 2) * 26), 27, 160, 380, PINK, 6,
            clamp((bp - i * .17) * 3), 110 + i, tq, 1.4, 12)
    write(cv, f'{int(bp * 100)}%', bx, by + 142, 54, PINK, HAND, p=clamp((lt - 1.5) / .4))
    for k in range(6):   # knowledge sparks flying into the brain
        sp = ((lt * .7 + k * .17) % 1.0)
        if lt > 1.6:
            a = -2.2 + k * .5
            r = 230 * (1 - sp)
            sparkle(cv, bx + r * math.cos(a), by + r * math.sin(a) + 30, sp, CYAN, 18)
    desk_y, gy = 1330, 1520
    box(d, W / 2 - 320, desk_y, W / 2 + 320, desk_y + 22, (165, 177, 200), 8, clamp((lt - .08) / .28), 91, tq)
    poly(d, [(W / 2 - 272, desk_y + 22), (W / 2 - 272, gy)], (165, 177, 200), 8, clamp((lt - .2) / .26), 92, tq)
    poly(d, [(W / 2 + 272, desk_y + 22), (W / 2 + 272, gy)], (165, 177, 200), 8, clamp((lt - .2) / .26), 93, tq)
    poly(d, [(110, gy), (W - 110, gy)], (120, 132, 155), 7, clamp(lt / .22), 21, tq)
    s_h, seat = 470, 1385
    box(d, W / 2 - 300, seat + 18, W / 2 - 150, gy, (150, 162, 185), 7, clamp((lt - .25) / .3), 94, tq)
    stick(d, W / 2 - 225, seat + .42 * s_h, s_h, pose_type(lt), CHALK, 10, 33, tq,
          clamp((lt - .1) / .35), 'neutral')
    laptop(d, W / 2 + 90, desk_y, 240, tq, 95, clamp((lt - .8) / .8),
           screen=lambda dd, x, y, w_, h_, pp: play_btn(dd, x, y, 46 + 4 * math.sin(lt * 7), pp, RED, tq, 96))
    for k in range(3):   # typing note particles
        sp = ((lt * 1.1 + k * .33) % 1.0)
        if lt > 1.0:
            write(cv, ['</>', '*', '~'][k], W / 2 + 60 + k * 40, desk_y - 120 - sp * 180, 34,
                  CYAN, HAND, p=1 - sp)
    arrow(d, (bx - 70, by + 140), (W / 2 - 150, 1120), PINK, 7, clamp((lt - 3.3) / .6), 97, tq, .22)
    p5 = clamp((lt - 4.3) / .6)
    if p5 > 0:
        highlighter(d, 230, 850, 1680, clamp((lt - 4.5) / .5), CYAN, 54)
        write(cv, 'YouTube = FREE university', W / 2, 1680, 58, CHALK, HAND, rot=-1, p=p5)

def scene3(cv, lt, tq):
    d = ImageDraw.Draw(cv)
    write(cv, '2', 150, 296, 150, GOLD, HAND, rot=5, p=clamp(lt / .22), pop=True)
    circ(d, (150, 290), 98, GOLD, 8, clamp((lt - .05) / .28), 82, tq, 3.0, 30)
    w3(cv, t3('s3t', 'ROZ 2 GHANTE', 88, CHALK, MARKER, 14), W / 2 + 110, 290,
       clamp((lt - .07) / .3), rot=-1.5, sweep=(lt - .9) / 1.3)
    cx, cy, cr = 320, 640, 158
    circ(d, (cx, cy), cr, CYAN, 10, clamp((lt - .1) / .4), 131, tq, 2.4, 40)
    for i in range(12):
        a = math.radians(i * 30)
        poly(d, [(cx + (cr - 30) * math.sin(a), cy - (cr - 30) * math.cos(a)),
                 (cx + (cr - 10) * math.sin(a), cy - (cr - 10) * math.cos(a))],
             CYAN, 6, clamp((lt - .32 - i * .022) / .25), 140 + i, tq, 1.4)
    sweep = clamp((lt - 1.1) / 2.2)
    ha = math.radians(sweep * 720)
    for k in range(3):   # motion trail on the fast hand
        aa = ha * 12 - k * .22
        poly(d, [(cx, cy), (cx + cr * .78 * math.sin(aa), cy - cr * .78 * math.cos(aa))],
             tuple(int(c * (.3 - k * .08)) for c in CHALK), 6, 1, 152 + k, tq, 1.2)
    poly(d, [(cx, cy), (cx + cr * .55 * math.sin(ha), cy - cr * .55 * math.cos(ha))], GOLD, 10, 1, 151, tq, 1.2)
    poly(d, [(cx, cy), (cx + cr * .78 * math.sin(ha * 12), cy - cr * .78 * math.cos(ha * 12))], CHALK, 7, 1, 153, tq, 1.2)
    w3(cv, t3('s3h', '2h DAILY', 62, GOLD, MARKER, 10), cx, cy + 222, clamp((lt - 1.4) / .4))
    gy2 = 870
    poly(d, [(640, gy2), (1010, gy2)], (120, 132, 155), 6, clamp((lt - .18) / .3), 23, tq)
    box(d, 700, gy2 - 150, 960, gy2 - 136, (165, 177, 200), 7, clamp((lt - .25) / .3), 98, tq)
    stick(d, 726, gy2 - 150 + .42 * 330, 330, pose_type(lt * 1.25), CHALK, 8, 37, tq, clamp((lt - .18) / .35), 'neutral')
    laptop(d, 912, gy2 - 150, 118, tq, 99, clamp((lt - 1.0) / .6))
    for i in range(3):
        sp = ((lt * 1.6 + i * .5) % 1.2)
        if lt > 2.2 and sp < .8:
            circ(d, (700 + i * 16, gy2 - 420 + sp * 110), 8, CYAN, 5, 1, 220 + i, tq, 1.2, 10)
    ox, oy, cw = 265, 990, 112
    box(d, ox - 38, oy - 54, ox + cw * 5 + 38, oy + cw * 6 - 30, (170, 182, 205), 7, clamp((lt - .55) / .45), 161, tq)
    done_f = clamp((lt - 1.6) / 3.0) * 30
    done = int(done_f)
    for i in range(30):
        r, c = divmod(i, 5)
        x, y = ox + c * cw + cw / 2, oy + r * cw + cw / 2 - 30
        box(d, x - 40, y - 36, x + 40, y + 36, (120, 132, 155), 4, clamp((lt - 1.3 - i * .01) / .3), 170 + i, tq, 1.2)
        if i < done:
            cross(d, x, y, 27, MINT, clamp((lt - 1.6 - i * .1) / .22), tq, 200 + i, 7)
        if i == done and done_f - done > 0:
            dust(cv, x, y, (done_f - done), 7, MINT, 60)
    hrs = int(clamp((lt - 1.6) / 3.0) * 60)
    w3(cv, t3(f's3n{hrs//5}', f'{hrs} HOURS', 84, MINT, MARKER, 14), W / 2, 1740,
       clamp((lt - 1.9) / .4), rot=-1, sq=.1 * math.sin(lt * 14) * (1 if hrs < 60 else 0))
    if 4.5 < lt < 5.4:
        shockwave(cv, W / 2, 1740, (lt - 4.5) / .9, MINT, 560, 14)
        badge(cv, 'CONSISTENCY = POWER', W / 2, 1600, (lt - 4.6) / 1.3, MINT, 38)

def scene4(cv, lt, tq):
    d = ImageDraw.Draw(cv)
    write(cv, '3', 150, 296, 150, GOLD, HAND, rot=-4, p=clamp(lt / .22), pop=True)
    circ(d, (150, 290), 98, GOLD, 8, clamp((lt - .05) / .28), 83, tq, 3.0, 30)
    w3(cv, t3('s4t', 'SAMPLE BANAO', 88, CHALK, MARKER, 14), W / 2 + 110, 290,
       clamp((lt - .07) / .3), rot=-1.5, sweep=(lt - .9) / 1.3)
    gy = 1560
    poly(d, [(100, gy), (W - 100, gy)], (120, 132, 155), 7, clamp(lt / .22), 21, tq)
    for i in range(3):
        st = .3 + i * .45
        p = clamp((lt - st) / .5)
        if p <= 0: continue
        x = 230 + i * 310
        y = 700 + (i % 2) * 36 + math.sin(lt * 1.6 + i) * 8
        k = out_back(p, 2.2)
        sq = 1 + .25 * (1 - clamp(p * 1.6))
        hw, hh = 125 * k * sq, 150 * k / sq
        box(d, x - hw, y - hh, x + hw, y + hh, CHALK, 8, 1, 231 + i, tq)
        if p > .85:
            q = clamp((lt - st - .45) / .5)
            if i == 0:
                circ(d, (x, y - 40), 50, PINK, 7, q, 241, tq, 1.8, 20)
                poly(d, [(x - 80, y + 90), (x - 20, y + 10), (x + 30, y + 70), (x + 80, y + 20)], MINT, 7, q, 242, tq)
            elif i == 1:
                play_btn(d, x, y, 58, q, RED, tq, 243)
            else:
                box(d, x - 80, y - 90, x + 80, y - 40, CYAN, 6, q, 244, tq)
                for kk in range(3):
                    poly(d, [(x - 80, y - 10 + kk * 36), (x + 60, y - 10 + kk * 36)], CYAN, 6,
                         clamp(q * 3 - kk), 245 + kk, tq, 1.4)
            sparkle(cv, x + 110, y - 150, clamp((lt - st - .5) / .8), GOLD, 30)
        if p > .9:
            write(cv, ['POSTER', 'REEL', 'WEBSITE'][i], x, y + 196, 46, GOLD, HAND,
                  p=clamp((lt - st - .6) / .4))
        if .85 < p < 1.25: dust(cv, x, y + 160, (p - .85) / .4, 8, CHALK, 90)
    pst = trail_stick(d, W / 2, gy, 470, lambda tt: pose_point(tt, right=False, up=True), lt,
                      CHALK, 10, 39, tq, clamp((lt - .06) / .3), 'happy', 1)
    poly(d, [pst['hand_l'], (pst['hand_l'][0] - 20, pst['hand_l'][1] - 70)], GOLD, 8, clamp((lt - .6) / .3), 251, tq)
    p2 = clamp((lt - 2.5) / .5)
    if p2 > 0:
        write(cv, 'DEGREE nahi,', W / 2, 1690, 70, CHALK, HAND, rot=-1, p=p2)
        circle_mark(d, W / 2 - 110, 1690, 180, 54, clamp((lt - 2.8) / .5), RED, 7, tq)
        w3(cv, t3('s4b', 'KAAM bolta hai!', 82, GOLD, MARKER, 14), W / 2, 1800,
           clamp((lt - 3.0) / .45), rot=1, sweep=(lt - 3.4) / 1.0)
    if 3.0 < lt < 3.7:
        speed_lines(cv, (1 - (lt - 3.0) / .7) * .55, GOLD, 24, 560, W / 2, 1800)

def scene5(cv, lt, tq):
    d = ImageDraw.Draw(cv)
    write(cv, '4', 150, 296, 150, GOLD, HAND, rot=6, p=clamp(lt / .22), pop=True)
    circ(d, (150, 290), 98, GOLD, 8, clamp((lt - .05) / .28), 84, tq, 3.0, 30)
    w3(cv, t3('s5t', 'SERVICE BECHO', 88, CHALK, MARKER, 14), W / 2 + 110, 290,
       clamp((lt - .07) / .3), rot=-1.5, sweep=(lt - .9) / 1.3)
    px, py = W / 2, 800
    box(d, px - 220, py - 310, px + 220, py + 310, CHALK, 9, clamp((lt - .1) / .4), 261, tq)
    poly(d, [(px - 50, py - 280), (px + 50, py - 280)], CHALK, 7, clamp((lt - .3) / .25), 262, tq)
    msgs = [('Hi! Reels edit karta hu', 1.3, CYAN, -1),
            ('Rate kya hai?', 2.0, CHALK, 1),
            ('Deal! Invoice bhejo', 2.7, MINT, -1)]
    for i, (m, st, col, side) in enumerate(msgs):
        p = clamp((lt - st) / .4)
        if p <= 0: continue
        by = py - 170 + i * 150
        bx = px + side * 60 + side * 240 * (1 - out_back(p, 1.8))
        box(d, bx - 180, by - 52, bx + 180, by + 52, col, 6, clamp(p * 2), 271 + i, tq, 1.8)
        write(cv, m, bx, by, 32, col, HAND, p=clamp((p - .3) / .5))
        if i == 2 and p > .5:
            sparkle(cv, bx + 200, by, clamp((lt - st - .3) / .7), MINT, 28)
    for i, nm in enumerate(['FIVERR', 'UPWORK', 'INSTA']):
        p = clamp((lt - 3.4 - i * .25) / .5)
        if p <= 0: continue
        x = 230 + i * 310
        k = out_back(p, 2.2)
        box(d, x - 130 * k, 1300, x + 130 * k, 1400, GOLD, 7, 1, 281 + i, tq)
        write(cv, nm, x, 1350, 46, GOLD, HAND, p=clamp((p - .3) / .5))
    gy = 1790
    poly(d, [(80, gy), (W - 80, gy)], (120, 132, 155), 7, 1, 21, tq)
    ph = clamp((lt - 4.2) / .5)
    if ph > 0:
        a = stick(d, W / 2 - 180, gy, 400, pose_shake(lt), CHALK, 9, 43, tq, ph, 'happy')
        b = stick(d, W / 2 + 180, gy, 400, {**pose_shake(lt + .3), 'ar': 18, 'er': 12, 'al': -74, 'el': -14},
                  CHALK, 9, 47, tq, ph, 'happy')
        poly(d, [a['hand_r'], b['hand_l']], GOLD, 8, clamp((lt - 4.6) / .25), 291, tq, 1.6)
        if 4.6 < lt < 5.3:
            comic_burst(cv, W / 2, gy - 190, (lt - 4.6) / .7, 'DEAL!', GOLD, 72, 180)
            shockwave(cv, W / 2, gy - 190, (lt - 4.6) / .8, GOLD, 480, 12)
        for i in range(5):
            cp = clamp((lt - 4.85 - i * .14) / .9)
            if cp > 0:
                cxx = W / 2 - 120 + i * 60
                coin(d, cxx, 1430 + cp * 260, 34, tq, 300 + i, 1, GOLD, lt * 5 + i)
                sparkle(cv, cxx, 1430 + cp * 260, cp, GOLD, 22)
    w3(cv, t3('s5d', '10 DM / DAY', 72, MINT, MARKER, 12), W / 2, 1190, clamp((lt - 3.0) / .45), rot=-1.5)
    if 3.0 < lt < 3.6: speed_lines(cv, (1 - (lt - 3.0) / .6) * .5, MINT, 22, 460, W / 2, 1190)

def scene6(cv, lt, tq):
    d = ImageDraw.Draw(cv)
    for i in range(22):
        sp = .5 + hsh(i * 3.7) * .8
        y = ((lt * sp * .4 + hsh(i * 1.3)) % 1.18) * (H + 300) - 150
        x = 60 + hsh(i * 7.1) * (W - 120)
        if y < -60: continue
        r = 26 + hsh(i * 2.2) * 20
        coin(d, x, y, r, tq, 320 + i, 1, GOLD, lt * 4 + i)
        if hsh(i * 5.5) > .6: sparkle(cv, x, y, ((lt * .9 + hsh(i)) % 1.0), GOLD, 18)
    gy = 1760
    poly(d, [(90, gy), (W - 90, gy)], (120, 132, 155), 7, 1, 21, tq)
    bounce = abs(math.sin(lt * 5.2)) * 30
    s_man = trail_stick(d, W / 2, gy - bounce, 470, pose_dance, lt, CHALK, 11, 53, tq,
                        clamp(lt / .22), 'happy', 2, .05)
    if lt > 2.2:
        crown(d, s_man['head'][0], s_man['head'][1] - 78, 46, GOLD, clamp((lt - 2.2) / .4))
    if abs(math.sin(lt * 5.2)) < .12:
        dust(cv, W / 2, gy, ((lt * 5.2 / math.pi) % 1.0), 8, CHALK, 90)
    w3(cv, t3('s6a', 'AAJ HI SHURU', 110, CHALK, MARKER, 18), W / 2, 420, clamp(lt / .28),
       rot=-2, sweep=(lt - .8) / 1.3)
    w3(cv, t3('s6b', 'KARO!', 112, GOLD, MARKER, 20), W / 2, 548, clamp((lt - .16) / .3),
       rot=1.5, sweep=(lt - 1.0) / 1.2)
    squiggle(d, 300, 628, 780, GOLD, 8, clamp((lt - .85) / .5), 331, tq)
    if .3 < lt < 1.1:
        speed_lines(cv, (1 - (lt - .3) / .8) * .8, GOLD, 30, 540, W / 2, 500)
        shockwave(cv, W / 2, 548, (lt - .3) / .8, GOLD, 760, 16)
    for i, (txt, st, col) in enumerate([('SKILL', 1.2, CYAN), ('TIME', 1.5, MINT),
                                        ('SAMPLES', 1.8, PINK), ('SELL', 2.1, GOLD)]):
        p = clamp((lt - st) / .4)
        if p <= 0: continue
        x = 180 + i * 240
        write(cv, txt, x, 790, 48, col, HAND, p=clamp(p * 2))
        tick(d, x, 858, 22, col, clamp(p * 2 - .6), tq, 340 + i)
        sparkle(cv, x, 858, clamp((lt - st - .2) / .7), col, 26)
    p2 = clamp((lt - 2.6) / .45)
    if p2 > 0:
        pulse = 1 + .03 * math.sin(lt * 7)
        box(d, 170, 960, W - 170, 1105, MINT, 8, clamp(p2 * 2), 351, tq)
        w3(cv, t3('s6c', 'FOLLOW = PART 2', 62, MINT, MARKER, 10), W / 2, 1032, p2, scale=pulse)
    p3 = clamp((lt - 3.3) / .45)
    if p3 > 0:
        write(cv, 'SAVE karo, bhool jaoge!', W / 2, 1175, 54, CHALK, HAND, rot=-1, p=p3)
        flame(d, 230, 1175, 34, lt, RED, p3)
        flame(d, W - 230, 1175, 34, lt + .7, GOLD, p3)
    for i in range(9):   # fireworks
        cp = clamp((lt - 2.9 - i * .09) / 1.3)
        if cp <= 0 or cp >= 1: continue
        a = -math.pi / 2 + (i - 4) * .3
        r = 480 * out_expo(cp)
        star(d, W / 2 + r * math.cos(a) * 1.25, 1450 + r * math.sin(a), 24 * (1 - cp * .4),
             [GOLD, PINK, CYAN, MINT][i % 4], 1, tq, 360 + i, 5)
    if lt > 4.6:
        comic_burst(cv, W / 2, 1450, (lt - 4.6) / 1.1, 'LET\u2019S GO!', GOLD, 70, 210)

SCENES = [scene1, scene2, scene3, scene4, scene5, scene6]

# ===================================================== transitions
MW, MH = W // 2, H // 2
_my, _mx = np.mgrid[0:MH, 0:MW].astype(np.float32)
def trans_mask(kind, p):
    """white = new scene"""
    if kind == 0:     # ink blob iris
        ang = np.arctan2(_my - MH * .62, _mx - MW * .5)
        rad = np.sqrt((_mx - MW * .5) ** 2 + (_my - MH * .62) ** 2)
        wob = 1 + .16 * np.sin(ang * 5) + .08 * np.sin(ang * 9 + 1.3)
        m = (rad < (p ** 1.25) * 700 * wob).astype(np.float32)
    elif kind == 1:   # paint strokes sweeping down
        m = np.zeros((MH, MW), np.float32)
        cols = 7
        bounds = [int(round(i * MW / cols)) for i in range(cols + 1)]
        for c in range(cols):
            a, b = bounds[c], bounds[c + 1]
            pp = clamp((p - c * .05) / .72)
            edge = MH * pp * 1.3 + 40 * math.sin(c * 2.1)
            m[:, a:b] = (_my[:, a:b] < edge).astype(np.float32)
    elif kind == 2:   # eraser wipe (horizontal, noisy edge)
        edge = (p * 1.3 - .15) * MW
        noise = 26 * np.sin(_my * .06) + 18 * np.sin(_my * .013 + 2)
        m = (_mx < edge + noise).astype(np.float32)
    elif kind == 3:   # vertical zip from centre
        half = p ** .85 * MH * .75
        m = (np.abs(_my - MH * .5) < half).astype(np.float32)
    else:             # diagonal whip
        m = ((_mx * .6 + _my * .4) < p * (MW * .6 + MH * .4) * 1.15).astype(np.float32)
    img = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8), 'L')
    img = img.filter(ImageFilter.GaussianBlur(5))
    return img.resize((W, H), Image.BILINEAR)

TKIND = [0, 1, 2, 3, 4]
TDUR = 0.34

# ===================================================== post
def bloom(arr, amount=.5, thr=168):
    small = Image.fromarray(arr.astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    a = np.clip(np.asarray(small).astype(np.float32) - thr, 0, None) * (255 / (255 - thr))
    b = Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(15))
    b2 = b.filter(ImageFilter.GaussianBlur(32))
    up = (np.asarray(b.resize((W, H), Image.BILINEAR)).astype(np.float32) * .6 +
          np.asarray(b2.resize((W, H), Image.BILINEAR)).astype(np.float32) * .5)
    return arr + up * amount

def grade(arr):
    lum = (arr[..., 0] * .299 + arr[..., 1] * .587 + arr[..., 2] * .114)[..., None] / 255.
    arr = arr + (1 - lum) * np.array([-3, 1, 11], np.float32) + lum * np.array([13, 5, -7], np.float32)
    x = np.clip(arr / 255., 0, 1)
    x = x * x * (3 - 2 * x) * .3 + x * .7
    return x * 255.

def camera(t):
    si = max(k for k in range(6) if t >= SCENE_START[k])
    lt = t - SCENE_START[si]
    dur = SCENE_END[si] - SCENE_START[si]
    zoom = 1.025 + .05 * (lt / dur) ** 1.05
    shx = 7 * math.sin(t * 2.0) + 4 * math.sin(t * 5.1 + 1)
    shy = 6 * math.sin(t * 1.6 + .5) + 3 * math.sin(t * 4.3 + 2)
    rot = .3 * math.sin(t * 1.1)
    flash = aberr = smear = 0.
    for c in CUTS:
        dd = t - c
        if -.2 <= dd <= .34:
            k = clamp(1 - abs(dd) / .26)
            flash = max(flash, .34 * k ** 2)
            aberr = max(aberr, 9 * k)
            smear = max(smear, 14 * k if dd < 0 else 7 * k)
            shx += 26 * k * math.sin(dd * 88); shy += 18 * k * math.cos(dd * 70)
            rot += 1.4 * k * math.sin(dd * 52)
    bp = (t % (60 / 112.)) / (60 / 112.)
    zoom += .01 * math.exp(-6 * bp)
    return zoom, shx, shy, rot, flash, aberr, smear

def scene_layer(si, t, tq, lt=None):
    cv = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    SCENES[si](cv, (t - SCENE_START[si]) if lt is None else lt, tq)
    return cv

def render(i):
    t = i / FPS
    tq = i // TQ
    si = max(k for k in range(6) if t >= SCENE_START[k])
    # ---- background
    mixn, nsi = 0.0, None
    for k, c in enumerate(CUTS):
        if c - .25 <= t < c + TDUR:
            nsi = k + 1; mixn = clamp((t - (c - .25)) / (TDUR + .25))
    bg = BOARD.convert('RGBA').copy()
    bg.alpha_composite(wash(t, si, nsi, mixn).convert('RGBA'))
    gy = int((t * 26) % 135)
    bg.alpha_composite(GRID, (0, -gy))
    dy = int((t * 34) % 600)
    bg.alpha_composite(DOODLES, (0, -dy))
    # ---- scene content (+ transition composite)
    layer = None
    for k, c in enumerate(CUTS):
        if c <= t < c + TDUR:
            p = (t - c) / TDUR
            old = scene_layer(k, 0, tq, lt=SCENE_END[k] - SCENE_START[k] - .001)
            new = scene_layer(k + 1, t, tq)
            m = trans_mask(TKIND[k], p)
            layer = Image.composite(new, old, m)
            # ink edge sparkle
            d = ImageDraw.Draw(layer)
            if TKIND[k] == 0:
                r = p ** 1.25 * 1400
                d.ellipse([W / 2 - r, H * .62 - r, W / 2 + r, H * .62 + r],
                          outline=ACCENT[k + 1] + (190,), width=10)
            elif TKIND[k] == 2:
                x = (p * 1.3 - .15) * W
                d.line([(x, 0), (x, H)], fill=CHALK + (170,), width=12)
            break
    if layer is None:
        layer = scene_layer(si, t, tq)
    hud(layer, t, tq)
    # chalk glow
    glow = layer.filter(ImageFilter.GaussianBlur(13))
    bg.alpha_composite(Image.blend(Image.new('RGBA', (W, H), (0, 0, 0, 0)), glow, .42))
    bg.alpha_composite(layer)
    frame = bg.convert('RGB')
    zoom, shx, shy, rot, flash, aberr, smear = camera(t)
    if smear > .5:
        a = np.asarray(frame).astype(np.float32); acc = np.zeros_like(a)
        for k in range(5): acc += np.roll(a, int((k - 2) * smear), axis=1)
        frame = Image.fromarray((acc / 5).astype(np.uint8))
    zw, zh = int(W * zoom), int(H * zoom)
    frame = frame.resize((zw, zh), Image.BILINEAR)
    if abs(rot) > .03: frame = frame.rotate(rot, Image.BILINEAR)
    ox = max(0, min(zw - W, (zw - W) // 2 + int(shx)))
    oy = max(0, min(zh - H, (zh - H) // 2 + int(shy)))
    frame = frame.crop((ox, oy, ox + W, oy + H))
    arr = np.asarray(frame).astype(np.float32)
    if aberr > .3:
        s = int(aberr)
        arr[..., 0] = np.roll(arr[..., 0], s, axis=1)
        arr[..., 2] = np.roll(arr[..., 2], -s, axis=1)
    arr = bloom(arr)
    arr = grade(arr)
    arr *= VIGN
    if flash > .004: arr += np.array([255, 248, 232], np.float32) * flash
    # paper jitter
    jx = int((hsh(tq * 1.1) - .5) * 4); jy = int((hsh(tq * 2.3 + 4) - .5) * 4)
    arr = np.roll(np.roll(arr, jx, 1), jy, 0)
    arr += np.repeat(np.repeat(GRAIN, 2, 0), 2, 1)[:H, :W] * 4.5
    return np.clip(arr, 0, 255).astype(np.uint8)

def main():
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    p = subprocess.Popen([ff, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'faster', '-crf', '18',
                          '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(NF):
        p.stdin.write(render(i).tobytes())
        if i % 60 == 0: print(f'frame {i}/{NF}', flush=True)
    p.stdin.close(); p.wait(); print('done')

if __name__ == '__main__':
    main()
