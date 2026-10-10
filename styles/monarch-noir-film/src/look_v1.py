#!/usr/bin/env python3
"""look_v1.py — THE WINDOW look sheet v1: 8 composed frames (real-life plates + human rig + light + text) + metrics."""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world as Wd
import human as Hm

W, H = Wd.W, Wd.H
OUT = os.path.join(Wd.WF, 'NOIRGO_LOOK_SHEET_v1_WINDOW.jpg')
SKIN_BLUE = ((26, 30, 42), (150, 184, 228))
SKIN_COLD = ((40, 42, 50), (172, 176, 184))
HOOD_BLUE = ((22, 26, 36), (96, 118, 160))
HOOD_COLD = ((30, 32, 40), (116, 120, 130))
PANTS_COLD = ((18, 18, 24), (62, 64, 74))


def hands_phone(layer, cx, cy, L, light, lit=SKIN_BLUE):
    """two hands gripping a phone seen from above the face (hook close-up)."""
    SS = 2
    cw, ch = int(L * 4.2) * SS, int(L * 3.0) * SS
    ox, oy = int(cx - L * 2.1), int(cy - L * 1.4)
    can = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    lx = ((light[0] - ox) * SS, (light[1] - oy) * SS)
    s = L / Hm.HAND_L
    # phone body (dark) with a bright screen — behind the hands
    d = ImageDraw.Draw(can)
    pw, ph = L * 1.05 * SS, L * 2.1 * SS
    pcx, pcy = (cx - ox) * SS, (cy - oy) * SS
    d.rounded_rectangle([pcx - pw / 2, pcy - ph / 2, pcx + pw / 2, pcy + ph / 2], radius=L * 0.16 * SS, fill=(8, 8, 10, 255), outline=(40, 44, 52, 255), width=3)
    d.rounded_rectangle([pcx - pw / 2 + 10, pcy - ph / 2 + 12, pcx + pw / 2 - 10, pcy + ph / 2 - 12], radius=L * 0.1 * SS, fill=(150, 180, 220, 255))
    # content blocks on the screen (a feed) — cool greys
    for i in range(5):
        yy = pcy - ph / 2 + 40 + i * ph * 0.17
        d.rounded_rectangle([pcx - pw / 2 + 24, yy, pcx + pw / 2 - 24, yy + ph * 0.11], radius=8, fill=(190, 212, 240, 255))
        d.rounded_rectangle([pcx - pw / 2 + 24, yy + ph * 0.12, pcx + pw / 2 - 60, yy + ph * 0.14], radius=4, fill=(120, 150, 200, 255))
    # hands: left from bottom-left, right from bottom-right
    Hm.draw_hand(can, ((cx - L * 0.75 - ox) * SS, (cy + L * 1.25 - oy) * SS), (0.42, -0.91), s * SS, 'grip', lx, 1.0, lit, flip=False, roll=0.0)
    Hm.draw_hand(can, ((cx + L * 0.75 - ox) * SS, (cy + L * 1.25 - oy) * SS), (-0.42, -0.91), s * SS, 'grip', lx, 1.0, lit, flip=True, roll=0.0)
    small = can.resize((cw // SS, ch // SS), Image.LANCZOS)
    layer.alpha_composite(small, dest=(max(0, ox), max(0, oy)), source=(max(0, -ox), max(0, -oy)))


def shot_hook(t=0.0):
    rng = np.random.default_rng(1)
    bg = Wd.camera(Wd.plate('bedroom_night'), zoom=1.9, cx=0.22, cy=0.62)
    bg = np.asarray(Image.fromarray(bg.astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) * 0.5
    fl = Wd.flicker(t, 3)
    phone = (1000, 880)
    frame = Wd.glow(bg, phone, 900, Wd.BLUE, power=0.8 * fl, falloff=2.2)
    layer = Wd.text_layer()
    # pillow (soft, cool) and the body lying toward the right under the blanket line
    pil = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    Hm._two_tone(pil, Hm._ellipse((820, 620), 420, 210, -0.18, 60), phone, 200, (20, 22, 30), (60, 70, 92), blur=0.5)
    pil = pil.filter(ImageFilter.GaussianBlur(2))
    layer.alpha_composite(pil)
    body = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    Hm._two_tone(body, Hm._ellipse((1380, 860), 640, 230, -0.10, 60), phone, 260, HOOD_BLUE[0], HOOD_BLUE[1])
    layer.alpha_composite(body)
    Wd.face_only(layer, (880, 500), 215, 262, math.radians(-30), 14, phone, 'tired', look=(0.25, 0.62),
                 blink_v=Hm.blink(t, 4), skin=SKIN_BLUE)
    hands_phone(layer, phone[0], phone[1] + 40, 175, (1000, 880))
    frame = Wd.composite(frame, layer)
    frame = Wd.glow(frame, phone, 380, Wd.BLUE, power=0.30 * fl, falloff=1.5)
    txt = Wd.text_layer()
    Wd.readout(txt, '11:48 PM', 64, 48)
    frame = Wd.composite(frame, txt)
    frame = Wd.grade(frame, cold=0.6, sat=0.9)
    return Wd.finish(frame, rng, vignette=0.6, grain=1.6)


def shot_facade(t=0.0):
    rng = np.random.default_rng(2)
    f = Wd.camera(Wd.plate('facade_night'), zoom=1.06, cx=0.5, cy=0.48, dx=math.sin(t * 0.3) * 6)
    # breathe the windows: TV windows flicker, amber ones steady
    for w in Wd.windows():
        if w['kind'] == 'blue':
            f = Wd.window_gain(f, w['rect'], Wd.flicker(t, 7 + hash(w['id']) % 5, rate=6, depth=0.3))
    f = Wd.rain(f, t, density=170, alpha=0.14)
    txt = Wd.text_layer()
    Wd.readout(txt, '11:48 PM', 64, 48)
    Wd.readout(txt, f"{len(Wd.windows())} WINDOWS LIT", 64, H - 92, size=28, alpha=190)
    f = Wd.composite(f, txt)
    f = Wd.grade(f, cold=0.35, sat=0.92)
    return Wd.finish(f, rng, vignette=0.5, grain=1.6)


def shot_couple(t=0.0):
    rng = np.random.default_rng(3)
    f = Wd.camera(Wd.plate('kitchen_window'), zoom=1.12, cx=0.5, cy=0.52)
    layer = Wd.text_layer()
    clip = (300, 190, 1620, 890)
    lamp = (640, 300)
    # him at the stove (facing right, stirring), her at the table (facing him)
    p1 = dict(Hm.p_stand(t, 0.3), yaw=55, az_l=35, az_r=48, ef_l=80, ef_r=70, lean=6)
    Wd.person(layer, 560, 900, 520, p1, lamp, clip=clip, silhouette=True)
    p2 = dict(Hm.p_stand(t + 1.0, -0.4), yaw=-45, az_l=10, az_r=12, ef_l=70, ef_r=10, lean=2)
    Wd.person(layer, 1220, 905, 500, p2, lamp, clip=clip, silhouette=True)
    f = Wd.composite(f, layer)
    f = Wd.rain(f, t, density=120, alpha=0.10)
    txt = Wd.text_layer()
    Wd.readout(txt, '11:52 PM', 64, 48)
    Wd.villain(txt, Wd.typewriter("they're happy.", t, -2.0), 110, 930, 44)
    f = Wd.composite(f, txt)
    f = Wd.grade(f, warm=0.25, sat=0.95)
    return Wd.finish(f, rng, vignette=0.5, grain=1.6)


def shot_deskman(t=0.0):
    rng = np.random.default_rng(4)
    f = Wd.camera(Wd.plate('desk_window'), zoom=1.08, cx=0.42, cy=0.5)
    layer = Wd.text_layer()
    clip = (170, 200, 790, 880)
    mon = (400, 720)
    # the man with two monitors, standing at the glass, looking out — at us
    p = dict(Hm.p_stand(t, 0.2), yaw=0, az_l=6, az_r=8, ef_l=12, ef_r=12, lean=3)
    Wd.person(layer, 640, 870, 560, p, mon, clip=clip, silhouette=True)
    f = Wd.composite(f, layer)
    f = Wd.rain(f, t, density=120, alpha=0.10)
    txt = Wd.text_layer()
    Wd.readout(txt, '2:04 AM', 64, 48)
    Wd.villain(txt, "it's two a.m.", 1180, 930, 44, col=Wd.BONE)
    f = Wd.composite(f, txt)
    f = Wd.grade(f, cold=0.5, sat=0.9)
    return Wd.finish(f, rng, vignette=0.5, grain=1.6)


def shot_ownwindow(t=0.0, state='blue'):
    rng = np.random.default_rng(5)
    base = Wd.facade_hero_dark() if state != 'blue' else Wd.plate('facade_hero')
    f = Wd.camera(base, zoom=1.0)
    x0, y0, x1, y1 = Wd.HERO_WIN
    c = ((x0 + x1) / 2, (y0 + y1) / 2)
    if state == 'blue':
        fl = Wd.flicker(t, 11, rate=7, depth=0.4)
        f = Wd.window_gain(f, Wd.HERO_WIN, 0.7 + 0.5 * fl)
        f = Wd.glow(f, c, 260, Wd.BLUE, power=0.22 * fl, falloff=2.5)
    elif state == 'amber':
        fl = Wd.lamp_flicker(t)
        f = Wd.window_gain(f, Wd.HERO_WIN, 1.0, color=Wd.AMBER * 0.0)
        m = Wd._soft_rect_mask((x0 + 6, y0 + 6, x1 - 6, y1 - 6), 3)[..., None]
        f = f * (1 - m) + (f * 0.3 + np.array([232, 178, 110], np.float32) * 0.85 * fl) * m
        f = Wd.glow(f, c, 300, Wd.AMBER, power=0.26 * fl, falloff=2.4)
    f = Wd.rain(f, t, density=180, alpha=0.15)
    txt = Wd.text_layer()
    Wd.readout(txt, '12:04 AM' if state == 'blue' else 'DAY 40 · 5:58 AM', 64, 48)
    if state == 'amber':
        Wd.narration(txt, "and there's a new window on the street.", W / 2, 980, 46, italic=True)
    f = Wd.composite(f, txt)
    f = Wd.grade(f, cold=0.45 if state == 'blue' else 0.1, sat=0.9)
    return Wd.finish(f, rng, vignette=0.55, grain=1.6)


def shot_reflection(t=0.0):
    rng = np.random.default_rng(6)
    f = Wd.camera(Wd.plate('window_inside'), zoom=1.15, cx=0.5, cy=0.46) * 0.9
    layer = Wd.text_layer()
    # the reflection: his face over the facade, cold, half-transparent
    Wd.face_only(layer, (980, 520), 215, 265, math.radians(2), 0, (700, 300), 'doubt', look=(0.0, 0.05),
                 blink_v=Hm.blink(t, 6), skin=SKIN_COLD, alpha=105)
    layer = layer.filter(ImageFilter.GaussianBlur(1.4))
    f = Wd.composite(f, layer)
    txt = Wd.text_layer()
    Wd.readout(txt, '12:30 AM', 64, 48)
    Wd.villain(txt, Wd.typewriter('look at you.', t, -1.0), 110, 930, 44, col=Wd.BONE)
    f = Wd.composite(f, txt)
    f = Wd.grade(f, cold=0.5, sat=0.85)
    return Wd.finish(f, rng, vignette=0.55, grain=1.6)


def shot_bed(t=0.0):
    rng = np.random.default_rng(7)
    f = Wd.camera(Wd.plate('bedroom_night'), zoom=1.45, cx=0.36, cy=0.62)
    layer = Wd.text_layer()
    win = (980, 200)      # window light from the back wall
    # hero bending over the bed, pulling the blanket flat (IK both hands onto the blanket edge)
    base = dict(Hm.p_stand(t, 0.0), yaw=-62, lean=38, head=10, kl=14, kr=10, lz_l=-6, lz_r=8)
    pose = Hm.reach(base, 'l', (760, 625), 1010, 980, 600)   # IK in frame space (similarity-invariant)
    pose = Hm.reach(pose, 'r', (880, 640), 1010, 980, 600)
    Wd.person(layer, 1010, 980, 600, pose, win, hand_l='hold', hand_r='hold', expr='focus',
              palette=dict(skin=SKIN_COLD, hood=HOOD_COLD, pants=PANTS_COLD))
    f = Wd.composite(f, layer)
    txt = Wd.text_layer()
    Wd.readout(txt, '12:41 AM', 64, 48)
    Wd.narration(txt, 'He makes the bed. At midnight.', W / 2, 980, 46)
    f = Wd.composite(f, txt)
    f = Wd.grade(f, cold=0.4, sat=0.9)
    return Wd.finish(f, rng, vignette=0.5, grain=1.6)


def shot_desk_amber(t=0.0):
    rng = np.random.default_rng(8)
    f = Wd.camera(Wd.plate('bedroom_amber'), zoom=1.5, cx=0.74, cy=0.60)
    lamp = (1430, 370)
    fl = Wd.lamp_flicker(t)
    f = Wd.glow(f, lamp, 520, Wd.AMBER, power=0.10 * fl, falloff=2.0)
    layer = Wd.text_layer()
    # hero seated at the desk in profile, typing — face lit amber
    pose = dict(Hm.p_sit(t, 0.1), yaw=78, lean=22, head=-6, head_t=-20)
    pose = Hm.reach(pose, 'l', (1285, 760), 1130, 830, 640, anchor='hip')
    pose = Hm.reach(pose, 'r', (1310, 775), 1130, 830, 640, anchor='hip')
    Wd.person(layer, 1130, 830, 640, pose, lamp, expr='calm', hand_l='relax', hand_r='relax', anchor='hip', look=(0.5, -0.2),
              palette=dict(skin=(Hm.SKIN_DK, (238, 206, 160)), hood=(Hm.HOODIE, (178, 160, 136)), pants=(Hm.PANTS, (96, 86, 76))))
    f = Wd.composite(f, layer)
    f = Wd.dust(f, t, lamp, 380, n=70, alpha=0.5)
    txt = Wd.text_layer()
    Wd.readout(txt, 'DAY 40 · 5:58 AM', 64, 48)
    Wd.narration(txt, 'Light it.', W / 2, 980, 60)
    f = Wd.composite(f, txt)
    f = Wd.grade(f, warm=0.35, sat=0.95)
    return Wd.finish(f, rng, vignette=0.5, grain=1.6)


SHOTS = [('01 HOOK · 11:48 PM · face glowing blue', shot_hook),
         ('02 THE WINDOWS · 31 lit · rain', shot_facade),
         ('03 third floor · the couple', shot_couple),
         ('04 two monitors · looking back', shot_deskman),
         ('05 his window · blue flicker', lambda t: shot_ownwindow(t, 'blue')),
         ('06 THE TURN · reflection', shot_reflection),
         ('07 THE WORK · the bed', shot_bed),
         ('08 DAY 40 · his window amber', lambda t: shot_ownwindow(t, 'amber')),
         ('09 5:58 AM · "Light it."', shot_desk_amber)]


def main():
    frames, metrics = [], {}
    for name, fn in SHOTS:
        img = fn(2.0)
        frames.append((name, img))
        metrics[name] = Wd.measure(img)
        print(name, metrics[name])
        Image.fromarray(img).save(os.path.join(Wd.WF, 'build_look', name[:2] + '.jpg'), quality=90)
    # sheet: 2 columns × 5 rows at 940×529 + header
    cw, ch = 940, 529
    cols = 2
    rows = (len(frames) + 1) // cols
    sheet = Image.new('RGB', (cols * cw + 40, 140 + rows * (ch + 56)), (9, 9, 11))
    d = ImageDraw.Draw(sheet)
    ft = Wd.font(Wd.F_SANS, 40, 'SemiBold')
    fs = Wd.font(Wd.F_SANS, 21, 'Medium')
    d.text((24, 26), 'NOIRGO MAX — THE WINDOW · look sheet v1 (real-life plates · human rig · light · text)', font=ft, fill=(236, 232, 222))
    d.text((24, 84), 'topic COMPARISON · ~170 s · full English VO (voice-03) · colour arc: phone blue → own lamp amber → dawn', font=fs, fill=(170, 168, 160))
    for i, (name, img) in enumerate(frames):
        x = 20 + (i % cols) * cw
        y = 140 + (i // cols) * (ch + 56)
        sheet.paste(Image.fromarray(img).resize((cw - 10, ch), Image.LANCZOS), (x, y))
        m = metrics[name]
        d.text((x + 4, y + ch + 8), f"{name}  ·  luma {m['luma']} dark {int(m['dark']*100)}% chroma {m['chroma']}", font=fs, fill=(200, 196, 188))
    sheet.save(OUT, quality=90)
    json.dump(metrics, open(OUT.replace('.jpg', '_metrics.json'), 'w'), indent=1)
    print('wrote', OUT, sheet.size)


if __name__ == '__main__':
    os.makedirs(os.path.join(Wd.WF, 'build_look'), exist_ok=True)
    main()
