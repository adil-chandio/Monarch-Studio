"""
charsheet.py — renders the BUDDY character sheets as PNG posters.
Run:  python3 src/charsheet.py
Out:  character_sheet_1_identity.png
      character_sheet_2_expressions.png
      character_sheet_3_poses.png
      character_sheet_4_cast.png
"""
import math, sys
sys.path.insert(0, '/home/user/src')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from stickbase import (W as VW, H as VH, CHALK, GOLD, CYAN, MINT, RED, PINK,
                       poly, circ, arc, box, squiggle, star, tick, write, text_img, put,
                       ft, MARKER, HAND, make_board, clamp,
                       pose_idle, pose_sad, pose_type, pose_cheer, pose_point,
                       pose_think, pose_walk, pose_shake, pose_dance)
import character as CH
from character import hero, face, EXPR, CHAR, ACCESSORIES, HERO_SEED

SW, SH = 1600, 2300          # sheet size
OUT = '/home/user/'

# ---------------------------------------------------------------- board plate
def plate(w, h):
    rng = np.random.default_rng(9)
    base = np.zeros((h // 3, w // 3, 3), np.float32)
    base[:] = np.array([17, 21, 30], np.float32)
    base += rng.normal(0, 7, (h // 3, w // 3, 1))
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6))
    img = img.resize((w, h), Image.BICUBIC)
    d = ImageDraw.Draw(img)
    for _ in range(900):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        r = int(rng.integers(1, 3)); v = int(rng.integers(26, 58))
        d.ellipse([x, y, x + r, y + r], fill=(v + 10, v + 12, v + 16))
    for _ in range(12):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        rr = int(rng.integers(90, 260))
        sm = Image.new('RGBA', (rr * 2, rr * 2), (0, 0, 0, 0))
        ImageDraw.Draw(sm).ellipse([0, 0, rr * 2, rr * 2], fill=(255, 255, 255, 7))
        reg = img.crop((x - rr, y - rr, x + rr, y + rr)).convert('RGBA')
        img.paste(Image.alpha_composite(reg, sm).convert('RGB'), (x - rr, y - rr))
    # faint grid
    g = Image.new('RGBA', (w, h), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for x in range(0, w, 100): gd.line([(x, 0), (x, h)], fill=(255, 255, 255, 8), width=2)
    for y in range(0, h, 100): gd.line([(0, y), (w, y)], fill=(255, 255, 255, 8), width=2)
    img = Image.alpha_composite(img.convert('RGBA'), g)
    return img


def new_sheet(title, sub, n):
    im = plate(SW, SH)
    cv = Image.new('RGBA', (SW, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    box(d, 40, 40, SW - 40, SH - 40, (90, 100, 125), 5, 1, 3, 0, 2.0)
    write(cv, CHAR['name'], 205, 122, 80, GOLD, MARKER, rot=-1.5, p=1)
    write(cv, f'SHEET {n}/4', 1430, 118, 36, CYAN, HAND, p=1)
    write(cv, title, SW // 2, 128, 50, CHALK, HAND, p=1)
    write(cv, sub, SW // 2, 185, 32, (150, 162, 190), HAND, p=1)
    squiggle(d, 90, 228, SW - 90, GOLD, 5, 1, 7, 0, 2, 26, 7)
    return im, cv, d


def finish(im, cv, name):
    glow = cv.filter(ImageFilter.GaussianBlur(11))
    im.alpha_composite(Image.blend(Image.new('RGBA', (SW, SH), (0, 0, 0, 0)), glow, .36))
    im.alpha_composite(cv)
    a = np.asarray(im.convert('RGB')).astype(np.float32)
    vy, vx = np.mgrid[0:SH, 0:SW].astype(np.float32)
    r = np.sqrt(((vx - SW / 2) / (SW / 2)) ** 2 + ((vy - SH / 2) / (SH / 2)) ** 2)
    a *= np.clip(1.05 - .38 * r ** 2, 0, 1.1)[..., None]
    a += np.random.default_rng(4).normal(0, 1, (SH, SW, 1)) * 3.2
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(OUT + name)
    print('wrote', name)


def label(cv, txt, x, y, col=CHALK, size=34):
    write(cv, txt, x, y, size, col, HAND, p=1)


def callout(d, cv, a, b, txt, tx, col=CYAN, size=27, seed=3):
    """Leader line from point a on the figure to elbow b, label centred at tx."""
    poly(d, [a, (b[0], a[1]), b], col, 3, 1, seed, 0, 1.2)
    d.ellipse([a[0] - 6, a[1] - 6, a[0] + 6, a[1] + 6], fill=col)
    write(cv, txt, tx, b[1], size, col, HAND, p=1)


# ════════════════════════════════════════════════ SHEET 1 — IDENTITY
def sheet1():
    im, cv, d = new_sheet('IDENTITY + CONSTRUCTION', 'one hero, every scene — lock this and never change it', 1)

    # ---- hero turnaround row (right 2/3), callout column (left 1/3)
    S = 600
    gy = 1030
    XS = [640, 980, 1320]
    for i, (ex, mk, cap, pose) in enumerate([
            ('neutral', 'cap', 'A-POSE', pose_idle(0.0)),
            ('determined', 'cap', '3/4 LEAN', dict(pose_idle(1.1), lean=9)),
            ('happy', 'cap', 'ACTION', pose_point(0.4, right=True, up=True))]):
        x = XS[i]
        poly(d, [(x - 140, gy), (x + 140, gy)], (108, 120, 145), 4, 1, 21 + i, 0)
        hero(d, x, gy, S, pose, ex, mk, tq=0, t=i * .4)
        label(cv, cap, x, gy + 52, (150, 162, 190), 29)

    # ---- construction callouts, all pointing at figure 1
    hx = XS[0]
    hipY = gy - .42 * S
    neckY = hipY - .36 * S
    hrad = .115 * S
    headY = neckY - hrad - .035 * S
    TX, EX = 250, 445        # label centre x, leader elbow x
    callout(d, cv, (hx - hrad * .92, headY), (EX, 360), 'HEAD   r = 0.115 s', TX, CYAN, 27, 61)
    callout(d, cv, (hx, neckY), (EX, 440), 'NECK   0.36 s over hip', TX, CYAN, 27, 62)
    callout(d, cv, (hx - 36, neckY + 112), (EX, 520), 'ARM    0.19 + 0.18 s', TX, CYAN, 27, 63)
    callout(d, cv, (hx, hipY), (EX, 600), 'HIP    0.42 s', TX, CYAN, 27, 64)
    callout(d, cv, (hx - 22, hipY + 104), (EX, 680), 'LEG    0.22 + 0.22 s', TX, CYAN, 27, 65)
    callout(d, cv, (hx - 44, gy - 6), (EX, 760), 'FOOT   0.055 s', TX, CYAN, 27, 66)

    # total-height bracket, clear of the ACTION figure
    bx = 1520
    poly(d, [(bx - 26, gy), (bx, gy), (bx, gy - S), (bx - 26, gy - S)], MINT, 3, 1, 71, 0, 1.0)
    write(cv, 's', bx - 13, gy - S - 32, 34, MINT, MARKER, p=1)

    write(cv, 'every proportion is a fraction of s (total height) — one rig, any size', SW // 2, 1136, 30, (152, 164, 192), HAND, p=1)
    write(cv, 'stroke width scales with it:  w = 10 x s / 600', SW // 2, 1176, 30, (152, 164, 192), HAND, p=1)

    # ---- identity marker options
    write(cv, 'IDENTITY MARKER  —  pick ONE, use it in every single scene', SW // 2, 1255, 42, GOLD, MARKER, rot=-.5, p=1)
    opts = [('cap', 'A · BACKWARDS CAP', 'young hustler / street', GOLD),
            ('hair', 'B · SPIKE TUFT', 'classic cartoon, cheapest', MINT),
            ('phones', 'C · HEADPHONES', 'creator / editor energy', CYAN),
            ('scarf', 'D · MUFFLER', 'strongest silhouette', PINK)]
    for i, (mk, nm, why, c) in enumerate(opts):
        x = 230 + i * 380
        box(d, x - 165, 1310, x + 165, 1700, (80, 92, 115), 3, 1, 90 + i, 0, 1.4)
        hero(d, x, 1660, 330, pose_idle(0.3), 'happy', mk, tq=0, acc_col=c, t=0.6)
        label(cv, nm, x, 1738, c, 30)
        label(cv, why, x, 1774, (140, 152, 180), 25)

    # ---- palette
    write(cv, 'LOCKED PALETTE', SW // 2, 1855, 40, GOLD, MARKER, rot=-.5, p=1)
    pal = [('CHALK', CHALK, 'body'), ('GOLD', GOLD, 'marker'), ('CYAN', CYAN, 'skill'),
           ('MINT', MINT, 'progress'), ('RED', RED, 'problem'), ('PINK', PINK, 'create')]
    for i, (nm, c, role) in enumerate(pal):
        x = 180 + i * 250
        box(d, x - 80, 1905, x + 80, 2015, c, 5, 1, 120 + i, 0, 1.6, fill=c + (46,))
        label(cv, nm, x, 1960, c, 30)
        label(cv, role, x, 2050, (140, 152, 180), 25)
        label(cv, '#%02X%02X%02X' % c, x, 2086, (110, 122, 150), 22)

    write(cv, 'HERO_SEED = 101  ·  never reuse this seed on any other figure', SW // 2, 2160, 30, RED, HAND, p=1)
    write(cv, 'every extra gets its own seed so nobody wobbles in lockstep', SW // 2, 2200, 28, (140, 152, 180), HAND, p=1)
    finish(im, cv, 'character_sheet_1_identity.png')


# ════════════════════════════════════════════════ SHEET 2 — EXPRESSIONS
def sheet2():
    im, cv, d = new_sheet('EXPRESSION LIBRARY', 'eyebrows + pupils + 8 mouths = 10 readable emotions', 2)
    order = [('neutral', 'NEUTRAL', 'default / idle'),
             ('worried', 'WORRIED', 'S1 — jeb khali'),
             ('sad', 'SAD', 'S1 — Rs 0'),
             ('shock', 'SHOCK', 'reveals, reactions'),
             ('think', 'THINK', 'choosing a skill'),
             ('focus', 'FOCUS', 'S2 — typing'),
             ('determined', 'DETERMINED', 'S3 — the grind'),
             ('proud', 'PROUD', 'S4 — samples'),
             ('happy', 'HAPPY', 'S5 — the deal'),
             ('celebrate', 'CELEBRATE', 'S6 — payoff')]
    hr = 110
    for i, (k, nm, use) in enumerate(order):
        c, r = i % 5, i // 5
        x = 200 + c * 300
        y = 420 + r * 440
        col = [RED, RED, RED, GOLD, CYAN, CYAN, MINT, PINK, GOLD, GOLD][i]
        box(d, x - 130, y - 162, x + 130, y + 142, (76, 88, 112), 3, 1, 140 + i, 0, 1.4)
        circ(d, (x, y - 14), hr, CHALK, 8, 1, HERO_SEED + i * 7, 0, 2.0, 28)
        face(d, (x, y - 14), hr, 900, k, CHALK, 7, 0, HERO_SEED + i * 7)
        label(cv, nm, x, y + 186, col, 31)
        label(cv, use, x, y + 226, (140, 152, 180), 25)

    # blink strip
    write(cv, 'BLINK CYCLE   ·   deterministic, period 3.1 s, lid shut for 0.14 s', SW // 2, 1240, 38, GOLD, MARKER, rot=-.5, p=1)
    for i in range(6):
        x = 230 + i * 230
        b = [0.0, .35, .70, 1.0, .70, .35][i]
        circ(d, (x, 1390), 76, CHALK, 7, 1, 300 + i, 0, 2.0, 24)
        face(d, (x, 1390), 76, 650, 'neutral', CHALK, 6, 0, 300 + i, blink=b)
        label(cv, f'blink {b:.2f}', x, 1496, (140, 152, 180), 25)

    # look direction
    write(cv, 'LOOK DIRECTION   ·   pupils follow the thing we want you to read', SW // 2, 1596, 38, GOLD, MARKER, rot=-.5, p=1)
    for i, (lk, nm) in enumerate([((-.55, 0), 'LEFT'), ((0, -.5), 'UP'), ((0, 0), 'CAMERA'),
                                  ((.55, 0), 'RIGHT'), ((.40, .40), 'DOWN-R'), ((0, .5), 'DOWN')]):
        x = 230 + i * 230
        circ(d, (x, 1746), 76, CHALK, 7, 1, 320 + i, 0, 2.0, 24)
        face(d, (x, 1746), 76, 650, 'neutral', CHALK, 6, 0, 320 + i, look=lk)
        label(cv, nm, x, 1852, CYAN, 27)

    write(cv, 'RULE  ·  expression changes on a BEAT, never mid-sentence.', SW // 2, 1960, 32, MINT, HAND, p=1)
    write(cv, 'RULE  ·  one expression per scene + one reaction. Never more.', SW // 2, 2010, 32, MINT, HAND, p=1)
    write(cv, 'RULE  ·  eyebrows do 70% of the work. If unsure, move the brows.', SW // 2, 2060, 32, MINT, HAND, p=1)
    write(cv, 'RULE  ·  he looks AT the thing the viewer should look at.', SW // 2, 2110, 32, MINT, HAND, p=1)
    write(cv, 'RULE  ·  blink is a pure function of t, so it never desyncs on a re-render.', SW // 2, 2160, 32, MINT, HAND, p=1)
    finish(im, cv, 'character_sheet_2_expressions.png')


# ════════════════════════════════════════════════ SHEET 3 — POSES
def sheet3():
    im, cv, d = new_sheet('POSE + ACTION LIBRARY', 'every pose is a pure function of time — no keyframes', 3)
    poses = [
        (lambda t: pose_idle(t),                         'IDLE',      'breathing, between beats', 'neutral',    CHALK),
        (lambda t: pose_walk(t),                         'WALK',      'S1 entry',                 'neutral',    CHALK),
        (lambda t: pose_sad(t),                          'SLUMP',     'S1 problem',               'sad',        RED),
        (lambda t: pose_think(t),                        'THINK',     'choosing a skill',         'think',      CYAN),
        (lambda t: pose_type(t),                         'TYPE',      'S2 / S3 working',          'focus',      CYAN),
        (lambda t: pose_point(t, right=True, up=False),  'POINT R',   'directing attention',      'determined', MINT),
        (lambda t: pose_point(t, right=False, up=True),  'POINT UP',  'S4 presenting',            'proud',      PINK),
        (lambda t: pose_shake(t),                        'HANDSHAKE', 'S5 the deal',              'happy',      GOLD),
        (lambda t: pose_cheer(t),                        'CHEER',     'win moment',               'celebrate',  GOLD),
        (lambda t: pose_dance(t),                        'DANCE',     'S6 payoff',                'celebrate',  GOLD),
    ]
    S = 270
    ROW_Y = [600, 1060]
    for i, (pf, nm, use, ex, col) in enumerate(poses):
        c, r = i % 5, i // 5
        x = 200 + c * 300
        y = ROW_Y[r]
        box(d, x - 132, y - 330, x + 132, y + 42, (76, 88, 112), 3, 1, 160 + i, 0, 1.4)
        poly(d, [(x - 108, y), (x + 108, y)], (104, 116, 142), 3, 1, 180 + i, 0)
        hero(d, x, y, S, pf(0.9 + i * .3), ex, 'cap', tq=0, acc_col=col, t=i * .4)
        label(cv, nm, x, y + 76, col, 30)
        label(cv, use, x, y + 114, (140, 152, 180), 24)

    write(cv, 'SCALE CHART  ·  s is the only number you change', SW // 2, 1250, 40, GOLD, MARKER, rot=-.5, p=1)
    gy = 1990
    poly(d, [(140, gy), (SW - 140, gy)], (104, 116, 142), 4, 1, 200, 0)
    for i, (sz, nm) in enumerate([(600, 'HERO   s=600'), (470, 'MID   s=470'),
                                  (400, 'PAIR   s=400'), (330, 'EXTRA   s=330')]):
        x = 280 + i * 360
        hero(d, x, gy, sz, pose_idle(i * .7), 'happy', 'cap', tq=0, t=i * .5)
        label(cv, nm, x, gy + 50, CYAN, 28)
    write(cv, 'stroke width auto-scales:  w = 10 x s / 600', SW // 2, 2098, 30, MINT, HAND, p=1)
    write(cv, 'the hero is ALWAYS the largest figure on screen', SW // 2, 2142, 30, MINT, HAND, p=1)
    write(cv, 'MOTION TRAIL  ·  2 ghosts at -0.055 s, 35% brightness, no face', SW // 2, 2192, 29, (150, 162, 190), HAND, p=1)
    finish(im, cv, 'character_sheet_3_poses.png')


# ════════════════════════════════════════════════ SHEET 4 — CAST
def sheet4():
    im, cv, d = new_sheet('SUPPORTING CAST + RULES',
                          'only the hero carries a marker, a hoodie and seed 101', 4)
    from stickbase import stick
    gy = 880

    poly(d, [(100, gy), (SW - 100, gy)], (104, 116, 142), 4, 1, 21, 0)

    # ---- the hero
    hero(d, 300, gy, 520, dict(pose_idle(0.4), lean=3), 'happy', 'cap', tq=0, t=0.3)

    # ---- the client (dimmer, thinner, no marker, no hoodie, open collar)
    jc = stick(d, 720, gy, 420, dict(pose_idle(1.4), lean=-3),
               (178, 188, 212), 8, 211, 0, 1, None)
    CH.face(d, jc['head'], jc['hr'], 420, 'happy', (178, 188, 212), 5, 0, 211)
    nx, ny = jc['neck']
    hrc = jc['hr']
    poly(d, [(nx - hrc * .62, ny - hrc * .06), (nx, ny + hrc * .46), (nx + hrc * .62, ny - hrc * .06)],
         CYAN, 5, 1, 213, 0, 1.2)

    # ---- the crowd (smallest, flattest, no face detail)
    for k in range(3):
        x = 1120 + k * 150
        jj = stick(d, x, gy, 320 - k * 16, pose_idle(k * 1.3), (146, 156, 180), 7, 231 + k, 0, 1, None)
        CH.face(d, jj['head'], jj['hr'], 320, ['neutral', 'happy', 'neutral'][k],
                (146, 156, 180), 4, 0, 231 + k)

    cast = [(300, CHAR['name'], GOLD, 'THE HERO  ·  seed 101  ·  cap  ·  hoodie',
             'in all 6 scenes, always the biggest'),
            (720, 'THE CLIENT', CYAN, 'seed 211  ·  collar, no cap  ·  dimmer stroke',
             'S5 only. Never upstages the hero.'),
            (1270, 'THE CROWD', (170, 180, 202), 'seeds 231+  ·  no marker  ·  no hoodie',
             'background only. Silhouette, not character.')]
    for x, nm, c, l1, l2 in cast:
        write(cv, nm, x, gy + 56, 42, c, MARKER, rot=-1, p=1)
        write(cv, l1, x, gy + 112, 26, CHALK, HAND, p=1)
        write(cv, l2, x, gy + 150, 25, (140, 152, 180), HAND, p=1)

    # ---- visual hierarchy bars
    write(cv, 'VISUAL HIERARCHY  ·  never break this order', SW // 2, 1160, 42, GOLD, MARKER, rot=-.5, p=1)
    rows = [('HERO', 520, GOLD, 'cap + hoodie + full face + motion trails'),
            ('CLIENT', 420, CYAN, 'open collar + face, no marker'),
            ('CROWD', 320, (124, 136, 162), 'body + simple face only')]
    for i, (nm, sz, ac, note) in enumerate(rows):
        y = 1265 + i * 118
        bw = int((sz / 520) * 840)
        box(d, 420, y - 36, 420 + bw, y + 36, ac, 4, 1, 250 + i, 0, 1.4, fill=ac + (38,))
        write(cv, nm, 300, y, 36, ac, MARKER, p=1)
        write(cv, note, 420 + bw / 2, y, 27, (222, 230, 245), HAND, p=1)
        write(cv, f's={sz}', 420 + bw + 76, y, 29, ac, HAND, p=1)

    # ---- the seven laws, LEFT aligned
    write(cv, 'THE SEVEN LAWS', SW // 2, 1700, 48, GOLD, MARKER, rot=-.8, p=1)
    laws = [
        'ONE hero. Same seed (101), same cap, same hoodie, every scene.',
        'The hero is always the LARGEST figure in frame.',
        'Only the hero gets an identity marker. Extras never do.',
        'Only the hero gets motion trails.',
        'Extras are 25% dimmer and 2 px thinner than the hero.',
        'The hero looks AT whatever the viewer should read next.',
        'Expression changes land on a beat, never mid-word.',
    ]
    fnt = ft(HAND, 31)
    for i, txt in enumerate(laws):
        y = 1800 + i * 66
        tick(d, 250, y, 22, MINT, 1, 0, 260 + i)
        write(cv, f'{i+1}.', 325, y - 4, 31, GOLD, HAND, p=1)
        bb = fnt.getbbox(txt)
        write(cv, txt, 370 + (bb[2] - bb[0]) / 2, y - 4, 31, CHALK, HAND, p=1)

    finish(im, cv, 'character_sheet_4_cast.png')



if __name__ == '__main__':
    sheet1(); sheet2(); sheet3(); sheet4()
    print('all sheets done')
