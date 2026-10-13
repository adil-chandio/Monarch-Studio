"""cards3d.py — AMEER KA KUTTA v8: real 3D card transitions.

Each shot is a textured card placed in a 3D stage. The camera is a pinhole (focal ZD = 1.55 frame widths),
cards are rotated in 3D, projected with true perspective, depth-sorted, and given:
  * side thickness (the card has a visible edge wall, not a flat sheet)
  * a cast shadow on the floor plane, softly blurred
  * a moving light sheen across the face, and a neon edge in the chapter accent colour
  * a receding floor grid and streaking particles (speed = how fast the stage travels)
  * chromatic split on the fastest frames

Moves (all take A, B as HxWx3 uint8, p in [0, 1], acc = accent RGB):
  carousel : four cards on a ring; the ring turns 90 degrees (A leaves, B arrives)
  tunnel   : A flies past the camera, B swings in out of depth
  deck     : A is thrown up and out; B's deck rises from depth with a fanned stack behind it

Numpy + PIL only. Frame size comes from the input.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import transitions3d as T3

TOP = np.array([7, 6, 12], np.float32)
BOT = np.array([26, 19, 36], np.float32)
_GRID = {}


class Stage:
    def __init__(self, A, acc):
        T3._size(A.shape[1], A.shape[0])
        self.W, self.H, self.ZD = T3.W, T3.H, T3.ZD
        self.acc = np.array(acc if acc is not None else (255, 201, 60), np.float32)

    def proj(self, x, y, z):
        return (self.W / 2.0 + self.ZD * x / z, self.H / 2.0 + self.ZD * y / z)


def _ease(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def _Rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float64)


def _Ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float64)


def _Rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float64)


def _hull(pts):
    pts = sorted(set((float(x), float(y)) for x, y in pts))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lo = []
    for q in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    up = []
    for q in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def background(st, p, glow=0.22, grid=0.0):
    """dark vertical gradient, accent glow behind the subject, receding floor grid."""
    W, H, ZD = st.W, st.H, st.ZD
    if (W, H) not in _GRID:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        _GRID[(W, H)] = (yy, xx)
    yy, xx = _GRID[(W, H)]
    g = np.exp(-(((xx - W / 2) / (W * 0.70)) ** 2 + ((yy - H * 0.40) / (H * 0.42)) ** 2)).astype(np.float32)
    vy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    base = TOP * (1 - vy) + BOT * vy
    img = np.broadcast_to(base, (H, W, 3)) + g[..., None] * st.acc * glow * (0.75 + 0.25 * math.sin(math.pi * p))
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    col = tuple(int(v) for v in st.acc * 0.9) + (80,)
    f = grid % 1.0
    Yf = 0.5 * H                       # floor sits half a frame below the camera axis
    for j in range(0, 14):
        z = ZD * (0.45 + 0.42 * (j + f))
        if z < 0.2 * ZD:
            continue
        y = H / 2.0 + ZD * Yf / z
        if y < H:
            d.line([(0, y), (W, y)], fill=col, width=2)
    for kx in range(-7, 8):
        xw = kx * 0.55 * W
        d.line([st.proj(xw, Yf, 0.45 * ZD), st.proj(xw, Yf, 6.0 * ZD)], fill=col, width=2)
    d.line([(0, H / 2.0), (W, H / 2.0)], fill=tuple(int(v) for v in st.acc) + (60,), width=2)
    return Image.alpha_composite(im, ov)


def _paint_poly(canvas, st, polys, color, alpha, blur=0.0, outline=False, width=3):
    """paint polygons in one colour with alpha, on a cropped mask (fast, bounded by the frame)."""
    if alpha <= 0.002:
        return
    xs = [x for poly in polys for x, _ in poly]
    ys = [y for poly in polys for _, y in poly]
    pad = int(blur * 3) + width + 4
    x0 = max(0, int(math.floor(min(xs))) - pad)
    y0 = max(0, int(math.floor(min(ys))) - pad)
    x1 = min(st.W, int(math.ceil(max(xs))) + pad)
    y1 = min(st.H, int(math.ceil(max(ys))) + pad)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    m = Image.new('L', (x1 - x0, y1 - y0), 0)
    d = ImageDraw.Draw(m)
    for poly in polys:
        q = [(x - x0, y - y0) for x, y in poly]
        if outline:
            d.line(q + [q[0]], fill=255, width=width, joint='curve')
        else:
            d.polygon(q, fill=255)
    if blur > 0:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    m = m.point(lambda v: int(v * alpha))
    canvas.paste(Image.new('RGB', m.size, tuple(int(v) for v in color)), (x0, y0), m)


def card(canvas, st, tex, c, ry=0.0, rx=0.0, rz=0.0, s=1.0, alpha=1.0, shade=1.0, thick=26.0,
         shadow=0.5, sheen=None, edge=True, sheen_gain=1.0):
    """one textured card. c = centre (x, y, depth). Returns nothing; paints onto canvas (RGB)."""
    if alpha <= 0.004 or shade <= 0.0:
        return
    W, H, ZD = st.W, st.H, st.ZD
    R = _Ry(ry) @ _Rx(rx) @ _Rz(rz)
    cc = np.asarray(c, np.float64)
    hw, hh = W * s / 2.0, H * s / 2.0
    local = np.array([[-hw, -hh, 0.0], [hw, -hh, 0.0], [hw, hh, 0.0], [-hw, hh, 0.0]])
    world = (R @ local.T).T + cc
    if world[:, 2].min() < 0.15 * ZD:
        return
    n = R @ np.array([0.0, 0.0, -1.0])          # visible-face normal (toward the viewer when facing > 0)
    view = -cc / np.linalg.norm(cc)
    facing = float(n @ view)
    sgn = 1.0 if facing >= 0 else -1.0
    front = [st.proj(*P) for P in world]
    back = [st.proj(*(P - n * thick * sgn)) for P in world]
    # cast shadow, offset down and blurred (reads as a card floating above the floor)
    if shadow > 0:
        off = 0.035 * H * s * (ZD / max(world[:, 2].mean(), 1.0))
        sh = [[(x + 0.02 * W * (ZD / max(world[:, 2].mean(), 1.0)) * 0.0, y + off) for x, y in front]]
        _paint_poly(canvas, st, sh, (0, 0, 0), shadow * alpha, blur=max(6.0, 0.02 * W))
    # side wall (edge thickness)
    if thick > 0:
        col = np.clip(st.acc * 0.30 * shade + 8, 0, 255)
        _paint_poly(canvas, st, [_hull(front + back)], col, alpha)
    # face
    tex_use = tex if facing >= 0 else tex.transpose(Image.FLIP_LEFT_RIGHT)
    fsh = shade * (0.40 + 0.60 * min(1.0, abs(facing))) * (1.0 if facing >= 0 else 0.62)
    piece = T3.warp_quad(tex_use, front)
    if piece is None:
        return
    x0, y0, rgb, mask = piece
    arr = np.asarray(rgb).astype(np.float32) * fsh
    if sheen is not None:
        xs = (np.arange(arr.shape[1], dtype=np.float32) + x0) / W
        band = np.exp(-((xs - sheen) / 0.07) ** 2) * 0.32 * sheen_gain
        arr = arr + band[None, :, None] * 255.0 * fsh
    rgb2 = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    m = mask if alpha >= 0.999 else mask.point(lambda v: int(v * alpha))
    canvas.paste(rgb2, (x0, y0), m)
    # neon edge in the chapter accent
    if edge:
        _paint_poly(canvas, st, [front], st.acc, alpha * 0.85, outline=True, width=3)


def particles(canvas, st, p, n=60, speed=1.0, seed=3):
    """streaking motes travelling through depth. speed = how fast the stage moves toward the camera."""
    W, H, ZD = st.W, st.H, st.ZD
    rng = np.random.default_rng(seed)
    X = rng.uniform(-1.3, 1.3, n) * W
    Y = rng.uniform(-1.0, 1.0, n) * H
    Z0 = rng.uniform(0.0, 1.0, n)
    S = rng.uniform(0.6, 1.4, n)
    mask = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(mask)
    span = 2.2 * ZD
    for i in range(n):
        z = 0.22 * ZD + ((Z0[i] * span - speed * p * 2.0 * ZD * S[i]) % span)
        zt = z + 0.10 * ZD * speed * S[i]
        x1, y1 = st.proj(X[i], Y[i], z)
        x0, y0 = st.proj(X[i], Y[i], zt)
        k = min(1.0, max(0.0, (2.4 * ZD - z) / (1.6 * ZD))) * min(1.0, max(0.0, (z - 0.22 * ZD) / (0.3 * ZD)))
        w = max(1, int(3.5 * ZD / z * S[i]))
        d.line([(x0, y0), (x1, y1)], fill=int(255 * k), width=w)
    col = tuple(int(v) for v in (0.55 * 255 + 0.45 * st.acc))
    canvas.paste(Image.new('RGB', (W, H), col), (0, 0), mask)


def chroma(img, amt):
    """lateral colour split on the fastest frames (R right, B left)."""
    if amt < 0.5:
        return img
    k = int(round(amt))
    out = img.copy()
    out[..., 0] = np.roll(img[..., 0], k, axis=1)
    out[..., 2] = np.roll(img[..., 2], -k, axis=1)
    return out


# ───────────────────────────────────────────────────────── carousel: four cards on a turning ring
def carousel(A, B, p, acc=None):
    st = Stage(A, acc)
    ZD = st.ZD
    e = _ease(p)
    rot = -(math.pi / 2) * e
    Rr = 0.36 * ZD
    Zc = ZD + Rr                                  # ring centre: the front card sits exactly at ZD
    canvas = background(st, p, glow=0.20, grid=e * 1.0).convert('RGB')
    ta, tb = Image.fromarray(A), Image.fromarray(B)
    slots = [(ta, 1.0), (tb, 1.0), (tb, 0.42), (ta, 0.42)]     # front A, right B, back B, left A (dim)
    cards = []
    for k, (tex, shade) in enumerate(slots):
        th = k * math.pi / 2 + rot
        c = (Rr * math.sin(th), 0.0, Zc - Rr * math.cos(th))
        cards.append((c[2], tex, c, th, shade))
    sheen = (p * 1.7 - 0.35)
    g = _ease(min(1.0, p / 0.25)) * _ease(min(1.0, (1.0 - p) / 0.25))   # light band fades in/out: no step at the window edges
    for z, tex, c, th, shade in sorted(cards, key=lambda t: -t[0]):
        # front card is 1.01x the frame so its edges are never uncovered (no dark margin at p=0 / p=1,
        # where it must match the flat shot exactly); the back/side cards keep the 0.92 ring size.
        # continuous in the angle (a hard switch at cos>0.99 made the front card jump one frame at p~.18)
        cz = max(0.0, math.cos(th)) ** 8 if shade >= 1.0 else 0.0
        card(canvas, st, tex, c, ry=th, s=0.92 + 0.09 * cz, shade=shade, thick=30, shadow=0.55,
             sheen=sheen if shade >= 1.0 else None, sheen_gain=g)
    particles(canvas, st, _ease(p), n=36, speed=0.30, seed=5)     # eased: no velocity jump at the window edges
    return chroma(np.asarray(canvas).astype(np.uint8), 2.5 * math.sin(math.pi * p))


# ───────────────────────────────────────────────────────── tunnel: A flies past the lens, B swings in
def tunnel(A, B, p, acc=None):
    st = Stage(A, acc)
    W, H, ZD = st.W, st.H, st.ZD
    canvas = background(st, p, glow=0.30, grid=_ease(p) * 4.0).convert('RGB')
    eb = _ease(p)
    tb = Image.fromarray(B)
    # B's alpha spreads over the whole move (was p .12-.72): a bright B popping in at the end read as a 10-level/frame flash
    # depth follows 1/z linear in p: B's screen coverage grows at a constant rate (no end-of-move flood)
    # v9: the last 20 % of B's approach decelerates to zero velocity (cubic Hermite, C1 at p=.8), so the move
    # does not stop dead at the window end (that stop was a 9-level step in motion energy when it met a deck)
    pc = min(1.0, max(0.0, p))
    if pc > 0.65:                                   # spread over the last 35 %: the 1.33x velocity bump lands at p=.77,
        u = (pc - 0.65) / 0.35                      # where B is still small (a late bump stepped a bright B by 8.4 levels)
        pc = 0.65 + 0.35 * (-u ** 3 + u ** 2 + u)
    zb = ZD * 2.6 / (1.0 + 1.6 * pc)
    card(canvas, st, tb, (W * 0.55 * (1 - eb) ** 1.6, 0.0, zb),
         ry=0.9 * (1 - eb), rz=0.12 * (1 - eb), s=1.0,
         alpha=_ease(pc / 0.95), shade=0.25 + 0.75 * pc, thick=34, shadow=0.45, sheen=p * 1.7 - 0.35)
    ta = Image.fromarray(A)
    za = ZD * (1 - 0.72 * (p ** 1.6))
    card(canvas, st, ta, (-0.45 * W * p ** 1.6, 0.05 * H * p, za), ry=0.35 * p, rz=-0.20 * p, s=1.0,
         alpha=1 - _ease((p - 0.45) / 0.5), shade=1.0, thick=44, shadow=0.0, sheen=None)
    particles(canvas, st, _ease(p), n=120, speed=1.6, seed=11)
    return chroma(np.asarray(canvas).astype(np.uint8), 6.0 * math.sin(math.pi * p))


# ───────────────────────────────────────────────────────── deck: A thrown up, B's deck rises from depth
def deck(A, B, p, acc=None):
    st = Stage(A, acc)
    W, H, ZD = st.W, st.H, st.ZD
    canvas = background(st, p, glow=0.18, grid=_ease(p) * 1.5).convert('RGB')
    f = 1.0 - _ease((p - 0.10) / 0.80)            # 1 at start (deck far away) -> 0 when settled
    tb = Image.fromarray(B)
    for k in (3, 2, 1):                           # fanned copies behind B, fading out as B settles
        card(canvas, st, tb, (-k * 0.06 * W * f, k * 0.03 * H * f, ZD * (1 + 0.7 * f + 0.20 * k)),
             ry=0.0, rz=0.035 * k * f, s=1.0, alpha=max(0.0, f) * 0.95, shade=0.42 - 0.08 * k,
             thick=20, shadow=0.35, edge=False)
    card(canvas, st, tb, (0.0, 0.0, ZD * (1 + 0.7 * f)), s=1.0 + 0.75 * f, shade=1.0, thick=30, shadow=0.5,
         sheen=p * 1.7 - 0.35, sheen_gain=_ease(min(1.0, p / 0.25)))
    ea = _ease(p)
    ta = Image.fromarray(A)
    card(canvas, st, ta, (0.10 * W * ea, -1.05 * H * _ease(p ** 1.2), ZD * (1 - 0.35 * ea)),
         rx=1.25 * ea, rz=0.10 * ea, s=1.0, alpha=1 - _ease((p - 0.15) / 0.55), shade=1.0,
         thick=34, shadow=0.45, sheen=None)
    particles(canvas, st, _ease(p), n=40, speed=0.5, seed=17)
    return chroma(np.asarray(canvas).astype(np.uint8), 3.0 * math.sin(math.pi * p))
