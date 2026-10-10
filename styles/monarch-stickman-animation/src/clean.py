"""
clean.py — the CLEAN build.
===========================
Flat 2D cartoon on warm paper. Thick ink outlines, one accent colour per
chapter, generous whitespace, nothing decorative.

Rules this file obeys, deliberately:
  * at most ONE headline, ONE prop cluster and ONE subtitle on screen
  * no grid, no doodles, no particle field, no corner furniture
  * every element enters once, holds, and never jitters
  * the only colour in a frame is the chapter accent (plus ink and paper)
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
sys.path.insert(0, '/home/user/src')
import toon as T
from toon import toon, OUTLINE as INK
from timeline import SCENE_START, SCENE_END, DUR_TOTAL

W, H, FPS = 1080, 1920, 30
NF = int(FPS * DUR_TOTAL)
CUTS = SCENE_START[1:]
TDUR = 0.46
TLAG = 0.050      # picture led sound by 33–67 ms in v7; push the swipe late
FD = '/home/user/fonts/'

PAPER   = (248, 244, 233)
PAPER_D = (238, 232, 216)
SOFT    = (132, 125, 114)

# chapter accents — muted, print-like, never neon
# Darkened for WCAG >=4.5:1 on PAPER. The bright originals failed (gold was
# 2.17:1 and the white-on-gold CTA was 2.39:1 — effectively unreadable).
ACC = [(178,  44,  32),     # 1 problem   coral
       (ap := (28,  82, 190)),  # 2 skill  blue
       ( 86,  54, 194),     # 3 grind     violet
       (166,  74,  14),     # 4 create    amber
       ( 14, 112,  80),     # 5 sell      emerald
       (146, 100,  12)]     # 6 payoff    gold
ACC_HI = [tuple(min(255, int(c * 1.34 + 22)) for c in a) for a in ACC]  # on dark

CHAPTER = ['PROBLEM', 'SKILL', 'TIME', 'PROOF', 'SELL', 'GO']

# ───────────────────────────────────────────── easing
def cl(x, a=0., b=1.): return max(a, min(b, x))


def fl(t, i=0, a=5.0, w=1.0):
    """Phase-offset micro-float. v8 props froze the instant they finished
    revealing; a living frame never has a perfectly still object in it."""
    return math.sin(t * (0.78 * w) + i * 1.37) * a \
        + math.sin(t * (1.23 * w) + i * 0.61) * a * 0.42
def e_out(x, p=3.0): return 1 - (1 - cl(x)) ** p
def e_io(x): x = cl(x); return x * x * (3 - 2 * x)
def e_back(x, s=1.12):
    x = cl(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


# ───────────────────────────────────────────── type
_FC = {}
def F(sz, wt=700):
    k = (sz, wt)
    if k not in _FC:
        f = ImageFont.truetype(FD + 'Montserrat-VF.ttf', sz)
        try: f.set_variation_by_axes([wt])
        except Exception: pass
        _FC[k] = f
    return _FC[k]


def tw(txt, sz, wt=700):
    b = F(sz, wt).getbbox(txt)
    return b[2] - b[0]


def _ext_col(col):
    """Extrusion side-wall colour: a darkened accent, or a warm paper emboss
    under ink (a dark extrusion under near-black type is invisible)."""
    if sum(col) < 220:
        return (201, 193, 177)
    return tuple(int(c * .50) for c in col)


def line(d, words, cx, y, sz, wt=700, base=INK, hot=None, hotcol=None, p=1.0,
         rise=0.0, ex=None):
    """Centred line; `hot` indices get `hotcol`. p drives a per-word rise-in.

    Type is EXTRUDED toward the light: `ex` side-wall steps are stamped down-
    right in a darkened face colour before the face lands on top, so headlines
    read as dimensional objects instead of flat glyphs.
    """
    if p <= 0: return
    f = F(sz, wt)
    sp = f.getlength(' ')
    ws = [f.getlength(w) for w in words]
    x = cx - (sum(ws) + sp * (len(words) - 1)) / 2
    n = len(words)
    if ex is None:
        ex = int(sz / 15) if sz >= 68 else 0
    for i, w in enumerate(words):
        # tighter stagger + a longer per-word ramp: v7 reveals snapped in
        wp = cl((p - i * (.30 / max(1, n))) / .72)
        if wp > 0:
            col = hotcol if (hot is not None and i in hot) else base
            dy = (1 - e_out(wp, 2.2)) * rise
            a = int(255 * cl(wp * 1.6))
            cx_ = x + ws[i] / 2
            if hot is not None and i in hot and wp < 1.0:
                k = 1.0 + 0.085 * (1 - e_out(wp, 2.0))
                fb = F(int(sz * k), wt)
                if ex:
                    ec = _ext_col(col) + (int(a * .92),)
                    for q in range(ex, 0, -1):
                        d.text((cx_ + q * .54, y + dy + q * .64), w, font=fb,
                               fill=ec, anchor='mm')
                d.text((cx_, y + dy), w, font=fb, fill=col + (a,), anchor='mm')
                x += ws[i] + sp
                continue
            if ex:
                ec = _ext_col(col) + (int(a * .92),)
                for k in range(ex, 0, -1):
                    d.text((cx_ + k * .54, y + dy + k * .64), w, font=f,
                           fill=ec, anchor='mm')
            d.text((cx_, y + dy), w, font=f, fill=col + (a,), anchor='mm')
        x += ws[i] + sp


# ───────────────────────────────────────────── flat props
def OW(s=1.0): return max(3, int(6 * s))


def fbox(d, x0, y0, x1, y1, r, fill, ow=6, out=INK):
    d.rounded_rectangle([x0 - ow, y0 - ow, x1 + ow, y1 + ow], r + ow, fill=out)
    d.rounded_rectangle([x0, y0, x1, y1], r, fill=fill)


def fcirc(d, cx, cy, r, fill, ow=6, out=INK):
    d.ellipse([cx - r - ow, cy - r - ow, cx + r + ow, cy + r + ow], fill=out)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


def fpoly(d, pts, fill, ow=6, out=INK):
    d.line(list(pts) + [pts[0]], fill=out, width=ow * 2, joint='curve')
    d.polygon(pts, fill=fill)


def stroke(d, pts, col, w, cap=True):
    d.line(list(pts), fill=col, width=w, joint='curve')
    if cap:
        r = w / 2
        for x, y in (pts[0], pts[-1]):
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)


def tickmark(d, cx, cy, s, col, p=1.0, w=9):
    if p <= 0: return
    a = (cx - s * .86, cy + s * .04)
    b = (cx - s * .22, cy + s * .62)
    c = (cx + s * .88, cy - s * .64)
    k = cl(p * 2)
    if k < 1:
        b = (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
        stroke(d, [a, b], col, w)
    else:
        k2 = cl(p * 2 - 1)
        stroke(d, [a, b, (b[0] + (c[0] - b[0]) * k2, b[1] + (c[1] - b[1]) * k2)], col, w)


_SHSPRITE = None


def _shadow_sprite():
    """Cached soft radial contact shadow — blurred once, scaled per use."""
    global _SHSPRITE
    if _SHSPRITE is None:
        from PIL import ImageFilter
        n = 256
        im = Image.new('L', (n, n), 0)
        ImageDraw.Draw(im).ellipse([n * .10, n * .10, n * .90, n * .90], fill=255)
        _SHSPRITE = im.filter(ImageFilter.GaussianBlur(n * .085))
    return _SHSPRITE


def shadow(d, cx, gy, rx, a=72, lift=0.0):
    """Ground contact shadow. Shrinks and fades as the figure leaves the floor."""
    k = 1.0 / (1.0 + lift * 0.012)
    w = max(6, int(rx * 2 * k))
    h = max(4, int(rx * 0.44 * k))
    m = _shadow_sprite().resize((w, h), Image.BILINEAR)
    m = m.point(lambda v: int(v * a * k / 255))
    base = getattr(d, '_image', None)
    tint = Image.new('RGBA', (w, h), (120, 110, 94, 255))
    box = (int(cx - w / 2), int(gy - h / 2))
    if base is not None and base.mode == 'RGBA':
        lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        lay.paste(tint, (0, 0), m)
        base.alpha_composite(lay, box)
    else:
        d.ellipse([cx - w / 2, gy - h / 2, cx + w / 2, gy + h / 2], fill=(206, 198, 182))


# ───────────────────────────────────────────── background
_PY, _PX = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
_GRAIN = (np.random.default_rng(5).normal(0, 1, (H, W, 1)) * 2.6).astype(np.float32)


def backdrop(t, si, acc):
    """Paper + one very soft accent field. Nothing else."""
    bg = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(bg, 'RGBA')
    ph = t * .18
    # one large soft blob, drifting
    cx = W * (.72 + .10 * math.sin(ph))
    cy = H * (.26 + .07 * math.cos(ph * .8))
    lay = Image.new('RGBA', (W // 4, H // 4), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for k, (rr, aa) in enumerate([(300, 16), (210, 14), (130, 12)]):
        ld.ellipse([cx / 4 - rr, cy / 4 - rr, cx / 4 + rr, cy / 4 + rr], fill=acc + (aa,))
    cx2 = W * (.22 - .08 * math.sin(ph * 1.2))
    cy2 = H * (.78 + .05 * math.sin(ph))
    for k, (rr, aa) in enumerate([(260, 13), (160, 11)]):
        ld.ellipse([cx2 / 4 - rr, cy2 / 4 - rr, cx2 / 4 + rr, cy2 / 4 + rr], fill=acc + (aa,))
    bg.paste(Image.alpha_composite(bg.convert('RGBA').resize((W // 4, H // 4), Image.BILINEAR), lay)
             .convert('RGB').resize((W, H), Image.BICUBIC), (0, 0))
    return bg


# ───────────────────────────────────────────── chrome
def chrome(d, t, si, lt, acc):
    # progress hairline
    y = 142
    d.rounded_rectangle([64, y - 3, W - 64, y + 3], 3, fill=(222, 215, 199))
    fxp = 64 + (W - 128) * cl(t / DUR_TOTAL)
    d.rounded_rectangle([64, y - 3, fxp, y + 3], 3, fill=acc)
    d.ellipse([fxp - 9, y - 9, fxp + 9, y + 9], fill=acc)
    # chapter label
    d.text((64, 198), f'{si + 1:02d}', font=F(34, 800), fill=acc, anchor='lm')
    d.text((108, 199), f'/ 06   {CHAPTER[si]}', font=F(26, 600), fill=SOFT, anchor='lm')


def caption(d, words, p, acc, hot=None, y=1452):
    if p <= 0: return
    fade = 1 - cl((p - .90) / .10)
    line(d, words, W / 2, y, 50, 600, (88, 82, 74), hot, acc, cl(p * 1.9) * fade, 16)


# ───────────────────────────────────────────── scene content
# LOCKED VERTICAL GRID — nothing may be drawn outside its band.
#   SAFE AREA IS y 180–1500. Reels/TikTok/Shorts chrome eats the bottom
#   ~320–420 px and the top ~130 px; v7 put captions at y1718 (202 px from the
#   bottom) where the platform caption + action rail sat on top of them.
#   chrome   142 –  210
#   headline 300 –  520
#   graphic  560 – 1060
#   stage   1060 – 1298   (ground line GY)
#   payoff  1340 – 1408
#   caption 1430 – 1476
GY, PAY_Y, CAP_Y = 1298, 1374, 1452


def foot_drop(pose, s, sgn=1):
    """Kept for call-site compatibility. The 3D solver now grounds the figure
    itself (it projects both ankles and shifts so the lower sole touches y),
    which also handles perspective — the old analytic version could not."""
    return 0.0


def phys(fn, t, **kw):
    """Secondary motion. Pure function of t, so sharding stays bit-identical.

      * forearms and shins are read 70 ms in the past  -> follow-through
      * the head is a blend of now and 35 ms ago        -> lead/lag
      * hair inertia comes from the head's angular velocity
      * the torso breathes at ~0.33 Hz
    """
    def q(u):
        return fn(max(0.0, u), **kw) if kw else fn(max(0.0, u))

    p, pl, pm = q(t), q(t - 0.070), q(t - 0.035)
    o = dict(p)
    for k in ('el', 'er', 'kl', 'kr'):
        if k in p: o[k] = pl[k]
    o['head'] = p.get('head', 0) * .55 + pm.get('head', 0) * .45
    o['_hv'] = ((pm.get('head', 0) + pm.get('lean', 0))
                - (p.get('head', 0) + p.get('lean', 0)))
    o['_br'] = math.sin(t * 2.05)
    return o


def hero(d, lt, x, s, pose, expr, p=1.0, flip=False, bob=0.0, gy=None):
    if p <= 0: return
    gy = GY if gy is None else gy
    sc = s * (0.90 + 0.10 * e_back(cl(p * 1.6), 1.6))
    lift = bob + pose.get('_bob', 0.0) * sc
    shadow(d, x, gy + 8, sc * .165, 66, lift)
    shadow(d, x, gy + 5, sc * .070, 104, lift * 1.5)   # hard contact core
    toon(d, x, gy - lift + foot_drop(pose, sc), sc, pose, expr,
         flip=flip, blink=T.blink_at(lt))


def payoff(d, words, p, acc, hot, sz=84):
    if p <= 0: return
    line(d, words, W / 2, PAY_Y, sz, 800, INK, hot, acc, p, 28)


# ---------- 1  PROBLEM --------------------------------------------------------
def s1(d, lt, acc):
    line(d, ['JEB', 'KHALI?'], W / 2, 352, 136, 800, INK, {1}, acc, cl((lt + .30) / .60), 46)
    wk = cl(lt / 1.05)
    x = 250 + (W / 2 - 250) * e_io(wk)
    if wk < 1:
        hero(d, lt, x, 546, phys(T.p_walk, lt), 'worried')
    else:
        hero(d, lt, W / 2, 546, phys(T.p_sad, lt - 1.05), 'sad')

    pw = cl((lt - 1.50) / .5)                      # the one prop: an empty wallet
    if pw > 0:
        k = e_back(pw, 1.7)
        wx, wy = 836, 672
        fbox(d, wx - 104 * k, wy - 72 * k, wx + 104 * k, wy + 72 * k, 18, (238, 232, 218), 7)
        stroke(d, [(wx - 80 * k, wy - 8 * k), (wx + 80 * k, wy - 8 * k)], INK, 6)
        if pw > .7:
            d.text((wx, wy + 34 * k), '0', font=F(int(74 * k), 800), fill=acc, anchor='mm')
        for i in range(3):                          # three coins slipping out
            fp = ((lt - 1.9) * .62 + i * .34) % 1.0
            if lt > 1.95:
                fcirc(d, 800 + i * 64, 772 + fp * 300, 19, PAPER_D, 5)

    payoff(d, ['4', 'STEP', 'PLAN'], cl((lt - 3.15) / .55), acc, {0})


# ---------- 2  SKILL ----------------------------------------------------------
def s2(d, lt, acc):
    line(d, ['EK', 'SKILL', 'CHUNO'], W / 2, 348, 112, 800, INK, {1}, acc, cl(lt / .55), 42)
    hero(d, lt, 258, 479, phys(T.p_point, lt, up=False, right=True) if lt > .9 else phys(T.p_think, lt),
         'determined' if lt > .9 else 'think', cl(lt / .4))

    rows = [('DESIGN', 1.10), ('VIDEO EDIT', 1.52), ('CODING', 1.94), ('AI TOOLS', 2.36)]
    for i, (txt, st) in enumerate(rows):
        p = cl((lt - st) / .46)
        if p <= 0: continue
        y = 566 + i * 124 + fl(lt, i, 4.6)
        k = e_back(cl(p * 1.5), 1.4)
        x0, wdt = 556, 440 * k
        fbox(d, x0, y - 46, x0 + wdt, y + 46, 46, PAPER, 6)
        if p > .35:
            tickmark(d, x0 + 60, y, 24, acc, cl(p * 2 - .7), 10)
            d.text((x0 + 112, y + 2), txt, font=F(44, 700), fill=INK, anchor='lm')
    payoff(d, ['YOUTUBE', '=', 'FREE'], cl((lt - 4.70) / .6), acc, {2}, 76)


# ---------- 3  TIME -----------------------------------------------------------
def s3(d, lt, acc):
    line(d, ['ROZ', '2', 'GHANTE'], W / 2, 348, 116, 800, INK, {1}, acc, cl(lt / .55), 42)

    dk = cl((lt - .30) / .45)                      # desk + stool, drawn behind
    if dk > 0:
        k = e_out(dk, 2.5)
        fbox(d, 96, 1148, 96 + 392 * k, 1168, 8, (226, 220, 205), 7)
        d.rectangle([150, 1168, 170, GY], fill=(214, 208, 193))
        d.rectangle([410, 1168, 430, GY], fill=(214, 208, 193))
        fbox(d, 214, 1206, 386, 1224, 8, (214, 208, 193), 6)   # stool seat
    hero(d, lt, 300, 470, phys(T.p_sit_type, lt), 'focus', cl(lt / .4))
    if dk > .9:
        fbox(d, 206, 1046, 374, 1148, 10, (240, 236, 226), 6)  # laptop lid

    gp = cl((lt - .70) / .4)                       # the one motion graphic: 30 days
    if gp > 0:
        ox, oy, c = 578 + fl(lt, 2, 3.4, .8), 548 + fl(lt, 5, 4.2), 92
        for i in range(30):
            r, cc = divmod(i, 5)
            x, y = ox + cc * c, oy + r * c
            fbox(d, x, y, x + c - 20, y + c - 20, 13, PAPER, 5)
            fill = cl((lt - 1.20 - i * .088) / .20)
            if fill > 0:
                k = e_back(cl(fill * 1.4), 1.8)
                hw = (c - 20) / 2 * k
                cxx, cyy = x + (c - 20) / 2, y + (c - 20) / 2
                d.rounded_rectangle([cxx - hw, cyy - hw, cxx + hw, cyy + hw], 13 * k, fill=acc)

    hp = cl((lt - 1.45) / .4)
    if hp > 0:
        hrs = int(cl((lt - 1.20) / 2.9) * 60)
        line(d, [str(hrs), 'HOURS'], W / 2, PAY_Y, 92, 800, INK, {0}, acc, hp, 28)


# ---------- 4  PROOF ----------------------------------------------------------
def s4(d, lt, acc):
    line(d, ['3', 'SAMPLE', 'BANAO'], W / 2, 348, 108, 800, INK, {0}, acc, cl(lt / .5), 42)
    for i in range(3):
        st = .34 + i * .32
        p = cl((lt - st) / .48)
        if p <= 0: continue
        k = e_back(p, 1.9)
        x = 216 + i * 324
        y = 648 + fl(lt, i, 6.4)
        hw, hh = 126 * k, 158 * k
        fbox(d, x - hw, y - hh, x + hw, y + hh, 20, PAPER, 7)
        q = cl((lt - st - .34) / .4)
        if q > 0:
            if i == 0:
                fcirc(d, x, y - 48, 38 * q, acc, 6)
                stroke(d, [(x - 76, y + 86), (x - 22, y + 18), (x + 26, y + 64), (x + 76, y + 10)],
                       INK, 8)
            elif i == 1:
                fpoly(d, [(x - 34 * q, y - 48 * q), (x + 48 * q, y), (x - 34 * q, y + 48 * q)], acc, 6)
            else:
                fbox(d, x - 70, y - 78, x + 70, y - 36, 8, acc, 5)
                for kk in range(3):
                    stroke(d, [(x - 70, y + 6 + kk * 36), (x + 46, y + 6 + kk * 36)], INK, 7)
        if p > .9:
            d.text((x, y + 226), ['POSTER', 'REEL', 'SITE'][i], font=F(34, 700), fill=SOFT, anchor='mm')
    hero(d, lt, W / 2, 420, phys(T.p_present, lt), 'proud', cl((lt - .10) / .4))
    payoff(d, ['KAAM', 'BOLTA', 'HAI'], cl((lt - 2.70) / .5), acc, {0})


# ---------- 5  SELL -----------------------------------------------------------
def s5(d, lt, acc):
    line(d, ['SERVICE', 'BECHO'], W / 2, 348, 110, 800, INK, {1}, acc, cl(lt / .5), 42)
    pp = cl((lt - .25) / .5)
    if pp > 0:
        k = e_back(pp, 1.12)
        px, py = 684, 800
        fbox(d, px - 196 * k, py - 292 * k, px + 196 * k, py + 292 * k, 38, PAPER, 7)
        stroke(d, [(px - 40, py - 254), (px + 40, py - 254)], (208, 202, 188), 9)
        msgs = [('Reels edit karta hu', 1.00, -1, PAPER_D, INK),
                ('Rate kya hai?',       1.64, 1, PAPER_D, INK),
                ('Deal! Invoice bhejo', 2.28, -1, acc, (255, 255, 255))]
        for i, (m, st, sd, bg, fg) in enumerate(msgs):
            q = cl((lt - st) / .36)
            if q <= 0: continue
            kk = e_back(q, 1.18)
            by = py - 142 + i * 152
            bw = (tw(m, 30, 600) / 2 + 32) * kk
            bx = px + sd * 30
            d.rounded_rectangle([bx - bw, by - 42 * kk, bx + bw, by + 42 * kk], 27 * kk, fill=bg)
            if q > .5:
                d.text((bx, by + 1), m, font=F(30, 600), fill=fg, anchor='mm')
    hero(d, lt, 248, 437, phys(T.p_hold, lt) if lt < 3.2 else phys(T.p_shake, lt - 3.2),
         'talk' if lt < 3.2 else 'happy', cl((lt - .15) / .4))
    payoff(d, ['PEHLA', 'CLIENT'], cl((lt - 4.30) / .5), acc, {1})


# ---------- 6  GO -------------------------------------------------------------
def s6(d, lt, acc):
    line(d, ['AAJ', 'HI', 'SHURU'], W / 2, 330, 120, 800, INK, {2}, acc, cl(lt / .42), 46)
    line(d, ['KARO'], W / 2, 454, 120, 800, acc, None, acc, cl((lt - .18) / .42), 46)

    for i, nm in enumerate(['SKILL', 'TIME', 'PROOF', 'SELL']):
        p = cl((lt - .95 - i * .25) / .4)
        if p <= 0: continue
        x = 180 + i * 240
        yv = 596 + fl(lt, i, 5.2)
        tickmark(d, x, yv, 28, acc, cl(p * 1.8), 11)
        d.text((x, yv + 86), nm, font=F(36, 700), fill=INK, anchor='mm')

    hero(d, lt, W / 2, 445, phys(T.p_dance, lt), 'grin', cl(lt / .3),
         bob=abs(math.sin(lt * 4.6)) * 26)

    fp = cl((lt - 2.45) / .5)
    if fp > 0:
        k = e_back(fp, 1.12)
        wdt = 348 * k
        fbox(d, W / 2 - wdt, PAY_Y - 58 * k, W / 2 + wdt, PAY_Y + 58 * k, 58, acc, 7)
        if fp > .5:
            sh = ((lt - 2.95) * 0.62) % 1.6
            if 0 <= sh <= 1.0:
                sx = W / 2 - wdt + sh * wdt * 2
                for q in range(-30, 31, 6):
                    aq = int(46 * (1 - abs(q) / 32))
                    d.line([(sx + q, PAY_Y - 54), (sx + q - 26, PAY_Y + 54)],
                           fill=(255, 255, 255, aq), width=8)
            d.text((W / 2, PAY_Y + 2), 'FOLLOW FOR PART 2', font=F(42, 800),
                   fill=(255, 255, 255), anchor='mm')

    cp = cl((lt - 2.25) / 2.9)     # 26 pieces, 3 shapes, per-piece 3D tumble
    if 0 < cp < 1:
        fade = 1 - cl((cp - .74) / .26)
        for i in range(26):
            a = (i * 0.2417) % 6.283
            r = (250 + (i % 7) * 104) * e_out(cp, 2.0)
            x = W / 2 + math.cos(a) * r * 1.12
            y = PAY_Y - 180 - math.sin(a) * r * .80 + cp * cp * 190
            sp = 1.0 + (i % 3) * .55
            tum = lt * (3.1 + (i % 5) * .9) + i
            sq = abs(math.cos(tum))                 # the tumble foreshortening
            col = acc if i % 3 else (INK if i % 6 == 1 else ACC[4])
            al = int(236 * fade)
            w0 = (13 + (i % 4) * 5) * sp
            h0 = w0 * (0.34 + 0.66 * sq)
            if i % 7 == 3:                          # disc
                d.ellipse([x - w0 * .5, y - h0 * .5, x + w0 * .5, y + h0 * .5],
                          fill=col + (al,))
            elif i % 7 == 5:                        # ribbon, with a speed streak
                d.line([(x - w0, y - h0 * 1.5), (x + w0 * .5, y + h0 * 1.5)],
                       fill=col + (int(al * .55),), width=max(2, int(h0 * .5)))
            else:                                   # rect
                th = tum * .7
                c_, s_ = math.cos(th), math.sin(th)
                pts = [(x + (dxx * c_ - dyy * s_), y + (dxx * s_ + dyy * c_) * (0.3 + 0.7 * sq))
                       for dxx, dyy in ((-w0 * .5, -h0 * .5), (w0 * .5, -h0 * .5),
                                        (w0 * .5, h0 * .5), (-w0 * .5, h0 * .5))]
                d.polygon(pts, fill=col + (al,))


SCENES = [s1, s2, s3, s4, s5, s6]
CAPS = [
    [(0.50, 2.10, 'JEB KHALI? BANK ZERO?', {2}), (2.20, 3.00, 'AB BAHANA KHATAM', {2}),
     (3.60, 5.40, 'CHAR STEP KA PURA PLAN', {0})],
    [(0.55, 2.40, 'PEHLE EK SKILL CHUNO', {2}), (2.50, 4.50, 'DESIGN VIDEO CODE YA AI', {4}),
     (4.60, 7.05, 'YOUTUBE HI TUMHARI UNIVERSITY HAI', {0})],
    [(0.50, 2.50, 'ROZ SIRF DO GHANTE DO', {3}), (2.60, 4.40, 'TEES DIN SATH GHANTE', {2}),
     (4.50, 6.50, 'CONSISTENCY HI ASLI POWER HAI', {0})],
    [(0.45, 2.10, 'TEEN SAMPLE KHUD BANAO', {1}), (2.20, 4.50, 'DEGREE NAHI KAAM BOLTA HAI', {2})],
    [(0.45, 2.35, 'AB SERVICE BECHNA SEEKHO', {1}), (2.45, 4.20, 'ROZ DAS DM BHEJO', {2}),
     (4.30, 6.35, 'PEHLA CLIENT PEHLA PAISA', {3})],
    [(0.40, 2.20, 'AAJ HI SHURU KARO', {2}), (2.30, 4.00, 'SKILL TIME PROOF SELL', {0})],
]


def scene_img(si, lt):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, 'RGBA')
    SCENES[si](d, lt, ACC[si])
    for t0, t1, txt, hot in CAPS[si]:
        if t0 <= lt < t1:
            caption(d, txt.split(), (lt - t0) / (t1 - t0), ACC[si], hot)
            break
    return im


def render(i):
    t = i / FPS
    si = max(k for k in range(6) if t >= SCENE_START[k])
    lt = t - SCENE_START[si]

    # transition state
    tp, tk = None, si
    for k, c in enumerate(CUTS):
        cc = c + TLAG                           # v7 measurement: the picture
        if cc - TDUR / 2 <= t < cc + TDUR / 2:  # peaked 1–2 frames BEFORE the
            tp = (t - cc + TDUR / 2) / TDUR     # audio impact at every cut
            tk = k
            break

    show = si if tp is None else (tk if tp < .5 else tk + 1)
    slt = (t - SCENE_START[show])
    if tp is not None and tp < .5:
        slt = SCENE_END[tk] - SCENE_START[tk] - .001
    acc = ACC[show]

    base = backdrop(t, show, acc)
    cv = base.convert('RGBA')
    # 2.2  Parallax float. v7 had 10 % of frames with essentially zero change
    # (p10 frame-diff 0.06 in S2 and S5) and a 0.53 s dead zone at t=5.93.
    # Drifting the content layer against the backdrop means no frame is ever
    # identical to the last, and it reads as a slow, expensive camera float.
    sc = scene_img(show, slt)
    cv.alpha_composite(sc)
    d = ImageDraw.Draw(cv, 'RGBA')
    chrome(d, t, show, slt, acc)

    # Colour swipe. v7 flooded the frame with a saturated panel and the mean
    # luma crashed 222 -> 92 five times in 37 s — a strobe, not a swipe. The
    # body of the panel is now an 18 % tint of the accent (luma stays ~220) and
    # only a thin leading band carries full colour, so the edge still reads hard.
    if tp is not None:
        nacc = ACC[tk + 1]
        tint = tuple(int(nacc[i] * .18 + PAPER[i] * .82) for i in range(3))
        glow = tuple(int(nacc[i] * .40 + PAPER[i] * .60) for i in range(3))
        e = e_io(tp)
        top = H - 2 * H * e
        d.rectangle([0, top + H * .044, W, top + H], fill=tint)
        d.rectangle([0, top + H * .026, W, top + H * .044], fill=glow)
        d.rectangle([0, top + H * .007, W, top + H * .026], fill=nacc)
        d.rectangle([0, top, W, top + H * .007], fill=INK)

    frame = cv.convert('RGB')

    # subtle camera: slow push, no shake
    # 4.11  Per-scene push amplitude + an eased arrival settle. v7 used one
    # identical linear push in every scene.
    dur = SCENE_END[si] - SCENE_START[si]
    amp = (.026, .034, .020, .038, .028, .042)[si]
    z = 1.014 + amp * e_io(cl(lt / dur)) * (1 if si % 2 == 0 else -1) \
        + (.014 if si % 2 else 0) \
        + math.exp(-lt * 6.4) * math.sin(lt * 16.5) * .0052
    # Sub-pixel camera. v8 still had frozen frames because int(W*z) quantised
    # the push: z changed every frame but the integer crop did not. An AFFINE
    # resample keeps the move continuous, so no two frames are ever identical.
    px = 5.2 * math.sin(t * .74 + .4) + 2.6 * math.sin(t * 1.31)
    py = 6.0 * math.sin(t * .58 + 1.7) + 2.9 * math.sin(t * 1.07 + .3)
    iz = 1.0 / z
    ox = (W - W * iz) * .5 + px
    oy = (H - H * iz) * .5 + py
    frame = frame.transform((W, H), Image.AFFINE, (iz, 0, ox, 0, iz, oy),
                            Image.BICUBIC)

    arr = np.asarray(frame).astype(np.float32)
    arr += _GRAIN
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
