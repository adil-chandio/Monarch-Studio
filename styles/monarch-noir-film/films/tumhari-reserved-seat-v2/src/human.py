#!/usr/bin/env python3
"""
human.py — WF-03 · Monarch Noir Film — NOIRGO MAX human-like hero rig (2026-10-10)

A line-and-fill human figure (not a stick figure): 3-D skeleton (WF-01 toon._skeleton, re-proportioned to a
~6.7-head adult), numeric IK for the hands, five-finger hands with pose presets, a real face (brows, lidded eyes with
iris/pupil/highlight and gaze, nose, mouth with open/smile), messy hair, ears, a hoodie with drawstrings that lag the
head, joggers and sneakers, two-tone shading toward the scene's practical light, breathing, blinks and weight shift.

Coordinates: everything is in SS (supersampled) pixels like noir.py. `draw_human()` paints into an RGBA layer and
returns the projected joints so shots can attach props (phone, mug, keys) to the hands.
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
import toon as T  # noqa: E402  (3-D skeleton + capsule helper from the WF-01 engine)

# ─────────────────────────────────────────────── proportions (fractions of standing height)
HP = dict(
    foot=0.000, ankle=0.050, knee=0.265, hip=0.500,
    shoulder=0.800, neck=0.840, head_b=0.860, head_c=0.925, head_top=1.000,
    head_rx=0.060, head_ry=0.074,
    sh_w=0.112, hip_w=0.064,
    arm_u=0.170, arm_l=0.150,
    leg_u=0.235, leg_l=0.215,
    arm_r0=0.030, arm_r1=0.023, leg_r0=0.042, leg_r1=0.028,
    hand_r=0.030, shoe_l=0.090, shoe_h=0.032,
)
HAND_L = 0.085      # wrist → fingertip (fraction of height)

BONE = (236, 232, 222)
SLATE = (96, 102, 112)
INK = (3, 3, 4)
HOODIE = (58, 62, 70)        # dark side of the hoodie
HOODIE_LIT = (150, 154, 160)  # lit side of the hoodie (grey marl)
PANTS = (34, 36, 42)
PANTS_LIT = (92, 94, 102)
SKIN = (222, 206, 188)
SKIN_DK = (120, 104, 94)
HAIR = (26, 24, 26)
HAIR_LIT = (74, 70, 72)
SHOE = (230, 228, 222)
SHOE_DK = (110, 108, 104)
SILH = (10, 10, 12)

# ─────────────────────────────────────────────── expressions
# lids: eye openness (1 = neutral), brow_h: brow raise (+up), brow_in: inner-brow angle (+ = inner ends UP = worry,
# − = inner ends DOWN = anger/focus), smile: corner lift (−1..1), open: mouth opening 0..1, squint: lower-lid rise.
EXPR = {
    'neutral': dict(lids=1.00, brow_h=0.00, brow_in=0.00, smile=0.00, open=0.00, squint=0.0),
    'tired':   dict(lids=0.62, brow_h=-0.05, brow_in=0.10, smile=-0.18, open=0.00, squint=0.1),
    'envy':    dict(lids=0.78, brow_h=-0.08, brow_in=0.22, smile=-0.28, open=0.00, squint=0.25),
    'doubt':   dict(lids=0.88, brow_h=0.10, brow_in=0.35, smile=-0.22, open=0.08, squint=0.0),
    'shock':   dict(lids=1.30, brow_h=0.40, brow_in=0.15, smile=-0.05, open=0.55, squint=0.0),
    'resolve': dict(lids=0.84, brow_h=-0.12, brow_in=-0.30, smile=0.02, open=0.00, squint=0.30),
    'calm':    dict(lids=0.86, brow_h=0.02, brow_in=0.05, smile=0.22, open=0.00, squint=0.05),
    'smile':   dict(lids=0.80, brow_h=0.08, brow_in=0.05, smile=0.60, open=0.12, squint=0.25),
    'pain':    dict(lids=0.35, brow_h=0.05, brow_in=0.45, smile=-0.45, open=0.25, squint=0.5),
    'focus':   dict(lids=0.80, brow_h=-0.10, brow_in=-0.18, smile=-0.05, open=0.00, squint=0.35),
}


def expr_mix(a, b, t):
    ea, eb = EXPR[a], EXPR[b]
    return {k: ea[k] + (eb[k] - ea[k]) * t for k in ea}


# ─────────────────────────────────────────────── motion helpers
def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def ease_q(t):
    t = min(1.0, max(0.0, t))
    return 1 - (1 - t) ** 5 if t > 0.5 else 16 * t ** 5


def anticipate(t, back=0.12):
    """0→1 with a small reverse move first (the body loads before it goes)."""
    t = min(1.0, max(0.0, t))
    if t < 0.2:
        return -back * math.sin(t / 0.2 * math.pi / 2)
    u = (t - 0.2) / 0.8
    return ease(u) * (1 + back * 0.0)


def settle(t, over=0.08, w=14.0, damp=5.0):
    """0→1 with overshoot and damped return."""
    t = min(1.0, max(0.0, t))
    if t <= 0:
        return 0.0
    return 1 + (-math.exp(-damp * t) * math.cos(w * t)) * over * 4 * (1 - t) if t < 1 else 1.0


def blink(t, seed=3, period=(3.1, 5.4), dur=0.14):
    """1 = fully closed at this instant (deterministic schedule from the seed)."""
    rng = np.random.default_rng(seed)
    tt = 0.6 + rng.random() * 2.0
    while tt < t + 1:
        if tt <= t <= tt + dur:
            u = (t - tt) / dur
            return math.sin(u * math.pi) ** 0.7
        # occasional double blink
        if rng.random() < 0.18 and tt + 0.26 <= t <= tt + 0.26 + dur:
            u = (t - tt - 0.26) / dur
            return math.sin(u * math.pi) ** 0.7
        tt += period[0] + rng.random() * (period[1] - period[0])
    return 0.0


def breathe(t, rate=0.23):
    return math.sin(2 * math.pi * rate * t)


def walk_pose(phase, stride=34.0, lean=4.0, arm=0.75):
    """One walking step cycle. phase 0..1 (0 = left foot contact). Returns pose dict."""
    w = 2 * math.pi * phase
    lz_l = stride * math.sin(w)
    lz_r = stride * math.sin(w + math.pi)
    kl = max(0.0, 46 * math.sin(w + 0.9)) if math.sin(w) > -0.3 else 8
    kr = max(0.0, 46 * math.sin(w + math.pi + 0.9)) if math.sin(w + math.pi) > -0.3 else 8
    return dict(lz_l=lz_l, lz_r=lz_r, kl=kl, kr=kr,
                az_l=-stride * 0.55 * arm * math.sin(w), az_r=-stride * 0.55 * arm * math.sin(w + math.pi),
                ef_l=22 + 12 * max(0, -math.sin(w)), ef_r=22 + 12 * max(0, -math.sin(w + math.pi)),
                lean=lean, sway=0.012 * math.sin(w), bob=0.016 * abs(math.sin(w)),
                head=-1.2 * math.sin(w), tilt=2.0 * math.sin(w))


def run_pose(phase, stride=58.0, lean=12.0):
    w = 2 * math.pi * phase
    p = walk_pose(phase, stride=stride, lean=lean, arm=1.0)
    p['kl'] = max(0.0, 85 * math.sin(w + 1.1)) + 10
    p['kr'] = max(0.0, 85 * math.sin(w + math.pi + 1.1)) + 10
    p['ef_l'] = 70 + 10 * math.sin(w)
    p['ef_r'] = 70 - 10 * math.sin(w)
    p['al'] = -8
    p['ar'] = 8
    p['bob'] = 0.03 * abs(math.sin(w))
    return p


# ─────────────────────────────────────────────── skeleton solve + IK
def solve(x, y, s, pose, flip=False, rot=0.0, anchor='feet'):
    """Project the 3-D skeleton. (x, y) = feet centre on the ground (anchor='feet') or hip (anchor='hip').
    rot = roll of the whole figure in the picture plane (deg, for lying down). Returns K, J, KS."""
    sgn = -1 if flip else 1
    saved = T.P
    T.P = HP
    try:
        K = T._skeleton(pose, s, sgn)
    finally:
        T.P = saved
    Fl = 4.2 * s
    ox, oy = x, y - HP['hip'] * s

    def PR(v):
        k = Fl / (Fl - v[2])
        return (ox + v[0] * k, oy + v[1] * k), k

    J, KS = {}, {}
    for key, v in K.items():
        if isinstance(v, tuple) and len(v) == 3:
            J[key], KS[key] = PR(v)
        else:
            J[key] = v
    if anchor == 'feet':
        sole = max(J['ftl'][1] + HP['ankle'] * s * KS['ftl'], J['ftr'][1] + HP['ankle'] * s * KS['ftr'])
        dy = y - sole - pose.get('bob', 0.0) * s
    else:
        dy = y - J['hipc'][1]
    for key in list(J):
        if isinstance(J[key], tuple) and len(J[key]) == 2:
            J[key] = (J[key][0], J[key][1] + dy)
    if abs(rot) > 1e-6:
        c = J['hipc'] if anchor == 'hip' else (x, y)
        ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        for key in list(J):
            v = J[key]
            if isinstance(v, tuple) and len(v) == 2:
                dx, dy2 = v[0] - c[0], v[1] - c[1]
                J[key] = (c[0] + dx * ca - dy2 * sa, c[1] + dx * sa + dy2 * ca)
        K['rot'] = math.radians(rot)
    return K, J, KS


def reach(pose, side, target, x, y, s, flip=False, rot=0.0, anchor='feet', iters=30):
    """Numeric IK: adjust abduction / swing / elbow flex of one arm so the wrist lands on `target` (SS px).
    side 'l' | 'r'. Returns the modified pose (copy)."""
    p = dict(pose)
    ka, kz, ke = ('al', 'az_l', 'ef_l') if side == 'l' else ('ar', 'az_r', 'ef_r')
    hand = 'hal' if side == 'l' else 'har'
    p.setdefault(ka, -14 if side == 'l' else 14)
    p.setdefault(kz, 0.0)
    p.setdefault(ke, 8.0)

    def err(q):
        _, J, _ = solve(x, y, s, q, flip, rot, anchor)
        return (J[hand][0] - target[0]) ** 2 + (J[hand][1] - target[1]) ** 2

    step = {ka: 18.0, kz: 18.0, ke: 22.0}
    e0 = err(p)
    for _ in range(iters):
        improved = False
        for k in (ka, kz, ke):
            for d in (step[k], -step[k]):
                q = dict(p)
                q[k] = p[k] + d
                if k == ke:
                    q[k] = max(0.0, min(150.0, q[k]))
                if k in ('az_l', 'az_r'):
                    q[k] = max(-80.0, min(80.0, q[k]))
                e = err(q)
                if e < e0 - 1e-3:
                    p, e0, improved = q, e, True
                    break
        if not improved:
            for k in step:
                step[k] *= 0.5
            if max(step.values()) < 0.4:
                break
    return p


# ─────────────────────────────────────────────── drawing primitives
def _capsule(a, b, r0, r1):
    return T._capsule(a, b, r0, r1, segs=12)


def _ellipse(c, rx, ry, ang=0.0, segs=44):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(c[0] + ca * rx * math.cos(t) - sa * ry * math.sin(t),
             c[1] + sa * rx * math.cos(t) + ca * ry * math.sin(t))
            for t in np.linspace(0, 2 * math.pi, segs, endpoint=False)]


def _two_tone(layer, poly, light, r, dark, lit, blur=0.18, shift=0.55):
    """Fill `poly` with `dark`, then the same shape shifted toward the light clipped inside → lit half."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    bbox = [int(min(xs)) - 4, int(min(ys)) - 4, int(max(xs)) + 5, int(max(ys)) + 5]
    bbox = [max(0, bbox[0]), max(0, bbox[1]), min(layer.width, bbox[2]), min(layer.height, bbox[3])]
    if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
        return
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    mid = (sum(xs) / len(xs), sum(ys) / len(ys))
    if light is None:
        off = (0.0, 0.0)
        la_const = 0.5
    else:
        lv = np.array([light[0] - mid[0], light[1] - mid[1]], np.float32)
        lv /= (np.linalg.norm(lv) + 1e-6)
        off = (lv[0] * r * shift, lv[1] * r * shift)
        la_const = None
    m = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(m).polygon([(p[0] - bbox[0], p[1] - bbox[1]) for p in poly], fill=255)
    ma = np.asarray(m, np.float32) / 255
    if la_const is None:
        lm = Image.new('L', (bw, bh), 0)
        ImageDraw.Draw(lm).polygon([(p[0] - bbox[0] + off[0], p[1] - bbox[1] + off[1]) for p in poly], fill=255)
        lm = lm.filter(ImageFilter.GaussianBlur(max(0.5, r * blur)))
        la = np.asarray(lm, np.float32) / 255
    else:
        la = np.full((bh, bw), la_const, np.float32)
    col = np.array(dark, np.float32)[None, None, :] * (1 - la[..., None]) + np.array(lit, np.float32)[None, None, :] * la[..., None]
    tile = Image.fromarray(np.concatenate([col.clip(0, 255).astype(np.uint8), (ma * 255).astype(np.uint8)[..., None]], 2), 'RGBA')
    layer.alpha_composite(tile, dest=(bbox[0], bbox[1]))


def _flat(layer, poly, col):
    ImageDraw.Draw(layer).polygon(poly, fill=col + (255,))


# ─────────────────────────────────────────────── hands
FINGER = [  # (base offset across palm −1..1, length factor)
    (-0.75, 0.86), (-0.25, 1.00), (0.25, 0.94), (0.75, 0.78)]
HAND_POSES = {
    # curl of proximal / distal joints in degrees per finger group, thumb (abd, curl), spread
    'relax': dict(curl=(20, 26), thumb=(30, 18), spread=0.5),
    'open':  dict(curl=(4, 6), thumb=(55, 5), spread=1.15),
    'flat':  dict(curl=(0, 0), thumb=(60, 0), spread=1.0),
    'fist':  dict(curl=(92, 96), thumb=(20, 70), spread=0.7),
    'point': dict(curl=(88, 92), thumb=(25, 60), spread=0.7, index=(6, 4)),
    'grip':  dict(curl=(62, 70), thumb=(-10, 40), spread=0.75),
    'hold':  dict(curl=(45, 55), thumb=(10, 35), spread=0.8),
}


def draw_hand(layer, wrist, fwd, s, pose='relax', light=None, k=1.0, skin=(SKIN_DK, SKIN), flip=False,
              roll=0.0, silhouette=False, ink=True):
    """fwd: unit vector wrist→fingers. k: perspective factor. Draws palm + 5 fingers (two segments each).
    Returns the fingertip point of the index finger (for props)."""
    hp = HAND_POSES[pose]
    fx, fy = fwd
    if abs(roll) > 1e-6:
        ca, sa = math.cos(roll), math.sin(roll)
        fx, fy = fx * ca - fy * sa, fx * sa + fy * ca
    nx, ny = -fy, fx                       # across the palm
    if flip:
        nx, ny = -nx, -ny
    L = HAND_L * s * k
    pw = 0.27 * L                          # half palm width
    pl = 0.50 * L                          # palm length
    palm = [(wrist[0] + nx * pw * 0.78, wrist[1] + ny * pw * 0.78),
            (wrist[0] + fx * pl + nx * pw, wrist[1] + fy * pl + ny * pw),
            (wrist[0] + fx * pl * 1.02 + nx * pw * 0.35, wrist[1] + fy * pl * 1.02 + ny * pw * 0.35),
            (wrist[0] + fx * pl * 1.02 - nx * pw * 0.35, wrist[1] + fy * pl * 1.02 - ny * pw * 0.35),
            (wrist[0] + fx * pl - nx * pw, wrist[1] + fy * pl - ny * pw),
            (wrist[0] - nx * pw * 0.78, wrist[1] - ny * pw * 0.78)]
    dk, lt = skin
    r_f = 0.052 * L
    ow = max(1.0, L * 0.03)
    if silhouette:
        _flat(layer, palm, SILH)
    else:
        if ink:
            _flat(layer, T._grow(palm, ow), INK)
        _two_tone(layer, palm, light, pw, dk, lt, blur=0.3)
    tip = None
    base_dir = math.atan2(fy, fx)
    for i, (off, lf) in enumerate(FINGER):
        c0, c1 = hp['curl']
        if i == 0 and 'index' in hp:
            c0, c1 = hp['index']
        spread = hp['spread'] * off * 0.26
        a0 = base_dir + spread * (-1 if flip else 1)
        # curl bends toward the palm side (toward −n if not flipped)
        side = -1 if not flip else 1
        a1 = a0 + math.radians(c0) * side
        a2 = a1 + math.radians(c1) * side
        l1, l2 = 0.29 * L * lf, 0.22 * L * lf
        b = (wrist[0] + fx * pl + nx * pw * off * 0.9, wrist[1] + fy * pl + ny * pw * off * 0.9)
        m = (b[0] + math.cos(a1) * l1, b[1] + math.sin(a1) * l1)
        e = (m[0] + math.cos(a2) * l2, m[1] + math.sin(a2) * l2)
        for (p, q, r0, r1) in ((b, m, r_f * 1.05, r_f * 0.95), (m, e, r_f * 0.95, r_f * 0.78)):
            poly = _capsule(p, q, r0, r1)
            if silhouette:
                _flat(layer, poly, SILH)
            else:
                if ink:
                    _flat(layer, T._grow(poly, ow), INK)
                _two_tone(layer, poly, light, r0, dk, lt, blur=0.3)
        if i == 0:
            tip = e
    # thumb: from the palm root on the n side, abducted away then curled
    ta, tc = hp['thumb']
    side = 1 if not flip else -1
    root = (wrist[0] + fx * pl * 0.25 + nx * pw * 0.95 * side, wrist[1] + fy * pl * 0.25 + ny * pw * 0.95 * side)
    a1 = base_dir + math.radians(ta) * side
    a2 = a1 - math.radians(tc) * side
    l1, l2 = 0.26 * L, 0.20 * L
    m = (root[0] + math.cos(a1) * l1, root[1] + math.sin(a1) * l1)
    e = (m[0] + math.cos(a2) * l2, m[1] + math.sin(a2) * l2)
    for (p, q, r0, r1) in ((root, m, r_f * 1.15, r_f * 1.0), (m, e, r_f * 1.0, r_f * 0.8)):
        poly = _capsule(p, q, r0, r1)
        if silhouette:
            _flat(layer, poly, SILH)
        else:
            if ink:
                _flat(layer, T._grow(poly, ow), INK)
            _two_tone(layer, poly, light, r0, dk, lt, blur=0.3)
    return tip


# ─────────────────────────────────────────────── face
def draw_face(layer, c, rx, ry, ang, yaw_deg, light, expr, look=(0.0, 0.0), blink_v=0.0, silhouette=False,
              hair=True, ink_w=None):
    """c: head centre; rx, ry: head radii (SS px); ang: head roll; yaw_deg: head yaw (−180..180, 0 = facing camera)."""
    d = ImageDraw.Draw(layer)
    E = expr
    yaw = math.radians(yaw_deg)
    face_vis = math.cos(yaw)                   # 1 front, 0 profile, <0 back of head
    ca, sa = math.cos(ang), math.sin(ang)

    def R(dx, dy):                              # head-local → canvas
        return (c[0] + dx * ca - dy * sa, c[1] + dx * sa + dy * ca)

    lw = ink_w or max(2, int(rx * 0.075))
    fx = math.sin(yaw) * rx * 0.62              # features slide with the yaw
    # ── hair (always: a messy cap, fringe toward the face side)
    if hair:
        pts = []
        n = 26
        for i in range(n + 1):
            t = -math.pi * 1.02 + i / n * math.pi * 1.04      # over the top
            r_ = 1.08 + 0.05 * math.sin(i * 2.3) + 0.03 * math.cos(i * 5.1)
            pts.append(R(math.cos(t) * rx * r_ * 1.0, math.sin(t) * ry * r_))
        # fringe: comes down over the forehead on the face side
        pts.append(R(rx * 1.05, -ry * 0.05))
        pts.append(R(rx * 0.85 + fx * 0.2, -ry * 0.42))
        pts.append(R(rx * 0.45 + fx * 0.3, -ry * 0.58))
        pts.append(R(fx * 0.3, -ry * 0.50))
        pts.append(R(-rx * 0.5 + fx * 0.3, -ry * 0.62))
        pts.append(R(-rx * 1.05, -ry * 0.1))
        if silhouette:
            _flat(layer, pts, SILH)
        else:
            _two_tone(layer, pts, light, rx, HAIR, HAIR_LIT, blur=0.25, shift=0.45)
    if silhouette or face_vis < 0.12:
        return
    a = min(1.0, (face_vis - 0.12) / 0.5)      # feature alpha near profile
    col = INK + (int(255 * a),)
    # ── ears
    for sgn_ in (-1, 1):
        ex = sgn_ * rx * 0.98 + fx * 0.35
        if abs(ex) < rx * 1.02:
            d.polygon(_ellipse(R(ex, ry * 0.05), rx * 0.14, ry * 0.2, ang), fill=SKIN_DK + (255,))
    # ── eyes
    eye_dx = rx * 0.40
    eye_y = -ry * 0.02
    ew, eh = rx * 0.24, ry * 0.13 * E['lids'] * (1 - blink_v)
    for sgn_ in (-1, 1):
        ex = fx * 0.9 + sgn_ * eye_dx * (1 - 0.18 * abs(math.sin(yaw)))
        # occluded eye near profile
        if (sgn_ * math.sin(yaw)) > 0.72:
            continue
        cx, cy = ex, eye_y
        if eh > 1.5:
            # almond: upper lid arc + lower lid arc
            up = [R(cx + ew * math.cos(t), cy - eh * math.sin(t) * 1.0) for t in np.linspace(0, math.pi, 14)]
            lo = [R(cx + ew * math.cos(t), cy - eh * math.sin(t) * (0.75 - 0.45 * E['squint'])) for t in np.linspace(math.pi, 2 * math.pi, 14)]
            eye_poly = up + lo
            # white (bone) of the eye, then iris clipped by the almond
            m = Image.new('L', layer.size, 0)
            ImageDraw.Draw(m).polygon(eye_poly, fill=255)
            bbox = m.getbbox()
            if bbox:
                tile = Image.new('RGBA', layer.size, (0, 0, 0, 0))
                td = ImageDraw.Draw(tile)
                td.polygon(eye_poly, fill=(228, 226, 222, 255))
                ir = ry * 0.105
                ix = cx + look[0] * ew * 0.45 + math.sin(yaw) * ew * 0.25
                iy = cy + look[1] * eh * 0.5
                td.ellipse([R(ix, iy)[0] - ir, R(ix, iy)[1] - ir, R(ix, iy)[0] + ir, R(ix, iy)[1] + ir], fill=(38, 40, 46, 255))
                pr = ir * 0.5
                td.ellipse([R(ix, iy)[0] - pr, R(ix, iy)[1] - pr, R(ix, iy)[0] + pr, R(ix, iy)[1] + pr], fill=INK + (255,))
                # highlight toward the light
                if light is not None:
                    lv = np.array([light[0] - c[0], light[1] - c[1]], np.float32)
                    lv /= (np.linalg.norm(lv) + 1e-6)
                else:
                    lv = np.array([-0.5, -0.6], np.float32)
                hx, hy = R(ix, iy)[0] + lv[0] * ir * 0.45, R(ix, iy)[1] + lv[1] * ir * 0.45
                hr = max(1.0, ir * 0.22)
                td.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=(250, 250, 248, 255))
                tile.putalpha(Image.fromarray(np.minimum(np.asarray(m), np.asarray(tile.split()[3]))))
                layer.alpha_composite(tile)
            # upper lid line (the eye's weight)
            d.line(up, fill=col, width=lw)
            # lower lid: thin
            d.line(lo[2:-2], fill=INK + (int(140 * a),), width=max(1, lw // 2))
        else:
            # closed: a single curved line
            d.line([R(cx + ew * math.cos(t), cy + ry * 0.02 * math.sin(t)) for t in np.linspace(0, math.pi, 10)], fill=col, width=lw)
        # ── brow
        by = eye_y - ry * (0.30 + 0.09 * E['brow_h'])
        inner = -sgn_ * ew * 1.05
        outer = sgn_ * ew * 1.15
        bi = by - ry * 0.10 * E['brow_in']           # inner end up when brow_in > 0
        bo = by + ry * 0.04 * max(0.0, E['brow_in'])
        d.line([R(cx + inner, bi), R(cx + inner * 0.2, by - ry * 0.02), R(cx + outer, bo)], fill=col, width=int(lw * 1.5), joint='curve')
    # ── nose: small hook on the face side
    nx0 = fx * 1.05
    d.line([R(nx0 - rx * 0.04, ry * 0.06), R(nx0 + rx * 0.02, ry * 0.30), R(nx0 - rx * 0.09, ry * 0.33)], fill=INK + (int(170 * a),), width=max(1, int(lw * 0.8)), joint='curve')
    # ── mouth
    my = ry * 0.56
    mw = rx * 0.36
    smile = E['smile']
    opn = E['open']
    mx = fx * 1.1
    pts = [R(mx - mw, my - ry * 0.05 * smile), R(mx, my + ry * 0.05 * smile), R(mx + mw, my - ry * 0.05 * smile)]
    if opn > 0.04:
        lower = [R(mx + mw, my - ry * 0.05 * smile), R(mx, my + ry * (0.05 * smile + 0.22 * opn)), R(mx - mw, my - ry * 0.05 * smile)]
        d.polygon(pts + lower, fill=(28, 22, 24, int(255 * a)))
        d.line(pts, fill=col, width=max(1, int(lw * 0.9)), joint='curve')
    else:
        d.line(pts, fill=col, width=max(1, int(lw * 0.9)), joint='curve')


# ─────────────────────────────────────────────── the figure
def _parts(J, KS, s):
    """(depth, name, geom) far → near. Clothing: hoodie torso+sleeves, joggers, sneakers."""
    P = []
    au0, au1 = HP['arm_r0'] * s * 1.10, HP['arm_r1'] * s * 1.02
    lu0, lu1 = HP['leg_r0'] * s * 1.02, HP['leg_r1'] * s * 1.05
    for a, b, r0, r1, nm in (('shl', 'ell', au0, au1, 'arm'), ('ell', 'hal', au1, au1 * 0.92, 'fore'),
                             ('shr', 'elr', au0, au1, 'arm'), ('elr', 'har', au1, au1 * 0.92, 'fore'),
                             ('hpl', 'knl', lu0, lu1, 'thigh'), ('knl', 'ftl', lu1, lu1 * 0.9, 'shin'),
                             ('hpr', 'knr', lu0, lu1, 'thigh'), ('knr', 'ftr', lu1, lu1 * 0.9, 'shin')):
        P.append(((KS[a] + KS[b]) / 2, nm, (J[a], J[b], r0 * KS[a], r1 * KS[b])))
    P.append((KS['hipc'] + 0.001, 'torso', (J['hipc'], J['shoc'], HP['hip_w'] * s * 1.25, HP['sh_w'] * s * 0.98)))
    P.append((KS['nek'] + 0.002, 'neck', (J['shoc'], J['nek'], HP['arm_r0'] * s * 0.95, HP['arm_r0'] * s * 0.85)))
    P.sort(key=lambda p: p[0])
    return P


def draw_human(layer, x, y, s, pose, light, expr='neutral', look=(0.0, 0.0), blink_v=0.0,
               hand_l='relax', hand_r='relax', flip=False, rot=0.0, anchor='feet', silhouette=False,
               string_sway=0.0, hair=True, shoes=True, hood_up=False, palette=None, ink=True):
    """Paint the hero into `layer` (RGBA, SS px). Returns (J, KS, extras) — extras has hand tips etc."""
    K, J, KS = solve(x, y, s, pose, flip, rot, anchor)
    pal = dict(hood=(HOODIE, HOODIE_LIT), pants=(PANTS, PANTS_LIT), skin=(SKIN_DK, SKIN), shoe=(SHOE_DK, SHOE))
    if palette:
        pal.update(palette)
    E = EXPR[expr] if isinstance(expr, str) else expr
    parts = _parts(J, KS, s)
    sgn = -1 if flip else 1
    yaw_deg = math.degrees(K.get('yaw', 0.0)) + pose.get('head_t', 0.0) * sgn
    head_ang = K.get('hd_a', 0.0) + K.get('rot', 0.0)
    hrx = HP['head_rx'] * s * KS['hctr']
    hry = HP['head_ry'] * s * KS['hctr']
    head_depth = KS['hctr'] + 0.003
    extras = {}

    ow = max(1.5, s * 0.0045)

    def paint(poly, r, dark, lit):
        if silhouette:
            _flat(layer, poly, SILH)
        else:
            if ink:
                _flat(layer, T._grow(poly, ow), INK)
            _two_tone(layer, poly, light, r, dark, lit)

    drawn_head = False
    for depth, nm, g in parts + [(head_depth, 'head', None)]:
        if nm == 'head':
            # neck already; head ellipse
            poly = _ellipse(J['hctr'], hrx, hry * 1.02, head_ang)
            paint(poly, (hrx + hry) / 2, *pal['skin'])
            draw_face(layer, J['hctr'], hrx, hry, head_ang, yaw_deg, light, E, look, blink_v, silhouette, hair)
            if hood_up:
                hood = _ellipse((J['hctr'][0], J['hctr'][1] - hry * 0.1), hrx * 1.35, hry * 1.3, head_ang)
                paint(hood, hrx, *pal['hood'])
                # face opening
                face = _ellipse((J['hctr'][0] + math.sin(math.radians(yaw_deg)) * hrx * 0.2, J['hctr'][1] + hry * 0.05), hrx * 0.95, hry * 0.98, head_ang)
                paint(face, hrx, *pal['skin'])
                draw_face(layer, J['hctr'], hrx, hry, head_ang, yaw_deg, light, E, look, blink_v, silhouette, hair=False)
            drawn_head = True
            continue
        a, b, r0, r1 = g
        if nm == 'torso':
            # hoodie body: wider at the chest, with a hem line at the hip
            poly = _capsule(a, b, r0, r1)
            paint(poly, (r0 + r1) / 2, *pal['hood'])
            # hood bunched behind the neck
            nek = J['nek']
            bun = _ellipse((nek[0] - math.sin(math.radians(yaw_deg)) * hrx * 0.3, nek[1] + hry * 0.25), hrx * 1.05, hry * 0.42, head_ang)
            paint(bun, hrx * 0.6, *pal['hood'])
            # kangaroo pocket (ink line) + drawstrings
            if not silhouette and ink:
                d = ImageDraw.Draw(layer)
                hip = J['hipc']
                w = r0 * 1.1
                d.line([(hip[0] - w, hip[1] - s * 0.06), (hip[0] - w * 0.9, hip[1] - s * 0.015), (hip[0] + w * 0.9, hip[1] - s * 0.015), (hip[0] + w, hip[1] - s * 0.06)],
                       fill=(30, 32, 36, 200), width=max(1, int(s * 0.004)), joint='curve')
                for sg in (-1, 1):
                    x0 = nek[0] + sg * hrx * 0.35 + math.sin(math.radians(yaw_deg)) * hrx * 0.2
                    y0 = nek[1] + hry * 0.45
                    sw = string_sway * s * 0.02
                    d.line([(x0, y0), (x0 + sw * 0.5 + sg * s * 0.004, y0 + s * 0.05), (x0 + sw, y0 + s * 0.095)], fill=(216, 212, 200, 230), width=max(1, int(s * 0.0035)), joint='curve')
            continue
        if nm in ('arm', 'fore'):
            poly = _capsule(a, b, r0, r1)
            paint(poly, (r0 + r1) / 2, *pal['hood'])
            if nm == 'fore':
                # hand at the wrist, continuing the forearm direction
                v = np.array([b[0] - a[0], b[1] - a[1]], np.float32)
                n_ = np.linalg.norm(v) + 1e-6
                fwd = (float(v[0] / n_), float(v[1] / n_))
                side = 'l' if b is J['hal'] else 'r'
                hp_ = hand_l if side == 'l' else hand_r
                kk = KS['hal' if side == 'l' else 'har']
                tip = draw_hand(layer, b, fwd, s, hp_, light, kk, pal['skin'], flip=(side == 'r') ^ flip, silhouette=silhouette)
                extras['tip_' + side] = tip
                extras['fwd_' + side] = fwd
            continue
        if nm in ('thigh', 'shin'):
            poly = _capsule(a, b, r0, r1)
            paint(poly, (r0 + r1) / 2, *pal['pants'])
            if nm == 'shin' and shoes:
                ft = b
                kk = KS['ftl' if b is J['ftl'] else 'ftr']
                L = HP['shoe_l'] * s * kk
                hh = HP['shoe_h'] * s * kk
                toe = 1 if (b is J['ftr']) ^ flip else -1
                toe = toe * (1 if abs(yaw_deg) < 90 else -1)
                # sneaker: rounded wedge, toe toward the facing direction
                sh = [(ft[0] - L * 0.35, ft[1] - hh * 0.3), (ft[0] + toe * L * 0.75, ft[1] - hh * 0.1),
                      (ft[0] + toe * L * 0.85, ft[1] + hh * 0.5), (ft[0] + toe * L * 0.6, ft[1] + hh * 1.0),
                      (ft[0] - toe * L * 0.4, ft[1] + hh * 1.0), (ft[0] - toe * L * 0.45, ft[1] + hh * 0.2)]
                paint(sh, hh, *pal['shoe'])
            continue
        poly = _capsule(a, b, r0, r1)
        paint(poly, (r0 + r1) / 2, *pal['hood'])
    extras['head'] = (J['hctr'], hrx, hry, head_ang, yaw_deg)
    return J, KS, extras


# ─────────────────────────────────────────────── pose presets (angles in degrees; see toon._skeleton)
def p_stand(t=0.0, weight=0.0):
    """Relaxed stance with weight on one leg (weight −1..1), breathing on the shoulders."""
    b = breathe(t)
    return dict(al=-16, ar=16, ef_l=10, ef_r=10, az_l=2, az_r=-2, ll=-5, lr=5, kl=3 + 4 * max(0, weight), kr=3 + 4 * max(0, -weight),
                sway=0.012 * weight, tilt=3 * weight, lean=1.5, sh_up=0.004 * b, head=-1.5 * weight)


def p_sit(t=0.0, slump=0.4):
    """Sitting on a bed edge, facing camera-ish: thighs forward (toward the lens), shins down."""
    b = breathe(t)
    return dict(lz_l=80, lz_r=76, kl=96, kr=92, ll=-9, lr=9, lean=8 + 12 * slump, head=5 * slump,
                al=-8, ar=8, az_l=38, az_r=38, ef_l=62, ef_r=62, sh_up=0.004 * b)


def p_phone_bed(t=0.0):
    """Lying on the back (use rot=−90), phone held above the face with both hands."""
    b = breathe(t, 0.2)
    return dict(lz_l=10, lz_r=14, kl=30, kr=40, ll=-6, lr=6, lean=0, az_l=120, az_r=120, ef_l=100, ef_r=100,
                al=-6, ar=6, el=10, er=-10, head_t=0, head=0, sh_up=0.004 * b)


def p_window(t=0.0, lean=6.0):
    """Standing at the glass, back to camera (yaw 180), palms on the window."""
    b = breathe(t)
    return dict(yaw=180, al=-30, ar=30, az_l=70, az_r=70, ef_l=35, ef_r=35, lean=lean, ll=-5, lr=5, sh_up=0.004 * b)
