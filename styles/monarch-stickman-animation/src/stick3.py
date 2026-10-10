"""
STICK3 — the v4 "elite" renderer.
=================================
Rebuilds all six scenes around ONE locked hero character and a per-scene
colour theme, with kinetic captions, premium HUD furniture, 9 transitions
and a real colour grade.

Does NOT touch stick2.py / stickbase.py — their sha256 still gates the old
build in verify.py.

Run:   python3 src/stick3.py            (single process)
       python3 src/stick3.py A B OUT    (render frames [A,B) to raw file)
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, '/home/user/src')
from stickbase import (W, H, FPS, CHALK, GOLD, CYAN, MINT, RED, PINK, BOARD, GRAIN,
                       TQ, clamp, out_back, out_cubic, out_expo, in_cubic, ease, hsh,
                       poly, circ, arc, box, squiggle, arrow, star, tick, cross, coin,
                       laptop, play_btn, speech, stick, ft, text_img, put, write,
                       MARKER, HAND, CAVEAT,
                       pose_idle, pose_sad, pose_type, pose_point, pose_walk,
                       pose_shake, pose_dance, pose_cheer, pose_think)
from timeline import SCENE_START, SCENE_END, DUR_TOTAL
import fx
from fx import (THEME, VIOLET, ORANGE, LIME, ICE, STEEL, SPB, beat_pulse, beat_phase,
                lerp_col, theme_wash, particles, corner_hud, progress_rail, scene_chip,
                label_tag, caption, counter, ring, glow_underline, confetti,
                light_sweep, radial_burst, shock_ring, trans_mask, trans_edge,
                bloom, halation, grade, chroma, vignette)
import character as CH
from character import hero, EXPR, CHAR, HERO_SEED

NF = int(FPS * DUR_TOTAL)
OUT = '/home/user/build/stick3_silent.mp4'
CUTS = SCENE_START[1:]
MARK = 'cap'                      # the chosen identity marker
HANDLE = '@YOURHANDLE'

# ═══════════════════════════════════════════════ 3D marker type (kept, retuned)
class T3:
    _c = {}
    def __init__(self, txt, size, col, fontp=MARKER, depth=16, dvec=(.45, .95), glow_a=140):
        f = ft(fontp, size)
        bb = f.getbbox(txt)
        pad = 74 + depth
        iw, ih = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
        pos = (pad - bb[0], pad - bb[1])
        m = Image.new('L', (iw, ih), 0)
        ImageDraw.Draw(m).text(pos, txt, font=f, fill=255)
        mo = Image.new('L', (iw, ih), 0)
        ImageDraw.Draw(mo).text(pos, txt, font=f, fill=255, stroke_width=7, stroke_fill=255)
        img = Image.new('RGBA', (iw, ih), (0, 0, 0, 0))
        gl = Image.new('RGBA', (iw, ih), col + (0,))
        gl.putalpha(mo.filter(ImageFilter.GaussianBlur(28)).point(
            lambda v: min(255, int(v * 2.0 * glow_a / 255))))
        img.alpha_composite(gl)
        side = tuple(max(0, int(c * .32)) for c in col)
        for i in range(depth, 0, -1):
            k = i / depth
            c = tuple(int(s * (.42 + .58 * (1 - k))) for s in side)
            lay = Image.new('RGBA', (iw, ih), c + (255,)); lay.putalpha(mo)
            img.alpha_composite(ImageChops.offset(lay, int(dvec[0] * i), int(dvec[1] * i)))
        dark = Image.new('RGBA', (iw, ih), (9, 12, 18, 255)); dark.putalpha(mo)
        img.alpha_composite(dark)
        face = Image.new('RGBA', (iw, ih), col + (255,)); face.putalpha(m)
        img.alpha_composite(face)
        self.img, self.size = img, (iw, ih)
        self._ma = np.asarray(m, np.float32) / 255.0

    def sweep(self, phase, width=.13, strength=232):
        iw, ih = self.size
        xs = np.linspace(0, 1, iw)[None, :]; ys = np.linspace(0, 1, ih)[:, None]
        band = np.exp(-((xs + .3 * ys - phase * 1.6) ** 2) / (2 * width ** 2))
        a = (band * self._ma * strength).clip(0, 255).astype(np.uint8)
        sw = Image.new('RGBA', (iw, ih), (255, 255, 255, 0)); sw.putalpha(Image.fromarray(a, 'L'))
        out = self.img.copy(); out.alpha_composite(sw); return out


def t3(key, *a, **k):
    if key not in T3._c:
        T3._c[key] = T3(*a, **k)
        if len(T3._c) > 60:
            T3._c.pop(next(iter(T3._c)))
    return T3._c[key]


def w3(cv, obj, cx, cy, p=1., scale=1., rot=0., sq=0., sweep=None, alpha=None, pop=True):
    if p <= 0: return
    e = out_back(p, 2.4) if pop else clamp(p)
    sc = scale * (0.4 + 0.6 * e)
    a = clamp(p * 3) if alpha is None else alpha
    img = obj.sweep(sweep) if sweep is not None and 0 <= sweep <= 1.4 else obj.img
    wsq = 1 + sq
    im = img.resize((max(2, int(img.width * sc * wsq)), max(2, int(img.height * sc / max(.2, wsq)))),
                    Image.BILINEAR)
    if rot: im = im.rotate(rot, Image.BICUBIC, expand=True)
    if a < .99:
        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    cv.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


# ═══════════════════════════════════════════════ baked background layers
def build_doodles():
    lay = Image.new('RGBA', (W, H + 600), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(46):
        x = hsh(i * 3.1) * W; y = hsh(i * 7.7) * (H + 600)
        s = 18 + hsh(i * 2.3) * 34
        col = [CHALK, GOLD, CYAN, MINT, PINK][i % 5] + (30,)
        k = i % 5
        if k == 0: circ(d, (x, y), s, col, 4, 1, i, 0, 2, 16)
        elif k == 1: star(d, x, y, s, col, 1, 0, i, 4)
        elif k == 2:
            d.text((x, y), '$', font=ft(MARKER, int(s * 2.4)), fill=col, anchor='mm')
        elif k == 3: poly(d, [(x - s, y + s), (x, y - s), (x + s, y + s)], col, 4, 1, i, 0, 2)
        else: squiggle(d, x - s, y, x + s, col, 4, 1, i, 0, 2, 5, 8)
    return lay


def build_grid():
    lay = Image.new('RGBA', (W, H + 240), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for x in range(0, W, 135): d.line([(x, 0), (x, H + 240)], fill=(255, 255, 255, 9), width=2)
    for y in range(0, H + 240, 135): d.line([(0, y), (W, y)], fill=(255, 255, 255, 9), width=2)
    return lay


DOODLES = build_doodles()
GRID = build_grid()

# ═══════════════════════════════════════════════ hero helpers
def hero_t(d, x, y, s, posef, lt, expr, p=1.0, tq=0, trails=2, dt=.055, **kw):
    """Hero with motion ghosts. Ghosts carry no face and no marker — they must
    read as speed, not as extra people."""
    if p > .25:
        for i in range(trails, 0, -1):
            g = .30 + .10 * (1 - i / (trails + 1))
            c = tuple(int(c0 * g) for c0 in CHALK)
            hero(d, x, y, s, posef(lt - i * dt), 'neutral', None, col=c,
                 w=max(3, int(10 * s / 600) - 3), tq=tq, p=p, seed=HERO_SEED + 500 + i,
                 hoodie=False, hands=False, t=lt)
    return hero(d, x, y, s, posef(lt), expr, MARK, tq=tq, p=p, t=lt,
                blink=CH.blink_at(lt), **kw)


def ground(d, y, p, tq, col=(118, 130, 154), x0=96, x1=None):
    x1 = W - 96 if x1 is None else x1
    poly(d, [(x0, y), (x1, y)], col, 7, p, 21, tq)


def title3(cv, key, txt, lt, th, y=300, size=92, delay=.07, x=None):
    w3(cv, t3(key, txt, size, CHALK, MARKER, 14), W / 2 + 108 if x is None else x, y,
       clamp((lt - delay) / .30), rot=-1.5, sweep=(lt - .9) / 1.3)


def step_badge(cv, d, n, lt, th, tq):
    p = clamp(lt / .22)
    write(cv, str(n), 150, 296, 150, th['key'], HAND, rot=-6 + n * 3, p=p, pop=True)
    circ(d, (150, 290), 98, th['key'], 8, clamp((lt - .05) / .28), 80 + n, tq, 3.0, 30)
    circ(d, (150, 290), 112, th['key'] + (70,), 4, clamp((lt - .22) / .4), 70 + n, tq, 2.2, 26)


# ═══════════════════════════════════════════════ kinetic captions
# (t0, t1, text, hot-word index) in scene-local time
CAPS = [
    [(0.45, 2.05, 'JEB KHALI? BANK ZERO?', 2),
     (2.15, 3.65, 'AB BAHANA KHATAM', 2),
     (3.75, 5.45, '4 STEP KA PURA PLAN', 1)],
    [(0.45, 2.35, 'PEHLE EK SKILL CHUNO', 2),
     (2.45, 4.45, 'DESIGN VIDEO CODE YA AI', 0),
     (4.55, 7.10, 'YOUTUBE HI TUMHARI UNIVERSITY HAI', 0)],
    [(0.45, 2.45, 'ROZ SIRF DO GHANTE DO', 2),
     (2.55, 4.45, 'TEES DIN = SATH GHANTE', 4),
     (4.55, 6.55, 'CONSISTENCY HI ASLI POWER HAI', 0)],
    [(0.40, 2.05, 'TEEN SAMPLE KHUD BANAO', 1),
     (2.15, 4.55, 'DEGREE NAHI, KAAM BOLTA HAI', 2)],
    [(0.40, 2.30, 'AB SERVICE BECHNA SEEKHO', 1),
     (2.40, 4.20, 'ROZ DAS DM BHEJO', 2),
     (4.30, 6.40, 'PEHLA CLIENT = PEHLA PAISA', 4)],
    [(0.35, 2.15, 'AAJ HI SHURU KARO', 2),
     (2.25, 3.95, 'SKILL TIME SAMPLE SELL', 0),
     (4.05, 6.10, 'SAVE KARO AUR FOLLOW KARO', 1)],
]
CAP_Y = 1706


def draw_caption(cv, si, lt, th):
    for t0, t1, txt, hot in CAPS[si]:
        if t0 <= lt < t1:
            caption(cv, txt, (lt - t0) / (t1 - t0), CAP_Y, th, 54, hot)
            return


# ═══════════════════════════════════════════════════════════ SCENE 1
def scene1(cv, lt, tq):
    th = THEME[0]
    d = ImageDraw.Draw(cv)
    gy = 1430
    ground(d, gy, clamp((lt + .16) / .22), tq)     # ERRATA E-frame0: alive at lt=0

    w_in = clamp(lt / .85)
    hx = 98 + (W / 2 - 70 - 98) * out_cubic(w_in)   # ERRATA E-frame0: on-stage at lt=0
    if w_in < 1:
        st = hero_t(d, hx, gy, 560, pose_walk, lt, 'worried', 1, tq, 2)
    else:
        st = hero_t(d, W / 2 - 70, gy, 560, lambda tt: pose_sad(tt - .85), lt,
                    'sad' if lt > 1.5 else 'worried', 1, tq, 0)

    # headline
    tp = clamp((lt + .30) / .62)                   # ERRATA E-frame0: p=0.48 at lt=0
    w3(cv, t3('s1a', 'JEB KHALI?', 122, CHALK, MARKER, 17), W / 2, 326,
       tp, rot=-2.5, sq=.14 * (1 - tp), sweep=(lt - 1.1) / 1.4)
    squiggle(d, 236, 424, 844, th['key'], 9, clamp((lt - .55) / .4), 7, tq)
    if lt < .55:
        radial_burst(cv, W / 2, 330, clamp((lt + .22) / .72), th['key'], 22, 300, 820, 7)

    # rain cloud
    cp = clamp((lt - 1.05) / .5)
    if cp > 0:
        cxx, cyy = W / 2 - 70, 700
        for k, (ox, oy, rr) in enumerate([(-70, 10, 56), (0, -16, 70), (72, 8, 52)]):
            circ(d, (cxx + ox, cyy + oy), rr, (164, 174, 198), 7, clamp(cp * 2 - k * .2),
                 41 + k, tq, 2.4, 20)
        if cp > .7:
            for k in range(6):
                dp = ((lt * 1.35 + k * .22) % 1.0)
                poly(d, [(cxx - 76 + k * 32, cyy + 72 + dp * 96),
                         (cxx - 80 + k * 32, cyy + 102 + dp * 96)],
                     th['third'], 5, 1, 45 + k, tq, 1.2)

    # empty pockets + Rs 0 bubble
    arc(d, (st['hip'][0] - 50, st['hip'][1] + 28), 25, 0, 180, CHALK, 7, clamp((lt - 1.2) / .4), 46, tq)
    arc(d, (st['hip'][0] + 50, st['hip'][1] + 28), 25, 0, 180, CHALK, 7, clamp((lt - 1.3) / .4), 47, tq)
    p2 = clamp((lt - 1.5) / .45)
    if p2 > 0:
        speech(d, W / 2 + 262, 860, 300, 184, (-.4, 1), p2, CHALK, tq, 51)
        w3(cv, t3('s1b', 'Rs 0', 94, th['key'], MARKER, 12), W / 2 + 262, 850,
           clamp((lt - 1.72) / .4), rot=-4)

    # doubt marks
    for i, (dx, dy, dl) in enumerate([(-330, 660, 1.85), (352, 540, 2.10), (-250, 450, 2.35)]):
        write(cv, '?', W / 2 + dx, dy + math.sin(lt * 2 + i) * 15, 112, th['third'], MARKER,
              rot=-10 + i * 9, p=clamp((lt - dl) / .4), pop=True)

    # the turn
    p3 = clamp((lt - 2.95) / .5)
    if p3 > 0:
        shock_ring(cv, W / 2, 1510, clamp((lt - 2.95) / .85), GOLD, 540, 15, 3)
        w3(cv, t3('s1c', 'PURA PLAN', 104, GOLD, MARKER, 19), W / 2, 1510, p3, rot=1.5,
           sweep=(lt - 3.35) / 1.2)
        label_tag(cv, '4 STEPS  \u00b7  FREE', W / 2, 1600, clamp((lt - 3.45) / .5), MINT, 34)
    if lt > 3.5:
        light_sweep(cv, clamp((lt - 3.5) / .9), (255, 236, 200), .14, 70)


# ═══════════════════════════════════════════════════════════ SCENE 2
def scene2(cv, lt, tq):
    th = THEME[1]
    d = ImageDraw.Draw(cv)
    step_badge(cv, d, 1, lt, th, tq)
    title3(cv, 's2t', 'SKILL SEEKHO', lt, th, 292, 94)

    # skill list
    skills = [('DESIGN', 1.30, th['key']), ('VIDEO EDIT', 1.68, MINT),
              ('CODING', 2.06, VIOLET), ('AI TOOLS', 2.44, GOLD)]
    for i, (txt, st, col) in enumerate(skills):
        p = clamp((lt - st) / .5)
        if p <= 0: continue
        y = 512 + i * 100
        k = out_back(min(1, p * 1.8), 2.0)
        x0 = 128 - 150 * (1 - k)
        d.rounded_rectangle([x0, y - 36, x0 + 392 * k, y + 36], 34,
                            fill=col + (30,), outline=col + (int(225 * clamp(p * 2)),), width=4)
        if p > .35:
            tick(d, x0 + 44, y, 19, col, clamp(p * 2 - .7), tq, 340 + i)
            write(cv, txt, x0 + 230, y - 2, 40, col, HAND, p=clamp((p - .3) / .4))

    # brain — NOTE seed moved to 401+ : 101-110 now belongs to the hero
    bp = clamp((lt - 1.25) / 2.9)
    bx, by = 836, 600
    circ(d, (bx, by), 92 + 5 * math.sin(lt * 4), th['key'], 8, clamp((lt - 1.0) / .5), 401, tq, 2.6, 26)
    for i in range(5):
        arc(d, (bx - 42 + i * 21, by - 10 + (i % 2) * 26), 27, 160, 380, th['key'], 6,
            clamp((bp - i * .17) * 3), 403 + i, tq, 1.4, 12)
    ring(d, bx, by, 124, bp, th['key'], 9)
    counter(cv, int(bp * 100), bx, by + 168, 52, th['key'], clamp((lt - 1.4) / .4), suffix='%', font=HAND)
    for k in range(7):
        sp = ((lt * .75 + k * .143) % 1.0)
        if lt > 1.5:
            a = -2.3 + k * .45
            r = 236 * (1 - sp)
            fx.star(d, bx + r * math.cos(a), by + r * math.sin(a) + 24, 13 * math.sin(sp * math.pi),
                    ICE, 1, tq, 410 + k, 4)

    # desk + hero working
    desk_y, gy = 1230, 1424
    box(d, W / 2 - 318, desk_y, W / 2 + 318, desk_y + 22, (162, 174, 198), 8, clamp((lt - .08) / .28), 91, tq)
    poly(d, [(W / 2 - 270, desk_y + 22), (W / 2 - 270, gy)], (162, 174, 198), 8, clamp((lt - .2) / .26), 92, tq)
    poly(d, [(W / 2 + 270, desk_y + 22), (W / 2 + 270, gy)], (162, 174, 198), 8, clamp((lt - .2) / .26), 93, tq)
    ground(d, gy, clamp(lt / .22), tq, x0=110, x1=W - 110)
    s_h, seat = 450, 1290
    box(d, W / 2 - 296, seat + 16, W / 2 - 152, gy, (148, 160, 184), 7, clamp((lt - .25) / .3), 94, tq)
    hero_t(d, W / 2 - 222, seat + .42 * s_h, s_h,
           lambda tt: (pose_think(tt) if tt < 1.15 else pose_type(tt)), lt,
           'think' if lt < 1.15 else 'focus', clamp((lt - .1) / .35), tq, 0)
    laptop(d, W / 2 + 92, desk_y, 236, tq, 95, clamp((lt - .8) / .8),
           screen=lambda dd, x, y, w_, h_, pp: play_btn(dd, x, y, 44 + 4 * math.sin(lt * 7), pp, RED, tq, 96))
    for k in range(3):
        sp = ((lt * 1.15 + k * .33) % 1.0)
        if lt > 1.0:
            write(cv, ['</>', '*', '~'][k], W / 2 + 64 + k * 40, desk_y - 110 - sp * 170, 34,
                  th['key'], HAND, p=1 - sp)
    arrow(d, (bx - 66, by + 150), (W / 2 - 150, 1020), th['third'], 7, clamp((lt - 3.3) / .6), 97, tq, .22)

    p5 = clamp((lt - 4.5) / .5)
    if p5 > 0:
        label_tag(cv, 'FREE  \u00b7  NO DEGREE  \u00b7  NO FEES', W / 2, 1560, clamp((lt - 4.6) / .6), MINT, 34)


# ═══════════════════════════════════════════════════════════ SCENE 3
def scene3(cv, lt, tq):
    th = THEME[2]
    d = ImageDraw.Draw(cv)
    step_badge(cv, d, 2, lt, th, tq)
    title3(cv, 's3t', 'ROZ 2 GHANTE', lt, th, 292, 90)

    # clock
    cx, cy, cr = 300, 614, 150
    circ(d, (cx, cy), cr, th['key'], 10, clamp((lt - .1) / .4), 131, tq, 2.4, 40)
    for i in range(12):
        a = math.radians(i * 30)
        poly(d, [(cx + (cr - 28) * math.sin(a), cy - (cr - 28) * math.cos(a)),
                 (cx + (cr - 10) * math.sin(a), cy - (cr - 10) * math.cos(a))],
             th['key'], 6, clamp((lt - .32 - i * .022) / .25), 140 + i, tq, 1.4)
    sweep = clamp((lt - 1.0) / 2.3)
    ha = math.radians(sweep * 720)
    for k in range(3):
        aa = ha * 12 - k * .22
        poly(d, [(cx, cy), (cx + cr * .76 * math.sin(aa), cy - cr * .76 * math.cos(aa))],
             tuple(int(c * (.30 - k * .08)) for c in CHALK), 6, 1, 152 + k, tq, 1.2)
    poly(d, [(cx, cy), (cx + cr * .54 * math.sin(ha), cy - cr * .54 * math.cos(ha))], GOLD, 10, 1, 151, tq, 1.2)
    poly(d, [(cx, cy), (cx + cr * .76 * math.sin(ha * 12), cy - cr * .76 * math.cos(ha * 12))],
         CHALK, 7, 1, 153, tq, 1.2)
    ring(d, cx, cy, cr + 30, sweep, th['sec'], 8)
    label_tag(cv, '2h / DAY', cx, cy + 222, clamp((lt - 1.3) / .4), GOLD, 36)

    # small hero grinding at a desk
    gy2 = 848
    poly(d, [(640, gy2), (1004, gy2)], (118, 130, 154), 6, clamp((lt - .18) / .3), 23, tq)
    box(d, 696, gy2 - 148, 956, gy2 - 134, (162, 174, 198), 7, clamp((lt - .25) / .3), 98, tq)
    hero_t(d, 730, gy2 - 148 + .42 * 320, 320, lambda tt: pose_type(tt * 1.25), lt,
           'determined', clamp((lt - .18) / .35), tq, 0)
    laptop(d, 912, gy2 - 148, 114, tq, 99, clamp((lt - 1.0) / .6))
    for i in range(3):
        sp = ((lt * 1.6 + i * .5) % 1.2)
        if lt > 2.1 and sp < .8:
            circ(d, (702 + i * 16, gy2 - 400 + sp * 108), 8, th['sec'], 5, 1, 220 + i, tq, 1.2, 10)

    # 30-day calendar
    ox, oy, cw = 258, 962, 110
    box(d, ox - 38, oy - 52, ox + cw * 5 + 38, oy + cw * 6 - 34, (166, 178, 202), 7,
        clamp((lt - .55) / .45), 161, tq)
    done_f = clamp((lt - 1.5) / 3.1) * 30
    done = int(done_f)
    for i in range(30):
        r, c = divmod(i, 5)
        x, y = ox + c * cw + cw / 2, oy + r * cw + cw / 2 - 32
        box(d, x - 39, y - 35, x + 39, y + 35, (116, 128, 152), 4,
            clamp((lt - 1.25 - i * .01) / .3), 170 + i, tq, 1.2)
        if i < done:
            cross(d, x, y, 26, th['sec'], clamp((lt - 1.5 - i * .1) / .22), tq, 200 + i, 7)
        elif i == done and done_f - done > .02:
            box(d, x - 39, y - 35, x + 39, y + 35, th['key'], 5, 1, 250 + i, tq, 1.4)

    hrs = int(clamp((lt - 1.5) / 3.1) * 60)
    w3(cv, t3(f's3n{hrs // 5}', f'{hrs} HOURS', 86, th['sec'], MARKER, 14), W / 2, 1530,
       clamp((lt - 1.85) / .4), rot=-1,
       sq=.09 * math.sin(lt * 14) * (1 if hrs < 60 else 0))
    if 4.4 < lt < 5.3:
        shock_ring(cv, W / 2, 1530, (lt - 4.4) / .9, th['sec'], 560, 14, 3)
        radial_burst(cv, W / 2, 1530, (lt - 4.4) / .8, th['sec'], 20, 220, 660, 7)


# ═══════════════════════════════════════════════════════════ SCENE 4
def scene4(cv, lt, tq):
    th = THEME[3]
    d = ImageDraw.Draw(cv)
    step_badge(cv, d, 3, lt, th, tq)
    title3(cv, 's4t', 'SAMPLE BANAO', lt, th, 292, 90)

    gy = 1430
    ground(d, gy, clamp(lt / .22), tq)

    for i in range(3):
        st = .28 + i * .42
        p = clamp((lt - st) / .5)
        if p <= 0: continue
        x = 226 + i * 314
        y = 672 + (i % 2) * 34 + math.sin(lt * 1.6 + i) * 8
        k = out_back(p, 2.2)
        sq = 1 + .25 * (1 - clamp(p * 1.6))
        hw, hh = 122 * k * sq, 146 * k / sq
        box(d, x - hw, y - hh, x + hw, y + hh, CHALK, 8, 1, 231 + i, tq)
        if p > .85:
            q = clamp((lt - st - .45) / .5)
            if i == 0:
                circ(d, (x, y - 38), 48, th['key'], 7, q, 241, tq, 1.8, 20)
                poly(d, [(x - 78, y + 88), (x - 20, y + 10), (x + 28, y + 68), (x + 78, y + 18)],
                     MINT, 7, q, 242, tq)
            elif i == 1:
                play_btn(d, x, y, 56, q, RED, tq, 243)
            else:
                box(d, x - 78, y - 88, x + 78, y - 38, th['sec'], 6, q, 244, tq)
                for kk in range(3):
                    poly(d, [(x - 78, y - 8 + kk * 34), (x + 58, y - 8 + kk * 34)], th['sec'], 6,
                         clamp(q * 3 - kk), 245 + kk, tq, 1.4)
            fx.star(d, x + 106, y - 146, 16 * math.sin(clamp((lt - st - .5) / .8) * math.pi),
                    GOLD, 1, tq, 260 + i, 5)
        if p > .9:
            label_tag(cv, ['POSTER', 'REEL', 'WEBSITE'][i], x, y + 196,
                      clamp((lt - st - .6) / .5), GOLD, 30)

    pst = hero_t(d, W / 2, gy, 470, lambda tt: pose_point(tt, right=False, up=True), lt,
                 'proud', clamp((lt - .06) / .3), tq, 1)
    poly(d, [pst['hand_l'], (pst['hand_l'][0] - 18, pst['hand_l'][1] - 66)], GOLD, 8,
         clamp((lt - .6) / .3), 251, tq)

    p2 = clamp((lt - 2.4) / .5)
    if p2 > 0:
        w3(cv, t3('s4b', 'KAAM bolta hai!', 84, GOLD, MARKER, 14), W / 2, 1540,
           clamp((lt - 2.5) / .45), rot=1, sweep=(lt - 2.9) / 1.0)
        if 2.5 < lt < 3.2:
            radial_burst(cv, W / 2, 1540, (lt - 2.5) / .7, GOLD, 22, 240, 700, 8)
    counter(cv, min(3, int(clamp((lt - .28) / 1.3) * 3.9)), 150, 460, 56, th['key'],
            clamp((lt - .5) / .4), suffix=' / 3', font=HAND)


# ═══════════════════════════════════════════════════════════ SCENE 5
def scene5(cv, lt, tq):
    th = THEME[4]
    d = ImageDraw.Draw(cv)
    step_badge(cv, d, 4, lt, th, tq)
    title3(cv, 's5t', 'SERVICE BECHO', lt, th, 292, 90)

    # phone
    px, py = W / 2, 712
    box(d, px - 216, py - 300, px + 216, py + 300, CHALK, 9, clamp((lt - .1) / .4), 261, tq)
    poly(d, [(px - 48, py - 272), (px + 48, py - 272)], CHALK, 7, clamp((lt - .3) / .25), 262, tq)
    msgs = [('Hi! Reels edit karta hu', 1.15, th['third'], -1),
            ('Rate kya hai?', 1.85, CHALK, 1),
            ('Deal! Invoice bhejo', 2.55, th['key'], -1)]
    for i, (m, st, col, side) in enumerate(msgs):
        p = clamp((lt - st) / .4)
        if p <= 0: continue
        by = py - 164 + i * 148
        bx = px + side * 56 + side * 236 * (1 - out_back(p, 1.8))
        box(d, bx - 176, by - 50, bx + 176, by + 50, col, 6, clamp(p * 2), 271 + i, tq, 1.8)
        write(cv, m, bx, by, 31, col, HAND, p=clamp((p - .3) / .5))
        if i == 2 and p > .6:
            fx.star(d, bx + 196, by, 14 * math.sin(clamp((lt - st - .3) / .7) * math.pi),
                    th['sec'], 1, tq, 279, 5)

    # platforms
    for i, nm in enumerate(['FIVERR', 'UPWORK', 'INSTA']):
        p = clamp((lt - 3.15 - i * .22) / .5)
        if p <= 0: continue
        label_tag(cv, nm, 226 + i * 314, 1142, min(p, .999), GOLD, 34, 30)
    label_tag(cv, '10 DM / DAY', W / 2, 1052, clamp((lt - 2.9) / .45), th['sec'], 34)

    # the handshake — hero stays the biggest figure in frame
    gy = 1596
    ground(d, gy, 1, tq, x0=80, x1=W - 80)
    ph = clamp((lt - 3.95) / .5)
    if ph > 0:
        a = hero_t(d, W / 2 - 168, gy, 392, pose_shake, lt, 'happy', ph, tq, 1)
        b = stick(d, W / 2 + 172, gy, 338,
                  {**pose_shake(lt + .3), 'ar': 18, 'er': 12, 'al': -74, 'el': -14},
                  (178, 188, 212), 7, 211, tq, ph, None)
        CH.face(d, b['head'], b['hr'], 338, 'happy', (178, 188, 212), 5, tq, 211)
        nx, ny = b['neck']
        poly(d, [(nx - b['hr'] * .62, ny - b['hr'] * .06), (nx, ny + b['hr'] * .46),
                 (nx + b['hr'] * .62, ny - b['hr'] * .06)], th['third'], 5, ph, 213, tq, 1.2)
        poly(d, [a['hand_r'], b['hand_l']], GOLD, 8, clamp((lt - 4.35) / .25), 291, tq, 1.6)
        if 4.35 < lt < 5.1:
            shock_ring(cv, W / 2, gy - 250, (lt - 4.35) / .8, GOLD, 440, 13, 3)
            w3(cv, t3('s5deal', 'DEAL!', 78, GOLD, MARKER, 13), W / 2, gy - 300,
               clamp((lt - 4.35) / .35) * (1 - clamp((lt - 4.9) / .3)), rot=-5)
        for i in range(6):
            cp = clamp((lt - 4.55 - i * .12) / .9)
            if cp > 0:
                cxx = W / 2 - 150 + i * 60
                coin(d, cxx, 1250 + cp * 240, 30, tq, 300 + i, 1, GOLD, lt * 5 + i)


# ═══════════════════════════════════════════════════════════ SCENE 6
def scene6(cv, lt, tq):
    th = THEME[5]
    d = ImageDraw.Draw(cv)

    for i in range(22):
        sp = .5 + hsh(i * 3.7) * .8
        y = ((lt * sp * .4 + hsh(i * 1.3)) % 1.18) * (H + 300) - 150
        x = 60 + hsh(i * 7.1) * (W - 120)
        if y < -60: continue
        coin(d, x, y, 24 + hsh(i * 2.2) * 19, tq, 320 + i, 1, GOLD, lt * 4 + i)

    gy = 1624
    ground(d, gy, 1, tq, x0=90, x1=W - 90)
    bounce = abs(math.sin(lt * 5.2)) * 24
    sm = hero_t(d, W / 2, gy - bounce, 376, pose_dance, lt, 'celebrate', clamp(lt / .22), tq, 2, .05)
    if lt > 2.0:
        cp = clamp((lt - 2.0) / .4)
        hxx, hyy = sm['head']
        s = 38
        hy2 = hyy - 66
        poly(d, [(hxx - s, hy2 + s * .5), (hxx - s, hy2 - s * .5), (hxx - s * .5, hy2),
                 (hxx, hy2 - s * .8), (hxx + s * .5, hy2), (hxx + s, hy2 - s * .5),
                 (hxx + s, hy2 + s * .5)], GOLD, 7, cp, 11.3, tq, 1.6, closed=True)

    w3(cv, t3('s6a', 'AAJ HI SHURU', 112, CHALK, MARKER, 18), W / 2, 408, clamp(lt / .28),
       rot=-2, sweep=(lt - .8) / 1.3)
    w3(cv, t3('s6b', 'KARO!', 114, GOLD, MARKER, 20), W / 2, 536, clamp((lt - .16) / .3),
       rot=1.5, sweep=(lt - 1.0) / 1.2)
    squiggle(d, 296, 616, 784, GOLD, 8, clamp((lt - .85) / .5), 331, tq)
    if .25 < lt < 1.1:
        radial_burst(cv, W / 2, 500, (lt - .25) / .85, GOLD, 28, 260, 900, 10)
        shock_ring(cv, W / 2, 536, (lt - .25) / .8, GOLD, 760, 16, 3)

    for i, (txt, st, col) in enumerate([('SKILL', 1.05, CYAN), ('TIME', 1.32, VIOLET),
                                        ('SAMPLE', 1.59, PINK), ('SELL', 1.86, MINT)]):
        p = clamp((lt - st) / .4)
        if p <= 0: continue
        x = 172 + i * 246
        write(cv, txt, x, 742, 46, col, HAND, p=clamp(p * 2))
        tick(d, x, 808, 22, col, clamp(p * 2 - .6), tq, 340 + i)

    p2 = clamp((lt - 2.45) / .45)
    if p2 > 0:
        pulse = 1 + .03 * math.sin(lt * 7)
        box(d, 166, 882, W - 166, 1016, th['third'], 8, clamp(p2 * 2), 351, tq)
        w3(cv, t3('s6c', 'FOLLOW = PART 2', 62, th['third'], MARKER, 10), W / 2, 950, p2, scale=pulse)
    p3 = clamp((lt - 3.15) / .45)
    if p3 > 0:
        label_tag(cv, 'SAVE karo, bhool jaoge!', W / 2, 1082, min(p3, .999), CHALK, 38, 30)

    confetti(cv, lt, clamp((lt - 2.7) / 2.6), th, W / 2, 560, 40)
    if lt > 4.3:
        shock_ring(cv, W / 2, 1330, (lt - 4.3) / 1.1, GOLD, 430, 13, 3)
        light_sweep(cv, clamp((lt - 4.4) / .8), (255, 240, 205), .13, 82)


SCENES = [scene1, scene2, scene3, scene4, scene5, scene6]
TKIND = [6, 5, 1, 8, 0]          # zoom-punch, glitch, paint, clock, ink-iris
TDUR = 0.34


# ═══════════════════════════════════════════════ HUD overlay
def hud(cv, t, si, th, tq):
    lt = t - SCENE_START[si]
    progress_rail(cv, t, DUR_TOTAL, CUTS, th, si)
    scene_chip(cv, si, lt, th)
    corner_hud(cv, t, th, clamp(t / .6))
    draw_caption(cv, si, lt, th)
    write(cv, HANDLE, W / 2, H - 78, 36, (176, 186, 206), HAND, p=1)


# ═══════════════════════════════════════════════ camera
# per-scene move: (zoom0, zoom1, driftx, drifty) — deliberate, varied
CAM = [(1.030, 1.085,  18, -10),
       (1.075, 1.028, -22,   8),
       (1.025, 1.080,  14,  16),
       (1.080, 1.030,  20, -14),
       (1.028, 1.078, -18,  10),
       (1.070, 1.020,   0, -20)]


def camera(t):
    si = max(k for k in range(6) if t >= SCENE_START[k])
    lt = t - SCENE_START[si]
    dur = SCENE_END[si] - SCENE_START[si]
    k = clamp(lt / dur)
    ke = k * k * (3 - 2 * k)
    z0, z1, dx, dy = CAM[si]
    zoom = z0 + (z1 - z0) * ke
    shx = dx * ke + 5 * math.sin(t * 2.0) + 3 * math.sin(t * 5.1 + 1)
    shy = dy * ke + 4 * math.sin(t * 1.6 + .5) + 2.5 * math.sin(t * 4.3 + 2)
    rot = .26 * math.sin(t * 1.1) + .12 * math.sin(t * 2.7 + 1.4)
    flash = aberr = smear = 0.
    for c in CUTS:
        dd = t - c
        # window matched to the falloff so no frame is inert (the v2 dead-code bug)
        if -.24 <= dd <= .26:
            kk = clamp(1 - abs(dd) / .26)
            flash = max(flash, .36 * kk ** 2)
            aberr = max(aberr, 11 * kk)
            smear = max(smear, 16 * kk if dd < 0 else 8 * kk)
            shx += 28 * kk * math.sin(dd * 88)
            shy += 20 * kk * math.cos(dd * 70)
            rot += 1.5 * kk * math.sin(dd * 52)
            zoom += .055 * kk ** 1.4
    bp = beat_phase(t)
    zoom += .013 * math.exp(-6 * bp)
    aberr += 1.1 + 1.6 * math.exp(-7 * bp)
    return zoom, shx, shy, rot, flash, aberr, smear


def scene_layer(si, t, tq, lt=None):
    cv = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    SCENES[si](cv, (t - SCENE_START[si]) if lt is None else lt, tq)
    return cv


# ═══════════════════════════════════════════════ frame
def render(i):
    t = i / FPS
    tq = i // TQ
    si = max(k for k in range(6) if t >= SCENE_START[k])
    pulse = beat_pulse(t, 6.0)

    # ---- which theme (cross-faded through the cut)
    nsi, mixn = None, 0.0
    for k, c in enumerate(CUTS):
        if c - .25 <= t < c + TDUR:
            nsi = k + 1
            mixn = clamp((t - (c - .25)) / (TDUR + .25))
    th = THEME[si]
    th2 = THEME[nsi] if nsi is not None else None

    # ---- background
    bg = BOARD.convert('RGBA').copy()
    bg.alpha_composite(theme_wash(t, si, nsi, mixn, pulse).convert('RGBA'))
    bg.alpha_composite(GRID, (0, -int((t * 26) % 135)))
    bg.alpha_composite(DOODLES, (0, -int((t * 34) % 600)))
    particles(bg, t, th2 if (th2 and mixn > .5) else th, 1.0, pulse)

    # ---- scene content
    layer = None
    for k, c in enumerate(CUTS):
        if c <= t < c + TDUR:
            p = (t - c) / TDUR
            old = scene_layer(k, 0, tq, lt=SCENE_END[k] - SCENE_START[k] - .001)
            new = scene_layer(k + 1, t, tq)
            layer = Image.composite(new, old, trans_mask(TKIND[k], p))
            trans_edge(layer, TKIND[k], p, THEME[k + 1]['key'])
            break
    if layer is None:
        layer = scene_layer(si, t, tq)

    hud(layer, t, si, th2 if (th2 and mixn > .62) else th, tq)

    # ---- chalk glow
    glow = layer.filter(ImageFilter.GaussianBlur(13))
    bg.alpha_composite(Image.blend(Image.new('RGBA', (W, H), (0, 0, 0, 0)), glow, .44))
    bg.alpha_composite(layer)
    frame = bg.convert('RGB')

    # ---- camera
    zoom, shx, shy, rot, flash, aberr, smear = camera(t)
    if smear > .5:
        a = np.asarray(frame).astype(np.float32)
        acc = np.zeros_like(a)
        for k in range(5):
            acc += np.roll(a, int((k - 2) * smear), axis=1)
        frame = Image.fromarray((acc / 5).astype(np.uint8))
    zw, zh = int(W * zoom), int(H * zoom)
    frame = frame.resize((zw, zh), Image.BILINEAR)
    if abs(rot) > .03:
        frame = frame.rotate(rot, Image.BILINEAR)
    ox = max(0, min(zw - W, (zw - W) // 2 + int(shx)))
    oy = max(0, min(zh - H, (zh - H) // 2 + int(shy)))
    frame = frame.crop((ox, oy, ox + W, oy + H))

    # ---- post
    arr = np.asarray(frame).astype(np.float32)
    arr = chroma(arr, aberr)
    arr = bloom(arr, .55, 160)
    arr = halation(arr, th2 if (th2 and mixn > .5) else th, .30)
    arr = grade(arr, th, 1.0, th2, mixn if th2 else 0.0)
    arr = vignette(arr)
    if flash > .004:
        arr += np.array([255, 246, 228], np.float32) * flash
    jx = int((hsh(tq * 1.1) - .5) * 4); jy = int((hsh(tq * 2.3 + 4) - .5) * 4)
    arr = np.roll(np.roll(arr, jx, 1), jy, 0)
    arr += np.repeat(np.repeat(GRAIN, 2, 0), 2, 1)[:H, :W] * 4.2
    return np.clip(arr, 0, 255).astype(np.uint8)


# ═══════════════════════════════════════════════ drivers
def shard(a, b, path):
    """Render frames [a,b) straight into an mp4 segment. render() is pure, so
    shards are bit-identical to a single-process run."""
    import imageio_ffmpeg, time
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    p = subprocess.Popen([ff, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'faster',
                          '-crf', '16', '-pix_fmt', 'yuv420p', '-g', '30', path],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    for i in range(a, b):
        p.stdin.write(render(i).tobytes())
        k = i - a + 1
        if k % 25 == 0 or k == b - a:
            el = time.time() - t0
            print(f'[{a}:{b}] {k}/{b - a}  {el:.0f}s  eta {el / k * (b - a - k):.0f}s', flush=True)
    p.stdin.close(); p.wait()
    print(f'[{a}:{b}] SHARD DONE -> {path}', flush=True)


def main():
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs('/home/user/build', exist_ok=True)
    p = subprocess.Popen([ff, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'faster',
                          '-crf', '18', '-pix_fmt', 'yuv420p', OUT],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(NF):
        p.stdin.write(render(i).tobytes())
        if i % 60 == 0:
            print(f'frame {i}/{NF}', flush=True)
    p.stdin.close(); p.wait(); print('done')


if __name__ == '__main__':
    if len(sys.argv) == 4:
        shard(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
    else:
        main()
