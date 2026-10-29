"""Build the CHAOS 04 film scene and save a .blend ready for resumable renders.

    blender -b --python chaos04/build.py -- --out build/chaos04.blend
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chaos04 import bl, camera, character, direct, world  # noqa: E402
from chaos04.bl import TAU, lerp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

LIGHT_NAMES = ["door_glow", "rim_teal", "rim_amber", "practical", "key", "fill",
               "rack_key", "floor_pool", "corr0", "corr1", "corr2", "corr3", "corr4",
               "corr_fill", "corr_end", "void_key", "endcard_fill"]


def clean_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def configure(scene, width=1080, height=1920, samples=24, device="CPU", fps=30):
    scene.render.engine = "CYCLES"
    scene.cycles.device = device
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.05
    scene.cycles.adaptive_min_samples = 0
    scene.cycles.max_bounces = 3
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.cycles.transmission_bounces = 2
    scene.cycles.transparent_max_bounces = 4
    scene.cycles.volume_bounces = 1
    scene.cycles.sample_clamp_indirect = 3.0
    scene.cycles.caustics_reflective = False
    scene.cycles.caustics_refractive = False
    scene.cycles.volume_step_rate = 2.0
    scene.cycles.blur_glossy = 1.0
    scene.render.use_persistent_data = True
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.fps = fps
    scene.render.fps_base = 1.0
    scene.frame_start = 1
    scene.frame_end = 1332
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "16"
    scene.render.image_settings.compression = 30
    scene.render.film_transparent = False
    scene.render.use_motion_blur = False   # speed first; whip energy comes from the camera
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0


def compositor(scene):
    """Only stable, well-tested nodes: our grade is finished in ffmpeg."""
    scene.use_nodes = True
    nt = scene.node_tree
    nt.nodes.clear()
    links = nt.links
    rl = nt.nodes.new("CompositorNodeRLayers")
    glare = nt.nodes.new("CompositorNodeGlare")
    glare.glare_type = "FOG_GLOW"
    glare.quality = "HIGH"
    glare.threshold = 3.2
    glare.size = 7
    glare.mix = -0.86
    out = nt.nodes.new("CompositorNodeComposite")
    links.new(rl.outputs["Image"], glare.inputs["Image"])
    last = glare
    try:
        lens = nt.nodes.new("CompositorNodeLensdist")
        lens.inputs["Distort"].default_value = -0.012
        lens.inputs["Dispersion"].default_value = 0.012
        links.new(last.outputs["Image"], lens.inputs["Image"])
        last = lens
    except Exception:
        pass
    links.new(last.outputs["Image"], out.inputs["Image"])


def bake_character(scene, rig):
    """Bake Monarch's performance for all 1332 frames, plus his world placement."""
    rest = {pb.name: pb.bone.matrix_local.to_quaternion() for pb in rig.pose.bones}
    bones = [n for n in rest if n != "root"]
    quats = {b: [] for b in bones}
    root_quats, root_locs = [], []
    hidden = Vector((0.0, 0.0, -140.0))

    for f in range(1, 1333):
        seg = direct.segment_at(f)
        pose = direct.pose_for(seg, f)
        if pose is None:
            res = Vector((0, 0, 0))
            qroot = Quaternion((1, 0, 0, 0))
            root_locs.append(hidden)
        else:
            pos, yaw = direct.char_world(seg, f)
            qroot = Euler((0, 0, math.radians(yaw)), "XYZ").to_quaternion()
            root_locs.append(Vector(pos))
        for b in bones:
            key = None
            if pose:
                for short, full in direct.BONE_MAP.items():
                    if full == b:
                        key = short
                        break
            local = pose.get(key) if (pose and key) else None
            if local is None:
                quats[b].append(Quaternion((1, 0, 0, 0)))
            else:
                rq = rest[b]
                quats[b].append(rq.inverted() @ Euler(
                    (math.radians(local[0]), math.radians(local[1]),
                     math.radians(local[2])), "XYZ").to_quaternion() @ rq)
        root_quats.append(qroot)

    frames = list(range(1, 1333))
    for b in bones:
        path = f'pose.bones["{b}"].rotation_quaternion'
        for i in range(4):
            bl.bake_curve(rig, path, i, frames, [q[i] for q in quats[b]])
    rq = rest["root"]
    for i in range(4):
        bl.bake_curve(rig, 'pose.bones["root"].rotation_quaternion', i, frames,
                      [(rq.inverted() @ q @ rq)[i] for q in root_quats])
    for i in range(3):
        bl.bake_curve(rig, 'pose.bones["root"].location', i, frames,
                      [(rq.inverted() @ v)[i] for v in root_locs])


def bake_lights(scene, lights):
    frames, energies = [], {name: [] for name in LIGHT_NAMES}
    for seg in direct.SEGMENTS:
        frames.append(seg["start"])
        spec = seg.get("lights", {})
        for name in LIGHT_NAMES:
            energies[name].append(float(spec.get(name, 0.0)))
    frames.append(1333)
    for name in LIGHT_NAMES:
        energies[name].append(0.0)
        ob = lights.get(name)
        if ob is None:
            continue
        bl.bake_curve(ob.data, "energy", 0, frames, energies[name], "CONSTANT")


def bake_world(scene, default=0.030, default_color="#0A1216"):
    """Ambient bounce per set: the corridor needs real fill, the void needs a lot."""
    frames, strengths = [], []
    cols = {0: [], 1: [], 2: []}
    for seg in direct.SEGMENTS:
        frames.append(seg["start"])
        strengths.append(float(seg.get("world", default)))
        hexs = seg.get("world_color", default_color).lstrip("#")
        rgb = [int(hexs[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
        rgb = [(c / 12.92) * 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        for i in range(3):
            cols[i].append(rgb[i])
    frames.append(1333)
    strengths.append(strengths[-1])
    for i in range(3):
        cols[i].append(cols[i][-1])
    base = 'node_tree.nodes["Background"].inputs[%d].default_value'
    bl.bake_curve(scene.world, base % 1, 0, frames, strengths, "CONSTANT")
    for i in range(3):
        bl.bake_curve(scene.world, base % 0, i, frames, cols[i], "CONSTANT")


def bake_exposure(scene):
    frames, values = [], []
    for seg in direct.SEGMENTS:
        frames.append(seg["start"])
        values.append(float(seg.get("exposure", 0.0)))
    frames.append(1333)
    values.append(values[-1])
    bl.bake_curve(scene, "view_settings.exposure", 0, frames, values, "CONSTANT")


def hide_by_segment(objects, tag):
    """Render objects only inside the segments that name them in `tag`."""
    frames, hidden = [], []
    for seg in direct.SEGMENTS:
        frames.append(seg["start"])
        on = bool(seg.get(tag, 0.0))
        hidden.append(0.0 if on else 1.0)
    frames.append(1333)
    hidden.append(1.0)
    for ob in objects:
        bl.bake_curve(ob, "hide_render", 0, frames, hidden, "CONSTANT")
        bl.bake_curve(ob, "hide_viewport", 0, frames, hidden, "CONSTANT")


def build_brood():
    """Our own shadow doubles: six stretched arms and three standing silhouettes."""
    m_dark = bl.material("Brood dark", base="#07090A", rough=0.55, spec=0.2)
    objs = []
    origin = world.ROOM + Vector((0.0, 0.55, 0.0))
    for i in range(3):
        x = -0.55 + 0.55 * i
        h = 1.62 + 0.06 * i
        objs.append(bl.loft(f"Brood body {i}", [
            ((origin.x + x, origin.y + 0.75 + 0.18 * i, 0.02), 0.13, 0.11),
            ((origin.x + x, origin.y + 0.75 + 0.18 * i, 0.55), 0.16, 0.13),
            ((origin.x + x, origin.y + 0.75 + 0.18 * i, 1.15), 0.17, 0.13),
            ((origin.x + x, origin.y + 0.75 + 0.18 * i, h), 0.10, 0.09),
            ((origin.x + x, origin.y + 0.75 + 0.18 * i, h + 0.14), 0.05, 0.05),
        ], m_dark, subsurf=2))
    for i in range(6):
        side = 1 if i % 2 else -1
        k = i // 2
        base = Vector((origin.x + 0.12 * side, origin.y + 0.55 + 0.1 * k, 1.42))
        pts = [tuple(base)]
        for j in range(4):
            u = (j + 1) / 4
            pts.append((base.x + side * (0.20 + 0.55 * u) * (1 + 0.15 * k),
                        base.y + 0.24 * u - 0.10 * k,
                        base.z + 0.55 * u - 0.28 * u * u + 0.12 * k))
        objs.append(bl.tube_path(f"Brood arm {i}", pts, 0.045, m_dark, sides=8, taper=0.25))
    return objs


def build_tendrils():
    m = bl.material("Tendril", base="#080A0B", rough=0.4, spec=0.35)
    origin = world.ROOM
    objs = []
    for i in range(6):
        a = TAU * i / 6
        pts = []
        for j in range(9):
            u = j / 8
            pts.append((origin.x + math.cos(a) * (0.24 + 0.42 * u) + 0.05 * math.sin(u * 6 + i),
                        origin.y + 0.10 + math.sin(a) * (0.22 + 0.34 * u),
                        1.42 + 0.30 * math.sin(u * 2.4 + i) - 0.18 * u))
        objs.append(bl.tube_path(f"Tendril {i}", pts, 0.022, m, sides=6, taper=0.3))
    return objs


def build_sparks():
    m = bl.emission_material("Spark", "#FFD9A6", 60.0)
    objs = []
    rng = __import__("random").Random(23)
    for i in range(90):
        r = 0.006 + 0.004 * rng.random()
        ob = bl.mesh_object(f"Spark {i}", [
            (r, 0, 0), (-r, 0, 0), (0, r, 0), (0, -r, 0), (0, 0, r), (0, 0, -r)],
            [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
             (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)], m, smooth=False)
        objs.append(ob)
    return objs


def animate_sparks(objs, start, end):
    import random
    rng = random.Random(31)
    frames = list(range(start, end + 1))
    for i, ob in enumerate(objs):
        v = Vector((rng.uniform(-3.4, 3.4), rng.uniform(-0.6, 3.4), rng.uniform(-2.6, 1.9)))
        p0 = Vector((rng.uniform(-0.5, 0.5), world.CORRIDOR.y - rng.uniform(3.6, 5.6),
                     rng.uniform(0.4, 2.3)))
        t0 = rng.uniform(0, 0.6)
        locs = []
        for f in frames:
            t = (f - start) / 30.0 - t0
            if t < 0:
                locs.append(p0 + Vector((0, 0, -8)))
            else:
                locs.append(p0 + v * t + Vector((0, 0, -0.5 * 9.8 * t * t)))
        bl.bake_vector(ob, "location", frames, locs)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(BUILD / "chaos04.blend"))
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--samples", type=int, default=24)
    parser.add_argument("--device", default="CPU", choices=["CPU", "GPU"])
    parser.add_argument("--no-haze", action="store_true")
    parser.add_argument("--preview", action="store_true", help="360x640, 8 samples")
    args = parser.parse_args(argv)

    if args.preview:
        args.width, args.height, args.samples = 360, 640, 8

    scene = bpy.context.scene
    clean_scene()
    configure(scene, args.width, args.height, args.samples, args.device)

    world.atmosphere_world(0.030, "#0A1216")
    world.room(world.ROOM, haze=not args.no_haze)
    world.corridor(world.CORRIDOR)
    world.white_void(world.VOID)
    world.endcard_set(world.ENDCARD)
    gate = world.frame_gate(world.ROOM)
    emblem = world.emblem_plane()
    word = world.wordmark_plane()
    lights = world.room_lights(world.ROOM)
    # corridor / void / endcard lights live in their own data blocks; look them up by name
    for i in range(5):
        ob = bpy.data.objects.get(f"Corridor light {i}")
        if ob:
            lights[f"corr{i}"] = ob
    vk = bpy.data.objects.get("Void key")
    if vk:
        lights["void_key"] = vk
    ef = bpy.data.objects.get("Endcard fill")
    if ef:
        lights["endcard_fill"] = ef
    for key, name in (("rack_key", "Room · rack key"), ("floor_pool", "Room · floor pool"),
                      ("corr_fill", "Corridor fill"), ("corr_end", "Corridor end glow")):
        ob = bpy.data.objects.get(name)
        if ob:
            lights[key] = ob

    monarch = character.build_character()
    rig = monarch["rig"]

    brood = build_brood()
    tendrils = build_tendrils()
    sparks = build_sparks()

    hide_by_segment(brood, "brood")
    hide_by_segment(tendrils, "tendril")
    hide_by_segment(sparks, "sparks")
    animate_sparks(sparks, direct.F(24.40), direct.F(25.50))

    # the frame gate only exists for shots 17 and 19
    for ob in gate:
        frames = [s["start"] for s in direct.SEGMENTS] + [1333]
        hidden = [0.0 if s["id"] in {"17", "19"} else 1.0 for s in direct.SEGMENTS] + [1.0]
        bl.bake_curve(ob, "hide_render", 0, frames, hidden, "CONSTANT")
        bl.bake_curve(ob, "hide_viewport", 0, frames, hidden, "CONSTANT")

    for ob in (emblem, word):
        frames = [s["start"] for s in direct.SEGMENTS] + [1333]
        wanted = "23" if ob is emblem else "24"
        hidden = [0.0 if s["id"] == wanted else 1.0 for s in direct.SEGMENTS] + [1.0]
        bl.bake_curve(ob, "hide_render", 0, frames, hidden, "CONSTANT")
        bl.bake_curve(ob, "hide_viewport", 0, frames, hidden, "CONSTANT")

    bake_character(scene, rig)
    bake_lights(scene, lights)
    bake_exposure(scene)
    bake_world(scene)
    camera.make_cameras(scene)
    compositor(scene)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    manifest = dict(
        blend=str(out), frames=1332, fps=30, width=args.width, height=args.height,
        samples=args.samples, device=args.device,
        segments=[dict(id=s["id"], start=s["start"], end=s["end"], name=s["name"])
                  for s in direct.SEGMENTS],
        character=dict(source="characters/monarch/character.json", state="LOCKED",
                       face="v5 projected", rig_bones=len(character.BONES)),
        assets=sorted(p.name for p in (Path(character.__file__).parent / "assets").iterdir()),
    )
    (out.with_suffix(".manifest.json")).write_text(json.dumps(manifest, indent=1))
    print("BUILD OK", json.dumps(manifest["segments"][:3]))
    print("SAVED", out, out.stat().st_size)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv)
