#!/usr/bin/env python3
"""charsheet_v2.py — HERO v2 character sheet: the 3-D human stick figure (stick3d.py) — turnaround, expressions,
hands, feet, walk/run cycles and three in-world test shots on the real-life plates.  python3 src/charsheet_v2.py out.jpg"""
import os, sys, math, json, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stick3d as S
import human as Hm
import world as Wd

WF = Wd.WF
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WF, 'CHARSHEET_HERO_v2.jpg')
SW = 1920
SS = 2
F_H = Wd.font(Wd.F_SANS, 54, 700)
F_S = Wd.font(Wd.F_SANS, 26, 600)
F_C = Wd.font(Wd.F_SANS, 20, 500)
F_D = Wd.font(Wd.F_SERIF, 24)
BONE = (236, 232, 222)
STUDIO = S.light_rig(key_dir=(-0.55, -0.6, 0.6), key_col=(1.0, 0.94, 0.86), key_int=1.05,
                     fill_dir=(0.7, -0.1, 0.7), fill_col=(0.55, 0.65, 0.9), fill_int=0.2,
                     rim_dir=(0.55, -0.35, -0.75), rim_col=(0.75, 0.85, 1.0), rim_int=0.6,
                     sky=(0.17, 0.19, 0.25), ground=(0.06, 0.05, 0.05))
METRICS = {}


def studio_bg(w, h, top=(34, 35, 41), bot=(12, 12, 15), floor=None):
    y = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, np.float32)[None, None, :] * (1 - y) + np.array(bot, np.float32)[None, None, :] * y
    a = np.repeat(a, w, axis=1)
    if floor is not None:
        # a faint floor plane below `floor` px
        fy = np.clip((np.arange(h)[:, None, None] - floor) / 60.0, 0, 1)
        a = a * (1 - 0.35 * fy) + np.array((18, 18, 22), np.float32)[None, None, :] * 0.35 * fy
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert('RGBA')


def panel(w, h, draw_fn, bg=None):
    """draw at 2× then downsample. draw_fn(can, SS) paints onto an RGBA canvas of size (w*SS, h*SS)."""
    can = (bg or studio_bg(w, h)).resize((w * SS, h * SS), Image.BICUBIC)
    draw_fn(can, SS)
    return can.resize((w, h), Image.LANCZOS)


def caption(sheet, x, y, txt, font=F_C, col=(170, 172, 180)):
    ImageDraw.Draw(sheet).text((x, y), txt, font=font, fill=col)


# ───────────────────────────────────────────── row A: turnaround
def row_turnaround():
    w, h = SW, 900
    views = [('FRONT', dict(Hm.p_stand(0.0, 0.3)), 'neutral', (0.0, 0.0)),
             ('¾ VIEW', dict(Hm.p_stand(0.0, 0.3), yaw=35, head_t=-10), 'calm', (0.15, 0.0)),
             ('SIDE', dict(Hm.p_stand(0.0, 0.0), yaw=90), 'neutral', (0.0, 0.0)),
             ('BACK', dict(Hm.p_stand(0.0, 0.3), yaw=180), 'neutral', (0.0, 0.0))]

    def draw(can, k):
        s = 800 * k
        for i, (nm, pose, ex, look) in enumerate(views):
            x, y = (300 + i * 440) * k, 860 * k
            _, J, _ = S.solve(x, y, s, pose)
            S.contact_shadows(can, J, s)
            S.render(can, x, y, s, pose, STUDIO, expr=ex, look=look, hands=('relax', 'relax'))
    im = panel(w, h, draw, studio_bg(w, h, floor=860))
    d = ImageDraw.Draw(im)
    for i, (nm, _, _, _) in enumerate(views):
        d.text((300 + i * 440 - d.textlength(nm, font=F_S) / 2, 872), nm, font=F_S, fill=(190, 192, 200))
    return im


# ───────────────────────────────────────────── row B: expressions
def row_expressions():
    names = ['neutral', 'tired', 'envy', 'doubt', 'shock', 'resolve', 'calm', 'smile', 'pain', 'focus']
    pw, ph = 384, 330
    rows = []
    for r in range(2):
        def draw(can, k, r=r):
            s = 1850 * k
            for c in range(5):
                i = r * 5 + c
                box = (c * pw * k + 4 * k, 6 * k, (c + 1) * pw * k - 4 * k, (ph - 4) * k)
                pose = dict(Hm.p_stand(0.0), head_t=12 * ((i % 3) - 1), head=3 * ((i % 2) - 0.5))
                S.render_window(can, box, s, pose, STUDIO, focus='hctr', focus_off=(0.0, -0.01), expr=names[i],
                                look=(0.18 * ((i % 3) - 1), 0.08))
        im = panel(SW, ph, draw)
        d = ImageDraw.Draw(im)
        for c in range(5):
            d.text((c * pw + 16, 12), names[r * 5 + c].upper(), font=F_C, fill=(190, 192, 200))
        rows.append(im)
    out = Image.new('RGBA', (SW, ph * 2))
    out.paste(rows[0], (0, 0)); out.paste(rows[1], (0, ph))
    return out


# ───────────────────────────────────────────── row C: hands + feet
def row_hands_feet():
    presets = ['relax', 'fist', 'flat', 'phone', 'grip', 'point', 'splay', 'glass']
    pw, ph = 192, 260

    def draw(can, k):
        s = 1500 * k
        for i, pr in enumerate(presets):
            box = (i * pw * k + 3 * k, 4 * k, (i + 1) * pw * k - 3 * k, (ph - 3) * k)
            pose = dict(Hm.p_stand(0.0), ar=60, az_r=-10, ef_r=60, hw_r=-110) if i % 2 == 0 else dict(Hm.p_stand(0.0), ar=28, ef_r=78, hw_r=45)
            if pr == 'phone':
                pose = dict(Hm.p_stand(0.0), ar=30, ef_r=80, hw_r=60)
            if pr == 'glass':
                pose = dict(Hm.p_stand(0.0), ar=20, ef_r=85, hw_r=175)
            props = [dict(kind='phone', hand='r')] if pr == 'phone' else []
            L = STUDIO
            if pr == 'phone':
                K3 = S.solve(0, 0, s, pose)[0]
                wr = K3['har']
                L = S.light_rig(key_dir=(-0.55, -0.6, 0.6), key_int=0.5, rim_int=0.5,
                                points=[S.point_light(wr + np.array([0.0, -0.06 * s, 0.07 * s]), (0.6, 0.78, 1.0), 1.4, 0.18 * s)])
            S.render_window(can, box, s, pose, L, focus='har', autocenter=True, hands=('relax', pr), props=props)
        # feet: side + ¾
        for j, (yaw, nm) in enumerate(((90, 'side'), (35, '¾'))):
            x0 = (8 * pw + j * pw) * k
            box = (x0 + 3 * k, 4 * k, x0 + pw * k - 3 * k, (ph - 3) * k)
            pose = dict(Hm.p_stand(0.0, 0.2), yaw=yaw)
            S.render_window(can, box, 1500 * k, pose, STUDIO, focus='ftr', autocenter=True)
    im = panel(SW, ph, draw)
    d = ImageDraw.Draw(im)
    for i, pr in enumerate(presets):
        d.text((i * pw + 12, ph - 30), pr.upper(), font=F_C, fill=(190, 192, 200))
    d.text((8 * pw + 12, ph - 30), 'FOOT · SIDE', font=F_C, fill=(190, 192, 200))
    d.text((9 * pw + 12, ph - 30), 'FOOT · ¾', font=F_C, fill=(190, 192, 200))
    return im


# ───────────────────────────────────────────── row D: walk / run / breathe
def row_motion():
    h = 430

    def draw(can, k):
        s = 340 * k
        y = 392 * k
        xs = 110
        for i in range(6):
            pose = dict(Hm.walk_pose(i / 6.0), yaw=90)
            x = (xs + i * 165) * k
            _, J, _ = S.solve(x, y, s, pose)
            S.contact_shadows(can, J, s, alpha=0.45)
            S.render(can, x, y, s, pose, STUDIO, expr='neutral', blink_v=Hm.blink(i * 0.45))
        for i in range(5):
            pose = dict(Hm.run_pose(i / 5.0), yaw=62)
            x = (xs + 6 * 165 + 60 + i * 175) * k
            _, J, _ = S.solve(x, y, s, pose)
            S.contact_shadows(can, J, s, alpha=0.45)
            S.render(can, x, y, s, pose, STUDIO, expr='focus', hands=('fist', 'fist'))
    im = panel(SW, h, draw, studio_bg(SW, h, floor=392))
    d = ImageDraw.Draw(im)
    d.text((40, 14), 'WALK CYCLE · 6 phases (side)', font=F_S, fill=(190, 192, 200))
    d.text((1130, 14), 'RUN CYCLE · 5 phases (¾)', font=F_S, fill=(190, 192, 200))
    return im


# ───────────────────────────────────────────── row E: in-world test shots (1920×1080 → 640×360)
def shot_window(t=0.0):
    rng = np.random.default_rng(3)
    f = Wd.camera(Wd.plate('window_inside'), zoom=1.12, cx=0.5, cy=0.47)
    x, y, s = 960, 1035, 720
    base = dict(Hm.p_window(t), yaw=180, lean=4)
    pose = S.reach(base, 'l', (1085, 520), x, y, s)
    pose = S.reach(pose, 'r', (835, 520), x, y, s)
    layer = Wd.text_layer()
    S.floor_shadow(layer, x, y, s, pose, direction=(0.0, 1.0), length=0.35, alpha=0.5, blur=10)
    L = S.scene_lights(x, y, s, (960, 330), key_col=(0.55, 0.7, 1.0), key_int=1.0, key_z=-0.9,
                       fill_col=(0.3, 0.36, 0.5), fill_int=0.22, rim_dir=(0.0, -0.3, -0.95), rim_col=(0.6, 0.78, 1.0),
                       rim_int=1.3, sky=(0.08, 0.10, 0.16), ground=(0.03, 0.03, 0.04))
    S.person(layer, x, y, s, pose, L, hands=('glass', 'glass'), expr='tired')
    f = Wd.composite(f, layer)
    f = Wd.rain(f, t, density=170, alpha=0.14)
    txt = Wd.text_layer()
    Wd.readout(txt, '12:04 AM', 64, 48)
    Wd.narration(txt, 'Thirty-one windows. All of them better than his.', Wd.W / 2, 980, 44, italic=True)
    f = Wd.composite(f, txt)
    f = Wd.grade(f, cold=0.5, sat=0.9)
    return Wd.finish(f, rng, vignette=0.55, grain=1.5)


def shot_bed_phone(t=0.0):
    rng = np.random.default_rng(4)
    f = Wd.camera(Wd.plate('bedroom_night'), zoom=1.45, cx=0.40, cy=0.62) * 0.55
    x, y, s = 930, 735, 700          # hip anchor on the bed edge
    pose = dict(Hm.p_sit(t, 0.75), yaw=-12, head=10, head_t=6, ll=-5, lr=5, kl=98, kr=94, lz_l=72, lz_r=70)
    pose = S.reach(pose, 'r', (935, 612), x, y, s, anchor='hip')
    pose = S.reach(pose, 'l', (1000, 735), x, y, s, anchor='hip')
    pose['hw_r'] = 85
    K3, J, fr = S.solve(x, y, s, pose, anchor='hip')
    wr = K3['har']
    phone_pos = wr + np.array([0.0, -0.03 * s, 0.07 * s])
    fl = Wd.flicker(t, 3)
    L = S.scene_lights(x, y, s, (300, 200), key_col=(0.35, 0.42, 0.6), key_int=0.35, key_z=0.2,
                       fill_col=(0.2, 0.25, 0.35), fill_int=0.1, rim_dir=(0.6, -0.4, -0.7), rim_col=(0.4, 0.5, 0.8), rim_int=0.35,
                       sky=(0.05, 0.06, 0.10), ground=(0.02, 0.02, 0.03),
                       points=[S.point_light(phone_pos, (0.55, 0.72, 1.0), 2.2 * (0.8 + 0.2 * fl), 0.22 * s)])
    layer = Wd.text_layer()
    S.person(layer, x, y, s, pose, L, hands=('relax', 'phone'), props=[dict(kind='phone', hand='r')], expr='tired',
             look=(0.1, 0.7), anchor='hip')
    f = Wd.glow(f, (J['har'][0], J['har'][1] - 20), 520, Wd.BLUE, power=0.55 * fl, falloff=2.2)
    f = Wd.composite(f, layer)
    txt = Wd.text_layer()
    Wd.readout(txt, '11:48 PM', 64, 48)
    Wd.narration(txt, 'Every night started the same.', Wd.W / 2, 980, 46)
    f = Wd.composite(f, txt)
    f = Wd.grade(f, cold=0.55, sat=0.9)
    return Wd.finish(f, rng, vignette=0.6, grain=1.6)


def shot_desk(t=0.0):
    rng = np.random.default_rng(8)
    f = Wd.camera(Wd.plate('bedroom_amber'), zoom=1.5, cx=0.74, cy=0.60)
    lamp = (1430, 370)
    fl = Wd.lamp_flicker(t)
    f = Wd.glow(f, lamp, 520, Wd.AMBER, power=0.10 * fl, falloff=2.0)
    x, y, s = 1175, 868, 725
    pose = dict(Hm.p_sit(t, 0.1), yaw=84, lean=14, head=-4, head_t=-24, lz_l=84, lz_r=80, kl=92, kr=88)
    pose = S.reach(pose, 'l', (1395, 655), x, y, s, anchor='hip')
    pose = S.reach(pose, 'r', (1415, 668), x, y, s, anchor='hip')
    L = S.scene_lights(x, y, s, lamp, key_col=(1.0, 0.78, 0.5), key_int=1.15 * fl, key_z=0.3,
                       fill_col=(0.25, 0.3, 0.45), fill_int=0.12, rim_dir=(-0.5, -0.4, -0.75), rim_col=(0.5, 0.6, 0.9), rim_int=0.3,
                       sky=(0.08, 0.08, 0.11), ground=(0.05, 0.035, 0.02))
    layer = Wd.text_layer()
    S.person(layer, x, y, s, pose, L, hands=('relax', 'grip'), expr='calm', look=(0.5, 0.35), anchor='hip')
    f = Wd.composite(f, layer)
    f = Wd.dust(f, t, lamp, 380, n=70, alpha=0.5)
    txt = Wd.text_layer()
    Wd.readout(txt, 'DAY 40 · 5:58 AM', 64, 48)
    Wd.narration(txt, 'Light it.', Wd.W / 2, 980, 60)
    f = Wd.composite(f, txt)
    f = Wd.grade(f, warm=0.35, sat=0.95)
    return Wd.finish(f, rng, vignette=0.5, grain=1.6)


def row_world():
    shots = [('IN-WORLD 1 · the window (back-lit, rain, floor shadow)', shot_window),
             ('IN-WORLD 2 · the hook (phone = real point light on the face)', shot_bed_phone),
             ('IN-WORLD 3 · DAY 40 desk (amber lamp key, dust)', shot_desk)]
    im = Image.new('RGBA', (SW, 400), (14, 14, 17, 255))
    for i, (nm, fn) in enumerate(shots):
        t0 = time.time()
        fr = fn(0.0)
        arr = np.asarray(fr, np.uint8) if not isinstance(fr, np.ndarray) else fr.clip(0, 255).astype(np.uint8)
        METRICS[nm] = dict(Wd.measure(arr), t=round(time.time() - t0, 2))
        Image.fromarray(arr).save(os.path.join(WF, 'build_look', 'v2_world_%d.jpg' % (i + 1)), quality=92)
        th = Image.fromarray(arr).resize((632, 356), Image.LANCZOS)
        im.paste(th, (8 + i * 640, 8))
        caption(im, 12 + i * 640, 370, nm)
    return im


def dna_card():
    im = Image.new('RGBA', (SW, 250), (10, 10, 13, 255))
    d = ImageDraw.Draw(im)
    lines = [
        'HERO v2 DNA — a stick figure, but everything human: true 3-D render (ray-cast capsules / ellipsoids / boxes, z-buffered, lit, ambient-occluded).',
        'Proportions ≈ 6.7 heads · stick limbs r 0.013 s · bone-white head + hands · charcoal hoodie (hood, strings, cuffs) · joggers · white sneakers (sole, heel, tongue).',
        'Face: eyeballs with lids (openness · squint · blink) · iris + limbal ring + pupil + gaze · lash line · brows (raise / inner tilt) · nose · ears · lips (smile · open cavity) · 10 expressions.',
        'Hands: palm + 5 fingers × 3 phalanges + thumb, correct chirality, 9 presets · props attach to the hand (phone = emissive screen + a real point light on the face).',
        'Motion: the same 3-D skeleton + IK + walk / run / breathe / blink / weight-shift as the rig — every shot of the film renders this figure; nothing is a drawing.',
        'Light: key · fill · rim · point lights per shot (window blue, phone, lamp amber) · Blinn-Phong · Fresnel · SSAO · skin warmth · contact + cast shadows · faint ink edge.',
    ]
    for i, ln in enumerate(lines):
        d.text((40, 22 + i * 36), ln, font=F_D, fill=(205, 200, 190) if i else BONE)
    return im


def main():
    t0 = time.time()
    os.makedirs(os.path.join(WF, 'build_look'), exist_ok=True)
    rows = []
    head = Image.new('RGBA', (SW, 120), (10, 10, 13, 255))
    d = ImageDraw.Draw(head)
    d.text((40, 24), 'NOIRGO MAX · HERO v2 — 3-D HUMAN STICK FIGURE', font=F_H, fill=BONE)
    d.text((40, 86), 'WF-03 · Monarch Noir Film · film #2 THE WINDOW · stick3d.py · rendered, not drawn · 2026-10-10', font=F_C, fill=(150, 152, 160))
    rows.append(head)
    for fn in (row_turnaround, row_expressions, row_hands_feet, row_motion, row_world, dna_card):
        t1 = time.time()
        rows.append(fn())
        print('%-18s %.1fs' % (fn.__name__, time.time() - t1), flush=True)
    H = sum(r.height for r in rows)
    sheet = Image.new('RGB', (SW, H), (12, 12, 15))
    y = 0
    for r in rows:
        sheet.paste(r.convert('RGB'), (0, y))
        y += r.height
    sheet.save(OUT, quality=92)
    json.dump(METRICS, open(OUT.replace('.jpg', '_metrics.json'), 'w'), indent=1)
    print('saved', OUT, sheet.size, '%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
