"""
character.py — THE HERO CHARACTER SYSTEM
=========================================
One main character for the entire film, with a stable identity so the viewer
recognises him in every scene.

What this adds on top of stickbase.stick():
  * EYEBROWS      — the single biggest expression upgrade a stickman can get
  * PUPILS        — look direction, surprise, squint
  * MOUTH SHAPES  — 10 named expressions instead of 3
  * HANDS         — small filled circles at the wrist, so gestures read
  * ACCESSORIES   — the identity marker (cap / hair / headphones / scarf)
  * HOODIE        — an optional torso silhouette that makes him feel designed
  * IDENTITY LOCK — one fixed seed + one fixed palette, used everywhere

Design rule: everything is still drawn with stickbase primitives, so the
character boils, draws-on, and jitters exactly like the rest of the film.
"""
import math, sys
sys.path.insert(0, '/home/user/src')
from PIL import ImageDraw
from stickbase import (CHALK, GOLD, CYAN, MINT, RED, PINK, poly, circ, arc, box,
                       rot2, clamp, hsh, ft, MARKER, HAND, write)

# ════════════════════════════════════════════════════════ IDENTITY
HERO_SEED = 101          # ONE seed for the hero, everywhere, forever
HERO_COL = CHALK         # body stroke colour
HERO_W = 10              # body stroke width at s=600
ACC_COL = GOLD           # accessory / identity-marker colour

CHAR = dict(
    name='BUDDY',
    # all proportions are fractions of total height `s`
    hip=0.42, neck=0.36, head_r=0.115, head_gap=0.035, shoulder=0.03,
    arm_u=0.19, arm_l=0.18, leg_u=0.22, leg_l=0.22, foot=0.055,
    hand_r=0.022,           # hand blob radius
)

# ════════════════════════════════════════════════════════ EXPRESSIONS
# brow_a : brow angle, + = inner end down (angry/determined)
# brow_y : brow height above the eye, in head-radius units
# eye    : 'open' | 'wide' | 'squint' | 'closed' | 'happy'
# pupil  : (dx, dy) in head-radius units
# mouth  : 'line' | 'smile' | 'bigsmile' | 'frown' | 'o' | 'flat' | 'grit' | 'open'
# m_w    : mouth width multiplier
EXPR = {
    'neutral':   dict(brow_a=0,   brow_y=.52, eye='open',   pupil=(0, 0),     mouth='line',     m_w=1.0),
    'sad':       dict(brow_a=-14, brow_y=.46, eye='squint', pupil=(0, .10),   mouth='frown',    m_w=1.0),
    'worried':   dict(brow_a=-18, brow_y=.58, eye='wide',   pupil=(0, .06),   mouth='frown',    m_w=.8),
    'shock':     dict(brow_a=-6,  brow_y=.72, eye='wide',   pupil=(0, 0),     mouth='o',        m_w=1.0),
    'think':     dict(brow_a=10,  brow_y=.50, eye='squint', pupil=(.26, -.10), mouth='flat',    m_w=.7),
    'focus':     dict(brow_a=16,  brow_y=.40, eye='squint', pupil=(0, .04),   mouth='grit',     m_w=.9),
    'determined':dict(brow_a=20,  brow_y=.42, eye='open',   pupil=(0, 0),     mouth='flat',     m_w=1.0),
    'happy':     dict(brow_a=-4,  brow_y=.60, eye='happy',  pupil=(0, 0),     mouth='smile',    m_w=1.0),
    'proud':     dict(brow_a=6,   brow_y=.58, eye='open',   pupil=(0, -.06),  mouth='smile',    m_w=1.1),
    'celebrate': dict(brow_a=-6,  brow_y=.66, eye='happy',  pupil=(0, 0),     mouth='bigsmile', m_w=1.25),
}


def _oval(d, c, rx, ry, col, w, seed, tq, segs=16):
    """Hand-drawn ellipse outline. Local to character.py so stickbase stays
    byte-identical (its sha256 gates the build harness)."""
    pts = [(c[0] + rx * math.cos(2 * math.pi * k / segs),
            c[1] + ry * math.sin(2 * math.pi * k / segs)) for k in range(segs + 1)]
    poly(d, pts, col, w, 1.0, seed, tq, .9)


def face(d, head, hr, s, expr='neutral', col=CHALK, w=6, tq=0, seed=HERO_SEED,
         blink=0.0, look=(0, 0)):
    """Rich face: eyebrows + pupils + 8 mouth shapes.
    blink : 0..1, 1 = fully closed.  look : extra pupil offset in hr units."""
    e = EXPR.get(expr, EXPR['neutral'])
    hx, hy = head
    ex = hr * .38                      # eye x-offset from centre
    ey = hy - hr * .10                 # eye line
    er = max(2.0, hr * .155)           # eye radius
    shape = e['eye']
    bl = clamp(blink)
    sq = max(0.10, 1.0 - bl)           # vertical squash of the eye as the lid comes down
    if bl > .86:
        shape = 'closed'

    for sx in (-1, 1):
        cx = hx + sx * ex
        dx = (e['pupil'][0] + look[0]) * hr * .36
        dy = (e['pupil'][1] + look[1]) * hr * .36 * sq
        # ---- eye
        if shape == 'closed':
            arc(d, (cx, ey), er * 1.0, 200, 340, col, max(3, w - 2), 1, seed + sx, tq, .9, 8)
        elif shape == 'happy':
            # ^ ^  upturned joy eyes
            arc(d, (cx, ey + er * .55), er * 1.15, 205, 335, col, max(3, w - 2), 1, seed + sx, tq, .9, 10)
        elif shape == 'wide':
            # only SHOCK/WORRY gets an outlined eye with a floating pupil
            rr = er * 1.22
            _oval(d, (cx, ey), rr, rr * sq, col, max(2, w - 4), seed + 2 + sx, tq)
            pr = max(1.6, rr * .40)
            d.ellipse([cx + dx - pr, ey + dy - pr * sq, cx + dx + pr, ey + dy + pr * sq], fill=col)
        elif shape == 'squint':
            # a flat lens — reads as narrowed, never as goggles
            pr = max(1.6, er * .46)
            d.ellipse([cx + dx - pr * 1.25, ey + dy - pr * .62 * sq,
                       cx + dx + pr * 1.25, ey + dy + pr * .62 * sq], fill=col)
        else:  # 'open' — the default: a clean solid dot, like the rest of the film
            pr = max(2.0, er * .66)
            d.ellipse([cx + dx - pr, ey + dy - max(1.2, pr * sq),
                       cx + dx + pr, ey + dy + max(1.2, pr * sq)], fill=col)
        # ---- eyebrow  (does ~70% of the expression work)
        by = ey - hr * e['brow_y']
        bl = hr * .30
        ang = math.radians(e['brow_a'] * sx * -1)
        a = (cx - bl * math.cos(ang), by - bl * math.sin(ang))
        b = (cx + bl * math.cos(ang), by + bl * math.sin(ang))
        poly(d, [a, b], col, max(3, w - 1), 1, seed + 6 + sx, tq, 1.0)

    # ---- mouth
    mw = hr * .46 * e['m_w']
    my = hy + hr * .40
    m = e['mouth']
    lw = max(4, w - 2)
    if m == 'smile':
        arc(d, (hx, my - mw * .55), mw, 18, 162, col, lw, 1, seed + 11, tq, 1.1, 12)
    elif m == 'bigsmile':
        arc(d, (hx, my - mw * .35), mw * 1.15, 8, 172, col, lw, 1, seed + 11, tq, 1.1, 14)
        poly(d, [(hx - mw * 1.13, my - mw * .33), (hx + mw * 1.13, my - mw * .33)],
             col, lw, 1, seed + 12, tq, 1.0)
    elif m == 'frown':
        arc(d, (hx, my + mw * .75), mw, 202, 338, col, lw, 1, seed + 11, tq, 1.1, 12)
    elif m == 'o':
        circ(d, (hx, my), mw * .52, col, lw, 1, seed + 11, tq, 1.0, 12)
    elif m == 'open':
        circ(d, (hx, my + mw * .1), mw * .72, col, lw, 1, seed + 11, tq, 1.0, 14)
    elif m == 'grit':
        box(d, hx - mw * .7, my - mw * .22, hx + mw * .7, my + mw * .22, col, max(3, w - 3), 1, seed + 11, tq, 1.0)
        for k in (-1, 0, 1):
            poly(d, [(hx + k * mw * .34, my - mw * .22), (hx + k * mw * .34, my + mw * .22)],
                 col, max(2, w - 4), 1, seed + 13 + k, tq, .8)
    elif m == 'flat':
        poly(d, [(hx - mw * .62, my), (hx + mw * .62, my)], col, lw, 1, seed + 11, tq, 1.0)
    else:  # line
        poly(d, [(hx - mw * .55, my), (hx + mw * .55, my)], col, lw, 1, seed + 11, tq, 1.0)


# ════════════════════════════════════════════════════════ ACCESSORIES
def acc_cap(d, head, hr, lean, col=ACC_COL, w=7, p=1., tq=0, seed=HERO_SEED + 40):
    """Backwards snapback. Reads as 'young hustler' at thumbnail size."""
    def R(v):
        return (head[0] + rot2(lean, v)[0], head[1] + rot2(lean, v)[1])
    # crown sits ON the skull — the band must stay clear of the eyebrows
    crown = [R((-hr * .95, -hr * .46)), R((-hr * .82, -hr * 1.00)), R((0, -hr * 1.26)),
             R((hr * .82, -hr * 1.00)), R((hr * .95, -hr * .46))]
    poly(d, crown, col, w, p, seed, tq, 1.6)
    poly(d, [R((-hr * .95, -hr * .46)), R((hr * .95, -hr * .50))], col, w, p, seed + 1, tq, 1.4)
    # peak pointing backwards (to the left)
    poly(d, [R((-hr * .93, -hr * .50)), R((-hr * 1.56, -hr * .66)),
             R((-hr * 1.52, -hr * .32)), R((-hr * .93, -hr * .30))],
         col, w, clamp(p * 1.4 - .2), seed + 2, tq, 1.5, closed=True)
    # button
    if p > .9:
        bx, by = R((0, -hr * 1.26))
        d.ellipse([bx - 4, by - 4, bx + 4, by + 4], fill=col)


def acc_hair(d, head, hr, lean, col=ACC_COL, w=7, p=1., tq=0, seed=HERO_SEED + 50):
    """Three-spike tuft."""
    def R(v):
        return (head[0] + rot2(lean, v)[0], head[1] + rot2(lean, v)[1])
    for k, (x0, x1, h) in enumerate([(-.58, -.16, 1.62), (-.20, .22, 1.84), (.16, .60, 1.56)]):
        poly(d, [R((hr * x0, -hr * .86)), R((hr * (x0 + x1) / 2, -hr * h)), R((hr * x1, -hr * .88))],
             col, w, clamp(p * 1.6 - k * .18), seed + k, tq, 1.6)


def acc_phones(d, head, hr, lean, col=ACC_COL, w=8, p=1., tq=0, seed=HERO_SEED + 60):
    """Over-ear headphones. Reads as 'creator / editor'."""
    def R(v):
        return (head[0] + rot2(lean, v)[0], head[1] + rot2(lean, v)[1])
    band = [R((-hr * 1.06, -hr * .18)), R((-hr * .80, -hr * 1.04)),
            R((0, -hr * 1.28)), R((hr * .80, -hr * 1.04)), R((hr * 1.06, -hr * .18))]
    poly(d, band, col, w, p, seed, tq, 1.5)
    for sx in (-1, 1):
        c = R((sx * hr * 1.08, -hr * .02))
        box(d, c[0] - hr * .26, c[1] - hr * .34, c[0] + hr * .26, c[1] + hr * .34,
            col, w, clamp(p * 1.5 - .3), seed + 2 + sx, tq, 1.4)


def acc_scarf(d, neck, hr, lean, col=ACC_COL, w=8, p=1., tq=0, seed=HERO_SEED + 70, t=0.0):
    """Muffler with a tail that flutters. Strongest silhouette of the four."""
    nx, ny = neck
    poly(d, [(nx - hr * .95, ny + hr * .10), (nx, ny + hr * .34), (nx + hr * .95, ny + hr * .10)],
         col, w + 2, p, seed, tq, 1.6)
    fl = math.sin(t * 3.4) * hr * .28
    poly(d, [(nx + hr * .72, ny + hr * .18), (nx + hr * 1.30, ny + hr * .70 + fl),
             (nx + hr * 1.08, ny + hr * 1.30 - fl * .6)],
         col, w, clamp(p * 1.4 - .2), seed + 1, tq, 2.0)


def acc_hoodie(d, neck, hip, hr, lean, col=CHALK, w=7, p=1., tq=0, seed=HERO_SEED + 80,
               head=None):
    """Torso detailing — suggests a hoodie WITHOUT closing into a dress.

    Three marks only:  the hood resting behind the head, a V collar with two
    drawstrings, and two side seams that stop short of the hip.
    No bottom edge is ever drawn — that is what turned the old version into a
    frock. The silhouette must stay a stick figure.
    """
    nx, ny = neck
    hx, hy = hip
    tl = hy - ny                      # torso length

    # ---- hood: an arc sitting BEHIND / BELOW the skull, not under the chin
    if head is not None:
        arc(d, head, hr * 1.30, 212, 328, col, max(3, w - 2), p, seed + 3, tq, 1.4, 14)

    # ---- V collar
    poly(d, [(nx - hr * .52, ny + hr * .02), (nx, ny + hr * .40), (nx + hr * .52, ny + hr * .02)],
         col, max(3, w - 2), p, seed, tq, 1.2)

    # ---- drawstrings
    sp = clamp(p * 1.5 - .4)
    for sx in (-1, 1):
        poly(d, [(nx + sx * hr * .18, ny + hr * .34), (nx + sx * hr * .26, ny + hr * .34 + tl * .22)],
             col, max(2, w - 4), sp, seed + 5 + sx, tq, 1.0)

    # ---- side seams: shoulder -> ribs, stopping at 72% of the torso
    for sx in (-1, 1):
        poly(d, [(nx + sx * hr * .80, ny + hr * .30),
                 (nx + sx * hr * .86, ny + tl * .34),
                 (nx + sx * hr * .70, ny + tl * .72)],
             col, max(3, w - 3), clamp(p * 1.3), seed + 8 + sx, tq, 1.4)

    # ---- kangaroo pocket
    if p > .85:
        poly(d, [(nx - hr * .62, ny + tl * .60), (nx - hr * .50, ny + tl * .80),
                 (nx + hr * .50, ny + tl * .80), (nx + hr * .62, ny + tl * .60)],
             col, max(2, w - 4), clamp(p * 6 - 5.1), seed + 11, tq, 1.1)


ACCESSORIES = {'cap': acc_cap, 'hair': acc_hair, 'phones': acc_phones, 'scarf': acc_scarf}


# ════════════════════════════════════════════════════════ THE HERO
def hero(d, x, y, s, pose, expr='neutral', marker='cap', col=HERO_COL, w=None,
         tq=0, p=1.0, seed=HERO_SEED, t=0.0, hoodie=True, acc_col=ACC_COL,
         blink=0.0, look=(0, 0), hands=True):
    """Draw the main character. Returns the joint dict (same contract as stick()).

    pose   : dict of joint angles in degrees (see stickbase pose_* generators)
    expr   : key into EXPR
    marker : 'cap' | 'hair' | 'phones' | 'scarf' | None
    """
    C = CHAR
    if w is None:
        w = max(4, int(HERO_W * s / 600))
    lean = math.radians(pose.get('lean', 0))
    hip = (x, y - C['hip'] * s)
    off = rot2(lean, (0, -C['neck'] * s))
    neck = (hip[0] + off[0], hip[1] + off[1])
    hr = C['head_r'] * s
    hd_off = rot2(lean + math.radians(pose.get('head', 0)), (0, -hr - C['head_gap'] * s))
    head = (neck[0] + hd_off[0], neck[1] + hd_off[1])

    def limb(root, a1, a2, l1, l2):
        a1 = math.radians(a1) + lean
        a2 = math.radians(a2) + a1
        j = (root[0] + l1 * math.sin(a1), root[1] + l1 * math.cos(a1))
        e = (j[0] + l2 * math.sin(a2), j[1] + l2 * math.cos(a2))
        return j, e

    sh = (neck[0], neck[1] + C['shoulder'] * s)
    el_l, hd_l = limb(sh, pose.get('al', 20), pose.get('el', 10), C['arm_u'] * s, C['arm_l'] * s)
    el_r, hd_r = limb(sh, pose.get('ar', -20), pose.get('er', -10), C['arm_u'] * s, C['arm_l'] * s)
    kn_l, ft_l = limb(hip, pose.get('ll', 12), pose.get('kl', 0), C['leg_u'] * s, C['leg_l'] * s)
    kn_r, ft_r = limb(hip, pose.get('lr', -12), pose.get('kr', 0), C['leg_u'] * s, C['leg_l'] * s)

    # ---- draw order: hoodie behind, then skeleton, then head, then face, then marker
    if hoodie:
        acc_hoodie(d, neck, hip, hr, lean, col, max(3, w - 2), clamp(p * 1.3), tq, seed + 80, head)
    poly(d, [neck, hip], col, w, p, seed + 1, tq)
    poly(d, [sh, el_l, hd_l], col, w, p, seed + 2, tq)
    poly(d, [sh, el_r, hd_r], col, w, p, seed + 3, tq)
    poly(d, [hip, kn_l, ft_l], col, w, p, seed + 4, tq)
    poly(d, [hip, kn_r, ft_r], col, w, p, seed + 5, tq)
    poly(d, [ft_l, (ft_l[0] - C['foot'] * s, ft_l[1])], col, w, p, seed + 8, tq)
    poly(d, [ft_r, (ft_r[0] + C['foot'] * s, ft_r[1])], col, w, p, seed + 9, tq)
    if hands and p > .75:
        hrad = max(2.5, C['hand_r'] * s)
        for q in (hd_l, hd_r):
            d.ellipse([q[0] - hrad, q[1] - hrad, q[0] + hrad, q[1] + hrad], fill=col)
    circ(d, head, hr, col, w, p, seed, tq, 2.0, segs=28)
    if p > .7:
        face(d, head, hr, s, expr, col, max(4, int(w * .62)), tq, seed + 20, blink, look)
    if marker and p > .6:
        fn = ACCESSORIES[marker]
        if marker == 'scarf':
            fn(d, neck, hr, lean, acc_col, max(5, int(w * .8)), clamp((p - .6) / .4), tq, seed + 70, t)
        else:
            fn(d, head, hr, lean, acc_col, max(5, int(w * .75)), clamp((p - .6) / .4), tq)

    return {'head': head, 'hand_l': hd_l, 'hand_r': hd_r, 'hip': hip,
            'neck': neck, 'hr': hr, 'foot_l': ft_l, 'foot_r': ft_r,
            'elbow_l': el_l, 'elbow_r': el_r, 'shoulder': sh}


def blink_at(t, period=3.1, dur=0.14):
    """Deterministic natural blink envelope — call per frame, feed into hero()."""
    ph = (t + 0.7) % period
    return 1.0 if ph < dur else (0.6 if ph < dur + .05 else 0.0)
