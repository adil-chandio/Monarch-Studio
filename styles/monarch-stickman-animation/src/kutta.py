"""kutta.py — "AMEER KA KUTTA" (24 s, 9:16). Same editing grammar as SHADE IZZAT v2/v3, new script:

  Kabhi kisi Ameer insan ke kutte ko dekha hai?
  AC wali luxury gaadi mein ghoomta hai, branded khana khata hai, makhmal ke bistar pe sota hai.
  Ameeron ka kutta janwar hokar bhi Raja ki tarah jeeta hai.
  Aur gareeb bechara insan hokar bhi janwaron ki tarah jeeta hai.

Editing kept from respect2: the picture cuts to the voice, 10 shots, 9 transitions from respect2's library
(TRANS / TD, each boundary its own kind), word-timed captions, chrome (progress + chapter label),
a slow camera push per chapter, a beat punch on each VO onset, and the v3 grade (respect3._grade).
New in this film: the characters (a golden dog in a luxury world, a grey insan on the pavement) drawn
as 2-D cut-outs with animation on every shot (tail wag, breath, blink, bowl peck, crown drop, Zs).

Pure function of t.  CLI:  kutta.py still T | shots | contact t1 t2 ... | A B out.mp4
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clean import W, H, FPS, PAPER, PAPER_D, F, cl, e_out, e_io
import respect2 as R2          # transition library (TRANS, TD)
import respect3 as R3          # v3 grade

# ───────────────────────────────────────────── timeline (VO measured in assets)
VO = [3.20, 6.28, 3.76, 4.36]           # /home/user/build/kutta/vo/k{1..4}.wav
LEAD = [0.60, 0.50, 0.50, 0.50]         # cut -> first sound
TAIL = [0.80, 0.80, 0.80, 1.60]         # last sound -> cut (last: hold on the final card)
CH_LEN = [round(LEAD[i] + VO[i] + TAIL[i], 3) for i in range(4)]
SCENE_START = [round(sum(CH_LEN[:i]), 3) for i in range(4)]
SCENE_END = [round(SCENE_START[i] + CH_LEN[i], 3) for i in range(4)]
DUR_TOTAL = round(sum(CH_LEN), 3)
VO_AT = [round(SCENE_START[i] + LEAD[i], 3) for i in range(4)]
NF = int(round(DUR_TOTAL * FPS))

CHAPTER = ['HOOK', 'LUXURY', 'RAJA', 'GAREEB']
ACC = [(226, 176, 84),      # gold        HOOK
       (92, 196, 206),      # teal (AC)   LUXURY
       (168, 112, 226),     # royal       RAJA
       (236, 96, 80)]       # coral       GAREEB
INK = (34, 28, 38)
FUR, FUR_D = (218, 164, 92), (170, 116, 62)
GOLD = (226, 176, 84)
CHROME = (206, 212, 222)
PLUM = (96, 40, 92)
MAN_SHIRT, MAN_PANTS, MAN_SKIN = (120, 116, 128), (58, 56, 66), (184, 138, 108)
TXT = (248, 244, 233)
CAP_INK = (30, 26, 36)

# shots per chapter: start offsets (s, relative to the chapter start)
SUBCUTS = [[0.0, 2.3], [0.0, 2.5, 4.9], [0.0, 2.6], [0.0, 2.2, 4.4]]
SHOTS = []
for _ch in range(4):
    for _j, _o in enumerate(SUBCUTS[_ch]):
        SHOTS.append(dict(ch=_ch, j=_j, t0=round(SCENE_START[_ch] + _o, 3)))
for _i, _s in enumerate(SHOTS):
    _s['t1'] = SHOTS[_i + 1]['t0'] if _i + 1 < len(SHOTS) else DUR_TOTAL
    _s['k'] = _i
N_SHOTS = len(SHOTS)
# one transition per boundary (9), each different from its neighbour
PLAN = ['whip_h', 'cube_h', 'slices', 'blur', 'card', 'zoom', 'ink', 'sweep', 'slices']   # rev2: iris@9.5 gave 9.1 -> blur
assert len(PLAN) == N_SHOTS - 1

# headlines per shot: (text, hot words)
HEAD = {
    (0, 0): ('AMEER KA KUTTA?', ['kutta?']),
    (0, 1): ('KABHI DEKHA HAI?', ['dekha']),
    (1, 0): ('AC WALI GAADI', ['ac']),
    (1, 1): ('BRANDED KHANA', ['branded']),
    (1, 2): ('MAKHMAL KA BISTAR', ['makhmal']),
    (2, 0): ('RAJA KI TARAH', ['raja']),
    (2, 1): ('JANWAR, PAR RAJA', ['raja']),
    (3, 0): ('GAREEB BECHARA', ['gareeb']),
    (3, 1): ('JANWAR KI TARAH', ['janwar']),
    (3, 2): ('INSAAN HOKAR BHI', ['insaan']),
}
# captions per chapter: (start, end, roman text, hot words), times local to the chapter
CAPS = [
    [(LEAD[0] + .28, LEAD[0] + 2.86, 'Kabhi kisi Ameer insan ke kutte ko dekha hai?', ['ameer'])],
    [(LEAD[1] + .28, LEAD[1] + 2.34, 'AC wali luxury gaadi mein ghoomta hai,', ['ac', 'luxury']),
     (LEAD[1] + 2.68, LEAD[1] + 4.00, 'branded khana khata hai,', ['branded']),
     (LEAD[1] + 4.40, LEAD[1] + 5.88, 'makhmal ke bistar pe sota hai.', ['makhmal'])],
    [(LEAD[2] + .28, LEAD[2] + 3.42, 'Ameeron ka kutta janwar hokar bhi Raja ki tarah jeeta hai.', ['raja'])],
    [(LEAD[3] + .28, LEAD[3] + 2.38, 'Aur gareeb bechara insan hokar bhi', ['gareeb']),
     (LEAD[3] + 2.64, LEAD[3] + 4.02, 'janwaron ki tarah jeeta hai.', ['janwaron'])],
]
SEAM_Y0, SEAM_Y1 = 1010, 950     # the diagonal seam (y at x=0 / x=W)
GY = 1320                        # ground line of the characters (on paper)


# ───────────────────────────────────────────── backdrop (cached per chapter)
_BG = {}


def backdrop(ch):
    if ch in _BG:
        return _BG[ch]
    acc = ACC[ch]
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    seam = SEAM_Y0 + (SEAM_Y1 - SEAM_Y0) * xx / W                      # (1, W)
    k = np.clip(yy / 1000.0, 0, 1)[..., None]
    dark = (np.array([22, 18, 32], np.float32) * (1 - k) + np.array([50, 40, 66], np.float32) * k)
    dark = np.broadcast_to(dark, (H, W, 3)).copy()
    r = np.sqrt(((xx - 540) / 640.0) ** 2 + ((yy - 620) / 780.0) ** 2)
    g = (np.clip(1 - r, 0, 1) ** 2 * 0.30)[..., None]
    dark = dark * (1 - g) + np.array(acc, np.float32) * g * 0.75
    k2 = np.clip((yy - 1000) / 920.0, 0, 1)[..., None]
    paper = np.array(PAPER, np.float32) * (1 - k2) + np.array(PAPER_D, np.float32) * k2
    sh = np.clip(1 - (yy - seam) / 60.0, 0, 1)[..., None] * 0.10
    paper = paper * (1 - sh)
    img = np.where((yy >= seam)[..., None], paper, dark).astype(np.uint8)
    im = Image.fromarray(img).convert('RGBA')
    gl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(gl).line([(0, SEAM_Y0), (W, SEAM_Y1)], fill=acc + (150,), width=34)
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(im).line([(0, SEAM_Y0), (W, SEAM_Y1)], fill=acc + (255,), width=5)
    _BG[ch] = im
    return im


# ───────────────────────────────────────────── drawing helpers (outlined cut-outs)
def _ell(d, cx, cy, rx, ry, fill, ow=5):
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill, outline=INK, width=ow)


def _dot(d, p, r, fill):
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)


def _limb(d, p0, p1, w, fill, ow=5):
    d.line([p0, p1], fill=INK, width=int(w + 2 * ow), joint='curve')
    _dot(d, p0, (w + 2 * ow) / 2, INK)
    _dot(d, p1, (w + 2 * ow) / 2, INK)
    d.line([p0, p1], fill=fill, width=int(w), joint='curve')
    _dot(d, p0, w / 2, fill)
    _dot(d, p1, w / 2, fill)


def _sparkle(d, cx, cy, r, a, col=(255, 250, 230)):
    for ang in (0, math.pi / 2):
        dx, dy = math.cos(ang) * r, math.sin(ang) * r
        d.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], fill=col + (a,), width=4)
    _dot(d, (cx, cy), r * .22, col + (a,))


# ───────────────────────────────────────────── the dog (golden, cut-out, 5 poses)
DOG = {
    'stand': dict(body=(0, -190, 150, 92), head=(150, -290, 78), snout=(218, -270, 52, 36),
                  ear=(108, -262, 26, 58), eye=(160, -312), collar=((110, -228), (184, -218)),
                  tag=(146, -196), back=[((-95, -130), (-100, 0)), ((-50, -130), (-50, 0))],
                  front=[((95, -130), (100, 0)), ((140, -130), (146, 0))],
                  tail=((-150, -200), (-210, -272)), wag=18),
    'sit': dict(body=(-10, -160, 118, 130), head=(40, -330, 84), snout=(130, -300, 56, 40),
                ear=(-12, -300, 28, 64), eye=(70, -350), collar=((0, -270), (72, -262)),
                tag=(40, -236), back=[], front=[((60, -120), (70, 0)), ((100, -120), (108, 0))],
                haunch=(-60, -80, 100, 70), tail=((-130, -60), (-226, -44)), wag=14),
    'eat': dict(body=(0, -190, 150, 92), head=(196, -146, 78), snout=(262, -126, 50, 34),
                ear=(152, -140, 24, 54), eye=(206, -186), collar=((150, -210), (220, -196)),
                tag=(190, -170), back=[((-95, -130), (-100, 0)), ((-50, -130), (-50, 0))],
                front=[((95, -130), (100, 0)), ((140, -130), (146, 0))],
                tail=((-150, -200), (-210, -272)), wag=18),
    'lie': dict(body=(0, -62, 230, 70), head=(220, -94, 74), snout=(280, -82, 46, 30),
                ear=(186, -86, 24, 46), eye=(236, -104), collar=((180, -118), (236, -110)),
                tag=(206, -98), back=[], front=[], paws=[(-150, -22, 52, 22), (120, -18, 58, 20)],
                tail=((-200, -40), (-268, -30)), wag=8, closed=True),
}


def dog(d, x, gy, s, t, pose='stand', flip=False, blink_at=3.4):
    P = DOG[pose]

    def Q(px, py):
        px = -px if flip else px
        return (x + px * s, gy + py * s)

    wag = math.sin(t * 6.8) * P['wag']
    br = math.sin(t * 2.3) * .012
    blink = (t % blink_at) < .12 and not P.get('closed')
    # tail (behind everything)
    (a0, a1) = P['tail']
    tip = (a1[0] + wag * (1 if a1[0] < 0 else -1) * .6, a1[1] - abs(wag) * .5)
    _limb(d, Q(*a0), Q(*tip), 26 * s, FUR_D)
    for (p0, p1) in P['back']:
        _limb(d, Q(*p0), Q(*p1), 34 * s, FUR_D)
    if 'haunch' in P:
        hx, hy, hrx, hry = P['haunch']
        c = Q(hx, hy)
        _ell(d, c[0], c[1], hrx * s, hry * s, FUR_D)
    bx, by, brx, bry = P['body']
    c = Q(bx, by)
    _ell(d, c[0], c[1], brx * s * (1 + br), bry * s * (1 - br), FUR)
    for (p0, p1) in P['front']:
        _limb(d, Q(*p0), Q(*p1), 36 * s, FUR)
    for (cx, cy, rx, ry) in P.get('paws', []):
        c = Q(cx, cy)
        _ell(d, c[0], c[1], rx * s, ry * s, FUR)
    # ears (behind head)
    ex, ey, erx, ery = P['ear']
    c = Q(ex, ey)
    _ell(d, c[0], c[1], erx * s, ery * s, FUR_D)
    hx, hy, hr = P['head']
    c = Q(hx, hy)
    _ell(d, c[0], c[1], hr * s, hr * s * (1 - br * .5), FUR)
    sx, sy, srx, sry = P['snout']
    c = Q(sx, sy)
    _ell(d, c[0], c[1], srx * s, sry * s, FUR)
    nz = Q(sx + srx * .72, sy - sry * .12)
    _dot(d, nz, 12 * s, INK)
    # eye
    ee = Q(*P['eye'])
    if blink or P.get('closed'):
        if P.get('closed'):
            d.arc([ee[0] - 16 * s, ee[1] - 10 * s, ee[0] + 16 * s, ee[1] + 10 * s], 200, 340, fill=INK, width=max(3, int(5 * s)))
        else:
            d.line([(ee[0] - 11 * s, ee[1]), (ee[0] + 11 * s, ee[1])], fill=INK, width=max(3, int(5 * s)))
    else:
        _dot(d, ee, 10 * s, INK)
        _dot(d, (ee[0] + 3 * s, ee[1] - 3 * s), 3 * s, (255, 255, 255))
    # collar + gold diamond tag (with a sparkle that pulses)
    c0, c1 = P['collar']
    _limb(d, Q(*c0), Q(*c1), 24 * s, GOLD, ow=4)
    tx, ty = Q(*P['tag'])
    r = 15 * s
    d.polygon([(tx, ty - r * 1.4), (tx + r, ty), (tx, ty + r * 1.4), (tx - r, ty)], fill=GOLD, outline=INK, width=3)
    ph = (t * 1.6) % 1.0
    if ph < .35:
        _sparkle(d, tx + r * 1.1, ty - r * 1.1, 14 * s * (1 - ph / .35) + 3, int(230 * (1 - ph / .35)))


# ───────────────────────────────────────────── the insan (grey cut-out, 2 poses)
MAN = {
    'stand': dict(head=(0, -432), hr=50, torso=[(-80, -372), (80, -372), (68, -176), (-68, -176)],
                  arms=[((-72, -350), (-100, -206)), ((72, -350), (104, -240))],
                  legs=[((-38, -180), (-46, 0)), ((38, -180), (46, 0))], bag=(118, -236)),
    'crouch': dict(head=(44, -318), hr=50, torso=[(-70, -250), (70, -250), (46, -118), (-46, -118)],
                   arms=[((-58, -236), (-92, -146)), ((58, -236), (88, -150))],
                   legs=[((-30, -120), (-104, -66)), ((30, -120), (100, -66))],
                   knees=[((-104, -66), (-40, 0)), ((100, -66), (42, 0))], bag=None),
}


def man(d, x, gy, s, t, pose='stand', bob=True):
    P = MAN[pose]
    by = math.sin(t * 2.2) * 4 * s if bob else 0.0

    def Q(px, py):
        return (x + px * s, gy + (py * s) + by)

    # shadow on the paper
    sx0, sy0 = Q(0, 0)
    d.ellipse([sx0 - 110 * s, sy0 - 14 * s, sx0 + 110 * s, sy0 + 14 * s], fill=(0, 0, 0, 58))
    for (p0, p1) in P['legs']:
        _limb(d, Q(*p0), Q(*p1), 40 * s, MAN_PANTS)
    for (p0, p1) in P.get('knees', []):
        _limb(d, Q(*p0), Q(*p1), 40 * s, MAN_PANTS)
    tors = [Q(*p) for p in P['torso']]
    d.polygon(tors, fill=MAN_SHIRT, outline=INK)
    # torn hem
    hem = [Q(-68, -176), Q(-44, -160), Q(-22, -178), Q(0, -158), Q(24, -178), Q(46, -160), Q(68, -176)]
    d.line(hem, fill=INK, width=int(4 * s) + 2, joint='curve')
    for (p0, p1) in P['arms']:
        _limb(d, Q(*p0), Q(*p1), 32 * s, MAN_SHIRT)
    if P.get('bag'):
        bx, byy = Q(*P['bag'])
        hl = Q(P['arms'][1][1][0], P['arms'][1][1][1] - 26)
        d.line([hl, (bx, byy - 40 * s)], fill=INK, width=int(4 * s) + 1)
        d.rounded_rectangle([bx - 30 * s, byy - 8 * s, bx + 30 * s, byy + 46 * s], 8 * s,
                            fill=(226, 226, 220), outline=INK, width=4)
    hx, hy = P['head']
    c = Q(hx, hy)
    _ell(d, c[0], c[1], P['hr'] * s, P['hr'] * s * 1.08, MAN_SKIN)
    d.pieslice([c[0] - P['hr'] * s * 1.05, c[1] - P['hr'] * s * 1.1, c[0] + P['hr'] * s * 1.05, c[1] + P['hr'] * s * .3],
               180, 360, fill=(44, 40, 50), outline=INK, width=4)
    for ex in (-17, 17):
        _dot(d, Q(hx + ex, hy + 4), 4.5 * s, INK)
    d.line([Q(hx - 26, hy - 16), Q(hx - 10, hy - 12)], fill=INK, width=int(4 * s) + 1)
    d.line([Q(hx + 10, hy - 12), Q(hx + 26, hy - 16)], fill=INK, width=int(4 * s) + 1)


# ───────────────────────────────────────────── props
def _zz(d, x, y, t0, t):
    for i in range(3):
        ph = ((t - t0) * .45 + i / 3.0) % 1.0
        a = int(230 * math.sin(math.pi * ph))
        if a <= 0:
            continue
        f = F(int(44 + 26 * ph), 800)
        d.text((x + i * 46 + 30 * ph, y - 150 * ph), 'Z', font=f, fill=(250, 246, 236, a), anchor='lm')


def _car(d, t):
    d.line([(0, GY + 2), (W, GY + 2)], fill=(150, 144, 140, 255), width=5)
    off = (t * 520) % 120
    for x in range(-120, W + 120, 120):
        d.line([(x - off, GY + 40), (x - off + 56, GY + 40)], fill=(170, 164, 160, 230), width=6)
    d.rounded_rectangle([110, 1130, 972, 1290], 60, fill=(30, 30, 44), outline=INK, width=5)
    d.polygon([(300, 1140), (384, 930), (742, 930), (846, 1140)], fill=(40, 44, 62), outline=INK)
    d.line([(150, 1236), (930, 1236)], fill=GOLD + (255,), width=5)
    d.ellipse([934, 1186, 968, 1214], fill=(255, 250, 220), outline=INK, width=3)


def _snow(d, t):
    for i in range(14):
        x0 = 330 + (i * 97) % 390
        ph = (t * .55 + i * .137) % 1.0
        x = x0 + math.sin(t * 1.3 + i) * 16
        y = 936 + ph * 200
        a = int(230 * math.sin(math.pi * ph))
        d.ellipse([x - 4.5, y - 4.5, x + 4.5, y + 4.5], fill=(230, 252, 255, a))


def _crown(d, cx, cy, s):
    w, h = 170 * s, 84 * s
    pts = [(cx - w / 2, cy), (cx - w / 2, cy - h * .6), (cx - w * .28, cy - h * .15), (cx, cy - h),
           (cx + w * .28, cy - h * .15), (cx + w / 2, cy - h * .6), (cx + w / 2, cy)]
    d.polygon(pts, fill=GOLD, outline=INK, width=4)
    d.rectangle([cx - w / 2, cy - 10 * s, cx + w / 2, cy + 12 * s], fill=GOLD, outline=INK, width=4)
    for jx, col in ((-w * .28, (168, 112, 226)), (0, (236, 96, 80)), (w * .28, (92, 196, 206))):
        _dot(d, (cx + jx, cy - h * .12 + 2), 9 * s, col)


def _rays(d, t, acc):
    for i in range(7):
        a = -0.9 + i * 0.3 + math.sin(t * .6) * .05
        d.polygon([(540, 620), (540 + 1600 * math.cos(a - .05), 620 + 1600 * math.sin(a - .05)),
                   (540 + 1600 * math.cos(a + .05), 620 + 1600 * math.sin(a + .05))], fill=acc + (34,))


def _throne(d):
    d.rounded_rectangle([330, 700, 750, 1196], 120, fill=(54, 42, 34), outline=GOLD, width=10)
    d.rounded_rectangle([300, 1168, 780, 1250], 28, fill=(98, 72, 40), outline=GOLD, width=8)
    d.rounded_rectangle([352, 740, 728, 1150], 96, outline=(120, 96, 52), width=6)


# ───────────────────────────────────────────── shots (each draws on a transparent RGBA layer)
def shot_layer(k, t, lay, d, lt_ch, u):
    ch, j = SHOTS[k]['ch'], SHOTS[k]['j']
    acc = ACC[ch]
    if (ch, j) == (0, 0):          # the spot, the dog stands, eyes open, tail wag
        d.ellipse([540 - 300, GY - 8, 540 + 300, GY + 36], fill=(0, 0, 0, 60))
        dog(d, 540, GY, 1.42, t, 'stand')
    elif (ch, j) == (0, 1):        # close on the collar tag, slow push
        dog(d, 500, 1470, 2.0, t, 'stand')
    elif (ch, j) == (1, 0):        # the luxury car, AC snow, road moves, wheels spin
        _car(d, t)
        dog(d, 470, 1186, .74, t, 'sit')
        _snow(d, t)
        for i, xx in enumerate((300, 780)):
            ang = t * 9.0 + i
            d.ellipse([xx - 72, 1218, xx + 72, 1362], fill=INK)
            d.ellipse([xx - 36, 1254, xx + 36, 1326], fill=CHROME, outline=INK, width=3)
            for q in range(4):
                a2 = ang + q * math.pi / 2
                d.line([(xx, 1290), (xx + math.cos(a2) * 32, 1290 + math.sin(a2) * 32)], fill=INK, width=5)
        d.polygon([(330, 1140), (398, 966), (530, 966), (530, 1140)], fill=(92, 140, 176, 90))
        d.polygon([(560, 1140), (560, 966), (724, 966), (818, 1140)], fill=(92, 140, 176, 90))
    elif (ch, j) == (1, 1):        # brand bowl, dog pecks at it (head bob)
        dog(d, 360, GY, 1.36, t, 'eat')
        d.pieslice([540, 1236, 860, 1344], 0, 180, fill=CHROME, outline=INK, width=5)
        d.ellipse([540, 1246, 860, 1282], fill=(190, 150, 90), outline=INK, width=4)
        rnd = np.random.default_rng(7)
        for _ in range(26):
            x = 570 + rnd.random() * 260
            y = 1254 + rnd.random() * 22
            d.ellipse([x - 9, y - 6, x + 9, y + 6], fill=(150, 96, 52), outline=INK, width=2)
        pulse = 1.0 + .03 * math.sin(t * 5.0)
        d.rounded_rectangle([660 - 116 * pulse, 1040 - 36 * pulse, 660 + 116 * pulse, 1040 + 36 * pulse], 22,
                            fill=GOLD, outline=INK, width=4)
        d.text((660, 1040), 'BRANDED', font=F(36, 800), fill=INK, anchor='mm')
    elif (ch, j) == (1, 2):        # the velvet bed, Zs drift up
        d.rounded_rectangle([150, 1186, 930, 1338], 70, fill=PLUM, outline=INK, width=5)
        d.rounded_rectangle([168, 1200, 912, 1324], 58, outline=GOLD, width=5)
        d.ellipse([210, 1204, 520, 1240], fill=(150, 80, 150, 90))
        dog(d, 520, 1210, 1.18, t, 'lie')
        _zz(d, 740, 960, 0.0, t)
    elif (ch, j) == (2, 0):        # the throne, the dog sits, rays
        _rays(d, t, acc)
        _throne(d)
        dog(d, 540, 1262, 1.24, t, 'sit')
    elif (ch, j) == (2, 1):        # the crown drops onto the head, sparkles after the landing
        _rays(d, t, acc)
        _throne(d)
        dog(d, 540, 1262, 1.24, t, 'sit')
        hy_top = 1262 - 330 * 1.24 - 84 * 1.24 - 46
        drop = max(0.0, min(1.0, u / .55))
        y = 300 + (hy_top - 300) * (1 - (1 - drop) ** 3) if drop < 1 else hy_top
        if drop >= 1 and u < .55 + .18:
            y = hy_top - 14 * math.sin((u - .55) / .18 * math.pi) * (1 - (u - .55) / .18)
        _crown(d, 540, y, 1.25)
        for i in range(6):
            if u > .7:
                a = (t * 2 + i) % 1.0
                ang = i * math.pi / 3 + t * 1.5
                r = 110 + 40 * a
                _sparkle(d, 540 + math.cos(ang) * r, hy_top - 40 + math.sin(ang) * r * .5, 12, int(240 * (1 - a)))
    elif (ch, j) == (3, 0):        # the insan on the pavement, a small hunch, the bag
        d.line([(0, GY + 36), (W, GY + 36)], fill=(170, 164, 160, 255), width=4)
        for x in range(-40, W + 60, 130):
            d.line([(x, GY + 80), (x + 60, GY + 80)], fill=(196, 190, 184, 255), width=3)
        man(d, 540, GY, 1.36, t, 'stand')
    elif (ch, j) == (3, 1):        # crouch, the animal posture, breathing
        man(d, 540, GY, 1.36, t, 'crouch')
    elif (ch, j) == (3, 2):        # split: dog on the cushion (left) vs insan (right)
        d.rounded_rectangle([168, 1238, 430, 1330], 40, fill=PLUM, outline=INK, width=4)
        dog(d, 300, 1282, .86, t, 'sit')
        man(d, 770, GY, .98, t, 'stand')
        d.line([(540, 700), (540, 1320)], fill=(60, 56, 66, 170), width=3)


def caption(d, lt, ch, acc):
    for (t0, t1, txt, hot) in CAPS[ch]:
        if t0 <= lt < t1 + .35:
            words = txt.split()
            n = len(words)
            p = cl((lt - t0) / max(.1, (t1 - t0)) * 1.12)
            f = F(50, 600)
            # wrap to 940 px
            lines, cur = [], []
            for w in words:
                trial = ' '.join(cur + [w])
                if f.getlength(trial) > 940 and cur:
                    lines.append(cur)
                    cur = [w]
                else:
                    cur.append(w)
            lines.append(cur)
            idx = 0
            for li, ln in enumerate(lines):
                wid = [f.getlength(w) for w in ln]
                sp = f.getlength(' ')
                tot = sum(wid) + sp * (len(ln) - 1)
                x = 540 - tot / 2
                y = 1560 + li * 62
                for w, ww in zip(ln, wid):
                    fr = cl(p * n - idx)
                    if fr > 0:
                        hot_w = w.strip('?,.!').lower() in hot
                        col = acc if hot_w else CAP_INK
                        d.text((x, y), w, font=f, fill=col + (int(255 * fr),), anchor='lm')
                    x += ww + sp
                    idx += 1
            return


def headline(d, text, hot, p, acc):
    words = text.split()
    n = len(words)
    f = F(118, 800)
    lines, cur = [], []
    for w in words:
        trial = ' '.join(cur + [w])
        if f.getlength(trial) > 960 and cur:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    lines.append(cur)
    idx = 0
    y0 = 370
    for li, ln in enumerate(lines):
        wid = [f.getlength(w) for w in ln]
        sp = f.getlength(' ')
        tot = sum(wid) + sp * (len(ln) - 1)
        x = 540 - tot / 2
        y = y0 + li * 124
        for w, ww in zip(ln, wid):
            rv = cl(p * (n + 1) - idx)
            if rv > 0:
                rise = (1 - e_out(rv)) * 40
                d.text((x + 5, y + rise + 7), w, font=f, fill=(20, 14, 26, int(255 * rv)), anchor='lm')
                col = acc if w.strip('?,.!').lower() in hot else TXT
                d.text((x, y + rise), w, font=f, fill=col + (int(255 * rv),), anchor='lm')
            x += ww + sp
            idx += 1


def chrome(d, t, ch, acc):
    y = 142
    d.rounded_rectangle([64, y - 3, W - 64, y + 3], 3, fill=(60, 56, 70))
    fx = 64 + (W - 128) * cl(t / DUR_TOTAL)
    d.rounded_rectangle([64, y - 3, fx, y + 3], 3, fill=acc)
    d.ellipse([fx - 9, y - 9, fx + 9, y + 9], fill=acc)
    d.text((64, 198), f'{ch + 1:02d}', font=F(34, 800), fill=acc, anchor='lm')
    d.text((108, 199), f'/ 04   {CHAPTER[ch]}', font=F(26, 600), fill=(168, 164, 158), anchor='lm')


def shot_img(k, t):
    s = SHOTS[k]
    ch, j = s['ch'], s['j']
    acc = ACC[ch]
    lt = t - SCENE_START[ch]
    u = max(0.0, t - s['t0'])
    cv = backdrop(ch).copy()
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay, 'RGBA')
    shot_layer(k, t, lay, d, lt, u)
    cv.alpha_composite(lay)
    d2 = ImageDraw.Draw(cv, 'RGBA')
    if (ch, j) in HEAD:
        txt, hot = HEAD[(ch, j)]
        headline(d2, txt, hot, cl(u / .55), acc)
    caption(d2, lt, ch, acc)
    chrome(d2, t, ch, acc)
    return np.asarray(cv.convert('RGB'))


# ───────────────────────────────────────────── frame assembly (transitions, camera, punch, grade)
def shot_at(t):
    return max(i for i, s in enumerate(SHOTS) if t >= s['t0'] - 1e-6)


def frame_rgb(t):
    k = shot_at(t)
    for b in range(N_SHOTS - 1):
        bt = SHOTS[b + 1]['t0']
        td = R2.TD[PLAN[b]]
        if bt - td / 2 <= t < bt + td / 2:
            p = (t - (bt - td / 2)) / td
            A = shot_img(b, t)
            B = shot_img(b + 1, t)
            return R2.TRANS[PLAN[b]](A, B, p, ACC[SHOTS[b + 1]['ch']])
    return shot_img(k, t)


def render(i):
    t = i / FPS
    ch = max(c for c in range(4) if t >= SCENE_START[c] - 1e-6)
    lt = t - SCENE_START[ch]
    u = cl(lt / CH_LEN[ch])
    # camera: a slow push on every chapter (alternating), a drift, and the beat punch
    z = 1.04 + .03 * (e_io(u) if ch % 2 == 0 else 1 - e_io(u))
    pun = 0.0
    for vt in VO_AT:
        dd = t - vt
        if 0 <= dd < .6:
            pun = max(pun, math.exp(-dd / .11))
    z = min(1.11, z * (1 + .016 * pun))
    arr = frame_rgb(t)
    iz = 1.0 / z
    mx, my = (W - W * iz) / 2, (H - H * iz) / 2
    dx = max(-mx, min(mx, 11 * math.sin(t * .71)))
    dy = max(-my, min(my, 13 * math.sin(t * .53 + 1.0)))
    frame = Image.fromarray(arr).transform((W, H), Image.AFFINE,
                                           (iz, 0, mx + dx, 0, iz, my + dy), Image.BICUBIC)
    g = R3._grade(np.asarray(frame))
    rng = np.random.default_rng(i)
    g = g + rng.normal(0, 1.6, (H, W, 1)).astype(np.float32)
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
    out_dir = '/home/user/build/kutta'
    os.makedirs(out_dir, exist_ok=True)
    if sys.argv[1] == 'still':
        t = float(sys.argv[2])
        Image.fromarray(render(int(round(t * FPS)))).save(f'{out_dir}/still_{t:.2f}.png')
    elif sys.argv[1] == 'shots':
        print('DUR', DUR_TOTAL, 'frames', NF, 'VO_AT', VO_AT)
        for s in SHOTS:
            print(f"{s['k']:2d} ch{s['ch'] + 1} j{s['j']} {s['t0']:7.3f}-{s['t1']:7.3f} {s['t1'] - s['t0']:5.2f}s"
                  + (f"  -> {PLAN[s['k']]}" if s['k'] < len(PLAN) else ''))
    elif sys.argv[1] == 'contact':
        from PIL import Image as _I
        ts = [float(x) for x in sys.argv[2:]]
        cols = min(5, len(ts))
        rows = (len(ts) + cols - 1) // cols
        cw, ch = 270, 480
        sheet = _I.new('RGB', (cols * cw, rows * (ch + 26)), (20, 20, 22))
        from PIL import ImageDraw as _D
        dd = _D.Draw(sheet)
        for n, t in enumerate(ts):
            im = _I.fromarray(render(int(round(t * FPS)))).resize((cw, ch), _I.LANCZOS)
            x, y = (n % cols) * cw, (n // cols) * (ch + 26)
            sheet.paste(im, (x, y))
            dd.text((x + 6, y + ch + 6), f'{t:.2f}s', fill=(230, 230, 230))
        sheet.save(f'{out_dir}/contact.png')
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        shard(a, b, sys.argv[3])
