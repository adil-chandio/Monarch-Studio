#!/usr/bin/env python3
"""charsheet.py — render the NOIRGO MAX hero character sheet (expressions · poses · hands) for approval."""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import human as Hm

SS = 2
W, H = 1920, 1600
BG = (9, 9, 11)
F_SANS = os.path.join(Hm.ROOT, 'fonts', 'Montserrat-VF.ttf')


def label(img, txt, x, y, size=26, col=(200, 196, 188)):
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(F_SANS, size)
    try:
        f.set_variation_by_name('Medium')
    except Exception:
        pass
    d.text((x, y), txt, font=f, fill=col)


def main(out):
    canvas = Image.new('RGBA', (W * SS, H * SS), BG + (255,))
    light = (300 * SS, 120 * SS)
    # ── row 1: expressions (heads only — big)
    exprs = ['neutral', 'tired', 'envy', 'doubt', 'shock', 'resolve', 'calm', 'smile', 'pain', 'focus']
    for i, e in enumerate(exprs):
        cx = (110 + i * 190) * SS
        cy = 170 * SS
        rx, ry = 62 * SS, 76 * SS
        layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        Hm._two_tone(layer, Hm._ellipse((cx, cy), rx, ry * 1.02), light, rx, Hm.SKIN_DK, Hm.SKIN)
        Hm.draw_face(layer, (cx, cy), rx, ry, 0.0, 0.0, light, Hm.EXPR[e], look=(0.0, 0.0), blink_v=0.0)
        canvas.alpha_composite(layer)
    # ── row 2: head turns + gaze + blink
    turns = [(-60, 'yaw −60'), (-30, 'yaw −30'), (0, 'front · look left'), (30, 'yaw 30'), (60, 'yaw 60'), (100, 'yaw 100'), (180, 'back'), (0, 'blink 50%'), (0, 'blink 100%'), (140, 'yaw 140')]
    for i, (yw, name) in enumerate(turns):
        cx = (110 + i * 190) * SS
        cy = 390 * SS
        rx, ry = 62 * SS, 76 * SS
        layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        if True:
            look = (-0.8, 0.1) if 'look' in name else (0.0, 0.0)
            bv = 0.5 if '50' in name else (1.0 if '100' in name else 0.0)
            Hm._two_tone(layer, Hm._ellipse((cx, cy), rx, ry * 1.02), light, rx, Hm.SKIN_DK, Hm.SKIN)
            Hm.draw_face(layer, (cx, cy), rx, ry, 0.0, yw, light, Hm.EXPR['neutral'], look=look, blink_v=bv)
        canvas.alpha_composite(layer)
    # ── row 3: full-body poses
    s = 520 * SS
    base_y = 1120 * SS
    poses = [
        ('stand · weight L', Hm.p_stand(0.0, weight=0.6), dict(expr='neutral')),
        ('walk 0.15', dict(Hm.walk_pose(0.15), yaw=25), dict(expr='focus')),
        ('walk 0.65', dict(Hm.walk_pose(0.65), yaw=25), dict(expr='focus')),
        ('run 0.3', dict(Hm.run_pose(0.3), yaw=30), dict(expr='pain', hand_l='fist', hand_r='fist')),
        ('sit · slump · phone', Hm.p_sit(0.0, slump=0.6), dict(expr='envy', hand_l='grip', hand_r='relax', look=(0.0, 0.6))),
        ('window · back', Hm.p_window(0.0), dict(expr='neutral', hand_l='flat', hand_r='flat')),
        ('resolve · fist', dict(Hm.p_stand(0.0), ef_l=80, az_l=20, al=-10), dict(expr='resolve', hand_l='fist', hand_r='relax')),
        ('point · doubt', dict(Hm.p_stand(0.0), ef_r=30, az_r=75, ar=20), dict(expr='doubt', hand_r='point')),
        ('hood up · silhouette', Hm.p_stand(0.0, -0.5), dict(silhouette=True)),
    ]
    for i, (name, pose, kw) in enumerate(poses):
        cx = (120 + i * 205) * SS
        layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        if kw.get('silhouette'):
            ImageDraw.Draw(canvas).rectangle([cx - 95 * SS, base_y - 560 * SS, cx + 95 * SS, base_y + 10 * SS], fill=(214, 170, 110, 255))
            Hm.draw_human(layer, cx - 40 * SS, base_y, s * 0.92, pose, light, **kw)
            Hm.draw_human(layer, cx + 50 * SS, base_y, s, dict(Hm.p_stand(0.0, 0.4), yaw=20), light, expr='resolve', hood_up=True)
        else:
            Hm.draw_human(layer, cx, base_y, s, pose, light, **kw)
        canvas.alpha_composite(layer)
    # ── row 4: hands + lying phone pose
    hands = ['relax', 'open', 'flat', 'fist', 'point', 'grip', 'hold']
    for i, hp in enumerate(hands):
        cx = (90 + i * 150) * SS
        cy = 1420 * SS
        layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        Hm.draw_hand(layer, (cx, cy + 60 * SS), (0.0, -1.0), 900 * SS, hp, light, 1.0)
        canvas.alpha_composite(layer)
    # lying with the phone (rot −90: head to the left)
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    pose = Hm.p_phone_bed(0.0)
    Hm.draw_human(layer, 1450 * SS, 1380 * SS, 520 * SS, pose, (1500 * SS, 1300 * SS), expr='tired', hand_l='grip', hand_r='grip',
                  rot=-90, anchor='hip', look=(0.0, -0.5))
    canvas.alpha_composite(layer)
    out_img = canvas.convert('RGB').resize((W, H), Image.LANCZOS)
    # labels
    for i, e in enumerate(exprs):
        label(out_img, e, 110 + i * 190 - 40, 262)
    for i, (yw, name) in enumerate(turns):
        label(out_img, name, 110 + i * 190 - 60, 482, 22)
    for i, (name, _, _) in enumerate(poses):
        label(out_img, name, 120 + i * 205 - 80, 1135, 22)
    for i, hp in enumerate(hands):
        label(out_img, hp, 90 + i * 150 - 30, 1500, 22)
    label(out_img, 'lying · phone', 1330, 1500, 22)
    label(out_img, 'NOIRGO MAX — hero rig v1 (human.py): expressions · turns · poses · five-finger hands', 40, 20, 30, (236, 232, 222))
    out_img.save(out, quality=92)
    print('wrote', out)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(Hm.HERE, '..', 'CHARSHEET_HERO_v1.jpg'))
