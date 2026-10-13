"""dogrig.py — the CC0 Husky (Quaternius Ultimate Animated Animal Pack, via trebeljahr/quaternius-showcase)
rendered as a golden toon dog for AMEER KA KUTTA. Blender 4.3 (bpy), Cycles CPU, one PNG per frame, RGBA.
Run inside bpy:  dogrig.py <out_dir> <anim:frames,...>  e.g.  Walk:0-24  Idle:0,20,40
"""
import bpy, math, os, sys, time
from mathutils import Vector

GLB = '/home/user/build/dog/Husky.glb'
GOLD_FUR = (0.80, 0.52, 0.22, 1.0)     # sRGB-ish gold; converted to linear below
CREAM = (0.93, 0.80, 0.56, 1.0)
DARK = (0.02, 0.018, 0.02, 1.0)
GOLD_D = (0.56, 0.33, 0.12, 1.0)   # saddle: deep gold instead of black

def srgb_to_lin(c):
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c[:3]) + (1.0,)

def build_scene(res):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=GLB)
    for o in list(bpy.data.objects):
        if o.name == 'Icosphere':
            bpy.data.objects.remove(o, do_unlink=True)
    arm = bpy.data.objects['AnimalArmature']
    body = bpy.data.objects['Cube']
    # recolour: grey-olive fur -> gold, white chest -> cream, near-black stays (nose, eyes, ears)
    recol = {'Material.001': GOLD_FUR, 'Material.003': CREAM, 'Material': GOLD_D, 'Material.002': DARK, 'Material.006': DARK}
    for m in bpy.data.materials:
        if m.name in recol:
            bsdf = m.node_tree.nodes['Principled BSDF']
            bsdf.inputs['Base Color'].default_value = srgb_to_lin(recol[m.name])
            bsdf.inputs['Roughness'].default_value = 0.62
            if 'Specular IOR Level' in bsdf.inputs:
                bsdf.inputs['Specular IOR Level'].default_value = 0.35
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 28
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.render.fps = 30
    # ortho side camera: the dog's long axis is Y, so look down +X (or -X)
    cam_d = bpy.data.cameras.new('cam')
    cam_d.type = 'ORTHO'
    cam_d.ortho_scale = 4.9
    cam = bpy.data.objects.new('cam', cam_d)
    bpy.context.collection.objects.link(cam)
    cam.location = (12.0, -0.45, 1.05)
    cam.rotation_euler = (math.radians(90), 0, math.radians(90))
    sc.camera = cam
    # three-point studio light (warm key, cool rim, soft fill), world = neutral grey so the alpha is clean
    def area(name, loc, energy, size, col):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy; ld.size = size; ld.color = col
        lo = bpy.data.objects.new(name, ld)
        bpy.context.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return lo
    area('key', (7.0, -4.5, 6.0), 900, 4.0, (1.0, 0.92, 0.80))
    area('rim', (-6.0, 5.0, 5.0), 700, 3.5, (0.70, 0.85, 1.0))
    area('fill', (5.0, 6.0, 1.5), 180, 6.0, (0.90, 0.95, 1.0))
    wd = bpy.data.worlds.new('w'); sc.world = wd; wd.use_nodes = True
    wd.node_tree.nodes['Background'].inputs['Color'].default_value = (0.5, 0.5, 0.5, 1)
    wd.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35
    return arm, body

def render_action(arm, name, frames, outdir):
    act = bpy.data.actions.get(f'AnimalArmature|{name}_AnimalArmature') or bpy.data.actions.get(name)
    arm.animation_data_create()
    arm.animation_data.action = act
    sc = bpy.context.scene
    for f in frames:
        sc.frame_set(int(f))
        sc.render.filepath = os.path.join(outdir, f'{name}_{int(f):03d}.png')
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print('RENDER', name, f, round(time.time() - t0, 1), 's', flush=True)

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:]
    outdir = argv[0]; res = int(argv[1]); spec = argv[2:]
    os.makedirs(outdir, exist_ok=True)
    arm, body = build_scene(res)
    for s in spec:
        name, rng = s.split(':')
        if '-' in rng:
            a, b = rng.split('-'); frames = list(range(int(a), int(b) + 1))
        else:
            frames = [int(x) for x in rng.split(',')]
        render_action(arm, name, frames, outdir)
