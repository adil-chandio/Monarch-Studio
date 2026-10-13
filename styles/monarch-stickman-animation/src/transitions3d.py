"""True 3D transitions for AMEER KA KUTTA v6 (no GPU, no bpy).

Each transition is a real perspective projection of planar faces (a rotating box or a hinged page),
textured with the outgoing (A) and incoming (B) full frames and shaded per face.

  cube_h / cube_v : box rotates about the vertical / horizontal axis; A is the front face, B the side face
  page_h          : A is a page hinged on its left spine, turning over to the left; B sits underneath
  Frame-space conventions: camera at the origin looking +z, focal length f == camera distance of the
  front plane, so the front face exactly fills the 720x1280 frame at rest.
"""
import math
import numpy as np
from PIL import Image, ImageFilter

W, H = 1080, 1920        # default; overwritten per call from the input frame (see _size)
ZD = 1.55 * W            # camera distance to the front plane (in px)
BG = np.array([9, 7, 12], np.float32)


def _e(p):
    """smoothstep ease (0..1 -> 0..1). Peak speed 1.5x average (cubic was 3x), so brightness swaps stay under the cut cap."""
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def _rot(axis, th):
    c, s = math.cos(th), math.sin(th)
    if axis == 'y':   # about vertical axis: x-z plane
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float64)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float64)   # about horizontal axis: y-z plane


def _project(P, zc, zd=None):
    """P: (4,3) box-space points -> (4,2) screen px. zc: z of the box centre in camera space."""
    f = ZD if zd is None else zd
    z = P[:, 2] + zc
    u = W / 2 + f * P[:, 0] / z
    v = H / 2 + f * P[:, 1] / z
    return np.stack([u, v], 1), z


def _coeffs(dst, src):
    """PIL PERSPECTIVE coefficients: output pixel (x,y) -> source (sx,sy); dst quad -> src rect."""
    A = []
    b = []
    for (x, y), (sx, sy) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -sx * x, -sx * y])
        b.append(sx)
        A.append([0, 0, 0, x, y, 1, -sy * x, -sy * y])
        b.append(sy)
    k = np.linalg.solve(np.array(A, np.float64), np.array(b, np.float64))
    return tuple(k.tolist())


def _face(tex_img, quad2d):
    """warp a full-frame RGB texture onto quad2d (TL, TR, BR, BL order). returns RGBA (W,H)."""
    src = [(0, 0), (W, 0), (W, H), (0, H)]
    rgba = Image.fromarray(tex_img).convert('RGBA')
    rgba.putalpha(255)
    co = _coeffs([tuple(p) for p in quad2d], src)
    return rgba.transform((W, H), Image.PERSPECTIVE, co, Image.BICUBIC)


def _shade(img_rgba, k):
    a = np.asarray(img_rgba).astype(np.float32)
    a[..., :3] *= k
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def _composite(base_rgb, layers):
    out = Image.fromarray(base_rgb.astype(np.uint8)).convert('RGBA')
    for L in layers:
        out.alpha_composite(L)
    return np.asarray(out.convert('RGB')).astype(np.float32)


def _visible(normal, centre):
    """face is visible when its outward normal points at the camera (origin)."""
    return np.dot(normal, -centre) > 0


def _size(A):
    """frame size comes from the input (kutta2 renders 1080x1920); keeps the module constants in sync."""
    global W, H, ZD
    H, W = A.shape[:2]
    ZD = 1.55 * W


def cube(A, B, p, axis='y', flip=False):
    """rotating box. p in 0..1 (eased inside). flip=True turns the other way (B from the other side)."""
    _size(A)
    e = _e(p)
    sign = (-1 if axis == 'x' else 1) * (-1 if flip else 1)   # the bottom face swings up into view
    th = (math.pi / 2) * e * sign
    a = W / 2.0
    b = H / 2.0
    c = W / 2.0 if axis == 'y' else H / 2.0
    zc = ZD + c                                  # box centre in camera space
    R = _rot(axis, th)
    # side face is at +x (axis y) or +y (axis x)
    if axis == 'y':
        front = np.array([[-a, -b, -c], [a, -b, -c], [a, b, -c], [-a, b, -c]], np.float64)
        side = np.array([[a, -b, -c], [a, -b, c], [a, b, c], [a, b, -c]], np.float64)
        nf, ns = np.array([0, 0, -1.0]), np.array([1.0, 0, 0])
    else:
        front = np.array([[-a, -b, -c], [a, -b, -c], [a, b, -c], [-a, b, -c]], np.float64)
        side = np.array([[-a, b, -c], [a, b, -c], [a, b, c], [-a, b, c]], np.float64)   # bottom face
        nf, ns = np.array([0, 0, -1.0]), np.array([0, 1.0, 0])
    # front/side texture corners: TL, TR, BR, BL of the image
    faces = [(front, nf, A, 1.0), (side, ns, B, 1.0)]
    layers = []
    for pts, n, tex, _ in faces:
        Rp = (R @ pts.T).T
        Rn = R @ n
        centre = Rp.mean(0) + np.array([0, 0, zc])
        if not _visible(Rn, centre):
            continue
        q2, z = _project(Rp, zc)
        if np.any(z <= 1):
            continue
        # light from the upper left; faces turn darker as they leave the viewer
        # shading ramps with the turn so the first/last frames match the still shots exactly:
        # outgoing front face is 1.0 at rest and darkens as it turns away; incoming face brightens to 1.0.
        if np.allclose(n, nf):
            k = 1.0 - 0.30 * e if tex is A else 1.0
        else:
            k = 0.70 + 0.30 * e if tex is B else 0.70
        layers.append((centre[2], _shade(_face(tex.astype(np.uint8), q2), k)))
    layers.sort(key=lambda t: -t[0])          # far first
    # background: blurred, darkened copy of the frame underneath (no black slivers at the edges)
    under = Image.fromarray((A if e < .5 else B).astype(np.uint8)).filter(ImageFilter.GaussianBlur(28))
    base = np.asarray(under).astype(np.float32) * 0.60 + 24.0      # lifted floor: never a black sliver
    return np.clip(_composite(base, [L for _, L in layers]), 0, 255).astype(np.uint8)


def page(A, B, p, flip=False):
    """A is a page hinged on its left spine; it turns over to the left and reveals B underneath."""
    _size(A)
    e = _e(p)
    phi = math.pi * e
    a = W / 2.0
    b = H / 2.0
    zc = ZD
    hinge_x = -a
    # page corners in box space (z = 0 plane at the front), hinge on the left edge
    TLc = [-a, -b, 0.0]
    BLc = [-a, b, 0.0]
    TRc = [a, -b, 0.0]
    BRc = [a, b, 0.0]
    pts = np.array([TLc, TRc, BRc, BLc], np.float64)
    rel = pts.copy()
    rel[:, 0] -= hinge_x
    rot = np.zeros_like(rel)
    rot[:, 0] = rel[:, 0] * math.cos(phi)
    rot[:, 2] = -rel[:, 0] * math.sin(phi)      # lifts toward the viewer (smaller z)
    rot[:, 0] += hinge_x
    rot[:, 1] = rel[:, 1]
    # bring the page slightly in front of the revealed page underneath
    rot[:, 2] -= 2.0
    PAGE_ZD = 2.7 * W      # longer lens for the page: mild perspective, no fan
    zc = PAGE_ZD
    q2, z = _project(rot, zc, PAGE_ZD)
    base = B.astype(np.float32)
    # background shadow of the lifting page on the revealed frame
    shadow_k = 0.55 + 0.45 * (1 - math.sin(phi))
    base = base * (0.72 + 0.28 * shadow_k)
    if np.any(z <= 1):
        return np.clip(base, 0, 255).astype(np.uint8)
    back = phi > math.pi / 2
    tex = A[:, ::-1] if back else A       # back of the page is the mirrored texture
    k = (0.55 if back else 1.0) * (0.86 + 0.14 * math.cos(phi))
    layer = _shade(_face(np.ascontiguousarray(tex).astype(np.uint8), q2), k)
    out = _composite(base, [layer])
    return np.clip(out, 0, 255).astype(np.uint8)


def cube_h(A, B, p, acc=None):
    return cube(A, B, p, axis='y')


def cube_v(A, B, p, acc=None):
    return cube(A, B, p, axis='x')


def page_h(A, B, p, acc=None):
    return page(A, B, p)
