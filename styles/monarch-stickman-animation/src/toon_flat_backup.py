"""
toon.py — 2D CARTOON CHARACTER (filled vector, thick outline)
==============================================================
Matches the reference sheet: white rounded head, dark swept hair, black dot
eyes, collared shirt with rolled sleeves, charcoal trousers, sneakers, and
solid black mitten hands.

HOW THE OUTLINE WORKS
---------------------
Every body part is registered as a shape, then the figure is drawn in TWO
passes over the same list:
    pass 1 — every shape grown by `ow` px, all in OUTLINE colour  -> silhouette
    pass 2 — every shape at true size in its fill colour           -> flats
That is the only way to get one unbroken contour with no seams where limbs
meet. Drawing each part with its own outline would show every joint.

The pose contract is unchanged (lean / head / al,el / ar,er / ll,kl / lr,kr)
so every pose_* generator keeps working.
"""
import math, sys
sys.path.insert(0, '/home/user/src')
from PIL import Image, ImageDraw

# ───────────────────────────────────────────── palette (character is CONSTANT)
OUTLINE = (26, 24, 22)
FACE    = (255, 255, 255)
HAIR    = (74, 56, 46)
HAIR_HI = (104, 80, 64)
SHIRT   = (221, 221, 215)
SHIRT_D = (196, 196, 189)
PANTS   = (52, 54, 61)
PANTS_D = (40, 42, 48)
SHOE    = (242, 242, 238)
SOLE    = (88, 90, 97)
HAND    = (24, 22, 20)
MOUTH_I = (58, 40, 40)

NAME = 'TOON'
OW = 0.0105          # outline width as a fraction of total height s

# ───────────────────────────────────────────── proportions (fraction of s, 0 = feet)
P = dict(
    foot=0.000, ankle=0.052, knee=0.245, hip=0.452,
    shoulder=0.722, neck=0.742, head_b=0.752, head_c=0.878, head_top=1.004,
    head_rx=0.104, head_ry=0.126,
    sh_w=0.100, hip_w=0.055,
    arm_u=0.168, arm_l=0.158,
    leg_u=0.207, leg_l=0.193,
    arm_r0=0.023, arm_r1=0.018, leg_r0=0.032, leg_r1=0.024,
    hand_r=0.033, shoe_l=0.082, shoe_h=0.040,
)

# ───────────────────────────────────────────── expressions
# brow : (inner_dy, outer_dy) in head-ry units, None = no brows drawn
# eye  : 'dot' | 'wide' | 'happy' | 'closed' | 'squint'
# mouth: 'smile' | 'grin' | 'open' | 'flat' | 'frown' | 'o' | 'wavy' | 'smirk'
EXPR = {
    'neutral':   dict(brow=None,         eye='dot',    mouth='flat',  mw=.46),
    'happy':     dict(brow=None,         eye='happy',  mouth='smile', mw=.58),
    'grin':      dict(brow=None,         eye='happy',  mouth='grin',  mw=.66),
    'talk':      dict(brow=None,         eye='dot',    mouth='open',  mw=.40),
    'sad':       dict(brow=(.30, -.10),  eye='squint', mouth='frown', mw=.50),
    'worried':   dict(brow=(.26, -.06),  eye='wide',   mouth='wavy',  mw=.46),
    'shock':     dict(brow=(-.18, -.22), eye='wide',   mouth='o',     mw=.40),
    'think':     dict(brow=(-.04, .14),  eye='squint', mouth='smirk', mw=.38),
    'focus':     dict(brow=(-.20, .10),  eye='dot',    mouth='flat',  mw=.34),
    'determined':dict(brow=(-.24, .12),  eye='dot',    mouth='smirk', mw=.44),
    'angry':     dict(brow=(-.30, .16),  eye='dot',    mouth='frown', mw=.52),
    'proud':     dict(brow=(-.10, .06),  eye='dot',    mouth='smile', mw=.52),
}


# ───────────────────────────────────────────── geometry helpers
def _rot(a, v):
    ca, sa = math.cos(a), math.sin(a)
    return (v[0] * ca - v[1] * sa, v[0] * sa + v[1] * ca)


def _capsule(a, b, r0, r1, segs=10):
    """Tapered capsule a(r0) -> b(r1) as one simple, non-self-intersecting loop."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1e-6
    ang = math.atan2(dy, dx)
    pts = []
    for i in range(segs + 1):                      # cap at a, sweeping behind it
        t = ang + math.pi / 2 + math.pi * i / segs
        pts.append((a[0] + r0 * math.cos(t), a[1] + r0 * math.sin(t)))
    for i in range(segs + 1):                      # cap at b, sweeping in front
        t = ang - math.pi / 2 + math.pi * i / segs
        pts.append((b[0] + r1 * math.cos(t), b[1] + r1 * math.sin(t)))
    return pts


def _superell(cx, cy, rx, ry, n=2.7, segs=48):
    pts = []
    for i in range(segs):
        t = 2 * math.pi * i / segs
        c, s = math.cos(t), math.sin(t)
        pts.append((cx + rx * math.copysign(abs(c) ** (2.0 / n), c),
                    cy + ry * math.copysign(abs(s) ** (2.0 / n), s)))
    return pts


def _grow(pts, g):
    """Push a convex-ish polygon outward from its centroid by ~g px."""
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    out = []
    for x, y in pts:
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy) or 1e-6
        out.append((x + dx / L * g, y + dy / L * g))
    return out


# ───────────────────────────────────────────── the figure
def toon(d, x, y, s, pose, expr='neutral', p=1.0, look=(0, 0), blink=0.0,
         flip=False, shirt=SHIRT, pants=PANTS, hair=HAIR, alpha=None):
    """Draw the character standing on (x, y) with total height s.
    Returns a dict of joint positions in screen space."""
    ow = max(2.0, OW * s)
    lean = math.radians(pose.get('lean', 0))
    hd_a = math.radians(pose.get('head', 0))
    sgn = -1 if flip else 1

    def U(fy):                                   # body-axis point at height fy
        return (x + _rot(lean, (0, -(fy - P['hip']) * s))[0],
                y - P['hip'] * s + _rot(lean, (0, -(fy - P['hip']) * s))[1])

    hip = (x, y - P['hip'] * s)
    sho = U(P['shoulder'])
    nek = U(P['neck'])
    hc0 = U(P['head_c'])
    pv = U(P['head_b'])
    hv = _rot(hd_a, (hc0[0] - pv[0], hc0[1] - pv[1]))
    hcx, hcy = pv[0] + hv[0], pv[1] + hv[1]
    hrx, hry = P['head_rx'] * s, P['head_ry'] * s

    def limb(root, a1, a2, l1, l2):
        a1 = math.radians(a1 * sgn) + lean
        a2 = math.radians(a2 * sgn) + a1
        j = (root[0] + l1 * math.sin(a1), root[1] + l1 * math.cos(a1))
        e = (j[0] + l2 * math.sin(a2), j[1] + l2 * math.cos(a2))
        return j, e

    shl = (sho[0] - P['sh_w'] * s * math.cos(lean), sho[1] - P['sh_w'] * s * math.sin(lean))
    shr = (sho[0] + P['sh_w'] * s * math.cos(lean), sho[1] + P['sh_w'] * s * math.sin(lean))
    hpl = (hip[0] - P['hip_w'] * s * math.cos(lean), hip[1] - P['hip_w'] * s * math.sin(lean))
    hpr = (hip[0] + P['hip_w'] * s * math.cos(lean), hip[1] + P['hip_w'] * s * math.sin(lean))

    ell, hal = limb(shl, pose.get('al', 18), pose.get('el', 10), P['arm_u'] * s, P['arm_l'] * s)
    elr, har = limb(shr, pose.get('ar', -18), pose.get('er', -10), P['arm_u'] * s, P['arm_l'] * s)
    knl, ftl = limb(hpl, pose.get('ll', 8), pose.get('kl', 2), P['leg_u'] * s, P['leg_l'] * s)
    knr, ftr = limb(hpr, pose.get('lr', -8), pose.get('kr', 2), P['leg_u'] * s, P['leg_l'] * s)

    au0, au1 = P['arm_r0'] * s, P['arm_r1'] * s
    lu0, lu1 = P['leg_r0'] * s, P['leg_r1'] * s
    hrr = P['hand_r'] * s

    def B(fy, lat):
        q = U(fy)
        return (q[0] + lat * math.cos(lean), q[1] + lat * math.sin(lean))

    sw, hw = P['sh_w'] * s, P['hip_w'] * s
    hem = P['hip'] - 0.030
    tw = sw * .98
    torso = [B(.728, -tw), B(.740, -sw * .40), B(.740, sw * .40), B(.728, tw),
             B(.668, tw * 1.02), B(.590, tw * .80), B(.520, tw * .76),
             B(hem, tw * .86), B(hem, -tw * .86), B(.520, -tw * .76),
             B(.590, -tw * .80), B(.668, -tw * 1.02)]

    head = _superell(hcx, hcy, hrx, hry, 2.7, 44)

    def shoe(ft, kn, side=1):
        """Sneaker: heel behind the ankle, toe out, sole flat on the ground."""
        fx, fy = ft
        T = sgn * side * .076 * s
        gy = fy + P['ankle'] * s          # ground under this foot
        return [(fx - abs(T) * .40, fy - .030 * s), (fx + T * .26, fy - .040 * s),
                (fx + T * .92, fy - .004 * s), (fx + T * 1.03, gy - .022 * s),
                (fx + T * .96, gy), (fx - abs(T) * .44, gy),
                (fx - abs(T) * .52, fy + .014 * s)]

    # ── part list, back to front
    parts = []
    back, front = ('l', 'r') if not flip else ('r', 'l')
    A = dict(l=(shl, ell, hal), r=(shr, elr, har))
    L = dict(l=(hpl, knl, ftl), r=(hpr, knr, ftr))

    def add_arm(k):
        sj, ej, hj = A[k]
        parts.append(('poly', _capsule(sj, ej, au0, au0 * .88), shirt))
        parts.append(('poly', _capsule(ej, hj, au0 * .80, au1), shirt))
        parts.append(('circ', (hj, hrr, hrr), HAND))

    def add_leg(k):
        hj, kj, fj = L[k]
        parts.append(('poly', _capsule(hj, kj, lu0, lu0 * .86), pants))
        parts.append(('poly', _capsule(kj, fj, lu0 * .80, lu1), pants))
        parts.append(('poly', shoe(fj, kj, -1 if k == 'l' else 1), SHOE))

    add_arm(back); add_leg(back)
    parts.append(('poly', torso, shirt))
    add_leg(front)
    parts.append(('circ', ((hcx, hcy - hry * .02), hrx, hry), None))   # neck-cover placeholder
    parts.pop()
    parts.append(('poly', head, FACE))
    add_arm(front)

    lay = Image.new('RGBA', d.im.size if hasattr(d, 'im') else (1, 1), (0, 0, 0, 0))

    # ── PASS 1 — grown silhouette
    def draw_part(dd, kind, data, col, grow=0.0):
        if kind == 'poly':
            if grow > 0:
                dd.line(list(data) + [data[0]], fill=col, width=max(1, int(grow * 2)), joint='curve')
            dd.polygon(data, fill=col)
        else:
            (cx, cy), rx, ry = data
            dd.ellipse([cx - rx - grow, cy - ry - grow, cx + rx + grow, cy + ry + grow], fill=col)

    for kind, data, _c in parts:
        draw_part(d, kind, data, OUTLINE, ow)
    for kind, data, c in parts:
        draw_part(d, kind, data, c, 0.0)

    # ── details on top of the flats
    _collar(d, nek, sho, shl, shr, hrx, ow, shirt, lean)
    _sleeves(d, A, back, front, au0, ow, SHIRT_D)
    _soles(d, L, shoe, ow)
    _hair(d, hcx, hcy, hrx, hry, hd_a + lean, ow, hair)
    _face(d, hcx, hcy, hrx, hry, hd_a + lean, expr, ow, look, blink, s)

    return dict(head=(hcx, hcy), hrx=hrx, hry=hry, hip=hip, neck=nek,
                sh_l=shl, sh_r=shr, hand_l=hal, hand_r=har,
                elbow_l=ell, elbow_r=elr, foot_l=ftl, foot_r=ftr,
                knee_l=knl, knee_r=knr, s=s, ow=ow)


# ───────────────────────────────────────────── details
def _collar(d, nek, sho, shl, shr, hrx, ow, shirt, lean):
    cw = hrx * .62
    nx, ny = nek
    v = [(nx - cw, ny - ow * .3), (nx, ny + cw * 1.15), (nx + cw, ny - ow * .3)]
    d.line(v + [v[0]], fill=OUTLINE, width=int(ow * .9), joint='curve')
    for sx in (-1, 1):
        lap = [(nx + sx * cw * .14, ny + cw * .62), (nx + sx * cw * 1.02, ny - cw * .16),
               (nx + sx * cw * .86, ny + cw * .46)]
        d.polygon(lap, fill=shirt, outline=OUTLINE, width=max(1, int(ow * .72)))
    # buttons
    for i in range(3):
        bx, by = nx, ny + cw * (1.5 + i * .95)
        r = max(1.4, ow * .40)
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=OUTLINE)


def _sleeves(d, A, back, front, au0, ow, col):
    for k in (back, front):
        sj, ej, hj = A[k]
        dx, dy = hj[0] - ej[0], hj[1] - ej[1]
        L = math.hypot(dx, dy) or 1e-6
        ux, uy = dx / L, dy / L
        px, py = -uy, ux
        r = au0 * .86
        c = (ej[0] + ux * L * .06, ej[1] + uy * L * .06)
        d.line([(c[0] - px * r, c[1] - py * r), (c[0] + px * r, c[1] + py * r)],
               fill=OUTLINE, width=max(1, int(ow * .8)))


def _soles(d, L, shoe_fn, ow):
    for k in ('l', 'r'):
        hj, kj, fj = L[k]
        sh = shoe_fn(fj, kj, -1 if k == 'l' else 1)
        d.line([sh[5], sh[4]], fill=SOLE, width=max(2, int(ow * 1.9)))


def _hair(d, cx, cy, rx, ry, ang, ow, col):
    """Swept spiky fringe sitting on the skull, tallest on the left."""
    def R(vx, vy):
        c, s = math.cos(ang), math.sin(ang)
        return (cx + vx * c - vy * s, cy + vx * s + vy * c)

    spikes = [(-1.05, .08), (-1.16, -.46), (-1.08, -1.04), (-0.84, -0.90),
              (-0.56, -1.30), (-0.22, -1.02), (0.18, -1.32), (0.54, -1.00),
              (0.88, -1.14), (1.06, -0.54), (1.06, .04)]
    inner = [(0.90, -0.22), (0.56, -0.44), (0.16, -0.54), (-0.26, -0.50),
             (-0.66, -0.36), (-0.90, -0.16)]
    pts = [R(px * rx, py * ry) for px, py in spikes] + \
          [R(px * rx, py * ry) for px, py in inner]
    d.polygon(pts, fill=col, outline=OUTLINE, width=max(2, int(ow * .95)))
    # highlight streak
    hl = [R(-.56 * rx, -.70 * ry), R(-.18 * rx, -.92 * ry), R(.10 * rx, -.74 * ry),
          R(-.22 * rx, -.62 * ry)]
    d.polygon(hl, fill=HAIR_HI)


def _face(d, cx, cy, rx, ry, ang, expr, ow, look, blink, s):
    e = EXPR.get(expr, EXPR['neutral'])

    def R(vx, vy):
        c, sn = math.cos(ang), math.sin(ang)
        return (cx + vx * c - vy * sn, cy + vx * sn + vy * c)

    ex, ey = rx * .40, -ry * .06
    erx, ery = rx * .145, ry * .185
    bl = max(0.0, min(1.0, blink))
    sq = max(.10, 1 - bl)
    shape = e['eye']
    if bl > .80:
        shape = 'closed'
    lw = max(2, int(ow * .92))

    for sx in (-1, 1):
        px, py = ex * sx + look[0] * rx * .14, ey + look[1] * ry * .14
        if shape == 'closed':
            a = R(px - erx * 1.15, py); b = R(px, py + ery * .42); c = R(px + erx * 1.15, py)
            d.line([a, b, c], fill=OUTLINE, width=lw, joint='curve')
        elif shape == 'happy':
            a = R(px - erx * 1.2, py + ery * .30); b = R(px, py - ery * .62)
            c = R(px + erx * 1.2, py + ery * .30)
            d.line([a, b, c], fill=OUTLINE, width=lw, joint='curve')
        else:
            k = 1.34 if shape == 'wide' else (.72 if shape == 'squint' else 1.0)
            w_, h_ = erx * k, ery * k * sq
            pts = _superell(0, 0, w_, h_, 2.1, 20)
            d.polygon([R(px + a0, py + b0) for a0, b0 in pts], fill=OUTLINE)
            if shape == 'wide':
                gx, gy = R(px + w_ * .34, py - h_ * .36)
                gr = max(1.2, w_ * .30)
                d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=FACE)

    if e['brow'] is not None:
        inn, out = e['brow']
        for sx in (-1, 1):
            by = -ry * .46
            a = R(sx * rx * .18, by + inn * ry)
            b = R(sx * rx * .66, by + out * ry)
            d.line([a, b], fill=OUTLINE, width=max(2, int(ow * 1.15)))

    m = e['mouth']
    mw = rx * e['mw']
    my = ry * .44
    mlw = max(2, int(ow * .95))
    if m == 'smile':
        d.line([R(-mw, my - mw * .18), R(-mw * .45, my + mw * .34), R(mw * .45, my + mw * .34),
                R(mw, my - mw * .18)], fill=OUTLINE, width=mlw, joint='curve')
    elif m == 'grin':
        pts = [R(-mw, my - mw * .10), R(-mw * .5, my + mw * .55), R(mw * .5, my + mw * .55),
               R(mw, my - mw * .10)]
        d.polygon(pts + [R(mw * .5, my - mw * .10), R(-mw * .5, my - mw * .10)], fill=MOUTH_I)
        d.line(pts, fill=OUTLINE, width=mlw, joint='curve')
        d.line([R(-mw, my - mw * .10), R(mw, my - mw * .10)], fill=OUTLINE, width=mlw)
    elif m == 'open':
        pts = _superell(0, 0, mw * .52, mw * .46, 2.2, 18)
        d.polygon([R(a0, my + b0) for a0, b0 in pts], fill=MOUTH_I,
                  outline=OUTLINE, width=mlw)
    elif m == 'o':
        pts = _superell(0, 0, mw * .40, mw * .54, 2.1, 18)
        d.polygon([R(a0, my + b0) for a0, b0 in pts], fill=MOUTH_I,
                  outline=OUTLINE, width=mlw)
    elif m == 'frown':
        d.line([R(-mw * .9, my + mw * .30), R(-mw * .4, my - mw * .22),
                R(mw * .4, my - mw * .22), R(mw * .9, my + mw * .30)],
               fill=OUTLINE, width=mlw, joint='curve')
    elif m == 'wavy':
        d.line([R(-mw * .9, my), R(-mw * .3, my - mw * .26), R(mw * .3, my + mw * .22),
                R(mw * .9, my - mw * .12)], fill=OUTLINE, width=mlw, joint='curve')
    elif m == 'smirk':
        d.line([R(-mw * .55, my + mw * .04), R(mw * .25, my + mw * .10),
                R(mw * .78, my - mw * .26)], fill=OUTLINE, width=mlw, joint='curve')
    else:   # flat
        d.line([R(-mw * .72, my), R(mw * .72, my)], fill=OUTLINE, width=mlw)


def blink_at(t, period=3.4, dur=0.15):
    ph = (t + 0.9) % period
    if ph < dur:
        return 1.0
    if ph < dur + .09:
        return 1.0 - (ph - dur) / .09
    return 0.0


# ───────────────────────────────────────────── pose library
# World angles in degrees. 0 = straight down. POSITIVE = toward screen +x.
# Left limbs therefore hang at a NEGATIVE angle, right limbs at a positive one.
def p_idle(t):
    b = math.sin(t * 2.1) * 2.5
    return dict(lean=math.sin(t * .62) * 1.2, head=math.sin(t * .83) * 2.0,
                al=-11 - b, el=-5, ar=11 + b, er=5, ll=-4, kl=-1, lr=4, kr=1)


def p_walk(t):
    ph = t * 7.2
    sw = math.sin(ph)
    return dict(lean=2, head=1.5 * sw,
                al=-10 + 24 * sw, el=-8, ar=10 + 24 * sw, er=8,
                ll=-22 * sw, kl=max(0, 24 * math.sin(ph + 1.1)),
                lr=22 * sw, kr=-max(0, 24 * math.sin(ph + 4.2)))


def p_sad(t):
    return dict(lean=5, head=11 + math.sin(t * 1.3) * 1.5,
                al=-8, el=-4, ar=8, er=4, ll=-4, kl=0, lr=4, kr=0)


def p_think(t):
    return dict(lean=3, head=8 + math.sin(t * .9) * 1.5,
                al=-10, el=-6, ar=34, er=102, ll=-4, kl=0, lr=5, kr=0)


def p_type(t):
    """standing at a laptop — both hands forward to the keyboard"""
    o = math.sin(t * 12) * 5
    return dict(lean=8, head=6 + math.sin(t * 2.4) * 1.5,
                al=26 + o, el=30, ar=-24 + o, er=-28,
                ll=-5, kl=-1, lr=5, kr=1)


def p_sit_type(t):
    """seated at a desk — thighs forward, shins down, hands on the keys"""
    o = math.sin(t * 12) * 5
    return dict(lean=8, head=6 + math.sin(t * 2.4) * 1.5,
                al=28 + o, el=28, ar=-26 + o, er=-26,
                ll=74, kl=-72, lr=80, kr=-78)


def p_point(t, up=False, right=True):
    j = math.sin(t * 4.6) * 3
    a = (152 if up else 96) + j
    if right:
        return dict(lean=-2, head=-3, al=-11, el=-5, ar=a, er=6, ll=-4, kl=0, lr=5, kr=0)
    return dict(lean=2, head=3, al=-a, el=-6, ar=11, er=5, ll=-5, kl=0, lr=4, kr=0)


def p_present(t):
    j = math.sin(t * 3.2) * 4
    return dict(lean=0, head=-2, al=-74 - j, el=-26, ar=74 + j, er=26,
                ll=-6, kl=0, lr=6, kr=0)


def p_shake(t):
    j = math.sin(t * 8.5) * 7
    return dict(lean=4, head=3, al=-10, el=-5, ar=72 + j, er=14, ll=-5, kl=0, lr=5, kr=0)


def p_cheer(t):
    a = math.sin(t * 6.2) * 11
    return dict(lean=0, head=-5, al=-163 - a, el=-10, ar=163 + a, er=10,
                ll=-9, kl=0, lr=9, kr=0)


def p_dance(t):
    ph = t * 6.6
    return dict(lean=math.sin(ph) * 7, head=math.sin(ph) * 6,
                al=-120 - 34 * math.sin(ph), el=-24,
                ar=120 + 34 * math.sin(ph + 2.1), er=24,
                ll=-10 - 10 * math.sin(ph), kl=0, lr=10 + 10 * math.sin(ph + 3), kr=0)


def p_shrug(t):
    return dict(lean=0, head=2, al=-104, el=-64, ar=104, er=64, ll=-5, kl=0, lr=5, kr=0)


def p_hold(t):
    """both hands forward, as if holding / offering something"""
    return dict(lean=0, head=2, al=26, el=44, ar=-24, er=-42, ll=-5, kl=0, lr=5, kr=0)


POSES = dict(idle=p_idle, walk=p_walk, sad=p_sad, think=p_think, type=p_type,
             sit_type=p_sit_type,
             present=p_present, shake=p_shake, cheer=p_cheer, dance=p_dance,
             shrug=p_shrug, hold=p_hold)
