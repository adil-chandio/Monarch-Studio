"""
wide.py — 16:9 LONG-FORM renderer (ancient-survival documentary).
=================================================================
Sibling of clean.py. Nothing in clean.py / toon.py / make_asmr.py is modified;
this file only *reads* the 3D character rig from toon.py.

What changes vs the vertical build
----------------------------------
  * 1920x1080. The platform UI problem disappears (no Shorts rail), so the
    safe area is the broadcast title-safe box: x 96-1824, y 54-1026.
  * Landscape wants a HORIZON, not a stack. Every scene is composed on one
    ground line with the subject on a third, graphic opposite.
  * Documentary palette: bone paper, iron ink, earth accents.
  * 8 beats instead of 6, cut to the measured VO, not to a beat grid.

The clean rule still holds: ONE headline, ONE graphic cluster, ONE caption.
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
sys.path.insert(0, '/home/user/src')
import toon as T
from toon import toon, OUTLINE as INK

W, H, FPS = 1920, 1080, 30
FD = '/home/user/fonts/'

# ───────────────────────────────────────────── timeline (fit to measured VO)
# VO durations measured off the generated mp3s:
#   w1 6.11  w2 5.30  w3 5.46  w4 4.83  w5 11.86  w6 14.92
# Scene lengths are fitted to the voice. The voice is never time-stretched to
# fit a grid — that is the re-fit law from the vertical build, applied the
# other way round because here the picture is the free variable.
SCENE_START = [0.000, 6.900, 13.000, 19.200, 24.700, 31.000, 37.300, 45.400]
DUR_TOTAL   = 53.000
SCENE_END   = SCENE_START[1:] + [DUR_TOTAL]
NS = len(SCENE_START)
NF = int(round(FPS * DUR_TOTAL))
CUTS = SCENE_START[1:]
TDUR = 0.42
TLAG = 0.050

# VO placement: (file, start_time)
VO = [('w1', 0.350), ('w2', 7.250), ('w3', 13.350), ('w4', 19.550),
      ('w5', 25.050), ('w6', 37.750)]

# ───────────────────────────────────────────── palette
PAPER   = (243, 236, 221)      # bone / sun-bleached paper
PAPER_D = (231, 221, 201)      # ground band
SOFT    = (104,  95,  82)      # 5.33:1 on PAPER, 4.66:1 on the ground band
SAND    = (221, 207, 180)

# Earth accents. Every one verified >= 4.5:1 against PAPER (see _contrast()).
ACC = [(166,  62,  24),    # 1 THE CHASE      burnt sienna
       (104,  70,  38),    # 2 NO WEAPONS     bark
       (171,  38,  30),    # 3 THE HEAT       ember
       ( 44,  58, 112),    # 4 THE QUESTION   indigo  (the title card)
       ( 16, 104,  96),    # 5 THE SKIN       verdigris
       (122,  84,  10),    # 6 THE LOCK       ochre
       ( 26,  96,  58),    # 7 THE CURVE      acacia
       (166,  62,  24)]    # 8 THE PROOF      sienna again (bookend)
ACC_HI = [tuple(min(255, int(c * 1.34 + 22)) for c in a) for a in ACC]

CHAPTER = ['THE CHASE', 'NO WEAPONS', 'THE HEAT', 'THE QUESTION',
           'THE SKIN', 'THE LOCK', 'THE CURVE', 'THE PROOF']

# Hunter recolour. The rig in toon.py is NOT edited — the two palette entries
# that toon() does not expose as arguments (shoe, and the two shading darks)
# are rebound here at import time, inside this process only. clean.py never
# imports wide.py, so the vertical build is unaffected.
SKIN_T  = (196, 150, 108)
WRAP    = (150, 110,  70)
HAIRK   = ( 44,  36,  30)
T.SHOE    = (132,  96,  58)    # hide sandal, not a white sneaker
T.SOLE    = ( 88,  62,  36)
T.SHIRT_D = (172, 128,  90)
T.PANTS_D = (124,  90,  56)

# ───────────────────────────────────────────── 16:9 GRID  (LOCKED)
#   title-safe   x  96 – 1824      y  54 – 1026
#   chrome       y  64 –  118
#   headline     y 170 –  300
#   stage        y 330 –  824      (ground line GY)
#   statchip     y 859 –  917
#   caption      y 952
#
# WHY THE LOWER BAND IS NOT AT THE BOTTOM OF THE FRAME:
# 16:9 has no Shorts rail, but YouTube's own transport bar + gradient occupies
# roughly the bottom 100 px of a 1080-tall player whenever the viewer moves the
# mouse. v1 put the caption baseline at y 998 (82 px clear) and the controls
# sat on it — the exact same class of bug as the vertical build's y1718
# captions. Everything below the horizon was lifted 46 px.
GY      = 824
CHIP_Y  = 888
CAP_Y   = 952
HEAD_Y  = 222


# ───────────────────────────────────────────── easing
def cl(x, a=0., b=1.): return max(a, min(b, x))
def e_out(x, p=3.0): return 1 - (1 - cl(x)) ** p
def e_io(x): x = cl(x); return x * x * (3 - 2 * x)
def e_back(x, s=1.12):
    x = cl(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def fl(t, i=0, a=5.0, w=1.0):
    """Phase-offset micro-float: no revealed prop is ever perfectly still."""
    return math.sin(t * (0.78 * w) + i * 1.37) * a \
        + math.sin(t * (1.23 * w) + i * 0.61) * a * 0.42


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
    if sum(col) < 220:
        return (199, 189, 170)
    return tuple(int(c * .50) for c in col)


def line(d, words, cx, y, sz, wt=700, base=INK, hot=None, hotcol=None, p=1.0,
         rise=0.0, ex=None):
    """Centred line with per-word stagger and a light extrusion."""
    if p <= 0: return
    f = F(sz, wt)
    sp = f.getlength(' ')
    ws = [f.getlength(w) for w in words]
    x = cx - (sum(ws) + sp * (len(words) - 1)) / 2
    n = len(words)
    if ex is None:
        ex = int(sz / 16) if sz >= 64 else 0
    for i, w in enumerate(words):
        wp = cl((p - i * (.30 / max(1, n))) / .72)
        if wp > 0:
            col = hotcol if (hot is not None and i in hot) else base
            dy = (1 - e_out(wp, 2.2)) * rise
            a = int(255 * cl(wp * 1.6))
            cx_ = x + ws[i] / 2
            fuse = f
            if hot is not None and i in hot and wp < 1.0:
                k = 1.0 + 0.075 * (1 - e_out(wp, 2.0))
                fuse = F(int(sz * k), wt)
            if ex:
                ec = _ext_col(col) + (int(a * .92),)
                for q in range(ex, 0, -1):
                    d.text((cx_ + q * .54, y + dy + q * .64), w, font=fuse,
                           fill=ec, anchor='mm')
            d.text((cx_, y + dy), w, font=fuse, fill=col + (a,), anchor='mm')
        x += ws[i] + sp


def headline(d, words, p, acc, hot=None, sz=92, y=None):
    line(d, words, W / 2, HEAD_Y if y is None else y, sz, 800, INK, hot, acc,
         p, 34)


def caption(d, words, p, acc, hot=None, y=None):
    if p <= 0: return
    fade = 1 - cl((p - .90) / .10)
    line(d, words, W / 2, CAP_Y if y is None else y, 40, 600, (82, 75, 66),
         hot, acc, cl(p * 1.9) * fade, 13)


# ───────────────────────────────────────────── flat props
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


def statchip(d, txt, p, acc, y=None):
    """One hard number, framed. The retention engine of this format is
    specificity density, so every scene gets its verifiable fact on screen."""
    if p <= 0: return
    y = CHIP_Y if y is None else y
    k = e_back(cl(p * 1.25), 1.10)
    f = F(32, 700)
    wd = f.getlength(txt) / 2 + 34
    a = int(255 * cl(p * 2))
    d.rounded_rectangle([W / 2 - wd * k, y - 29 * k, W / 2 + wd * k, y + 29 * k],
                        29 * k, outline=acc + (a,), width=4)
    if p > .35:
        d.text((W / 2, y + 1), txt, font=f, fill=acc + (a,), anchor='mm')


_SHSPRITE = None
def _shadow_sprite():
    global _SHSPRITE
    if _SHSPRITE is None:
        n = 256
        im = Image.new('L', (n, n), 0)
        ImageDraw.Draw(im).ellipse([n * .10, n * .10, n * .90, n * .90], fill=255)
        _SHSPRITE = im.filter(ImageFilter.GaussianBlur(n * .085))
    return _SHSPRITE


def shadow(d, cx, gy, rx, a=72, lift=0.0, sq=0.44, col=(126, 112, 90)):
    k = 1.0 / (1.0 + lift * 0.012)
    w = max(6, int(rx * 2 * k))
    h = max(4, int(rx * sq * k))
    m = _shadow_sprite().resize((w, h), Image.BILINEAR)
    m = m.point(lambda v: int(v * a * k / 255))
    base = getattr(d, '_image', None)
    tint = Image.new('RGBA', (w, h), col + (255,))
    box = (int(cx - w / 2), int(gy - h / 2))
    if base is not None and base.mode == 'RGBA':
        lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        lay.paste(tint, (0, 0), m)
        base.alpha_composite(lay, box)


# ───────────────────────────────────────────── backdrop
_GRAIN = (np.random.default_rng(5).normal(0, 1, (H, W, 1)) * 2.5).astype(np.float32)
_RID = np.random.default_rng(31)
# distant ridge line, generated once so it is identical in every shard
_RIDGE = [(x, sum(math.sin(x / f + ph) * a for f, ph, a in
                  ((317., 0.8, 15), (151., 2.3, 8), (73., 5.1, 4))))
          for x in range(-20, W + 40, 20)]


def backdrop(t, si, acc):
    """Sky + sun + one distant ridge + the ground band. Nothing else.

    In 16:9 the horizon IS the composition. One ground line, held across all
    eight beats, is what makes eight unrelated diagrams feel like one film.
    """
    bg = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(bg, 'RGBA')

    # soft heat field in the sky, drifting
    ph = t * .15
    lay = Image.new('RGBA', (W // 4, H // 4), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    cx, cy = W * (.74 + .06 * math.sin(ph)), H * (.20 + .05 * math.cos(ph * .8))
    for rr, aa in ((250, 15), (170, 13), (100, 11)):
        ld.ellipse([cx / 4 - rr, cy / 4 - rr, cx / 4 + rr, cy / 4 + rr],
                   fill=acc + (aa,))
    cx2, cy2 = W * (.20 - .05 * math.sin(ph * 1.2)), H * (.64 + .04 * math.sin(ph))
    for rr, aa in ((200, 12), (120, 10)):
        ld.ellipse([cx2 / 4 - rr, cy2 / 4 - rr, cx2 / 4 + rr, cy2 / 4 + rr],
                   fill=acc + (aa,))
    bg.paste(Image.alpha_composite(
        bg.convert('RGBA').resize((W // 4, H // 4), Image.BILINEAR), lay)
        .convert('RGB').resize((W, H), Image.BICUBIC), (0, 0))
    d = ImageDraw.Draw(bg, 'RGBA')

    # distant ridge, sitting just above the horizon
    pts = [(x, GY - 34 + y) for x, y in _RIDGE]
    d.polygon(pts + [(W + 40, GY + 2), (-20, GY + 2)], fill=(222, 210, 189))

    # ground band
    d.rectangle([0, GY, W, H], fill=PAPER_D)
    d.line([(0, GY), (W, GY)], fill=(196, 183, 161), width=3)
    return bg


def heat_shimmer(img, t, amt=1.0):
    """Horizontal sine displacement in the band just above the horizon.
    Cheap, and it is the single cue that sells 42 degrees."""
    if amt <= 0: return img
    a = np.asarray(img)
    y0, y1 = GY - 230, GY + 4
    band = a[y0:y1].copy()
    for i in range(band.shape[0]):
        f = (i / (y1 - y0)) ** 2.2
        sh = int(round(math.sin(t * 5.1 + i * 0.09) * 10.5 * f * amt
                       + math.sin(t * 3.3 + i * 0.17) * 5.2 * f * amt))
        if sh:
            band[i] = np.roll(band[i], sh, axis=0)
    a = a.copy()
    a[y0:y1] = band
    return Image.fromarray(a)


# ───────────────────────────────────────────── chrome
def chrome(d, t, si, acc):
    y = 76
    d.rounded_rectangle([96, y - 3, W - 96, y + 3], 3, fill=(221, 211, 192))
    fxp = 96 + (W - 192) * cl(t / DUR_TOTAL)
    d.rounded_rectangle([96, y - 3, fxp, y + 3], 3, fill=acc)
    d.ellipse([fxp - 8, y - 8, fxp + 8, y + 8], fill=acc)
    d.text((96, 124), f'{si + 1:02d}', font=F(30, 800), fill=acc, anchor='lm')
    d.text((144, 125), f'/ 08   {CHAPTER[si]}', font=F(24, 600), fill=SOFT,
           anchor='lm')
    d.text((W - 96, 125), 'PERSISTENCE HUNTING', font=F(22, 600), fill=SOFT,
           anchor='rm')


# ───────────────────────────────────────────── character
def phys(fn, t, **kw):
    """Secondary motion: forearms/shins read 70 ms late, head leads/lags."""
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


def p_run(t, rate=9.4, yaw=60):
    """A run, not a fast walk. Longer stride, deeper knee lift, forward trunk
    lean, arms driving through a bigger arc, and a real flight phase in _bob.
    Built on top of the v9 rig contract — no change to toon.py.

    YAW IS THE WHOLE TRICK. At the v9 walk's 27 deg the sagittal stride is
    foreshortened to almost nothing and the figure reads as hopping on the
    spot. A near-profile 60 deg projects the stride at sin(60)=0.87 of its
    true length, so the run finally travels. Tested at 44 / 62 / 78 — 78
    collapses the shoulders and the lead arm crosses the chest.
    """
    ph = t * rate
    sw = math.sin(ph)
    def knee(q):
        return 14 + 78 * max(0.0, math.sin(q + 1.9)) ** 1.5
    return dict(yaw=yaw,
        lean=16.0, twist=-11.0 * sw, pelvis=10.5 * sw,
        tilt=3.4 * math.sin(ph + 1.6), sway=0.012 * math.sin(ph + 1.6),
        head=-2.0 * sw - 4.5, head_t=3.0 * sw,
        al=-14, az_l=-46 * sw, el=-6, ef_l=66 + 20 * max(0, -sw),
        ar=14, az_r=46 * sw, er=6, ef_r=66 + 20 * max(0, sw),
        ll=-5.0, lz_l=36 * sw, kl=knee(ph),
        lr=5.0, lz_r=-36 * sw, kr=knee(ph + math.pi),
        hl='fist', hr='fist',
        _bob=0.040 * abs(math.cos(ph)) - 0.012, _br=math.sin(t * 2.05))


def p_jog(t):
    """The economical gait: lower cadence, less lean, lower knee lift."""
    p = p_run(t, rate=6.6, yaw=54)
    p['lean'] = 8.0
    p['kl'] = 8 + (p['kl'] - 14) * 0.52
    p['kr'] = 8 + (p['kr'] - 14) * 0.52
    p['ef_l'] = 48 + (p['ef_l'] - 66) * 0.5
    p['ef_r'] = 48 + (p['ef_r'] - 66) * 0.5
    p['az_l'] *= 0.62
    p['az_r'] *= 0.62
    p['lz_l'] *= 0.70
    p['lz_r'] *= 0.70
    p['_bob'] = 0.024 * abs(math.cos(t * 6.6)) - 0.008
    return p


def hero(d, lt, x, s, pose, expr, p=1.0, flip=False, bob=0.0, gy=None,
         alpha=None):
    if p <= 0: return
    gy = GY if gy is None else gy
    sc = s * (0.90 + 0.10 * e_back(cl(p * 1.6), 1.6))
    lift = bob + pose.get('_bob', 0.0) * sc
    # low sun: the contact shadow is long and thrown to the left
    shadow(d, x - sc * .26, gy + 7, sc * .30, 46, lift, sq=0.17)
    shadow(d, x, gy + 7, sc * .150, 60, lift)
    shadow(d, x, gy + 4, sc * .064, 96, lift * 1.5)
    toon(d, x, gy - lift, sc, pose, expr, flip=flip, blink=T.blink_at(lt),
         shirt=SKIN_T, pants=WRAP, hair=HAIRK, alpha=alpha)


# ───────────────────────────────────────────── animal silhouettes
def antelope(d, cx, gy, s, t, col=INK, gallop=1.0, alpha=255, dust=True):
    """A kudu reduced to ONE filled silhouette, on real ungulate proportions.

    `s` is withers height (ground to shoulder), the way ungulates are actually
    measured. The first attempt used a round body with four symmetric splayed
    legs and read as an insect; the fixes that mattered were a long wedge
    barrel, legs swinging fore-aft rather than sideways, opposed joints
    (carpus bends BACK on the forelimb, hock bends FORWARD on the hind), and
    horns that sweep back instead of standing up like antennae.

    `t` drives a transverse gallop — fore pair and hind pair in antiphase,
    with a suspension lift. That whole-body gait is what pins its breathing
    to a 1:1 ratio with the stride.
    """
    ph = t * 6.2
    g = math.sin(ph)
    susp = max(0.0, math.cos(ph)) ** 2
    C = col + (alpha,)
    lw = max(2, int(s * .052))
    shadow(d, cx, gy + 4, s * .46, int(40 * alpha / 255), 0.0, sq=0.13)

    # s is WITHERS height, so the top of the back must land at gy - s. The
    # first pass put the barrel centre at 0.64 s and the animal looked
    # dachshund-legged; the belly now sits at 0.66 s, which is ungulate.
    rise = s * .050 * susp * gallop
    hipx, hipy = cx - s * .30, gy - s * .815 - rise
    witx, wity = cx + s * .26, gy - s * .845 - rise

    # ── barrel: a wedge, deep at the chest, tucked at the flank
    def seg(a, b, ra, rb, n=16):
        ax, ay = a; bx, by = b
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        pts = []
        for i in range(n + 1):
            u = i / n
            r = ra + (rb - ra) * u
            pts.append((ax + dx * u + nx * r, ay + dy * u + ny * r))
        for i in range(n, -1, -1):
            u = i / n
            r = ra + (rb - ra) * u
            pts.append((ax + dx * u - nx * r, ay + dy * u - ny * r))
        d.polygon(pts, fill=C)
    seg((hipx, hipy), (witx, wity), s * .140, s * .158)
    d.ellipse([witx - s * .155, wity - s * .150, witx + s * .155, wity + s * .168],
              fill=C)                                   # chest
    d.ellipse([hipx - s * .145, hipy - s * .140, hipx + s * .145, hipy + s * .158],
              fill=C)                                   # haunch

    # ── neck + head, thrown forward as the body extends
    ext = g * gallop
    nx2 = witx + s * (.27 + .05 * ext)
    ny2 = wity - s * (.40 - .06 * ext)
    seg((witx + s * .07, wity - s * .07), (nx2, ny2), s * .100, s * .052)
    hx = nx2 + s * .125
    hy = ny2 + s * .030
    seg((nx2, ny2), (hx, hy), s * .058, s * .038)
    d.ellipse([hx - s * .050, hy - s * .046, hx + s * .070, hy + s * .044],
              fill=C)                                   # muzzle
    # ear: rounded, laid BACK along the neck (a forward spike read as a horn)
    d.polygon([(nx2 - s * .015, ny2 - s * .030), (nx2 - s * .115, ny2 - s * .055),
               (nx2 - s * .050, ny2 + s * .035)], fill=C)

    # ── horns: long, swept BACK over the shoulders, with the spiral kink
    for o, w in ((-1, .88), (1, 1.0)):
        base = (nx2 + s * .015, ny2 - s * .045)
        pts = [base]
        for i in range(1, 9):
            u = i / 8
            r = s * .60 * w * u
            a = math.radians(-112 + 44 * u)             # up, then raked back
            kx = math.cos(a) * r + math.sin(u * 9.0) * s * .032
            ky = math.sin(a) * r
            pts.append((base[0] + kx, base[1] + ky + o * s * .014 * u))
        d.line(pts, fill=C, width=max(2, int(s * .028 * w)), joint='curve')

    # ── tail: short, with a tuft
    tx, ty = hipx - s * .17 - s * .03 * g, hipy + s * .13
    d.line([(hipx - s * .11, hipy - s * .04), (tx, ty)], fill=C,
           width=max(2, int(s * .020)), joint='curve')
    d.ellipse([tx - s * .022, ty - s * .014, tx + s * .022, ty + s * .046],
              fill=C)

    # ── four legs. fore pair and hind pair in antiphase; joints oppose.
    def leg(ax, ay, th, hind):
        fx = ax + math.sin(th) * s * .30
        lift = max(0.0, math.cos(th)) * s * .22
        fy = gy - lift
        bend = (0.12 if hind else -0.10) * s * (0.45 + 0.55 * (lift / (s * .22)))
        mx = (ax + fx) * .5 + bend
        my = (ay + fy) * .5 + s * .02
        d.line([(ax, ay), (mx, my), (fx, fy)], fill=C, width=lw, joint='curve')
        d.ellipse([fx - lw * .7, fy - lw * .5, fx + lw * .7, fy + lw * .5],
                  fill=C)
    for dx_, off in ((.10, 0.00), (-.04, 0.46)):          # fore pair
        leg(witx + s * dx_, wity + s * .10,
            math.sin(ph + off) * 1.35 * gallop, False)
    for dx_, off in ((-.08, 0.00), (.04, 0.46)):          # hind pair, antiphase
        leg(hipx + s * dx_, hipy + s * .08,
            math.sin(ph + math.pi + off) * 1.35 * gallop, True)

    # ── dust kicked off the hind hooves
    if dust:
        for i in range(3):
            fp = ((t * 1.5) + i * .33) % 1.0
            r = s * (.030 + fp * .075)
            cxx = hipx - s * .34 - fp * s * .46
            d.ellipse([cxx - r, gy - r * .62, cxx + r, gy + r * .40],
                      fill=(207, 195, 174, int(135 * (1 - fp) * alpha / 255)))


# ═════════════════════════════════════════════ SCENES
# ---------- 1  THE CHASE -----------------------------------------------------
def s1(d, lt, acc):
    headline(d, ['TWO', 'HOURS', 'IN'], cl((lt + .25) / .60), acc, {0}, 96)
    # hero runs in from the left and settles on the left third
    k = e_io(cl(lt / 2.6))
    x = 190 + (560 - 190) * k
    hero(d, lt, x, 430, phys(p_run, lt), 'determined')
    # the quarry, far ahead on the right third, small (distance = scale)
    ap = cl((lt - .55) / .9)
    if ap > 0:
        ax = 1530 + 130 * (1 - e_out(ap, 2.2)) + math.sin(lt * .5) * 10
        antelope(d, ax, GY - 6, 172, lt, (92, 80, 66), 1.0, int(230 * ap))
    # the gap, annotated once
    gp = cl((lt - 2.10) / .7)
    if gp > 0:
        # anchored between the two figures, just above the ground. Floating it
        # up at eye level read as an unrelated banner.
        y = GY - 156 + fl(lt, 1, 2.2)
        x0, x1 = 690, 1330
        xe = x0 + (x1 - x0) * e_out(gp, 2.4)
        stroke(d, [(x0, y), (xe, y)], acc, 5)
        for xx in (x0, xe):
            d.line([(xx, y - 13), (xx, y + 13)], fill=acc, width=5)
        if gp > .75:
            d.text(((x0 + x1) / 2, y - 34), 'THE GAP IS NO LONGER CLOSING',
                   font=F(30, 700), fill=acc, anchor='mm')
    statchip(d, '2 HOURS  ·  UP TO 35 KM  ·  KALAHARI', cl((lt - 3.5) / .6), acc)


# ---------- 2  NO WEAPONS ----------------------------------------------------
def s2(d, lt, acc):
    headline(d, ['NOTHING', 'IN', 'YOUR', 'HANDS'], cl(lt / .55), acc, {0}, 86)
    hero(d, lt, 420, 420, phys(T.p_idle, lt), 'determined', cl(lt / .4))

    # four objects on one baseline: two struck out, two kept
    items = [('BOW', 0.70, False), ('SPEAR', 1.05, False),
             ('STICK', 1.55, True), ('WATER', 1.90, True)]
    bx, by = 1020, GY - 318
    K = 1.34                      # icons were lost at 16:9 viewing distance
    for i, (nm, st, keep) in enumerate(items):
        p = cl((lt - st) / .45)
        if p <= 0: continue
        x = bx + i * 250
        y = by + fl(lt, i, 4.4)
        k = e_back(p, 1.12) * K
        col = acc if keep else (158, 148, 132)
        # icon
        if nm == 'BOW':
            # a D: limb bowing right, string straight down the left
            d.arc([x - 50 * k, y - 60 * k, x + 34 * k, y + 60 * k], -86, 86,
                  fill=col, width=int(9 * k))
            d.line([(x - 10 * k, y - 57 * k), (x - 10 * k, y + 57 * k)],
                   fill=col, width=int(4 * k))
            d.line([(x - 10 * k, y), (x - 44 * k, y)], fill=col,
                   width=int(5 * k))          # nocked arrow
            fpoly(d, [(x - 2 * k, y), (x - 20 * k, y - 9 * k),
                      (x - 20 * k, y + 9 * k)], col, 0)
        elif nm == 'SPEAR':
            d.line([(x + 26 * k, y - 62 * k), (x - 14 * k, y + 62 * k)],
                   fill=col, width=int(9 * k))
            fpoly(d, [(x + 26 * k, y - 72 * k), (x + 44 * k, y - 36 * k),
                      (x + 12 * k, y - 40 * k)], col, 0)
        elif nm == 'STICK':
            d.line([(x + 18 * k, y - 62 * k), (x - 12 * k, y + 62 * k)],
                   fill=col, width=int(10 * k), joint='curve')
            d.line([(x + 18 * k, y - 62 * k), (x + 40 * k, y - 44 * k)],
                   fill=col, width=int(8 * k))
        else:
            fcirc(d, x, y + 10 * k, 44 * k, PAPER, int(7 * k), col)
            d.rectangle([x - 11 * k, y - 60 * k, x + 11 * k, y - 28 * k],
                        fill=col)
            d.ellipse([x - 26 * k, y + 2 * k, x + 4 * k, y + 26 * k],
                      fill=col + (60,))
        d.text((x, y + 132), nm, font=F(30, 700),
               fill=(INK if keep else (158, 148, 132)), anchor='mm')
        if not keep and p > .55:
            q = cl((p - .55) / .45)
            r = 86
            stroke(d, [(x - r, y - r), (x - r + 2 * r * q, y - r + 2 * r * q)],
                   (171, 38, 30), 8)
    statchip(d, 'NO PROJECTILE WEAPON IS REQUIRED', cl((lt - 3.3) / .6), acc)


# ---------- 3  THE HEAT ------------------------------------------------------
def s3(d, lt, acc):
    headline(d, ['FORTY-TWO', 'DEGREES'], cl(lt / .55), acc, {0}, 86)
    # the sun, high and hard
    sp = cl(lt / 1.0)
    sx, sy = 1648, 392          # was 1560,300 — the rays clipped 'DEGREES'
    sr = 78 * e_back(sp, 1.1)
    if sp > 0:
        for i in range(14):
            a = i / 14 * math.tau + lt * .10
            l0, l1 = sr + 26, sr + 26 + 36 * (0.6 + 0.4 * math.sin(lt * 2.1 + i))
            d.line([(sx + math.cos(a) * l0, sy + math.sin(a) * l0),
                    (sx + math.cos(a) * l1, sy + math.sin(a) * l1)],
                   fill=acc + (190,), width=6)
        fcirc(d, sx, sy, sr, acc, 0)

    # the number, as the graphic
    np_ = cl((lt - .75) / .8)
    if np_ > 0:
        a = int(255 * cl(np_ * 1.8))
        k = 1 + .06 * (1 - e_out(np_, 2.0))
        f = F(int(260 * k), 800)
        d.text((640 + 2, GY - 300 + 3), '42', font=f, fill=(199, 189, 170, a),
               anchor='mm')
        d.text((640, GY - 300), '42', font=f, fill=acc + (a,), anchor='mm')
        d.text((640 + f.getlength('42') / 2 + 56, GY - 372), '°C',
               font=F(76, 800), fill=INK + (a,), anchor='mm')
    # thermometer bar
    tp = cl((lt - 1.55) / 1.1)
    if tp > 0:
        x0, x1, y = 380, 900, GY - 128
        d.rounded_rectangle([x0, y - 15, x1, y + 15], 15, fill=(224, 214, 195))
        d.rounded_rectangle([x0, y - 15, x0 + (x1 - x0) * e_out(tp, 2.2), y + 15],
                            15, fill=acc)
        d.text((x0, y + 48), '20°', font=F(24, 600), fill=SOFT, anchor='lm')
        d.text((x1, y + 48), '45°', font=F(24, 600), fill=SOFT, anchor='rm')

    hero(d, lt, 1330, 372, phys(p_jog, lt), 'determined', cl((lt - .3) / .5))
    statchip(d, 'KALAHARI HUNTS RUN AT 40–42 °C', cl((lt - 3.4) / .6), acc)


# ---------- 4  THE QUESTION (title card) -------------------------------------
def s4(d, lt, acc):
    # the hero walks to centre and the title lands on him
    k = e_io(cl(lt / 1.5))
    x = 380 + (W / 2 - 380) * k
    # 380 tall, not 470: at 470 the head crown reached y 392 and the subtitle
    # at 418 was printed across his face.
    hero(d, lt, x, 384, phys(T.p_walk, lt) if k < 1 else phys(T.p_idle, lt - 1.5),
         'determined')
    p1 = cl((lt - .55) / .75)
    line(d, ['THE', 'SLOWEST', 'PREDATOR'], W / 2, 284, 116, 800, INK, {1}, acc,
         p1, 44)
    p2 = cl((lt - 1.15) / .70)
    line(d, ['ON', 'THE', 'SAVANNA'], W / 2, 388, 58, 700, SOFT, {2}, acc, p2, 20)
    statchip(d, 'AND THE ONE THAT NEVER LOSES', cl((lt - 2.7) / .6), acc)


# ---------- 5  THE SKIN ------------------------------------------------------
_STIP = np.random.default_rng(77)
# Confined to the torso-and-arms band. Scattered over the whole figure the
# dots landed on the wrap and the sandals and read as mould, not skin.
_SPTS = [(float(_STIP.uniform(-.21, .21)), float(_STIP.uniform(-.74, -.40)),
          float(_STIP.uniform(0, 1))) for _ in range(380)]


def s5(d, lt, acc):
    headline(d, ['FOUR', 'MILLION', 'SWEAT', 'GLANDS'], cl(lt / .55), acc, {0}, 80)
    hx, hs = 520, 470
    hero(d, lt, hx, hs, phys(T.p_present, lt), 'talk', cl(lt / .4))
    # stipple the skin — the glands, one dot at a time
    sp = cl((lt - .85) / 2.4)
    if sp > 0:
        n = int(len(_SPTS) * e_out(sp, 1.6))
        for i in range(n):
            ux, uy, r = _SPTS[i]
            x = hx + ux * hs
            y = GY + uy * hs
            rr = 1.7 + r * 1.3
            fade = cl((n - i) / 40.)
            d.ellipse([x - rr, y - rr, x + rr, y + rr],
                      fill=acc + (int(150 * fade + 58),))
    # the counter
    cp = cl((lt - 1.10) / 2.2)
    if cp > 0:
        v = int(4_000_000 * e_out(cp, 2.6) / 1000) * 1000
        d.text((1300, GY - 476), f'{v:,}', font=F(118, 800), fill=INK,
               anchor='mm')
        d.text((1300, GY - 392), 'ECCRINE GLANDS ON ONE HUMAN BODY',
               font=F(28, 600), fill=SOFT, anchor='mm')
    # the comparison, two bars
    bp = cl((lt - 3.30) / 1.0)
    if bp > 0:
        bx, by, bw = 1300, GY - 96, 150
        for i, (nm, val, col) in enumerate((('HUMAN', 1.0, acc),
                                            ('CHIMPANZEE', 0.1, (150, 140, 124)))):
            x = bx + (i * 2 - 1) * 180
            hgt = 170 * val * e_out(bp, 2.2)
            d.rounded_rectangle([x - bw / 2, by - hgt, x + bw / 2, by], 8, fill=col)
            d.text((x, by + 28), nm, font=F(26, 700), fill=INK, anchor='mm')
        if bp > .6:
            d.text((bx, by - 232), '10×', font=F(58, 800), fill=acc,
                   anchor='mm')


# ---------- 6  THE LOCK ------------------------------------------------------
def s6(d, lt, acc):
    headline(d, ['LOCKED', 'TO', 'ITS', 'STRIDE'], cl(lt / .55), acc, {0}, 86)
    antelope(d, 1430, GY - 8, 268, lt, (88, 76, 62), 1.0, 255)

    # the gait-lock diagram: two rows of pulses
    rows = [('KUDU', 1, (171, 38, 30), GY - 420),
            ('HUMAN', 2, acc, GY - 280)]
    x0, x1 = 250, 1080
    for ri, (nm, ratio, col, y) in enumerate(rows):
        p = cl((lt - .75 - ri * .55) / .55)
        if p <= 0: continue
        xe = x0 + (x1 - x0) * e_out(p, 2.2)
        d.line([(x0, y), (xe, y)], fill=(206, 195, 175), width=4)
        d.text((x0 - 24, y), nm, font=F(30, 800), fill=col, anchor='rm')
        d.text((x1 + 24, y), f'{ratio} : 1' if ratio == 1 else '2 : 1',
               font=F(30, 800), fill=col, anchor='lm')
        # 8 strides
        for k in range(8):
            sx = x0 + (k + .5) * (x1 - x0) / 8
            if sx > xe: break
            # stride tick
            d.line([(sx, y - 16), (sx, y + 16)], fill=(168, 156, 138), width=4)
            # breath pulse
            if k % ratio == 0:
                beat = (lt * 2.4) % 8
                hot = abs(((beat - k + 4) % 8) - 4) < 0.7
                r = 15 + (9 if hot else 0)
                d.ellipse([sx - r, y - r, sx + r, y + r],
                          fill=col + (255 if hot else 150,))
    lp = cl((lt - 2.40) / .7)
    if lp > 0:
        d.text((660, GY - 150), 'IT CANNOT PANT WHILE IT GALLOPS',
               font=F(40, 800), fill=INK + (int(255 * cl(lp * 1.8)),), anchor='mm')
    statchip(d, 'A GALLOP HOLDS ONLY 10–15 MINUTES', cl((lt - 3.5) / .6), acc)


# ---------- 7  THE CURVE -----------------------------------------------------
def s7(d, lt, acc):
    headline(d, ['TWO', 'CORE', 'TEMPERATURES'], cl(lt / .55), acc, {1}, 80)
    # chart frame
    x0, x1 = 300, 1620
    # dropped 54 px after the safe-area lift: the 44 deg end of the kudu
    # curve put its label right on the baseline of the headline.
    y0, y1 = GY - 466, GY - 96
    cp = cl((lt - .45) / .5)
    if cp > 0:
        xe = x0 + (x1 - x0) * e_out(cp, 2.2)
        d.line([(x0, y1), (xe, y1)], fill=(176, 164, 146), width=4)
        d.line([(x0, y1), (x0, y1 - (y1 - y0) * e_out(cp, 2.2))],
               fill=(176, 164, 146), width=4)
    if cp > .8:
        for v, lab in ((0.0, '37°'), (0.5, '40°'), (1.0, '44°')):
            yy = y1 - (y1 - y0) * v
            d.text((x0 - 20, yy), lab, font=F(26, 600), fill=SOFT, anchor='rm')
            if v > 0:
                for xx in range(int(x0), int(x1), 26):
                    d.line([(xx, yy), (xx + 13, yy)], fill=(214, 203, 184), width=2)
        d.text(((x0 + x1) / 2, y1 + 40), 'TIME IN PURSUIT  →', font=F(26, 600),
               fill=SOFT, anchor='mm')

    def curve(f, col, p, wdt=9):
        if p <= 0: return
        pts = []
        n = 110
        for i in range(int(n * e_out(p, 1.6)) + 1):
            u = i / n
            pts.append((x0 + (x1 - x0) * u, y1 - (y1 - y0) * f(u)))
        if len(pts) > 1:
            stroke(d, pts, col, wdt)
            d.ellipse([pts[-1][0] - 11, pts[-1][1] - 11,
                       pts[-1][0] + 11, pts[-1][1] + 11], fill=col)

    # the quarry: sawtooth sprints, each one leaving it hotter
    def f_kudu(u):
        return cl(u * 0.98 + 0.085 * math.sin(u * 20.0) * (1 - u * .4))
    # the hunter: a shallow plateau
    def f_man(u):
        return cl(0.26 * (1 - math.exp(-u * 4.2)) + 0.012 * math.sin(u * 13.0))

    curve(f_kudu, (171, 38, 30), cl((lt - 1.15) / 2.4))
    curve(f_man, acc, cl((lt - 1.55) / 2.4))
    if lt > 2.6:
        a = int(255 * cl((lt - 2.6) / .5))
        d.text((x1 - 30, y1 - (y1 - y0) * 0.99 - 42), 'THE KUDU',
               font=F(32, 800), fill=(171, 38, 30) + (a,), anchor='rm')
        d.text((x1 - 30, y1 - (y1 - y0) * 0.26 - 40), 'THE HUNTER',
               font=F(32, 800), fill=acc + (a,), anchor='rm')
    statchip(d, 'IT SPRINTS AND HEATS  ·  YOU JOG AND COOL',
             cl((lt - 4.6) / .6), acc)


# ---------- 8  THE PROOF -----------------------------------------------------
def s8(d, lt, acc):
    headline(d, ['THE', 'NAMIB', 'DESERT'], cl(lt / .55), acc, {1}, 82)
    pairs = [('38.9', '°C', 'THE HUNTER', (16, 104, 96), 600, .75),
             ('44.0', '°C', 'THE ORYX',   (171, 38, 30), 1320, 1.15)]
    for val, unit, nm, col, x, st in pairs:
        p = cl((lt - st) / .8)
        if p <= 0: continue
        a = int(255 * cl(p * 1.7))
        k = 1 + .05 * (1 - e_out(p, 2.0))
        f = F(int(170 * k), 800)
        yy = GY - 420 + fl(lt, 0 if x < 900 else 1, 3.2)
        d.text((x + 2, yy + 3), val, font=f, fill=(199, 189, 170, a), anchor='mm')
        d.text((x, yy), val, font=f, fill=col + (a,), anchor='mm')
        d.text((x + f.getlength(val) / 2 + 42, yy - 44), unit, font=F(54, 800),
               fill=INK + (a,), anchor='mm')
        d.text((x, yy + 118), nm, font=F(34, 700), fill=INK + (a,), anchor='mm')

    # the aphorism takes the stage
    ap = cl((lt - 4.00) / .8)
    if ap > 0:
        line(d, ['HE', "DIDN'T", 'OUTRUN', 'IT.'], W / 2, GY - 150, 72, 800,
             INK, {2}, acc, ap, 26)
    ap2 = cl((lt - 4.90) / .8)
    if ap2 > 0:
        line(d, ['HE', 'OUT-COOLED', 'IT.'], W / 2, GY - 56, 72, 800, INK, {1},
             acc, ap2, 26)
    statchip(d, 'AMBIENT 36–41 °C  ·  FIELD MEASUREMENT',
             cl((lt - 2.3) / .6) * (1 - cl((lt - 3.9) / .4)), acc)


SCENES = [s1, s2, s3, s4, s5, s6, s7, s8]

CAPS = [
    [(0.35, 3.00, 'You have been running for two hours', {4}),
     (3.10, 6.00, 'The antelope stopped being faster forty minutes ago', {6})],
    [(0.35, 2.10, 'No bow. No spear.', {1}),
     (2.20, 5.60, 'Nothing in your hands but a stick and a gourd of water', {7})],
    [(0.35, 2.60, 'It is forty-two degrees out here', {3}),
     (2.70, 5.80, 'Push too hard, and you go down before it does', {1})],
    [(0.35, 5.00, 'So how did the slowest predator become the one that never loses?', {4})],
    [(0.35, 3.10, 'Your skin carries up to four million sweat glands', {6}),
     (3.20, 6.10, "Ten times a chimpanzee's", {1})],
    [(0.20, 2.60, 'The kudu has almost none. It cools by panting', {5}),
     (2.70, 5.90, 'And it cannot pant while it gallops', {3})],
    [(0.35, 3.60, 'Every time it sprints, it heats up', {4}),
     (3.70, 7.60, 'Every time you jog, you cool down', {4})],
    [(0.35, 3.60, 'Researchers clocked a hunter below thirty-nine degrees', {5}),
     (3.70, 7.20, 'While the oryx he chased hit forty-four', {7})],
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


# ───────────────────────────────────────────── frame
def render(i):
    t = i / FPS
    si = max(k for k in range(NS) if t >= SCENE_START[k])
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

    base = backdrop(t, show, acc)
    # heat shimmer belongs to the heat beat, and bleeds a little either side
    sh = 0.0
    if show == 2: sh = 1.0
    elif show == 1: sh = 0.30 * cl(slt / 3.0)
    elif show == 3: sh = 0.35 * (1 - cl(slt / 2.2))
    if sh > 0:
        base = heat_shimmer(base, t, sh)

    cv = base.convert('RGBA')
    cv.alpha_composite(scene_img(show, slt))
    d = ImageDraw.Draw(cv, 'RGBA')
    chrome(d, t, show, acc)

    # horizontal wipe — 16:9 reads a side-to-side cut, not a vertical one.
    # Body of the panel is an 18 % tint so the mean luma never crashes.
    if tp is not None:
        nacc = ACC[tk + 1]
        tint = tuple(int(nacc[j] * .18 + PAPER[j] * .82) for j in range(3))
        glow = tuple(int(nacc[j] * .40 + PAPER[j] * .60) for j in range(3))
        e = e_io(tp)
        lx = W - 2 * W * e
        d.rectangle([lx + W * .028, 0, lx + W, H], fill=tint)
        d.rectangle([lx + W * .016, 0, lx + W * .028, H], fill=glow)
        d.rectangle([lx + W * .004, 0, lx + W * .016, H], fill=nacc)
        d.rectangle([lx, 0, lx + W * .004, H], fill=INK)

    frame = cv.convert('RGB')

    dur = SCENE_END[si] - SCENE_START[si]
    amp = (.024, .030, .020, .034, .026, .030, .022, .036)[si]
    z = 1.012 + amp * e_io(cl(lt / dur)) * (1 if si % 2 == 0 else -1) \
        + (.012 if si % 2 else 0) \
        + math.exp(-lt * 6.4) * math.sin(lt * 16.5) * .0048
    px = 5.6 * math.sin(t * .74 + .4) + 2.8 * math.sin(t * 1.31)
    py = 4.4 * math.sin(t * .58 + 1.7) + 2.2 * math.sin(t * 1.07 + .3)
    iz = 1.0 / z
    frame = frame.transform((W, H), Image.AFFINE,
                            (iz, 0, (W - W * iz) * .5 + px,
                             0, iz, (H - H * iz) * .5 + py), Image.BICUBIC)

    arr = np.asarray(frame).astype(np.float32)
    arr += _GRAIN
    # final 0.45 s: ease to paper so the hook hands off cleanly to the body
    ft = DUR_TOTAL - t
    if ft < 0.45:
        m = e_io(cl(ft / 0.45))
        arr = arr * m + np.float32(PAPER) * (1 - m)
    return np.clip(arr, 0, 255).astype(np.uint8)


def shard(a, b, path):
    import imageio_ffmpeg, time
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs('/home/user/build', exist_ok=True)
    p = subprocess.Popen([ff, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-an',
                          '-c:v', 'libx264', '-preset', 'faster', '-crf', '16',
                          '-pix_fmt', 'yuv420p', '-g', '30', path],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    t0 = time.time()
    for i in range(a, b):
        p.stdin.write(render(i).tobytes())
        k = i - a + 1
        if k % 50 == 0:
            el = time.time() - t0
            print(f'[{a}:{b}] {k}/{b-a} {el:.0f}s eta {el/k*(b-a-k):.0f}s',
                  flush=True)
    p.stdin.close(); p.wait()
    print(f'[{a}:{b}] DONE', flush=True)


if __name__ == '__main__':
    if len(sys.argv) == 4:
        shard(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
