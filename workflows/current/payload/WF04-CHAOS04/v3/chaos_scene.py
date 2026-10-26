#!/usr/bin/env python3
"""
CHAOS · NEXT FILM — v3 true-3D scene builder + renderer.

Everything in frame is generated here by code: set, character, mask, lights,
cameras, animation. No downloaded asset, no reference pixel, no image plate.

Usage (bpy needs the GL stub path):
  LD_LIBRARY_PATH=/home/user/.runtime/xstub python3 v3/chaos_scene.py \
      --shots 0:6 --res 405x720 --samples 12 --out v3/render/animatic

Frames already on disk are skipped, so the render is resumable.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector, Euler

HERE = Path(__file__).resolve().parent
PAYLOAD = HERE.parent
SHOTLIST = HERE / "SHOTLIST_3D.json"
FPS = 30

# ----------------------------------------------------------------- helpers ---


def _new_mesh(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def box(name, center, size, mat, rot=None):
    cx, cy, cz = center
    sx, sy, sz = (s / 2 for s in size)
    v = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
         (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    ob = _new_mesh(name, v, f, mat)
    ob.location = (cx, cy, cz)
    if rot:
        ob.rotation_euler = rot
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


def sphere(name, center, radius, mat, segs=24, rings=14, scale=(1, 1, 1)):
    v, f = [], []
    for i in range(rings + 1):
        th = math.pi * i / rings
        for j in range(segs):
            ph = 2 * math.pi * j / segs
            v.append((radius * math.sin(th) * math.cos(ph) * scale[0],
                      radius * math.sin(th) * math.sin(ph) * scale[1],
                      radius * math.cos(th) * scale[2]))
    for i in range(rings):
        for j in range(segs):
            a = i * segs + j
            b = i * segs + (j + 1) % segs
            c = (i + 1) * segs + (j + 1) % segs
            d = (i + 1) * segs + j
            f.append((a, b, c, d))
    ob = _new_mesh(name, v, f, mat)
    ob.location = center
    return ob


def frustum(name, p0, p1, r0, r1, mat, segs=18, cap=True):
    """Tapered tube between two points (a limb / torso / coat)."""
    a, b = Vector(p0), Vector(p1)
    axis = (b - a)
    L = axis.length
    if L < 1e-6:
        L = 1e-6
    z = axis.normalized()
    ref = Vector((0, 0, 1)) if abs(z.z) < 0.9 else Vector((1, 0, 0))
    x = z.cross(ref).normalized()
    y = z.cross(x).normalized()
    verts, faces = [], []
    for k, (p, r) in enumerate(((a, r0), (b, r1))):
        for j in range(segs):
            ph = 2 * math.pi * j / segs
            verts.append(tuple(p + x * (r * math.cos(ph)) + y * (r * math.sin(ph))))
    for j in range(segs):
        jn = (j + 1) % segs
        faces.append((j, jn, segs + jn, segs + j))
    if cap:
        verts.append(tuple(a))
        verts.append(tuple(b))
        ca, cb = len(verts) - 2, len(verts) - 1
        for j in range(segs):
            jn = (j + 1) % segs
            faces.append((ca, jn, j))
            faces.append((cb, segs + j, segs + jn))
    return _new_mesh(name, verts, faces, mat)


def torus(name, center, R, r, mat, segs=28, rings=10, rot=None, arc=(0.0, 2 * math.pi)):
    a0, a1 = arc
    verts, faces = [], []
    closed = abs((a1 - a0) - 2 * math.pi) < 1e-6
    n = segs if closed else segs + 1
    for i in range(n):
        a = a0 + (a1 - a0) * (i / segs)
        ca, sa = math.cos(a), math.sin(a)
        for j in range(rings):
            b = 2 * math.pi * j / rings
            rr = R + r * math.cos(b)
            verts.append((rr * ca, rr * sa, r * math.sin(b)))
    for i in range(n if closed else n - 1):
        inx = (i + 1) % n
        for j in range(rings):
            jn = (j + 1) % rings
            faces.append((i * rings + j, inx * rings + j, inx * rings + jn, i * rings + jn))
    ob = _new_mesh(name, verts, faces, mat)
    ob.location = center
    if rot:
        ob.rotation_euler = rot
    return ob


def crescent(name, center, R, tube, mat, a0=math.radians(-62), a1=math.radians(62),
             segs=44, rings=10, taper=0.6, bulge=1.0, bow=0.0):
    """Glowing visor band: arc on a horizontal circle around the head, tapered tube.
    Angle 0 = straight ahead (-Y). Thick middle, sharp tips => crescent read."""
    verts, faces = [], []
    for i in range(segs + 1):
        t = i / segs
        a = a0 + (a1 - a0) * t
        r = tube * (math.sin(math.pi * t) ** taper)
        ca, sa = math.cos(a), math.sin(a)
        P = Vector((R * sa, -R * ca * bulge, bow * (1.0 - ca)))
        N = Vector((sa, -ca, 0.0))          # outward normal
        B = Vector((0.0, 0.0, 1.0))         # up
        for j in range(rings):
            b = 2 * math.pi * j / rings
            q = P + N * (r * math.cos(b)) + B * (r * math.sin(b))
            verts.append((q.x, q.y, q.z))
    for i in range(segs):
        for j in range(rings):
            jn = (j + 1) % rings
            faces.append((i * rings + j, (i + 1) * rings + j,
                          (i + 1) * rings + jn, i * rings + jn))
    ob = _new_mesh(name, verts, faces, mat)
    ob.location = center
    return ob


# ---------------------------------------------------------------- materials ---


def mat_basic(name, base=(0.02, 0.02, 0.02), rough=0.4, metal=0.0, emission=None,
              strength=0.0, sheen=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    for key, val in (("Sheen Weight", sheen), ("Coat Weight", coat)):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = val
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    return m


def mat_brick(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    coord = nt.nodes.new("ShaderNodeTexCoord")
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 9.0
    brick.inputs["Mortar Size"].default_value = 0.018
    brick.inputs["Color1"].default_value = (0.055, 0.028, 0.022, 1)
    brick.inputs["Color2"].default_value = (0.030, 0.016, 0.014, 1)
    brick.inputs["Mortar"].default_value = (0.012, 0.012, 0.013, 1)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 40.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.65
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    nt.links.new(coord.outputs["Object"], brick.inputs["Vector"])
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bump.inputs["Height"])
    nt.links.new(brick.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.85
    return m


def mat_floor(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6.0
    noise.inputs["Detail"].default_value = 6.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[0].color = (0.02, 0.021, 0.024, 1)
    ramp.color_ramp.elements[1].color = (0.006, 0.006, 0.008, 1)
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs["From Min"].default_value = 0.0
    rough.inputs["From Max"].default_value = 1.0
    rough.inputs["To Min"].default_value = 0.08
    rough.inputs["To Max"].default_value = 0.42
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(noise.outputs["Fac"], rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    bsdf.inputs["Metallic"].default_value = 0.55
    return m


# ------------------------------------------------------------------- scene ---

S = dict()  # scene registry


def look_at(cam, pos, target, roll=0.0):
    cam.location = Vector(pos)
    d = (Vector(target) - Vector(pos))
    if d.length < 1e-6:
        d = Vector((0, 1, 0))
    rot = d.to_track_quat("-Z", "Y").to_euler()
    rot.rotate_axis("Z", roll)
    cam.rotation_euler = rot


def build():
    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 1
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast" if "AgX - Medium High Contrast" in [
        l.name for l in sc.view_settings.bl_rna.properties["look"].enum_items] else "None"
    sc.view_settings.exposure = 0.0
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    sc.render.image_settings.compression = 15

    # ---- world: near-total darkness with a cold ambient whisper
    world = bpy.data.worlds.new("chaos_world") if not bpy.data.worlds else bpy.data.worlds[0]
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.008, 0.010, 0.016, 1)
    bg.inputs["Strength"].default_value = 0.30

    M = S["M"] = dict(
        floor=mat_floor("mat_floor"),
        brick=mat_brick("mat_brick"),
        brick_plain=mat_basic("mat_wall", (0.030, 0.026, 0.028), 0.9),
        concrete=mat_basic("mat_conc", (0.028, 0.028, 0.030), 0.75),
        metal=mat_basic("mat_metal", (0.045, 0.045, 0.05), 0.32, 1.0),
        darkmetal=mat_basic("mat_darkmetal", (0.0085, 0.0085, 0.0105), 0.74, 0.18),
        coat=mat_basic("mat_coat", (0.0050, 0.0052, 0.0072), 0.60, 0.02, sheen=0.22, coat=0.05),
        cloth=mat_basic("mat_cloth", (0.020, 0.020, 0.024), 0.72),
        skin_shadow=mat_basic("mat_shadow", (0.008, 0.007, 0.007), 0.55),
        tie=mat_basic("mat_tie", (0.085, 0.008, 0.010), 0.52, 0.0, sheen=0.35),
        visor=mat_basic("mat_visor", (0.05, 0.005, 0.004), 0.15, 0.0,
                        emission=(1.0, 0.085, 0.030), strength=3.8),
        visor_hot=mat_basic("mat_visor_hot", (0.05, 0.005, 0.004), 0.1, 0.0,
                            emission=(1.0, 0.72, 0.52), strength=6.0),
        portal=mat_basic("mat_portal", (0.02, 0.0, 0.0), 0.5, 0.0,
                         emission=(1.0, 0.055, 0.03), strength=5.0),
        lamp=mat_basic("mat_lamp", (0.02, 0.02, 0.02), 0.4, 0.0,
                       emission=(1.0, 0.55, 0.26), strength=12.0),
        blade=mat_basic("mat_blade", (0.32, 0.32, 0.34), 0.12, 1.0),
        blade_edge=mat_basic("mat_blade_edge", (0.05, 0.0, 0.0), 0.2, 0.0,
                             emission=(1.0, 0.20, 0.10), strength=26.0),
        chain=mat_basic("mat_chain", (0.06, 0.055, 0.05), 0.42, 0.95),
    )

    # ---- set: industrial hall (our build, 24 x 9 x 34 m)
    box("floor", (0, 0, 0), (26, 34, 0.2), M["floor"])
    back = box("wall_far", (0, 17, 5), (26, 0.4, 12), M["brick"])
    back.rotation_euler = (0, 0, 0)
    box("wall_right", (13, 0, 5), (0.4, 34, 12), M["concrete"])
    box("wall_left", (-13, 0, 5), (0.4, 34, 12), M["concrete"])
    box("ceiling", (0, 0, 10.2), (26, 34, 0.4), M["concrete"])

    # brick pillars + steel beams for silhouette depth
    for x in (-8.5, -4.2, 4.2, 8.5):
        box(f"pillar_{x}", (x, 12.5, 5), (0.9, 0.9, 10), M["brick"])
    for y in (-6, 2, 10):
        box(f"beam_{y}", (0, y, 9.4), (26, 0.35, 0.5), M["darkmetal"])
    for x in (-9, -3, 3, 9):
        for y in (-4, 4, 12):
            frustum(f"pipe_{x}_{y}", (x, y, 10), (x, y, 7.4), 0.09, 0.09, M["metal"], 10)

    # hanging chains
    for i, (x, y) in enumerate([(-6.2, 8.5), (-2.4, 6.0), (2.6, 7.4), (6.0, 9.2), (-0.6, 11.0)]):
        top = 9.2
        for k in range(7):
            z = top - 0.42 * k
            torus(f"chain_{i}_{k}", (x, y, z), 0.10, 0.022, M["chain"], 12, 6,
                  rot=(math.radians(90) if k % 2 else 0, 0, 0))
        frustum(f"chain_hook_{i}", (x, y, top - 3.0), (x, y, top - 3.55), 0.05, 0.02, M["chain"], 8)

    # lamps
    S["lamps"] = []
    for i, (x, y) in enumerate([(-5.0, 4.0), (5.0, 2.0), (0.0, 9.0)]):
        frustum(f"lampcord_{i}", (x, y, 10.0), (x, y, 7.6), 0.02, 0.02, M["darkmetal"], 6)
        shade = frustum(f"lampshade_{i}", (x, y, 7.6), (x, y, 7.15), 0.34, 0.10, M["darkmetal"], 16)
        disc = torus(f"lampglow_{i}", (x, y, 7.16), 0.10, 0.05, M["lamp"], 14, 6,
                     rot=(0, 0, 0))
        S["lamps"].append(disc)

    # ---- doorway + red portal (the reference's red practical, rebuilt)
    dw = S["door"] = {}
    box("door_frame_l", (-1.35, 14.6, 1.7), (0.28, 0.5, 3.4), M["darkmetal"])
    box("door_frame_r", (1.35, 14.6, 1.7), (0.28, 0.5, 3.4), M["darkmetal"])
    box("door_frame_t", (0, 14.6, 3.35), (3.0, 0.5, 0.30), M["darkmetal"])
    portal = box("portal_glow", (0, 15.6, 1.7), (2.4, 0.1, 3.1), M["portal"])
    dw["portal"] = portal
    torus("portal_ring", (0, 15.2, 1.75), 1.05, 0.06, M["visor"], 40, 8,
          rot=(math.radians(90), 0, 0))

    # ---- lights
    def area(name, loc, target, size, energy, color=(1, 1, 1), shape="SQUARE"):
        d = bpy.data.lights.new(name, type="AREA")
        d.shape = shape
        d.size = size
        d.energy = energy
        d.color = color
        ob = bpy.data.objects.new(name, d)
        ob.location = loc
        direction = Vector(target) - Vector(loc)
        ob.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(ob)
        return ob

    HERO_AIM = (0.0, 5.6, 1.45)
    FACE_AIM = (0.0, 5.6, 1.72)
    L = S["L"] = {}
    L["portal"] = area("lt_portal", (0, 13.9, 2.0), (0, 11.6, 0.4), 2.2, 240, (1.0, 0.10, 0.055))
    L["floorpool"] = area("lt_floorpool", (0, 12.2, 0.28), (0, 10.0, 0.0), 2.6, 120, (1.0, 0.13, 0.08))
    L["key"] = area("lt_key", (-2.9, 7.2, 5.2), HERO_AIM, 2.0, 200, (0.50, 0.64, 1.0))
    L["rim"] = area("lt_rim", (2.7, 10.6, 4.3), HERO_AIM, 1.4, 175, (1.0, 0.20, 0.11))
    L["hero_rim"] = area("lt_hero_rim", (0.0, 8.9, 2.45), (0.0, 5.6, 1.6), 1.7, 260,
                         (0.52, 0.70, 1.0))
    L["overhead"] = area("lt_overhead", (0.0, 3.2, 8.4), (0.0, 5.6, 0.4), 2.6, 90, (1.0, 0.62, 0.34))
    L["fill"] = area("lt_fill", (0, -2.4, 3.4), HERO_AIM, 6.0, 42, (0.26, 0.40, 0.78))
    # front 'mask' key: cool, sculpts the visor side of the face
    L["face_key"] = area("lt_face_key", (-1.7, 3.05, 2.45), FACE_AIM, 1.2, 48, (0.68, 0.80, 1.0))
    L["face_kick"] = area("lt_face_kick", (1.5, 3.45, 1.95), FACE_AIM, 1.0, 38, (1.0, 0.34, 0.20))

    # ---- character: OUR masked Monarch (heroic 1.85 m proportions)
    C = {}
    rig = bpy.data.objects.new("hero_root", None)
    sc.collection.objects.link(rig)
    rig.location = HERO_POS
    C["root"] = rig

    def part(ob, sx=1.0, sy=1.0, sz=1.0):
        ob.parent = rig
        ob.scale = (sx, sy, sz)
        return ob

    Z = dict(foot=0.0, knee=0.46, hip=1.00, waist=1.10, chest=1.34,
             shoulder=1.47, neck=1.555, head=1.735, top=1.875)
    # torso volumes (ellipsoids read as tailoring, not as a barrel)
    part(sphere("pelvis", (0, 0, Z["hip"]), 1.0, M["coat"], 26, 16, scale=(0.168, 0.115, 0.135)))
    part(sphere("waist", (0, 0, Z["waist"]), 1.0, M["coat"], 26, 16, scale=(0.142, 0.100, 0.100)))
    part(sphere("chest", (0, -0.006, 1.352), 1.0, M["coat"], 28, 18, scale=(0.184, 0.124, 0.158)))
    part(sphere("upper_back", (0, 0.045, 1.40), 1.0, M["coat"], 24, 14, scale=(0.195, 0.125, 0.135)))
    for side in (-1, 1):
        part(sphere(f"shoulder_{side}", (0.198 * side, 0.010, Z["shoulder"] - 0.005), 1.0, M["coat"],
                    22, 14, scale=(0.078, 0.074, 0.062)))
        part(frustum(f"deltoid_{side}", (0.150 * side, 0.006, Z["shoulder"] + 0.015),
                     (0.232 * side, 0.012, 1.360), 0.070, 0.050, M["coat"], 16))
        # arms: jacket sleeves taper to gloved hands
        part(frustum(f"upperarm_{side}", (0.205 * side, 0.012, Z["shoulder"] - 0.02),
                     (0.238 * side, 0.026, 1.175), 0.062, 0.050, M["coat"], 14))
        part(frustum(f"forearm_{side}", (0.238 * side, 0.026, 1.175),
                     (0.252 * side, 0.076, 0.905), 0.050, 0.040, M["coat"], 14))
        part(sphere(f"hand_{side}", (0.255 * side, 0.090, 0.872), 0.046, M["skin_shadow"], 14, 10,
                    scale=(1.0, 1.15, 1.25)))
        part(box(f"boot_{side}", (0.108 * side, -0.045, 0.072), (0.115, 0.275, 0.145), M["darkmetal"]))
    # floor-length coat, elliptical section, open front
    skirt = part(frustum("coat_skirt", (0, 0, Z["hip"] + 0.02), (0, 0, 0.055), 0.205, 0.335,
                         M["coat"], 26), 1.0, 0.78, 1.0)
    part(torus("belt", (0, 0, Z["waist"] - 0.03), 0.148, 0.018, M["darkmetal"], 26, 8), 1.0, 0.70, 1.0)
    part(box("coat_closure", (0, -0.121, 1.255), (0.020, 0.012, 0.300), M["cloth"]))
    # shirt V, lapels, tie (sits ON the chest surface, not inside it)
    part(box("shirt_v", (0, -0.128, 1.398), (0.098, 0.022, 0.170), M["cloth"],
             rot=(math.radians(6), 0, 0)))
    for side in (-1, 1):
        part(box(f"lapel_{side}", (0.058 * side, -0.126, 1.392), (0.062, 0.012, 0.195),
                 M["coat"], rot=(math.radians(4), math.radians(11 * side), math.radians(-8 * side))))
    tie = part(box("tie", (0, -0.139, 1.302), (0.042, 0.011, 0.215), M["tie"],
                   rot=(math.radians(-3), 0, 0)))
    C["tie"] = tie
    part(box("tie_knot", (0, -0.136, 1.436), (0.050, 0.018, 0.044), M["tie"],
             rot=(math.radians(12), 0, 0)))
    # our crest on the chest (focal point for chest close-ups)
    part(crescent("crest", (-0.082, -0.118, 1.404), 0.026, 0.0055, M["visor"],
                  a0=math.radians(-100), a1=math.radians(100), segs=28, rings=7, taper=0.45))
    part(frustum("collar", (0, 0.004, Z["neck"] - 0.035), (0, 0.004, Z["neck"] + 0.020),
                 0.070, 0.052, M["coat"], 18))
    part(frustum("neck", (0, 0, Z["neck"] - 0.02), (0, 0, Z["neck"] + 0.075), 0.042, 0.042,
                 M["skin_shadow"], 14))
    # head + mask + crescent visor
    head = part(sphere("head", (0, 0.004, Z["head"]), 1.0, M["coat"], 30, 20,
                       scale=(0.110, 0.116, 0.118)))
    C["head"] = head
    part(sphere("mask_shell", (0, 0.001, Z["head"] + 0.004), 1.0, M["darkmetal"], 28, 18,
                scale=(0.114, 0.121, 0.122)))
    part(sphere("jaw_plate", (0, -0.056, Z["head"] - 0.078), 1.0, M["darkmetal"], 22, 12,
                scale=(0.086, 0.084, 0.055)))
    # dark backing band gives the glow an outline
    visor = part(crescent("visor", (0, 0.001, Z["head"] + 0.016), 0.122, 0.021, M["visor"],
                          a0=math.radians(-70), a1=math.radians(70), segs=48, rings=9, taper=0.55))
    C["visor"] = visor
    part(crescent("visor_glint", (0, 0.001, Z["head"] + 0.019), 0.124, 0.0075, M["visor_hot"],
                  a0=math.radians(-42), a1=math.radians(14), segs=24, rings=6, taper=0.5))
    # brow / temple armour to break the sphere silhouette
    part(crescent("brow_ridge", (0, 0.001, Z["head"] + 0.072), 0.122, 0.011, M["darkmetal"],
                  a0=math.radians(-72), a1=math.radians(72), segs=40, rings=8,
                  taper=0.40, bow=0.014))
    part(crescent("brow_glint", (0, 0.001, Z["head"] + 0.0735), 0.124, 0.0032, M["visor"],
                  a0=math.radians(-48), a1=math.radians(48), segs=32, rings=6,
                  taper=0.5, bow=0.014))
    # blade (hidden until the climax)
    blade = bpy.data.objects.new("blade_root", None)
    sc.collection.objects.link(blade)
    blade.parent = rig
    blade.location = (0.255, 0.090, 0.872)
    b1 = frustum("blade_body", (0, 0, 0), (0, 0, 1.30), 0.026, 0.004, M["blade"], 4, True)
    b1.parent = blade
    b2 = frustum("blade_glow", (0, -0.004, 0.02), (0, -0.004, 1.32), 0.007, 0.0015,
                 M["blade_edge"], 4, True)
    b2.parent = blade
    blade.rotation_euler = (math.radians(-64), 0, 0)
    blade.scale = (0.001, 0.001, 0.001)
    C["blade"] = blade
    C["blade_rot"] = blade.rotation_euler.copy()
    for f, sc_ in ((1, 0.001), (1020, 0.001), (1036, 1.0), (1180, 1.0), (1230, 0.001),
                   (1332, 0.001)):
        blade.scale = (sc_, sc_, sc_)
        blade.keyframe_insert("scale", frame=f)
    for f, rx in ((1, -64), (1020, -64), (1040, -14), (1100, -26), (1180, -18),
                  (1230, -64), (1332, -64)):
        blade.rotation_euler = (math.radians(rx), 0, 0)
        blade.keyframe_insert("rotation_euler", frame=f)
    S["C"] = C
    S["rig"] = rig

    # ---- hero performance (global timeline): breathing, weight shift, tie sway
    rig.rotation_mode = "XYZ"
    for f, (z, ry, rx) in {1: (0.0, 0.0, 0.0), 120: (0.012, 0.02, 0.004),
                           300: (0.004, -0.015, -0.003), 520: (0.010, 0.012, 0.002),
                           760: (0.002, -0.008, 0.0), 1000: (0.014, 0.02, -0.004),
                           1180: (0.004, -0.012, 0.003), 1332: (0.008, 0.0, 0.0)}.items():
        rig.location = (HERO_POS[0], HERO_POS[1], HERO_POS[2] + z)
        rig.keyframe_insert("location", frame=f)
        rig.rotation_euler = (rx, 0, ry)
        rig.keyframe_insert("rotation_euler", frame=f)
    for f, rz in {1: 0.0, 260: math.radians(7), 540: math.radians(-9),
                  820: math.radians(6), 1100: math.radians(-4), 1332: 0.0}.items():
        tie.rotation_euler = (math.radians(-4), 0, rz)
        tie.keyframe_insert("rotation_euler", frame=f)
    # head micro-motion (keeps every shot alive without a rig)
    for f, (rh, rz) in {1: (0, 0), 200: (0.03, 0.05), 430: (-0.02, -0.04),
                        700: (0.025, 0.03), 950: (-0.03, -0.02), 1200: (0.02, 0.04),
                        1332: (0.0, 0.0)}.items():
        head.rotation_euler = (rh, 0, rz)
        head.keyframe_insert("rotation_euler", frame=f)

    # ---- chains + portal pulse (set life)
    for i in range(5):
        for k in range(7):
            ob = bpy.data.objects.get(f"chain_{i}_{k}")
            if not ob:
                continue
            base = ob.rotation_euler.copy()
            for f, sgn in ((1, 0.0), (160 + i * 40, 1.0), (340 + i * 30, -1.0),
                           (560 + i * 20, 0.6), (900, -0.5), (1332, 0.0)):
                ob.rotation_euler = (base.x + sgn * 0.06, base.y, base.z + sgn * 0.05)
                ob.keyframe_insert("rotation_euler", frame=f)
    for m in (M["portal"], M["visor"]):
        for f, s in ((1, 1.0), (300, 1.25), (620, 0.85), (900, 1.35), (1150, 1.1), (1332, 1.0)):
            if f in (1, 300, 620, 900, 1150, 1332):
                pass
        node = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        base = node.default_value
        for f, s in ((1, 1.0), (300, 1.3), (620, 0.8), (900, 1.4), (1150, 1.05), (1332, 1.0)):
            node.default_value = base * s
            node.keyframe_insert("default_value", frame=f)

    # ---- cameras + markers, driven by the shotlist
    S["shot_cam"] = {}
    return S


# ------------------------------------------------------- camera per shot -----

BASE = {
    # setup -> (cam pos, target, lens)   hero stands at (0, 5.6, 0), faces -Y
    # Design rule: the figure is shown as a lit silhouette inside a big dark hall.
    # Detail inserts are environmental (portal ring, chains, blade) — never a
    # low-detail close-up of the character.
    "hall_wide_a": ((0.0, -11.5, 2.05), (0.0, 15.0, 1.95), 26),
    "hall_wide_b": ((-4.2, -8.0, 1.50), (0.6, 14.8, 1.85), 22),
    "doorway_wide": ((0.0, 2.6, 1.30), (0.0, 14.2, 1.80), 34),
    "doorway_hold": ((0.0, 3.4, 1.02), (0.0, 14.6, 1.55), 30),
    "masked_cu_low": ((1.05, 1.15, 0.72), (0.0, 5.60, 1.48), 45),
    "masked_cu_high": ((-1.25, 3.35, 3.70), (0.0, 5.60, 1.30), 40),
    "masked_profile": ((3.75, 5.05, 1.52), (0.0, 5.60, 1.44), 45),
    "tie_detail": ((1.25, 9.20, 4.70), (-2.10, 8.40, 3.90), 62),
    "visor_insert": ((5.60, 9.40, 2.70), (0.0, 14.60, 1.90), 50),
    "climax_blade": ((1.55, 4.05, 0.98), (0.30, 5.60, 1.02), 58),
    "climax_overhead": ((0.50, 4.20, 3.95), (0.0, 5.60, 1.18), 30),
    "climax_strobe": ((1.35, 1.95, 0.48), (0.20, 5.60, 1.58), 50),
    "climax_whip": ((-2.10, 2.90, 6.40), (2.40, 8.20, 3.10), 32),
    "end_card": ((0.0, 3.30, 1.62), (0.0, 5.58, 1.62), 45),
}
HERO_POS = (0.0, 5.6, 0.0)


def make_cameras(shots):
    sc = bpy.context.scene
    for s in shots:
        setup = s["setup"]
        pos, tgt, lens = BASE[setup]
        sdx = (s["seed"] % 1000) / 1000.0 - 0.5
        sdy = ((s["seed"] // 1000) % 1000) / 1000.0 - 0.5
        # small per-shot framing variation so consecutive shots never look identical
        jitter = 0.16 if setup.startswith(("masked", "climax", "tie", "visor")) else 0.05
        pos = (pos[0] + sdx * jitter, pos[1] + sdy * jitter * 0.6, pos[2] + sdy * 0.09)
        tgt = (tgt[0] - sdx * 0.08, tgt[1], tgt[2] + (sdy * 0.05 if setup != "end_card" else 0))
        cam_data = bpy.data.cameras.new(f"cam_{s['shot']}")
        cam_data.lens = lens
        cam_data.sensor_fit = "VERTICAL"
        cam_data.sensor_height = 24.0
        cam_data.clip_start = 0.05
        cam_data.clip_end = 200.0
        cam = bpy.data.objects.new(f"cam_{s['shot']}", cam_data)
        sc.collection.objects.link(cam)
        S["shot_cam"][s["shot"]] = cam

        f0, f1 = s["f0"], s["f1"]
        kind, strength = s["motion"], s["motion_strength"]
        nkeys = 3
        for i in range(nkeys + 1):
            t = i / nkeys
            f = f0 + int((f1 - f0) * t)
            f = min(f, f1 - 1)
            p = list(pos)
            tg = list(tgt)
            amp = strength * jitter
            if kind == "push":
                p[1] -= 0.55 * strength * t
                p[2] += 0.03 * t
            elif kind == "handheld_push":
                p[1] -= 0.30 * strength * t
                p[0] += 0.035 * strength * math.sin(t * 5.1 + s["seed"] % 7)
                p[2] += 0.022 * strength * math.sin(t * 7.7 + s["seed"] % 5)
                tg[1] += 0.02 * math.sin(t * 4.3)
            elif kind == "handheld_pull":
                p[1] += 0.24 * strength * t
                p[0] += 0.03 * strength * math.sin(t * 6.2 + s["seed"] % 9)
                p[2] += 0.018 * strength * math.cos(t * 5.4)
            elif kind == "orbit":
                a = math.radians(-16 * strength * (t - 0.5) * 2)
                dx, dy = p[0] - HERO_POS[0], p[1] - HERO_POS[1]
                p[0] = HERO_POS[0] + dx * math.cos(a) - dy * math.sin(a)
                p[1] = HERO_POS[1] + dx * math.sin(a) + dy * math.cos(a)
            elif kind == "whip":
                p[0] += (t - 0.5) * 2.0 * strength
                p[2] += (t - 0.5) * 0.45 * strength
                tg[0] += (t - 0.5) * 0.55 * strength
            elif kind == "crane":
                p[2] += (0.5 - t) * 1.5 * strength
                p[1] += (t - 0.5) * 0.4
            elif kind == "shake":
                p[0] += 0.05 * strength * math.sin(t * 21 + s["seed"] % 11)
                p[1] += 0.03 * strength * math.cos(t * 17)
                p[2] += 0.04 * strength * math.sin(t * 25 + 1.7)
            elif kind == "drift":
                p[0] += 0.55 * t * (1 if s["seed"] % 2 else -1)
                p[1] -= 0.25 * t
            look_at(cam, p, tg, roll=0.012 * strength * math.sin(t * 3 + s["seed"] % 5))
            cam.keyframe_insert("location", frame=f)
            cam.keyframe_insert("rotation_euler", frame=f)
        # cut marker binds the camera
        mk = sc.timeline_markers.new(s["shot"], frame=f0)
        mk.camera = cam


def apply_act_looks(shots):
    """Exposure + strobe behaviour per act, keyed on the global timeline."""
    sc = bpy.context.scene
    expo = {"A1": -1.20, "A2": -0.70, "A3": -1.05, "A4": -0.85, "A5": -0.85, "A6": -1.9}
    tight = ("visor_insert", "climax_blade", "climax_strobe")
    for s in shots:
        e = expo[s["act"]] - (0.35 if s["setup"].startswith(tight) else 0.0)
        sc.view_settings.exposure = e
        sc.view_settings.keyframe_insert("exposure", frame=s["f0"])

    # climax strobes: visible red burst light that fires on a subset of A5 cuts
    d = bpy.data.lights.new("lt_strobe", type="POINT")
    d.energy = 0.0
    d.color = (1.0, 0.08, 0.05)
    d.shadow_soft_size = 0.6
    ob = bpy.data.objects.new("lt_strobe", d)
    ob.location = (0.0, 5.0, 2.3)
    sc.collection.objects.link(ob)
    a5 = [s for s in shots if s["act"] == "A5"]
    for i, s in enumerate(a5):
        if i % 3 == 0:
            base = 900 if i % 2 else 620
            d.energy = base
            d.keyframe_insert("energy", frame=s["f0"])
            d.energy = 60
            d.keyframe_insert("energy", frame=min(s["f0"] + 2, s["f1"] - 1))
    d.energy = 0.0
    d.keyframe_insert("energy", frame=1331)


# ------------------------------------------------------------------ render ---


def render(shots, outdir: Path, res, samples, frame_range):
    sc = bpy.context.scene
    r = sc.render
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = 100
    sc.cycles.samples = samples
    sc.cycles.use_denoising = samples >= 8
    r.fps = FPS
    outdir.mkdir(parents=True, exist_ok=True)
    f_start, f_end = frame_range

    todo = [f for f in range(f_start, min(f_end, 1331) + 1)
            if not (outdir / f"f_{f:04d}.png").exists()]
    t0 = time.time()
    done = 0
    for f in todo:
        sc.frame_set(f)
        r.filepath = str(outdir / f"f_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        done += 1
        if done % 10 == 0 or done == len(todo):
            el = time.time() - t0
            per = el / done
            left = per * (len(todo) - done)
            print(f"PROGRESS frame={f} done={done}/{len(todo)} "
                  f"{per:.2f}s/frame eta={left/60:.1f}min", flush=True)
    print(f"RENDER_DONE frames={done} range={frame_range} "
          f"total={time.time() - t0:.1f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", default=None, help="a:b inclusive frame range")
    ap.add_argument("--shots", default=None, help="shot index range a:b (debug)")
    ap.add_argument("--res", default="405x720")
    ap.add_argument("--samples", type=int, default=12)
    ap.add_argument("--out", default="v3/render/animatic")
    ap.add_argument("--scale", type=float, default=1.0, help="resolution percentage")
    a = ap.parse_args()

    doc = json.loads(SHOTLIST.read_text())
    shots = doc["shots"]
    if a.shots:
        i0, i1 = (int(x) for x in a.shots.split(":"))
        shots = shots[i0:i1]
    res = tuple(int(x) for x in a.res.split("x"))
    outdir = (PAYLOAD / a.out) if not Path(a.out).is_absolute() else Path(a.out)

    build()
    make_cameras(shots)
    apply_act_looks(doc["shots"])
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = doc["frames"]

    if a.frames:
        f0, f1 = (int(x) for x in a.frames.split(":"))
        render(doc["shots"], outdir, res, a.samples, (f0, f1))
    else:
        print("SCENE_BUILD_OK shots=", len(shots), flush=True)


if __name__ == "__main__":
    main()
