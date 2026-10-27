"""MONARCH — our locked character, rebuilt as real 3D geometry.

Authority: characters/monarch/character.json  (state LOCKED, "USE, DO NOT REDESIGN")
variant  : real — face v5, body v2
palette  : characters/monarch/tooling/SF_proportions_v1.json
The face is the locked v5 capture, projected onto a sculpted head (planar -Y);
everything below the neck is modelled from the v2 body sheet: black shirt,
charcoal blazer no tie, slim black trousers, black leather sneakers.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Euler, Quaternion, Vector

from . import bl
from .bl import TAU, srgb

ASSETS = Path(__file__).resolve().parent / "assets"

SKIN = "#958C7E"
HAIR = "#2B2B2A"
BLAZER = "#2B2B2A"
BLAZER_EDGE = "#3A3A38"
SHIRT = "#171817"
TROUSERS = "#0C0F0E"
GLOVE = "#DED6D0"
SNEAKER = "#1B1B1A"
SOLE = "#6E6A64"
RIM_TEAL = "#3E827E"
RIM_AMBER = "#9E6E46"

HEIGHT = 1.785
CHIN_Z = 1.545
HAIRLINE_Z = 1.730
FACE_HALF_W = 0.0686
NECK_TOP = 1.56
SHOULDER_Z = 1.435
SHOULDER_X = 0.195

FINGER_BONES = ("hand", "fingers")


# ------------------------------------------------------------------ rig
BONES = [
    ("root", (0, 0, 0.02), (0, 0, 0.16), None, False),
    ("hips", (0, 0, 0.98), (0, 0, 1.10), "root", False),
    ("spine", (0, 0, 1.10), (0, 0, 1.26), "hips", True),
    ("chest", (0, 0, 1.26), (0, 0, 1.44), "spine", True),
    ("neck", (0, 0, 1.44), (0, 0, 1.55), "chest", True),
    ("head", (0, 0, 1.55), (0, 0, 1.79), "neck", True),
]
for s, sx in (("L", 1.0), ("R", -1.0)):
    BONES += [
        (f"shoulder.{s}", (0.035 * sx, 0, 1.420), (0.195 * sx, 0, 1.435), "chest", False),
        (f"upper_arm.{s}", (0.195 * sx, 0, 1.435), (0.225 * sx, 0.012, 1.150),
         f"shoulder.{s}", True),
        (f"forearm.{s}", (0.225 * sx, 0.012, 1.150), (0.240 * sx, 0.020, 0.905),
         f"upper_arm.{s}", True),
        (f"hand.{s}", (0.240 * sx, 0.020, 0.905), (0.245 * sx, 0.020, 0.815),
         f"forearm.{s}", True),
        (f"fingers.{s}", (0.245 * sx, 0.020, 0.815), (0.250 * sx, 0.020, 0.735),
         f"hand.{s}", True),
        (f"thigh.{s}", (0.095 * sx, 0, 0.98), (0.100 * sx, 0, 0.50), "hips", False),
        (f"shin.{s}", (0.100 * sx, 0, 0.50), (0.105 * sx, 0, 0.09), f"thigh.{s}", True),
        (f"foot.{s}", (0.105 * sx, 0, 0.09), (0.105 * sx, -0.17, 0.03), f"shin.{s}", True),
    ]


def build_rig():
    return bl.ensure_armature("MONARCH_RIG", BONES)


def set_pose(rig, pose, frame=None):
    """pose: {bone: (rx, ry, rz) degrees about armature axes} (+ optional 'loc:<bone>').

    Rotations are given in armature space (X = pitch forward, Y = side lean,
    Z = twist) and converted into each bone's local basis, so numbers mean the
    same thing on every bone.
    """
    for key, val in pose.items():
        if key.startswith("loc:"):
            bone = key[4:]
            pb = rig.pose.bones[bone]
            rest = pb.bone.matrix_local.to_quaternion()
            pb.location = rest.inverted() @ Vector(val)
            if frame is not None:
                pb.keyframe_insert("location", frame=frame)
            continue
        pb = rig.pose.bones.get(key)
        if pb is None:
            continue
        rest = pb.bone.matrix_local.to_quaternion()
        deg = [math.radians(a) for a in val]
        delta = Euler(deg, "XYZ").to_quaternion()
        pb.rotation_quaternion = rest.inverted() @ delta @ rest
        if frame is not None:
            pb.keyframe_insert("rotation_quaternion", frame=frame)


def rest_pose(rig):
    for pb in rig.pose.bones:
        pb.rotation_quaternion = Quaternion((1, 0, 0, 0))
        pb.location = Vector((0, 0, 0))


# ------------------------------------------------------------------ head
# measured off the locked v5 sheet: chin 1.545, mouth 1.595, nose 1.622,
# eyes 1.658, brows 1.669, hairline 1.730, crown 1.785
HEAD_RINGS = [
    (1.5450, 0.0195, 0.0300, -0.0030),
    (1.5540, 0.0300, 0.0385, -0.0025),
    (1.5660, 0.0405, 0.0470, -0.0015),
    (1.5760, 0.0470, 0.0530, -0.0010),
    (1.5900, 0.0530, 0.0575, 0.0000),
    (1.6050, 0.0590, 0.0625, 0.0000),
    (1.6220, 0.0640, 0.0665, 0.0005),
    (1.6400, 0.0675, 0.0690, 0.0010),
    (1.6580, 0.0688, 0.0700, 0.0012),
    (1.6690, 0.0688, 0.0708, 0.0012),
    (1.6900, 0.0672, 0.0710, 0.0015),
    (1.7100, 0.0620, 0.0690, 0.0020),
    (1.7300, 0.0530, 0.0620, 0.0025),
    (1.7500, 0.0420, 0.0500, 0.0030),
    (1.7700, 0.0270, 0.0340, 0.0030),
    (1.7830, 0.0100, 0.0140, 0.0030),
]


def _gauss(x, mu, sigma):
    return math.exp(-0.5 * ((x - mu) / sigma) ** 2)


def _face_relief(x, z):
    """Front-facing displacement: nose, brow, sockets, lips, chin, cheekbones."""
    ax = abs(x)
    d = 0.0
    # nose ridge + tip
    d += 0.0255 * _gauss(x, 0, 0.0135) * _gauss(z, 1.6215, 0.0155)
    d += 0.0105 * _gauss(x, 0, 0.0110) * _gauss(z, 1.6520, 0.0260)
    d += 0.0060 * _gauss(x, 0, 0.0080) * _gauss(z, 1.6760, 0.0100)
    # brow ridge, two lobes
    d += 0.0062 * (_gauss(x, 0.040, 0.019) + _gauss(x, -0.040, 0.019)) * _gauss(z, 1.6720, 0.0085)
    # eye sockets recessed
    d -= 0.0042 * (_gauss(x, 0.049, 0.017) + _gauss(x, -0.049, 0.017)) * _gauss(z, 1.6570, 0.0110)
    # lips
    d += 0.0048 * _gauss(x, 0, 0.0200) * _gauss(z, 1.5950, 0.0090)
    # chin
    d += 0.0058 * _gauss(x, 0, 0.0220) * _gauss(z, 1.5560, 0.0110)
    # cheekbones
    d += 0.0034 * (_gauss(x, 0.058, 0.016) + _gauss(x, -0.058, 0.016)) * _gauss(z, 1.6250, 0.0130)
    return d


def build_head(mat_skin, mat_face):
    seg = 64
    verts, faces, uvs = [], [], []
    for (z, rx, ry, dy) in HEAD_RINGS:
        for j in range(seg):
            a = TAU * j / seg
            x = math.cos(a) * rx
            y = math.sin(a) * ry + dy
            front = max(0.0, -math.sin(a))
            if front > 0:
                y -= _face_relief(x, z) * front ** 1.35
            verts.append((x, y, z))
    for i in range(len(HEAD_RINGS) - 1):
        for j in range(seg):
            a = i * seg + j
            b = i * seg + (j + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    # crown cap + chin cap
    top = len(verts)
    verts.append((0, HEAD_RINGS[-1][3], HEAD_RINGS[-1][0] + 0.012))
    for j in range(seg):
        faces.append((top, (len(HEAD_RINGS) - 1) * seg + j, (len(HEAD_RINGS) - 1) * seg + (j + 1) % seg))
    verts.append((0, HEAD_RINGS[0][3], HEAD_RINGS[0][0] - 0.008))
    low = len(verts) - 1
    for j in range(seg):
        faces.append((low, (j + 1) % seg, j))

    # planar UV through the measured face rect
    meta = json.loads((ASSETS / "face_rect.json").read_text())
    u0, v0, u1, v1 = meta["inner_rect"]
    uv = []
    for v in verts:
        tx = 0.5 + (v[0] / (2 * FACE_HALF_W))
        tz = (v[2] - CHIN_Z) / (HAIRLINE_Z - CHIN_Z)
        uv.append((u0 + (u1 - u0) * tx, v0 + (v1 - v0) * tz))

    me = bpy.data.meshes.new("HEAD")
    me.from_pydata([Vector(v) for v in verts], [], [list(f) for f in faces])
    me.validate(verbose=False)
    me.update()
    layer = me.uv_layers.new(name="face projection")
    flat = []
    for poly in me.polygons:
        for vi in poly.vertices:          # UVs live on loops, not vertices
            flat.extend(uv[vi])
    layer.data.foreach_set("uv", flat)
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new("HEAD · Monarch v5", me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(mat_face)

    sub = ob.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 2

    neck = bl.loft("Neck", [
        ((0, 0.004, 1.420), 0.058, 0.052),
        ((0, 0.004, 1.470), 0.052, 0.048),
        ((0, 0.002, 1.530), 0.049, 0.046),
        ((0, 0.000, 1.560), 0.050, 0.048),
    ], mat_skin, subsurf=1, close_start=False)
    ears = []
    for s in (1, -1):
        e = bl.loft(f"Ear.{s}", [
            ((0.0665 * s, 0.012, 1.6480), 0.006, 0.016),
            ((0.0730 * s, 0.014, 1.6520), 0.004, 0.019),
            ((0.0700 * s, 0.012, 1.6640), 0.003, 0.010),
        ], mat_skin, subsurf=1)
        ears.append(e)
    return ob, neck, ears


def build_hair(mat_hair, mat_sheen):
    """Sculpted scalp volume + swept fringe + groom strands. Reads as our hair:
    black, swept back off the forehead, short on the sides, full at the crown."""
    rnd = random.Random(7)
    verts, faces = [], []
    seg, rings = 72, 26
    for i in range(rings + 1):
        t = i / rings                        # 0 = hairline/back bottom, 1 = crown
        for j in range(seg):
            a = TAU * j / seg
            # cap that follows the skull and dips at the hairline
            front = max(0.0, -math.sin(a))
            back = max(0.0, math.sin(a))
            base_z = bl.lerp(1.6520, 1.7380, front) + bl.lerp(0.0, 0.010, back)
            phi = (math.pi * 0.5) * t
            r_scale = 1.052 + 0.020 * math.sin(a * 3 + 0.7) * (1 - t)
            z = base_z + (1.8000 - base_z) * math.sin(phi) ** 0.92
            rx = 0.0700 * r_scale * math.cos(phi * 0.86)
            ry = 0.0715 * r_scale * math.cos(phi * 0.86)
            # mass at the back of the head, tighter at the temples
            swell = 1.0 + 0.16 * max(0.0, math.sin(a)) * (1 - t * 0.5)
            x = math.cos(a) * rx * swell
            y = math.sin(a) * ry * swell + 0.002
            verts.append((x, y, z))
    for i in range(rings):
        for j in range(seg):
            a = i * seg + j
            b = i * seg + (j + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    cap = bl.mesh_object("Hair · sculpted mass", verts, faces, mat_hair, subsurf=1)

    # groom: strands following the swept-back direction
    lines = []
    for _ in range(1100):
        a = rnd.uniform(0, TAU)
        front = max(0.0, -math.sin(a))
        start = rnd.uniform(0.02, 0.42)
        end = rnd.uniform(0.72, 1.0)
        line = []
        for k in range(9):
            u = k / 8
            t = bl.lerp(start, end, u)
            phi = (math.pi * 0.5) * t
            base_z = bl.lerp(1.6520, 1.7380, front) + bl.lerp(0.0, 0.010, max(0.0, math.sin(a)))
            z = base_z + (1.8000 - base_z) * math.sin(phi) ** 0.92
            rr = 1.056 + rnd.uniform(-0.004, 0.006)
            rx = 0.0700 * rr * math.cos(phi * 0.86)
            ry = 0.0715 * rr * math.cos(phi * 0.86)
            # sweep the strand tips backwards
            sweep = 0.010 * u * u
            x = math.cos(a) * rx + sweep * 0.35
            y = math.sin(a) * ry + 0.002 + sweep
            line.append((x, y, z + 0.0015 * math.sin(u * math.pi)))
        lines.append(line)
    strands = bl.strands("Hair · groom", lines, 0.00042, mat_sheen, sides=3)

    # fringe curtains over the forehead, asymmetry as in v5
    fringe = []
    for sgn in (1, -1):
        for _ in range(150):
            off = rnd.uniform(-0.011, 0.011)
            depth = rnd.uniform(-0.004, 0.006)
            p0 = Vector((0.010 * sgn + off, -0.052 + depth, 1.7420))
            p1 = Vector((0.044 * sgn + off * 0.8, -0.070 + depth, 1.7350))
            p2 = Vector((0.064 * sgn + off * 0.5, -0.062 + depth, 1.7080))
            p3 = Vector((0.068 * sgn + off * 0.3, -0.052 + depth,
                         1.6780 + rnd.uniform(-0.010, 0.012)))
            line = []
            for k in range(11):
                u = k / 10
                p = ((1 - u) ** 3) * p0 + 3 * ((1 - u) ** 2) * u * p1 \
                    + 3 * (1 - u) * u * u * p2 + (u ** 3) * p3
                line.append(tuple(p))
            fringe.append(line)
    fringe_obj = bl.strands("Hair · swept fringe", fringe, 0.0011, mat_sheen, sides=3)

    # sideburns
    sides = []
    for sgn in (1, -1):
        for _ in range(90):
            z0 = rnd.uniform(1.6600, 1.6900)
            line = []
            for k in range(7):
                u = k / 6
                line.append((0.0685 * sgn + rnd.uniform(-0.002, 0.002),
                             -0.030 + 0.020 * u,
                             z0 - 0.030 * u))
            sides.append(line)
    side_obj = bl.strands("Sideburns", sides, 0.0006, mat_sheen, sides=3)
    return cap, strands, fringe_obj, side_obj


def build_beard(mat_hair):
    """Short beard + moustache, 3D fibres on the measured lower face."""
    rnd = random.Random(11)
    skin = srgb(SKIN)
    lines = []
    for _ in range(3400):
        z = rnd.uniform(1.5450, 1.6120)
        # beard band: jaw and chin, thin up the cheeks, thicker at the chin
        half_w = 0.062 * min(1.0, (z - 1.530) / 0.070) ** 0.6
        if z > 1.598 and rnd.random() < 0.55:
            continue
        x = rnd.uniform(-half_w, half_w)
        if abs(x) < 0.026 and z > 1.588 and z < 1.604:
            continue                     # keep the lips clear
        ry = 0.0700
        y = -math.sqrt(max(0.0, 1 - (x / max(1e-4, half_w)) ** 2)) * ry * 0.98 - 0.004
        y -= _face_relief(x, z) * 0.9
        base = Vector((x, y, z))
        normal = Vector((x * 0.6, -1.0, 0.1)).normalized()
        length = rnd.uniform(0.0028, 0.0052)
        lines.append([tuple(base),
                      tuple(base + normal * length * 0.55),
                      tuple(base + normal * length + Vector((0, 0, -0.0012)))])
    return bl.strands("Beard · groom", lines, 0.00011, mat_hair, sides=3)


# ------------------------------------------------------------------ body
def build_body(rig, mat_blazer, mat_edge, mat_shirt, mat_trouser, mat_skin,
               mat_shoe, mat_sole):
    parts = []
    torso = bl.loft("Blazer · torso", [
        ((0, 0, 0.855), 0.176, 0.113),
        ((0, 0, 0.905), 0.172, 0.111),
        ((0, 0.002, 0.980), 0.168, 0.110),
        ((0, 0.004, 1.060), 0.162, 0.107),
        ((0, 0.004, 1.120), 0.157, 0.105),
        ((0, 0.002, 1.200), 0.168, 0.110),
        ((0, 0.000, 1.280), 0.184, 0.117),
        ((0, -0.002, 1.350), 0.196, 0.122),
        ((0, -0.004, 1.408), 0.199, 0.121),
        ((0, -0.002, 1.440), 0.180, 0.114),
        ((0, 0.002, 1.462), 0.100, 0.083),
    ], mat_blazer, subsurf=2, close_start=True, close_end=False)
    bl.bump_material(mat_blazer, scale=1400, strength=0.12)
    parts.append(torso)

    # shirt: dark panel filling the open blazer front
    shirt = bl.loft("Shirt", [
        ((0, 0.004, 0.990), 0.108, 0.104),
        ((0, 0.002, 1.120), 0.112, 0.104),
        ((0, 0.000, 1.260), 0.120, 0.108),
        ((0, -0.002, 1.360), 0.126, 0.112),
        ((0, 0.000, 1.430), 0.118, 0.106),
        ((0, 0.002, 1.470), 0.086, 0.078),
    ], mat_shirt, subsurf=2)
    parts.append(shirt)

    # lapels, proud of the blazer, running collar → sternum
    for s in (1, -1):
        v = [(0.012 * s, -0.116, 1.462), (0.088 * s, -0.104, 1.452),
             (0.140 * s, -0.086, 1.360), (0.070 * s, -0.116, 1.290),
             (0.020 * s, -0.120, 1.250)]
        f = [(0, 1, 2, 3), (0, 3, 4)]
        lap = bl.mesh_object(f"Lapel.{s}", v, f, mat_edge, smooth=False)
        sol = lap.modifiers.new("Solidify", "SOLIDIFY")
        sol.thickness = 0.008
        parts.append(lap)

    # collar band
    collar = bl.loft("Collar", [
        ((0, 0.004, 1.452), 0.098, 0.086),
        ((0, 0.002, 1.480), 0.092, 0.082),
        ((0, 0.000, 1.498), 0.086, 0.078),
    ], mat_edge, subsurf=2, close_start=False, close_end=False)
    parts.append(collar)

    # sleeves + hands
    for s, sx in (("L", 1.0), ("R", -1.0)):
        upper = bl.loft(f"Sleeve upper.{s}", [
            ((0.186 * sx, -0.002, 1.452), 0.064, 0.062),
            ((0.198 * sx, 0.000, 1.400), 0.066, 0.064),
            ((0.212 * sx, 0.006, 1.300), 0.060, 0.058),
            ((0.222 * sx, 0.010, 1.180), 0.055, 0.054),
            ((0.225 * sx, 0.012, 1.150), 0.053, 0.052),
        ], mat_blazer, subsurf=2, close_start=True, close_end=False)
        parts.append(upper)
        fore = bl.loft(f"Sleeve fore.{s}", [
            ((0.225 * sx, 0.012, 1.155), 0.053, 0.052),
            ((0.233 * sx, 0.016, 1.050), 0.048, 0.047),
            ((0.239 * sx, 0.019, 0.960), 0.043, 0.042),
            ((0.240 * sx, 0.020, 0.915), 0.041, 0.040),
        ], mat_blazer, subsurf=2, close_start=False, close_end=False)
        parts.append(fore)
        cuff = bl.loft(f"Cuff.{s}", [
            ((0.240 * sx, 0.020, 0.922), 0.043, 0.042),
            ((0.241 * sx, 0.020, 0.902), 0.042, 0.041),
        ], mat_edge, subsurf=1, close_start=False, close_end=False)
        parts.append(cuff)
        hand, fingers = build_hand(f"hand.{s}", 0.243 * sx, 0.020, 0.900, sx, mat_skin)
        parts += [hand, fingers]
        parts.append(bl.loft(f"Elbow.{s}", [
            ((0.225 * sx, 0.010, 1.170), 0.050, 0.049),
            ((0.226 * sx, 0.012, 1.150), 0.054, 0.053),
            ((0.227 * sx, 0.014, 1.130), 0.051, 0.050),
        ], mat_blazer, subsurf=2))

    # legs
    for s, sx in (("L", 1.0), ("R", -1.0)):
        thigh = bl.loft(f"Trouser thigh.{s}", [
            ((0.098 * sx, 0, 0.995), 0.086, 0.084),
            ((0.099 * sx, 0, 0.900), 0.080, 0.079),
            ((0.100 * sx, 0.002, 0.740), 0.070, 0.069),
            ((0.100 * sx, 0.002, 0.560), 0.062, 0.061),
            ((0.100 * sx, 0.002, 0.500), 0.060, 0.059),
        ], mat_trouser, subsurf=2, close_start=False, close_end=False)
        parts.append(thigh)
        shin = bl.loft(f"Trouser shin.{s}", [
            ((0.100 * sx, 0.002, 0.505), 0.059, 0.058),
            ((0.102 * sx, 0.002, 0.380), 0.055, 0.054),
            ((0.104 * sx, 0.002, 0.220), 0.052, 0.051),
            ((0.105 * sx, 0.002, 0.115), 0.050, 0.049),
        ], mat_trouser, subsurf=2, close_start=False, close_end=False)
        parts.append(shin)
        parts.append(bl.loft(f"Knee.{s}", [
            ((0.100 * sx, 0.002, 0.520), 0.058, 0.057),
            ((0.100 * sx, 0.000, 0.500), 0.061, 0.060),
            ((0.100 * sx, 0.002, 0.480), 0.058, 0.057),
        ], mat_trouser, subsurf=2))
        shoe = bl.mesh_object(f"Sneaker.{s}", [
            (0.062 * sx, 0.055, 0.000), (0.062 * sx, -0.155, 0.000),
            (0.155 * sx, -0.155, 0.000), (0.155 * sx, 0.055, 0.000),
            (0.068 * sx, 0.045, 0.062), (0.068 * sx, -0.135, 0.078),
            (0.150 * sx, -0.135, 0.078), (0.150 * sx, 0.045, 0.062),
        ], [(0, 1, 2, 3), (4, 5, 6, 7), (0, 4, 5, 1), (1, 5, 6, 2),
            (2, 6, 7, 3), (3, 7, 4, 0)], mat_shoe, smooth=False)
        bev = shoe.modifiers.new("Bevel", "BEVEL")
        bev.width = 0.012
        bev.segments = 3
        parts.append(shoe)
        sole = bl.mesh_object(f"Sole.{s}", [
            (0.060 * sx, 0.058, 0.000), (0.060 * sx, -0.158, 0.000),
            (0.157 * sx, -0.158, 0.000), (0.157 * sx, 0.058, 0.000),
            (0.060 * sx, 0.058, 0.018), (0.060 * sx, -0.158, 0.018),
            (0.157 * sx, -0.158, 0.018), (0.157 * sx, 0.058, 0.018),
        ], [(0, 1, 2, 3), (4, 5, 6, 7), (0, 4, 5, 1), (1, 5, 6, 2),
            (2, 6, 7, 3), (3, 7, 4, 0)], mat_sole, smooth=False)
        parts.append(sole)

    # ---- skinning
    torso_stops = [(0.86, "hips"), (1.02, "spine"), (1.20, "spine"),
                   (1.30, "chest"), (1.47, "chest")]
    for ob in (torso, shirt, collar):
        bl.bind(ob, rig, bl.ramp_weights(torso_stops, axis=2, softness=1.4))
    for ob in parts:
        if ob.name.startswith(("Lapel",)):
            bl.bind(ob, rig, bl.ramp_weights([(1.25, "chest"), (1.47, "chest")], axis=2))
        elif ob.name.startswith(("Sleeve upper", "Elbow")):
            side = ob.name[-1]
            bl.bind(ob, rig, bl.ramp_weights(
                [(1.12, f"forearm.{side}"), (1.20, f"upper_arm.{side}"),
                 (1.40, f"upper_arm.{side}"), (1.46, "chest")], axis=2, softness=0.9))
        elif ob.name.startswith("Sleeve fore"):
            side = ob.name[-1]
            bl.bind(ob, rig, bl.ramp_weights(
                [(0.86, f"hand.{side}"), (0.95, f"forearm.{side}")], axis=2))
        elif ob.name.startswith("Cuff"):
            bl.bind(ob, rig, {f"forearm.{ob.name[-1]}": 1.0})
        elif ob.name.startswith(("Hand", "Fingers", "Thumb")):
            side = ob.name.split(".")[-1]
            if ob.name.startswith("Fingers"):
                bl.bind(ob, rig, {f"fingers.{side}": 0.82, f"hand.{side}": 0.18})
            else:
                bl.bind(ob, rig, {f"hand.{side}": 1.0})
        elif ob.name.startswith("Trouser thigh"):
            side = ob.name[-1]
            bl.bind(ob, rig, bl.ramp_weights(
                [(0.48, f"shin.{side}"), (0.56, f"thigh.{side}"),
                 (0.94, f"thigh.{side}"), (1.01, "hips")], axis=2, softness=1.0))
        elif ob.name.startswith("Trouser shin"):
            side = ob.name[-1]
            bl.bind(ob, rig, bl.ramp_weights(
                [(0.075, f"foot.{side}"), (0.150, f"shin.{side}")], axis=2))
        elif ob.name.startswith("Knee"):
            side = ob.name[-1]
            bl.bind(ob, rig, {f"shin.{side}": 0.55, f"thigh.{side}": 0.45})
        elif ob.name.startswith(("Sneaker", "Sole")):
            bl.bind(ob, rig, {f"foot.{ob.name[-1]}": 1.0})
    return parts


def build_hand(bone_side, x, y, z, sx, mat):
    """Palm + four fingers + thumb, bound as a group so a curl reads as a gesture."""
    tag = bone_side.split(".")[-1]
    palm = bl.loft(f"Hand palm.{tag}", [
        ((x, y, z + 0.004), 0.036, 0.017),
        ((x + 0.002 * sx, y, z - 0.030), 0.040, 0.016),
        ((x + 0.003 * sx, y, z - 0.062), 0.038, 0.014),
        ((x + 0.004 * sx, y, z - 0.078), 0.032, 0.012),
    ], mat, subsurf=2, close_start=False, close_end=True)
    verts, faces = [], []
    for i, off in enumerate((-0.026, -0.009, 0.009, 0.026)):
        length = 0.070 - abs(off) * 0.55
        base = Vector((x + 0.004 * sx, y + off, z - 0.078))
        for k in range(4):
            u = k / 3
            r = 0.0085 - 0.0022 * u
            cx = base.x + 0.0015 * u * sx
            cz = base.z - length * u
            cy = base.y + off * 0.10 * u
            start = len(verts)
            for j in range(6):
                a = TAU * j / 6
                verts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.9, cz))
            if k:
                for j in range(6):
                    a0 = start - 6 + j
                    b0 = start - 6 + (j + 1) % 6
                    faces.append((a0, b0, start + (j + 1) % 6, start + j))
        tip = len(verts)
        verts.append((base.x + 0.002 * sx, base.y + off * 0.1, base.z - length - 0.006))
        for j in range(6):
            faces.append((tip, start + j, start + (j + 1) % 6))
    # thumb
    tb = Vector((x + 0.030 * sx, y - 0.006, z - 0.030))
    for k in range(4):
        u = k / 3
        r = 0.011 - 0.003 * u
        cx = tb.x + 0.004 * u * sx
        cz = tb.z - 0.045 * u
        cy = tb.y - 0.012 * u
        start = len(verts)
        for j in range(6):
            a = TAU * j / 6
            verts.append((cx + math.cos(a) * r, cy + math.sin(a) * r, cz))
        if k:
            for j in range(6):
                faces.append((start - 6 + j, start - 6 + (j + 1) % 6,
                              start + (j + 1) % 6, start + j))
    fingers = bl.mesh_object(f"Fingers.{tag}", verts, faces, mat, smooth=True, subsurf=1)
    return palm, fingers


# ------------------------------------------------------------------ assemble
def build_character():
    m_face = bl.material("MONARCH skin · v5 projected", base=SKIN, rough=0.44,
                         spec=0.42, sss=0.06, sss_radius=(0.9, 0.32, 0.2),
                         sss_scale=0.0035)
    tex = bl.image_texture(m_face, ASSETS / "face_tex.png")
    tex.extension = "EXTEND"
    bl.bump_material(m_face, scale=2600, strength=0.10)

    m_skin = bl.material("MONARCH skin", base=SKIN, rough=0.46, spec=0.40,
                         sss=0.05, sss_scale=0.003)
    m_hair = bl.material("MONARCH hair", base=HAIR, rough=0.34, spec=0.5, sheen=0.25)
    m_sheen = bl.material("MONARCH hair sheen", base="#1A1A19", rough=0.26, spec=0.7)
    m_blazer = bl.material("MONARCH blazer", base=BLAZER, rough=0.72, spec=0.35,
                           sheen=0.30)
    m_edge = bl.material("MONARCH blazer edge", base=BLAZER_EDGE, rough=0.62, spec=0.4,
                         sheen=0.2)
    m_shirt = bl.material("MONARCH shirt", base=SHIRT, rough=0.68, spec=0.3, sheen=0.15)
    m_trouser = bl.material("MONARCH trousers", base=TROUSERS, rough=0.76, spec=0.28)
    m_shoe = bl.material("MONARCH sneakers", base=SNEAKER, rough=0.36, spec=0.5, coat=0.2)
    m_sole = bl.material("MONARCH soles", base=SOLE, rough=0.62, spec=0.3)

    rig = build_rig()
    head, neck, ears = build_head(m_skin, m_face)
    hair = build_hair(m_hair, m_sheen)
    beard = build_beard(m_hair)
    body = build_body(rig, m_blazer, m_edge, m_shirt, m_trouser, m_skin, m_shoe, m_sole)

    for ob in (head, neck, beard):
        bl.bind(ob, rig, {"head": 1.0})
    for e in ears:
        bl.bind(e, rig, {"head": 1.0})
    for ob in hair:
        bl.bind(ob, rig, {"head": 1.0})

    rig.location = (0, 0, 0)
    return dict(rig=rig, head=head, neck=neck, hair=hair, beard=beard, body=body,
                materials=dict(blazer=m_blazer, skin=m_skin, hair=m_hair))
