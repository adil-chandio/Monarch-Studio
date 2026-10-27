"""Head study: is the v5 capture actually on the face, and does it read at size?

Renders the head from a few distances/angles with a clean key, prints the shader
links so a broken projection is diagnosable from the log, not guessed at.

    python gpu/jobs/headtest.py -- --blend build/chaos04.blend --out render/head
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import bpy
from mathutils import Euler, Vector

HEAD = Vector((0.0, 2.47, 1.640))     # measured: shot 05 places him at y≈2.48
VIEWS = [
    ("front_wide", 1.15, 0.0, 0.0, 58),
    ("front_mid", 0.72, 0.0, 0.0, 72),
    ("three_quarter", 0.70, 42.0, 0.0, 72),
    ("profile", 0.70, 88.0, 0.0, 72),
    ("front_35mm", 1.90, 0.0, 0.0, 35),
]


def report_material():
    out = {}
    for name in ("MONARCH skin · v5 projected", "MONARCH skin"):
        m = bpy.data.materials.get(name)
        if not m:
            continue
        nodes = [(n.name, n.bl_idname) for n in m.node_tree.nodes]
        links = [(l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name)
                 for l in m.node_tree.links]
        images = [i.name for i in bpy.data.images if i.name.lower().endswith(".png")]
        out[name] = dict(nodes=nodes, links=links, images=images)
    head = bpy.data.objects.get("HEAD · Monarch v5")
    if head:
        me = head.data
        out["head"] = dict(
            verts=len(me.vertices), polys=len(me.polygons),
            mats=[m.name if m else None for m in me.materials],
            front_polys=sum(1 for p in me.polygons if p.material_index == 1),
            uv_layers=[u.name for u in me.uv_layers],
        )
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", default="build/chaos04.blend")
    ap.add_argument("--out", default="render/head")
    ap.add_argument("--width", type=int, default=360)
    ap.add_argument("--height", type=int, default=640)
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--frame", type=int, default=250,
                    help="Monarch only exists inside his segments; 250 = shot 05")
    args = ap.parse_args(argv)

    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=str(Path(args.blend).resolve()))
    diag = report_material()
    print("SHADERS " + json.dumps(diag)[:1200], flush=True)
    Path(args.out).mkdir(parents=True, exist_ok=True)
    (Path(args.out) / "report.json").write_text(json.dumps(diag, indent=1))

    scene = bpy.context.scene
    scene.frame_set(args.frame)      # his root/bones are baked per frame, incl. the hide
    scene.cycles.samples = args.samples
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # a clean, neutral key so the capture can be judged without the film grade
    key = bpy.data.lights.new("HeadTest key", "AREA")
    key.energy = 55
    key.size = 1.6
    key.color = (1.0, 0.97, 0.94)
    key_ob = bpy.data.objects.new("HeadTest key", key)
    bpy.context.collection.objects.link(key_ob)

    cam_data = bpy.data.cameras.new("HeadTest cam")
    cam_data.sensor_width = 36.0
    cam_data.dof.use_dof = False
    cam = bpy.data.objects.new("HeadTest cam", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    scene.view_settings.exposure = 0.0

    for name, dist, yaw, pitch, lens in VIEWS:
        a = math.radians(yaw)
        pos = HEAD + Vector((math.sin(a) * dist, -math.cos(a) * dist, 0.02))
        cam.location = pos
        cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (HEAD - pos).to_track_quat("-Z", "Y")
        cam_data.lens = lens
        key_ob.location = pos + Vector((0.5, 0, 0.45))
        key_ob.rotation_euler = (HEAD - key_ob.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print("HEAD", name, (out / f"{name}.png").stat().st_size, flush=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(argv)
