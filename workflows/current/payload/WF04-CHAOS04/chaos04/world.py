"""Sets, lights, atmosphere and the endcard. Everything here is ours.

Layout trick: the four sets sit far apart in one scene so that a single render
pass can cut between them without rebuilding anything. Light falloff keeps them
independent.
"""
from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Euler, Vector

from . import bl
from .bl import TAU
from .character import RIM_AMBER, RIM_TEAL
from .spaces import CORRIDOR as _CORRIDOR, ENDCARD as _ENDCARD, ROOM as _ROOM
from .spaces import VOID as _VOID

ASSETS = Path(__file__).resolve().parent / "assets"

ROOM = Vector(_ROOM)
CORRIDOR = Vector(_CORRIDOR)
VOID = Vector(_VOID)
ENDCARD = Vector(_ENDCARD)


def _light(name, kind, loc, energy, color="#ffffff", size=1.0, rot=(0, 0, 0),
           spread=math.pi, size_y=None, shadow=True):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.color = bl.srgb(color)[:3]
    if kind == "AREA":
        data.size = size
        data.size_y = size_y if size_y else size
    if kind == "SPOT":
        data.spot_size = spread
        data.spot_blend = 0.35
        data.shadow_soft_size = size
    if kind in {"POINT", "SPOT"}:
        data.shadow_soft_size = size
    data.use_shadow = shadow
    ob = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = Euler(rot)
    return ob


def room_lights(origin=ROOM):
    """Teal rim camera-left, amber rim camera-right, cold doorway backlight."""
    o = origin
    lights = {}
    lights["door_glow"] = _light(
        "Room · doorway backlight", "AREA", (o.x, o.y + 3.0, 1.55), 620,
        color="#BFE6E2", size=2.6, size_y=3.0, rot=(math.radians(-90), 0, 0))
    lights["rim_teal"] = _light(
        "Room · rim teal", "AREA", (o.x - 2.1, o.y + 1.9, 2.15), 150,
        color=RIM_TEAL, size=1.6, rot=(math.radians(70), 0, math.radians(-38)))
    lights["rim_amber"] = _light(
        "Room · rim amber", "AREA", (o.x + 2.2, o.y + 1.7, 1.95), 120,
        color=RIM_AMBER, size=1.4, rot=(math.radians(66), 0, math.radians(40)))
    lights["practical"] = _light(
        "Room · practical", "POINT", (o.x + 1.30, o.y + 0.85, 2.32), 70,
        color="#FFC27A", size=0.12)
    lights["key"] = _light(
        "Room · soft key", "AREA", (o.x - 0.9, o.y - 2.2, 2.5), 46,
        color="#D8E6E4", size=2.4, rot=(math.radians(-64), 0, math.radians(-20)))
    lights["fill"] = _light(
        "Room · floor bounce", "AREA", (o.x, o.y - 0.4, 0.06), 22,
        color="#7EA6A4", size=3.0, rot=(math.radians(180), 0, 0))  # faces up at the figure
    # a hard little key for the steel rack, and a pool of light on the wet floor
    lights["rack_key"] = _light(
        "Room · rack key", "AREA", (o.x - 1.55, o.y + 0.25, 2.05), 260,
        color="#CFE4E2", size=0.9, rot=(math.radians(58), 0, math.radians(-28)))
    lights["floor_pool"] = _light(
        "Room · floor pool", "SPOT", (o.x + 1.15, o.y + 0.35, 2.30), 420,
        color="#FFD3A1", size=0.25, spread=math.radians(52),
        rot=(math.radians(8), 0, math.radians(14)))
    return lights


def room(origin=ROOM, haze=True):
    o = origin
    m_floor = bl.material("Room floor · wet concrete", base="#14181A", rough=0.20,
                          spec=0.6, metal=0.05)
    bl.bump_material(m_floor, scale=180, strength=0.22, detail=4)
    m_wall = bl.material("Room wall · plaster", base="#1B1D1E", rough=0.86)
    bl.bump_material(m_wall, scale=90, strength=0.3, detail=5)
    m_trim = bl.material("Room steel", base="#24282A", rough=0.42, metal=0.85)
    m_neon = bl.emission_material("Room neon", RIM_TEAL, 9.0)
    m_door = bl.emission_material("Room doorway", "#CFEDEA", 7.0)

    parts = []
    parts.append(bl.plane("Floor", (o.x, o.y + 0.4, 0), (7.0, 6.4), m_floor))
    # puddles: tighter gloss patches
    m_puddle = bl.material("Puddle", base="#0B0E0F", rough=0.015, spec=0.9, metal=0.1)
    for i, (x, y, sx, sy) in enumerate([(-0.9, 0.6, 1.5, 1.1), (1.1, 1.4, 1.2, 0.9),
                                        (0.2, -0.6, 1.9, 1.3)]):
        parts.append(bl.plane(f"Puddle {i}", (o.x + x, o.y + y, 0.001), (sx, sy), m_puddle))

    # back wall with a doorway hole
    wall_y = o.y + 2.75
    dw, dh = 1.15, 2.25
    for name, ctr, size in [
        ("back wall L", (o.x - (dw / 2 + 1.9), wall_y, 1.7), (3.8, 0.18, 3.4)),
        ("back wall R", (o.x + (dw / 2 + 1.9), wall_y, 1.7), (3.8, 0.18, 3.4)),
        ("back wall above", (o.x, wall_y, dh + (3.4 - dh) / 2), (dw, 0.18, 3.4 - dh)),
    ]:
        parts.append(bl.box(name, ctr, size, m_wall))
    for sx in (-1, 1):
        parts.append(bl.box(f"Side wall {sx}", (o.x + 3.5 * sx, o.y + 0.4, 1.7),
                            (0.18, 6.4, 3.4), m_wall))
    parts.append(bl.box("Front wall", (o.x, o.y - 2.8, 1.7), (7.2, 0.18, 3.4), m_wall))
    parts.append(bl.box("Ceiling", (o.x, o.y + 0.4, 3.42), (7.2, 6.6, 0.16), m_wall))
    # door reveal + light box behind it
    parts.append(bl.box("Door light", (o.x, o.y + 3.15, 1.28), (1.18, 0.08, 2.30), m_door))
    for sx in (-1, 1):
        parts.append(bl.box(f"Door jamb {sx}", (o.x + (dw / 2 + 0.06) * sx, wall_y, 1.13),
                            (0.12, 0.34, 2.26), m_trim))
    parts.append(bl.box("Door head", (o.x, wall_y, dh + 0.06), (dw + 0.24, 0.34, 0.12), m_trim))

    # neon strip along the right wall base and a steel rack on the left
    parts.append(bl.box("Wall neon", (o.x + 3.40, o.y + 0.4, 0.10), (0.05, 5.4, 0.045), m_neon))
    for i in range(5):
        parts.append(bl.box(f"Rack post {i}", (o.x - 2.55 + 0.0016 * i, o.y + 1.5 - 0.62 * i, 1.05),
                            (0.06, 0.06, 2.1), m_trim))
    for i in range(3):
        parts.append(bl.box(f"Rack shelf {i}", (o.x - 2.55, o.y + 0.6, 0.55 + 0.62 * i),
                            (0.9, 2.6, 0.05), m_trim))

    # ceiling cables
    m_cable = bl.material("Cable", base="#101112", rough=0.55)
    for i in range(7):
        y = o.y - 2.2 + 0.68 * i
        sag = 0.16 + 0.05 * (i % 3)
        pts = [(o.x - 3.4 + 6.8 * k / 24,
                y + 0.10 * math.sin(k * 0.7),
                o.y * 0 + 3.30 - sag * math.sin(math.pi * k / 24)) for k in range(25)]
        parts.append(bl.tube_path(f"Cable {i}", pts, 0.012, m_cable, sides=5))

    # practical lamp: shade + bulb
    m_shade = bl.material("Lamp shade", base="#2A2320", rough=0.5, metal=0.6)
    parts.append(bl.loft("Lamp shade", [
        ((o.x + 1.30, o.y + 0.85, 2.40), 0.055, 0.055),
        ((o.x + 1.30, o.y + 0.85, 2.34), 0.150, 0.150),
        ((o.x + 1.30, o.y + 0.85, 2.28), 0.175, 0.175),
    ], m_shade, subsurf=1, close_start=False, close_end=False))
    bulb = bl.loft("Lamp bulb", [
        ((o.x + 1.30, o.y + 0.85, 2.31), 0.055, 0.055),
    ], bl.emission_material("Lamp bulb", "#FFC27A", 22.0), subsurf=1)
    parts.append(bulb)
    parts.append(bl.tube_path("Lamp cable",
                             [(o.x + 1.30, o.y + 0.85, 3.34), (o.x + 1.30, o.y + 0.85, 2.42)],
                             0.006, m_cable, sides=4))

    if haze:
        _haze_box("Room haze", (o.x, o.y + 0.2, 1.7), (7.0, 6.2, 3.4), 0.020)
    return parts


def corridor(origin=CORRIDOR):
    o = origin
    m_floor = bl.material("Corridor floor", base="#101314", rough=0.13, spec=0.7, metal=0.1)
    m_wall = bl.material("Corridor wall", base="#191B1C", rough=0.7, metal=0.15)
    m_neon = bl.emission_material("Corridor neon", RIM_TEAL, 10.0)
    m_neon2 = bl.emission_material("Corridor neon amber", RIM_AMBER, 7.0)
    m_steel = bl.material("Corridor steel", base="#26292B", rough=0.38, metal=0.9)
    parts = []
    parts.append(bl.plane("Corridor floor", (o.x, o.y - 7.5, 0), (2.6, 24.0), m_floor))
    parts.append(bl.box("Corridor ceiling", (o.x, o.y - 7.5, 2.85), (2.8, 24.0, 0.12), m_wall))
    for sx in (-1, 1):
        parts.append(bl.box(f"Corridor wall {sx}", (o.x + 1.35 * sx, o.y - 7.5, 1.42),
                            (0.12, 24.0, 2.85), m_wall))
        for i in range(9):
            y = o.y - 1.0 - 2.2 * i
            parts.append(bl.box(f"Corridor strip {sx}{i}", (o.x + 1.28 * sx, y, 1.55),
                                (0.03, 0.06, 2.2), m_neon if sx < 0 else m_neon2))
    m_panel = bl.emission_material("Corridor ceiling panel", "#E8FBFA", 26.0)
    for i in range(9):
        y = o.y - 1.6 - 2.0 * i
        parts.append(bl.plane(f"Corridor panel {i}", (o.x, y, 2.78), (1.15, 1.15), m_panel,
                              rot=(math.radians(180), 0, 0)))
    for i in range(12):
        y = o.y - 0.6 - 1.9 * i
        parts.append(bl.box(f"Corridor rib {i}", (o.x, y, 1.42), (2.7, 0.10, 2.85), m_steel))
    parts.append(bl.box("Corridor end", (o.x, o.y - 19.6, 1.4), (2.7, 0.2, 2.9),
                        bl.emission_material("Corridor end glow", "#DCF2EF", 12.0)))
    lights = {}
    for i in range(5):
        y = o.y - 1.4 - 2.6 * i
        lights[f"corr{i}"] = _light(f"Corridor light {i}", "AREA", (o.x, y, 2.70), 620,
                                    color=RIM_TEAL if i % 2 else "#DFF3F0",
                                    size=1.5, size_y=1.1,
                                    rot=(0, 0, 0))     # -Z is down: light the floor
    lights["corr_fill"] = _light(
        "Corridor fill", "AREA", (o.x - 0.9, o.y - 1.2, 1.9), 500,
        color="#DCEFEC", size=1.6, rot=(math.radians(66), 0, math.radians(64)))
    lights["corr_end"] = _light(
        "Corridor end glow", "AREA", (o.x, o.y - 19.0, 1.6), 900,
        color="#DFF7F4", size=2.2, size_y=2.4, rot=(math.radians(-90), 0, 0))
    _haze_box("Corridor haze", (o.x, o.y - 7.5, 1.4), (2.6, 23.6, 2.7), 0.024)
    return parts, lights


def white_void(origin=VOID):
    o = origin
    m_white = bl.emission_material("Void white", "#F4F8F7", 3.0)
    parts = [
        bl.plane("Void backdrop", (o.x, o.y + 4.2, 1.6), (26.0, 20.0), m_white,
                 rot=(math.radians(90), 0, 0)),
        bl.plane("Void floor", (o.x, o.y, 0), (26.0, 26.0), m_white),
        bl.plane("Void side", (o.x - 6.0, o.y + 1.0, 1.6), (20.0, 20.0), m_white,
                 rot=(0, math.radians(90), 0)),
    ]
    lights = {
        "void_key": _light("Void key", "AREA", (o.x, o.y - 2.4, 2.2), 90,
                           color="#F2FBFA", size=3.0, rot=(math.radians(-60), 0, 0)),
    }
    return parts, lights


def endcard_set(origin=ENDCARD):
    o = origin
    m_black = bl.material("Endcard black", base="#050606", rough=0.9)
    parts = [bl.plane("Endcard backdrop", (o.x, o.y + 2.2, 1.25), (6.0, 6.0), m_black,
                      rot=(math.radians(90), 0, 0))]
    lights = {"endcard_fill": _light("Endcard fill", "AREA", (o.x, o.y - 1.0, 2.0), 18,
                                     color="#9FC7C4", size=2.0,
                                     rot=(math.radians(-70), 0, 0))}
    return parts, lights


def emblem_plane(origin=ENDCARD, size=0.42, z=1.66):
    m = bl.material("Emblem", base="#000000", rough=0.4, alpha=0.0, emit="#EAF6F4",
                    emit_strength=7.0)
    tex = bl.image_texture(m, ASSETS / "emblem.png")
    p = m.node_tree.nodes.get("Principled BSDF")
    m.node_tree.links.new(tex.outputs["Color"], p.inputs["Emission Color"])
    m.node_tree.links.new(tex.outputs["Alpha"], p.inputs["Alpha"])
    m.blend_method = "BLEND"
    ob = bl.plane("Monarch emblem", (origin.x, origin.y + 2.0, z), (size, size), m,
                  rot=(math.radians(90), 0, 0))
    return ob


def wordmark_plane(origin=ENDCARD, width=0.56, z=1.20):
    m = bl.material("Wordmark", base="#000000", rough=0.4, alpha=0.0, emit="#F2FAF8",
                    emit_strength=6.0)
    tex = bl.image_texture(m, ASSETS / "wordmark.png")
    p = m.node_tree.nodes.get("Principled BSDF")
    m.node_tree.links.new(tex.outputs["Color"], p.inputs["Emission Color"])
    m.node_tree.links.new(tex.outputs["Alpha"], p.inputs["Alpha"])
    m.blend_method = "BLEND"
    ob = bl.plane("Monarch wordmark", (origin.x, origin.y + 2.0, z), (width, width / 2.2857),
                  m, rot=(math.radians(90), 0, 0))
    return ob


def _haze_box(name, center, size, density):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    vol = n.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.82, 0.90, 0.95, 1.0)
    vol.inputs["Density"].default_value = density
    vol.inputs["Anisotropy"].default_value = 0.45
    m.node_tree.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    ob = bl.box(name, center, size, None)
    ob.data.materials.append(m)
    ob.visible_shadow = False
    return ob


def frame_gate(origin=ROOM, x=0.0, y=-0.55):
    """A heavy picture-frame gate the figure stands inside for shots 17/19."""
    o = origin
    m = bl.material("Frame steel", base="#202324", rough=0.36, metal=0.9)
    parts = []
    parts.append(bl.box("Gate left", (o.x + x - 0.62, o.y + y, 1.05), (0.07, 0.07, 2.1), m))
    parts.append(bl.box("Gate right", (o.x + x + 0.62, o.y + y, 1.05), (0.07, 0.07, 2.1), m))
    parts.append(bl.box("Gate top", (o.x + x, o.y + y, 2.09), (1.31, 0.07, 0.07), m))
    parts.append(bl.box("Gate bottom", (o.x + x, o.y + y, 0.02), (1.31, 0.07, 0.07), m))
    return parts


def chains(origin=ROOM, count=6):
    m = bl.material("Chain", base="#2B2E2F", rough=0.35, metal=0.95)
    parts = []
    for i in range(count):
        x = origin.x - 1.7 + 0.72 * i
        y = origin.y + 1.9
        pts = [(x, y + 0.02 * math.sin(k), 3.1) for k in range(2)]
        parts.append(bl.tube_path(f"Chain {i}", [(x, y, 3.34), (x, y, 1.85)], 0.008, m, sides=4))
    return parts


def atmosphere_world(strength=0.035, color="#0B1418"):
    scene = bpy.context.scene
    world = bpy.data.worlds.new("Monarch world")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = bl.srgb(color)
    bg.inputs[1].default_value = strength
    scene.world = world
    return world
