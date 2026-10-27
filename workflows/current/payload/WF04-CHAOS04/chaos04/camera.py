"""Camera evaluation: one camera object per segment, cuts bound to markers."""
from __future__ import annotations

import math

import bpy
from mathutils import Euler, Quaternion, Vector

from . import bl
from .bl import ease, ease_io, lerp, wobble
from . import direct


def _skip(seg, frame):
    return (frame - seg["start"]) / max(1, (seg["end"] - seg["start"]))


def eval_camera(seg, frame, char_pos=None, seed=0):
    spec = seg["cam"]
    kind = spec["kind"]
    u = _skip(seg, frame)
    e = ease_io(u)
    pos = None
    target = None

    if kind in {"lerp", "whip"}:
        pos = bl.vlerp(spec["p0"], spec["p1"], e)
        if spec.get("t0") is not None:
            target = bl.vlerp(spec["t0"], spec.get("t1", spec["t0"]), e)
    elif kind == "orbit":
        c = Vector(spec["center"])
        a = math.radians(lerp(spec["a0"], spec["a1"], e))
        r = lerp(spec["r0"], spec["r1"], e)
        h = lerp(spec["h0"], spec["h1"], e)
        pos = Vector((c.x + math.sin(a) * r, c.y - math.cos(a) * r, h))
        target = Vector(spec["target"])
    elif kind == "follow":
        if char_pos is not None:
            off = Vector(spec["follow"])
            pos = char_pos + off
            target = char_pos + Vector(spec["char_off"])
        else:
            pos = Vector((0, -48, 1.3))
            target = Vector((0, -46, 1.3))
    elif kind == "static":
        pos = Vector(spec["p"])
        target = Vector(spec["t"])
    else:
        raise ValueError(kind)

    lens = lerp(spec.get("lens0", 50), spec.get("lens1", spec.get("lens0", 50)), e)
    fstop = spec.get("fstop", 2.8)
    focus_point = Vector(spec.get("focus", target))

    # handheld: low-frequency wobble, bigger on whip/chaos shots
    amp = spec.get("shake", 0.0)
    t = frame / 30.0
    sx = wobble(seed + 1, t, freq=1.0) * amp
    sy = wobble(seed + 2, t, freq=1.0) * amp
    sz = wobble(seed + 3, t, freq=1.0) * amp * 0.6
    pos = pos + Vector((sx, sy, sz)) * 0.0016

    if kind == "whip":
        yaw = math.radians(lerp(spec["yaw0"], spec["yaw1"], ease_io(u) ** 0.55))
        base = (target - pos)
        rot = Euler((0, 0, yaw)).to_matrix()
        target = pos + (rot @ base)

    direction = (target - pos)
    if direction.length < 1e-6:
        direction = Vector((0, 1, 0))
    q = direction.to_track_quat("-Z", "Y")
    roll = math.radians(lerp(spec.get("roll0", 0.0), spec.get("roll1", 0.0), e))
    shake_q = Euler((math.radians(sx * amp * 0.55), math.radians(sy * amp * 0.55),
                     roll + math.radians(sz * amp * 0.35)), "XYZ").to_quaternion()
    q = q @ shake_q
    focus = (focus_point - pos).length
    return dict(loc=pos, quat=q, lens=lens, fstop=fstop, focus=focus)


def make_cameras(scene):
    """One camera per segment; cut points are timeline markers bound to cameras."""
    cams = {}
    for i, seg in enumerate(direct.SEGMENTS):
        name = f"CAM {seg['id']} {seg['name']}"
        data = bpy.data.cameras.new(name)
        data.sensor_fit = "AUTO"
        data.sensor_width = 36.0
        data.clip_start = 0.02
        data.clip_end = 120.0
        data.dof.use_dof = True
        data.dof.aperture_blades = 7
        ob = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(ob)
        cams[seg["id"]] = ob

    # bake every frame of every camera, so cuts are exact and shake is reproducible
    frames = range(1, 1333)
    for i, seg in enumerate(direct.SEGMENTS):
        cam = cams[seg["id"]]
        locs, quats, lenses, fstops, focuses = [], [], [], [], []
        for f in frames:
            ff = min(max(f, seg["start"]), seg["end"] - 1)
            char_pos = None
            if seg.get("char"):
                cp, yaw = direct.char_world(seg, f)
                char_pos = cp
            ev = eval_camera(seg, ff, char_pos, seed=i * 7)
            locs.append(ev["loc"])
            quats.append(ev["quat"])
            lenses.append(ev["lens"])
            fstops.append(ev["fstop"])
            focuses.append(max(0.05, ev["focus"]))
        cam.rotation_mode = "QUATERNION"
        bl.bake_vector(cam, "location", list(frames), locs)
        bl.bake_vector(cam, "rotation_quaternion", list(frames), quats)
        bl.bake_curve(cam.data, "lens", 0, list(frames), lenses)
        bl.bake_curve(cam.data, "dof.aperture_fstop", 0, list(frames), fstops)
        bl.bake_curve(cam.data, "dof.focus_distance", 0, list(frames), focuses)

    # markers decide which camera is live
    scene.timeline_markers.clear()
    for seg in direct.SEGMENTS:
        m = scene.timeline_markers.new(seg["id"], frame=seg["start"])
        m.camera = cams[seg["id"]]
    scene.camera = cams[direct.SEGMENTS[0]["id"]]
    return cams
