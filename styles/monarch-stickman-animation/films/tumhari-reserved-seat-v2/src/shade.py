"""
shade.py — "SHADE" · the hooded black-suit hero (the user's personal main character)
=====================================================================================
Built ON the toon.py 3D rig: the same `_skeleton` solve, the same pose contract
(lean / yaw / head / al,el / ar,er / ll,kl / lr,kr / hl,hr …), the same long-lens
projection and the same two-pass silhouette.  Every pose generator written for
the stickman (toon.p_*, power.p_*) drives this character unchanged.

What is different — and why
---------------------------
* GARMENTS   notch-lapel open blazer, turtleneck, trousers, gloves, dress shoes,
             knit hood.  Six near-black tones, 10–18 levels apart: a black
             character reads as 3D only through tonal steps + light, never line.
* FACE       a void.  Two glowing wedge eyes (outer end thick and high, inner tip
             low — the reference's sly angle) and a thin crescent smirk, both
             bloomed.  Expressions are carried ONLY by the eyes and the mouth.
* LIGHTING   toon.py darkens a white body; that does nothing on black cloth.
             Here: key rim (upper-left), fill rim (lower-right), a broad form lift
             on the lit side, AO pools, knit crackle on the hood, satin lapels,
             gloss on the shoes, and the eye-glow leaking onto the hood interior.
* OUTLINE    a mid-grey contour (not ink) so the silhouette still separates when
             the figure stands in front of the dark half of the split backdrop.

Public entry: shade(d, x, y, s, pose, expr, look, blink, flip) -> joint dict
             (same signature as toon.toon, drop-in for power.hero()).
"""
import math, sys
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter
sys.path.insert(0, '/home/user/src')
import toon as T
from toon import P, _skeleton, _capsule, _superell, _hand_parts

NAME = 'SHADE'

# ───────────────────────────────────────────── proportions (fraction of s, 0 = feet)
# Adult, dapper: head ≈ 1/5.2 of height (toon is 1/4), broad padded shoulders,
# long legs.  Swapped into toon.P for the duration of each solve so the shared
# _skeleton() solver drives this body without touching the stickman.
SP = dict(
    foot=0.000, ankle=0.052, knee=0.245, hip=0.452,
    shoulder=0.748, neck=0.772, head_b=0.784, head_c=0.878, head_top=0.972,
    head_rx=0.078, head_ry=0.094,
    sh_w=0.122, hip_w=0.060,
    arm_u=0.176, arm_l=0.166,
    leg_u=0.207, leg_l=0.193,
    arm_r0=0.026, arm_r1=0.020, leg_r0=0.034, leg_r1=0.026,
    hand_r=0.034, shoe_l=0.090, shoe_h=0.032,
)

# ───────────────────────────────────────────── palette (near-black steps)
VOID    = (6, 6, 8)          # inside the hood
TURTLE  = (15, 15, 18)       # matte turtleneck (darkest garment)
GLOVE   = (19, 19, 22)
TROUSER = (24, 24, 28)
JACKET  = (29, 29, 34)
LAPEL   = (37, 37, 43)       # satin facing
HOOD    = (46, 46, 52)       # knit
HOOD_HI = (74, 74, 82)
SHOE    = (16, 16, 19)
OUTL    = (58, 58, 66)       # contour — grey, so it survives on dark ground
SEAM    = (52, 52, 60)       # highlight lines (lapel edge, trouser crease)
GLOW    = (240, 244, 255)    # eyes / mouth
GLOW_T  = (176, 196, 255)    # bloom tint (cool, so paper never looks "lit")
GLOW_C  = (226, 236, 255)    # tight-bloom core (swapped with GLOW/GLOW_T for the red-eye beat)

OW = 0.0095                  # contour width as a fraction of s

# ───────────────────────────────────────────── expressions
# eye : 'sly' | 'wide' | 'squint' | 'happy' | 'closed' | 'angry' | 'soft'
# mouth: 'smirk' | 'grin' | 'smile' | 'flat' | 'o' | 'frown' | 'talk' | 'wavy'
# open: eye thickness multiplier · tilt: extra outer-up slant in degrees
EXPR = {
    'sly':        dict(eye='sly',    open=1.00, tilt=0,   mouth='smirk', glow=1.00),
    'neutral':    dict(eye='sly',    open=0.90, tilt=0,   mouth='flat',  glow=0.92),
    'happy':      dict(eye='happy',  open=1.00, tilt=0,   mouth='smile', glow=1.00),
    'grin':       dict(eye='happy',  open=1.00, tilt=0,   mouth='grin',  glow=1.10),
    'proud':      dict(eye='sly',    open=0.95, tilt=4,   mouth='smile', glow=1.05),
    'determined': dict(eye='squint', open=0.75, tilt=8,   mouth='smirk', glow=1.00),
    'focus':      dict(eye='squint', open=0.62, tilt=4,   mouth='flat',  glow=0.95),
    'think':      dict(eye='squint', open=0.70, tilt=-2,  mouth='smirk', glow=0.95),
    'angry':      dict(eye='angry',  open=0.85, tilt=14,  mouth='frown', glow=1.15),
    'talk':       dict(eye='sly',    open=0.95, tilt=0,   mouth='talk',  glow=1.00),
    'shock':      dict(eye='wide',   open=1.00, tilt=-6,  mouth='o',     glow=1.20),
    'worried':    dict(eye='soft',   open=0.80, tilt=-10, mouth='wavy',  glow=0.85),
    'sad':        dict(eye='soft',   open=0.60, tilt=-14, mouth='frown', glow=0.75),
    'calm':       dict(eye='closed', open=1.00, tilt=0,   mouth='flat',  glow=0.80),
    'calm_smile': dict(eye='closed', open=1.00, tilt=0,   mouth='smile', glow=0.90),
}


def _R(cx, cy, ang):
    c, s_ = math.cos(ang), math.sin(ang)
    return lambda vx, vy: (cx + vx * c - vy * s_, cy + vx * s_ + vy * c)


# ───────────────────────────────────────────── solve + project (toon contract)
def _solve(x, y, s, pose, flip):
    sgn = -1 if flip else 1
    _saved = T.P
    T.P = SP
    try:
        K = _skeleton(pose, s, sgn)
    finally:
        T.P = _saved
    Fl = 4.2 * s
    ox, oy = x, y - SP['hip'] * s

    def PR(v):
        k = Fl / (Fl - v[2])
        return (ox + v[0] * k, oy + v[1] * k), k

    J, KS = {}, {}
    for key, v in K.items():
        if isinstance(v, tuple) and len(v) == 3:
            J[key], KS[key] = PR(v)
        else:
            J[key] = v
    sole = max(J['ftl'][1] + SP['ankle'] * s * KS['ftl'],
               J['ftr'][1] + SP['ankle'] * s * KS['ftr'])
    dy = y - sole
    for key in list(J):
        if isinstance(J[key], tuple) and len(J[key]) == 2:
            J[key] = (J[key][0], J[key][1] + dy)
    return K, J, KS, sgn


def _hood_pts(R, hrx, hry, tw_=0.0):
    """Hood contour: a superellipse around the head, a soft peak at the top-back
    (index 36 = top), and the back of the hood pulled away from the face side."""
    raw = _superell(0, -hry * .08, hrx * 1.38, hry * 1.30, 2.5, 48)
    out = []
    back = -tw_ * hrx * .22
    for i, (a, b) in enumerate(raw):
        k = 1.0
        if 33 <= i <= 39:                                 # peak
            k = 1.0 + 0.16 * (1 - abs(i - 36) / 4.0)
        a2 = a + back * (1 if b < 0 else .4)
        out.append(R(a2, b * k if b < 0 else b))
    return out


# ───────────────────────────────────────────── body paint
def _draw_body(d, x, y, s, pose, flip, hood_mask_d=None, lapel_d=None):
    """Garments only (no face). Returns joints + geometry needed by the face."""
    ow = max(2.0, OW * s)
    K, J, KS, sgn = _solve(x, y, s, pose, flip)
    lean = K['lean']
    hrx = SP['head_rx'] * s * KS['hctr']
    hry = SP['head_ry'] * s * KS['hctr']

    def depth(c, z):
        k = 1.0 + 0.42 * (z / s)
        lift = 12.0 * (z / s)
        return tuple(int(max(0, min(255, v * k + lift))) for v in c)

    def cap(a, b, ra, rb):
        return _capsule(J[a], J[b], ra, rb)

    au0, au1 = SP['arm_r0'] * s * 1.06, SP['arm_r1'] * s * 1.04   # sleeves are fuller than skin
    lu0, lu1 = SP['leg_r0'] * s * 1.02, SP['leg_r1'] * s * 1.06   # trousers: straight leg
    hrr = SP['hand_r'] * s * .96

    ROLL = {}
    for side, sg, kf in (('l', 'lz_l', 'kl'), ('r', 'lz_r', 'kr')):
        shin = pose.get(sg, 0) - max(0.0, pose.get(kf, 0))
        ROLL[side] = math.radians(max(-26, min(26, shin * .62))) * sgn

    def shoe(ft, side, roll, k):
        """Dress shoe: lower and longer than the sneaker, slight heel."""
        fx, fy = ft
        Tt = sgn * side * .070 * s * k
        gy = fy + SP['ankle'] * s * k
        h = .028 * s * k
        pts = [(fx - Tt * .46, fy - h * .60), (fx - Tt * .30, fy - h * 1.00),
               (fx + Tt * .20, fy - h * 1.02), (fx + Tt * .90, fy - h * .30),
               (fx + Tt * 1.08, gy - h * .40), (fx + Tt * 1.02, gy),
               (fx - Tt * .50, gy), (fx - Tt * .58, gy - h * .55)]
        if abs(roll) < 1e-4:
            return pts
        c, sn = math.cos(roll), math.sin(roll)
        return [(fx + (px - fx) * c - (py - fy) * sn,
                 fy + (px - fx) * sn + (py - fy) * c) for px, py in pts]

    groups, CREASE, POCKET = [], [], []
    for side, sh, el, ha in (('l', 'shl', 'ell', 'hal'), ('r', 'shr', 'elr', 'har')):
        z = (K[el][2] + K[ha][2]) * .5
        ks, ke, kh = KS[sh], KS[el], KS[ha]
        style = pose.get('h' + side, 'relax')
        g = [('poly', cap(sh, el, au0 * ks, au0 * .90 * ke), depth(JACKET, K[el][2])),
             ('circn', (J[sh], au0 * 1.02 * ks, au0 * 1.02 * ks), depth(JACKET, K[sh][2])),
             ('poly', cap(el, ha, au0 * .84 * ke, au1 * kh), depth(JACKET, K[ha][2]))]
        if style == 'pocket':
            POCKET.append(side)
        else:
            fa = math.atan2(J[ha][1] - J[el][1], J[ha][0] - J[el][0])
            hp, hc = _hand_parts(J[ha], fa, hrr * kh, style, -1 if side == 'l' else 1)
            g += [(t_, dd, depth(GLOVE, K[ha][2])) for t_, dd, _ in hp]
            CREASE += [(c0, c1, K[ha][2]) for c0, c1 in hc]
        groups.append((z, g, ('arm', side)))

    for side, hp_, kn, ft in (('l', 'hpl', 'knl', 'ftl'), ('r', 'hpr', 'knr', 'ftr')):
        z = (K[kn][2] + K[ft][2]) * .5
        kh_, kk, kf = KS[hp_], KS[kn], KS[ft]
        g = [('poly', cap(hp_, kn, lu0 * kh_, lu0 * .90 * kk), depth(TROUSER, K[kn][2])),
             ('circ', (J[kn], lu0 * .88 * kk, lu0 * .88 * kk), depth(TROUSER, K[kn][2])),
             ('poly', cap(kn, ft, lu0 * .86 * kk, lu1 * kf), depth(TROUSER, K[ft][2])),
             ('poly', shoe(J[ft], -1 if side == 'l' else 1, ROLL[side], kf),
              depth(SHOE, K[ft][2]))]
        groups.append((z, g, ('leg', side)))

    def B(fy, lat):
        u = (fy - SP['hip']) / (SP['shoulder'] - SP['hip'])
        bx = J['hipc'][0] + (J['shoc'][0] - J['hipc'][0]) * u
        by = J['hipc'][1] + (J['shoc'][1] - J['hipc'][1]) * u
        return (bx + lat * math.cos(lean), by + lat * math.sin(lean))

    br = 1.0 + 0.018 * pose.get('_br', 0.0)
    tws = SP['sh_w'] * s * 1.10 * br                      # padded shoulder
    hem = SP['hip'] - 0.038                               # jacket covers the hips
    jacket = [B(.742, -tws * 1.00), B(.752, -tws * .34), B(.752, tws * .34), B(.742, tws * 1.00),
              B(.700, tws * 1.02), B(.600, tws * .84), B(.520, tws * .80),
              B(hem, tws * .92), B(hem, -tws * .92), B(.520, -tws * .80),
              B(.600, -tws * .84), B(.700, -tws * 1.02)]
    vtop = .742
    vpt = B(.552, 0.0)                                   # button point
    vee = [B(vtop, -tws * .30), B(vtop, tws * .30), vpt]
    hood_shawl = [B(.790, -tws * .50), B(.790, tws * .50), B(.726, tws * .34),
                  B(.690, tws * .10), B(.690, -tws * .10), B(.726, -tws * .34)]

    def lapel(sx):
        return [B(.746, sx * tws * .30), B(.708, sx * tws * .60), B(.692, sx * tws * .47),
                B(.655, sx * tws * .52), B(.552, sx * tws * .06), B(.610, sx * tws * .02)]

    def paint(g):
        for kind, data, col in g:
            if kind == 'poly':
                d.line(list(data) + [data[0]], fill=OUTL, width=max(1, int(ow * 2)), joint='curve')
                d.polygon(data, fill=OUTL)
            elif kind == 'circ':
                (cx, cy), rx, ry = data
                d.ellipse([cx - rx - ow, cy - ry - ow, cx + rx + ow, cy + ry + ow], fill=OUTL)
        for kind, data, col in g:
            if kind == 'poly':
                d.polygon(data, fill=col)
            else:                                        # 'circ' and 'circn' (no contour)
                (cx, cy), rx, ry = data
                d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col)

    def sleeve_buttons(side):
        e = J['ell'] if side == 'l' else J['elr']
        h = J['hal'] if side == 'l' else J['har']
        kk = KS['hal'] if side == 'l' else KS['har']
        vx, vy = h[0] - e[0], h[1] - e[1]
        L = math.hypot(vx, vy) or 1e-6
        ux, uy = vx / L, vy / L
        px, py = -uy, ux
        r = max(1.5, s * 0.0045 * kk)
        for q in (.80, .87):
            bx = e[0] + vx * q + px * au1 * .55 * kk
            by = e[1] + vy * q + py * au1 * .55 * kk
            d.ellipse([bx - r, by - r, bx + r, by + r], fill=(70, 70, 80))

    limbs = sorted(groups, key=lambda t_: t_[0])
    for z, g, tag in limbs:
        if z < 0:
            paint(g)
            if tag[0] == 'arm': sleeve_buttons(tag[1])
    # torso: jacket -> turtleneck V -> hood shawl -> lapels
    nk = _capsule(J['shoc'], J['hpiv'], hrx * .54, hrx * .50)
    paint([('poly', jacket, JACKET), ('poly', nk, TURTLE)])
    d.polygon(vee, fill=TURTLE)
    d.polygon(hood_shawl, fill=HOOD)
    if hood_mask_d is not None:
        hood_mask_d.polygon(hood_shawl, fill=255)
    for sx in (-1, 1):
        lp = lapel(sx)
        d.polygon(lp, fill=LAPEL)
        d.line([lp[4], lp[5], lp[0]], fill=(10, 10, 12), width=max(1, int(ow * .9)), joint='curve')
        d.line([lp[0], lp[1]], fill=SEAM, width=max(1, int(ow * .7)))
        d.line([lp[3], lp[4]], fill=SEAM, width=max(1, int(ow * .7)))
        if lapel_d is not None:
            lapel_d.polygon(lp, fill=255)
    # front edge + buttons + breast pocket
    d.line([vpt, B(hem + .004, tws * .06)], fill=SEAM, width=max(1, int(ow * .6)))
    for fy in (.548, .488):
        bx, by = B(fy, tws * .07)
        r = max(1.5, s * 0.006)
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=(78, 78, 88))
    d.line([B(.668, -tws * .70), B(.660, -tws * .40)], fill=SEAM, width=max(1, int(ow * .6)))
    for z, g, tag in limbs:
        if z >= 0:
            paint(g)
            if tag[0] == 'arm': sleeve_buttons(tag[1])
    # hand-in-pocket: the jacket's lower front covers the wrist
    for side in POCKET:
        sx = -1 if side == 'l' else 1
        flap = [B(.520, sx * tws * .10), B(.520, sx * tws * .80), B(hem, sx * tws * .92), B(hem, sx * tws * .10)]
        d.polygon(flap, fill=JACKET)
        d.line([flap[1], flap[2]], fill=OUTL, width=max(1, int(ow * 1.4)))
        d.line([flap[2], flap[3]], fill=OUTL, width=max(1, int(ow * 1.4)))
        d.line([B(.468, sx * tws * .34), B(.428, sx * tws * .62)], fill=SEAM, width=max(1, int(ow * .8)))
    # trouser creases + knee fold
    for side, hp_, kn, ft in (('l', 'hpl', 'knl', 'ftl'), ('r', 'hpr', 'knr', 'ftr')):
        d.line([J[kn], ((J[kn][0] + J[ft][0]) * .5, (J[kn][1] + J[ft][1]) * .5)],
               fill=(36, 36, 42), width=max(1, int(ow * .5)))
    for c0, c1, cz in CREASE:
        d.line([c0, c1], fill=depth((44, 44, 52), cz), width=max(1, int(ow * .55)))
    # shoe gloss
    for side, ft in (('l', 'ftl'), ('r', 'ftr')):
        sp = shoe(J[ft], -1 if side == 'l' else 1, ROLL[side], KS[ft])
        d.line([sp[2], sp[3]], fill=(96, 96, 108), width=max(1, int(ow * .55)))
        d.line([sp[5], sp[6]], fill=(60, 60, 68), width=max(1, int(ow * 1.3)))

    # hood (head)
    hx, hy = J['hctr']
    ang = K['hd_a']
    R = _R(hx, hy, ang)
    tw_ = math.sin(K['yaw'] + math.radians(pose.get('head_t', 0) * sgn))
    hood = _hood_pts(R, hrx, hry, tw_)
    d.line(hood + [hood[0]], fill=OUTL, width=max(1, int(ow * 2)), joint='curve')
    d.polygon(hood, fill=HOOD)
    if hood_mask_d is not None:
        hood_mask_d.polygon(hood, fill=255)
    fx = tw_ * hrx * .30
    opening = [R(fx + a, hry * .04 + b) for a, b in _superell(0, 0, hrx * .98, hry * 1.06, 2.3, 40)]
    d.polygon(opening, fill=VOID)
    # knit edge catching the key light (upper-left of the opening)
    arc = [R(fx + hrx * 1.02 * math.cos(a), hry * .04 + hry * 1.10 * math.sin(a))
           for a in np.linspace(math.radians(190), math.radians(300), 14)]
    d.line(arc, fill=HOOD_HI, width=max(1, int(ow * .8)), joint='curve')

    return dict(head=(hx, hy), hrx=hrx, hry=hry, ang=ang, tw=tw_, fx=fx,
                hip=J['hipc'], neck=J['nek'], sh_l=J['shl'], sh_r=J['shr'],
                hand_l=J['hal'], hand_r=J['har'], elbow_l=J['ell'], elbow_r=J['elr'],
                foot_l=J['ftl'], foot_r=J['ftr'], knee_l=J['knl'], knee_r=J['knr'],
                s=s, ow=ow, opening=opening)


# ───────────────────────────────────────────── lighting for black cloth
_NOISE = None
_GRADC = {}


def _noise(w, h):
    global _NOISE
    if _NOISE is None:
        rng = np.random.default_rng(11)
        n = rng.normal(0, 1, (256, 256)).astype(np.float32)
        im = Image.fromarray(np.clip(n * 40 + 128, 0, 255).astype('uint8'), 'L')
        im = im.filter(ImageFilter.GaussianBlur(0.9))
        a = np.asarray(im).astype(np.float32)
        a = np.abs(a - 128.0) * 2.4                      # crackle (ridges), knit-like
        _NOISE = Image.fromarray(np.clip(a, 0, 255).astype('uint8'), 'L')
    return _NOISE.resize((w, h), Image.BILINEAR)


def _form(w, h):
    k = (w, h)
    if k not in _GRADC:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        g = 1.0 - ((xx / max(w - 1, 1)) * 0.6 + (yy / max(h - 1, 1)) * 0.4)
        _GRADC[k] = Image.fromarray((np.clip(g, 0, 1) * 255).astype('uint8'), 'L')
    return _GRADC[k]


def _light(tile, s, j, hood_mask, lapel_mask):
    a = tile.getchannel('A')
    w, h = tile.size
    ow = max(2.0, OW * s)
    inner = a.filter(ImageFilter.GaussianBlur(ow * 1.1)).point(lambda v: 255 if v > 246 else 0)
    inner = ImageChops.multiply(inner, a)
    D = max(2, int(s * 0.017))
    Rb = max(1.6, s * 0.018)
    key = ImageChops.multiply(ImageChops.subtract(a, ImageChops.offset(a, D, D))
                              .filter(ImageFilter.GaussianBlur(Rb)), inner)
    fil = ImageChops.multiply(ImageChops.subtract(a, ImageChops.offset(a, -int(D * .8), -int(D * .8)))
                              .filter(ImageFilter.GaussianBlur(Rb * 1.3)), inner)
    out = tile.copy()
    def lay(col):
        return Image.new('RGBA', (w, h), col + (255,))
    form = ImageChops.multiply(_form(w, h), inner)
    out.paste(lay((98, 100, 112)), (0, 0), form.point(lambda v: int(v * 0.30)))
    # knit crackle on the hood only
    if hood_mask is not None:
        hm = ImageChops.multiply(hood_mask, inner)
        kn = ImageChops.multiply(_noise(w, h), hm)
        out.paste(lay((118, 118, 128)), (0, 0), kn.point(lambda v: int(v * 0.42)))
    if lapel_mask is not None:                            # satin facing: broader sheen
        lm = ImageChops.multiply(lapel_mask, inner)
        out.paste(lay((92, 92, 106)), (0, 0), ImageChops.multiply(_form(w, h), lm).point(lambda v: int(v * .20)))
    # AO pools
    ao = Image.new('L', (w, h), 0)
    ad = ImageDraw.Draw(ao)
    for key_, rad in (('neck', .066), ('sh_l', .052), ('sh_r', .052), ('hip', .060),
                      ('elbow_l', .032), ('elbow_r', .032), ('knee_l', .036), ('knee_r', .036)):
        jx, jy = j[key_]
        rr = rad * s
        ad.ellipse([jx - rr, jy - rr, jx + rr, jy + rr], fill=190)
    ao = ImageChops.multiply(ao.filter(ImageFilter.GaussianBlur(s * 0.034)), inner)
    out.paste(lay((0, 0, 0)), (0, 0), ao.point(lambda v: int(v * 0.42)))
    # rims
    out.paste(lay((122, 128, 142)), (0, 0), fil.point(lambda v: int(v * 0.34)))
    out.paste(lay((222, 226, 236)), (0, 0), key.point(lambda v: int(v * 0.70)))
    return out


# ───────────────────────────────────────────── the glowing face
def _eye_pts(sx, e, openk, tilt):
    """Wedge eye in head-local units (rx, ry). Outer end thick & high, inner tip low."""
    shape = e['eye']
    k = max(0.06, openk * e['open'])
    if shape == 'wide':
        pts = [(a * .26, b * .24) for a, b in _superell(0, 0, 1, 1, 2.2, 22)]
        pts = [(sx * (0.38 + a), -0.12 + b * max(.3, k)) for a, b in pts]
        rot = math.radians(-8 * sx)
    elif shape == 'happy':                               # ^ arcs
        pts = []
        for a in np.linspace(0, math.pi, 12):
            pts.append((sx * (0.38 + 0.24 * math.cos(a)), -0.10 - 0.22 * math.sin(a)))
        for a in np.linspace(math.pi, 0, 12):
            pts.append((sx * (0.38 + 0.24 * math.cos(a)), -0.10 - 0.22 * math.sin(a) + 0.11 * k))
        rot = 0.0
    elif shape == 'closed':                              # ‿ gentle arcs
        pts = []
        for a in np.linspace(0, math.pi, 12):
            pts.append((sx * (0.38 + 0.24 * math.cos(a)), -0.02 + 0.10 * math.sin(a)))
        for a in np.linspace(math.pi, 0, 12):
            pts.append((sx * (0.38 + 0.24 * math.cos(a)), -0.02 + 0.10 * math.sin(a) + 0.07))
        rot = 0.0
    else:
        # base wedge (sly). thickness t scaled by k; 'soft' flips the slant (inner high)
        t = 0.22 * k
        if shape == 'angry': t = 0.19 * k
        if shape == 'squint': t = 0.15 * k
        top = [(0.09, 0.02), (0.30, -0.18), (0.56, -0.38), (0.70, -0.42)]
        bot = [(0.68, -0.42 + t * 1.0), (0.48, -0.22 + t * .95), (0.26, -0.04 + t * .6), (0.09, 0.02 + t * .25)]
        pts = [(sx * a, b) for a, b in top + bot]
        rot = math.radians(-tilt * sx) if shape != 'soft' else math.radians((22 - tilt) * sx)
        if shape == 'soft':                              # worried: slant reversed, lifted
            pts = [(sx * a, b - 0.06) for a, b in top + bot]
    if rot:
        c, s_ = math.cos(rot), math.sin(rot)
        cx = sx * 0.38
        pts = [(cx + (a - cx) * c - b * s_, (a - cx) * s_ + b * c) for a, b in pts]
    return pts


def _mouth(e, rx, ry, R_, lw):
    m = e['mouth']
    pts = []
    if m in ('smirk', 'smile', 'grin'):
        wd = 0.46 if m != 'grin' else 0.54
        for u in np.linspace(-1, 1, 15):
            pts.append(R_(u * wd * rx, (0.40 + 0.16 * (1 - u * u)) * ry))
        if m == 'smirk':
            pts = pts[2:] + [R_(0.52 * rx, 0.30 * ry)]
            return [('line', pts, lw)]
        if m == 'grin':
            lower = [R_(u * wd * rx, (0.40 + 0.30 * (1 - u * u)) * ry) for u in np.linspace(1, -1, 15)]
            return [('poly', pts + lower, lw)]
        return [('line', pts, lw)]
    if m == 'flat':
        return [('line', [R_(-0.26 * rx, 0.46 * ry), R_(0.30 * rx, 0.45 * ry)], lw)]
    if m == 'frown':
        for u in np.linspace(-1, 1, 13):
            pts.append(R_(u * 0.36 * rx, (0.56 - 0.14 * (1 - u * u)) * ry))
        return [('line', pts, lw)]
    if m == 'wavy':
        for u in np.linspace(-1, 1, 13):
            pts.append(R_(u * 0.36 * rx, (0.48 + 0.07 * math.sin(u * 4.5)) * ry))
        return [('line', pts, lw)]
    if m == 'o':
        return [('poly', [R_(a, 0.48 * ry + b) for a, b in _superell(0, 0, rx * .14, ry * .17, 2.1, 18)], lw, 'ring')]
    if m == 'talk':
        return [('poly', [R_(a, 0.47 * ry + b) for a, b in _superell(0, 0, rx * .22, ry * .11, 2.3, 18)], lw)]
    return []


def draw_face(base, hx, hy, hrx, hry, ang, expr, look, blink, s, tw_=0.0, fx=None, glow=1.0):
    """Glowing eyes + mouth with bloom, composited onto `base` (RGB or RGBA)."""
    e = EXPR.get(expr, EXPR['sly'])
    if fx is None:
        fx = tw_ * hrx * .30
    cx = hx + fx * math.cos(ang) + look[0] * hrx * .12
    cy = hy + hry * .04 + fx * math.sin(ang) + look[1] * hry * .10
    pad = int(hrx * 2.6)
    w, h = pad * 2, pad * 2
    ox, oy = int(cx - pad), int(cy - pad)
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay, 'RGBA')
    R_ = _R(cx - ox, cy - oy, ang)
    lw = max(2, int(s * 0.0085))
    openk = max(0.0, 1.0 - max(0.0, min(1.0, blink)))
    shapes = []
    for sx in (-1, 1):
        pts = _eye_pts(sx, e, openk, e['tilt'])
        shapes.append(('poly', [R_(a * hrx, b * hry) for a, b in pts], lw))
    shapes += _mouth(e, hrx, hry, R_, lw)
    g = max(0.0, min(1.6, glow * e['glow']))

    def stamp(dd, col, extra=0):
        for sh in shapes:
            kind, pts = sh[0], sh[1]
            wd = sh[2] + extra
            if kind == 'line':
                dd.line(pts, fill=col, width=wd, joint='curve')
            elif len(sh) > 3 and sh[3] == 'ring':
                dd.line(pts + [pts[0]], fill=col, width=wd, joint='curve')
            else:
                dd.polygon(pts, fill=col)
                if extra:
                    dd.line(pts + [pts[0]], fill=col, width=extra, joint='curve')

    # interior glow on the hood (the light source is inside)
    inner = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(inner).ellipse([pad - hrx * .95, pad - hry * .65, pad + hrx * .95, pad + hry * .95],
                                  fill=GLOW_T + (int(44 * g),))
    inner = inner.filter(ImageFilter.GaussianBlur(hrx * .30))
    # wide bloom + tight bloom
    wide = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    stamp(ImageDraw.Draw(wide, 'RGBA'), GLOW_T + (int(150 * g),), extra=int(lw * 1.5))
    wide = wide.filter(ImageFilter.GaussianBlur(hrx * .22))
    tight = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    stamp(ImageDraw.Draw(tight, 'RGBA'), GLOW_C + (int(200 * min(1.0, g)),), extra=int(lw * .8))
    tight = tight.filter(ImageFilter.GaussianBlur(max(1.0, hrx * .055)))
    stamp(ld, GLOW + (255,))
    for L_ in (inner, wide, tight, lay):
        if base.mode == 'RGBA':
            base.alpha_composite(L_, (ox, oy))
        else:
            base.paste(L_, (ox, oy), L_)


# ───────────────────────────────────────────── public entry point
def shade(d, x, y, s, pose, expr='sly', p=1.0, look=(0, 0), blink=0.0, flip=False,
          glow=1.0, **_ignored):
    """Draw SHADE standing on (x, y) with total height s. toon.toon-compatible."""
    ox, oy = int(x - 0.92 * s), int(y - 1.30 * s)
    tw, th = int(1.84 * s) + 4, int(1.50 * s) + 4
    tile = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile, 'RGBA')
    hood_m = Image.new('L', (tw, th), 0)
    lapel_m = Image.new('L', (tw, th), 0)
    j = _draw_body(td, x - ox, y - oy, s, pose, flip, ImageDraw.Draw(hood_m), ImageDraw.Draw(lapel_m))
    tile = _light(tile, s, j, hood_m, lapel_m)
    base = getattr(d, '_image', None)
    if base is None:
        base = d.im
    if base.mode == 'RGBA':
        base.alpha_composite(tile, (ox, oy))
    else:
        base.paste(tile, (ox, oy), tile)
    jw = dict(j)
    for k in ('head', 'hip', 'neck', 'sh_l', 'sh_r', 'hand_l', 'hand_r',
              'elbow_l', 'elbow_r', 'foot_l', 'foot_r', 'knee_l', 'knee_r'):
        jw[k] = (j[k][0] + ox, j[k][1] + oy)
    draw_face(base, jw['head'][0], jw['head'][1], j['hrx'], j['hry'], j['ang'],
              expr, look, blink, s, j['tw'], j['fx'], glow)
    return jw


def head_only(base, cx, cy, hr, expr='sly', look=(0, 0), blink=0.0, ang=0.0, yaw=0.0):
    """Hood + face as a standalone bust (for sheets / big reaction inserts)."""
    hrx, hry = hr, hr * 1.21
    w, h = int(hr * 4.2), int(hr * 4.2)
    tile = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile, 'RGBA')
    R = _R(w / 2, h / 2, ang)
    ow = max(2.0, hr * 0.06)
    hood = _hood_pts(R, hrx, hry, math.sin(math.radians(yaw)))
    shawl = [R(-hrx * 1.5, hry * 1.9), R(hrx * 1.5, hry * 1.9), R(hrx * 1.1, hry * .6), R(-hrx * 1.1, hry * .6)]
    hm = Image.new('L', (w, h), 0)
    td.polygon(shawl, fill=HOOD)
    ImageDraw.Draw(hm).polygon(shawl, fill=255)
    td.line(hood + [hood[0]], fill=OUTL, width=int(ow * 2), joint='curve')
    td.polygon(hood, fill=HOOD)
    ImageDraw.Draw(hm).polygon(hood, fill=255)
    tw_ = math.sin(math.radians(yaw))
    fx = tw_ * hrx * .30
    td.polygon([R(fx + a, hry * .04 + b) for a, b in _superell(0, 0, hrx * .98, hry * 1.06, 2.3, 40)], fill=VOID)
    arc = [R(fx + hrx * 1.02 * math.cos(a), hry * .04 + hry * 1.10 * math.sin(a))
           for a in np.linspace(math.radians(190), math.radians(300), 14)]
    td.line(arc, fill=HOOD_HI, width=int(ow * .8), joint='curve')
    j = dict(neck=(w / 2, h / 2 + hry * 1.6), sh_l=(w * .2, h), sh_r=(w * .8, h), hip=(w / 2, h * 2),
             elbow_l=(0, h * 2), elbow_r=(0, h * 2), knee_l=(0, h * 2), knee_r=(0, h * 2))
    tile = _light(tile, hr / SP['head_rx'], j, hm, None)
    ox, oy = int(cx - w / 2), int(cy - h / 2)
    if base.mode == 'RGBA':
        base.alpha_composite(tile, (ox, oy))
    else:
        base.paste(tile, (ox, oy), tile)
    draw_face(base, cx, cy, hrx, hry, ang, expr, look, blink, hr / SP['head_rx'], tw_, fx)


# ───────────────────────────────────────────── signature poses
def p_pocket(t):
    """The reference stance: three-quarter, right hand in the trouser pocket,
    left arm hanging, weight on the left leg, head a touch tilted."""
    b = math.sin(t * 2.05)
    w = math.sin(t * 0.42)
    return dict(lean=-2.0 + 0.6 * w, yaw=16, twist=4, pelvis=4, tilt=-2.5, sway=0.010 * (1 + .3 * w),
                head=3.0 + 1.0 * w, head_t=-10,
                al=-11 - 0.6 * b, az_l=2, el=-2, ef_l=6,
                ar=9, az_r=18 + 0.5 * b, er=-24, ef_r=58,
                ll=-5, lz_l=0, kl=2, lr=9, lz_r=1, kr=5,
                hl='relax', hr='pocket', _br=b)


def p_pocket_both(t):
    b = math.sin(t * 2.05)
    return dict(lean=0.0, yaw=0, head=1.5 * math.sin(t * .5), head_t=0,
                al=-9, az_l=18 + 0.5 * b, el=24, ef_l=58,
                ar=9, az_r=18 + 0.5 * b, er=-24, ef_r=58,
                ll=-6, kl=2, lr=6, kr=2, hl='pocket', hr='pocket', _br=b)


def p_arms_cross(t):
    b = math.sin(t * 2.05)
    return dict(lean=0, yaw=8, head=2, head_t=-4,
                al=-16, az_l=22, el=-44, ef_l=112, ar=16, az_r=22, er=44, ef_r=112,
                ll=-7, kl=2, lr=7, kr=2, hl='fist', hr='fist', _br=b)


POSES = dict(pocket=p_pocket, pocket_both=p_pocket_both, arms_cross=p_arms_cross)
