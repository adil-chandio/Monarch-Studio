"""kutta2.py — AMEER KA KUTTA v2 (~20 s, 9:16). The black SHADE hero is back and walks the golden dog
on a leash; the car is drawn with shading (gradient body, glass, wheel arches, rims, door that opens,
the dog hops in). Motion grammar on top of the v1 editing:

  * 3-plane parallax (far / mid / near) with a perspective floor; the far plane is softer (depth)
  * keyframed camera per shot (eased zoom + pan), plus a beat punch on each VO onset
  * kinetic typography (each letter drops in), an AC toggle motion graphic, a physics leash
  * new transitions: page wipe with a fold shadow, light flare with an anamorphic streak;
    plus respect2's cube / whip / slices / blur / zoom / card / ink / sweep

Voice: prep_vo_kutta.py fits the clips (inner pauses <= 0.22 s). Pure function of t.
CLI:  kutta2.py still T | shots | contact t1 t2 ... | A B out.mp4
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clean import W, H, FPS, PAPER, PAPER_D, F, cl, e_out, e_io
import power2 as P2
import toon as T
import respect2 as R2
import respect3 as R3
import kutta as K1                       # the grey insan, the throne, the crown, the snow
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'husky'))
import dog_husky as DH                   # v5: the golden dog is a CC0 Husky rig (Quaternius), rendered by husky/dogrig.py
import cinema9 as C9                     # v9: CHAOS CINEMA layer (grade, bloom, handheld, punches, rain, money, slam title, end stamp)

GROUND = 1320
P2.GY = GROUND                           # SHADE's contact shadow and feet use this ground
OUT_DIR = '/home/user/build/kutta'

INK = (30, 24, 34)
GOLD = (226, 176, 84)
TEAL = (92, 196, 206)
ROYAL = (168, 112, 226)
CORAL = (236, 96, 80)
TXT = (248, 244, 233)
LEATHER = (150, 92, 54)

# ───────────────────────────────────────────── timing (VO fitted by prep_vo_kutta.py)
_TIM = json.load(open('/home/user/build/kutta/vo/timing.json'))
CLIP = _TIM['clips']
CAPW = _TIM['captions']                  # per clip: [(start, end)] chunks, clip-local seconds
LEAD = [0.30, 0.0, 0.0, 0.0]   # VO runs continuously: clip i+1 starts where clip i ends (prep edge 0.05 s each side)
TAIL = [0.0, 0.0, 0.0, 4.1]
CH_LEN = [round(LEAD[i] + CLIP[i] + TAIL[i], 3) for i in range(4)]
SCENE_START = [round(sum(CH_LEN[:i]), 3) for i in range(4)]
DUR_TOTAL = round(sum(CH_LEN), 3)
VO_AT = [round(SCENE_START[i] + LEAD[i], 3) for i in range(4)]
NF = int(round(DUR_TOTAL * FPS))
CHAPTER = ['HOOK', 'LUXURY', 'RAJA', 'GAREEB']
ACC = [GOLD, TEAL, ROYAL, CORAL]
VO_END = round(VO_AT[3] + CLIP[3], 3)                 # last spoken sample
# T_STAMP is defined below SHOT_BY_NAME: the end card lives in the split shot, so it slams once the flare has cleared
T_SLAM = 0.30                                          # v9: hook title first word lands with the crack hit and the VO onset

# shots: (chapter, weight inside the chapter, name)
SHOT_SPEC = [
    (0, .50, 'room_wide'), (0, .50, 'room_close'),
    (1, .22, 'walk'), (1, .16, 'door'), (1, .24, 'drive'), (1, .18, 'bowl'), (1, .20, 'bed'),  # v6: walk longer so the two cube turns never overlap
    (2, .55, 'throne'), (2, .45, 'crown'),
    (3, .40, 'pave'), (3, .28, 'crouch'), (3, .32, 'split'),
]
SHOTS = []
for _ch in range(4):
    _ss = [s for s in SHOT_SPEC if s[0] == _ch]
    _acc = 0.0
    for _j, (_c, _w, _name) in enumerate(_ss):
        _t0 = SCENE_START[_ch] + LEAD[_ch] * 0 + CH_LEN[_ch] * _acc
        SHOTS.append(dict(ch=_ch, j=_j, name=_name, t0=round(_t0, 3)))
        _acc += _w
for _i, _s in enumerate(SHOTS):
    _s['t1'] = SHOTS[_i + 1]['t0'] if _i + 1 < len(SHOTS) else DUR_TOTAL
    _s['k'] = _i
    _s['name_'] = _s['name']
N_SHOTS = len(SHOTS)
SHOT_BY_NAME = {s['name']: s for s in SHOTS}
T_CROWN_LAND = round(SHOT_BY_NAME['crown']['t0'] + .55 * (SHOT_BY_NAME['crown']['t1'] - SHOT_BY_NAME['crown']['t0']), 3)  # v9: crown touchdown
THUNDER = [round(SHOT_BY_NAME['pave']['t0'] + 1.05, 3), round(SHOT_BY_NAME['crouch']['t0'] + .80, 3)]                   # v9: GAREEB lightning
T_STAMP = round(max(VO_END + 0.55, SHOT_BY_NAME['split']['t0'] + 0.35 + 0.12), 3)   # v9.1: stamp sound + slam + punch on the same frame, after the flare (v9 fired the sound 1 s early, in the crouch)

# one transition per boundary (11), no two neighbours alike
# v7: every boundary is a real 3D / parallax move (transitions3d.py): hinged page, depth push-through
# (3 layers per shot), cube turns, origami fold, glass shatter, chroma light flare. No 2D slides.
# v7 gate: fold at drive->bowl (dark->bright) gave a 16.6 luma step/frame (gate < 8). depth's bloom
# carries that pair instead; fold stays on crown->pave where the luma step is 7.2.
PLAN = ['carousel', 'tunnel', 'deck_short', 'shatter', 'carousel', 'tunnel', 'deck', 'shatter', 'carousel', 'tunnel_long', 'flare']   # v9: walk is 1.12 s, so walk->door is the short deck (a long tunnel + deck overlapped: trans_jerk 17); hook->luxury dims the room instead
# v8 fix: pave->crouch is the one tunnel where the bright incoming card covers a dark outgoing one; 1.4 s spreads that luma climb (gate: max dluma < 8)
# blend lengths; half of each sits inside the neighbouring shot (window check: half-sums <= shot length)
TDX = {'carousel': 1.00, 'tunnel': 1.00, 'tunnel_long': 1.60, 'deck': 1.00, 'deck_short': 0.70, 'shatter': 0.80, 'flare': 0.70,
       'page': 1.30, 'depth': 1.20, 'cube_h': 1.00, 'cube_v': 1.10, 'fold': 0.90,
       'zoom': .62, 'sweep': .85, 'slices': .80, 'card': .75, 'ink': .70}
assert len(PLAN) == N_SHOTS - 1, (len(PLAN), N_SHOTS)

HEAD = {
    'room_wide': ('AMEER KA KUTTA?', ['kutta?']),
    'room_close': ('KABHI DEKHA HAI?', ['dekha']),
    'walk': ('AMEER KI CHAAL', ['ameer']),
    'door': ('AC WALI GAADI', ['ac']),
    'drive': ('LUXURY SAFAR', ['luxury']),
    'bowl': ('BRANDED KHANA', ['branded']),
    'bed': ('MAKHMAL KA BISTAR', ['makhmal']),
    'throne': ('RAJA KI TARAH', ['raja']),
    'crown': ('JANWAR, PAR RAJA', ['raja']),
    'pave': ('GAREEB BECHARA', ['gareeb']),
    'crouch': ('JANWAR KI TARAH', ['janwar']),
    'split': ('INSAAN HOKAR BHI', ['insaan']),
}
CAP_TEXT = [
    ['Kabhi kisi Ameer insan ke kutte ko dekha hai?'],
    ['AC wali luxury gaadi mein ghoomta hai,', 'branded khana khata hai,', 'makhmal ke bistar pe sota hai.'],
    ['Ameeron ka kutta janwar hokar bhi Raja ki tarah jeeta hai.'],
    ['Aur gareeb bechara insan hokar bhi,', 'janwaron ki tarah jeeta hai.'],
]
CAP_HOT = [['ameer'], ['ac', 'luxury', 'branded', 'makhmal'], ['raja'], ['gareeb', 'janwaron']]


# ───────────────────────────────────────────── camera keyframes per shot (eased)
CAMK = {
    'room_wide': [(0, 1.03, 0), (1, 1.10, 0)],
    'room_close': [(0, 1.07, 0), (1, 1.15, -20)],
    'walk': [(0, 1.04, 0), (1, 1.06, 0)],
    'door': [(0, 1.05, 0), (1, 1.09, 0)],
    'drive': [(0, 1.03, 0), (1, 1.07, 0)],
    'bowl': [(0, 1.05, 0), (1, 1.12, 0)],
    'bed': [(0, 1.06, 0), (1, 1.12, 0)],
    'throne': [(0, 1.04, 0), (1, 1.10, 0)],
    'crown': [(0, 1.12, 0), (1, 1.05, 0)],
    'pave': [(0, 1.04, 0), (1, 1.07, 0)],
    'crouch': [(0, 1.06, 0), (1, 1.13, 0)],
    'split': [(0, 1.04, 0), (1, 1.10, 0)],
}


def smooth(u):
    u = cl(u)
    return u * u * u * (u * (u * 6 - 15) + 10)


def cam(name, u):
    ks = CAMK[name]
    (u0, z0, p0), (u1, z1, p1) = ks[0], ks[-1]
    s = smooth((u - u0) / max(1e-6, u1 - u0))
    return z0 + (z1 - z0) * s, p0 + (p1 - p0) * s


def pans(name, u, t):
    """(far, mid, near, actor) pan in px. Negative moves the content left (the camera travels right)."""
    if name == 'walk':
        n = -760 * e_io(u)
        return n * .22, n * .55, n, 0.0
    if name == 'drive':
        n = -700 * u
        return n * .18, n * .5, n, 0.0
    if name == 'pave':
        n = -620 * e_io(u)
        return n * .22, n * .55, n, 0.0
    return 0.0, 0.0, 0.0, 0.0


# ───────────────────────────────────────────── backdrops: three planes per kind (world-wide canvases)
BG_W = 3 * W
_BG = {}


def _grad(h, top, bot):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    return (np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t) * np.ones((h, 1, 1), np.float32)


def _plane(kind):
    if kind in _BG:
        return _BG[kind]
    far = Image.new('RGBA', (BG_W, H), (0, 0, 0, 255))
    mid = Image.new('RGBA', (BG_W, H), (0, 0, 0, 0))
    near = Image.new('RGBA', (BG_W, H), (0, 0, 0, 0))
    df, dm, dn = ImageDraw.Draw(far, 'RGBA'), ImageDraw.Draw(mid, 'RGBA'), ImageDraw.Draw(near, 'RGBA')
    ox = W                              # world x = canvas x - ox  (screen x = world x at pan 0)
    if kind == 'room':
        far.paste(Image.fromarray(_grad(H, (20, 16, 30), (46, 36, 62)).astype(np.uint8)).resize((BG_W, H)), (0, 0))
        glow = Image.new('RGBA', (BG_W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([ox + 540 - 720, 300, ox + 540 + 720, 1400], fill=(226, 176, 84, 70))
        far.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
        for x in range(-200, 2 * W, 520):   # pillars (mid)
            dm.rectangle([ox + x, 0, ox + x + 70, 1080], fill=(34, 28, 44, 230))
            dm.rectangle([ox + x - 14, 1060, ox + x + 84, 1090], fill=(60, 50, 74, 230))
        # paper floor with the diagonal seam (near)
        yy = np.arange(H, dtype=np.float32)[:, None]
        xx = np.arange(BG_W, dtype=np.float32)[None, :]
        seam = 1010 - 60 * (xx - ox) / W
        k2 = np.clip((yy - 1000) / 920.0, 0, 1)[..., None]
        pap = np.array(PAPER, np.float32) * (1 - k2) + np.array(PAPER_D, np.float32) * k2
        m = (yy >= seam)
        arr = np.zeros((H, BG_W, 4), np.uint8)
        arr[..., :3] = pap.astype(np.uint8)
        arr[..., 3] = (m * 255).astype(np.uint8)
        near.paste(Image.fromarray(arr, 'RGBA'))
        dn.line([(0, 1010), (BG_W, 950)], fill=GOLD + (255,), width=5)
    elif kind == 'palace':
        far.paste(Image.fromarray(_grad(H, (34, 18, 44), (70, 36, 80)).astype(np.uint8)).resize((BG_W, H)), (0, 0))
        for x in range(-200, 2 * W, 620):   # arches (far)
            df.rounded_rectangle([ox + x, 360, ox + x + 300, 1040], 150, outline=(120, 80, 110, 160), width=6)
        for x in range(-200, 2 * W, 520):   # columns (mid)
            dm.rectangle([ox + x, 260, ox + x + 84, 1100], fill=(74, 52, 80, 235))
            dm.rectangle([ox + x - 16, 240, ox + x + 100, 280], fill=(226, 176, 84, 210))
        # marble floor with converging lines (near)
        dn.rectangle([0, 1000, BG_W, H], fill=(44, 28, 52, 255))
        vx, vy = ox + 540, 1000
        for x in range(-2400, 2 * W + 2400, 260):
            dn.line([(vx, vy), (ox + x, H)], fill=(226, 176, 84, 90), width=3)
        for y in (1080, 1200, 1360, 1560, 1800):
            dn.line([(0, y), (BG_W, y)], fill=(226, 176, 84, 60), width=2)
    elif kind in ('street', 'pave'):
        dim = kind == 'pave'
        sky = ((16, 20, 36), (36, 44, 70)) if not dim else ((30, 30, 40), (56, 56, 66))
        far.paste(Image.fromarray(_grad(H, sky[0], sky[1]).astype(np.uint8)).resize((BG_W, H)), (0, 0))
        rnd = np.random.default_rng(3)
        x = -300
        while x < 2 * W:                   # skyline (far), lit windows
            bw = int(rnd.integers(150, 260)); bh = int(rnd.integers(380, 820))
            col = (34, 40, 66) if not dim else (60, 62, 74)
            df.rectangle([ox + x, 1270 - bh, ox + x + bw, 1270], fill=col + (255,))
            for wy in range(1270 - bh + 30, 1250, 56):
                for wx in range(ox + x + 18, ox + x + bw - 26, 44):
                    if rnd.random() < .45:
                        df.rectangle([wx, wy, wx + 18, wy + 26], fill=(250, 210, 120, 200) if not dim else (120, 120, 130, 180))
            x += bw + int(rnd.integers(10, 60))
        for x in range(-200, 2 * W, 420):  # street lamps (mid) + glow
            dm.rectangle([ox + x, 620, ox + x + 10, 1270], fill=(20, 20, 26, 255))
            dm.ellipse([ox + x - 28, 600, ox + x + 38, 640], fill=(250, 226, 160, 255))
            near_glow = Image.new('RGBA', (BG_W, H), (0, 0, 0, 0))
            ImageDraw.Draw(near_glow).ellipse([ox + x - 120, 520, ox + x + 150, 760], fill=(250, 220, 150, 60))
            mid.alpha_composite(near_glow.filter(ImageFilter.GaussianBlur(40)))
        # road / pavement (near) with dashes that scroll with the camera
        road = (60, 60, 68) if not dim else (96, 94, 100)
        dn.rectangle([0, 1270, BG_W, H], fill=road + (255,))
        dn.rectangle([0, 1262, BG_W, 1280], fill=(120, 116, 124, 255))
        for x in range(-400, 2 * W, 240):
            dn.rectangle([ox + x, 1600, ox + x + 130, 1614], fill=(230, 214, 160, 230))
    _BG[kind] = (far, mid, near)
    return _BG[kind]


def _window(big, pan):
    """screen-sized crop of a world canvas, world content moved by pan px."""
    left = W - int(round(pan))
    return big.crop((left, 0, left + W, H))


def background(kind, pf, pm, pn, blur_far=True):
    far, mid, near = _plane(kind)
    f = _window(far, pf)
    if blur_far:
        f = f.filter(ImageFilter.GaussianBlur(3))
    out = f.copy()
    out.alpha_composite(_window(mid, pm))
    out.alpha_composite(_window(near, pn))
    return out


def _shift(img, dx):
    if abs(dx) < .5:
        return img
    return img.transform((W, H), Image.AFFINE, (1, 0, -dx, 0, 1, 0), resample=Image.BILINEAR)


# ───────────────────────────────────────────── helpers: outlines, catmull, gradient fills
def _catmull(P, seg=10, closed=True):
    out = []
    n = len(P)
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = P[(i - 1) % n] if closed else P[max(0, i - 1)]
        p1 = P[i]
        p2 = P[(i + 1) % n] if closed else P[i + 1]
        p3 = P[(i + 2) % n] if closed else P[min(n - 1, i + 2)]
        for k in range(seg):
            t = k / seg
            t2, t3 = t * t, t * t * t
            x = .5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = .5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    return out


def grad_poly(img, poly, top, bot, alpha=255):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    x0, y0 = max(0, int(min(xs)) - 2), max(0, int(min(ys)) - 2)
    x1, y1 = min(W, int(max(xs)) + 3), min(H, int(max(ys)) + 3)
    if x1 <= x0 or y1 <= y0:
        return
    w, h = x1 - x0, y1 - y0
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).polygon([(x - x0, y - y0) for x, y in poly], fill=alpha)
    g = Image.fromarray(np.broadcast_to(_grad(h, top, bot), (h, w, 3)).astype(np.uint8)).convert('RGBA')
    g.putalpha(mask)
    img.alpha_composite(g, (x0, y0))


def _ell(d, cx, cy, rx, ry, fill, ow=4):
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill, outline=INK, width=ow)


def _leash(d, p0, p1, t):
    (x0, y0), (x1, y1) = p0, p1
    dist = math.hypot(x1 - x0, y1 - y0)
    sag = min(70, .10 * dist) + 5 * math.sin(t * 4.6)
    pts = []
    for k in range(29):
        u = k / 28
        pts.append((x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + sag * 4 * u * (1 - u)))
    d.line(pts, fill=INK + (255,), width=11, joint='curve')
    d.line(pts, fill=LEATHER + (255,), width=6, joint='curve')
    _ell(d, x0, y0, 9, 9, GOLD, 3)              # the handle ring in SHADE's hand


# ───────────────────────────────────────────── SHADE (the black hero) — on the toon rig
def shade(d, lt, x, s, pose, flip=False):
    return P2.hero(d, lt, x, s, pose, 'sly', flip=flip)


def pose_walk(t):
    return T.p_walk(t)


def pose_idle(t):
    return T.p_idle(t)


def pose_bow(t, k=1.0):
    p = dict(T.p_idle(t))
    p['lean'] = 24 * k
    p['head'] = 18 * k
    return p


# ───────────────────────────────────────────── the dog: tag point (for the leash)
def dog_tag(x, gy, s, pose, flip):
    P = K1.DOG[pose]
    tx, ty = P['tag']
    if flip:
        tx = -tx
    return (x + tx * s, gy + ty * s)


def dog_pose_at(t, pose, flip, x, gy, s, d):
    return DH.dog(d, x, gy, s, t, pose, flip=flip)


# ───────────────────────────────────────────── the grey insan (walks, crouches, breathes)
def insan(d, x, gy, s, t, pose='stand', walk=0.0):
    P = K1.MAN[pose]
    bob = (abs(math.sin(walk)) * 6 if pose == 'stand' else math.sin(t * 2.2) * 3) * s

    def Q(px, py):
        return (x + px * s, gy + py * s - bob)
    sx0, sy0 = Q(0, 0)
    d.ellipse([sx0 - 110 * s, sy0 - 14 * s, sx0 + 110 * s, sy0 + 14 * s], fill=(0, 0, 0, 58))
    sw = 34 * math.sin(walk) if pose == 'stand' else 0
    if pose == 'stand':
        for side, sign in (((-38, -180), 1), ((38, -180), -1)):
            hip = (side[0], side[1])
            foot = (side[0] + sw * sign * .6, -2)
            K1._limb(d, Q(*hip), Q(*foot), 40 * s, K1.MAN_PANTS)
    else:
        for (p0, p1) in P['legs']:
            K1._limb(d, Q(*p0), Q(*p1), 40 * s, K1.MAN_PANTS)
        for (p0, p1) in P.get('knees', []):
            K1._limb(d, Q(*p0), Q(*p1), 40 * s, K1.MAN_PANTS)
    tors = [Q(*p) for p in P['torso']]
    d.polygon(tors, fill=K1.MAN_SHIRT, outline=INK)
    hem = [Q(-68, -176), Q(-44, -160), Q(-22, -178), Q(0, -158), Q(24, -178), Q(46, -160), Q(68, -176)]
    d.line(hem, fill=INK, width=int(4 * s) + 2, joint='curve')
    for i, (p0, p1) in enumerate(P['arms']):
        swing = (sw * .8 * (1 if i == 0 else -1)) if pose == 'stand' else 0
        K1._limb(d, Q(*p0), Q(p1[0] + swing, p1[1]), 32 * s, K1.MAN_SHIRT)
    if P.get('bag'):
        bx, byy = Q(P['bag'][0] + (sw * .8 * -1 if pose == 'stand' else 0), P['bag'][1])
        d.rounded_rectangle([bx - 30 * s, byy - 8 * s, bx + 30 * s, byy + 46 * s], 8 * s, fill=(226, 226, 220), outline=INK, width=4)
    hx, hy = P['head']
    c = Q(hx, hy)
    _ell(d, c[0], c[1], P['hr'] * s, P['hr'] * s * 1.08, K1.MAN_SKIN)
    d.pieslice([c[0] - P['hr'] * s * 1.05, c[1] - P['hr'] * s * 1.1, c[0] + P['hr'] * s * 1.05, c[1] + P['hr'] * s * .3], 180, 360, fill=(44, 40, 50), outline=INK, width=4)
    for ex in (-17, 17):
        K1._dot(d, Q(hx + ex, hy + 4), 4.5 * s, INK)


# ───────────────────────────────────────────── the car (realistic side view, shaded)
CS = .95                                   # car scale
BODY = [(0, -18), (6, -78), (30, -120), (62, -164), (172, -200), (262, -216), (366, -318), (560, -334),
        (652, -302), (722, -234), (806, -198), (884, -172), (914, -122), (912, -40), (882, -14),
        (822, -8), (640, -10), (300, -10), (120, -10), (32, -14)]
GLASS_R = [(190, -224), (268, -244), (364, -310), (420, -312), (420, -228)]
GLASS_F = [(438, -228), (438, -312), (556, -320), (640, -290), (708, -232)]
DOOR = [(206, -226), (418, -226), (418, -24), (206, -24)]
WHEEL_R, WHEEL_F = (168, -66), (748, -66)
WHEEL_RAD = 66


def _cp(x0, lx, ly):
    return (x0 + lx * CS, GROUND + ly * CS)


def _cpoly(x0, pts):
    return [_cp(x0, px, py) for px, py in pts]


def car(img, d, x0, door=0.0, wheel=0.0, interior=None, lights=True):
    """draws the car on img (RGBA) with d (ImageDraw on the same img, RGBA mode)."""
    body = _catmull(BODY, 8)
    # ground shadow
    d.ellipse([x0 + 40 * CS, GROUND - 12, x0 + 900 * CS, GROUND + 14], fill=(0, 0, 0, 90))
    grad_poly(img, _cpoly(x0, body), (84, 104, 156), (18, 22, 44))
    # light band across the flanks and a top rim light
    band = [(x, -214 if i < 2 else -150) for i, (x, _) in enumerate([(30, 0), (900, 0)])]
    grad_poly(img, _cpoly(x0, [(60, -150), (880, -150), (880, -206), (560, -262), (60, -190)]), (150, 170, 220), (84, 104, 156), alpha=70)
    d.line(_cpoly(x0, [(262, -216), (366, -318), (560, -334), (652, -302), (722, -234)]), fill=(210, 232, 255, 170), width=3)
    d.line(_cpoly(x0, [(30, -120), (62, -164), (172, -200), (262, -216)]), fill=(150, 200, 230, 110), width=2)
    # cabin tint
    grad_poly(img, _cpoly(x0, GLASS_R), (42, 64, 98), (12, 18, 34), 250)
    grad_poly(img, _cpoly(x0, GLASS_F), (42, 64, 98), (12, 18, 34), 250)
    # door seams, gold rocker trim
    d.line(_cpoly(x0, [(206, -226), (206, -24)]), fill=INK + (255,), width=3)
    d.line(_cpoly(x0, [(40, -34), (900, -34)]), fill=GOLD + (230,), width=4)
    # wheel arches
    for wx, wy in (WHEEL_R, WHEEL_F):
        cx, cy = _cp(x0, wx, wy)
        r = (WHEEL_RAD + 14) * CS
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(10, 12, 20, 255))
    # door: opens about its front hinge (x = 418); the cabin is shown through the gap
    if interior is not None:
        interior(d)
    if door > 0:
        sx = max(.12, math.cos(math.radians(door)))
        hinge = 418
        dp = [(hinge - (hinge - x) * sx, y) for x, y in DOOR]
        dp_s = _cpoly(x0, dp)
        grad_poly(img, dp_s, (84, 104, 156), (18, 22, 44))
        d.line(dp_s + [dp_s[0]], fill=INK + (255,), width=3)
    # glass (over the interior so a passenger reads through it)
    d.polygon(_cpoly(x0, [(190, -224), (268, -244), (364, -310), (420, -312), (420, -228)]), fill=(0, 0, 0, 0))
    # reflection stripes on the glass
    d.polygon(_cpoly(x0, [(230, -300), (300, -234), (330, -234), (262, -300)]), fill=(255, 255, 255, 46))
    d.polygon(_cpoly(x0, [(470, -300), (520, -300), (620, -248), (580, -248)]), fill=(255, 255, 255, 40))
    # lights
    if lights:
        hl = _cp(x0, 898, -130)
        d.ellipse([hl[0] - 14, hl[1] - 8, hl[0] + 14, hl[1] + 8], fill=(255, 252, 230, 255))
        d.ellipse([hl[0] - 36, hl[1] - 22, hl[0] + 36, hl[1] + 22], fill=(255, 250, 220, 60))
        tl = _cp(x0, 14, -124)
        d.rounded_rectangle([tl[0] - 6, tl[1] - 9, tl[0] + 10, tl[1] + 10], 4, fill=(230, 40, 50, 255))
    # side mirror
    mp = _cpoly(x0, [(404, -240), (424, -250), (432, -238), (412, -230)])
    grad_poly(img, mp, (84, 104, 156), (18, 22, 44))
    # wheels
    for wx, wy in (WHEEL_R, WHEEL_F):
        cx, cy = _cp(x0, wx, wy)
        r = WHEEL_RAD * CS
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(14, 14, 18, 255), outline=(0, 0, 0, 255), width=3)
        rr = 44 * CS
        for i in range(10):
            f = i / 9
            col = (int(120 + 110 * f), int(124 + 110 * f), int(134 + 112 * f), 255)
            d.ellipse([cx - rr + i * 2.5, cy - rr + i * 2.5, cx + rr - i * 2.5, cy + rr - i * 2.5], outline=col, width=2)
        for k in range(5):
            a = wheel + k * 2 * math.pi / 5
            ex, ey = cx + math.cos(a) * rr * .92, cy + math.sin(a) * rr * .92
            d.line([(cx, cy), (ex, ey)], fill=(70, 74, 84, 255), width=int(7 * CS) + 1)
        d.ellipse([cx - 11 * CS, cy - 11 * CS, cx + 11 * CS, cy + 11 * CS], fill=GOLD + (255,), outline=INK, width=2)


def car_interior(x0):
    def _f(d):
        a = _cp(x0, 214, -226)
        b = _cp(x0, 430, -22)
        d.rectangle([a[0], a[1], b[0], b[1]], fill=(28, 24, 34, 255))
        for sx0, sx1 in ((214, 400),):
            seat = _cpoly(x0, [(sx0, -150), (sx1, -150), (sx1, -70), (sx0, -70)])
            d.polygon(seat, fill=(110, 72, 46, 255), outline=INK)
    return _f


# ───────────────────────────────────────────── the bowl, the mat, the velvet bed
def bowl_prop(d, x, y, t):
    d.rounded_rectangle([x - 240, y - 6, x + 240, y + 90], 26, fill=(176, 36, 40, 255), outline=INK, width=4)
    d.pieslice([x - 130, y - 16, x + 130, y + 64], 0, 180, fill=(206, 212, 222, 255), outline=INK, width=5)
    d.ellipse([x - 130, y - 14, x + 130, y + 14], fill=(170, 150, 120, 255), outline=INK, width=4)
    rnd = np.random.default_rng(11)
    for _ in range(26):
        kx = x - 110 + rnd.random() * 220
        ky = y - 4 + rnd.random() * 14
        d.ellipse([kx - 9, ky - 6, kx + 9, ky + 6], fill=(150, 96, 52, 255), outline=INK, width=2)
    pulse = 1.0 + .03 * math.sin(t * 5.0)
    ty = y + 40
    d.rounded_rectangle([x - 116 * pulse, ty - 26 * pulse, x + 116 * pulse, ty + 26 * pulse], 20, fill=GOLD + (255,), outline=INK, width=4)
    d.text((x, ty), 'BRANDED', font=F(32, 800), fill=INK + (255,), anchor='mm')


def velvet_bed(d, t):
    d.rounded_rectangle([150, 1186, 930, 1338], 70, fill=(96, 40, 92, 255), outline=INK, width=5)
    d.rounded_rectangle([168, 1200, 912, 1324], 58, outline=GOLD + (255,), width=5)
    d.ellipse([210, 1204, 520, 1240], fill=(150, 80, 150, 90))
    d.ellipse([600, 1204, 900, 1236], fill=(150, 80, 150, 70))


def _zz(d, x, y, t):
    for i in range(3):
        ph = (t * .45 + i / 3.0) % 1.0
        a = int(230 * math.sin(math.pi * ph))
        if a > 0:
            d.text((x + i * 46 + 30 * ph, y - 150 * ph), 'Z', font=F(int(44 + 26 * ph), 800), fill=(250, 246, 236, a), anchor='lm')


# ───────────────────────────────────────────── shot actors (drawn on an RGBA layer, screen coords)
def draw_actors(name, lay, d, t, u, lt):
    if name == 'room_wide':
        dog_x = 710
        d.ellipse([430 - 260, GROUND - 6, 430 + 260, GROUND + 30], fill=(0, 0, 0, 60))
        h = shade(d, lt, 430, 600, pose_idle(t))
        tag = dog_tag(dog_x, GROUND, 1.0, 'sit', False)
        if h:
            _leash(d, (h['hand_r'][0], h['hand_r'][1]), tag, t)
        DH.dog(d, dog_x, GROUND, 1.0, t, 'sit')
    elif name == 'room_close':
        h = shade(d, lt, 360, 860, pose_idle(t))
        dog_x = 740
        tag = dog_tag(dog_x, GROUND, 1.4, 'stand', False)
        if h:
            _leash(d, (h['hand_r'][0], h['hand_r'][1]), tag, t)
        DH.dog(d, dog_x, GROUND, 1.4, t, 'stand')
    elif name == 'walk':
        walk = 14 * t
        dog_x = 210
        p = pose_walk(lt)
        h = shade(d, lt, 470, 560, p)
        tag = dog_tag(dog_x, GROUND - 2, .9, 'stand', False)
        if h:
            _leash(d, (h['hand_r'][0], h['hand_r'][1]), tag, t)
        DH.dog(d, dog_x, GROUND - 2 * abs(math.sin(walk)), .9, t, 'walk')
    elif name == 'door':
        x0 = 60
        dang = 0.0
        if u > .16:
            dang = 72 * smooth((u - .16) / .22)
        if u > .70:
            dang = 72 * (1 - smooth((u - .70) / .14))
        wheel = 0.0
        car(lay, d, x0, door=dang, wheel=wheel, interior=car_interior(x0))
        hl = _cp(x0, 898, -130)
        C9.light_cone(lay, hl[0], hl[1], length=420, spread=150, a=60)          # v9: headlight beam (bloom picks it up)
        h = shade(d, lt, 170, 460, pose_idle(t))
        # dog: on the ground by the open door, then hops onto the seat (u .36 to .56)
        if u < .36:
            dog_x, dog_y, dog_pose = 268, GROUND, 'stand'
            s_dog = .7
        elif u < .56:
            k = smooth((u - .36) / .20)
            dog_x = 268 + (352 - 268) * k
            dog_y = GROUND - 150 * math.sin(math.pi * k) * .9
            dog_pose = 'stand'
            s_dog = .7
        else:
            dog_x, dog_y, dog_pose = 352, GROUND - 14, 'sit'
            s_dog = .70
        tag = dog_tag(dog_x, dog_y, s_dog, dog_pose, False)
        if h:
            _leash(d, (h['hand_r'][0], h['hand_r'][1]), tag, t)
        DH.dog(d, dog_x, dog_y, s_dog, t, dog_pose)
    elif name == 'drive':
        us = cl(u)
        x0 = 60 + 620 * (us * us * us * (us * (us * 6 - 15) + 10))     # smootherstep: no accel jolt at either end
        lay.alpha_composite(C9.speed_streaks(t))                        # v9: night-drive light streaks behind the car
        car(lay, d, x0, door=0.0, wheel=t * 14.0, interior=None)
        hl = _cp(x0, 898, -130)
        C9.light_cone(lay, hl[0], hl[1], length=520, spread=170, a=70)
        # SHADE at the wheel, seen through the windshield: the figure is drawn on its own layer and
        # masked to the two glass panes, so only the part behind the glass shows (the car body hides the rest)
        drv = Image.new('RGBA', lay.size, (0, 0, 0, 0))
        P2.hero(ImageDraw.Draw(drv), lt, x0 + 540 * CS, 330, pose_idle(t), 'sly', flip=False, bob=-34.0)
        # v9: the dog rides INSIDE: drawn on the same layer, so only its head shows through the rear window
        DH.dog(ImageDraw.Draw(drv, 'RGBA'), x0 + 290 * CS, GROUND - 60, .66, t, 'sit')
        mk = Image.new('L', lay.size, 0)
        mdr = ImageDraw.Draw(mk)
        mdr.polygon(_cpoly(x0, GLASS_F), fill=255)
        mdr.polygon(_cpoly(x0, GLASS_R), fill=255)
        drv.putalpha(Image.fromarray(np.minimum(np.asarray(drv.getchannel('A')), np.asarray(mk))))
        lay.alpha_composite(drv)
        _snow_from(d, x0, t)
        _ac_toggle(d, u, t)
    elif name == 'bowl':
        C9.money_rain(lay, t, SHOT_BY_NAME['bowl']['t0'] - .6, n=20, seed=21)      # v9: it rains money on the branded dinner
        bowl_prop(d, 760, GROUND, t)
        DH.dog(d, 540, GROUND, .95, t, 'eat')
        h = shade(d, lt, 985, 460, pose_idle(t), flip=True)
    elif name == 'bed':
        C9.god_rays(lay, t, 540, -200, col=(200, 150, 255), n=7, a=30, spin=0.05)  # v9: velvet moonlight
        C9.money_rain(lay, t, SHOT_BY_NAME['bed']['t0'] - .8, n=12, seed=33, speed=420.0)
        velvet_bed(d, t)
        DH.dog(d, 520, 1210, 1.18, t, 'lie')
        _zz(d, 740, 960, t)
    elif name == 'throne':
        _rays(d, t)
        C9.god_rays(lay, t, 470, 560, col=(255, 220, 140), n=11, a=34, spin=0.10)   # v9: the throne is lit like an altar
        K1._throne(d)
        DH.dog(d, 470, 1262, 1.24, t, 'sit')
        h = shade(d, lt, 880, 500, pose_bow(t), flip=True)
        if h:
            _leash(d, (h['hand_r'][0], h['hand_r'][1]), dog_tag(470, 1262, 1.24, 'sit', False), t)
    elif name == 'crown':
        _rays(d, t)
        K1._throne(d)
        DH.dog(d, 470, 1262, 1.24, t, 'sit')
        k = 1 - smooth(u / .4)
        h = shade(d, lt, 880, 500, pose_bow(t, k), flip=True)
        hy_top = 1262 - 330 * 1.24 - 84 * 1.24 - 46
        drop = cl(u / .55)
        y = 300 + (hy_top - 300) * (1 - (1 - drop) ** 3)
        if drop >= 1 and u < .55 + .18:
            y = hy_top - 14 * math.sin((u - .55) / .18 * math.pi) * (1 - (u - .55) / .18)
        K1._crown(d, 470, y, 1.25)
        if u > .7:
            for i in range(6):
                a = (t * 2 + i) % 1.0
                ang = i * math.pi / 3 + t * 1.5
                r = 110 + 40 * a
                K1._sparkle(d, 470 + math.cos(ang) * r, hy_top - 40 + math.sin(ang) * r * .5, 12, int(240 * (1 - a)))
        # v9: the crown LANDS. shockwave ring, gold confetti burst, dust at the dog's paws
        t_land = T_CROWN_LAND
        C9.shockwave(lay, t, t_land, 470, hy_top + 10, col=(255, 236, 190), rmax=640)
        C9.dust_puff(lay, t, t_land, 470, 1262, col=(200, 170, 120))
        C9.confetti(lay, t, t_land, 470, hy_top - 20, n=56, seed=7)
    elif name == 'pave':
        walk = 12 * t
        lay.alpha_composite(C9.rain_layer(t, strength=.55))                        # v9: far rain behind him
        insan(d, 540 + 10 * math.sin(walk), GROUND, 1.02, t, 'stand', walk=walk)
        C9.breath_fog(lay, t, 540 + 10 * math.sin(walk) - 46, GROUND - 440)
        lay.alpha_composite(C9.rain_layer(t + 7.3, strength=.9))                   # near rain in front
        C9.splashes(d, t, GROUND + 4)
    elif name == 'crouch':
        lay.alpha_composite(C9.rain_layer(t, strength=.55))
        insan(d, 540, GROUND, 1.08, t, 'crouch')
        C9.breath_fog(lay, t, 540 + 44 * 1.08 + 30, GROUND - 318 * 1.08 - 10)
        lay.alpha_composite(C9.rain_layer(t + 7.3, strength=.9))
        C9.splashes(d, t, GROUND + 4, seed=8)
    elif name == 'split':
        # v9: two worlds in one frame. left = warm velvet glow, right = cold rain
        glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([300 - 330, 1240 - 260, 300 + 330, 1240 + 220], fill=(226, 150, 90, 70))
        lay.alpha_composite(glow.filter(ImageFilter.GaussianBlur(70)))
        lay.alpha_composite(C9.rain_layer(t, strength=.55, half='right'))
        d.rounded_rectangle([160, 1236, 430, 1330], 40, fill=(96, 40, 92, 255), outline=INK, width=4)
        DH.dog(d, 300, 1300, .86, t, 'lie')      # v5: lies on the velvet cushion (a standing dog on a cushion read wrong)
        insan(d, 790, GROUND, 1.02, t, 'stand')
        C9.breath_fog(lay, t, 790 - 46, GROUND - 440)
        lay.alpha_composite(C9.rain_layer(t + 7.3, strength=.9, half='right'))
        C9.splashes(d, t, GROUND + 4, half='right', seed=9)
        d.line([(540, 700), (540, 1320)], fill=(60, 56, 66, 170), width=3)


def _rays(d, t):
    for i in range(7):
        a = -0.9 + i * 0.3 + math.sin(t * .6) * .05
        d.polygon([(540, 620), (540 + 1600 * math.cos(a - .05), 620 + 1600 * math.sin(a - .05)),
                   (540 + 1600 * math.cos(a + .05), 620 + 1600 * math.sin(a + .05))], fill=ROYAL + (34,))


def _snow_from(d, x0, t):
    for i in range(14):
        ph = (t * .55 + i * .137) % 1.0
        x = x0 + 300 + (i * 37) % 340 + math.sin(t * 1.3 + i) * 14
        y = GROUND - 330 * CS + ph * 200
        a = int(200 * math.sin(math.pi * ph))
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(230, 252, 255, a))


def _ac_toggle(d, u, t):
    """motion graphic: AC card, the switch slides on (u .18 to .34)."""
    k = smooth((u - .18) / .16)
    x, y = 690, 600
    d.rounded_rectangle([x, y, x + 290, y + 96], 26, fill=(14, 18, 30, 210), outline=TEAL + (255,), width=3)
    d.text((x + 24, y + 48), 'AC', font=F(38, 800), fill=TXT + (255,), anchor='lm')
    px0, px1 = x + 118, x + 246
    kx = px0 + (px1 - px0) * k
    d.rounded_rectangle([px0, y + 26, px1, y + 70], 22, fill=(TEAL if k > .5 else (70, 70, 80)) + (255,))
    d.ellipse([kx - 18, y + 30, kx + 18, y + 66], fill=(250, 250, 250, 255))


# ───────────────────────────────────────────── text: kinetic headline, word-timed captions, chrome
def headline(d, text, hot, p, acc):
    words = text.split()
    f = F(118, 800)
    chars_total = len(text.replace(' ', ''))
    # v3: line breaks are the v2 layout (960 px); a line wider than 860 px shrinks the whole headline
    # (static per headline, so no layout jump inside a transition) to keep a 110 px safe margin.
    lines, cur = [], []
    for w in words:
        trial = ' '.join(cur + [w])
        if f.getlength(trial) > 960 and cur:
            lines.append(cur); cur = [w]
        else:
            cur.append(w)
    lines.append(cur)
    widest = max(f.getlength(' '.join(ln)) for ln in lines)
    if widest > 860:
        f = F(int(118 * 860 / widest), 800)
    idx = 0
    for li, ln in enumerate(lines):
        wid = [f.getlength(w) for w in ln]
        sp = f.getlength(' ')
        tot = sum(wid) + sp * (len(ln) - 1)
        x = 540 - tot / 2
        y = 370 + li * 124
        for w, ww in zip(ln, wid):
            col = acc if w.strip('?,.!').lower() in hot else TXT
            # per-letter drop-in
            cx = x
            for ch in w:
                cl_ = cl(p * (chars_total + 6) - idx)
                if cl_ > 0:
                    drop = (1 - e_out(cl_, 3.0)) * 70
                    cw = f.getlength(ch)
                    # v4: 3D extrusion (9 receding layers, accent-dark to ink) + top gloss, then face
                    for k in range(9, 0, -1):
                        sh = 0.55 + 0.45 * (1 - k / 9)
                        ec = tuple(int(c * sh * 0.45) for c in col)
                        d.text((cx + k * .8, y + drop + k * 1.0), ch, font=f, fill=ec + (int(255 * cl_),), anchor='lm')
                    d.text((cx + 3, y + drop + 10), ch, font=f, fill=(12, 8, 18, int(150 * cl_)), anchor='lm')
                    d.text((cx, y + drop), ch, font=f, fill=col + (int(255 * cl_),), anchor='lm')
                    d.text((cx - 1, y + drop - 2), ch, font=f, fill=(255, 255, 255, int(70 * cl_)), anchor='lm')
                    cx += cw
                else:
                    cx += f.getlength(ch)
                idx += 1
            x += ww + sp


def caption(d, lt, ch, acc):
    """v5 caption: word-timed Roman Urdu on a soft-shadowed plate with an accent top rule.
    The word being spoken gets an accent pill (karaoke); spoken words are full white, upcoming words dim."""
    from PIL import ImageFilter as _IF
    base = Image.Image()._new(d.im)
    for k, (c0, c1) in enumerate(CAPW[ch]):
        t0 = LEAD[ch] + c0
        t1 = LEAD[ch] + c1
        if not (t0 - .1 <= lt < t1 + .35):
            continue
        text = CAP_TEXT[ch][k]
        words = text.split()
        n = len(words)
        p = cl((lt - t0) / max(.1, (t1 - t0)))
        f = F(52, 600)
        lines, cur = [], []
        for w in words:
            trial = ' '.join(cur + [w])
            if f.getlength(trial) > 900 and cur:
                lines.append(cur); cur = [w]
            else:
                cur.append(w)
        lines.append(cur)
        sp = f.getlength(' ')
        blocks = []
        for li, ln in enumerate(lines):
            wid = [f.getlength(w) for w in ln]
            tot = sum(wid) + sp * (len(ln) - 1)
            blocks.append((ln, wid, tot, 1562 + li * 72))
        fade = cl((lt - t0) / .15) * cl((t1 + .35 - lt) / .25)
        if fade <= 0:
            continue
        head = p * n * 1.1                       # fractional index of the word being spoken
        # 1) soft drop shadow for the plates
        sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
        shd = ImageDraw.Draw(sh)
        idx = 0
        for ln, wid, tot, y in blocks:
            shd.rounded_rectangle([540 - tot / 2 - 34, y - 38 + 10, 540 + tot / 2 + 34, y + 38 + 10], 30,
                                  fill=(0, 0, 0, int(150 * fade)))
            idx += len(ln)
        sh = sh.filter(_IF.GaussianBlur(14))
        base.alpha_composite(sh)
        # 2) plates: dark glass, 1 px light edge, accent rule on top of the first line
        pl = Image.new('RGBA', base.size, (0, 0, 0, 0))
        pd = ImageDraw.Draw(pl)
        for li, (ln, wid, tot, y) in enumerate(blocks):
            first = cl(head - sum(len(x) for x in lines[:li]))
            if first <= 0:
                continue
            x0, x1 = 540 - tot / 2 - 34, 540 + tot / 2 + 34
            pd.rounded_rectangle([x0, y - 38, x1, y + 38], 30, fill=(16, 12, 24, int(205 * fade * first)),
                                 outline=(255, 255, 255, int(38 * fade * first)), width=2)
            if li == 0:
                pd.rounded_rectangle([x0 + 26, y - 38, x1 - 26, y - 35], 2, fill=acc + (int(230 * fade * first),))
        base.alpha_composite(pl)
        # 3) words: active pill, spoken = white, upcoming = dim; hot words take the accent colour
        tx = ImageDraw.Draw(base, 'RGBA')
        idx = 0
        for ln, wid, tot, y in blocks:
            x = 540 - tot / 2
            for w, ww in zip(ln, wid):
                fr = cl(head - idx)
                if fr > 0:
                    hot_w = w.strip('?,.!').lower() in CAP_HOT[ch]
                    active = 0 <= head - idx < 1.0
                    if active:
                        tx.rounded_rectangle([x - 10, y - 26, x + ww + 10, y + 26], 16, fill=acc + (int(70 * fade),))
                        col = (255, 255, 255)
                    elif head - idx >= 1.0:
                        col = acc if hot_w else TXT
                    else:
                        col = acc if hot_w else TXT
                    tx.text((x, y), w, font=f, fill=col + (int(255 * fade * fr),), anchor='lm')
                else:
                    tx.text((x, y), w, font=f, fill=TXT + (int(120 * fade),), anchor='lm')
                x += ww + sp
                idx += 1
        return


def chrome(d, t, ch, acc):
    y = 142
    d.rounded_rectangle([64, y - 3, W - 64, y + 3], 3, fill=(60, 56, 70))
    fx = 64 + (W - 128) * cl(t / DUR_TOTAL)
    d.rounded_rectangle([64, y - 3, fx, y + 3], 3, fill=acc)
    d.ellipse([fx - 9, y - 9, fx + 9, y + 9], fill=acc)
    d.text((64, 198), f'{ch + 1:02d}', font=F(34, 800), fill=acc, anchor='lm')
    d.text((108, 199), f'/ 04   {CHAPTER[ch]}', font=F(26, 600), fill=(168, 164, 158), anchor='lm')


# ───────────────────────────────────────────── transitions (new: page wipe, light flare)
def tr_page(A, B, p, acc):
    e = e_io(p)
    xc = int(round(W * (1 - e)))
    out = B.astype(np.float32).copy()
    if xc > 0:
        out[:, :xc] = A[:, :xc]
        g0 = max(0, xc - 140)
        if xc > g0:
            ramp = np.linspace(.55, 1.0, xc - g0, dtype=np.float32)[None, :, None]
            out[:, g0:xc] *= ramp
        out[:, xc:xc + 3] = 255.0
    return np.clip(out, 0, 255).astype(np.uint8)


def tr_flare(A, B, p, acc):
    mix = e_io(p)
    base = A.astype(np.float32) * (1 - mix) + B.astype(np.float32) * mix
    amp = math.sin(math.pi * cl(p)) ** 1.5
    cx = -200 + (W + 400) * cl(p)
    cy = 960
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r2 = ((xx - cx) / 420.0) ** 2 + ((yy - cy) / 520.0) ** 2
    glow = np.exp(-r2 * 2.2)[..., None] * amp * 230.0
    streak = np.exp(-((yy - cy) / 9.0) ** 2)[..., None] * np.exp(-((xx - cx) / 700.0) ** 2)[..., None] * amp * 200.0
    col = np.array(acc, np.float32) * .35 + 255 * .65
    out = base + glow * col / 255.0 + streak * col / 255.0
    return np.clip(out, 0, 255).astype(np.uint8)


def tr_zoom_soft(A, B, p, acc):
    """zoom-through with the mix spread over the whole window (respect2's 0.4-wide window made a 20-level luma step)."""
    e = e_io(p)
    ia = R2._gblur(R2._zoom(Image.fromarray(A), 1 + 1.1 * e, W / 2, 760), 14 * e)
    ib = R2._gblur(R2._zoom(Image.fromarray(B), 1 + .45 * (1 - e), W / 2, 760), 10 * (1 - e))
    k = R2._sm(p)
    return (np.asarray(ia).astype(np.float32) * (1 - k) + np.asarray(ib).astype(np.float32) * k).astype(np.uint8)


TRANS = dict(R2.TRANS)
import transitions3d as T3
TRANS['page'] = T3.page_h
TRANS['cube_h'] = T3.cube_h
TRANS['cube_v'] = T3.cube_v
TRANS['fold'] = T3.fold
TRANS['shatter'] = T3.shatter
TRANS['flare'] = T3.flare
TRANS['zoom'] = tr_zoom_soft
import cards3d as C3                    # v8: real 3D card stage (perspective cards, thickness, shadows)
TRANS['carousel'] = C3.carousel
TRANS['tunnel'] = C3.tunnel
TRANS['tunnel_long'] = C3.tunnel
TRANS['deck'] = C3.deck
TRANS['deck_short'] = C3.deck
# 'depth' takes the layered shots (backdrop, actors, ui) instead of flat frames: see frame_rgb_once


def tdur(kind):
    return TDX.get(kind, R2.TD.get(kind, .5))


# ───────────────────────────────────────────── cues for the audio (mux_kutta2 reads these)
def cue_list():
    cues = []
    s = SHOT_BY_NAME
    cues.append((s['room_close']['t0'] + .30, 'jingle', 1.0))
    cues.append((s['room_close']['t0'] + .02, 'lib:modern_shutter', .7))   # 'KABHI DEKHA HAI?' question reveal: camera-shutter flash (v6)
    cues.append((s['walk']['t0'] + .05, 'jingle', .8))
    walk0, walk1 = s['walk']['t0'], s['walk']['t1']
    tt = walk0 + .2
    while tt < walk1 - .1:
        cues.append((tt, 'step', 1.0))
        tt += .42
    cues.append((s['door']['t0'] + .16 * (s['door']['t1'] - s['door']['t0']), 'door_open', 1.0))
    cues.append((s['door']['t0'] + .72 * (s['door']['t1'] - s['door']['t0']), 'door_close', 1.0))
    cues.append((s['door']['t0'] + .40 * (s['door']['t1'] - s['door']['t0']), 'hop', 1.0))
    cues.append((s['drive']['t0'] + .02, 'engine_on', 1.0))
    cues.append((s['drive']['t0'] + .30 * (s['drive']['t1'] - s['drive']['t0']), 'lib:digital_click', 1.0))   # AC switch: crisp digital click (v6)
    cues.append((s['bowl']['t0'] + .85, 'ping', 1.0))
    # v4 licensed-sample placement (50+SFX premium pack), each by meaning of the moment:
    cues.append((s['room_wide']['t0'] + .30, 'lib:crack_flash', 1.0))        # hook title impact
    cues.append((s['bed']['t0'] + .10, 'lib:gleam', 1.0))                    # makhmal bistar: luxury sparkle reveal
    cues.append((s['throne']['t0'] + .05, 'lib:conjure_charge', 1.0))        # Raja throne: regal charge-up
    cues.append((s['crown']['t0'] + .55, 'chime', 1.0))
    cues.append((s['crown']['t0'] + .02, 'lib:lighter_ignite', .6))         # Raja crown: spark ignite (v6)
    cues.append((s['crown']['t0'] + .95, 'lib:synth_sparkle', 1.0))          # crown settles: sparkle
    cues.append((s['crouch']['t0'] - .10, 'lib:riser_click', 1.0))           # climb into the final GAREEB shot
    cues.append((s['crown']['t0'] + .75, 'chime', .6))
    cues.append((s['pave']['t0'] + .2, 'step', .8))
    # v9 CHAOS CINEMA sound: braam under the hook, coins with the money rain, the crown touchdown,
    # thunder on the GAREEB flashes, rain bed under the whole GAREEB chapter, sub drop on the last line, end stamp
    cues.append((0.0, 'braam', 1.0))
    cues.append((T_SLAM, 'impact', 1.0))
    rnd = np.random.default_rng(5)
    for _ in range(7):
        cues.append((float(s['bowl']['t0'] + rnd.uniform(.1, s['bowl']['t1'] - s['bowl']['t0'])), 'coin', float(rnd.uniform(.4, .8))))
    for _ in range(4):
        cues.append((float(s['bed']['t0'] + rnd.uniform(.2, s['bed']['t1'] - s['bed']['t0'])), 'coin', float(rnd.uniform(.3, .5))))
    cues.append((T_CROWN_LAND, 'impact', .9))
    cues.append((T_CROWN_LAND, 'confetti', 1.0))
    for k, tt in enumerate(THUNDER):
        cues.append((tt, 'thunder', 1.0 if k == 0 else .7))
    cues.append((SCENE_START[3] - .3, 'rain', DUR_TOTAL - SCENE_START[3] + .3))
    cues.append((VO_AT[3] - .08, 'sub_drop', 1.0))
    cues.append((T_STAMP, 'impact', .8))
    cues.append((T_STAMP, 'stamp_ring', 1.0))
    # v7 transition sound, placed by what the move does (not one riser on every cut):
    #   shatter -> glass crack sample on the impact frame; fold -> shutter-snap sample at the fold;
    #   the other moves keep the procedural tonal whoosh, starting at the blend start.
    for b in range(N_SHOTS - 1):
        mid = SHOTS[b + 1]['t0']
        if PLAN[b] == 'shatter':
            cues.append((mid, 'lib:crack_flash', 1.0))
        elif PLAN[b] in ('tunnel', 'tunnel_long'):
            cues.append((mid - tdur(PLAN[b]) / 2, 'lib:riser_click', 1.0))
        elif PLAN[b] == 'fold':
            cues.append((mid, 'lib:modern_shutter', 1.0))
        else:
            cues.append((mid - tdur(PLAN[b]) / 2, 'whoosh', float(b)))
    return sorted(cues)


CUES = cue_list()


# ───────────────────────────────────────────── frame assembly
def shot_at(t):
    return max(i for i, s in enumerate(SHOTS) if t >= s['t0'] - 1e-6)


def shot_parts(k, t):
    """A shot as three RGBA layers: (backdrop, actors, ui). depth_push flies them at different speeds;
    shot_img stacks them back into the flat frame (same pixels as the v6 single-canvas draw)."""
    s = SHOTS[k]
    name, ch = s['name'], s['ch']
    acc = ACC[ch]
    lt = t - SCENE_START[ch]
    u = cl((t - s['t0']) / max(1e-6, s['t1'] - s['t0']))
    pf, pm, pn, pa = pans(name, u, t)
    kind = 'room' if name in ('room_wide', 'room_close', 'bowl', 'bed', 'crouch', 'split') else \
        ('palace' if name in ('throne', 'crown') else ('pave' if name == 'pave' else 'street'))
    bg = background(kind, pf, pm, pn, blur_far=True)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay, 'RGBA')
    draw_actors(name, lay, d, t, u, lt)
    lay = _shift(lay, pa)
    ui = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(ui, 'RGBA')
    if name == 'room_wide':
        # v9: the hook title SLAMS in word by word (scale overshoot, 4-frame fade), gold on the payoff word
        C9.slam_words(ui, ['AMEER', 'KA', 'KUTTA?'], [TXT, TXT, acc], t, T_SLAM, 420, gap=.17, sz=150)
    elif name in HEAD:
        txt, hot = HEAD[name]
        headline(d2, txt, hot, cl((t - s['t0']) / .9), acc)
    caption(d2, lt, ch, acc)
    chrome(d2, t, ch, acc)
    if name == 'split':
        C9.end_stamp(ui, t, T_STAMP, y=760)                                # v9: end card inside the hold
    return bg, lay, ui


EXPO = {'bed': .80, 'bowl': .92, 'crouch': .90, 'split': .95}   # v9: night bedroom / dining / rain-night exposure (keeps the bright-room steps under the dluma cap)


def shot_img(k, t):
    bg, lay, ui = shot_parts(k, t)
    cv = bg
    cv.alpha_composite(lay)
    s = SHOTS[k]
    f = EXPO.get(s['name'], 1.0)
    if s['name'] == 'room_close':
        # the lights go down as the question lands (bright room -> dark street would step the luma in the tunnel)
        f *= 1 - .38 * C9.sstep(cl((t - (s['t1'] - .84)) / .70))
    if f < .999:
        arr = np.asarray(cv.convert('RGB')).astype(np.float32) * f
        cv = Image.fromarray(np.clip(arr + .5, 0, 255).astype(np.uint8)).convert('RGBA')
    cv.alpha_composite(ui)
    return np.asarray(cv.convert('RGB'))


def _trans_at(t):
    """(boundary index, eased-free progress p) when t is inside a blend window, else None."""
    for b in range(N_SHOTS - 1):
        bt = SHOTS[b + 1]['t0']
        td = tdur(PLAN[b])
        if bt - td / 2 <= t < bt + td / 2:
            return b, (t - (bt - td / 2)) / td
    return None


def frame_rgb_once(t):
    hit = _trans_at(t)
    if hit is None:
        return shot_img(shot_at(t), t)
    b, p = hit
    kind = PLAN[b]
    acc = ACC[SHOTS[b + 1]['ch']]
    if kind == 'depth':
        return T3.depth_push(shot_parts(b, t), shot_parts(b + 1, t), p, acc)
    return TRANS[kind](shot_img(b, t), shot_img(b + 1, t), p, acc)


MB_SUB = (-0.30, 0.0, 0.30)     # motion blur: sub-frame offsets in frames, inside blend windows only


def frame_rgb(t):
    """Blend windows are motion-blurred: the mean of three sub-frames at -0.3, 0, +0.3 frame.
    Outside the windows it is a single exact frame."""
    if _trans_at(t) is None:
        return frame_rgb_once(t)
    acc = None
    for o in MB_SUB:
        f = frame_rgb_once(t + o / FPS).astype(np.float32)
        acc = f if acc is None else acc + f
    return np.clip(acc / len(MB_SUB) + .5, 0, 255).astype(np.uint8)


def cam_z(t):
    """camera zoom at time t. Inside a transition window the outgoing shot's end zoom and the incoming
    shot's start zoom are blended with the same eased p as the picture (no camera pop at the cut)."""
    for b in range(N_SHOTS - 1):
        bt = SHOTS[b + 1]['t0']
        td = tdur(PLAN[b])
        if bt - td / 2 <= t < bt + td / 2:
            p = e_io((t - (bt - td / 2)) / td)
            sa, sb = SHOTS[b], SHOTS[b + 1]
            # each side uses ITS OWN shot progress at time t, so both ends match the shot cameras exactly
            ua = cl((t - sa['t0']) / max(1e-6, sa['t1'] - sa['t0']))
            ub = cl((t - sb['t0']) / max(1e-6, sb['t1'] - sb['t0']))
            za, _ = cam(sa['name'], ua)
            zb, _ = cam(sb['name'], ub)
            return za + (zb - za) * p
    s = SHOTS[shot_at(t)]
    u = cl((t - s['t0']) / max(1e-6, s['t1'] - s['t0']))
    return cam(s['name'], u)[0]


# ───────────────────────────────────────────── v9 CHAOS CINEMA: punches, flashes, camera, post
def _hot_word_times():
    """absolute times at which the accent (hot) caption words are spoken (same head math as caption())."""
    out = []
    for ch in range(4):
        for k, (c0, c1) in enumerate(CAPW[ch]):
            words = CAP_TEXT[ch][k].split()
            n = len(words)
            for idx, w in enumerate(words):
                if w.strip('?,.!').lower() in CAP_HOT[ch]:
                    out.append(round(SCENE_START[ch] + LEAD[ch] + c0 + (c1 - c0) * idx / (n * 1.1), 3))
    return out


def _build_hits():
    s = SHOT_BY_NAME
    door = s['door']
    punches = [(vt, .55, 1) for vt in VO_AT]                                   # VO onsets
    punches += [(ht, .40, -1) for ht in _hot_word_times()]                     # hot words
    punches += [(door['t0'] + .56 * (door['t1'] - door['t0']), .40, 1)]        # the dog lands on the seat
    punches += [(T_CROWN_LAND, .45, -1), (T_STAMP, .55, 1), (T_SLAM, .55, 1)]
    thunder = THUNDER
    punches += [(tt, .35, -1) for tt in thunder]
    flashes = [(T_SLAM, .06, (255, 236, 200)), (T_CROWN_LAND, .06, (255, 226, 150)),
               (thunder[0], .07, (210, 225, 255)), (thunder[1], .05, (210, 225, 255)), (T_STAMP, .05, (255, 236, 200))]
    return sorted(punches), flashes, thunder


PUNCHES, FLASHES, _ = _build_hits()
_IN_TRANS = None


def punch_at(t):
    """(energy 0..1, signed roll) at t. Punches are suppressed inside blend windows (gate trans_jerk)."""
    if _trans_at(t) is not None:
        return 0.0, 0.0
    e, roll = 0.0, 0.0
    for pt, amp, sgn in PUNCHES:
        v = amp * C9.punch_env(t - pt)
        if v > e:
            e, roll = v, sgn * v
    return e, roll


def flash_at(t):
    amt, col = 0.0, (255, 236, 200)
    for ft, a, c in FLASHES:
        v = a * C9.ramp(t - ft, 8 / FPS, 14 / FPS)
        if v > amt:
            amt, col = v, c
    return amt, col


SHAKE_AMP = [1.0, 1.25, 0.85, 0.6]          # handheld energy per chapter (hook, luxury, raja, gareeb)
VIG_K = [0.10, 0.08, 0.10, 0.22]             # extra vignette per chapter


def _ch_at(t):
    return max(i for i, st in enumerate(SCENE_START) if t >= st - 1e-6)


def _ch_mix(vals, t):
    i = _ch_at(t)
    v = vals[i]
    if i + 1 < 4:
        k = cl((t - (SCENE_START[i + 1] - .35)) / .7)
        v = v + (vals[i + 1] - v) * k
    return v


def render(i):
    t = i / FPS
    pe, roll = punch_at(t)
    z = cam_z(t) * 1.02 * (1 + .045 * pe)
    dx, dy, rot = C9.handheld(t, amp=_ch_mix(SHAKE_AMP, t))
    rot += .55 * roll
    # keep the shake inside the zoom margin (no black edge, gate black_edge_frames)
    mx, my = (W * z - W) / 2 - 4, (H * z - H) / 2 - 4
    need = (H / 2) * math.sin(math.radians(abs(rot)))
    dx = max(-(mx - need), min(mx - need, dx))
    dy = max(-(my - need * W / H), min(my - need * W / H, dy))
    x = frame_rgb(t).astype(np.float32)
    x = C9.chapter_grade(x, t, SCENE_START)
    x = C9.bloom(x, amount=.38, streak=.26, thresh=185.0)
    x = C9.apply_camera(x, z, dx, dy, rot)
    if pe > .08:
        x = C9.chroma(x, 6.0 * pe)
    if pe > .35:
        x = C9.radial_rush(x, .55 * (pe - .35) / .65, cy=.42)
    g = R3._grade(x)
    g = C9.vignette(g, _ch_mix(VIG_K, t))
    g = C9.toe_lift(g, 14.0, 90.0)
    fa, fc = flash_at(t)
    g = C9.flash_add(g, fa, fc)
    rng = np.random.default_rng(i)
    g = g + rng.normal(0, 1.3, (H, W, 1)).astype(np.float32)
    return np.clip(g, 0, 255).astype(np.uint8)


def shard(a, b, path):
    import imageio_ffmpeg, time
    FF = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [FF, '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(a, b):
        p.stdin.write(render(i).tobytes())
        if (i - a) % 50 == 49:
            el = time.time() - t0
            print(f'[{a}:{b}] {i - a + 1}/{b - a} {el:.0f}s eta {el / (i - a + 1) * (b - i - 1):.0f}s', flush=True)
    p.stdin.close()
    p.wait()
    assert p.returncode == 0, p.returncode


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    if sys.argv[1] == 'still':
        t = float(sys.argv[2])
        Image.fromarray(render(int(round(t * FPS)))).save(f'{OUT_DIR}/v2_still_{t:.2f}.png')
    elif sys.argv[1] == 'shots':
        print('DUR', DUR_TOTAL, 'frames', NF, 'VO_AT', VO_AT, 'CH_LEN', CH_LEN)
        for s in SHOTS:
            print(f"{s['k']:2d} ch{s['ch'] + 1} {s['name']:10s} {s['t0']:7.3f}-{s['t1']:7.3f} {s['t1'] - s['t0']:5.2f}s"
                  + (f"  -> {PLAN[s['k']]}" if s['k'] < len(PLAN) else ''))
    elif sys.argv[1] == 'contact':
        from PIL import Image as _I, ImageDraw as _D
        ts = [float(x) for x in sys.argv[2:]]
        cols = min(5, len(ts))
        rows = (len(ts) + cols - 1) // cols
        cw, ch = 270, 480
        sheet = _I.new('RGB', (cols * cw, rows * (ch + 26)), (20, 20, 22))
        dd = _D.Draw(sheet)
        for n, t in enumerate(ts):
            im = _I.fromarray(render(int(round(t * FPS)))).resize((cw, ch), _I.LANCZOS)
            x, y = (n % cols) * cw, (n // cols) * (ch + 26)
            sheet.paste(im, (x, y))
            dd.text((x + 6, y + ch + 6), f'{t:.2f}s', fill=(230, 230, 230))
        sheet.save(f'{OUT_DIR}/v2_contact.png')
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        shard(a, b, sys.argv[3])
