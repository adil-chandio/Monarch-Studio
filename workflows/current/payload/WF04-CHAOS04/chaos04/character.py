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

SKIN = "#958C7E"            # palette swatch (hands, ears)
SKIN_CAPTURE = "#8A5F46"     # measured off the v5 capture (core mean 133,95,72)
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
FACE_HALF_W = 0.0765
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
    assert len(flat) == len(layer.data) * 2, (len(flat), len(layer.data) * 2)
    layer.data.foreach_set("uv", flat)
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new("HEAD · Monarch v5", me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(mat_skin)      # slot 0: our modelled skin
    me.materials.append(mat_face)      # slot 1: the locked v5 capture, front only

    # keep the capture on the face front; temples, jaw line and skull stay modelled
    for poly in me.polygons:
        cz = sum(me.vertices[i].co.z for i in poly.vertices) / len(poly.vertices)
        ny = poly.normal.y            # -1 = facing the lens, +1 = back of the skull
        front = ny < 0.10 and 1.5480 < cz < 1.7420
        poly.material_index = 1 if front else 0

    sub = ob.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 2

    neck = bl.loft("Neck", [
        ((0, 0.006, 1.404), 0.072, 0.062),
        ((0, 0.006, 1.432), 0.060, 0.052),
        ((0, 0.004, 1.462), 0.050, 0.045),
        ((0, 0.002, 1.500), 0.044, 0.041),
        ((0, 0.000, 1.536), 0.046, 0.044),
    ], mat_skin, subsurf=1, close_start=False)
    ears = []
    for s in (1, -1):
        e = bl.loft(f"Ear.{s}", [
            ((0.0740 * s, 0.012, 1.6520), 0.006, 0.017),
            ((0.0812 * s, 0.014, 1.6560), 0.004, 0.020),
            ((0.0778 * s, 0.012, 1.6680), 0.003, 0.011),
        ], mat_skin, subsurf=1)
        ears.append(e)
    return ob, neck, ears


def build_hair(mat_hair, mat_sheen):
    """A hair shell grown off the skull's own profile: crown → hairline, with
    thickness that tapers to nothing at the apex (no top-knot), extra mass at the
    nape, and a slightly higher hairline over the brow."""
    rnd = random.Random(7)
    rings = HEAD_RINGS

    def skull(z):
        if z <= rings[0][0]:
            return rings[0][1], rings[0][2], rings[0][3]
        if z >= rings[-1][0]:
            return rings[-1][1], rings[-1][2], rings[-1][3]
        for (z0, rx0, ry0, dy0), (z1, rx1, ry1, dy1) in zip(rings, rings[1:]):
            if z0 <= z <= z1:
                u = (z - z0) / max(1e-6, z1 - z0)
                return bl.lerp(rx0, rx1, u), bl.lerp(ry0, ry1, u), bl.lerp(dy0, dy1, u)
        return rings[-1][1], rings[-1][2], rings[-1][3]

    Z_CROWN = 1.7955
    seg, rows = 72, 26

    def hairline_z(a):
        front = max(0.0, -math.sin(a))
        back = max(0.0, math.sin(a))
        return 1.7480 + 0.006 * front - 0.052 * back

    verts, faces = [], []
    for i in range(rows + 1):
        t = i / rows                      # 0 = apex, 1 = hairline
        for j in range(seg):
            a = TAU * j / seg
            front = max(0.0, -math.sin(a))
            back = max(0.0, math.sin(a))
            z = bl.lerp(Z_CROWN, hairline_z(a), t ** 0.92)
            rx, ry, dy = skull(z)
            # thickness: zero at the apex, full over the skull, a touch more at the nape
            thick = (0.0085 + 0.0050 * back) * math.sin(min(1.0, t * 1.9) * math.pi / 2) ** 0.8
            x = math.cos(a) * (rx + thick)
            y = math.sin(a) * (ry + thick) + dy
            verts.append((x, y, z + 0.002))
    for i in range(rows):
        for j in range(seg):
            a = i * seg + j
            b = i * seg + (j + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    # a real apex, so the crown rounds off instead of pinching into a knot
    apex = len(verts)
    verts.append((0.0, 0.004, Z_CROWN + 0.004))
    for j in range(seg):
        faces.append((apex, (j + 1) % seg, j))
    cap = bl.mesh_object("Hair · shell", verts, faces, mat_hair, subsurf=2)

    # groom: strands combed from the crown back and down over the same shell
    lines = []
    for _ in range(1200):
        a = rnd.uniform(0, TAU)
        t0 = rnd.uniform(0.22, 0.62)
        line = []
        for k in range(9):
            u = k / 8
            t = bl.lerp(t0, 1.0, u)
            front = max(0.0, -math.sin(a))
            back = max(0.0, math.sin(a))
            z = bl.lerp(Z_CROWN, hairline_z(a), t ** 0.92)
            rx, ry, dy = skull(z)
            thick = (0.0098 + 0.0050 * back) * math.sin(min(1.0, t * 1.9) * math.pi / 2) ** 0.8
            sweep = 0.006 * u * u * back
            x = math.cos(a) * (rx + thick) + sweep * 0.25
            y = math.sin(a) * (ry + thick) + dy + sweep
            line.append((x, y, z + 0.0016 * math.sin(u * math.pi)))
        lines.append(line)
    strands = bl.strands("Hair · groom", lines, 0.00040, mat_sheen, sides=3)

    # thin sideburns in front of the ears
    sides = []
    for sgn in (1, -1):
        for _ in range(90):
            z0 = rnd.uniform(1.7060, 1.7400)
            line = []
            for k in range(6):
                u = k / 5
                z = z0 - 0.034 * u
                rx, ry, dy = skull(z)
                line.append(((rx + 0.003) * sgn * 0.98, -0.026 + 0.014 * u, z))
            sides.append(line)
    side_obj = bl.strands("Sideburns", sides, 0.0005, mat_sheen, sides=3)
    return [cap, strands, side_obj]


def build_beard(mat_hair):
    """Short beard + moustache, 3D fibres on the measured lower face."""
    rnd = random.Random(11)
    skin = srgb(SKIN)
    lines = []
    for _ in range(3400):
        z = rnd.uniform(1.5410, 1.6160)
        # beard band: jaw and chin, thin up the cheeks, thicker at the chin
        half_w = 0.070 * min(1.0, (z - 1.526) / 0.076) ** 0.6
        if z > 1.598 and rnd.random() < 0.55:
            continue
        x = rnd.uniform(-half_w, half_w)
        if abs(x) < 0.026 and z > 1.588 and z < 1.604:
            continue                     # keep the lips clear
        ry = 0.0780
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
               mat_shoe, mat_sole, mat_lapel, mat_face_skin):
    parts = []
    torso = bl.loft("Blazer · torso", [
        ((0, 0, 0.858), 0.174, 0.112),
        ((0, 0, 0.905), 0.170, 0.110),
        ((0, 0.002, 0.980), 0.166, 0.109),
        ((0, 0.004, 1.060), 0.160, 0.106),
        ((0, 0.004, 1.120), 0.156, 0.104),
        ((0, 0.002, 1.200), 0.163, 0.107),
        ((0, 0.000, 1.280), 0.176, 0.113),
        ((0, -0.002, 1.330), 0.174, 0.111),
        ((0, -0.002, 1.368), 0.172, 0.110),
        ((0, -0.001, 1.396), 0.158, 0.104),
        ((0, 0.001, 1.420), 0.122, 0.090),
        ((0, 0.003, 1.444), 0.080, 0.072),
        ((0, 0.005, 1.462), 0.056, 0.055),
    ], mat_blazer, subsurf=2, close_start=True, close_end=False)
    bl.bump_material(mat_blazer, scale=1400, strength=0.12)
    parts.append(torso)

    # shirt: a dark column that shows through the blazer's V
    shirt = bl.loft("Shirt", [
        ((0, 0.004, 0.990), 0.104, 0.104),
        ((0, 0.002, 1.120), 0.110, 0.106),
        ((0, 0.000, 1.260), 0.118, 0.110),
        ((0, -0.003, 1.360), 0.126, 0.114),
        ((0, -0.002, 1.434), 0.122, 0.110),
        ((0, 0.002, 1.468), 0.092, 0.084),
    ], mat_shirt, subsurf=2)
    parts.append(shirt)

    # the open blazer front, as a patch that sits just proud of the chest:
    # a V of shirt with a lapel edge either side. No wrapping maths, no flaps.
    patch = [
        (-0.086, -0.100, 1.446), (0.086, -0.100, 1.446),      # across the shoulders
        (0.060, -0.106, 1.386), (-0.060, -0.106, 1.386),
        (0.030, -0.110, 1.334), (-0.030, -0.110, 1.334),
        (0.000, -0.113, 1.286),                                # the V point
    ]
    v = patch
    f = [(0, 1, 2, 3), (3, 2, 4, 5), (5, 4, 6)]
    vpatch = bl.mesh_object("Shirt V", v, f, mat_shirt, smooth=True)
    sol = vpatch.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.004
    parts.append(vpatch)
    for sgn in (1, -1):
        lap_v = [(0.086 * sgn, -0.100, 1.446), (0.104 * sgn, -0.096, 1.436),
                 (0.070 * sgn, -0.104, 1.384), (0.048 * sgn, -0.108, 1.340),
                 (0.014 * sgn, -0.112, 1.292)]
        lap_f = [(0, 1, 2, 3), (3, 2, 4)]
        lap = bl.mesh_object(f"Lapel.{sgn}", lap_v, lap_f, mat_lapel, smooth=True)
        sol2 = lap.modifiers.new("Solidify", "SOLIDIFY")
        sol2.thickness = 0.005
        parts.append(lap)

    # no separate collar tube: the blazer's own top rings read as the neckline
    collar = None

    # sleeves + hands
    for s, sx in (("L", 1.0), ("R", -1.0)):
        upper = bl.loft(f"Sleeve upper.{s}", [
            ((0.120 * sx, -0.002, 1.408), 0.062, 0.060),
            ((0.158 * sx, -0.001, 1.398), 0.060, 0.058),
            ((0.208 * sx, 0.006, 1.300), 0.055, 0.053),
            ((0.219 * sx, 0.010, 1.180), 0.050, 0.049),
            ((0.225 * sx, 0.012, 1.150), 0.053, 0.052),
        ], mat_blazer, subsurf=2, close_start=True, close_end=False)
        parts.append(upper)
        fore = bl.loft(f"Sleeve fore.{s}", [
            ((0.222 * sx, 0.012, 1.155), 0.049, 0.048),
            ((0.229 * sx, 0.016, 1.075), 0.045, 0.044),
            ((0.234 * sx, 0.019, 1.010), 0.042, 0.041),
            ((0.236 * sx, 0.020, 0.988), 0.040, 0.039),
        ], mat_blazer, subsurf=2, close_start=False, close_end=False)
        parts.append(fore)
        cuff = bl.loft(f"Cuff.{s}", [
            ((0.238 * sx, 0.020, 0.994), 0.043, 0.042),
            ((0.239 * sx, 0.020, 0.978), 0.042, 0.041),
        ], mat_edge, subsurf=1, close_start=False, close_end=False)
        parts.append(cuff)
        parts += build_hand(f"hand.{s}", 0.240 * sx, 0.020, 0.976, sx, mat_face_skin)
        parts.append(bl.loft(f"Elbow.{s}", [
            ((0.225 * sx, 0.010, 1.170), 0.050, 0.049),
            ((0.226 * sx, 0.012, 1.150), 0.054, 0.053),
            ((0.227 * sx, 0.014, 1.130), 0.051, 0.050),
        ], mat_blazer, subsurf=2))

    # pelvis: a single tapered block the thighs grow out of, no visible slab edge
    parts.append(bl.loft("Trouser pelvis", [
        ((0, 0, 1.020), 0.162, 0.104),
        ((0, 0, 0.985), 0.168, 0.107),
        ((0, 0.001, 0.940), 0.172, 0.108),
        ((0, 0.002, 0.900), 0.170, 0.106),
        ((0, 0.002, 0.868), 0.163, 0.102),
        ((0, 0.002, 0.840), 0.152, 0.097),
    ], mat_trouser, subsurf=2, close_start=True, close_end=False))

    # legs
    for s, sx in (("L", 1.0), ("R", -1.0)):
        thigh = bl.loft(f"Trouser thigh.{s}", [
            ((0.090 * sx, 0, 0.960), 0.090, 0.088),
            ((0.096 * sx, 0, 0.880), 0.084, 0.082),
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
    for ob in (torso, shirt):
        bl.bind(ob, rig, bl.ramp_weights(torso_stops, axis=2, softness=1.4))
    for ob in parts:
        if ob.name.startswith(("Lapel", "Shirt V")):
            bl.bind(ob, rig, bl.ramp_weights(
                [(0.90, "spine"), (1.06, "spine"), (1.24, "chest"), (1.47, "chest")],
                axis=2, softness=1.3))
        elif ob.name.startswith(("Lapel_old",)):
            bl.bind(ob, rig, bl.ramp_weights([(1.25, "chest"), (1.47, "chest")], axis=2))
        elif ob.name.startswith(("Sleeve upper", "Elbow")):
            side = ob.name[-1]
            bl.bind(ob, rig, bl.ramp_weights(
                [(1.12, f"forearm.{side}"), (1.20, f"upper_arm.{side}"),
                 (1.40, f"upper_arm.{side}"), (1.46, "chest")], axis=2, softness=0.9))
        elif ob.name.startswith("Sleeve fore"):
            side = ob.name[-1]
            bl.bind(ob, rig, bl.ramp_weights(
                [(0.94, f"hand.{side}"), (1.02, f"forearm.{side}")], axis=2))
        elif ob.name.startswith("Cuff"):
            bl.bind(ob, rig, {f"forearm.{ob.name[-1]}": 1.0})
        elif ob.name.startswith(("Hand", "Fingers", "Thumb")):
            side = ob.name.split(".")[-1]
            if ob.name.startswith("Fingers"):
                bl.bind(ob, rig, {f"fingers.{side}": 0.72, f"hand.{side}": 0.28})
            elif ob.name.startswith("Thumb"):
                bl.bind(ob, rig, {f"hand.{side}": 0.75, f"fingers.{side}": 0.25})
            else:
                bl.bind(ob, rig, {f"hand.{side}": 1.0})
        elif ob.name.startswith("Trouser pelvis"):
            bl.bind(ob, rig, bl.ramp_weights(
                [(0.80, "hips"), (1.02, "spine")], axis=2, softness=1.2))
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
    """Palm + a curled-four-finger mass + a thumb. At these frame sizes a mitten
    reads as a hand; separate cylinders read as forks."""
    tag = bone_side.split(".")[-1]
    palm = bl.loft(f"Hand palm.{tag}", [
        ((x, y, z + 0.004), 0.032, 0.015),
        ((x + 0.002 * sx, y, z - 0.028), 0.037, 0.016),
        ((x + 0.004 * sx, y, z - 0.058), 0.036, 0.015),
        ((x + 0.006 * sx, y - 0.002, z - 0.080), 0.030, 0.013),
    ], mat, subsurf=2, close_start=False, close_end=True)
    # finger mass: a rounded block that tapers, with two shallow grooves suggested
    # by the profile rather than modelled as separate digits
    fingers = bl.loft(f"Fingers.{tag}", [
        ((x + 0.006 * sx, y - 0.002, z - 0.078), 0.029, 0.0125),
        ((x + 0.007 * sx, y - 0.004, z - 0.098), 0.028, 0.0120),
        ((x + 0.008 * sx, y - 0.006, z - 0.118), 0.025, 0.0105),
        ((x + 0.008 * sx, y - 0.007, z - 0.132), 0.019, 0.0085),
        ((x + 0.008 * sx, y - 0.007, z - 0.138), 0.010, 0.0050),
    ], mat, subsurf=2, close_start=False, close_end=True)
    thumb = bl.loft(f"Thumb.{tag}", [
        ((x + 0.026 * sx, y - 0.008, z - 0.026), 0.011, 0.010),
        ((x + 0.031 * sx, y - 0.014, z - 0.048), 0.010, 0.009),
        ((x + 0.033 * sx, y - 0.019, z - 0.066), 0.008, 0.007),
        ((x + 0.033 * sx, y - 0.021, z - 0.074), 0.004, 0.004),
    ], mat, subsurf=2, close_start=True, close_end=True)
    return palm, fingers, thumb


# ------------------------------------------------------------------ assemble
def build_character():
    m_face = bl.material("MONARCH skin · v5 projected", base=SKIN_CAPTURE, rough=0.52,
                         spec=0.30, sss=0.05, sss_radius=(0.9, 0.32, 0.2),
                         sss_scale=0.0035)
    tex = bl.image_texture(m_face, ASSETS / "face_tex.png")
    tex.extension = "EXTEND"
    bl.bump_material(m_face, scale=2600, strength=0.09)

    m_skin = bl.material("MONARCH skin", base=SKIN, rough=0.46, spec=0.40,
                         sss=0.05, sss_scale=0.003)
    m_face_skin = bl.material("MONARCH skin · capture tone", base=SKIN_CAPTURE,
                              rough=0.50, spec=0.32, sss=0.05, sss_scale=0.003)
    m_hair = bl.material("MONARCH hair", base="#171717", rough=0.52, spec=0.28, sheen=0.45)
    m_sheen = bl.material("MONARCH hair sheen", base="#121212", rough=0.42, spec=0.42)
    m_blazer = bl.material("MONARCH blazer", base="#1E1E1D", rough=0.80, spec=0.24,
                           sheen=0.18)
    m_edge = bl.material("MONARCH blazer edge", base=BLAZER_EDGE, rough=0.62, spec=0.4,
                         sheen=0.2)
    m_shirt = bl.material("MONARCH shirt", base=SHIRT, rough=0.68, spec=0.3, sheen=0.15)
    m_trouser = bl.material("MONARCH trousers", base=TROUSERS, rough=0.76, spec=0.28)
    m_shoe = bl.material("MONARCH sneakers", base=SNEAKER, rough=0.36, spec=0.5, coat=0.2)
    m_sole = bl.material("MONARCH soles", base=SOLE, rough=0.62, spec=0.3)
    m_lapel = bl.material("MONARCH lapel", base="#232322", rough=0.78, spec=0.22,
                          sheen=0.15)

    rig = build_rig()
    head, neck, ears = build_head(m_face_skin, m_face)
    hair = build_hair(m_hair, m_sheen)
    beard = build_beard(m_hair)
    body = build_body(rig, m_blazer, m_edge, m_shirt, m_trouser, m_skin, m_shoe,
                      m_sole, m_lapel, m_face_skin)

    for ob in (head, neck, beard):
        bl.bind(ob, rig, {"head": 1.0})
    for e in ears:
        bl.bind(e, rig, {"head": 1.0})
    for ob in hair:
        bl.bind(ob, rig, {"head": 1.0})

    rig.location = (0, 0, 0)
    return dict(rig=rig, head=head, neck=neck, hair=hair, beard=beard, body=body,
                materials=dict(blazer=m_blazer, skin=m_skin, hair=m_hair))
