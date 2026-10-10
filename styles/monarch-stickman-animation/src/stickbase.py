"""Doodle/stickman drawing primitives: hand-drawn strokes, rigged stick figure, props, board."""
import math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
sys.path.insert(0, '/home/user/src')

W, H, FPS = 1080, 1920, 30
FD = '/home/user/fonts/'
MARKER, HAND, CAVEAT = FD + 'PermanentMarker.ttf', FD + 'PatrickHand.ttf', FD + 'Caveat-VF.ttf'

CHALK = (238, 242, 250)
GOLD = (255, 201, 60)
CYAN = (70, 224, 255)
MINT = (124, 255, 178)
RED = (255, 107, 107)
PINK = (255, 140, 200)
rng = np.random.default_rng(5)
TQ = 2

# ---------------------------------------------------------------- easing
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def out_back(x, s=1.9): x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2
def out_cubic(x): x = clamp(x); return 1 - (1 - x) ** 3
def out_expo(x): x = clamp(x); return 1 - 2 ** (-10 * x) if x < 1 else 1
def in_cubic(x): x = clamp(x); return x ** 3
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)

def hsh(a, b=0.0):
    v = math.sin(a * 12.9898 + b * 78.233) * 43758.5453
    return v - math.floor(v)

def jpt(p, seed, tq, amp=2.6):
    return (p[0] + (hsh(seed * 1.7 + tq * 3.1) - .5) * 2 * amp,
            p[1] + (hsh(seed * 3.3 + tq * 5.7 + 9.1) - .5) * 2 * amp)

def _cut(pts, p):
    if p >= 1: return pts
    if p <= 0: return []
    segs = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(segs) or 1
    want = total * p
    out = [pts[0]]; acc = 0
    for i, L in enumerate(segs):
        if acc + L >= want:
            k = (want - acc) / max(L, 1e-6)
            out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * k,
                        pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k))
            return out
        acc += L; out.append(pts[i + 1])
    return out

def poly(dr, pts, col=CHALK, w=9, p=1.0, seed=1.0, tq=0, amp=2.6, closed=False, fill=None):
    if len(pts) < 2 or p <= 0: return
    pj = [jpt(q, seed + i * 2.3, tq, amp) for i, q in enumerate(pts)]
    if closed: pj = pj + [pj[0]]
    pj = _cut(pj, p)
    if len(pj) < 2: return
    if fill and p >= 1: dr.polygon(pj, fill=fill)
    dr.line(pj, fill=col, width=w, joint='curve')
    r = w / 2 - .5
    for q in (pj[0], pj[-1]):
        dr.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)

def circ(dr, c, rad, col=CHALK, w=9, p=1.0, seed=2.0, tq=0, amp=2.4, segs=34, fill=None, start=-90):
    pts = [(c[0] + rad * math.cos(math.radians(start + 360 * i / segs)),
            c[1] + rad * math.sin(math.radians(start + 360 * i / segs))) for i in range(segs + 1)]
    if fill: dr.ellipse([c[0] - rad, c[1] - rad, c[0] + rad, c[1] + rad], fill=fill)
    poly(dr, pts, col, w, p, seed, tq, amp)

def arc(dr, c, rad, a0, a1, col=CHALK, w=9, p=1.0, seed=3.0, tq=0, amp=2.2, segs=22):
    pts = [(c[0] + rad * math.cos(math.radians(a0 + (a1 - a0) * i / segs)),
            c[1] + rad * math.sin(math.radians(a0 + (a1 - a0) * i / segs))) for i in range(segs + 1)]
    poly(dr, pts, col, w, p, seed, tq, amp)

def box(dr, x0, y0, x1, y1, col=CHALK, w=9, p=1.0, seed=4.0, tq=0, amp=2.4, fill=None):
    poly(dr, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], col, w, p, seed, tq, amp, closed=True, fill=fill)

def squiggle(dr, x0, y, x1, col=GOLD, w=8, p=1.0, seed=5.0, tq=0, amp=3, n=9, h=11):
    poly(dr, [(x0 + (x1 - x0) * i / n, y + (h if i % 2 else -h)) for i in range(n + 1)], col, w, p, seed, tq, amp)

def arrow(dr, a, b, col=CYAN, w=8, p=1.0, seed=6.0, tq=0, curve=0.25):
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]
    cx, cy = mx - dy * curve, my + dx * curve
    pts = [(a[0] * (1 - t) ** 2 + 2 * cx * t * (1 - t) + b[0] * t * t,
            a[1] * (1 - t) ** 2 + 2 * cy * t * (1 - t) + b[1] * t * t) for t in np.linspace(0, 1, 16)]
    poly(dr, pts, col, w, p, seed, tq)
    if p > .85:
        ang = math.atan2(pts[-1][1] - pts[-3][1], pts[-1][0] - pts[-3][0])
        for s in (2.6, -2.6):
            poly(dr, [b, (b[0] - 34 * math.cos(ang + s * .7), b[1] - 34 * math.sin(ang + s * .7))],
                 col, w, 1, seed + 3, tq)

# ---------------------------------------------------------------- text
_fc, _tc = {}, {}
def ft(path, size, var=None):
    k = (path, size, var)
    if k not in _fc:
        f = ImageFont.truetype(path, int(size))
        if var:
            try: f.set_variation_by_name(var)
            except Exception: pass
        _fc[k] = f
    return _fc[k]

def text_img(txt, size, col=CHALK, fontp=MARKER, rot=0., shadow=True, var=None, outline=0):
    key = (txt, size, col, fontp, round(rot, 1), outline)
    if key in _tc: return _tc[key]
    f = ft(fontp, size, var)
    pad = 36 + outline
    bb = f.getbbox(txt)
    im = Image.new('RGBA', (bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if outline:
        d.text((pad - bb[0], pad - bb[1]), txt, font=f, fill=(14, 17, 24, 255),
               stroke_width=outline, stroke_fill=(14, 17, 24, 255))
    d.text((pad - bb[0], pad - bb[1]), txt, font=f, fill=col + (255,))
    if shadow:
        g = im.getchannel('A').filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * .5))
        gl = Image.new('RGBA', im.size, col + (0,)); gl.putalpha(g)
        gl.alpha_composite(im); im = gl
    if rot: im = im.rotate(rot, Image.BICUBIC, expand=True)
    _tc[key] = im
    if len(_tc) > 160: _tc.pop(next(iter(_tc)))
    return im

def put(cv, im, cx, cy, scale=1., alpha=1., reveal=1.):
    if alpha <= .01 or scale <= .01: return
    if scale != 1:
        im = im.resize((max(2, int(im.width * scale)), max(2, int(im.height * scale))), Image.BILINEAR)
    if reveal < 1:
        m = Image.new('L', im.size, 0)
        ImageDraw.Draw(m).rectangle([0, 0, int(im.width * clamp(reveal)), im.size[1]], fill=255)
        im = im.copy(); im.putalpha(ImageChops.multiply(im.getchannel('A'), m))
    if alpha < .99:
        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
    cv.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def write(cv, txt, cx, cy, size, col=CHALK, fontp=MARKER, rot=0., p=1., scale=1., pop=False, var=None, outline=0):
    if p <= 0: return
    im = text_img(txt, size, col, fontp, rot, var=var, outline=outline)
    sc = scale * (out_back(p, 2.6) if pop else 1.0)
    put(cv, im, cx, cy, sc, clamp(p * 3) if pop else 1.0, 1.0 if pop else p)

# ---------------------------------------------------------------- stick rig
def rot2(a, v):
    ca, sa = math.cos(a), math.sin(a)
    return (v[0] * ca - v[1] * sa, v[0] * sa + v[1] * ca)

def stick(dr, x, y, s, pose, col=CHALK, w=10, seed=1.0, tq=0, p=1.0, face='neutral'):
    lean = math.radians(pose.get('lean', 0))
    hip = (x, y - .42 * s)
    off = rot2(lean, (0, -.36 * s))
    neck = (hip[0] + off[0], hip[1] + off[1])
    hr = .115 * s
    hd_off = rot2(lean + math.radians(pose.get('head', 0)), (0, -hr - .035 * s))
    head = (neck[0] + hd_off[0], neck[1] + hd_off[1])
    def limb(root, a1, a2, l1, l2):
        a1 = math.radians(a1) + lean; a2 = math.radians(a2) + a1
        j = (root[0] + l1 * math.sin(a1), root[1] + l1 * math.cos(a1))
        e = (j[0] + l2 * math.sin(a2), j[1] + l2 * math.cos(a2))
        return j, e
    sh = (neck[0], neck[1] + .03 * s)
    el_l, hd_l = limb(sh, pose.get('al', 20), pose.get('el', 10), .19 * s, .18 * s)
    el_r, hd_r = limb(sh, pose.get('ar', -20), pose.get('er', -10), .19 * s, .18 * s)
    kn_l, ft_l = limb(hip, pose.get('ll', 12), pose.get('kl', 0), .22 * s, .22 * s)
    kn_r, ft_r = limb(hip, pose.get('lr', -12), pose.get('kr', 0), .22 * s, .22 * s)
    circ(dr, head, hr, col, w, p, seed, tq, 2.0, segs=28)
    poly(dr, [neck, hip], col, w, p, seed + 1, tq)
    poly(dr, [sh, el_l, hd_l], col, w, p, seed + 2, tq)
    poly(dr, [sh, el_r, hd_r], col, w, p, seed + 3, tq)
    poly(dr, [hip, kn_l, ft_l], col, w, p, seed + 4, tq)
    poly(dr, [hip, kn_r, ft_r], col, w, p, seed + 5, tq)
    poly(dr, [ft_l, (ft_l[0] - .055 * s, ft_l[1])], col, w, p, seed + 8, tq)
    poly(dr, [ft_r, (ft_r[0] + .055 * s, ft_r[1])], col, w, p, seed + 9, tq)
    if p > .7 and face:
        er = max(2, int(.014 * s))
        ex, ey = head[0], head[1] - .012 * s
        for sx in (-1, 1):
            dr.ellipse([ex + sx * hr * .38 - er, ey - er, ex + sx * hr * .38 + er, ey + er], fill=col)
        mw = hr * .46; my = head[1] + hr * .34
        if face == 'happy':
            arc(dr, (head[0], my - mw * .5), mw, 20, 160, col, max(4, w - 4), 1, seed + 11, tq, 1.2, 10)
        elif face == 'sad':
            arc(dr, (head[0], my + mw * .7), mw, 200, 340, col, max(4, w - 4), 1, seed + 11, tq, 1.2, 10)
        else:
            poly(dr, [(head[0] - mw * .6, my), (head[0] + mw * .6, my)], col, max(4, w - 4), 1, seed + 11, tq, 1.2)
    return {'head': head, 'hand_l': hd_l, 'hand_r': hd_r, 'hip': hip, 'neck': neck, 'hr': hr}

# ---------------------------------------------------------------- poses
def pose_idle(t):
    b = math.sin(t * 2.2) * 4
    return dict(lean=math.sin(t * .7) * 2, head=math.sin(t * .9) * 3, al=18 + b, el=10,
                ar=-18 - b, er=-10, ll=10, kl=2, lr=-10, kr=2)

def pose_sad(t):
    return dict(lean=8, head=16 + math.sin(t * 1.4) * 2, al=14, el=20, ar=-14, er=-20,
                ll=8, kl=4, lr=-8, kr=4)

def pose_type(t, s=1.0):
    osc = math.sin(t * 13) * 7
    return dict(lean=12, head=6 + math.sin(t * 2.6) * 2, al=68 + osc, el=42, ar=66 - osc, er=44,
                ll=96, kl=-92, lr=88, kr=-86)

def pose_cheer(t):
    a = math.sin(t * 6.5) * 14
    return dict(lean=-3, head=-6, al=168 + a, el=12, ar=-168 - a, er=-12, ll=20, kl=6, lr=-20, kr=6)

def pose_point(t, right=True, up=False):
    a = 96 if not up else 150
    j = math.sin(t * 5) * 5
    if right:
        return dict(lean=2, head=4, al=16, el=12, ar=-a - j, er=-6, ll=11, kl=3, lr=-11, kr=3)
    return dict(lean=-2, head=-4, al=a + j, el=6, ar=-16, er=-12, ll=11, kl=3, lr=-11, kr=3)

def pose_think(t):
    return dict(lean=4, head=10 + math.sin(t) * 2, al=16, el=14, ar=-52, er=-108, ll=10, kl=3, lr=-10, kr=3)

def pose_walk(t):
    ph = t * 7.5
    return dict(lean=4, head=2, al=26 * math.sin(ph), el=18, ar=-26 * math.sin(ph), er=-18,
                ll=30 * math.sin(ph), kl=max(0, 26 * math.sin(ph + 1)),
                lr=-30 * math.sin(ph), kr=max(0, 26 * math.sin(ph + 4)))

def pose_shake(t):
    j = math.sin(t * 9) * 8
    return dict(lean=5, head=4, al=18, el=12, ar=-74 - j, er=-14, ll=11, kl=3, lr=-11, kr=3)

def pose_dance(t):
    ph = t * 7
    return dict(lean=math.sin(ph) * 10, head=math.sin(ph) * 8,
                al=120 + 40 * math.sin(ph), el=30, ar=-120 - 40 * math.sin(ph + 2), er=-30,
                ll=18 + 14 * math.sin(ph), kl=8, lr=-18 - 14 * math.sin(ph + 3), kr=8)

# ---------------------------------------------------------------- props
def coin(dr, x, y, r, tq, seed, p=1.0, col=GOLD, spin=0.0):
    rx = max(3, abs(math.cos(spin)) * r)
    pts = [(x + rx * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))) for a in range(0, 361, 18)]
    poly(dr, pts, col, 7, p, seed, tq, 1.8)
    if rx > r * .45 and p > .6:
        dr.text((x, y), '$', font=ft(MARKER, int(r * 1.5)), fill=col, anchor='mm')

def laptop(dr, x, y, w_, tq, seed, p=1.0, screen=None, col=CHALK):
    h_ = w_ * .62
    box(dr, x - w_ / 2, y - h_, x + w_ / 2, y, col, 8, clamp(p * 2), seed, tq)
    poly(dr, [(x - w_ * .62, y + 18), (x + w_ * .62, y + 18), (x + w_ * .5, y), (x - w_ * .5, y)],
         col, 8, clamp((p - .35) * 2.4), seed + 2, tq, closed=True)
    if screen and p > .6:
        screen(dr, x, y - h_ / 2, w_ * .8, h_ * .66, clamp((p - .6) / .4))

def play_btn(dr, cx, cy, s, p=1., col=RED, tq=0, seed=9):
    box(dr, cx - s, cy - s * .7, cx + s, cy + s * .7, col, 7, p, seed, tq)
    if p > .8:
        dr.polygon([(cx - s * .22, cy - s * .33), (cx + s * .34, cy), (cx - s * .22, cy + s * .33)], fill=col)

def speech(dr, cx, cy, w_, h_, tail=(0, 1), p=1., col=CHALK, tq=0, seed=11):
    pts = [(cx - w_ / 2, cy - h_ / 2), (cx + w_ / 2, cy - h_ / 2), (cx + w_ / 2, cy + h_ / 2),
           (cx + w_ * tail[0] * .5 + 36, cy + h_ / 2), (cx + w_ * tail[0] * .5, cy + h_ / 2 + 44),
           (cx + w_ * tail[0] * .5 - 24, cy + h_ / 2), (cx - w_ / 2, cy + h_ / 2)]
    poly(dr, pts, col, 7, p, seed, tq, 2.0, closed=True)

def star(dr, x, y, r, col=GOLD, p=1., tq=0, seed=13, w=6):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * .45
        a = math.radians(-90 + i * 36)
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    poly(dr, pts, col, w, p, seed, tq, 1.6, closed=True)

def tick(dr, x, y, s, col=MINT, p=1., tq=0, seed=17):
    poly(dr, [(x - s, y), (x - s * .25, y + s * .7), (x + s, y - s * .8)], col, 9, p, seed, tq, 1.8)

def cross(dr, x, y, s, col=RED, p=1., tq=0, seed=19, w=8):
    poly(dr, [(x - s, y - s), (x + s, y + s)], col, w, clamp(p * 2), seed, tq, 1.6)
    poly(dr, [(x + s, y - s), (x - s, y + s)], col, w, clamp(p * 2 - 1), seed + 1, tq, 1.6)

def _bullet(cv, d, tq, x, y, txt, p, i, col=CHALK):
    if p <= 0: return
    tick(d, x, y, 26, MINT, clamp(p * 2), tq, 70 + i)
    write(cv, txt, x + 190, y - 6, 58, col, HAND, p=clamp((p - .3) / .5))

# ---------------------------------------------------------------- board
def make_board():
    base = np.zeros((H // 3, W // 3, 3), np.float32)
    base[:] = np.array([16, 20, 28], np.float32)
    base += rng.normal(0, 7, (H // 3, W // 3, 1))
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6))
    img = img.resize((W, H), Image.BICUBIC)
    d = ImageDraw.Draw(img)
    for _ in range(900):
        x, y = rng.integers(0, W), rng.integers(0, H)
        r = rng.integers(1, 3); v = int(rng.integers(26, 60))
        d.ellipse([x, y, x + r, y + r], fill=(v + 10, v + 12, v + 16))
    for _ in range(14):
        x, y = int(rng.integers(0, W)), int(rng.integers(0, H))
        rr = int(rng.integers(70, 240))
        sm = Image.new('RGBA', (rr * 2, rr * 2), (0, 0, 0, 0))
        ImageDraw.Draw(sm).ellipse([0, 0, rr * 2, rr * 2], fill=(255, 255, 255, 7))
        reg = img.crop((x - rr, y - rr, x + rr, y + rr)).convert('RGBA')
        img.paste(Image.alpha_composite(reg, sm).convert('RGB'), (x - rr, y - rr))
    return img.convert('RGB')

BOARD = make_board()
_vy, _vx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_vx - W / 2) / (W / 2)) ** 2 + ((_vy - H / 2) / (H / 2)) ** 2)
VIGN = np.clip(1.06 - .45 * _r ** 2.0, 0, 1.1)[..., None].astype(np.float32)
del _vy, _vx, _r
GRAIN = rng.normal(0, 1, (H // 2, W // 2, 1)).astype(np.float32)
