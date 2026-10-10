#!/usr/bin/env python3
"""
stick3d.py — WF-03 · Monarch Noir Film — NOIRGO MAX · the 3-D HUMAN STICK FIGURE (2026-10-10, turn 20)

"Stickman — but everything human." A true 3-D render (not a 2-D drawing) of the Monarch stick hero:
  • geometry  : analytic ray casting of round cones (limbs, fingers, neck, brows, lips, lashes, drawstrings),
                oriented ellipsoids (head, jaw, hair clumps, ears, nose, palms, shoes, hood) and boxes (phone),
                z-buffered per pixel — thin stick limbs, full human proportions, real joints.
  • face      : eyeballs with eyelids (openness, squint, blink), iris + limbal ring + pupil, gaze, lash line,
                brows (raise / inner tilt), nose, ears, lip line, open-mouth cavity, 10 expressions (human.EXPR).
  • hands     : palm + 5 fingers × 3 phalanges + thumb, 8 gesture presets, correct chirality (thumbs forward).
  • feet      : sneakers with sole + heel, foot follows the shin, splay, toe-down on the back leg.
  • light     : key / fill / rim / point lights (phone screen, lamp), Blinn-Phong speculars, Fresnel rim,
                screen-space AO, subsurface warmth on skin, hemisphere ambient, emissive phone screen.
  • finish    : faint ink edge (depth discontinuities + silhouette) so the figure keeps the Monarch stick identity.
Skeleton + poses + expressions + IK come from human.py / WF-01 toon._skeleton (3-D joints).

API (canvas = RGBA PIL image in SS pixels, like human.draw_human):
    render(can, x, y, s, pose, lights, expr='neutral', look=(0,0), blink_v=0.0, hands=('relax','relax'),
           props=(), flip=False, rot=0.0, anchor='feet', ink=0.35, ao=0.6) -> J (screen joints), extras
    solve(x, y, s, pose, flip, rot, anchor) -> K3 (figure-space 3-D points), J (screen px), frames
    reach(pose, side, target, x, y, s, ...) -> pose (numeric IK on the projected wrist)
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, HERE)
import toon as T            # noqa: E402
import human as Hm          # noqa: E402  (HP proportions, EXPR, walk/run/blink/breathe)

HP = Hm.HP
EXPR = Hm.EXPR
INF = np.float32(np.inf)
np.seterr(invalid='ignore', divide='ignore')

# ─────────────────────────────────────────────── materials  (sRGB base colour, spec, gloss, wrap, sss)
MATS = {
    'skin':     dict(col=(236, 224, 208), spec=0.10, gloss=22.0, wrap=0.42, sss=1.0),
    'lid':      dict(col=(232, 218, 200), spec=0.12, gloss=26.0, wrap=0.42, sss=1.0),
    'sclera':   dict(col=(240, 238, 234), spec=0.90, gloss=260.0, wrap=0.25, sss=0.0),
    'iris':     dict(col=(96, 62, 40),    spec=0.90, gloss=260.0, wrap=0.30, sss=0.0),
    'pupil':    dict(col=(7, 6, 6),       spec=0.90, gloss=260.0, wrap=0.0, sss=0.0),
    'lash':     dict(col=(18, 14, 14),    spec=0.05, gloss=10.0, wrap=0.1, sss=0.0),
    'brow':     dict(col=(30, 25, 24),    spec=0.08, gloss=12.0, wrap=0.1, sss=0.0),
    'hair':     dict(col=(36, 28, 26),    spec=0.09, gloss=16.0, wrap=0.22, sss=0.0),
    'hair2':    dict(col=(46, 36, 33),    spec=0.09, gloss=16.0, wrap=0.22, sss=0.0),
    'lips':     dict(col=(112, 62, 58),   spec=0.28, gloss=34.0, wrap=0.35, sss=0.6),
    'mouth_in': dict(col=(26, 11, 11),    spec=0.0, gloss=10.0, wrap=0.0, sss=0.0),
    'hoodie':   dict(col=(56, 60, 68),    spec=0.05, gloss=8.0, wrap=0.22, sss=0.0),
    'hoodie_dk': dict(col=(42, 45, 52),   spec=0.05, gloss=8.0, wrap=0.22, sss=0.0),
    'string':   dict(col=(196, 194, 188), spec=0.08, gloss=12.0, wrap=0.3, sss=0.0),
    'joggers':  dict(col=(36, 38, 45),    spec=0.04, gloss=8.0, wrap=0.2, sss=0.0),
    'shoe':     dict(col=(222, 218, 210), spec=0.22, gloss=30.0, wrap=0.25, sss=0.0),
    'sole':     dict(col=(186, 184, 180), spec=0.10, gloss=16.0, wrap=0.25, sss=0.0),
    'phone':    dict(col=(22, 22, 26),    spec=0.55, gloss=90.0, wrap=0.1, sss=0.0),
    'screen':   dict(col=(176, 204, 244), spec=0.3, gloss=120.0, wrap=0.0, sss=0.0, emit=0.85),
    'ink':      dict(col=(8, 8, 10),      spec=0.0, gloss=1.0, wrap=0.0, sss=0.0),
    'plate':    dict(col=(226, 224, 218), spec=0.45, gloss=60.0, wrap=0.3, sss=0.0),
    'sponge':   dict(col=(214, 190, 70),  spec=0.05, gloss=6.0, wrap=0.4, sss=0.0),
    'ice':      dict(col=(196, 222, 240), spec=0.35, gloss=40.0, wrap=0.35, sss=0.0),
    'paper':    dict(col=(230, 226, 214), spec=0.08, gloss=10.0, wrap=0.3, sss=0.0),
}
MAT_ID = {k: i for i, k in enumerate(MATS)}
MAT_LIST = list(MATS)

HAND_PRESETS = {  # curl (deg) per phalanx for index..pinky, spread (deg), thumb (abd, curl1, curl2)
    'relax': dict(curl=(20, 28, 15), spread=4.0, thumb=(38, 12, 22), per=None),
    'fist':  dict(curl=(88, 100, 72), spread=0.0, thumb=(20, 48, 56), per=None),
    'flat':  dict(curl=(3, 2, 0), spread=6.0, thumb=(42, 0, 4), per=None),
    'phone': dict(curl=(60, 72, 34), spread=3.0, thumb=(28, 18, 22), per=None),
    'grip':  dict(curl=(68, 84, 46), spread=2.0, thumb=(24, 34, 44), per=None),
    'point': dict(curl=(90, 100, 72), spread=0.0, thumb=(24, 36, 44), per={0: (4, 2, 0)}),
    'splay': dict(curl=(4, 4, 0), spread=15.0, thumb=(58, 0, 2), per=None),
    'cup':   dict(curl=(44, 60, 32), spread=5.0, thumb=(40, 16, 24), per=None),
    'glass': dict(curl=(1, 0, 0), spread=9.0, thumb=(50, 0, 0), per=None),
}

# ─────────────────────────────────────────────── small vector helpers (tuples / arrays)
def _n(v):
    v = np.asarray(v, dtype=np.float64)
    l = np.linalg.norm(v)
    return v / l if l > 1e-12 else v


def _rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def _rot_axis(axis, a):
    axis = _n(axis)
    x, y, z = axis
    c, s = math.cos(a), math.sin(a)
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


# ─────────────────────────────────────────────── skeleton solve in figure space
def solve(x, y, s, pose, flip=False, rot=0.0, anchor='feet'):
    """Figure space: origin = anchor point (feet centre on the ground, or the hip), x right, y DOWN, z toward
    the camera; camera at (0, 0, F), F = 4.2 s. Returns (K3, J, frames).
    K3: 3-D points (np arrays) · J: projected canvas px · frames: dict(R_body, R_head, yaw, sgn, F)."""
    sgn = -1 if flip else 1
    saved = T.P
    T.P = HP
    try:
        K = T._skeleton(pose, s, sgn)
    finally:
        T.P = saved
    g = pose.get
    F = 4.2 * s
    pts = {k: np.array(v, dtype=np.float64) for k, v in K.items() if isinstance(v, tuple) and len(v) == 3}
    if anchor == 'feet':
        sole = max(pts['ftl'][1], pts['ftr'][1]) + HP['ankle'] * s
        ty = -sole - g('bob', 0.0) * s
    else:
        ty = 0.0
    Rr = _rot_z(math.radians(rot)) if abs(rot) > 1e-9 else np.eye(3)
    K3 = {}
    for k, v in pts.items():
        K3[k] = Rr @ (v + np.array([0.0, ty, 0.0]))
    yaw = math.radians(g('yaw', 0) * sgn)
    lean = math.radians(g('lean', 0) * sgn)
    hd_z = math.radians(g('head', 0) * sgn)
    hd_y = math.radians(g('head_t', 0) * sgn)
    R_body = Rr @ _rot_y(yaw) @ _rot_z(lean)
    R_head = Rr @ _rot_y(yaw) @ _rot_z(lean + hd_z) @ _rot_y(hd_y)
    R_pelvis = Rr @ _rot_y(yaw) @ _rot_z(math.radians(g('tilt', 0) * sgn)) @ _rot_y(math.radians(g('pelvis', 0) * sgn))
    frames = dict(R_body=R_body, R_head=R_head, R_pelvis=R_pelvis, yaw=yaw, sgn=sgn, F=F, x=x, y=y, s=s)
    J = {k: project(v, frames) for k, v in K3.items()}
    return K3, J, frames


def project(p, fr):
    F = fr['F']
    k = F / (F - p[2])
    return (fr['x'] + p[0] * k, fr['y'] + p[1] * k)


def reach(pose, side, target, x, y, s, flip=False, rot=0.0, anchor='feet', iters=30):
    """Numeric IK on the projected wrist (same search as human.reach, but on the 3-D solve)."""
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


# ─────────────────────────────────────────────── primitive builders
# prim = dict(kind='cone'|'ellip'|'box', mat=str, ... , bs=[(centre, radius), ...] bounding spheres, deco=callable|None)
def cone(a, b, ra, rb, mat, deco=None):
    a = np.asarray(a, float); b = np.asarray(b, float)
    return dict(kind='cone', a=a, b=b, ra=float(ra), rb=float(rb), mat=mat, bs=[(a, ra), (b, rb)], deco=deco)


def sphere(c, r, mat, deco=None):
    c = np.asarray(c, float)
    return dict(kind='ellip', c=c, R=np.eye(3), rad=np.array([r, r, r], float), mat=mat, bs=[(c, r)], deco=deco)


def ellip(c, R, rad, mat, deco=None):
    c = np.asarray(c, float)
    rad = np.asarray(rad, float)
    return dict(kind='ellip', c=c, R=np.asarray(R, float), rad=rad, mat=mat, bs=[(c, float(rad.max()))], deco=deco)


def box(c, R, half, mat, face_mats=None):
    c = np.asarray(c, float)
    half = np.asarray(half, float)
    return dict(kind='box', c=c, R=np.asarray(R, float), half=half, mat=mat, bs=[(c, float(np.linalg.norm(half)))],
                face_mats=face_mats, deco=None)


# ─────────────────────────────────────────────── the figure → primitives
def build_prims(K3, fr, s, pose, expr='neutral', look=(0.0, 0.0), blink_v=0.0, hands=('relax', 'relax'),
                props=(), silhouette=False, only=None):
    E = EXPR[expr] if isinstance(expr, str) else expr
    P = []
    sgn = fr['sgn']
    Rb, Rh = fr['R_body'], fr['R_head']
    fwd_b = Rb @ np.array([0, 0, 1.0])
    right_b = Rb @ np.array([1.0, 0, 0])
    up_b = Rb @ np.array([0, -1.0, 0])
    hipc, shoc, nek, hpiv, hctr = K3['hipc'], K3['shoc'], K3['nek'], K3['hpiv'], K3['hctr']
    shl, shr, hpl, hpr = K3['shl'], K3['shr'], K3['hpl'], K3['hpr']
    sk = 'ink' if silhouette else 'skin'
    cl = 'ink' if silhouette else 'hoodie'
    cl2 = 'ink' if silhouette else 'hoodie_dk'
    pj = 'ink' if silhouette else 'joggers'
    hr = 'ink' if silhouette else 'hair'

    # torso (slim stick body with a hoodie), shoulder + pelvis bars, hood, drawstrings
    P.append(cone(hipc, shoc, 0.024 * s, 0.041 * s, cl))
    P.append(cone(shl + up_b * 0.0 * s, shoc + up_b * 0.016 * s, 0.015 * s, 0.021 * s, cl))
    P.append(cone(shr + up_b * 0.0 * s, shoc + up_b * 0.016 * s, 0.015 * s, 0.021 * s, cl))
    P.append(cone(hpl, hpr, 0.018 * s, 0.018 * s, pj))
    P.append(cone(hipc - up_b * 0.01 * s, hipc + up_b * 0.02 * s, 0.029 * s, 0.029 * s, pj))   # waistband
    hood_c = nek - fwd_b * 0.034 * s - up_b * 0.012 * s
    P.append(ellip(hood_c, Rb, (0.054 * s, 0.022 * s, 0.028 * s), cl2))
    P.append(cone(nek - fwd_b * 0.005 * s, nek + fwd_b * 0.010 * s, 0.026 * s, 0.026 * s, cl2))  # collar ring
    for sd in (-1, 1):
        a = nek + fwd_b * 0.034 * s + right_b * sd * 0.014 * s - up_b * 0.004 * s
        b = a + np.array([0, 1.0, 0]) * 0.085 * s + fwd_b * 0.004 * s
        P.append(cone(a, b, 0.0038 * s, 0.0032 * s, 'string' if not silhouette else 'ink'))
        P.append(sphere(b, 0.0046 * s, 'string' if not silhouette else 'ink'))
    # neck
    P.append(cone(shoc, hpiv, 0.0135 * s, 0.0125 * s, sk))

    # arms (sleeves) + hands
    for sd, nm_s, nm_e, nm_w in (('l', 'shl', 'ell', 'hal'), ('r', 'shr', 'elr', 'har')):
        S, El, Wr = K3[nm_s], K3[nm_e], K3[nm_w]
        P.append(cone(S, El, 0.0135 * s, 0.0118 * s, cl))
        P.append(sphere(El, 0.0126 * s, cl))
        P.append(cone(El, Wr, 0.0118 * s, 0.0100 * s, cl))
        P.append(sphere(Wr, 0.0112 * s, cl2))               # cuff
        preset = hands[0] if sd == 'l' else hands[1]
        tw = pose.get('hw_' + sd, 0.0)
        hp = hand_prims(Wr, El, S, shl, shr, sd, sgn, preset, s, tw, sk, props, fwd_b)
        for q in hp:
            q['grp'] = 'hand_' + sd
        P += hp

    # legs (joggers) + sneakers
    for sd, nm_h, nm_k, nm_f in (('l', 'hpl', 'knl', 'ftl'), ('r', 'hpr', 'knr', 'ftr')):
        H, Kn, Ft = K3[nm_h], K3[nm_k], K3[nm_f]
        P.append(cone(H, Kn, 0.0165 * s, 0.0140 * s, pj))
        P.append(sphere(Kn, 0.0150 * s, pj))
        P.append(cone(Kn, Ft, 0.0140 * s, 0.0108 * s, pj))
        P.append(sphere(Ft, 0.0118 * s, pj))
        fp = shoe_prims(Ft, Kn, hpl, hpr, sd, sgn, s, silhouette)
        for q in fp:
            q['grp'] = 'foot_' + sd
        P += fp

    # head
    hp = head_prims(hctr, Rh, s, E, look, blink_v, silhouette, sgn)
    for q in hp:
        q['grp'] = 'head'
    P += hp
    if only:
        P = [q for q in P if q.get('grp') == only]
    return P


def hand_prims(Wr, El, Sh, shl, shr, side, sgn, preset, s, twist_deg, skin_mat, props, fwd_b):
    """Palm + five fingers. Frame: f = forearm direction (toward the fingers), n = palm normal (the way the palm
    faces), u = thumb side. Default: palm faces the body; `twist_deg` pronates about f (+ = palm turns forward)."""
    out = []
    f = _n(Wr - El)
    lat = _n(shr - shl)                                       # body lateral axis (screen right when facing camera)
    toward_body = -lat if side == 'r' else lat                # the body is on this side of the hand
    n0 = toward_body - f * float(toward_body @ f)
    if np.linalg.norm(n0) < 0.15:
        n0 = fwd_b - f * float(fwd_b @ f)
    n = _n(n0)
    if abs(twist_deg) > 1e-6:
        n = _rot_axis(f, math.radians(twist_deg * (1 if side == 'r' else -1))) @ n
    side_sign = (1.0 if side == 'r' else -1.0) * sgn
    u = side_sign * np.cross(f, n)                           # thumb side (forward when the palms face the thighs)
    Lp, Wp = 0.040 * s, 0.033 * s
    palm_c = Wr + f * Lp * 0.52 - n * 0.002 * s
    out.append(ellip(palm_c, np.stack([u, n, f], axis=1), (Wp * 0.50, 0.0105 * s, Lp * 0.56), skin_mat))
    out.append(sphere(Wr + f * 0.004 * s, 0.0098 * s, skin_mat))   # wrist
    pr = HAND_PRESETS.get(preset, HAND_PRESETS['relax'])
    FL = 0.050 * s
    lens = (0.80, 0.88, 0.82, 0.64)
    offs = (-0.56, -0.19, 0.19, 0.56)
    r0 = 0.0054 * s
    for i in range(4):
        curl = pr['per'].get(i, pr['curl']) if pr['per'] else pr['curl']
        spread = math.radians(pr['spread'] * (1.5 - i))        # index spreads toward the thumb, pinky away
        base = Wr + f * Lp * 0.98 + u * (-offs[i]) * Wp * 0.5 * (1 if True else 1)
        # finger axis in the palm plane (spread), curling toward the palm face (+n)
        fa = _n(f * math.cos(spread) + u * math.sin(spread) * (1 if side_sign > 0 else 1))
        ang = 0.0
        p = base
        fracs = (0.45, 0.31, 0.24)
        rr = r0
        for j in range(3):
            ang += math.radians(curl[j])
            d = _n(fa * math.cos(ang) + n * math.sin(ang))
            q = p + d * FL * lens[i] * fracs[j]
            r1 = rr * (0.92 if j < 2 else 0.84)
            out.append(cone(p, q, rr, r1, skin_mat))
            if j < 2:
                out.append(sphere(q, r1, skin_mat))          # knuckle: closes the gap on the outside of a bend
            p, rr = q, r1
    # thumb
    ta, tc1, tc2 = pr['thumb']
    tb = Wr + f * Lp * 0.28 + u * Wp * 0.50 - n * 0.003 * s
    ta_r = math.radians(ta)
    t_dir = _n(f * math.cos(ta_r) + u * math.sin(ta_r))
    tcurl = math.radians(tc1)
    d1 = _n(t_dir * math.cos(tcurl) + n * math.sin(tcurl))
    TL = 0.040 * s
    m1 = tb + d1 * TL * 0.55
    out.append(cone(tb, m1, 0.0075 * s, 0.0066 * s, skin_mat))
    out.append(sphere(m1, 0.0066 * s, skin_mat))
    tcurl2 = tcurl + math.radians(tc2)
    d2 = _n(t_dir * math.cos(tcurl2) + n * math.sin(tcurl2))
    m2 = m1 + d2 * TL * 0.45
    out.append(cone(m1, m2, 0.0066 * s, 0.0056 * s, skin_mat))
    # props attached to this hand
    for pp in props:
        if pp.get('hand') != side:
            continue
        if pp['kind'] == 'phone':
            pc = Wr + f * Lp * 0.78 + n * 0.013 * s + u * 0.012 * s
            Rm = np.stack([u, f, n], axis=1)           # box axes: u (length, across the palm), f (width), n (thickness)
            out.append(box(pc, Rm, (0.0425 * s, 0.021 * s, 0.0028 * s), 'phone',
                           face_mats={(2, 1): 'screen'}))
        elif pp['kind'] == 'mug':
            mc = Wr + f * Lp * 1.05 + n * 0.030 * s
            out.append(ellip(mc, np.stack([u, n, f], axis=1), (0.030 * s, 0.030 * s, 0.040 * s), 'sole'))
        elif pp['kind'] == 'plate':      # a dinner plate resting on the open palm (disc normal = palm normal)
            pc = Wr + f * Lp * 0.95 + n * 0.014 * s
            out.append(ellip(pc, np.stack([u, n, f], axis=1), (0.078 * s, 0.0035 * s, 0.078 * s), 'plate'))
        elif pp['kind'] == 'sponge':     # a kitchen sponge gripped under the fingers
            pc = Wr + f * Lp * 0.95 + n * 0.016 * s
            out.append(box(pc, np.stack([u, f, n], axis=1), (0.024 * s, 0.018 * s, 0.009 * s), 'sponge'))
        elif pp['kind'] == 'icepack':    # a soft ice pack held against the knee
            pc = Wr + f * Lp * 0.9 + n * 0.018 * s
            out.append(ellip(pc, np.stack([u, n, f], axis=1), (0.055 * s, 0.014 * s, 0.045 * s), 'ice'))
        elif pp['kind'] == 'papers':     # a stack of papers held flat
            pc = Wr + f * Lp * 0.9 + n * 0.012 * s
            out.append(box(pc, np.stack([u, f, n], axis=1), (0.075 * s, 0.055 * s, 0.004 * s), 'paper'))
    return out


def shoe_prims(Ft, Kn, hpl, hpr, side, sgn, s, silhouette):
    out = []
    d_shin = _n(Ft - Kn)
    lat = _n(hpr - hpl)
    fwd = np.cross(lat, d_shin)
    if np.linalg.norm(fwd) < 1e-6:
        fwd = np.array([0, 0, 1.0])
    fwd = _n(fwd)
    splay = math.radians(9.0) * (1.0 if side == 'r' else -1.0) * sgn
    fwd = _rot_axis(d_shin, splay) @ fwd
    down = _n(np.cross(fwd, lat))
    if down[1] < 0:
        down = -down
    sidev = _n(np.cross(down, fwd))
    m_sh = 'ink' if silhouette else 'shoe'
    m_so = 'ink' if silhouette else 'sole'
    Rm = np.stack([sidev, down, fwd], axis=1)
    c = Ft + fwd * 0.030 * s + down * 0.030 * s
    out.append(ellip(c, Rm, (0.0235 * s, 0.0235 * s, 0.070 * s), m_sh))
    out.append(sphere(Ft + down * 0.034 * s - fwd * 0.012 * s, 0.0205 * s, m_sh))
    out.append(ellip(Ft + fwd * 0.026 * s + down * 0.050 * s, Rm, (0.0255 * s, 0.0070 * s, 0.078 * s), m_so))
    out.append(ellip(Ft + fwd * 0.012 * s + down * 0.012 * s, Rm, (0.021 * s, 0.020 * s, 0.028 * s), m_sh))  # tongue
    return out


def head_prims(hctr, Rh, s, E, look, blink_v, silhouette, sgn):
    out = []
    R = 0.066 * s
    right = Rh @ np.array([1.0, 0, 0])
    up = Rh @ np.array([0, -1.0, 0])
    fwd = Rh @ np.array([0, 0, 1.0])

    def dirv(phi, th):
        return math.cos(th) * math.sin(phi) * right + math.sin(th) * up + math.cos(th) * math.cos(phi) * fwd

    sk = 'ink' if silhouette else 'skin'
    hr = 'ink' if silhouette else 'hair'
    # cranium + jaw
    mouth = None if silhouette else dict(open=E['open'], smile=E['smile'])
    out.append(sphere(hctr, R, sk, deco=('head', Rh, hctr, R, mouth)))
    out.append(ellip(hctr - up * 0.22 * R + fwd * 0.04 * R, Rh, (0.76 * R, 0.90 * R, 0.84 * R), sk, deco=('head', Rh, hctr, R, mouth)))
    # ears
    for sd in (-1, 1):
        out.append(ellip(hctr + dirv(sd * 1.52, -0.05) * R * 0.98, Rh, (0.065 * R, 0.17 * R, 0.12 * R), sk))
    # nose
    out.append(cone(hctr + dirv(0, -0.06) * R * 0.96, hctr + dirv(0, -0.25) * R * 0.99 + fwd * 0.085 * R,
                    0.075 * R, 0.10 * R, sk))
    if silhouette:
        out += hair_prims(hctr, R, right, up, fwd, 'ink')
        return out
    # eyes
    open_v = E['lids'] * (1.0 - blink_v)
    top = 0.56 * open_v
    bot = -0.46 * open_v * (1.0 - 0.55 * E['squint']) - 0.02
    re = 0.29 * R
    gaze = dirv(look[0] * 0.42, -look[1] * 0.32)
    for sd in (-1, 1):
        ce = hctr + dirv(sd * 0.40, -0.04) * (R - 0.84 * re)
        out.append(sphere(ce, re, 'sclera', deco=('eye', Rh, ce, re, gaze, top, bot, sd)))
        # lash line on the upper lid edge (only the part outside the head is visible)
        pts = []
        for a in np.linspace(-0.80, 0.80, 5):
            el = top - 0.10 * max(0.0, a * sd)      # outer corner slightly lower
            d = math.cos(el) * math.sin(a) * right + math.sin(el) * up + math.cos(el) * math.cos(a) * fwd
            pts.append(ce + d * re * 1.025)
        for i in range(4):
            out.append(cone(pts[i], pts[i + 1], 0.055 * re, 0.055 * re, 'lash'))
        # brow
        bpts = []
        for a in np.linspace(-1.0, 1.0, 4):
            th = -0.04 + 0.36 + E['brow_h'] * 0.26 + 0.07 * (1 - a * a) + E['brow_in'] * 0.22 * (1 - a) * 0.5
            ph = sd * (0.40 + a * 0.30)
            bpts.append(hctr + dirv(ph, th) * R * 1.02)
        for i in range(3):
            w0 = (0.062 - 0.012 * i) * R
            out.append(cone(bpts[i], bpts[i + 1], w0, w0 - 0.010 * R, 'brow'))
    # lips: upper line (corners follow `smile`), lower line drops with `open` → an oval opening
    thm = -0.66
    op = E['open']
    lp = []
    for a in np.linspace(-0.30, 0.30, 7):
        u_ = (a / 0.30) ** 2
        th = thm + E['smile'] * 0.11 * u_ + op * 0.05 * (1 - u_)
        lp.append(hctr + dirv(a, th) * R * 1.0 + fwd * 0.045 * R)
    for i in range(6):
        out.append(cone(lp[i], lp[i + 1], 0.036 * R, 0.036 * R, 'lips'))
    if op > 0.05:
        lp2 = []
        wmax = 0.30 - op * 0.08
        for a in np.linspace(-wmax, wmax, 7):
            u_ = (a / wmax) ** 2
            th = thm - 0.03 - op * 0.26 * (1 - 0.55 * u_) + E['smile'] * 0.06 * u_
            lp2.append(hctr + dirv(a, th) * R * 1.0 + fwd * 0.045 * R)
        for i in range(6):
            out.append(cone(lp2[i], lp2[i + 1], 0.034 * R, 0.034 * R, 'lips'))
    out += hair_prims(hctr, R, right, up, fwd, hr)
    return out


def hair_prims(hctr, R, right, up, fwd, mat):
    """Short messy hair: a matte cap that leaves the forehead clear, side + back volume, a nape, and a fringe
    of flattened lobes swept to screen-right (reads as hair, not as sticks)."""
    Rm = np.stack([right, up, fwd], axis=1)
    out = []
    out.append(ellip(hctr + up * 0.30 * R - fwd * 0.12 * R, Rm, (0.98 * R, 0.88 * R, 0.98 * R), mat))   # cap
    out.append(ellip(hctr + up * 0.02 * R - fwd * 0.45 * R, Rm, (0.90 * R, 0.80 * R, 0.62 * R), mat))   # back
    for sd in (-1, 1):
        out.append(ellip(hctr + right * sd * 0.78 * R + up * 0.34 * R - fwd * 0.22 * R, Rm,
                         (0.30 * R, 0.46 * R, 0.60 * R), mat))                                            # sides
    out.append(ellip(hctr - up * 0.32 * R - fwd * 0.70 * R, Rm, (0.56 * R, 0.28 * R, 0.34 * R), mat))   # nape
    # fringe lobes: (centre right, up, fwd), (radii), yaw tilt around fwd/up
    lobes = [((-0.50, 0.62, 0.62), (0.36, 0.15, 0.34), 0.60, 0),
             ((-0.10, 0.70, 0.68), (0.42, 0.14, 0.34), 0.35, 1),
             ((0.32, 0.68, 0.64), (0.42, 0.15, 0.36), 0.05, 0),
             ((0.68, 0.54, 0.56), (0.34, 0.17, 0.34), -0.35, 1),
             ((0.06, 0.86, 0.46), (0.60, 0.16, 0.40), 0.15, 0),
             ((-0.72, 0.42, 0.60), (0.20, 0.26, 0.28), 0.75, 1),
             ((0.80, 0.30, 0.40), (0.18, 0.30, 0.34), -0.40, 0)]
    for (ax, ay, az), (rx, ry, rz), tilt, alt in lobes:
        c = hctr + (right * ax + up * ay + fwd * az) * R
        Rl = Rm @ _rot_z(tilt)
        out.append(ellip(c, Rl, (rx * R, ry * R, rz * R), (mat if (alt == 0 or mat == 'ink') else 'hair2')))
    # a few thin flyaway strands on top for texture
    strands = [((-0.35, 1.02, 0.20), (0.30, 1.10, 0.05), 0.045, 0.02),
               ((0.10, 1.08, 0.10), (0.70, 0.98, -0.10), 0.045, 0.02),
               ((-0.60, 0.94, -0.10), (-0.05, 1.10, -0.30), 0.04, 0.02)]
    for (ax, ay, az), (bx, by, bz), ra, rb in strands:
        a = hctr + (right * ax + up * ay + fwd * az) * R
        b = hctr + (right * bx + up * by + fwd * bz) * R
        out.append(cone(a, b, ra * R, rb * R, mat))
    return out


# ─────────────────────────────────────────────── analytic intersections (vectorised over rays)
def _isect_cone(ro, D, pa, pb, ra, rb):
    ba = pb - pa
    oa = ro - pa
    ob = ro - pb
    rr = ra - rb
    m0 = float(ba @ ba)
    m1 = float(ba @ oa)
    m2 = D @ ba
    m3 = D @ oa
    m5 = float(oa @ oa)
    m6 = D @ ob
    m7 = float(ob @ ob)
    d2 = m0 - rr * rr
    k2 = d2 - m2 * m2
    k1 = d2 * m3 - m1 * m2 + m2 * rr * ra
    k0 = d2 * m5 - m1 * m1 + m1 * rr * ra * 2.0 - m0 * ra * ra
    h = k1 * k1 - k0 * k2
    N = D.shape[0]
    t = np.full(N, np.inf)
    nrm = np.zeros((N, 3))
    with np.errstate(invalid='ignore', divide='ignore'):
        tb = (-np.sqrt(np.maximum(h, 0.0)) - k1) / k2
        yb = m1 - ra * rr + tb * m2
        body = (h >= 0) & (np.abs(k2) > 1e-9) & (yb > 0) & (yb < d2) & (tb > 0)
        if body.any():
            pb_ = oa + tb[body, None] * D[body]
            nb = d2 * pb_ - ba[None, :] * yb[body, None]
            nb /= np.linalg.norm(nb, axis=1, keepdims=True) + 1e-12
            t[body] = tb[body]
            nrm[body] = nb
        # caps
        h1 = m3 * m3 - m5 + ra * ra
        h2 = m6 * m6 - m7 + rb * rb
        t1 = np.where(h1 > 0, -m3 - np.sqrt(np.maximum(h1, 0)), np.inf)
        t2 = np.where(h2 > 0, -m6 - np.sqrt(np.maximum(h2, 0)), np.inf)
        rest = ~body
        tc = np.minimum(t1, t2)
        capok = rest & np.isfinite(tc) & (tc > 0)
        if capok.any():
            useA = capok & (t1 <= t2)
            useB = capok & (t2 < t1)
            if useA.any():
                pA = oa + t1[useA, None] * D[useA]
                t[useA] = t1[useA]
                nrm[useA] = pA / ra
            if useB.any():
                pB = ob + t2[useB, None] * D[useB]
                t[useB] = t2[useB]
                nrm[useB] = pB / rb
    return t, nrm


def _isect_ellip(ro, D, c, R, rad):
    inv = 1.0 / rad
    ro2 = (R.T @ (ro - c)) * inv
    D2 = (D @ R) * inv[None, :]
    A = np.einsum('ij,ij->i', D2, D2)
    B = D2 @ ro2
    C = float(ro2 @ ro2) - 1.0
    h = B * B - A * C
    N = D.shape[0]
    t = np.full(N, np.inf)
    nrm = np.zeros((N, 3))
    ok = h >= 0
    with np.errstate(invalid='ignore', divide='ignore'):
        tt = (-B - np.sqrt(np.maximum(h, 0))) / A
    ok &= tt > 0
    if ok.any():
        p2 = ro2[None, :] + tt[ok, None] * D2[ok]
        n2 = p2 * inv[None, :]
        nw = n2 @ R.T
        nw /= np.linalg.norm(nw, axis=1, keepdims=True) + 1e-12
        t[ok] = tt[ok]
        nrm[ok] = nw
    return t, nrm


def _isect_box(ro, D, c, R, half):
    ro2 = R.T @ (ro - c)
    D2 = D @ R
    N = D.shape[0]
    with np.errstate(invalid='ignore', divide='ignore'):
        invd = 1.0 / D2
        t1 = (-half[None, :] - ro2[None, :]) * invd
        t2 = (half[None, :] - ro2[None, :]) * invd
    tmin = np.minimum(t1, t2)
    tmax = np.maximum(t1, t2)
    tn = tmin.max(axis=1)
    tf = tmax.min(axis=1)
    ok = (tf >= np.maximum(tn, 0)) & (tn > 0)
    t = np.full(N, np.inf)
    nrm = np.zeros((N, 3))
    face = np.zeros(N, dtype=np.int8)
    sgnf = np.zeros(N, dtype=np.int8)
    if ok.any():
        ax = tmin.argmax(axis=1)
        t[ok] = tn[ok]
        nl = np.zeros((ok.sum(), 3))
        axo = ax[ok]
        sg = -np.sign(D2[ok, axo])
        nl[np.arange(ok.sum()), axo] = sg
        nrm[ok] = nl @ R.T
        face[ok] = axo
        sgnf[ok] = sg
    return t, nrm, face, sgnf


# ─────────────────────────────────────────────── the renderer
def _prim_rect(prim, fr, W, H, pad=3.0):
    F, x, y = fr['F'], fr['x'], fr['y']
    xs, ys = [], []
    for c, r in prim['bs']:
        zc = c[2]
        if zc + r >= F - 1.0:
            return None
        k0 = F / (F - zc)
        kn = F / (F - (zc + r))
        rr = r * kn + pad
        cx, cy = x + c[0] * k0, y + c[1] * k0
        xs += [cx - rr, cx + rr]
        ys += [cy - rr, cy + rr]
    x0, x1 = int(max(0, math.floor(min(xs)))), int(min(W, math.ceil(max(xs)) + 1))
    y0, y1 = int(max(0, math.floor(min(ys)))), int(min(H, math.ceil(max(ys)) + 1))
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def render(can, x, y, s, pose, lights, expr='neutral', look=(0.0, 0.0), blink_v=0.0, hands=('relax', 'relax'),
           props=(), flip=False, rot=0.0, anchor='feet', ink=0.35, ao=0.6, silhouette=False, alpha=1.0,
           clip=None, return_buffers=False, only=None):
    """Render the figure into `can` (RGBA PIL, SS px). lights = dict(key=..., fill=..., rim=..., points=[...],
    sky=(r,g,b), ground=(r,g,b)) — see light_rig(). Returns (J, extras)."""
    K3, J, fr = solve(x, y, s, pose, flip, rot, anchor)
    prims = build_prims(K3, fr, s, pose, expr, look, blink_v, hands, props, silhouette, only)
    W, H = can.size
    rects = []
    for p in prims:
        r = _prim_rect(p, fr, W, H)
        rects.append(r)
    valid = [r for r in rects if r is not None]
    if not valid:
        return J, dict(head=(J['hctr'], 0.066 * s), tips={})
    bx0 = max(0, min(r[0] for r in valid)); by0 = max(0, min(r[1] for r in valid))
    bx1 = min(W, max(r[2] for r in valid)); by1 = min(H, max(r[3] for r in valid))
    if clip is not None:
        bx0, by0 = max(bx0, int(clip[0])), max(by0, int(clip[1]))
        bx1, by1 = min(bx1, int(clip[2])), min(by1, int(clip[3]))
    if bx1 <= bx0 or by1 <= by0:
        return J, dict(head=(J['hctr'], 0.066 * s), tips={})
    bw, bh = bx1 - bx0, by1 - by0
    Z = np.full((bh, bw), np.inf, dtype=np.float64)
    Nn = np.zeros((bh, bw, 3), dtype=np.float32)
    Pp = np.zeros((bh, bw, 3), dtype=np.float32)
    M = np.full((bh, bw), -1, dtype=np.int16)
    AUX = np.zeros((bh, bw), dtype=np.float32)
    F = fr['F']
    ro = np.array([0.0, 0.0, F])
    for p, r in zip(prims, rects):
        if r is None:
            continue
        x0, y0, x1, y1 = max(r[0], bx0), max(r[1], by0), min(r[2], bx1), min(r[3], by1)
        if x1 <= x0 or y1 <= y0:
            continue
        px = np.arange(x0, x1) + 0.5 - x
        py = np.arange(y0, y1) + 0.5 - y
        PX, PY = np.meshgrid(px, py)
        D = np.stack([PX.ravel(), PY.ravel(), np.full(PX.size, -F)], axis=1)
        D /= np.linalg.norm(D, axis=1, keepdims=True)
        face = None
        if p['kind'] == 'cone':
            t, nrm = _isect_cone(ro, D, p['a'], p['b'], p['ra'], p['rb'])
        elif p['kind'] == 'ellip':
            t, nrm = _isect_ellip(ro, D, p['c'], p['R'], p['rad'])
        else:
            t, nrm, face, sgnf = _isect_box(ro, D, p['c'], p['R'], p['half'])
        zs = Z[y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]
        tt = t.reshape(PY.shape)
        closer = tt < zs
        if not closer.any():
            continue
        hitP = (ro[None, :] + t[:, None] * D)
        mat = np.full(t.shape, MAT_ID[p['mat']], dtype=np.int16)
        aux = np.zeros(t.shape, dtype=np.float32)
        if face is not None and p.get('face_mats'):
            for (axis, sg), mname in p['face_mats'].items():
                sel = (face == axis) & (sgnf == sg)
                mat[sel] = MAT_ID[mname]
        if p.get('deco') is not None:
            mat, aux = _decorate(p['deco'], hitP, mat, aux)
        sel = closer.ravel()
        idx = np.where(sel)[0]
        zs[closer] = tt[closer]
        sub = (slice(y0 - by0, y1 - by0), slice(x0 - bx0, x1 - bx0))
        Nn[sub][closer] = nrm[idx].astype(np.float32)
        Pp[sub][closer] = hitP[idx].astype(np.float32)
        M[sub][closer] = mat[idx]
        AUX[sub][closer] = aux[idx]
    rgb, A = _shade(Z, Nn, Pp, M, AUX, fr, lights, s, ink, ao, silhouette)
    if alpha < 1.0:
        A = A * alpha
    out = np.dstack([np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8),
                     np.clip(A * 255 + 0.5, 0, 255).astype(np.uint8)])
    layer = Image.fromarray(out, 'RGBA')
    can.alpha_composite(layer, dest=(bx0, by0))
    ex = dict(head=(J['hctr'], 0.066 * s * F / (F - K3['hctr'][2])), K3=K3, frames=fr)
    if return_buffers:
        ex['buffers'] = (Z, Nn, Pp, M, AUX, (bx0, by0))
    return J, ex


def _decorate(deco, hitP, mat, aux):
    kind = deco[0]
    if kind == 'head':
        _, Rh, c, R, mouth = deco
        if mouth is None or mouth['open'] <= 0.05:
            return mat, aux
        loc = (hitP - c[None, :]) @ Rh          # head-local (x right, y down, z fwd)
        lx, ly, lz = loc[:, 0] / R, loc[:, 1] / R, loc[:, 2] / R
        th = np.arcsin(np.clip(-ly, -1, 1))
        ph = np.arctan2(lx, np.maximum(lz, 1e-6))
        op = mouth['open']
        thm = -0.66 - 0.015 - op * 0.13
        mw, mh = 0.27 - op * 0.07, 0.02 + op * 0.14
        cav = ((ph / mw) ** 2 + ((th - thm) / mh) ** 2 < 1.0) & (lz > 0)
        mat = mat.copy()
        mat[cav] = MAT_ID['mouth_in']
        return mat, aux
    if kind == 'eye':
        _, Rh, ce, re, gaze, top, bot, sd = deco
        e = (hitP - ce[None, :]) / re
        right = Rh @ np.array([1.0, 0, 0]); up = Rh @ np.array([0, -1.0, 0])
        ey = np.clip(e @ up, -1, 1)
        ex_ = e @ right
        el = np.arcsin(ey) + 0.10 * np.maximum(0.0, ex_ * sd)      # outer corner droops a little
        lid = (el > top) | (el < bot)
        cosang = np.clip(e @ gaze, -1, 1)
        ang = np.arccos(cosang)
        iris_a, pupil_a = 0.50, 0.21
        mat = mat.copy()
        aux = aux.copy()
        mat[:] = MAT_ID['sclera']
        iris = ang < iris_a
        mat[iris] = MAT_ID['iris']
        aux[iris] = (ang[iris] / iris_a).astype(np.float32)
        mat[ang < pupil_a] = MAT_ID['pupil']
        dtop = np.minimum(np.abs(el - top), np.abs(el - bot))
        scl = ~iris
        aux[scl] = np.clip(dtop[scl] / 0.22, 0, 1).astype(np.float32)
        mat[lid] = MAT_ID['lid']
        aux[lid] = np.clip(dtop[lid] / 0.14, 0, 1).astype(np.float32)
        return mat, aux
    return mat, aux


def light_rig(key_dir=(-0.55, -0.55, 0.62), key_col=(1.0, 0.93, 0.84), key_int=1.0,
              fill_dir=(0.6, -0.2, 0.75), fill_col=(0.55, 0.65, 0.85), fill_int=0.18,
              rim_dir=(0.5, -0.4, -0.75), rim_col=(0.75, 0.85, 1.0), rim_int=0.55,
              sky=(0.16, 0.19, 0.26), ground=(0.06, 0.05, 0.05), points=()):
    return dict(key=(np.asarray(_n(key_dir)), np.asarray(key_col, float), key_int),
                fill=(np.asarray(_n(fill_dir)), np.asarray(fill_col, float), fill_int),
                rim=(np.asarray(_n(rim_dir)), np.asarray(rim_col, float), rim_int),
                sky=np.asarray(sky, float), ground=np.asarray(ground, float), points=list(points))


def point_light(pos, col=(0.6, 0.75, 1.0), intensity=1.0, radius=120.0):
    """pos in figure space (px): e.g. the phone screen 0.3 s in front of the face."""
    return dict(pos=np.asarray(pos, float), col=np.asarray(col, float), int=float(intensity), rad=float(radius))


def _lin(c):
    return (np.asarray(c, float) / 255.0) ** 2.2


def _shade(Z, Nn, Pp, M, AUX, fr, L, s, ink, ao_k, silhouette):
    bh, bw = Z.shape
    hit = np.isfinite(Z)
    A = hit.astype(np.float32)
    rgb = np.zeros((bh, bw, 3), dtype=np.float32)
    if not hit.any():
        return rgb, A
    if silhouette:
        rgb[hit] = _lin(MATS['ink']['col'])
        rgb = np.clip(rgb, 0, 1) ** (1 / 2.2)
        return rgb, A
    F = fr['F']
    cam = np.array([0.0, 0.0, F], dtype=np.float32)
    n = Nn[hit]
    p = Pp[hit]
    v = cam[None, :] - p
    v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-9
    m = M[hit]
    aux = AUX[hit]
    # material tables
    base = np.zeros((len(m), 3), dtype=np.float32)
    spec = np.zeros(len(m), dtype=np.float32)
    gloss = np.ones(len(m), dtype=np.float32)
    wrap = np.zeros(len(m), dtype=np.float32)
    sss = np.zeros(len(m), dtype=np.float32)
    emit = np.zeros(len(m), dtype=np.float32)
    for name, mid in MAT_ID.items():
        sel = m == mid
        if not sel.any():
            continue
        md = MATS[name]
        base[sel] = _lin(md['col'])
        spec[sel] = md['spec']; gloss[sel] = md['gloss']; wrap[sel] = md['wrap']; sss[sel] = md['sss']
        emit[sel] = md.get('emit', 0.0)
    # iris gradient + limbal ring, sclera / lid shading from the lid edge
    iris = m == MAT_ID['iris']
    if iris.any():
        t = aux[iris]
        g = np.clip(1.45 - 1.05 * t, 0.35, 1.45)                 # bright near the pupil, dark limbal ring
        g = np.where(t > 0.86, 0.32, g)
        base[iris] *= g[:, None]
    scl = m == MAT_ID['sclera']
    if scl.any():
        base[scl] *= (0.70 + 0.30 * aux[scl])[:, None]           # the lid casts a soft shadow on the eyeball
    lid = m == MAT_ID['lid']
    if lid.any():
        base[lid] *= (0.78 + 0.22 * aux[lid])[:, None]          # crease
    # screen-space AO on the depth buffer
    occ = np.zeros((bh, bw), dtype=np.float32)
    if ao_k > 0:
        rad = max(2, int(0.022 * s))
        Zf = np.where(hit, Z, 1e9).astype(np.float32)
        cnt = 0
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            for rr in (rad, rad * 2):
                sh = np.roll(np.roll(Zf, dy * rr, axis=0), dx * rr, axis=1)
                d = Zf - sh                       # positive = neighbour closer to the camera (occluder)
                occ += np.clip((d - 0.004 * s) / (0.05 * s), 0, 1) * (1.0 if rr == rad else 0.6)
                cnt += 1.0 if rr == rad else 0.6
        occ /= cnt
    aoF = (1.0 - ao_k * np.clip(occ, 0, 1)[hit] * 1.4).clip(0.25, 1.0)
    # lights
    col = np.zeros_like(base)
    nup = -n[:, 1]
    amb = L['sky'][None, :] * (0.5 + 0.5 * nup)[:, None] + L['ground'][None, :] * (0.5 - 0.5 * nup)[:, None]
    col += base * amb * aoF[:, None]
    warm = np.array([1.0, 0.72, 0.55], dtype=np.float32)

    def add_light(Ld, Lc, Li, atten=None):
        nonlocal col
        ndl = np.einsum('ij,ij->i', n, Ld)
        diff = np.clip((ndl + wrap) / (1.0 + wrap), 0, 1)
        if atten is not None:
            diff = diff * atten
        d3 = diff[:, None] * Lc[None, :] * Li
        col += base * d3 * (0.65 + 0.35 * aoF)[:, None]
        # subsurface warmth on the terminator (skin, lips)
        term = np.clip(1.0 - np.abs(ndl - 0.05) / 0.35, 0, 1) * sss
        if atten is not None:
            term = term * atten
        col += base * (term * 0.22 * Li)[:, None] * warm[None, :] * Lc[None, :]
        hv = Ld + v
        hv /= np.linalg.norm(hv, axis=1, keepdims=True) + 1e-9
        ndh = np.clip(np.einsum('ij,ij->i', n, hv), 0, 1)
        sp = spec * np.power(ndh, gloss) * (ndl > -0.05) * Li
        if atten is not None:
            sp = sp * atten
        col += sp[:, None] * Lc[None, :]

    for key in ('key', 'fill'):
        Ld, Lc, Li = L[key]
        if Li <= 0:
            continue
        add_light(np.repeat(Ld[None, :].astype(np.float32), len(n), axis=0), Lc.astype(np.float32), Li)
    for pl in L.get('points', []):
        dvec = pl['pos'][None, :].astype(np.float32) - p
        dist = np.linalg.norm(dvec, axis=1) + 1e-6
        Ld = dvec / dist[:, None]
        att = 1.0 / (1.0 + (dist / pl['rad']) ** 2)
        add_light(Ld, pl['col'].astype(np.float32), pl['int'], atten=att.astype(np.float32))
    # rim (Fresnel toward the rim light)
    Ld, Lc, Li = L['rim']
    if Li > 0:
        fres = np.power(np.clip(1.0 - np.einsum('ij,ij->i', n, v), 0, 1), 2.6)
        back = np.clip(np.einsum('ij,ij->i', n, np.repeat(Ld[None, :], len(n), axis=0)) + 0.35, 0, 1)
        col += (fres * back * Li)[:, None] * Lc[None, :] * (0.35 + 0.65 * base.mean(axis=1, keepdims=True))
    # emissive
    col += base * emit[:, None] * 1.1
    col = np.clip(col, 0, 1) ** (1 / 2.2)
    rgb[hit] = col
    # ink: depth edges + silhouette
    if ink > 0:
        Zf = np.where(hit, Z, np.nan)
        edge = np.zeros((bh, bw), dtype=np.float32)
        for dx, dy in ((1, 0), (0, 1)):
            sh = np.roll(np.roll(Zf, dy, axis=0), dx, axis=1)
            d = np.abs(Zf - sh)
            e = np.where(np.isnan(d), 0.0, np.clip((d - 0.012 * s) / (0.02 * s), 0, 1))
            edge = np.maximum(edge, e)
        edge = np.maximum(edge, np.roll(np.roll(edge, -1, axis=0), -1, axis=1) * 0.0)
        rgb *= (1.0 - ink * 0.75 * edge)[:, :, None]
        # outline: 1 px dark halo under the silhouette
        Ai = Image.fromarray((A * 255).astype(np.uint8))
        dil = np.asarray(Ai.filter(ImageFilter.MaxFilter(3)), dtype=np.float32) / 255.0
        halo = np.clip(dil - A, 0, 1) * ink * 0.9
        inkcol = np.array([0.03, 0.03, 0.04], dtype=np.float32)
        # composite: figure over halo
        outA = A + halo * (1 - A)
        rgb = np.where(hit[:, :, None], rgb, inkcol[None, None, :])
        A = outA
    return rgb, A


def scene_lights(x, y, s, key_pt, key_col=(1.0, 0.93, 0.84), key_int=1.0, key_z=0.35, fill_col=(0.5, 0.6, 0.8),
                 fill_int=0.16, rim_dir=(0.4, -0.5, -0.75), rim_col=(0.8, 0.88, 1.0), rim_int=0.5,
                 sky=(0.14, 0.16, 0.22), ground=(0.05, 0.045, 0.045), points=()):
    """Lights from a practical at frame/canvas point `key_pt` for a figure anchored at (x, y) with scale s.
    The key direction is taken from the figure's chest toward the practical, slightly in front (key_z)."""
    cx, cy = x, y - 0.70 * s
    d = np.array([key_pt[0] - cx, key_pt[1] - cy, key_z * s], float)
    d = d / (np.linalg.norm(d) + 1e-9)
    fill = np.array([-d[0], -0.3, 0.8])
    return light_rig(key_dir=d, key_col=key_col, key_int=key_int, fill_dir=fill, fill_col=fill_col, fill_int=fill_int,
                     rim_dir=rim_dir, rim_col=rim_col, rim_int=rim_int, sky=sky, ground=ground, points=points)


def contact_shadows(layer, J, s, alpha=0.55, SS=1):
    """Soft ground-contact shadows under both feet (frame-scale RGBA layer, joints in layer px)."""
    from PIL import ImageDraw
    sh = Image.new('L', layer.size, 0)
    d = ImageDraw.Draw(sh)
    for k in ('ftl', 'ftr'):
        fx, fy = J[k]
        fy += 0.05 * s
        d.ellipse([fx - 0.085 * s, fy - 0.022 * s, fx + 0.085 * s, fy + 0.022 * s], fill=int(255 * alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(0.012 * s + 2))
    dark = Image.new('RGBA', layer.size, (4, 4, 6, 255))
    dark.putalpha(sh)
    layer.alpha_composite(dark)


def floor_shadow(layer, x, y, s, pose, direction=(0.0, 1.0), length=0.55, alpha=0.45, blur=6, **kw):
    """Cast shadow on the floor: the figure's silhouette squashed along `direction` from the feet (frame layer)."""
    can = Image.new('RGBA', layer.size, (0, 0, 0, 0))
    L = light_rig()
    render(can, x, y, s, pose, L, silhouette=True, ink=0.0, ao=0.0, **kw)
    a = can.split()[3]
    # squash: map every point (px, py) → feet + (px - x, (py - y) * length) sheared along direction
    W_, H_ = layer.size
    dx, dy = direction
    sx = dx * length
    m = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    # affine: X' = X + sx*(Y - y) ... PIL uses inverse mapping; build it explicitly
    # forward: X' = X + sx*(Y - y); Y' = y + (Y - y)*dy*length  → inverse: Y = y + (Y' - y)/(dy*length); X = X' - sx*(Y - y)
    ky = dy * length if abs(dy * length) > 1e-6 else 1e-6
    inv = (1.0, -sx / ky, sx * y / ky - 0.0, 0.0, 1.0 / ky, y - y / ky)
    a2 = a.transform(a.size, Image.AFFINE, inv, resample=Image.BILINEAR)
    a2 = a2.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha))
    dark = Image.new('RGBA', layer.size, (3, 3, 5, 255))
    dark.putalpha(a2)
    layer.alpha_composite(dark)


def render_window(can, box, s, pose, lights, focus='hctr', focus_off=(0.0, 0.0), autocenter=False, **kw):
    """Close-up: render the figure at scale s so that joint `focus` (plus an offset in units of s) lands in the
    centre of `box` = (x0, y0, x1, y1) on the canvas; only that window is rendered. autocenter=True re-centres on
    the rendered pixels' bounding box (two passes; use for hands / feet whose extent is pose dependent)."""
    _, J0, _ = solve(0.0, 0.0, s, pose, kw.get('flip', False), kw.get('rot', 0.0), kw.get('anchor', 'feet'))
    cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
    fx, fy = J0[focus]
    x = cx - fx - focus_off[0] * s
    y = cy - fy - focus_off[1] * s
    if autocenter:
        probe = Image.new('RGBA', can.size, (0, 0, 0, 0))
        big = (box[0] - (box[2] - box[0]), box[1] - (box[3] - box[1]), box[2] + (box[2] - box[0]), box[3] + (box[3] - box[1]))
        big = (max(0, big[0]), max(0, big[1]), min(can.size[0], big[2]), min(can.size[1], big[3]))
        grp = {'har': 'hand_r', 'hal': 'hand_l', 'ftr': 'foot_r', 'ftl': 'foot_l', 'hctr': 'head'}.get(focus)
        render(probe, x, y, s, pose, lights, clip=big, ink=0.0, ao=0.0, only=grp,
               **{k: v for k, v in kw.items() if k not in ('ink', 'ao', 'only')})
        a = np.asarray(probe.split()[3])
        ys, xs = np.where(a > 8)
        if len(xs):
            bx, by = (xs.min() + xs.max()) / 2.0, (ys.min() + ys.max()) / 2.0
            x += cx - bx
            y += cy - by
    return render(can, x, y, s, pose, lights, clip=box, **kw)


# ─────────────────────────────────────────────── convenience: a figure drawn at frame scale via a 2× canvas
def person(frame_layer, x, y, s, pose, lights, clip=None, SS=2, **kw):
    """Render into an RGBA frame-scale layer using a 2× cropped canvas (drop-in for world.person)."""
    cw, ch = int(s * 1.9) * SS, int(s * 1.9) * SS          # covers lying / sitting / hip-anchored figures
    ox, oy = int(x - s * 0.95), int(y - s * 1.2)
    can = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    L = _scale_lights(lights, ox, oy, SS)
    J, ex = render(can, (x - ox) * SS, (y - oy) * SS, s * SS, pose, L, **kw)
    small = can.resize((cw // SS, ch // SS), Image.LANCZOS)
    if clip is not None:
        m = Image.new('L', small.size, 0)
        from PIL import ImageDraw
        ImageDraw.Draw(m).rectangle([clip[0] - ox, clip[1] - oy, clip[2] - ox, clip[3] - oy], fill=255)
        small.putalpha(Image.fromarray(np.minimum(np.asarray(m), np.asarray(small.split()[3]))))
    frame_layer.alpha_composite(small, dest=(max(0, ox), max(0, oy)), source=(max(0, -ox), max(0, -oy)))
    Jf = {k: ((v[0] / SS) + ox, (v[1] / SS) + oy) for k, v in J.items()}
    hc, hr = ex['head']
    ex['head'] = (((hc[0] / SS) + ox, (hc[1] / SS) + oy), hr / SS)
    return Jf, ex


def _scale_lights(L, ox, oy, SS):
    """Point lights are given in FIGURE space already (relative to the anchor), so only the radius scales."""
    L2 = dict(L)
    pts = []
    for pl in L.get('points', []):
        pts.append(dict(pos=pl['pos'] * SS, col=pl['col'], int=pl['int'], rad=pl['rad'] * SS))
    L2['points'] = pts
    return L2


if __name__ == '__main__':
    import time
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build', 'hero3d', 'test.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    W, H = 1200, 1400
    can = Image.new('RGBA', (W, H), (22, 22, 26, 255))
    t0 = time.time()
    L = light_rig()
    pose = Hm.p_stand(0.0, weight=0.4)
    J, ex = render(can, 350, 1300, 1150, pose, L, expr='calm', look=(0.2, 0.1))
    pose2 = dict(pose, yaw=40, head_t=-20)
    J, ex = render(can, 850, 1300, 1150, pose2, L, expr='resolve', hands=('fist', 'relax'))
    print('render %.2fs' % (time.time() - t0))
    can.convert('RGB').save(out, quality=92)
    print(out)
