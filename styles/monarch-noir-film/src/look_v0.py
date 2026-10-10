#!/usr/bin/env python3
"""look_v0.py — WF-03 NOIRGO look sheet: 7 key beats of film #1 'THE SHADOW' + DNA card, rendered by noir.py."""
import os, sys, json, time
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import noir as N
import toon as T

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), 'build', 'wf03_look')
os.makedirs(OUT, exist_ok=True)
K_M = 1.8  # hero height in metres → readout = 1.8 · k
P_WALL = dict(T.p_idle(0.5)); P_WALL.update(ar=118, ef_r=12, az_r=10, head=-4, head_t=0, lean=1.5)  # palm on the wall

def R(z, lz):
    return round(K_M * (1 - lz) / max(z - lz, 0.08), 1)

SHOTS = [
 ('01 · Every night, it was the same', dict(
    hero=dict(u=-0.22, z=0.55, pose=T.p_idle(0.3), yaw=38, expr='sad'),
    lamp=(-0.78, 0.42, 520, 1.0), readout=R(0.55, 0.42),
    lines=[('Every night, it was there.', 960, 985)])),
 ('02 · The corner (villain text)', dict(
    hero=dict(u=0.02, z=0.62, pose=T.p_sad(0.4), yaw=-35, expr='sad'),
    lamp=(-0.55, 0.44, 560, 1.0), readout=R(0.62, 0.44),
    villain=[('stay.', 1330, 300, dict(size=48)), ('not yet.', 1420, 380, dict(size=40, alpha=200)),
             ('what if.', 1270, 470, dict(size=56))])),
 ('03 · Lights out (rock bottom)', dict(
    hero=dict(u=0.05, z=0.60, pose=T.p_sad(0.9), yaw=0, expr='sad'),
    lamp=(-0.45, 0.42, 520, 0.07), ambient=0.55, readout=None,
    lines=[('Some nights, he just turned it off.', 960, 985, dict(italic=True, size=42))])),
 ('04 · One step (back view)', dict(
    hero=dict(u=-0.18, z=0.50, pose=T.p_walk(0.15), yaw=168, expr='calm'),
    lamp=(-0.72, 0.30, 560, 1.0), readout=R(0.50, 0.30),
    lines=[('Not brave.  One step.', 960, 985)])),
 ('05 · The walk (shaft + dust)', dict(
    hero=dict(u=-0.02, z=0.78, pose=T.p_walk(0.62), yaw=160, expr='calm'),
    lamp=(-0.70, 0.30, 560, 0.95), readout=R(0.78, 0.30),
    shaft=((1560 * N.SS, -40 * N.SS), (1180 * N.SS, 760 * N.SS), 120, 0.55),
    lines=[('Every step, it shrank.', 960, 985)])),
 ('06 · The wall (payoff)', dict(
    hero=dict(u=0.0, z=0.96, pose=P_WALL, yaw=172, expr='calm'),
    lamp=(-0.80, 0.30, 600, 1.05), readout=R(0.96, 0.30),
    lines=[('When he touched the wall, the shadow was exactly his size.', 1000, 940, dict(size=40))])),
 ('07 · End card', dict(
    lamp=None, ambient=0.0, readout=None,
    lines=[('WALK TOWARD IT.', 960, 520, dict(size=72, tracking=1.4)),
           ('a monarch noir film', 960, 600, dict(size=26, italic=True, col=(150, 146, 138)))],
    finish=dict(vignette=0.2, halation=0.0))),
]

def dna_card():
    im = Image.new('RGB', (N.W, N.H), (7, 7, 9))
    d = ImageDraw.Draw(im)
    fs = N.font(N.F_SERIF, 54); fb = N.font(N.F_SANS, 24, 'Medium'); fl = N.font(N.F_SANS, 22, 'Light'); ft = N.font(N.F_TYPE, 30)
    d.text((110, 90), 'NOIRGO · film DNA', font=fs, fill=N.BONE)
    sw = [('BLACK 7·7·9', (7, 7, 9)), ('WALL 14·14·15', (14, 14, 15)), ('BONE 236·232·222', N.BONE),
          ('SLATE 96·102·112', N.SLATE), ('AMBER 255·214·170', (255, 214, 170)), ('RED 214·38·32', N.RED)]
    for i, (nm, c) in enumerate(sw):
        x = 110 + i * 285
        d.rectangle([x, 200, x + 240, 330], fill=c, outline=(60, 60, 66))
        d.text((x, 345), nm, font=fl, fill=N.BONE)
    rules = ['hero  = bone-white two-tone line figure on the 3-D skeleton · lit side / dark side · eyes only · scarf',
             'light = ONE motivated amber source per scene (lantern) · wall falloff · floor pool · halation · dust',
             'spine = his cast shadow (homothety about the lamp, k = depth ratio) · SHADOW readout in metres',
             'villain = red typewriter text (never a face) · narration = Computer-Modern serif, bone, bottom third',
             'grammar = holds 8-14 s · hard cuts + dip-to-black · no dissolves · camera always drifting (never still)',
             'audio = 2-3 voice lines only · motif score ~90 BPM · sub-heavy bed · -16.5 LUFS · quiet ending',
             'gates = luma 14-24 · dark ≥85 % · sat ≤0.10 · ≥3 callbacks · 2 quotable lines · title pun · md5']
    for i, r in enumerate(rules):
        d.text((110, 430 + i * 62), r, font=fl, fill=(200, 196, 188))
    d.text((110, 900), 'stay.  not yet.  what if.', font=ft, fill=N.RED)
    d.text((110, 960), 'Fear is a shadow. Walk toward it — and it is exactly your size.', font=N.font(N.F_SERIF_I, 34), fill=N.BONE)
    return np.asarray(im)

if __name__ == '__main__':
    t0 = time.time()
    frames, rows = [], []
    for i, (label, spec) in enumerate(SHOTS):
        fr, mt, info = N.shot(spec, seed=11 + i)
        Image.fromarray(fr).save(os.path.join(OUT, f'f{i + 1:02d}.jpg'), quality=92)
        rows.append(dict(shot=label, **mt, k=None if info['k'] is None else round(info['k'], 2), hero_px=round(info['s'])))
        frames.append((label, fr))
        print(f'{label:38s} luma {mt["luma"]:5.1f} dark {mt["dark_lt30"]:.2f} p99 {mt["p99"]:5.1f} sat {mt["sat"]:.3f} k {info["k"]}  {time.time() - t0:.0f}s', flush=True)
    frames.append(('08 · DNA card', dna_card()))
    # contact sheet 2 × 4, cells 960×540 + 44 px label
    cw, ch, lb = 960, 540, 44
    sheet = Image.new('RGB', (cw * 2, (ch + lb) * 4), (18, 18, 20))
    d = ImageDraw.Draw(sheet)
    f = N.font(N.F_SANS, 22, 'Medium')
    for i, (label, fr) in enumerate(frames):
        r, c = divmod(i, 2)
        sheet.paste(Image.fromarray(fr).resize((cw, ch), Image.LANCZOS), (c * cw, r * (ch + lb) + lb))
        d.text((c * cw + 16, r * (ch + lb) + 10), label, font=f, fill=(225, 222, 214))
    sp = os.path.join(os.path.dirname(HERE), 'NOIRGO_LOOK_SHEET_v0.jpg')
    sheet.save(sp, quality=88)
    json.dump(rows, open(os.path.join(os.path.dirname(HERE), 'NOIRGO_LOOK_SHEET_v0_metrics.json'), 'w'), indent=1)
    print('sheet →', sp, sheet.size, f'{time.time() - t0:.0f}s')
