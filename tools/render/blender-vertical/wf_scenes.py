"""Monarch · three distinct 9:16 Blender (Cycles CPU) scenes, 10 s each.

Run inside the bpy venv with the X11/GL stub libraries on LD_LIBRARY_PATH:
  python wf_scenes.py --wf 02 --out frames_wf02 [--res 360x640] [--samples 48] [--frames 0-239]
  python wf_scenes.py --wf 02 --lookdev 3.5 --out lookdev_wf02.png

Every frame is evaluated from time t inside Python.

WF-02  ZACK-D POWER    : gold/chrome tower, one cube per second; extruded 3-D text "30 HRS"
                         rotates in at 6.5 s; four hard camera cuts; cyan rim + key sweep.
WF-03  MIDNIGHT NOIR   : one reserved ticket under a swinging lamp, volumetric haze in a
                         cube, train window light crossing the wall, lamp dies at 8.4 s.
WF-01  PAPER CINEMA    : three paper layers at different depths (parallax), a 3-D shade
                         figure, page-turn flips at each cut.
"""
import argparse
import math
import os
import random
import sys
import time

sys.setdlopenflags(os.RTLD_LAZY | os.RTLD_GLOBAL)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

FPS = 24


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def bounce(x):
    x = min(1.0, max(0.0, x))
    n1, d1 = 7.5625, 2.75
    if x < 1 / d1:
        return n1 * x * x
    if x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x * x + 0.75
    if x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x * x + 0.9375
    x -= 2.625 / d1
    return n1 * x * x + 0.984375


# ----------------------------------------------------------------- scene helpers
def reset(res_x, res_y, samples):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 6
    sc.render.resolution_x = res_x
    sc.render.resolution_y = res_y
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.film_transparent = False
    sc.render.fps = FPS
    return sc


def world(color, strength):
    sc = bpy.context.scene
    w = bpy.data.worlds.new('world')
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (*color, 1)
    bg.inputs['Strength'].default_value = strength
    sc.world = w


def mat(name, color=(0.8, 0.8, 0.8), metallic=0.0, rough=0.5, emit=None, emit_strength=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = rough
    if emit is not None:
        p.inputs['Emission Color'].default_value = (*emit, 1)
        p.inputs['Emission Strength'].default_value = emit_strength
    if alpha < 1:
        p.inputs['Alpha'].default_value = alpha
    return m


def set_emit(m, strength):
    m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = strength


def cube(name, loc, scale, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.data.materials.append(m)
    return o


def plane(name, loc, rot, scale, m):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = rot
    o.scale = scale
    o.data.materials.append(m)
    return o


def sphere(name, loc, r, m):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=48, ring_count=24)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(m)
    return o


def cyl(name, loc, r, depth, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(m)
    return o


def text3d(name, body, loc, size, m, extrude=0.06, align='CENTER'):
    bpy.ops.object.text_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.data.body = body
    o.data.size = size
    o.data.extrude = extrude
    o.data.bevel_depth = 0.004
    o.data.bevel_resolution = 2
    o.data.align_x = align
    o.data.materials.append(m)
    return o


def point_light(name, loc, energy, color=(1, 1, 1), radius=0.5):
    d = bpy.data.lights.new(name, 'POINT')
    d.energy = energy
    d.color = color
    d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    return o


def area_light(name, loc, rot, size, energy, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, 'AREA')
    d.energy = energy
    d.color = color
    d.size = size
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    return o


def camera(name, loc, target, lens=35):
    d = bpy.data.cameras.new(name)
    d.lens = lens
    d.sensor_width = 36
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    aim(o, loc, target)
    return o


def aim(o, loc, target):
    o.location = Vector(loc)
    direction = Vector(target) - Vector(loc)
    o.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def set_camera(obj):
    bpy.context.scene.camera = obj


# ----------------------------------------------------------------- WF-02 · ZACK-D POWER
WF02_CAMS = [(0, -21, 6.8), (15, -15, 13.0), (-14, -14, 4.0), (0, -27, 9.0)]
WF02_TGT = [(0, 0, 6.8), (0, 0, 6.8), (0, 0, 5.5), (0, 0, 7.2)]


def sky_world(strength=0.6, sun_elev_deg=14.0, sun_rot_deg=200.0, air=1.0, dust=0.6):
    """Procedural Nishita sky as the world. Gives metal a real environment to reflect."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new('world_sky')
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'NISHITA'
    sky.sun_elevation = math.radians(sun_elev_deg)
    sky.sun_rotation = math.radians(sun_rot_deg)
    sky.air_density = air
    sky.dust_density = dust
    nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength
    sc.world = w


def build_wf02():
    # Default flat = r5 baseline. WF02_WORLD=sky enables the Nishita sky (lookdev r6, not accepted).
    if os.environ.get('WF02_WORLD', 'flat') == 'flat':
        world((0.22, 0.27, 0.36), 1.1)
    else:
        sky_world(strength=float(os.environ.get('WF02_SKY', '0.6')))
    floor = mat('floor', (0.02, 0.022, 0.03), 0.0, 0.12)
    plane('floor', (0, 0, 0), (0, 0, 0), (40, 40, 1), floor)
    gold = mat('gold', (1.0, 0.72, 0.28), 1.0, 0.18)
    chrome = mat('chrome', (0.85, 0.87, 0.92), 1.0, 0.05)
    cyan = mat('cyan', (0.2, 0.9, 1.0), 0.0, 0.2, emit=(0.2, 0.9, 1.0), emit_strength=0.0)
    cubes = []
    for k in range(10):
        m = gold if k % 2 == 0 else chrome
        cubes.append(cube(f'tower{k}', (0, 0, 0.5 + k * 1.25), (0.5, 0.5, 0.5), m))
    txt = text3d('txt', '30 HRS', (0, 0, 13.4), 1.3, cyan, extrude=0.22)
    txt.rotation_euler = (math.radians(90), 0, 0)
    key = area_light('key', (0, -9, 14), (math.radians(35), 0, 0), 10, 2600)
    rim = point_light('rim', (-6, 6, 8), 900, (0.3, 0.9, 1.0), 1.0)
    fill = point_light('fill', (8, -10, 5), 2500, (1.0, 0.7, 0.4), 2.0)
    cams = [camera(f'shot_{i}', WF02_CAMS[i], WF02_TGT[i], 50) for i in range(4)]
    return dict(cubes=cubes, txt=txt, cyan=cyan, rim=rim, key=key, cams=cams)


def update_wf02(t, S):
    for k, c in enumerate(S['cubes']):
        age = (t - k) / 0.9
        y_final = 0.5 + k * 1.25
        drop = (1.0 - bounce(age)) * 4.0 if age < 1 else 0.0
        if t < k:
            c.hide_render = True
            continue
        c.hide_render = False
        c.location = (0, 0, y_final + drop)
        c.rotation_euler = (0, 0, math.radians(12 * k + 6 * min(1, age)))
    rise = ease((t - 6.5) / 2.0)
    S['txt'].rotation_euler = (math.radians(90 * (1 - rise)), 0, 0)
    S['txt'].scale = (rise, rise, rise)
    set_emit(S['cyan'], 1.2 + 2.2 * rise)
    cut = int(min(3, t // 2.5))
    shot_t = (t - cut * 2.5) / 2.5
    cam = S['cams'][cut]
    base = WF02_CAMS[cut]
    push = 1.0 - 0.12 * ease(shot_t)
    aim(cam, (base[0] * push, base[1] * push, base[2]), WF02_TGT[cut])
    set_camera(cam)
    S['rim'].location = (-6 + 12 * shot_t, 6, 8)
    S['rim'].data.energy = 1500 + 1000 * math.sin(math.pi * shot_t)


# ----------------------------------------------------------------- WF-03 · MIDNIGHT NOIR
WF03_CAMS = [(0, -3.0, 1.9), (1.2, -2.2, 1.6), (-0.8, -4.6, 2.4)]
WF03_TGT = [(0, -1.0, 0.72), (0, -1.0, 0.72), (0, -1.0, 0.8)]


def build_wf03():
    world((0.003, 0.004, 0.008), 0.05)
    wet = mat('wet_floor', (0.02, 0.025, 0.035), 0.0, 0.06)
    plane('floor', (0, 0, 0), (0, 0, 0), (30, 30, 1), wet)
    wall = mat('wall', (0.03, 0.032, 0.045), 0.0, 0.4)
    plane('wall', (0, 6, 0), (math.radians(90), 0, 0), (30, 12, 1), wall)
    wood = mat('wood', (0.12, 0.07, 0.04), 0.0, 0.6)
    steel = mat('steel', (0.05, 0.05, 0.06), 0.9, 0.3)
    cube('bench_seat', (0, -1.0, 0.62), (2.2, 0.5, 0.08), wood)
    cube('bench_leg_l', (-2.0, -1.0, 0.3), (0.07, 0.45, 0.3), steel)
    cube('bench_leg_r', (2.0, -1.0, 0.3), (0.07, 0.45, 0.3), steel)
    cream = mat('ticket', (0.92, 0.86, 0.66), 0.0, 0.5)
    cube('ticket_card', (0, -1.0, 0.73), (0.55, 0.32, 0.012), cream)
    red = mat('stamp', (0.8, 0.07, 0.05), 0.0, 0.3, emit=(0.8, 0.07, 0.05), emit_strength=0.0)
    stamp = cube('stamp', (0.22, -1.0, 0.742), (0.16, 0.09, 0.006), red)
    warm = mat('bulb', (1, 0.8, 0.5), 0.0, 0.2, emit=(1.0, 0.75, 0.45), emit_strength=40)
    bulb = sphere('bulb', (0, -1.0, 7.0), 0.22, warm)
    cord = cyl('cord', (0, -1.0, 8.4), 0.012, 2.8, steel)
    trainm = mat('train', (0.4, 0.55, 0.9), 0.0, 0.2, emit=(0.4, 0.55, 0.9), emit_strength=8)
    train = plane('train', (-16, 5.9, 3.5), (math.radians(90), 0, 0), (1.3, 3.0, 1), trainm)
    # volumetric haze inside a cube the camera sits inside
    vol = cube('haze', (0, 0, 4), (14, 14, 8), mat('haze_mat', (0.5, 0.5, 0.5), 0.0, 0.5))
    if os.environ.get('NOVOL'):
        vol.hide_render = True
    vol.display_type = 'WIRE'
    vm = bpy.data.materials.new('haze_vol')
    vm.use_nodes = True
    nt = vm.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    pv = nt.nodes.new('ShaderNodeVolumePrincipled')
    pv.inputs['Density'].default_value = 0.004
    pv.inputs['Anisotropy'].default_value = 0.45
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(pv.outputs['Volume'], out.inputs['Volume'])
    vol.data.materials.clear()
    vol.data.materials.append(vm)
    dust_m = mat('dust', (1, 0.9, 0.7), 0.0, 0.5, emit=(1, 0.85, 0.6), emit_strength=0.0)
    rng = random.Random(3)
    dusts = [sphere(f'dust{i}', (rng.uniform(-4, 4), rng.uniform(-3, 2), rng.uniform(1.5, 6)), 0.02, dust_m)
             for i in range(24)]
    lamp_light = point_light('lamp_light', (0, -1.0, 6.8), 4200, (1.0, 0.78, 0.5), 0.9)
    cams = [camera(f'shot_{i}', WF03_CAMS[i], WF03_TGT[i], 40) for i in range(3)]
    return dict(bulb=bulb, bulb_mat=warm, stamp=stamp, red=red, train=train, trainm=trainm,
                cord=cord, lamp=lamp_light, dusts=dusts, dust_m=dust_m, cams=cams)


def update_wf03(t, S):
    lamp_on = 1.0 - ease((t - 8.4) / 1.4)
    swing = math.radians(9 * math.sin(2 * math.pi * 0.45 * t) * (1 - ease((t - 8.0) / 1.5)))
    x = 7.0 * math.sin(swing) * 0.2
    z = 7.0 - 0.4 * (1 - math.cos(swing))
    S['bulb'].location = (x, -1.0, z)
    S['cord'].location = (x, -1.0, z + 1.2)
    set_emit(S['bulb_mat'], 40 * lamp_on + 0.01)
    S['lamp'].location = (x, -1.0, z - 0.3)
    S['lamp'].data.energy = 4200 * lamp_on + 0.01
    set_emit(S['dust_m'], 1.4 * lamp_on)
    if 1.5 <= t <= 5.0:
        u = (t - 1.5) / 3.5
        S['train'].location = (-16 + 32 * u, 5.9, 3.5)
        set_emit(S['trainm'], 8.0)
    else:
        S['train'].location = (60, 5.9, 3.5)
    rise = ease((t - 4.0) / 2.0)
    tk = bpy.data.objects['ticket_card']
    tk.location = (0, -1.0, 0.73)
    tk.rotation_euler = (0, 0, math.radians(14 * rise))
    st = S['stamp']
    st.location = (0.22, -1.0, 0.742)
    s_on = ease((t - 5.5) / 0.6)
    st.scale = (0.16 * s_on + 0.001, 0.09 * s_on + 0.001, 0.006)
    set_emit(S['red'], 2.0 * s_on)
    cut = int(min(2, t // 4.0))
    shot_t = (t - cut * 4.0) / 4.0
    cam = S['cams'][cut]
    base = WF03_CAMS[cut]
    push = 1.0 - 0.15 * ease(shot_t)
    aim(cam, (base[0] * push, base[1] * push, base[2]), WF03_TGT[cut])
    set_camera(cam)


# ----------------------------------------------------------------- WF-01 · PAPER CINEMA
WF01_CAMS = [(-1.5, -11, 1.6), (2.5, -9, 1.2), (0, -12.5, 2.0)]
WF01_TGT = [(-0.4, 0, 1.6), (0.8, 0, 1.2), (0, 0, 1.6)]


def build_wf01():
    world((0.22, 0.21, 0.2), 0.3)
    paper_back = mat('paper_back', (0.93, 0.88, 0.78), 0.0, 0.85)
    paper_mid = mat('paper_mid', (0.97, 0.94, 0.88), 0.0, 0.8)
    paper_front = mat('paper_front', (0.99, 0.97, 0.92), 0.0, 0.75)
    red = mat('ink_red', (0.75, 0.16, 0.16), 0.0, 0.6)
    ink = mat('ink', (0.1, 0.09, 0.1), 0.0, 0.5)
    shade = mat('shade', (0.02, 0.02, 0.025), 0.0, 0.35)
    eyes = mat('eyes', (0.9, 0.95, 1.0), 0.0, 0.2, emit=(0.9, 0.95, 1.0), emit_strength=6.0)
    back = plane('paper_back', (0, 4, 0), (math.radians(90), 0, 0), (9, 5, 1), paper_back)
    mid = plane('paper_mid', (0, 1.5, 0), (math.radians(90), 0, 0), (5.2, 3.2, 1), paper_mid)
    front = plane('paper_front', (-0.6, -0.8, 0), (math.radians(90), 0, 0), (2.8, 1.9, 1), paper_front)
    title = text3d('title', 'SEAT KHAALI', (0, 1.42, 2.6), 0.42, red, extrude=0.02)
    title.rotation_euler = (math.radians(90), 0, 0)
    title2 = text3d('title2', 'NAHI REHTI.', (0, 1.42, 2.05), 0.42, red, extrude=0.02)
    title2.rotation_euler = (math.radians(90), 0, 0)
    head = sphere('shade_head', (-1.2, -0.85, 1.5), 0.34, shade)
    eye_l = sphere('eye_l', (-1.08, -1.2, 1.56), 0.05, eyes)
    eye_r = sphere('eye_r', (-1.32, -1.2, 1.56), 0.05, eyes)
    cube('torso', (-1.2, -0.85, 0.85), (0.32, 0.2, 0.42), shade)
    arm_r = cyl('arm_r', (-0.6, -0.85, 0.9), 0.07, 0.8, shade, rot=(0, math.radians(90), 0))
    cyl('leg_l', (-1.35, -0.85, 0.2), 0.08, 0.6, shade)
    cyl('leg_r', (-1.05, -0.85, 0.2), 0.08, 0.6, shade)
    ticket = cube('ticket', (1.3, -0.9, 0.6), (0.7, 0.05, 0.4), red)
    ticket_card = cube('ticket_card', (1.3, -0.95, 0.6), (0.62, 0.02, 0.34), paper_front)
    text3d('tnum', '20', (0.9, -1.0, 0.7), 0.46, ink, extrude=0.02)
    key = area_light('key', (-4.5, -5.5, 4.5), (math.radians(55), 0, math.radians(-35)), 2.5, 380, (1.0, 0.93, 0.85))
    cams = [camera(f'shot_{i}', WF01_CAMS[i], WF01_TGT[i], 32 if i < 2 else 30) for i in range(3)]
    return dict(back=back, mid=mid, front=front, title=title, title2=title2, head=head, arm=arm_r,
                eye_l=eye_l, eye_r=eye_r, ticket=ticket, ticket_card=ticket_card, key=key, cams=cams)


def update_wf01(t, S):
    cut = int(min(2, t // 2.5))
    shot_t = (t - cut * 2.5) / 2.5
    cam = S['cams'][cut]
    slide = -1.0 + 2.0 * ease(shot_t)
    base = WF01_CAMS[cut]
    target = WF01_TGT[cut]
    aim(cam, (base[0] + slide * 0.6, base[1], base[2]), (target[0] + slide * 0.2, target[1], target[2]))
    set_camera(cam)
    turn = 0.0
    for c in (2.5, 5.0, 7.5):
        d = t - c
        if 0 <= d <= 0.45:
            turn = ease(d / 0.45)
    S['front'].rotation_euler = (math.radians(90), 0, math.radians(-160 * turn))
    S['front'].location = (-0.6 + 0.8 * turn, -0.8 - 0.15 * turn, 0)
    S['ticket'].location = (1.3 + 0.1 * math.sin(t * 2.0), -0.9, 0.6 + 0.05 * math.sin(t * 3.0))
    S['ticket_card'].location = (S['ticket'].location.x, -0.95, S['ticket'].location.z)
    S['arm'].rotation_euler = (0, math.radians(90 + 14 * ease(min(1, t / 2.0)) * math.sin(t * 2.0)), 0)
    S['head'].location = (-1.2, -0.85, 1.5 + 0.03 * math.sin(t * 4.0))


BUILD = {'02': build_wf02, '03': build_wf03, '01': build_wf01}
UPDATE = {'02': update_wf02, '03': update_wf03, '01': update_wf01}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wf', required=True, choices=['01', '02', '03'])
    ap.add_argument('--out', required=True)
    ap.add_argument('--res', default='360x640')
    ap.add_argument('--samples', type=int, default=48)
    ap.add_argument('--frames', default='0-239')
    ap.add_argument('--lookdev', type=float, default=None)
    a = ap.parse_args()
    rx, ry = [int(v) for v in a.res.split('x')]
    reset(rx, ry, a.samples)
    S = BUILD[a.wf]()
    if a.lookdev is not None:
        UPDATE[a.wf](a.lookdev, S)
        bpy.context.scene.render.filepath = a.out
        bpy.ops.render.render(write_still=True)
        print('LOOKDEV', a.out, flush=True)
        return
    os.makedirs(a.out, exist_ok=True)
    i0, i1 = [int(v) for v in a.frames.split('-')]
    fps = 30 if a.wf == '01' else FPS
    bpy.context.scene.render.fps = fps
    t0 = time.time()
    for i in range(i0, i1 + 1):
        t = i / fps
        path = os.path.join(a.out, f'f{i:04d}.png')
        if os.path.exists(path):
            continue
        UPDATE[a.wf](t, S)
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print(f'frame {i + 1} t={t:.2f} elapsed {round(time.time() - t0)}s', flush=True)
    print('RENDER_DONE', flush=True)


if __name__ == '__main__':
    main()
