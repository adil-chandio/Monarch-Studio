"""dog3d.py — the golden dog as a real 3D model (Blender bpy, Cycles), for AMEER KA KUTTA v3.

Built from metaball ellipsoids (smooth organic union), converted to mesh, subdivided, smooth-shaded.
Materials: golden fur (Principled, sheen), black nose and eyes, gold collar and tag.
Renders a transparent RGBA PNG per frame so the 2.5D film can composite it with its own sets.

Run (bpy 4.3.0 needs the X/GL stub preload on this host, see docs in the session log):
  LD_PRELOAD=/tmp/stubs/libstubs_all.so LD_LIBRARY_PATH=/tmp/stubs /tmp/venvs/bpy/bin/python dog3d.py still out.png
"""
import math
import sys

import bpy

FUR = (0.95, 0.62, 0.22, 1.0)
FUR_D = (0.55, 0.33, 0.14, 1.0)
GOLD = (0.95, 0.74, 0.32, 1.0)
BLACK = (0.02, 0.015, 0.02, 1.0)


def _clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _mat(name, rgba, rough=0.5, metal=0.0, sheen=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if 'Sheen Weight' in b.inputs:
        b.inputs['Sheen Weight'].default_value = sheen
    return m


def _ellipsoid(mb, co, r, sz=None):
    e = mb.elements.new(type='ELLIPSOID')
    e.co = co
    e.radius = r
    e.stiffness = 3.2
    if sz:
        e.size_x, e.size_y, e.size_z = sz
    return e


def build_body(pose='stand'):
    """Metaball body. Coordinates: +X forward (head), Z up, ground at z=0. Units ~ 1 = 1 m-ish."""
    mb = bpy.data.metaballs.new('dog_mb')
    mb.resolution = 0.035
    mb.render_resolution = 0.018
    mb.threshold = 0.42
    # torso: deep chest, tucked waist, flat back
    _ellipsoid(mb, (0.0, 0.0, 1.00), 0.52, (1.08, 0.62, 0.70))
    _ellipsoid(mb, (0.52, 0.0, 1.04), 0.48, (0.62, 0.58, 0.78))
    # neck + head + muzzle
    _ellipsoid(mb, (0.82, 0.0, 1.48), 0.30, (0.45, 0.36, 0.55))
    _ellipsoid(mb, (1.12, 0.0, 1.70), 0.34, (1.0, 0.92, 1.0))
    _ellipsoid(mb, (1.42, 0.0, 1.60), 0.20, (1.45, 0.62, 0.70))
    # floppy ears
    _ellipsoid(mb, (0.98, 0.30, 1.52), 0.16, (0.6, 0.55, 1.3))
    _ellipsoid(mb, (0.98, -0.30, 1.52), 0.16, (0.6, 0.55, 1.3))
    # legs: upper, knee, paw (front pair at x=0.62, back pair at x=-0.56)
    for x, yo in [(0.62, 0.20), (0.62, -0.20), (-0.56, 0.20), (-0.56, -0.20)]:
        _ellipsoid(mb, (x, yo, 0.66), 0.26, (1.0, 1.0, 1.7))
        _ellipsoid(mb, (x, yo, 0.24), 0.19, (1.0, 1.0, 1.4))
        _ellipsoid(mb, (x + 0.08, yo, 0.08), 0.18, (1.5, 1.1, 0.6))
    # tail: a chain of balls, rising and curling up
    for k, (x, z, r) in enumerate([(-0.90, 1.00, 0.22), (-1.06, 1.12, 0.21), (-1.20, 1.28, 0.20),
                                    (-1.30, 1.46, 0.19), (-1.34, 1.64, 0.18), (-1.32, 1.80, 0.16)]):
        _ellipsoid(mb, (x, 0.0, z), r, (1.0, 1.0, 1.0))
    obj = bpy.data.objects.new('dog', mb)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    me = bpy.context.view_layer.objects.active
    bpy.ops.object.shade_smooth()
    sub = me.modifiers.new('sub', 'SUBSURF')
    sub.levels = 1
    sub.render_levels = 2
    me.data.materials.clear()
    me.data.materials.append(_mat('fur', FUR, rough=0.62, sheen=0.4))
    me.active_material = me.data.materials[0]
    return me


def add_details():
    """Nose, eyes, collar and gold tag."""
    def sph(name, loc, r, mat, sc=(1, 1, 1)):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=32, ring_count=16)
        o = bpy.context.active_object
        o.name = name
        o.scale = sc
        bpy.ops.object.shade_smooth()
        o.data.materials.append(mat)
        return o

    black = _mat('black', BLACK, rough=0.25)
    white = _mat('white', (1, 1, 1, 1), rough=0.2)
    sph('nose', (1.72, 0.0, 1.66), 0.07, black, (1.2, 1.0, 0.8))
    for s in (1, -1):
        sph('eye', (1.27, 0.15 * s, 1.78), 0.07, black)
        sph('glint', (1.30, 0.17 * s, 1.81), 0.022, white)
    # collar: torus around the neck (in the XZ plane tilted), gold
    gold = _mat('gold', GOLD, rough=0.22, metal=1.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.36, minor_radius=0.045, location=(0.86, 0.0, 1.30),
                                      rotation=(math.radians(90), 0, math.radians(-14)))
    c = bpy.context.active_object
    c.name = 'collar'
    c.scale = (0.9, 1.0, 1.0)
    c.data.materials.append(gold)
    bpy.ops.object.shade_smooth()
    # tag: diamond below the collar
    bpy.ops.mesh.primitive_cone_add(radius1=0.09, depth=0.12, location=(1.05, 0.0, 1.05))
    t = bpy.context.active_object
    t.name = 'tag'
    t.rotation_euler = (math.radians(180), 0, 0)
    t.data.materials.append(gold)


def add_world_and_lights():
    scn = bpy.context.scene
    scn.render.film_transparent = True
    # key (warm), rim (cool), fill
    for name, loc, energy, color, size in [
        ('key', (3.0, -3.0, 4.0), 110, (1.0, 0.92, 0.82), 3.0),
        ('rim', (-3.0, 3.0, 3.5), 90, (0.72, 0.85, 1.0), 3.0),
        ('fill', (0.0, -4.0, 1.5), 25, (1.0, 0.95, 0.9), 5.0),
    ]:
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.color = color
        ld.size = size
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        scn.collection.objects.link(lo)
        # aim at the dog
        d = (0.4, 0.0, 1.0)
        dx, dy, dz = d[0] - loc[0], d[1] - loc[1], d[2] - loc[2]
        yaw = math.atan2(dy, dx)
        pitch = math.atan2(dz, math.hypot(dx, dy))
        lo.rotation_euler = (math.pi / 2 + pitch, 0, yaw - math.pi / 2)


def add_camera(res=1080):
    scn = bpy.context.scene
    cd = bpy.data.cameras.new('cam')
    cd.lens = 55
    co = bpy.data.objects.new('cam', cd)
    scn.collection.objects.link(co)
    co.location = (0.2, -8.2, 1.35)
    tgt = bpy.data.objects.new('tgt', None)
    tgt.location = (0.25, 0.0, 1.1)
    scn.collection.objects.link(tgt)
    tc = co.constraints.new('TRACK_TO')
    tc.target = tgt
    tc.track_axis = 'TRACK_NEGATIVE_Z'
    tc.up_axis = 'UP_Y'
    scn.camera = co


def setup_render(out_path, res=540, samples=48):
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'CPU'
    scn.cycles.samples = samples
    scn.cycles.use_denoising = True
    scn.render.resolution_x = res
    scn.render.resolution_y = res
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGBA'
    scn.render.filepath = out_path
    scn.view_settings.view_transform = 'AgX'
    scn.view_settings.look = 'AgX - Medium High Contrast'


def still(out_path, res=540):
    _clear()
    build_body()
    add_details()
    add_world_and_lights()
    add_camera()
    setup_render(out_path, res=res)
    bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    mode = argv[0] if argv else 'still'
    out = argv[1] if len(argv) > 1 else '/home/user/build/kutta/v3/dog3d_still.png'
    if mode == 'still':
        still(out)
        print('rendered', out)
