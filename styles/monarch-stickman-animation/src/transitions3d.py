"""True 3D / parallax transitions for AMEER KA KUTTA (v7). Numpy + PIL only, no GPU, no bpy.

Every transition is a real perspective projection of planar pieces (box faces, hinged page, origami
strips, shattered triangles) or a depth-layered parallax push. Frame size comes from the input, so the
module works for any canvas (kutta2 renders 1080x1920).

  page      : hinged page turning over its left spine, B revealed underneath
  cube_h/_v : rotating box, A on the front face, B on the side face
  depth     : parallax push-through. Each shot is three layers (backdrop, actors, UI) that move at
              different speeds and scales, so the outgoing layers fly past the camera while the
              incoming ones grow out of depth
  fold      : 10-strip origami accordion. A folds to a thin line, B unfolds from it
  shatter   : 3D glass shards (triangles) rotate and drift into depth, revealing B underneath
  flare     : light leak with chromatic split and lens ghosts

Camera: origin, looking +z. Plane distance ZD == focal length, so an untransformed plane fills the frame.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
ZD = 1.55 * W


def _size(w, h):
    global W, H, ZD
    W, H = int(w), int(h)
    ZD = 1.55 * W


def _smooth(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


_e = _smooth


def _rot(axis, th):
    c, s = math.cos(th), math.sin(th)
    if axis == 'y':
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float64)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float64)


def _rodrigues(axis, th):
    axis = np.asarray(axis, np.float64)
    axis = axis / (np.linalg.norm(axis) + 1e-12)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * (K @ K)


def _solve_coeffs(dst, src, n):
    """solve the projective (n=8) or affine (n=6) map dst(x,y) -> src."""
    A, b = [], []
    for (x, y), (sx, sy) in zip(dst, src):
        if n == 8:
            A.append([x, y, 1, 0, 0, 0, -sx * x, -sx * y]); b.append(sx)
            A.append([0, 0, 0, x, y, 1, -sy * x, -sy * y]); b.append(sy)
        else:
            A.append([x, y, 1, 0, 0, 0]); b.append(sx)
            A.append([0, 0, 0, x, y, 1]); b.append(sy)
    return tuple(np.linalg.solve(np.array(A, np.float64), np.array(b, np.float64)).tolist())


def _coeffs(dst, src):
    return _solve_coeffs(dst, src, 8)


def _affine(dst3, src3):
    return _solve_coeffs(dst3, src3, 6)


def _bbox(pts, pad=2):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0 = max(0, int(math.floor(min(xs))) - pad)
    y0 = max(0, int(math.floor(min(ys))) - pad)
    x1 = min(W, int(math.ceil(max(xs))) + pad)
    y1 = min(H, int(math.ceil(max(ys))) + pad)
    return x0, y0, x1, y1


def warp_quad(tex, quad):
    """tex: PIL RGB texture; quad: TL, TR, BR, BL on screen. -> (x0, y0, rgb, mask) or None."""
    x0, y0, x1, y1 = _bbox(quad)
    bw, bh = x1 - x0, y1 - y0
    if bw < 2 or bh < 2:
        return None
    local = [(x - x0, y - y0) for x, y in quad]
    tw, th = tex.size
    co = _coeffs(local, [(0, 0), (tw, 0), (tw, th), (0, th)])
    rgb = tex.transform((bw, bh), Image.PERSPECTIVE, co, Image.BILINEAR)
    mask = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(mask).polygon(local, fill=255, outline=255)
    return x0, y0, rgb, mask


def warp_tri(tex, dst, src):
    """affine map of the source triangle `src` (texture px) onto screen triangle `dst`."""
    x0, y0, x1, y1 = _bbox(dst)
    bw, bh = x1 - x0, y1 - y0
    if bw < 2 or bh < 2:
        return None
    local = [(x - x0, y - y0) for x, y in dst]
    co = _affine(local, src)
    rgb = tex.transform((bw, bh), Image.AFFINE, co, Image.BILINEAR)
    mask = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(mask).polygon(local, fill=255, outline=255)
    return x0, y0, rgb, mask


def _paste(canvas, piece, shade=1.0):
    x0, y0, rgb, mask = piece
    if shade != 1.0:
        a = np.asarray(rgb).astype(np.float32) * shade
        rgb = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    canvas.paste(rgb, (x0, y0), mask)


def _arr(img):
    return Image.fromarray(img) if isinstance(img, np.ndarray) else img


def _np(img):
    return np.asarray(img.convert('RGB')).astype(np.float32)


# ───────────────────────────────────────────────────────── page (hinged, 3D)
def page_h(A, B, p, acc=None):
    _size(A.shape[1], A.shape[0])
    e = _e(p)
    phi = math.pi * e
    a, b = W / 2.0, H / 2.0
    zd = 2.7 * W
    rel = np.array([[-a, -b, 0.0], [a, -b, 0.0], [a, b, 0.0], [-a, b, 0.0]])
    rot = rel.copy()
    x = rel[:, 0] - (-a)
    rot[:, 0] = x * math.cos(phi) - a
    rot[:, 2] = -x * math.sin(phi) - 2.0
    z = rot[:, 2] + zd
    q = [(W / 2 + zd * px / zz, H / 2 + zd * py / zz) for (px, py, _), zz in zip(rot, z)]
    base = _np(Image.fromarray(B)) * (0.72 + 0.28 * (0.55 + 0.45 * (1 - math.sin(phi))))
    canvas = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    if np.all(z > 1):
        back = phi > math.pi / 2
        tex = Image.fromarray(np.ascontiguousarray(A[:, ::-1] if back else A))
        piece = warp_quad(tex, q)
        if piece is not None:
            _paste(canvas, piece, (0.55 if back else 1.0) * (0.86 + 0.14 * math.cos(phi)))
    return np.asarray(canvas.convert('RGB'))


# ───────────────────────────────────────────────────────── cube (rotating box)
def cube(A, B, p, axis='y', flip=False):
    _size(A.shape[1], A.shape[0])
    e = _e(p)
    sign = (-1 if axis == 'x' else 1) * (-1 if flip else 1)
    th = (math.pi / 2) * e * sign
    a = W / 2.0
    b = H / 2.0
    c = W / 2.0 if axis == 'y' else H / 2.0
    zc = ZD + c
    R = _rot(axis, th)
    if axis == 'y':
        front = np.array([[-a, -b, -c], [a, -b, -c], [a, b, -c], [-a, b, -c]], np.float64)
        side = np.array([[a, -b, -c], [a, -b, c], [a, b, c], [a, b, -c]], np.float64)
        ns = np.array([1.0, 0, 0])
    else:
        front = np.array([[-a, -b, -c], [a, -b, -c], [a, b, -c], [-a, b, -c]], np.float64)
        side = np.array([[-a, b, -c], [a, b, -c], [a, b, c], [-a, b, c]], np.float64)
        ns = np.array([0, 1.0, 0])
    nf = np.array([0, 0, -1.0])
    pieces = []
    for pts, n, tex_arr, is_front in ((front, nf, A, True), (side, ns, B, False)):
        Rp = (R @ pts.T).T
        Rn = R @ n
        centre = Rp.mean(0) + np.array([0, 0, zc])
        if np.dot(Rn, -centre) <= 0:
            continue
        z = Rp[:, 2] + zc
        if np.any(z <= 1):
            continue
        q = [(W / 2 + ZD * px / zz, H / 2 + ZD * py / zz) for (px, py, _), zz in zip(Rp, z)]
        lam = max(0.0, float(np.dot(Rn, np.array([-.45, -.55, -.7]))))
        if is_front:
            k = 1.0 - 0.30 * e
        else:
            k = 0.70 + 0.30 * e
        pc = warp_quad(Image.fromarray(tex_arr), q)
        if pc is not None:
            pieces.append((centre[2], pc, k))
    pieces.sort(key=lambda t: -t[0])
    canvas = Image.fromarray(np.clip(_np(Image.fromarray(A if e < .5 else B)) * 0.0, 0, 255).astype(np.uint8))
    under = Image.fromarray((A if e < .5 else B)).filter(ImageFilter.GaussianBlur(28))
    canvas = Image.fromarray(np.clip(np.asarray(under).astype(np.float32) * 0.60 + 24.0, 0, 255).astype(np.uint8))
    for _, pc, k in pieces:
        _paste(canvas, pc, k)
    return np.asarray(canvas.convert('RGB'))


def cube_h(A, B, p, acc=None):
    return cube(A, B, p, axis='y')


def cube_v(A, B, p, acc=None):
    return cube(A, B, p, axis='x')


# ───────────────────────────────────────────────────────── depth: parallax push-through
def _xf(img, s, dx, dy, alpha=1.0):
    """scale an RGBA layer about the frame centre, then shift it. alpha multiplies the layer."""
    cx, cy = W / 2.0, H / 2.0
    a = 1.0 / s
    co = (a, 0, cx * (1 - a) - dx / s, 0, a, cy * (1 - a) - dy / s)
    out = img.transform((W, H), Image.AFFINE, co, resample=Image.BILINEAR)
    if alpha < 0.999:
        al = out.getchannel('A').point(lambda v, k=alpha: int(v * k))
        out.putalpha(al)
    return out


def depth_push(PA, PB, p, acc=(255, 201, 60)):
    """PA/PB = (backdrop, actors, ui) RGBA layers of the outgoing / incoming shot."""
    _size(PA[0].size[0], PA[0].size[1])
    e = _e(p)
    ea = e ** 1.6
    out = Image.new('RGBA', (W, H), (8, 6, 10, 255))
    # incoming shot: starts far away (small, soft), grows out of depth into place
    bg_b = PB[0]
    if e < 0.95:
        bg_b = _xf(bg_b, 0.78 + 0.22 * e, -24 * (1 - e), 0)
        if 1 - e > 0.05:
            bg_b = bg_b.filter(ImageFilter.GaussianBlur(6 * (1 - e)))
    out.alpha_composite(bg_b)
    out.alpha_composite(_xf(PB[1], 0.60 + 0.40 * e, -110 * (1 - e), 0, alpha=min(1, e * 1.25)))
    out.alpha_composite(_xf(PB[2], 0.90 + 0.10 * e, 0, 0, alpha=e))
    # outgoing shot: its layers fly toward the camera at different speeds (parallax) and fade
    out.alpha_composite(_xf(PA[0], 1 + 0.30 * e, 34 * e, 0, alpha=max(0.0, 1 - ea)))
    out.alpha_composite(_xf(PA[1], 1 + 1.05 * e, 150 * e, 0, alpha=max(0.0, 1 - ea * 1.1)))
    out.alpha_composite(_xf(PA[2], 1 + 0.55 * e, 0, 0, alpha=max(0.0, (1 - e) ** 1.2)))
    arr = np.asarray(out.convert('RGB')).astype(np.float32)
    # light bloom in the middle of the push, tinted by the chapter accent
    amp = math.sin(math.pi * p) ** 1.3
    if amp > 0.01:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        g = np.exp(-(((xx - W / 2) / (W * .55)) ** 2 + ((yy - H * .46) / (H * .32)) ** 2) * 2.0)
        col = np.array(acc, np.float32) * .5 + 128
        arr += g[..., None] * col * amp * 0.42
    return np.clip(arr, 0, 255).astype(np.uint8)


# ───────────────────────────────────────────────────────── fold: origami accordion
def fold(A, B, p, acc=None, N=10):
    _size(A.shape[1], A.shape[0])
    e = _e(p)
    if e < 0.5:
        tex_full = Image.fromarray(A)
        th = (math.pi / 2) * _e(e / 0.5)
    else:
        tex_full = Image.fromarray(B)
        th = (math.pi / 2) * (1 - _e((e - 0.5) / 0.5))
    base = (_np(Image.fromarray(A)) + _np(Image.fromarray(B))) * 0.5 * 0.30 + 10.0
    canvas = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    w = W / N
    xs, zs = [0.0], [0.0]
    for i in range(N):
        s = 1.0 if i % 2 == 0 else -1.0
        phi = s * th
        xs.append(xs[-1] + w * math.cos(phi))
        zs.append(zs[-1] + w * math.sin(phi))
    off = -xs[-1] / 2.0
    L = np.array([-0.45, -0.89])          # light from the camera side, slightly left (x, z)
    strips = []
    for i in range(N):
        x0, x1 = xs[i] + off, xs[i + 1] + off
        z0, z1 = zs[i], zs[i + 1]
        q3 = [(x0, -H / 2, z0), (x1, -H / 2, z1), (x1, H / 2, z1), (x0, H / 2, z0)]
        q2 = [(W / 2 + ZD * x / (ZD + z), H / 2 + ZD * y / (ZD + z)) for x, y, z in q3]
        dx, dz = x1 - x0, z1 - z0
        ln = math.hypot(dx, dz) + 1e-9
        nx, nz = dz / ln, -dx / ln           # normal in the x-z plane
        cx, cz = (x0 + x1) / 2, ZD + (z0 + z1) / 2
        facing = nx * (-cx) + nz * (-cz) > 0
        lam = max(0.0, nx * L[0] + nz * L[1])
        k = (0.65 + 0.35 * lam / 0.89) if facing else 0.50
        sl = tex_full.crop((int(round(i * w)), 0, int(round((i + 1) * w)), H))
        piece = warp_quad(sl, q2)
        if piece is not None:
            strips.append((cz, piece, min(1.0, k)))
    strips.sort(key=lambda t: -t[0])          # far first
    for _, piece, k in strips:
        _paste(canvas, piece, k)
    return np.asarray(canvas.convert('RGB'))


# ───────────────────────────────────────────────────────── shatter: 3D glass shards
_SHARDS = None


def _shard_plan():
    global _SHARDS
    if _SHARDS is not None:
        return _SHARDS
    rng = np.random.default_rng(11)
    R, C = 8, 5
    cw, ch = W / C, H / R
    V = [[None] * (C + 1) for _ in range(R + 1)]
    for r in range(R + 1):
        for c in range(C + 1):
            jx = rng.uniform(-.28, .28) * cw if 0 < c < C else 0.0
            jy = rng.uniform(-.28, .28) * ch if 0 < r < R else 0.0
            V[r][c] = (c * cw + jx, r * ch + jy)
    tris = []
    for r in range(R):
        for c in range(C):
            a, b, cc, d = V[r][c], V[r][c + 1], V[r + 1][c + 1], V[r + 1][c]
            tris += [(a, b, cc), (a, cc, d)]
    I = np.array([W * 0.5, H * 0.56])
    plan = []
    for tri in tris:
        cen = np.mean(np.array(tri), axis=0)
        d = cen - I
        d = d / (np.linalg.norm(d) + 1e-9) + rng.normal(0, .35, 2)
        d = d / (np.linalg.norm(d) + 1e-9)
        m = 0.55 + rng.random() * 0.85
        axis = rng.normal(size=3)
        ang = rng.uniform(-1.7, 1.7)
        zoff = rng.uniform(0.25, 1.1) * ZD * (1.0 if rng.random() < 0.8 else -0.32)
        plan.append((tri, d, m, axis, ang, zoff))
    _SHARDS = plan
    return plan


def shatter(A, B, p, acc=None):
    _size(A.shape[1], A.shape[0])
    e = _e(p)
    Ai = Image.fromarray(A)
    if e <= 0.0:
        return A.copy()
    canvas = Image.fromarray(B).copy()
    L = np.array([-0.4, -0.5, -0.77])
    items = []
    for tri, d, m, axis, ang, zoff in _shard_plan():
        P = np.array([[x - W / 2, y - H / 2, 0.0] for x, y in tri])
        cen = P.mean(0)
        Rm = _rodrigues(axis, ang * e)
        Q = (Rm @ (P - cen).T).T + cen
        dist = e * (0.9 + 0.6 * m) * W
        Q[:, 0] += d[0] * dist
        Q[:, 1] += d[1] * dist
        Q[:, 2] += zoff * e
        z = Q[:, 2] + ZD
        if np.any(z < 0.18 * ZD):
            continue
        dst = [(W / 2 + ZD * x / zz, H / 2 + ZD * y / zz) for (x, y, _), zz in zip(Q, z)]
        n = np.cross(Q[1] - Q[0], Q[2] - Q[0])
        n = n / (np.linalg.norm(n) + 1e-9)
        lam = abs(float(np.dot(n, L)))
        shade = 1.0 - e * (1.0 - (0.62 + 0.38 * lam))
        items.append((float(np.mean(z)), dst, tri, shade))
    items.sort(key=lambda t: -t[0])          # far first
    for _, dst, src, shade in items:
        piece = warp_tri(Ai, dst, src)
        if piece is not None:
            _paste(canvas, piece, shade)
    # glass edge glint, strongest mid-flight
    gl = math.sin(math.pi * e)
    if gl > 0.25:
        dr = ImageDraw.Draw(canvas)
        col = (255, 246, 232)
        for _, dst, _, _ in items[::3]:
            dr.line(dst + [dst[0]], fill=col, width=2)
    return np.asarray(canvas.convert('RGB'))


# ───────────────────────────────────────────────────────── flare: light leak + chroma split
def flare(A, B, p, acc=(255, 201, 60)):
    _size(A.shape[1], A.shape[0])
    mix = _e(p)
    base = A.astype(np.float32) * (1 - mix) + B.astype(np.float32) * mix
    amp = math.sin(math.pi * min(1, max(0, p))) ** 1.5
    cx = -200 + (W + 400) * min(1, max(0, p))
    cy = H * 0.5
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r2 = ((xx - cx) / (W * .45)) ** 2 + ((yy - cy) / (H * .30)) ** 2
    glow = np.exp(-r2 * 2.2)[..., None] * amp * 230.0
    streak = np.exp(-((yy - cy) / 9.0) ** 2)[..., None] * np.exp(-((xx - cx) / (W * .7)) ** 2)[..., None] * amp * 200.0
    col = np.array(acc, np.float32) * .35 + 255 * .65
    # lens ghost on the opposite side
    gx, gy = W - cx, H - cy
    ghost = np.exp(-(((xx - gx) / (W * .18)) ** 2 + ((yy - gy) / (H * .10)) ** 2) * 2.0)[..., None] * amp * 90.0
    out = base + glow * col / 255.0 + streak * col / 255.0 + ghost * col / 255.0
    # chromatic split grows with the flash
    k = int(round(9 * amp))
    if k > 0:
        out[..., 0] = np.roll(out[..., 0], k, axis=1)
        out[..., 2] = np.roll(out[..., 2], -k, axis=1)
    return np.clip(out, 0, 255).astype(np.uint8)
