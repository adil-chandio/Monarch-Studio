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
from PIL import Image, ImageChops, ImageDraw, ImageFilter

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
HAND = (41, 36, 31)
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
    hand_r=0.040, shoe_l=0.082, shoe_h=0.040,
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
# ───────────────────────────────────────────── 3D kinematics
# Body space: x = screen right, y = DOWN, z = TOWARD THE CAMERA.
# Origin is the hip centre. Everything is solved in 3D and then projected,
# which is what separates a real figure from a paper doll: a limb that swings
# forward actually comes toward the lens, grows, and occludes the torso.

def _rz(a, v):
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2])


def _ry(a, v):
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c)


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _dirv(abd, swing):
    """Unit limb direction. abd = frontal abduction (deg, + toward +x).
    swing = sagittal swing (deg, + = forward, toward the camera)."""
    a, w = math.radians(abd), math.radians(swing)
    return (math.cos(w) * math.sin(a), math.cos(w) * math.cos(a), math.sin(w))


def _skeleton(pose, s, sgn):
    """Full 3D joint solve. Returns a dict of body-space points."""
    g = pose.get
    R = math.radians
    lean = R(g('lean', 0) * sgn)
    twist = R(g('twist', 0) * sgn)
    pelv = R(g('pelvis', 0) * sgn)
    tilt = R(g('tilt', 0) * sgn)
    sway = g('sway', 0.0) * s * sgn          # pelvis lateral weight shift

    HIPY = 0.0
    shy = -(P['shoulder'] - P['hip']) * s
    nky = -(P['neck'] - P['hip']) * s
    hby = -(P['head_b'] - P['hip']) * s
    hcy = -(P['head_c'] - P['hip']) * s

    hipc = (sway, HIPY, 0.0)
    spine = _rz(lean, (0.0, shy, 0.0))
    shoc = _add(hipc, spine)
    nek = _add(hipc, _rz(lean, (0.0, nky, 0.0)))
    hpiv = _add(hipc, _rz(lean, (0.0, hby, 0.0)))

    hd_y = R(g('head_t', 0) * sgn)           # yaw, turns the head in depth
    hd_z = R(g('head', 0) * sgn)             # roll/tilt in the picture plane
    hvec = _rz(lean + hd_z, _ry(hd_y, (0.0, hcy - hby, 0.0)))
    hctr = _add(hpiv, hvec)

    sw, hw = P['sh_w'] * s, P['hip_w'] * s
    rise = g('sh_up', 0.0) * s               # shrug
    shl = _add(shoc, _rz(lean, _ry(twist, (-sw, -rise, 0.0))))
    shr = _add(shoc, _rz(lean, _ry(twist, (sw, -rise, 0.0))))
    hpl = _add(hipc, _rz(tilt, _ry(pelv, (-hw, 0.0, 0.0))))
    hpr = _add(hipc, _rz(tilt, _ry(pelv, (hw, 0.0, 0.0))))

    au, af = P['arm_u'] * s, P['arm_l'] * s
    lu, lf = P['leg_u'] * s, P['leg_l'] * s

    def arm(root, abd, swing, eflex, eabd):
        d1 = _dirv(abd * sgn, swing)
        j = _add(root, (d1[0] * au, d1[1] * au, d1[2] * au))
        # the elbow only ever flexes FORWARD — a human elbow cannot hyperextend
        d2 = _dirv((abd + eabd) * sgn, swing + max(0.0, eflex))
        e = _add(j, (d2[0] * af, d2[1] * af, d2[2] * af))
        return j, e

    def leg(root, abd, swing, kflex):
        d1 = _dirv(abd * sgn, swing)
        j = _add(root, (d1[0] * lu, d1[1] * lu, d1[2] * lu))
        # the knee only ever flexes BACKWARD
        d2 = _dirv(abd * sgn, swing - max(0.0, kflex))
        e = _add(j, (d2[0] * lf, d2[1] * lf, d2[2] * lf))
        return j, e

    ell, hal = arm(shl, g('al', -14), g('az_l', 0), g('ef_l', 8), g('el', -5))
    elr, har = arm(shr, g('ar', 14), g('az_r', 0), g('ef_r', 8), g('er', 5))
    knl, ftl = leg(hpl, g('ll', -4), g('lz_l', 0), g('kl', 2))
    knr, ftr = leg(hpr, g('lr', 4), g('lz_r', 0), g('kr', 2))

    out = dict(hipc=hipc, shoc=shoc, nek=nek, hpiv=hpiv, hctr=hctr,
                shl=shl, shr=shr, hpl=hpl, hpr=hpr,
                ell=ell, hal=hal, elr=elr, har=har,
                knl=knl, ftl=ftl, knr=knr, ftr=ftr)
    yaw = R(g('yaw', 0) * sgn)
    if abs(yaw) > 1e-6:
        for k2, v in out.items():
            out[k2] = _ry(yaw, v)
    out['lean'] = lean
    out['hd_a'] = lean + hd_z
    out['yaw'] = yaw
    return out


def _draw_figure(d, x, y, s, pose, expr='neutral', p=1.0, look=(0, 0), blink=0.0,
                 flip=False, shirt=SHIRT, pants=PANTS, hair=HAIR, alpha=None,
                 face=True):
    """Solve the skeleton in 3D, project it, then paint back-to-front.

    Groups (arm / leg / torso / head) each get their own two-pass silhouette so
    there are no seams WITHIN a limb, and the groups are composited in depth
    order so a limb in front of the chest gets its own contour against it.
    """
    ow = max(2.0, OW * s)
    sgn = -1 if flip else 1
    K = _skeleton(pose, s, sgn)

    # ── perspective projection -------------------------------------------------
    F = 4.2 * s                      # long lens: depth reads, nothing distorts
    ox, oy = x, y - P['hip'] * s

    def PR(v):
        k = F / (F - v[2])
        return (ox + v[0] * k, oy + v[1] * k), k

    J, KS = {}, {}
    for key, v in K.items():
        if isinstance(v, tuple) and len(v) == 3:
            J[key], KS[key] = PR(v)
        else:
            J[key] = v

    # ── stand the figure on y --------------------------------------------------
    sole = max(J['ftl'][1] + P['ankle'] * s * KS['ftl'],
               J['ftr'][1] + P['ankle'] * s * KS['ftr'])
    dy = y - sole
    for key in list(J):
        if isinstance(J[key], tuple) and len(J[key]) == 2:
            J[key] = (J[key][0], J[key][1] + dy)

    lean = K['lean']
    hrx = P['head_rx'] * s * KS['hctr']
    hry = P['head_ry'] * s * KS['hctr']

    def warm(c, f=1.0):
        """Subsurface warmth. A head lit by one spec highlight on flat white
        reads as plastic; real skin bleeds warm where the light wraps."""
        return (min(255, int(c[0] + 7 * f)), min(255, int(c[1] + 2 * f)),
                max(0, int(c[2] - 9 * f)))

    def depth(c, z):
        """Aerial perspective: limbs behind the body sit back, limbs in front pop."""
        k = 1.0 + 0.26 * (z / s)
        return tuple(min(255, max(0, int(v * k))) for v in c)

    def cap(a, b, ra, rb):
        return _capsule(J[a], J[b], ra, rb)

    au0 = P['arm_r0'] * s
    au1 = P['arm_r1'] * s
    lu0 = P['leg_r0'] * s
    lu1 = P['leg_r1'] * s
    hrr = P['hand_r'] * s

    # ── foot roll from the shin's sagittal angle ------------------------------
    ROLL = {}
    for side, sg, kf in (('l', 'lz_l', 'kl'), ('r', 'lz_r', 'kr')):
        shin = pose.get(sg, 0) - max(0.0, pose.get(kf, 0))
        ROLL[side] = math.radians(max(-26, min(26, shin * .62))) * sgn

    def shoe(ft, side, roll, k):
        """Sneaker. The heel sits BEHIND the ankle, opposite the toe — using
        abs() here is what put the heel on the same side as the toe and made
        one foot read as reversed."""
        fx, fy = ft
        T = sgn * side * .063 * s * k
        gy = fy + P['ankle'] * s * k
        h = .034 * s * k
        pts = [(fx - T * .44, fy - h * .55), (fx - T * .30, fy - h * 1.00),
               (fx + T * .26, fy - h * 1.10), (fx + T * .92, fy - h * .15),
               (fx + T * 1.05, gy - h * .50), (fx + T * .98, gy),
               (fx - T * .48, gy), (fx - T * .56, gy - h * .50)]
        if abs(roll) < 1e-4:
            return pts
        c, sn = math.cos(roll), math.sin(roll)
        return [(fx + (px - fx) * c - (py - fy) * sn,
                 fy + (px - fx) * sn + (py - fy) * c) for px, py in pts]

    # ── groups, each tagged with its depth ------------------------------------
    CREASE = []
    groups = []

    for side, sh, el, ha in (('l', 'shl', 'ell', 'hal'), ('r', 'shr', 'elr', 'har')):
        z = (K[el][2] + K[ha][2]) * .5
        ks, ke, kh = KS[sh], KS[el], KS[ha]
        g = [('circ', (J[sh], au0 * 1.05 * ks, au0 * 1.05 * ks), depth(shirt, K[sh][2])),
             ('poly', cap(sh, el, au0 * ks, au0 * .88 * ke), depth(shirt, K[el][2])),
             ('poly', cap(el, ha, au0 * .80 * ke, au1 * kh), depth(shirt, K[ha][2]))]
        fa = math.atan2(J[ha][1] - J[el][1], J[ha][0] - J[el][0])
        hp, hc = _hand_parts(J[ha], fa, hrr * kh, pose.get('h' + side, 'relax'),
                             -1 if side == 'l' else 1)
        g += [(t, dd, depth(HAND, K[ha][2])) for t, dd, _ in hp]
        CREASE += [(c0, c1, K[ha][2]) for c0, c1 in hc]
        groups.append((z, g, ('arm', side)))

    for side, hp_, kn, ft in (('l', 'hpl', 'knl', 'ftl'), ('r', 'hpr', 'knr', 'ftr')):
        z = (K[kn][2] + K[ft][2]) * .5
        kh_, kk, kf = KS[hp_], KS[kn], KS[ft]
        g = [('poly', cap(hp_, kn, lu0 * kh_, lu0 * .86 * kk), depth(pants, K[kn][2])),
             ('circ', (J[kn], lu0 * .85 * kk, lu0 * .85 * kk), depth(pants, K[kn][2])),
             ('poly', cap(kn, ft, lu0 * .80 * kk, lu1 * kf), depth(pants, K[ft][2])),
             ('poly', shoe(J[ft], -1 if side == 'l' else 1, ROLL[side], kf),
              depth(SHOE, K[ft][2]))]
        groups.append((z, g, ('leg', side)))

    def B(fy, lat):
        """A point on the torso surface, in projected screen space."""
        u = (fy - P['hip']) / (P['shoulder'] - P['hip'])
        bx = J['hipc'][0] + (J['shoc'][0] - J['hipc'][0]) * u
        by = J['hipc'][1] + (J['shoc'][1] - J['hipc'][1]) * u
        return (bx + lat * math.cos(lean), by + lat * math.sin(lean))

    tws = P['sh_w'] * s * .98 * (1.0 + 0.020 * pose.get('_br', 0.0))
    hem = P['hip'] - 0.030
    torso = [B(.728, -tws), B(.740, -tws * .40), B(.740, tws * .40), B(.728, tws),
             B(.668, tws * 1.02), B(.590, tws * .80), B(.520, tws * .76),
             B(hem, tws * .86), B(hem, -tws * .86), B(.520, -tws * .76),
             B(.590, -tws * .80), B(.668, -tws * 1.02)]
    head = _superell(J['hctr'][0], J['hctr'][1], hrx, hry, 2.7, 44)

    def paint(g):
        for kind, data, col in g:
            if kind == 'poly':
                d.line(list(data) + [data[0]], fill=OUTLINE,
                       width=max(1, int(ow * 2)), joint='curve')
                d.polygon(data, fill=OUTLINE)
            else:
                (cx, cy), rx, ry = data
                d.ellipse([cx - rx - ow, cy - ry - ow, cx + rx + ow, cy + ry + ow],
                          fill=OUTLINE)
        for kind, data, col in g:
            if kind == 'poly':
                d.polygon(data, fill=col)
            else:
                (cx, cy), rx, ry = data
                d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col)

    def cuff(side):
        """Rolled-sleeve hem, drawn perpendicular to ITS OWN forearm."""
        e = J['ell'] if side == 'l' else J['elr']
        h = J['hal'] if side == 'l' else J['har']
        kk = KS['ell'] if side == 'l' else KS['elr']
        vx, vy = h[0] - e[0], h[1] - e[1]
        L = math.hypot(vx, vy) or 1e-6
        px, py = -vy / L, vx / L
        cx, cy = e[0] + vx * .30, e[1] + vy * .30
        r = au0 * .82 * kk
        d.line([(cx - px * r, cy - py * r), (cx + px * r, cy + py * r)],
               fill=SHIRT_D, width=max(2, int(ow * .70)))

    limbs = sorted(groups, key=lambda t: t[0])
    for z, g, tag in limbs:
        if z < 0:
            paint(g)
            if tag[0] == 'arm':
                cuff(tag[1])
    nk = _capsule(J['shoc'], J['hpiv'], P['head_rx'] * s * .50 * KS['shoc'],
                  P['head_rx'] * s * .44 * KS['hpiv'])
    paint([('poly', torso, shirt), ('poly', nk, (228, 228, 224))])
    _collar(d, J['nek'], J['shoc'], J['shl'], J['shr'], hrx, ow, shirt, lean)
    paint([('poly', head, FACE)])
    hx, hy = J['hctr']
    for q in range(7):                      # warm wrap across the lower skull
        f = (q + 1) / 7.0
        ry_ = hry * (0.30 + 0.62 * f)
        d.ellipse([hx - hrx * (0.94 - 0.10 * f), hy + hry * 0.26 - ry_ * 0.30,
                   hx + hrx * (0.94 - 0.10 * f), hy + hry * 0.26 + ry_ * 0.52],
                  fill=warm(FACE, f * 1.5) + (16,))
    _hair(d, J['hctr'][0], J['hctr'][1], hrx, hry, K['hd_a'], ow, hair,
          pose.get('_hv', 0.0))
    for z, g, tag in limbs:
        if z >= 0:
            paint(g)
            if tag[0] == 'arm':
                cuff(tag[1])

    hemL, hemR = B(hem + .012, -tws * .84), B(hem + .012, tws * .84)
    d.line([hemL, hemR], fill=SHIRT_D, width=max(2, int(ow * .62)))
    for side, hp_, kn in (('l', 'hpl', 'knl'), ('r', 'hpr', 'knr')):
        kf = pose.get('kl' if side == 'l' else 'kr', 0)
        if kf > 14:
            kk = KS[kn]
            vx, vy = J[kn][0] - J[hp_][0], J[kn][1] - J[hp_][1]
            L_ = math.hypot(vx, vy) or 1e-6
            px_, py_ = -vy / L_, vx / L_
            r_ = lu0 * .62 * kk * min(1.0, kf / 48)
            d.line([(J[kn][0] - px_ * r_, J[kn][1] - py_ * r_),
                    (J[kn][0] + px_ * r_, J[kn][1] + py_ * r_)],
                   fill=(38, 40, 46), width=max(1, int(ow * .50)))
    for side, sh_, el_ in (('l', 'shl', 'ell'), ('r', 'shr', 'elr')):
        ef = pose.get('ef_l' if side == 'l' else 'ef_r', 0)
        if ef > 35:
            ke = KS[el_]
            vx, vy = J[el_][0] - J[sh_][0], J[el_][1] - J[sh_][1]
            L_ = math.hypot(vx, vy) or 1e-6
            ux, uy = vx / L_, vy / L_
            for q in (.30, .52):
                bx, by = J[el_][0] - ux * au0 * q * 2.1, J[el_][1] - uy * au0 * q * 2.1
                d.line([(bx - uy * au0 * .40 * ke, by + ux * au0 * .40 * ke),
                        (bx + uy * au0 * .18 * ke, by - ux * au0 * .18 * ke)],
                       fill=SHIRT_D, width=max(1, int(ow * .42)))

    for c0, c1, cz in CREASE:
        d.line([c0, c1], fill=depth((132, 122, 112), cz), width=max(2, int(ow * .58)))
    for side, ft in (('l', 'ftl'), ('r', 'ftr')):
        sp = shoe(J[ft], -1 if side == 'l' else 1, ROLL[side], KS[ft])
        d.line([sp[5], sp[6]], fill=SOLE, width=max(2, int(ow * 2.1)))
        d.line([sp[4], sp[7]], fill=(214, 214, 209), width=max(1, int(ow * .70)))
        d.line([sp[2], sp[3]], fill=(206, 206, 200), width=max(1, int(ow * .60)))
        mx = ((sp[1][0] + sp[2][0]) * .5, (sp[1][1] + sp[2][1]) * .5)
        d.line([sp[1], mx], fill=(198, 198, 192), width=max(1, int(ow * .55)))
    if face:
        tw_ = math.sin(K['yaw'] + math.radians(pose.get('head_t', 0) * sgn))
        _face(d, J['hctr'][0], J['hctr'][1], hrx, hry, K['hd_a'], expr, ow,
              (look[0] + tw_ * 0.34, look[1]), blink, s)

    return dict(head=J['hctr'], hrx=hrx, hry=hry, ang=K['hd_a'],
                hip=J['hipc'], neck=J['nek'], sh_l=J['shl'], sh_r=J['shr'],
                hand_l=J['hal'], hand_r=J['har'], elbow_l=J['ell'],
                elbow_r=J['elr'], foot_l=J['ftl'], foot_r=J['ftr'],
                knee_l=J['knl'], knee_r=J['knr'], s=s, ow=ow)


# ───────────────────────────────────────────── articulated hand
def _hand_parts(hj, ang, r, style, side):
    """A hand with real fingers.

    The palm and the four fingers are ONE scalloped polygon, so the outline
    pass strokes the notches between the fingers instead of welding them shut
    (which is what happens if each finger is its own overlapping circle).
    The thumb is a second piece because a thumb genuinely does separate.
    Returns (parts, creases) — creases are drawn after the fills.
    """
    ca, sa = math.cos(ang), math.sin(ang)

    def L(u, v):
        return (hj[0] + ca * u * r - sa * v * r * side,
                hj[1] + sa * u * r + ca * v * r * side)

    def arc(cu, cv, rr, a0, a1, n=9):
        return [L(cu + rr * math.cos(a0 + (a1 - a0) * k / n),
                  cv + rr * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]

    parts, cre = [], []

    if style == 'fist':
        pal = [L(-0.05 + 0.98 * math.cos(t * math.pi / 11),
                 0.92 * math.sin(t * math.pi / 11)) for t in range(22)]
        parts.append(('poly', pal, HAND))
        parts.append(('poly', _capsule(L(0.20, 0.64), L(0.78, 1.00), 0.30 * r, 0.24 * r), HAND))
        for i in range(3):
            v = -0.46 + i * 0.44
            cre.append((L(0.30, v), L(0.80, v)))
        return parts, cre

    # finger layout: (centre across, tip reach, radius)
    if style == 'point':
        FG = [(-0.60, 2.15, 0.21)]
        fold = [(-0.10, 0.74, 0.30), (0.26, 0.70, 0.29), (0.60, 0.62, 0.27)]
    elif style == 'open':
        FG = [(-0.78, 1.14, 0.21), (-0.28, 1.32, 0.22), (0.22, 1.26, 0.21), (0.68, 1.02, 0.20)]
        fold = []
    else:                                   # 'relax'
        FG = [(-0.66, 1.00, 0.21), (-0.24, 1.16, 0.22), (0.18, 1.10, 0.21), (0.58, 0.92, 0.20)]
        fold = []

    pts = [L(-1.00, -0.42), L(-0.76, -0.76), L(-0.30, -0.90)]
    for i, (vc, ut, fr) in enumerate(FG):
        pts += arc(ut - fr, vc, fr, -math.pi / 2, math.pi / 2, 9)
        if i < len(FG) - 1:
            nv = (vc + FG[i + 1][0]) / 2
            depth = min(ut, FG[i + 1][1]) - fr - 0.30
            pts.append(L(depth, nv))
            cre.append((L(depth - 0.12, nv), L(ut - fr * 0.2, nv)))
    for vc, ut, fr in fold:                 # curled fingers behind a pointing index
        pts += arc(ut - fr, vc, fr, -math.pi / 2, math.pi / 2, 7)
    pts += [L(0.46, 1.00), L(-0.10, 1.04), L(-0.62, 0.86), L(-0.98, 0.36)]
    parts.append(('poly', pts, HAND))
    parts.append(('poly', _capsule(L(-0.02, 0.66), L(0.62, 1.22), 0.30 * r, 0.24 * r), HAND))
    cre.append((L(-0.16, 0.50), L(0.30, 0.86)))
    return parts, cre


# ───────────────────────────────────────────── soft-body 3D shading
_GRAD = {}


def _form_gradient(w, h):
    """Cached diagonal form gradient: lit upper-left, falling to lower-right."""
    k = (w, h)
    if k not in _GRAD:
        import numpy as _np
        yy, xx = _np.mgrid[0:h, 0:w].astype(_np.float32)
        g = (xx / max(w - 1, 1)) * 0.55 + (yy / max(h - 1, 1)) * 0.45
        _GRAD[k] = Image.fromarray((_np.clip(g, 0, 1) * 255).astype('uint8'), 'L')
    return _GRAD[k]


def _shade(tile, s, joints, off):
    """Turn a flat silhouette into a soft-shaded solid.

    Everything is masked by an ERODED alpha, so the crisp ink contour drawn by
    the silhouette pass is never touched. Shading lives strictly inside the
    outline — which is exactly how a hand-shaded vector character works.

      1. bevel — alpha minus itself offset: lit edge upper-left, dark lower-right
      2. form  — a broad diagonal ramp giving every limb a lit and a shaded side
      3. AO    — soft dark pools in the creases (neck, armpits, hips, joints)
      4. spec  — one small highlight on the skull
    """
    a = tile.getchannel('A')
    w, h = tile.size
    ow = max(2.0, OW * s)
    inner = a.filter(ImageFilter.GaussianBlur(ow * 1.15)).point(
        lambda v: 255 if v > 248 else 0)
    inner = ImageChops.multiply(inner, a)

    D = max(2, int(s * 0.020))
    R = max(1.6, s * 0.020)
    hi = ImageChops.multiply(
        ImageChops.subtract(a, ImageChops.offset(a, D, D)).filter(ImageFilter.GaussianBlur(R)),
        inner)
    sh = ImageChops.multiply(
        ImageChops.subtract(a, ImageChops.offset(a, -D, -D)).filter(ImageFilter.GaussianBlur(R)),
        inner)

    ao = Image.new('L', (w, h), 0)
    ad = ImageDraw.Draw(ao)
    for key, rad in (('neck', .062), ('sh_l', .050), ('sh_r', .050), ('hip', .058),
                     ('elbow_l', .032), ('elbow_r', .032),
                     ('knee_l', .036), ('knee_r', .036)):
        jx, jy = joints[key]
        jx -= off[0]; jy -= off[1]
        rr = rad * s
        ad.ellipse([jx - rr, jy - rr, jx + rr, jy + rr], fill=170)
    ao = ImageChops.multiply(ao.filter(ImageFilter.GaussianBlur(s * 0.032)), inner)

    out = tile.copy()
    black = Image.new('RGBA', (w, h), (14, 13, 12, 255))
    warm = Image.new('RGBA', (w, h), (255, 250, 236, 255))
    white = Image.new('RGBA', (w, h), (255, 255, 255, 255))

    form = ImageChops.multiply(_form_gradient(w, h), inner)
    out.paste(black, (0, 0), form.point(lambda v: int(v * 0.115)))
    out.paste(black, (0, 0), ao.point(lambda v: int(v * 0.26)))
    out.paste(black, (0, 0), sh.point(lambda v: int(v * 0.30)))
    out.paste(warm, (0, 0), hi.point(lambda v: int(v * 0.33)))

    hx, hy = joints['head']
    hx -= off[0]; hy -= off[1]
    hrx, hry = joints['hrx'], joints['hry']
    sp = Image.new('L', (w, h), 0)
    ImageDraw.Draw(sp).ellipse([hx - hrx * .70, hy - hry * .74,
                                hx - hrx * .10, hy - hry * .16], fill=74)
    sp = ImageChops.multiply(sp.filter(ImageFilter.GaussianBlur(s * 0.024)), inner)
    out.paste(white, (0, 0), sp)
    return out


# ───────────────────────────────────────────── public entry point
def toon(d, x, y, s, pose, expr='neutral', p=1.0, look=(0, 0), blink=0.0,
         flip=False, shirt=SHIRT, pants=PANTS, hair=HAIR, alpha=None, shade=True):
    """Draw the character standing on (x, y) with total height s.

    With shade=True the figure is rendered into its own tile so the whole body
    can be lit as one solid, then composited. Returns the joint dict.
    """
    if not shade:
        return _draw_figure(d, x, y, s, pose, expr, p, look, blink, flip,
                            shirt, pants, hair, alpha)

    ox, oy = int(x - 0.86 * s), int(y - 1.26 * s)
    tw, th = int(1.72 * s) + 4, int(1.44 * s) + 4
    tile = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile, 'RGBA')
    j = _draw_figure(td, x - ox, y - oy, s, pose, expr, p, look, blink, flip,
                     shirt, pants, hair, alpha, face=False)
    jw = dict(j)
    for k in ('head', 'hip', 'neck', 'sh_l', 'sh_r', 'hand_l', 'hand_r',
              'elbow_l', 'elbow_r', 'foot_l', 'foot_r', 'knee_l', 'knee_r'):
        jw[k] = (j[k][0] + ox, j[k][1] + oy)
    tile = _shade(tile, s, j, (0, 0))

    base = getattr(d, '_image', None)
    if base is None:
        base = d.im
    if base.mode == 'RGBA':
        base.alpha_composite(tile, (ox, oy))
    else:
        base.paste(tile, (ox, oy), tile)
    _face(d, jw['head'][0], jw['head'][1], j['hrx'], j['hry'], j['ang'],
          expr, max(2.0, OW * s), look, blink, s)
    return jw


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


def _soles(d, L, shoe_fn, ow, ROLL):
    for k in ('l', 'r'):
        hj, kj, fj = L[k]
        sh = shoe_fn(fj, kj, -1 if k == 'l' else 1, ROLL[k])
        d.line([sh[5], sh[4]], fill=SOLE, width=max(2, int(ow * 1.9)))


def _hair(d, cx, cy, rx, ry, ang, ow, col, hv=0.0):
    """Swept spiky fringe sitting on the skull, tallest on the left."""
    def R(vx, vy):
        c, s = math.cos(ang), math.sin(ang)
        return (cx + vx * c - vy * s, cy + vx * s + vy * c)

    spikes = [(-1.05, .08), (-1.16, -.46), (-1.08, -1.04), (-0.84, -0.90),
              (-0.56, -1.30), (-0.22, -1.02), (0.18, -1.32), (0.54, -1.00),
              (0.88, -1.14), (1.06, -0.54), (1.06, .04)]
    inner = [(0.90, -0.22), (0.56, -0.44), (0.16, -0.54), (-0.26, -0.50),
             (-0.66, -0.36), (-0.90, -0.16)]
    # inertia: only the free tips (py < -0.6) swing, the roots stay planted
    k = max(-0.42, min(0.42, hv * 0.055))
    pts = [R(px * rx + (k * rx if py < -0.6 else 0.0), py * ry) for px, py in spikes] + \
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
    """Contrapposto. A standing human never stands square: the weight sits on
    one leg, that hip rides UP, the shoulders counter-tilt, and the spine makes
    a shallow S. The weight drifts to the other leg every few seconds."""
    w = math.sin(t * 0.46)                      # slow weight drift, ~6.8 s cycle
    br = math.sin(t * 2.05)
    sup = w                                     # +1 = weight on the right leg
    return dict(yaw=14, 
        sway=0.016 * sup, tilt=-3.4 * sup, pelvis=2.0 * sup,
        lean=1.3 * sup + math.sin(t * .61) * .5, twist=-2.6 * sup,
        head=-1.1 * sup + math.sin(t * .83) * 1.4, head_t=3.0 * sup,
        al=-10 + 1.2 * br, az_l=5 - 2 * sup, el=-4, ef_l=13 + 2 * br,
        ar=10 - 1.2 * br, az_r=5 + 2 * sup, er=4, ef_r=13 - 2 * br,
        ll=-4 + 1.6 * sup, lz_l=-1.5 * sup, kl=2.5 + 4.5 * max(0, -sup),
        lr=4 + 1.6 * sup, lz_r=1.5 * sup, kr=2.5 + 4.5 * max(0, sup),
        hl='relax', hr='relax', _br=br)


def p_walk(t):
    """A real two-beat gait, solved in depth rather than sideways.

    The legs swing through the SAGITTAL plane (toward and away from the lens),
    the pelvis rotates with the leading leg, the shoulders counter-rotate, the
    arms swing opposite their own leg, the knee flexes only during swing, and
    the body rises over the passing leg and drops onto the plant.
    """
    ph = t * 6.6
    sw = math.sin(ph)

    def knee(q):
        return 7 + 52 * max(0.0, math.sin(q + 2.0)) ** 1.6

    return dict(yaw=27, 
        lean=2.4, twist=-7.5 * sw, pelvis=7.5 * sw, tilt=2.6 * math.sin(ph + 1.6),
        sway=0.011 * math.sin(ph + 1.6),
        head=-1.6 * sw, head_t=2.4 * sw,
        al=-12, az_l=-26 * sw, el=-4, ef_l=26 + 16 * max(0, -sw),
        ar=12, az_r=26 * sw, er=4, ef_r=26 + 16 * max(0, sw),
        ll=-4.5, lz_l=27 * sw, kl=knee(ph),
        lr=4.5, lz_r=-27 * sw, kr=knee(ph + math.pi),
        hl='relax', hr='relax',
        _bob=0.020 * abs(math.cos(ph)) - 0.008, _br=math.sin(t * 2.05))


def p_sad(t):
    """Collapsed posture: head down, shoulders rolled forward and dropped,
    chest closed, weight dead centre."""
    return dict(yaw=13, lean=5.5, twist=0, sh_up=-0.012, sway=0.004 * math.sin(t * .5),
                head=12 + math.sin(t * 1.25) * 1.3, head_t=-2,
                al=-9, az_l=9, el=-3, ef_l=17,
                ar=9, az_r=9, er=3, ef_r=17,
                ll=-4, lz_l=0, kl=4, lr=4, lz_r=0, kr=4,
                hl='relax', hr='relax', _br=math.sin(t * 1.7))


def p_think(t):
    """Hand to chin, the other arm folded across to support that elbow —
    the one pose everybody reads instantly as thinking."""
    o = math.sin(t * .9)
    return dict(yaw=20, lean=2.6, twist=7, tilt=-2.6, sway=0.012, pelvis=3,
                head=8 + o * 1.4, head_t=7,
                al=26, az_l=30, el=18, ef_l=70,
                ar=14, az_r=64 + o * 2, er=-4, ef_r=112,
                ll=-3, lz_l=-2, kl=3, lr=5, lz_r=2, kr=7,
                hl='relax', hr='fist', _br=math.sin(t * 1.9))


def p_type(t):
    """Standing at a laptop. Forearms come FORWARD out of the screen, which is
    only expressible because the elbows flex in depth."""
    o = math.sin(t * 13) * 4
    return dict(yaw=12, lean=7, twist=0, head=7 + math.sin(t * 2.4) * 1.2,
                al=-16, az_l=30 + o, el=12, ef_l=58,
                ar=16, az_r=30 - o, er=-12, ef_r=58,
                ll=-5, lz_l=-3, kl=4, lr=5, lz_r=3, kr=4,
                hl='open', hr='open', _br=math.sin(t * 2.2))


def p_sit_type(t):
    """Seated: thighs swing forward, shins drop vertically under the knee."""
    o = math.sin(t * 13) * 4
    return dict(yaw=18, lean=8, head=7 + math.sin(t * 2.4) * 1.2,
                al=-15, az_l=32 + o, el=10, ef_l=54,
                ar=15, az_r=32 - o, er=-10, ef_r=54,
                ll=-6, lz_l=76, kl=76, lr=6, lz_r=80, kr=80,
                hl='open', hr='open', _br=math.sin(t * 2.2))


def p_present(t):
    """Open offer. Arms abduct AND come forward, palms up, chest open."""
    j = math.sin(t * 2.6) * 3
    return dict(yaw=4, lean=0, twist=0, sh_up=0.004, head=-2, head_t=0,
                al=-68 - j, az_l=26, el=-14, ef_l=24,
                ar=68 + j, az_r=26, er=14, ef_r=24,
                ll=-6, lz_l=0, kl=3, lr=6, lz_r=0, kr=3,
                hl='open', hr='open', _br=math.sin(t * 1.9))


def p_point(t, up=False, right=True):
    """Pointing reads best when the arm also comes toward the lens."""
    j = math.sin(t * 4.2) * 2.4
    a = (150 if up else 88) + j
    if right:
        return dict(yaw=16, lean=-2, twist=-6, tilt=-2.5, sway=0.010, head=-3, head_t=-5,
                    al=-12, az_l=6, el=-4, ef_l=14,
                    ar=a, az_r=18, er=4, ef_r=6,
                    ll=-4, lz_l=0, kl=3, lr=5, lz_r=0, kr=5,
                    hl='relax', hr='point', _br=math.sin(t * 1.9))
    return dict(yaw=-16, lean=2, twist=6, tilt=2.5, sway=-0.010, head=3, head_t=5,
                al=-a, az_l=18, el=-4, ef_l=6,
                ar=12, az_r=6, er=4, ef_r=14,
                ll=-5, lz_l=0, kl=5, lr=4, lz_r=0, kr=3,
                hl='point', hr='relax', _br=math.sin(t * 1.9))


def p_shake(t):
    """A handshake happens IN DEPTH — the arm reaches out of the frame toward
    the other person, which a flat rig simply cannot show."""
    j = math.sin(t * 7.5)
    return dict(yaw=23, lean=3.5, twist=-9, tilt=-2.4, sway=0.011, pelvis=4,
                head=3, head_t=-6,
                al=-11, az_l=8, el=-4, ef_l=15,
                ar=16, az_r=74 + j * 5, er=2, ef_r=34 - j * 6,
                ll=-4, lz_l=-4, kl=3, lr=5, lz_r=6, kr=6,
                hl='relax', hr='open', _br=math.sin(t * 2.1))


def p_cheer(t):
    a = math.sin(t * 6.0)
    return dict(yaw=6, lean=0, twist=a * 3, sh_up=0.010, head=-5 - a * 2, head_t=a * 4,
                al=-158 - a * 9, az_l=14, el=-8, ef_l=10,
                ar=158 + a * 9, az_r=14, er=8, ef_r=10,
                ll=-9, lz_l=0, kl=4, lr=9, lz_r=0, kr=4,
                hl='open', hr='open',
                _bob=0.012 * abs(a), _br=math.sin(t * 2.4))


def p_dance(t):
    """Weight bounces side to side, hips lead, shoulders follow a beat late,
    arms alternate in depth."""
    ph = t * 6.2
    sw = math.sin(ph)
    return dict(yaw=10 * sw, sway=0.020 * sw, tilt=-4.5 * sw, pelvis=9 * sw,
                lean=3.5 * sw, twist=-8 * math.sin(ph - 0.6),
                head=4.5 * math.sin(ph - 0.9), head_t=7 * sw, sh_up=0.006,
                al=-118 - 30 * sw, az_l=16 + 26 * sw, el=-16, ef_l=22,
                ar=118 + 30 * math.sin(ph + 2.0), az_r=16 - 26 * sw, er=16, ef_r=22,
                ll=-9 - 7 * sw, lz_l=5 * sw, kl=6 + 10 * max(0, sw),
                lr=9 - 7 * sw, lz_r=-5 * sw, kr=6 + 10 * max(0, -sw),
                hl='open', hr='open',
                _bob=0.016 * abs(math.cos(ph)), _br=math.sin(t * 2.4))


def p_shrug(t):
    """Shoulders UP, elbows pinned to the ribs, forearms rotated out, palms up."""
    return dict(yaw=5, lean=0, sh_up=0.030, head=2, head_t=0,
                al=-30, az_l=16, el=-58, ef_l=66,
                ar=30, az_r=16, er=58, ef_r=66,
                ll=-5, lz_l=0, kl=3, lr=5, lz_r=0, kr=3,
                hl='open', hr='open', _br=math.sin(t * 1.8))


def p_hold(t):
    """Both hands forward, offering. Depth does the work, not abduction."""
    o = math.sin(t * 1.7) * 2
    return dict(yaw=10, lean=1, head=2, head_t=0,
                al=-20, az_l=38 + o, el=14, ef_l=50,
                ar=20, az_r=38 - o, er=-14, ef_r=50,
                ll=-5, lz_l=0, kl=3, lr=5, lz_r=0, kr=3,
                hl='open', hr='open', _br=math.sin(t * 2.0))


POSES = dict(idle=p_idle, walk=p_walk, sad=p_sad, think=p_think, type=p_type,
             sit_type=p_sit_type, present=p_present, shake=p_shake,
             cheer=p_cheer, dance=p_dance, shrug=p_shrug, hold=p_hold)

