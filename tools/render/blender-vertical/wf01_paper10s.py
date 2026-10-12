"""WF-01 Paper Cinema · 10 s vertical test (topic: Har subah ki pehli 10 minute).

Layers (back to front): timetable card (texture) · seated cut-out figure with red bench · ticket page that flips away.
Paper cards are thin cubes with a Bevel modifier (edge highlight) and image textures from make_textures().

Run (Blender, CPU):
  LD_LIBRARY_PATH=/tmp/stublib /tmp/venvs/blender/bin/python wf01_paper10s.py --lookdev 5.0 --out /tmp/wf01/lk50.png
  LD_LIBRARY_PATH=/tmp/stublib /tmp/venvs/blender/bin/python wf01_paper10s.py --out /tmp/wf01/frames --res 360x640 --samples 32
Textures: /tmp/venvs/render/bin/python wf01_paper10s.py --make-textures /tmp/wf01/tex
"""
import argparse
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FONTS = os.path.join(HERE, '..', '..', '..', 'styles', 'monarch-stickman-animation', 'fonts')
FPS = 30
DUR = 10.0


def make_textures(outdir):
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    os.makedirs(outdir, exist_ok=True)
    mont = os.path.join(FONTS, 'Montserrat-VF.ttf')
    marker = os.path.join(FONTS, 'PermanentMarker.ttf')

    def f(path, size):
        return ImageFont.truetype(path, size)

    def paper(w, h, base):
        rng = np.random.default_rng(7)
        arr = np.ones((h, w, 3), np.float32) * np.array(base, np.float32)
        grain = rng.normal(0, 0.012, (h, w, 1)).astype(np.float32)
        arr = np.clip(arr + grain, 0, 1)
        yy, xx = np.mgrid[0:h, 0:w]
        edge = np.minimum(np.minimum(xx, w - xx), np.minimum(yy, h - yy)) / min(w, h)
        shade = np.clip(0.9 + 0.12 * np.clip(edge * 14, 0, 1), 0, 1)[..., None]
        return Image.fromarray((np.clip(arr * shade, 0, 1) * 255).astype(np.uint8))

    # Timetable card: 960 x 1360 (aspect 0.706)
    W, H = 960, 1360
    im = paper(W, H, (0.96, 0.93, 0.86))
    d = ImageDraw.Draw(im)
    ink = (34, 30, 28)
    red = (178, 34, 34)
    d.text((80, 90), 'PAPER EXPRESS', font=f(mont, 74), fill=ink)
    d.text((80, 190), 'TIMETABLE · DAILY', font=f(mont, 36), fill=(90, 84, 78))
    d.line((80, 260, W - 80, 260), fill=ink, width=5)
    rows = [('05:40', 'Platform 1', 'ON TIME'), ('06:10', 'Car B · Seat 20', 'RESERVED'),
            ('06:25', 'Platform 2', 'ON TIME'), ('07:00', 'Car A · Seat 4', 'OPEN'),
            ('07:30', 'Platform 3', 'ON TIME')]
    y = 330
    for t, where, st in rows:
        hot = st == 'RESERVED'
        if hot:
            d.rectangle((70, y - 16, W - 70, y + 118), fill=(246, 226, 214))
            d.rectangle((70, y - 16, 84, y + 118), fill=red)
        d.text((100, y), t, font=f(mont, 80), fill=red if hot else ink)
        d.text((100, y + 92), where, font=f(mont, 34), fill=ink)
        d.text((W - 420, y + 30), st, font=f(mont, 38), fill=red if hot else (110, 104, 98))
        d.line((80, y + 150, W - 80, y + 150), fill=(180, 170, 158), width=2)
        y += 205
    d.text((80, H - 230), 'Aap ki seat kisi aur ko nahi di jaati.', font=f(marker, 58), fill=red)
    d.text((80, H - 130), 'Har subah ki pehli 10 minute', font=f(mont, 34), fill=(90, 84, 78))
    im.save(os.path.join(outdir, 'timetable.png'))

    # Ticket page: 1000 x 560 (aspect 1.786)
    TW, TH = 1000, 560
    tk = paper(TW, TH, (0.99, 0.97, 0.92))
    d = ImageDraw.Draw(tk)
    d.rectangle((0, 0, TW, 120), fill=red)
    d.text((50, 30), 'RESERVED', font=f(mont, 64), fill=(255, 248, 240))
    d.text((50, 170), 'SEAT', font=f(mont, 40), fill=(90, 84, 78))
    d.text((50, 215), '20', font=f(mont, 190), fill=ink)
    d.text((420, 170), 'CAR', font=f(mont, 40), fill=(90, 84, 78))
    d.text((420, 215), 'B', font=f(mont, 190), fill=ink)
    d.text((50, 450), '06:10 · PLATFORM 2', font=f(mont, 46), fill=ink)
    for x in range(TW - 60, TW - 20, 12):
        d.line((x, 170, x, 480), fill=(180, 170, 158), width=3)
    tk.save(os.path.join(outdir, 'ticket.png'))
    print('TEXTURES', outdir)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--make-textures':
        make_textures(sys.argv[2])
        sys.exit(0)

import wf_scenes as W  # noqa: E402  (sets dlopen flags before bpy loads)
import bpy  # noqa: E402
from wf_scenes import reset, ease, aim, set_camera, camera  # noqa: E402


def tex_mat(name, png, rough=0.82):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(png, check_existing=True)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Specular IOR Level'].default_value = 0.35
    return m


def flat_mat(name, color, rough=0.85):
    return W.mat(name, color, 0.0, rough)


def card(name, loc, w, h, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (w / 2, 0.006, h / 2)
    o.rotation_euler = rot
    o.data.materials.append(m)
    bev = o.modifiers.new('paper_edge', 'BEVEL')
    bev.width = 0.004
    bev.segments = 2
    if parent is not None:
        o.parent = parent
    return o


def disk(name, loc, rx, rz, m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1, depth=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = (math.radians(90), 0, 0)
    o.scale = (rx, rz, 0.02)
    o.data.materials.append(m)
    return o


CAMS = [(-1.6, -7.0, 1.7), (1.8, -6.2, 1.5), (0.0, -5.0, 1.9)]
TGTS = [(-0.2, 0, 1.9), (0.4, 0, 1.9), (-0.2, 0, 1.6)]


def build():
    W.world((0.06, 0.05, 0.045), 0.35)
    tt_mat = tex_mat('tt', '/tmp/wf01/tex/timetable.png')
    tk_mat = tex_mat('tk', '/tmp/wf01/tex/ticket.png')
    wall = flat_mat('wall', (0.12, 0.09, 0.075), 0.9)
    shade = flat_mat('shade', (0.035, 0.03, 0.03), 0.6)
    red = flat_mat('bench_red', (0.62, 0.1, 0.1), 0.55)

    card('wall', (0, 7.0, 2.0), 40, 26, wall)
    tt = card('timetable', (0, 3.2, 2.2), 3.2, 4.53, tt_mat)  # aspect 0.706

    # seated cut-out figure, mid layer (y = 1.0)
    fy = 1.0
    head = disk('head', (-0.55, fy, 2.85), 0.3, 0.33, shade)
    card('torso', (-0.55, fy, 2.1), 0.62, 0.95, shade)
    card('arm_up', (-0.14, fy, 2.25), 0.14, 0.78, shade, rot=(0, math.radians(-25), 0))
    arm = card('arm_hand', (0.02, fy, 2.55), 0.14, 0.62, shade, rot=(0, math.radians(20), 0))
    card('thigh', (-0.2, fy, 1.25), 0.78, 0.22, shade)
    card('shin', (0.14, fy, 0.68), 0.22, 0.95, shade)
    card('bench', (-0.1, fy - 0.05, 0.95), 1.9, 0.14, red)
    card('bench_leg', (-0.9, fy, 0.45), 0.12, 0.9, red)

    # front ticket page on a pivot at its left edge (flips about Z = vertical axis)
    pivot = bpy.data.objects.new('page_pivot', None)
    bpy.context.scene.collection.objects.link(pivot)
    pivot.location = (-0.75, -0.6, 2.4)
    ticket = card('ticket', (0, 0, 0), 1.5, 0.84, tk_mat, parent=pivot)
    ticket.location = (0.75, 0, 0)
    ticket.rotation_euler = (0, 0, 0)
    ticket.location = (0.75, 0, 0)

    key = W.area_light('key', (-4.0, -5.0, 5.0), (math.radians(50), 0, math.radians(-30)), 2.2, 260, (1.0, 0.92, 0.82))
    rim = W.point_light('rim', (3.5, 4.0, 4.5), 700, (1.0, 0.75, 0.45), 1.0)
    cams = [camera(f'shot_{i}', CAMS[i], TGTS[i], 32) for i in range(3)]
    return dict(tt=tt, head=head, arm=arm, pivot=pivot, ticket=ticket, key=key, rim=rim, cams=cams)


FLIP = (3.3, 3.8)


def update(t, S):
    cut = int(min(2, t // (DUR / 3)))
    st = (t - cut * DUR / 3) / (DUR / 3)
    cam = S['cams'][cut]
    slide = -1.0 + 2.0 * ease(st)
    base, tgt = CAMS[cut], TGTS[cut]
    aim(cam, (base[0] + 0.5 * slide, base[1], base[2]), (tgt[0] + 0.25 * slide, tgt[1], tgt[2]))
    set_camera(cam)
    # page flip: rotate pivot about Z (vertical axis)
    k = 0.0
    if t >= FLIP[0]:
        k = ease(min(1.0, (t - FLIP[0]) / (FLIP[1] - FLIP[0])))
    S['pivot'].rotation_euler = (0, 0, math.radians(-165 * k))
    S['pivot'].location = (-0.75 - 0.25 * math.sin(math.pi * k), -0.6 - 1.2 * k, 2.4)
    # figure: breath + reach toward the reserved row after the flip
    S['head'].location = (-0.55, 1.0, 2.85 + 0.02 * math.sin(t * 3.0))
    reach = ease(min(1.0, max(0.0, (t - 3.8) / 1.5)))
    S['arm'].rotation_euler = (0, math.radians(20 - 60 * reach), 0)
    S['rim'].location = (3.5 - 6 * st if cut == 1 else 3.5, 4.0, 4.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--res', default='360x640')
    ap.add_argument('--samples', type=int, default=32)
    ap.add_argument('--frames', default='0-299')
    ap.add_argument('--lookdev', type=float, default=None)
    a = ap.parse_args()
    rx, ry = [int(v) for v in a.res.split('x')]
    reset(rx, ry, a.samples)
    S = build()
    if a.lookdev is not None:
        update(a.lookdev, S)
        bpy.context.scene.render.filepath = a.out
        bpy.ops.render.render(write_still=True)
        print('LOOKDEV', a.out, flush=True)
        return
    os.makedirs(a.out, exist_ok=True)
    i0, i1 = [int(v) for v in a.frames.split('-')]
    bpy.context.scene.render.fps = FPS
    t0 = time.time()
    for i in range(i0, i1 + 1):
        path = os.path.join(a.out, f'f{i:04d}.png')
        if os.path.exists(path):
            continue
        update(i / FPS, S)
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print(f'frame {i + 1} t={i / FPS:.2f} elapsed {round(time.time() - t0)}s', flush=True)
    print('RENDER_DONE', flush=True)


if __name__ == '__main__':
    main()
