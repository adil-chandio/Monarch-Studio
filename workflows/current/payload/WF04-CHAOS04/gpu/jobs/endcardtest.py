"""Endcard check: are the emblem and wordmark actually visible, and why not."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
blend = argv[0] if argv else "build/chaos04.blend"
bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()))
scene = bpy.context.scene
scene.cycles.samples = 12
out = Path("render/endcard")
out.mkdir(parents=True, exist_ok=True)

report = {}
for name in ("Monarch emblem", "Monarch wordmark", "Endcard backdrop"):
    ob = bpy.data.objects.get(name)
    if not ob:
        report[name] = "MISSING"
        continue
    mats = [m.name for m in ob.data.materials]
    m = ob.data.materials[0] if ob.data.materials else None
    links = {}
    if m:
        for l in m.node_tree.links:
            links[f"{l.from_node.name}.{l.from_socket.name}"] = f"{l.to_node.name}.{l.to_socket.name}"
        em = m.node_tree.nodes.get("Principled BSDF")
        links["emission_strength"] = em.inputs["Emission Strength"].default_value if em else None
        links["emission_color"] = tuple(em.inputs["Emission Color"].default_value)[:3] if em else None
        links["base_alpha"] = em.inputs["Alpha"].default_value if em else None
    report[name] = dict(loc=tuple(round(v, 3) for v in ob.location),
                        rot=tuple(round(v, 3) for v in ob.rotation_euler),
                        mats=mats, links=links)

for f in (1220, 1240, 1300, 1332):
    scene.frame_set(f)
    vis = {n: (bpy.data.objects[n].hide_render if bpy.data.objects.get(n) else None)
           for n in ("Monarch emblem", "Monarch wordmark")}
    scene.render.filepath = str(out / f"f{f:04d}.png")
    bpy.ops.render.render(write_still=True)
    report[f"frame {f}"] = vis

(out / "report.json").write_text(json.dumps(report, indent=1))
print("ENDCARD " + json.dumps(report)[:1500])
