"""Small, boring Blender helpers. No scene knowledge lives here."""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

from .mathx import TAU, ease, ease_io, lerp, smoothstep, vlerp, wobble


# ---------------------------------------------------------------- colour
def srgb(hexstr: str, a: float = 1.0):
    h = hexstr.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (lin[0], lin[1], lin[2], a)


# ---------------------------------------------------------------- materials
def material(name, base="#808080", rough=0.5, metal=0.0, spec=0.5, sheen=0.0,
             alpha=1.0, emit=None, emit_strength=0.0, coat=0.0, sss=0.0,
             sss_radius=(0.9, 0.35, 0.2), sss_scale=0.002, ior=1.45):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    p = n.get("Principled BSDF")
    p.inputs["Base Color"].default_value = srgb(base)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["IOR"].default_value = ior
    for key, val in (("Specular IOR Level", spec), ("Sheen Weight", sheen),
                     ("Coat Weight", coat), ("Alpha", alpha),
                     ("Subsurface Weight", sss)):
        if key in p.inputs:
            p.inputs[key].default_value = val
    if sss:
        p.inputs["Subsurface Radius"].default_value = sss_radius
        p.inputs["Subsurface Scale"].default_value = sss_scale
    if emit is not None:
        p.inputs["Emission Color"].default_value = srgb(emit)
        p.inputs["Emission Strength"].default_value = emit_strength
    if alpha < 1.0:
        for attr, val in (("blend_method", "BLEND"), ("shadow_method", "NONE"),
                          ("surface_render_method", "BLENDED")):
            if hasattr(m, attr):
                try:
                    setattr(m, attr, val)
                except Exception:
                    pass
    m.diffuse_color = srgb(base)
    return m


def emission_material(name, color="#ffffff", strength=5.0):
    return material(name, base=color, rough=1.0, spec=0.0, emit=color,
                    emit_strength=strength)


def image_texture(material_obj, path: Path, alpha_socket=False):
    """Image → Base Color on an existing principled material."""
    n = material_obj.node_tree.nodes
    l = material_obj.node_tree.links
    p = n.get("Principled BSDF")
    tex = n.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(path))
    tex.image.pack()
    tex.extension = "CLIP"
    tex.interpolation = "Linear"
    tex.location = (-520, 260)
    l.new(tex.outputs["Color"], p.inputs["Base Color"])
    if alpha_socket:
        l.new(tex.outputs["Alpha"], p.inputs["Alpha"])
    return tex


def facing_mix(material_obj, image_path, skin_hex, front=0.62, fade=0.16):
    """Photo capture on the front of a head, modelled skin at grazing angles.

    Layer Weight "Facing" is 1 straight on and 0 at the silhouette, so the seam
    never lands on a hard edge: it dissolves over the temples and jaw.
    """
    m = material_obj
    n = m.node_tree.nodes
    l = m.node_tree.links
    p = n.get("Principled BSDF")
    tex = n.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(image_path))
    tex.image.pack()
    tex.extension = "EXTEND"
    tex.interpolation = "Linear"
    tex.location = (-900, 260)

    mix = n.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs[1].default_value = srgb(skin_hex)
    mix.label = "skin ↔ capture"
    mix.location = (-560, 300)
    l.new(tex.outputs["Color"], mix.inputs[2])

    lw = n.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.45
    lw.location = (-900, -60)
    ramp = n.new("ShaderNodeValToRGB")
    ramp.location = (-700, -60)
    ramp.color_ramp.elements[0].position = max(0.0, front - fade)
    ramp.color_ramp.elements[1].position = min(1.0, front + fade)
    l.new(lw.outputs["Facing"], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], mix.inputs[0])
    l.new(mix.outputs[0], p.inputs["Base Color"])
    return tex


def bump_material(material_obj, scale=900.0, strength=0.35, detail=2.0):
    n = material_obj.node_tree.nodes
    l = material_obj.node_tree.links
    p = n.get("Principled BSDF")
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = detail
    noise.inputs["Roughness"].default_value = 0.55
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    l.new(noise.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], p.inputs["Normal"])
    return noise


# ---------------------------------------------------------------- objects
def mesh_object(name, verts, faces, mat=None, smooth=True, subsurf=0,
                shade_angle=None, recalc=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector(v) for v in verts], [], [list(f) for f in faces])
    me.validate(verbose=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if smooth:
        for poly in me.polygons:
            poly.use_smooth = True
    if mat is not None:
        ob.data.materials.append(mat)
    if subsurf:
        mod = ob.modifiers.new("Subdivision", "SUBSURF")
        mod.levels = subsurf
        mod.render_levels = subsurf
    if shade_angle is not None:
        try:
            with bpy.context.temp_override(active_object=ob, selected_editable_objects=[ob]):
                bpy.ops.object.shade_smooth_by_angle(angle=shade_angle)
        except Exception:
            pass
    return ob


def loft_rings(rings, close_start=True, close_end=True):
    """rings: [(center(x,y,z), rx, ry, [rot_z])] → verts, faces tube."""
    verts, faces, seg = [], [], 24
    for ring in rings:
        c = Vector(ring[0])
        rx, ry = ring[1], ring[2]
        rot = ring[3] if len(ring) > 3 else 0.0
        squash = ring[4] if len(ring) > 4 else 1.0
        for j in range(seg):
            a = TAU * j / seg
            x = math.cos(a) * rx
            y = math.sin(a) * ry
            # squash: flatter front (−Y) for torsos / faces
            if squash != 1.0 and y < 0:
                y *= squash
            verts.append((c.x + x * math.cos(rot) - y * math.sin(rot),
                          c.y + x * math.sin(rot) + y * math.cos(rot),
                          c.z))
    for i in range(len(rings) - 1):
        for j in range(seg):
            a = i * seg + j
            b = i * seg + (j + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    if close_start:
        c0 = Vector(rings[0][0])
        verts.append(tuple(c0))
        for j in range(seg):
            faces.append((len(verts) - 1, (j + 1) % seg, j))
    if close_end:
        base = (len(rings) - 1) * seg
        verts.append(tuple(Vector(rings[-1][0])))
        for j in range(seg):
            faces.append((len(verts) - 1, base + j, base + (j + 1) % seg))
    return verts, faces


def loft(name, rings, mat, subsurf=1, **kw):
    v, f = loft_rings(rings, kw.pop("close_start", True), kw.pop("close_end", True))
    return mesh_object(name, v, f, mat, subsurf=subsurf, **kw)


def box(name, center, size, mat, rot=(0, 0, 0), bevel=0.0, seg=2):
    cx, cy, cz = center
    sx, sy, sz = (s / 2 for s in size)
    v = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
         (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2),
         (2, 6, 7, 3), (3, 7, 4, 0)]
    ob = mesh_object(name, v, f, mat, smooth=False)
    ob.location = center
    ob.rotation_euler = Euler(rot)
    if bevel:
        m = ob.modifiers.new("Bevel", "BEVEL")
        m.width = bevel
        m.segments = seg
        m.harden_normals = True
        ob.data.polygons.foreach_set("use_smooth", [True] * len(ob.data.polygons))
    return ob


def plane(name, center, size, mat, rot=(0, 0, 0)):
    sx, sy = size[0] / 2, size[1] / 2
    v = [(-sx, -sy, 0), (sx, -sy, 0), (sx, sy, 0), (-sx, sy, 0)]
    ob = mesh_object(name, v, [(0, 1, 2, 3)], mat, smooth=False)
    ob.location = center
    ob.rotation_euler = Euler(rot)
    return ob


def tube_path(name, points, radius, mat, sides=6, taper=1.0):
    """Thin swept tube through points (hair strands, cables)."""
    pts = [Vector(p) for p in points]
    verts, faces = [], []
    for i, p in enumerate(pts):
        if i == 0:
            d = (pts[1] - pts[0])
        elif i == len(pts) - 1:
            d = (pts[-1] - pts[-2])
        else:
            d = (pts[i + 1] - pts[i - 1])
        d.normalize()
        up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        side = d.cross(up).normalized()
        up2 = side.cross(d).normalized()
        r = radius * (1.0 - (1.0 - taper) * i / max(1, len(pts) - 1))
        for j in range(sides):
            a = TAU * j / sides
            verts.append(tuple(p + side * math.cos(a) * r + up2 * math.sin(a) * r))
    for i in range(len(pts) - 1):
        for j in range(sides):
            a = i * sides + j
            b = i * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    return mesh_object(name, verts, faces, mat, smooth=True)


def strands(name, lines, radius, mat, sides=4):
    verts, faces = [], []
    for line in lines:
        pts = [Vector(p) for p in line]
        start = len(verts)
        for i, p in enumerate(pts):
            if i == 0:
                d = pts[1] - pts[0]
            elif i == len(pts) - 1:
                d = pts[-1] - pts[-2]
            else:
                d = pts[i + 1] - pts[i - 1]
            d.normalize()
            up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0))
            side = d.cross(up).normalized()
            up2 = side.cross(d).normalized()
            for j in range(sides):
                a = TAU * j / sides
                verts.append(tuple(p + side * math.cos(a) * radius + up2 * math.sin(a) * radius))
        for i in range(len(pts) - 1):
            for j in range(sides):
                a = start + i * sides + j
                b = start + i * sides + (j + 1) % sides
                faces.append((a, b, b + sides, a + sides))
    return mesh_object(name, verts, faces, mat, smooth=True)


# ---------------------------------------------------------------- rigging
def ensure_armature(name, bones):
    """bones: [(name, head, tail, parent, connect)] → armature object, in rest pose."""
    arm = bpy.data.armatures.new(name + " data")
    ob = bpy.data.objects.new(name, arm)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    _mode_set(ob, "EDIT")
    created = {}
    for bname, head, tail, parent, connect in bones:
        eb = arm.edit_bones.new(bname)
        eb.head = Vector(head)
        eb.tail = Vector(tail)
        eb.roll = 0.0
        if parent:
            eb.parent = created[parent]
            eb.use_connect = bool(connect)
        created[bname] = eb
    _mode_set(ob, "OBJECT")
    for pb in ob.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return ob


def _mode_set(ob, mode):
    try:
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode=mode)
    except Exception:
        with bpy.context.temp_override(active_object=ob, object=ob,
                                       selected_objects=[ob],
                                       selected_editable_objects=[ob]):
            bpy.ops.object.mode_set(mode=mode)


def bind(obj, rig, groups):
    """groups: {bone: weight_or_callable(co)->float} — rigid or per-vertex skinning."""
    for bone, w in groups.items():
        vg = obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
        if callable(w):
            for v in obj.data.vertices:
                weight = w(v.co)
                if weight > 1e-4:
                    vg.add([v.index], min(1.0, weight), "REPLACE")
        else:
            vg.add([v.index for v in obj.data.vertices], float(w), "REPLACE")
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    mod.use_vertex_groups = True
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    return obj


def ramp_weights(stops, axis=2, softness=1.0):
    """Weight ramp along one axis. stops: [(coord, bone)] ascending.

    Returns a dict {bone: callable(co)->weight} that sums to 1 at every vertex,
    so a torso bends smoothly instead of shearing at a joint.
    """
    stops = sorted(stops, key=lambda s: s[0])

    def attr(co):
        return co[axis]

    def make(i):
        bone = stops[i][1]

        def w(co):
            x = attr(co)
            if i == 0 and x <= stops[0][0]:
                return 1.0
            if i == len(stops) - 1 and x >= stops[-1][0]:
                return 1.0
            lo = stops[i][0]
            hi = stops[i + 1][0] if i + 1 < len(stops) else lo
            prev = stops[i - 1][0] if i > 0 else lo
            val = 0.0
            if lo <= x <= hi and hi > lo:
                val = max(val, 1.0 - (x - lo) / (hi - lo))
            if prev <= x <= lo and lo > prev:
                val = max(val, 1.0 - (lo - x) / (lo - prev))
            if abs(x - lo) < 1e-9:
                val = 1.0
            return val ** (1.0 / max(0.05, softness))

        return w

    # several stops can name the same bone (a limb's shoulder and elbow overlap);
    # their weights add up so every vertex still sums to ~1
    groups = {}
    for i, (_coord, bone) in enumerate(stops):
        groups.setdefault(bone, []).append(make(i))

    def merged(fns):
        def w(co):
            return sum(f(co) for f in fns)
        return w

    return {bone: merged(fns) for bone, fns in groups.items()}



# ---------------------------------------------------------------- animation
def bake_curve(id_data, path, index, frames, values, interp="LINEAR"):
    ad = id_data.animation_data or id_data.animation_data_create()
    if ad.action is None:
        ad.action = bpy.data.actions.new((id_data.name or "id") + " action")
    action = ad.action
    fcu = action.fcurves.find(path, index=index)
    if fcu:
        action.fcurves.remove(fcu)
    fcu = action.fcurves.new(path, index=index)
    fcu.keyframe_points.add(len(frames))
    flat = []
    for f, v in zip(frames, values):
        flat.extend((float(f), float(v)))
    fcu.keyframe_points.foreach_set("co", flat)
    for kp in fcu.keyframe_points:
        kp.interpolation = interp
    fcu.update()
    return fcu


def bake_vector(id_data, path, frames, vectors, interp="LINEAR"):
    for i in range(len(vectors[0])):
        bake_curve(id_data, path, i, frames, [v[i] for v in vectors], interp)


def bake_quats(rig, frames, poses, interp="LINEAR"):
    """poses: {bone: [Quaternion or None per frame]}"""
    for bone, quats in poses.items():
        path = f'pose.bones["{bone}"].rotation_quaternion'
        for i in range(4):
            vals = [(q[i] if q is not None else (1.0 if i == 0 else 0.0)) for q in quats]
            bake_curve(rig, path, i, frames, vals, interp)


def bake_locs(rig, frames, locs, interp="LINEAR"):
    for bone, vecs in locs.items():
        path = f'pose.bones["{bone}"].location'
        for i in range(3):
            bake_curve(rig, path, i, frames, [v[i] for v in vecs], interp)
