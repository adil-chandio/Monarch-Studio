"""dog3.py — the golden dog, redrawn for AMEER KA KUTTA v3 (2.5D).

Built from real dog parts, each one smooth and separately outlined:
  * torso: deep chest, tucked waist, flat back (Catmull-Rom closed outline)
  * skull + tapered muzzle (rotatable: the eat pose lowers the head to the bowl)
  * floppy ear, two-segment legs with knee and elbow taper, oval paws
  * feathered tail, brow + eye with catch-light, collar that follows the neck, gold tag

Supersampled 3x into an RGBA sprite. Local units match kutta.py (origin = ground under the body centre,
body about 350 units from paw to ear). Call:  sprite, (ox, oy) = dog_sprite(x, gy, s, t, pose, flip)
poses: 'stand', 'sit', 'eat', 'lie'
"""
import math
from PIL import Image, ImageDraw

INK = (30, 24, 34, 255)
FUR = (228, 172, 94, 255)
FUR_HI = (248, 206, 132, 255)
FUR_MID = (204, 146, 76, 255)
FUR_D = (160, 104, 52, 255)
EAR = (146, 92, 46, 255)
GOLD = (240, 194, 100, 255)
GOLD_D = (178, 128, 56, 255)
NOSE = (32, 24, 28, 255)
EYE_W = (255, 252, 242, 255)
SS = 3
OW = 6


def _catmull(P, seg=10, closed=True):
    n = len(P)
    out = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = P[(i - 1) % n] if closed else P[max(i - 1, 0)]
        p1 = P[i]
        p2 = P[(i + 1) % n] if closed else P[min(i + 1, n - 1)]
        p3 = P[(i + 2) % n] if closed else P[min(i + 2, n - 1)]
        for k in range(seg):
            u = k / seg
            u2, u3 = u * u, u * u * u
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * u + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * u + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)
            out.append((x, y))
    if not closed:
        out.append(P[-1])
    return out


def _limb_poly(p0, p1, w0, w1):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    return [(p0[0] + nx * w0 / 2, p0[1] + ny * w0 / 2), (p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2),
            (p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2), (p0[0] - nx * w0 / 2, p0[1] - ny * w0 / 2)]


def _rot(p, c, ang):
    x, y = p[0] - c[0], p[1] - c[1]
    ca, sa = math.cos(ang), math.sin(ang)
    return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)


# ── per-pose geometry (local units) ───────────────────────────────────────────
POSES = {
    'stand': dict(
        torso=[(-158, -236), (-96, -268), (-6, -276), (84, -266), (142, -238), (170, -188), (160, -138),
               (112, -112), (30, -104), (-52, -108), (-112, -118), (-156, -152), (-170, -196)],
        legs_back=[[(-108, -150), (-124, -78), (-116, 0)]],
        legs_front=[[(92, -150), (108, -80), (116, 0)], [(128, -150), (136, -80), (146, 0)]],
        head=(196, -316), head_r=58, head_rot=0.0,
        ear=(158, -320), eye=(214, -322), brow=(214, -350), nose=(292, -298),
        collar=[(118, -262), (150, -252), (184, -244)], tag=(170, -232),
        tail_root=(-160, -236), tail=[(-166, -236), (-212, -256), (-240, -300), (-226, -340)], tail_w=(24, 8),
        haunch=None),
    'sit': dict(
        torso=[(-132, -90), (-150, -170), (-112, -270), (-40, -322), (40, -316), (96, -282), (118, -220),
               (112, -150), (88, -100), (30, -60), (-40, -40), (-100, -40)],
        legs_back=[],
        legs_front=[[(72, -190), (92, -110), (104, 0)], [(104, -190), (114, -110), (124, 0)]],
        head=(98, -378), head_r=58, head_rot=0.0,
        ear=(60, -384), eye=(116, -386), brow=(116, -412), nose=(190, -358),
        collar=[(70, -330), (104, -322), (136, -316)], tag=(116, -302),
        tail_root=(-130, -70), tail=[(-130, -70), (-200, -30), (-244, -70), (-240, -120)], tail_w=(24, 8),
        haunch=(-74, -82, 96, 84)),
    'eat': dict(
        torso=[(-158, -236), (-96, -268), (-6, -276), (84, -266), (142, -238), (170, -188), (160, -138),
               (112, -112), (30, -104), (-52, -108), (-112, -118), (-156, -152), (-170, -196)],
        legs_back=[[(-108, -150), (-124, -78), (-116, 0)]],
        legs_front=[[(92, -150), (108, -80), (116, 0)], [(128, -150), (136, -80), (146, 0)]],
        head=(206, -196), head_r=58, head_rot=0.62,
        ear=(170, -200), eye=(232, -206), brow=(232, -234), nose=(300, -150),
        collar=[(126, -252), (158, -228), (192, -206)], tag=(180, -190),
        tail_root=(-160, -236), tail=[(-166, -236), (-212, -256), (-240, -300), (-226, -340)], tail_w=(24, 8),
        haunch=None),
    'lie': dict(
        torso=[(-190, -104), (-120, -132), (-20, -128), (80, -122), (150, -110), (176, -80), (150, -40),
               (60, -26), (-40, -22), (-130, -28), (-188, -56)],
        legs_back=[[(-150, -66), (-190, -30), (-214, -14)]],
        legs_front=[[(100, -70), (150, -36), (196, -20)]],
        head=(222, -112), head_r=54, head_rot=0.22,
        ear=(190, -112), eye=(246, -118), brow=(246, -142), nose=(312, -96),
        collar=[(170, -140), (200, -128), (226, -124)], tag=(206, -116),
        tail_root=(-190, -80), tail=[(-188, -80), (-236, -60), (-270, -66), (-282, -96)], tail_w=(22, 8),
        haunch=None, closed=True),
}

XS, YS = [-360, 360], [-440, 40]


def _head(Qf, sc, hx, hy, hr, rot, ear, eye, brow, nose, closed, blink, flip):
    """Skull + muzzle + ear + eye, all in head-local space then rotated."""
    c = (hx, hy)

    def R(px, py):
        return _rot((px, py), c, rot)

    # ear (behind skull)
    ex, ey = ear
    ear_pts = _catmull([(ex - 26, ey - 10), (ex - 4, ey - 52), (ex + 26, ey - 28), (ex + 18, ey + 26), (ex - 6, ey + 58),
                        (ex - 26, ey + 30)], seg=8)
    ear_pts = [R(px, py) for px, py in ear_pts]
    ear_pts = [Qf(px, py) for px, py in ear_pts]
    return dict(ear=ear_pts, R=R)


def dog_sprite(x, gy, s, t, pose='stand', flip=False):
    P = POSES[pose]
    bw, bh = int((XS[1] - XS[0]) * s), int((YS[1] - YS[0]) * s)
    ox, oy = int(x + XS[0] * s), int(gy + YS[0] * s)
    big = Image.new('RGBA', (bw * SS, bh * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)

    def Qf(px, py):
        if flip:
            px = -px
        return ((px - XS[0]) * s * SS, (py - YS[0]) * s * SS)

    def sc(v):
        return v * s * SS

    def outline(pts, fill, ow=OW):
        d.polygon(pts, fill=fill)
        d.line(list(pts) + [pts[0]], fill=INK, width=int(ow * SS), joint='curve')

    breath = math.sin(t * 2.3) * 4.0
    wag = math.sin(t * 6.8) * (16 if pose != 'lie' else 6)
    blink = (t % 3.4) < 0.12 and pose != 'lie'

    # tail (behind)
    tp = _catmull([(px + (wag * 0.5 if i > 1 else 0), py - abs(wag) * 0.12 * i) for i, (px, py) in enumerate(P['tail'])],
                  seg=12, closed=False)
    n = len(tp)
    w0, w1 = P['tail_w']
    left, right = [], []
    for i, (px, py) in enumerate(tp):
        a, b = tp[max(i - 1, 0)], tp[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = (w0 + (w1 - w0) * i / max(n - 1, 1)) * s * SS / 2
        q = Qf(px, py)
        left.append((q[0] + nx * w, q[1] + ny * w))
        right.append((q[0] - nx * w, q[1] - ny * w))
    outline(left + right[::-1], FUR_D)
    # tail tip feather
    tip = Qf(*tp[-1])
    d.ellipse([tip[0] - sc(10), tip[1] - sc(10), tip[0] + sc(10), tip[1] + sc(10)], fill=FUR_HI)

    # back legs (behind body)
    for leg in P['legs_back']:
        pts = _catmull(leg, seg=8, closed=False)
        for i in range(len(pts) - 1):
            w = 40 - 14 * i / max(len(pts) - 1, 1)
            outline(_limb_poly(Qf(*pts[i]), Qf(*pts[i + 1]), sc(w), sc(w - 6)), FUR_D, ow=OW - 1)
        fx, fy = Qf(*leg[-1])
        d.ellipse([fx - sc(30), fy - sc(12), fx + sc(34), fy + sc(12)], fill=FUR_D, outline=INK, width=int(OW * SS))

    # body
    tor = _catmull(P['torso'], seg=10)
    body_pts = [Qf(px, py + breath * (1 if py < -200 else 0.4)) for px, py in tor]
    outline(body_pts, FUR)
    # belly shade and back highlight
    shade = _catmull([(-120, -124), (-40, -100), (50, -100), (120, -120)], seg=8, closed=False)
    d.line([Qf(*p) for p in shade], fill=FUR_MID, width=int(sc(22)), joint='curve')
    hi = _catmull([(-80, -262), (0, -268), (80, -258)], seg=8, closed=False)
    d.line([Qf(*p) for p in hi], fill=FUR_HI, width=int(sc(12)), joint='curve')
    if P.get('haunch'):
        hx_, hy_, rx, ry = P['haunch']
        c = Qf(hx_, hy_)
        d.ellipse([c[0] - sc(rx), c[1] - sc(ry), c[0] + sc(rx), c[1] + sc(ry)], fill=FUR, outline=INK, width=int(OW * SS))
        arc = _catmull([(hx_ - rx * .35, hy_ - ry * .1), (hx_ - rx * .05, hy_ + ry * .55), (hx_ + rx * .4, hy_ + ry * .4)], seg=8, closed=False)
        d.line([Qf(*p) for p in arc], fill=FUR_MID, width=int(sc(10)), joint='curve')

    # front legs (in front of body, far leg first)
    for k, leg in enumerate(P['legs_front']):
        col = FUR_MID if k == 0 else FUR
        pts = _catmull(leg, seg=8, closed=False)
        for i in range(len(pts) - 1):
            w = 46 - 18 * i / max(len(pts) - 1, 1)
            outline(_limb_poly(Qf(*pts[i]), Qf(*pts[i + 1]), sc(w), sc(w - 6)), col, ow=OW - 1)
        fx, fy = Qf(*leg[-1])
        d.ellipse([fx - sc(10), fy - sc(12), fx + sc(44), fy + sc(12)], fill=col, outline=INK, width=int(OW * SS))

    # ear (behind head)
    hx, hy, hr = P['head'][0], P['head'][1], P['head_r']
    rot = P['head_rot']
    ex, ey = P['ear']
    ear_src = [(ex - 26, ey - 10), (ex - 6, ey - 52), (ex + 26, ey - 28), (ex + 18, ey + 26), (ex - 6, ey + 60), (ex - 26, ey + 32)]
    ear_src = _catmull(ear_src, seg=8)
    ear_pts = [_rot(p, (hx, hy), rot) for p in ear_src]
    outline([Qf(*p) for p in ear_pts], EAR)

    # skull (circle, slightly flattened)
    skull = [_rot((hx + math.cos(a) * hr, hy + math.sin(a) * hr * 0.92), (hx, hy), rot)
             for a in [i * math.pi * 2 / 40 for i in range(40)]]
    outline([Qf(*p) for p in skull], FUR)

    # muzzle: tapered, rounded nose end, rotated with the head
    nx_, ny_ = P['nose']
    mz = [(hx - 10, hy - 42), (hx + 60, hy - 30), (nx_ - 8, ny_ - 16), (nx_ + 6, ny_ - 2),
          (nx_ - 2, ny_ + 18), (hx + 40, hy + 36), (hx - 10, hy + 40)]
    mz = _catmull(mz, seg=8)
    mz = [_rot(p, (hx, hy), rot) for p in mz]
    outline([Qf(*p) for p in mz], FUR_HI)
    # nose
    nq = Qf(*_rot((nx_, ny_), (hx, hy), rot))
    d.ellipse([nq[0] - sc(16), nq[1] - sc(12), nq[0] + sc(16), nq[1] + sc(12)], fill=NOSE)
    d.ellipse([nq[0] - sc(9), nq[1] - sc(8), nq[0] - sc(2), nq[1] - sc(3)], fill=(255, 255, 255, 170))
    # mouth line
    m0 = Qf(*_rot((hx + 40, hy + 14), (hx, hy), rot))
    m1 = Qf(*_rot((nx_ - 14, ny_ + 12), (hx, hy), rot))
    d.line([m0, m1], fill=INK, width=int(sc(4)))

    # brow + eye
    bq = Qf(*_rot(P['brow'], (hx, hy), rot))
    d.line([(bq[0] - sc(20), bq[1] + sc(6)), (bq[0] + sc(12), bq[1] - sc(2))], fill=INK, width=int(sc(7)), joint='curve')
    eq = Qf(*_rot(P['eye'], (hx, hy), rot))
    if blink:
        d.line([(eq[0] - sc(18), eq[1]), (eq[0] + sc(18), eq[1])], fill=INK, width=int(sc(7)))
    else:
        d.ellipse([eq[0] - sc(17), eq[1] - sc(17), eq[0] + sc(17), eq[1] + sc(17)], fill=EYE_W, outline=INK, width=int(sc(4)))
        d.ellipse([eq[0] - sc(11), eq[1] - sc(11), eq[0] + sc(11), eq[1] + sc(11)], fill=INK)
        d.ellipse([eq[0] - sc(3), eq[1] - sc(8), eq[0] + sc(6), eq[1] + sc(1)], fill=(255, 255, 255, 255))

    # collar (follows the neck), gold tag
    col = [Qf(*p) for p in _catmull(P['collar'], seg=8, closed=False)]
    d.line(col, fill=INK, width=int(sc(26)), joint='curve')
    d.line(col, fill=GOLD, width=int(sc(16)), joint='curve')
    tx, ty = Qf(*P['tag'])
    r = sc(15)
    tag = [(tx, ty - r * 1.5), (tx + r, ty), (tx, ty + r * 1.5), (tx - r, ty)]
    outline(tag, GOLD_D, ow=4)
    shine = (t * 1.6) % 1.0
    if shine < 0.35:
        a = int(230 * (1 - shine / 0.35))
        d.line([(tx - r * 0.3, ty - r), (tx + r * 0.3, ty + r * 0.2)], fill=(255, 250, 230, a), width=int(sc(4)))

    sprite = big.resize((bw, bh), Image.LANCZOS)
    return sprite, (ox, oy)
