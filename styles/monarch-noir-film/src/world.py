#!/usr/bin/env python3
"""
world.py — WF-03 · NOIRGO MAX world engine for THE WINDOW (2026-10-10)

Real-life world: illustrated plates (plates/*.png, generated once, graded here), per-window light control on the
opposite facade (plates/facade_windows.json — 55 cells, 31 lit at threshold lum>55), silhouette people inside the
windows (human.py, silhouette mode), the hero's own window (facade_hero: blue flicker → dark → amber), rain, dust,
camera push/drift, text (serif narration, typewriter red villain lines, Montserrat readouts), finish (vignette,
halation, grain) and measure(). Frames are composed at 1920×1080; the hero is drawn at 2× in a cropped canvas.
"""
import os, sys, math, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
WF = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(WF))
sys.path.insert(0, HERE)
import human as Hm  # noqa: E402

W, H = 1920, 1080
PLATES = os.path.join(WF, 'plates')
FD = os.path.join(ROOT, 'fonts')
F_SERIF = '/usr/share/R/doc/html/katex/fonts/KaTeX_Main-Regular.ttf'
F_SERIF_I = '/usr/share/R/doc/html/katex/fonts/KaTeX_Main-Italic.ttf'
F_TYPE = '/usr/share/R/doc/html/katex/fonts/KaTeX_Typewriter-Regular.ttf'
F_SANS = os.path.join(FD, 'Montserrat-VF.ttf')

BONE = (236, 232, 222)
RED = (214, 38, 32)
AMBER = np.array([255, 196, 128], np.float32)
BLUE = np.array([120, 170, 255], np.float32)
PX = 1376.0 / W   # plate px → frame px factor (plates are 1376×768)

_cache = {}


def font(path, size, var=None):
    f = ImageFont.truetype(path, int(size))
    if var:
        try:
            f.set_variation_by_name(var)
        except Exception:
            pass
    return f


# ─────────────────────────────────────────────── plates
def plate(name):
    """float32 RGB (H, W, 3) of plates/raw_<name>.png resized to 1920×1080 (cached)."""
    if name in _cache:
        return _cache[name]
    p = os.path.join(PLATES, f'raw_{name}.png')
    im = Image.open(p).convert('RGB').resize((W, H), Image.LANCZOS)
    arr = np.asarray(im, np.float32)
    if name == 'facade_hero_dark':
        pass
    _cache[name] = arr
    return arr


def facade_hero_dark():
    """facade_hero with the lit window painted dark (copy of the neighbouring dark window)."""
    if 'facade_hero_dark' in _cache:
        return _cache['facade_hero_dark']
    a = plate('facade_hero').copy()
    x0, y0, x1, y1 = HERO_WIN
    sx0 = x0 - int(180 / PX)  # neighbour window to the left, same row
    a[y0:y1, x0:x1] = a[y0:y1, sx0:sx0 + (x1 - x0)]
    _cache['facade_hero_dark'] = a
    return a


def camera(arr, zoom=1.0, cx=0.5, cy=0.5, dx=0.0, dy=0.0):
    """Crop-zoom a plate: zoom ≥ 1 about (cx, cy) in 0..1, plus drift in frame px. Returns float32 (H, W, 3)."""
    if zoom <= 1.0001 and abs(dx) < 0.5 and abs(dy) < 0.5:
        return arr
    cw, ch = W / zoom, H / zoom
    x0 = cx * W - cw / 2 + dx
    y0 = cy * H - ch / 2 + dy
    x0 = min(max(0.0, x0), W - cw)
    y0 = min(max(0.0, y0), H - ch)
    im = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    im = im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    return np.asarray(im, np.float32)


def to_frame_rect(r):
    """plate-px rect (x0, y0, x1, y1) → frame px."""
    return (int(r[0] / PX), int(r[1] / PX * (768 / 1080) * (1080 / 768)), int(r[2] / PX), int(r[3] / PX))


def _frame_rect(x0, y0, x1, y1):
    sx, sy = W / 1376.0, H / 768.0
    return (int(x0 * sx), int(y0 * sy), int(x1 * sx), int(y1 * sy))


# the hero's own window on facade_hero (plate px 650..725 × 305..410)
HERO_WIN = _frame_rect(650, 303, 727, 412)


def windows():
    """lit windows on the opposite facade (frame px rects + kind), sorted by id."""
    if 'wins' in _cache:
        return _cache['wins']
    cells = json.load(open(os.path.join(PLATES, 'facade_windows.json')))
    out = []
    for c in cells:
        if c['lum'] > 55:   # 31 lit windows (the number the script says)
            r = _frame_rect(c['x0'], c['y0'], c['x1'], c['y1'])
            kind = 'blue' if c['kind'] == 'blue' else 'amber'
            out.append(dict(id=c['id'], rect=r, kind=kind, lum=c['lum']))
    _cache['wins'] = out
    return out


def win_by_id(wid):
    return next(w for w in windows() if w['id'] == wid)


# ─────────────────────────────────────────────── light ops (all on float32 frames)
def _soft_rect_mask(rect, feather=6, grow=0):
    x0, y0, x1, y1 = rect
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).rectangle([x0 - grow, y0 - grow, x1 + grow, y1 + grow], fill=255)
    if feather > 0:
        m = m.filter(ImageFilter.GaussianBlur(feather))
    return np.asarray(m, np.float32) / 255


def window_gain(frame, rect, gain, color=None, feather=2):
    """multiply the window interior by gain (0 = off); optional colour push (float32 RGB) for a tint."""
    m = _soft_rect_mask(rect, feather)[..., None]
    base = frame
    out = base * gain
    if color is not None:
        lum = base.mean(2, keepdims=True)
        out = out * 0.4 + (lum / 255.0) * color[None, None, :] * gain * 0.6
    return base * (1 - m) + out * m


def glow(frame, center, radius, color, power=1.0, falloff=2.0):
    """additive radial glow (a practical's spill)."""
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xs - center[0]) ** 2 + (ys - center[1]) ** 2) / radius
    g = np.clip(1 - d, 0, 1) ** falloff
    return frame + g[..., None] * color[None, None, :] * power


def flicker(t, seed=0, rate=9.0, depth=0.35):
    """phone/TV light: stepwise content changes + fine shimmer, deterministic in t."""
    rng = np.random.default_rng(seed + int(t * rate))
    step = 1 - depth + depth * rng.random()
    shimmer = 1 + 0.05 * math.sin(t * 37.0 + seed) + 0.03 * math.sin(t * 61.0)
    return step * shimmer


def lamp_flicker(t, seed=1):
    return 1 + 0.025 * math.sin(t * 13.1 + seed) + 0.015 * math.sin(t * 29.7 + 2 * seed) + 0.01 * math.sin(t * 3.3)


# ─────────────────────────────────────────────── atmosphere
def rain(frame, t, density=160, alpha=0.16, speed=900, seed=5, angle=0.08):
    """procedural rain streaks scrolling down (deterministic per frame)."""
    rng = np.random.default_rng(seed)
    xs = rng.random(density) * (W + 200) - 100
    ys0 = rng.random(density) * H
    ln = 26 + rng.random(density) * 34
    layer = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(layer)
    off = (t * speed) % H
    for x, y0, L in zip(xs, ys0, ln):
        y = (y0 + off) % (H + 60) - 30
        d.line([(x + y * angle, y), (x + (y + L) * angle, y + L)], fill=int(255 * (0.5 + 0.5 * rng.random())), width=1)
    layer = layer.filter(ImageFilter.GaussianBlur(0.6))
    r = np.asarray(layer, np.float32) / 255
    return frame + r[..., None] * alpha * np.array([170, 185, 210], np.float32)


def dust(frame, t, center, radius, n=90, seed=9, color=AMBER, alpha=0.55):
    """slow drifting motes inside a practical's cone."""
    rng = np.random.default_rng(seed)
    ang = rng.random(n) * 2 * math.pi
    rad = np.sqrt(rng.random(n)) * radius
    ph = rng.random(n) * 10
    sz = 1.0 + rng.random(n) * 1.6
    layer = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(layer)
    for a, r, p, s in zip(ang, rad, ph, sz):
        x = center[0] + math.cos(a) * r + math.sin(t * 0.37 + p) * 18
        y = center[1] + math.sin(a) * r + t * 9 * (0.5 + s * 0.3) % 60 + math.cos(t * 0.29 + p) * 10
        br = int(255 * (0.35 + 0.65 * abs(math.sin(t * 0.8 + p * 3))))
        d.ellipse([x - s, y - s, x + s, y + s], fill=br)
    layer = layer.filter(ImageFilter.GaussianBlur(0.8))
    m = np.asarray(layer, np.float32) / 255
    return frame + m[..., None] * alpha * color[None, None, :]


# ─────────────────────────────────────────────── people
def person(frame_layer, x, y, s, pose, light, clip=None, **kw):
    """draw a human (hero or silhouette) into an RGBA PIL layer at frame scale using a 2× cropped canvas."""
    SS = 2
    # bounding canvas around the figure (generous)
    cw, ch = int(s * 1.6) * SS, int(s * 1.25) * SS
    ox, oy = int(x - s * 0.8), int(y - s * 1.12)
    can = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    lx = None if light is None else ((light[0] - ox) * SS, (light[1] - oy) * SS)
    J, KS, ex = Hm.draw_human(can, (x - ox) * SS, (y - oy) * SS, s * SS, pose, lx, **kw)
    small = can.resize((cw // SS, ch // SS), Image.LANCZOS)
    if clip is not None:
        m = Image.new('L', small.size, 0)
        ImageDraw.Draw(m).rectangle([clip[0] - ox, clip[1] - oy, clip[2] - ox, clip[3] - oy], fill=255)
        small.putalpha(Image.fromarray(np.minimum(np.asarray(m), np.asarray(small.split()[3]))))
    frame_layer.alpha_composite(small, dest=(max(0, ox), max(0, oy)), source=(max(0, -ox), max(0, -oy)))
    # joints back to frame px
    Jf = {k: ((v[0] / SS) + ox, (v[1] / SS) + oy) for k, v in J.items() if isinstance(v, tuple) and len(v) == 2}
    exf = {}
    for k, v in ex.items():
        if k.startswith('tip_') and v is not None:
            exf[k] = ((v[0] / SS) + ox, (v[1] / SS) + oy)
        elif k == 'head':
            c, rx, ry, ang, yaw = v
            exf[k] = (((c[0] / SS) + ox, (c[1] / SS) + oy), rx / SS, ry / SS, ang, yaw)
    return Jf, exf


def face_only(layer, c, rx, ry, roll, yaw, light, expr, look=(0, 0), blink_v=0.0, skin=(Hm.SKIN_DK, Hm.SKIN), alpha=255):
    """a big head (close-ups / reflections) drawn at 2× then downsampled into `layer` (RGBA, frame scale)."""
    SS = 2
    cw, ch = int(rx * 3.2) * SS, int(ry * 3.2) * SS
    ox, oy = int(c[0] - rx * 1.6), int(c[1] - ry * 1.6)
    can = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    cc = ((c[0] - ox) * SS, (c[1] - oy) * SS)
    lx = None if light is None else ((light[0] - ox) * SS, (light[1] - oy) * SS)
    ow = max(2, rx * SS * 0.03)
    Hm._flat(can, Hm.T._grow(Hm._ellipse(cc, rx * SS, ry * SS * 1.02, roll), ow), Hm.INK)
    Hm._two_tone(can, Hm._ellipse(cc, rx * SS, ry * SS * 1.02, roll), lx, rx * SS, skin[0], skin[1])
    E = Hm.EXPR[expr] if isinstance(expr, str) else expr
    Hm.draw_face(can, cc, rx * SS, ry * SS, roll, yaw, lx, E, look, blink_v)
    small = can.resize((cw // SS, ch // SS), Image.LANCZOS)
    if alpha < 255:
        a = small.split()[3].point(lambda v: v * alpha // 255)
        small.putalpha(a)
    layer.alpha_composite(small, dest=(max(0, ox), max(0, oy)), source=(max(0, -ox), max(0, -oy)))


# ─────────────────────────────────────────────── text
def text_layer():
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))


def narration(layer, txt, cx, cy, size=48, col=BONE, italic=False, alpha=255, shadow=True, tracking=0):
    d = ImageDraw.Draw(layer)
    f = font(F_SERIF_I if italic else F_SERIF, size)
    tw = d.textlength(txt, font=f)
    x, y = cx - tw / 2, cy - size * 0.6
    if shadow:
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x, y), txt, font=f, fill=(0, 0, 0, int(alpha * 0.9)))
        sh = sh.filter(ImageFilter.GaussianBlur(size * 0.12))
        layer.alpha_composite(sh)
    d.text((x, y), txt, font=f, fill=col + (alpha,))
    return (x, y, x + tw, y + size * 1.1)


def villain(layer, txt, x, y, size=42, alpha=255, col=RED):
    d = ImageDraw.Draw(layer)
    f = font(F_TYPE, size)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x, y), txt, font=f, fill=(0, 0, 0, int(alpha * 0.85)))
    sh = sh.filter(ImageFilter.GaussianBlur(size * 0.1))
    layer.alpha_composite(sh)
    d.text((x, y), txt, font=f, fill=col + (alpha,))


def readout(layer, txt, x=64, y=48, size=30, alpha=210, col=BONE):
    d = ImageDraw.Draw(layer)
    f = font(F_SANS, size, 'SemiBold')
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x, y), txt, font=f, fill=(0, 0, 0, int(alpha * 0.9)))
    sh = sh.filter(ImageFilter.GaussianBlur(size * 0.1))
    layer.alpha_composite(sh)
    d.text((x, y), txt, font=f, fill=col + (alpha,))


def typewriter(txt, t, t0, cps=18.0):
    """characters revealed at t (cps chars/s) from t0."""
    n = int(max(0.0, t - t0) * cps)
    return txt[:n]


def composite(frame, layer):
    """RGBA PIL layer over a float32 frame."""
    a = np.asarray(layer, np.float32)
    al = a[..., 3:4] / 255.0
    return frame * (1 - al) + a[..., :3] * al


# ─────────────────────────────────────────────── finish + measure
def grade(frame, cold=0.0, warm=0.0, lift=0.0, gamma=1.0, sat=1.0):
    """cold: push shadows blue; warm: push highlights amber; lift: raise blacks; gamma; sat."""
    f = frame / 255.0
    lum = f.mean(2, keepdims=True)
    if sat != 1.0:
        f = lum + (f - lum) * sat
    if cold:
        f = f + (1 - lum) * cold * np.array([-0.02, 0.0, 0.06], np.float32)[None, None, :]
    if warm:
        f = f + lum * warm * np.array([0.06, 0.02, -0.04], np.float32)[None, None, :]
    f = f + lift
    if gamma != 1.0:
        f = np.clip(f, 0, 1) ** gamma
    return np.clip(f, 0, 1) * 255.0


def finish(frame, rng, vignette=0.5, grain=1.5, halation=0.16):
    f = frame.astype(np.float32)
    if halation > 0:
        hi = np.clip(f - 150, 0, 255)
        im = Image.fromarray(hi.astype(np.uint8)).filter(ImageFilter.GaussianBlur(18))
        f = f + np.asarray(im, np.float32) * halation
    if vignette > 0:
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xs - W / 2) / (W / 2)) ** 2 + ((ys - H / 2) / (H / 2)) ** 2)
        v = 1 - vignette * np.clip(r - 0.45, 0, 1) ** 1.6
        f = f * v[..., None]
    if grain > 0:
        f = f + rng.normal(0, grain, (H, W, 1)).astype(np.float32)
    return np.clip(f, 0, 255).astype(np.uint8)


def measure(rgb):
    a = rgb.astype(np.float32)
    luma = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    chroma = (a.max(2) - a.min(2)).mean()
    return dict(luma=round(float(luma.mean()), 1), dark=round(float((luma < 30).mean()), 3),
                chroma=round(float(chroma), 1), p99=round(float(np.percentile(luma, 99)), 1))


def contrast(fg, bg):
    def L(c):
        c = np.array(c, np.float32) / 255
        c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    a, b = L(fg), L(bg)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)
