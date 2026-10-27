"""Direction: all 24 segments, their cameras, and what Monarch does in each.

Timeline (30 fps, 1332 frames) is pinned to the measured reference grid:
act I 0-13.27, act II 13.27-39.50, act III 39.50-44.55, strobes every 0.50 s
(120 BPM half-beats). Shot 20 holds the measured sub-cuts at 34.12 / 34.88 /
35.75 / 36.50 s as its own camera beats.
"""
from __future__ import annotations

import math
import random

from .mathx import TAU, ease, ease_io, lerp, smoothstep, wobble
from .spaces import CORRIDOR, ENDCARD, ROOM, VOID

DOOR = (0.0, 2.50, 0.0)          # where Monarch stands in the room
GATE = (0.0, -0.55, 0.0)         # the frame gate


def F(t: float) -> int:
    """seconds → blender frame (1-based)."""
    return int(round(t * 30)) + 1


SEGMENTS = [
    # ---------------- ACT I : the room ----------------
    dict(id="01", start=1, end=57, set="room", name="Room, push in",
         char=None,
         cam=dict(kind="lerp", p0=(0.62, -2.05, 1.30), p1=(-0.18, 0.95, 1.52),
                  t0=(0.05, 2.4, 1.15), t1=(0.0, 2.2, 1.28),
                  lens0=26, lens1=30, fstop=2.8, focus=(0, 2.2, 1.3), shake=0.30),
         exposure=-0.25, lights=dict(door_glow=3400, rim_teal=520, rim_amber=430,
                                     practical=240, key=150, fill=70)),
    dict(id="02", start=57, end=112, set="room", name="Practical / floor",
         char=None,
         cam=dict(kind="lerp", p0=(2.05, -0.55, 1.62), p1=(1.62, 0.35, 1.12),
                  t0=(1.30, 0.85, 2.22), t1=(0.55, 0.35, 0.10),
                  lens0=50, lens1=58, fstop=2.0, focus=(1.3, 0.85, 2.2), shake=0.22),
         exposure=-0.35, lights=dict(door_glow=900, rim_teal=380, rim_amber=520,
                                     practical=420, key=90, fill=60)),
    dict(id="03", start=112, end=168, set="room", name="Doorway glow",
         char=None,
         cam=dict(kind="lerp", p0=(0.0, -0.75, 1.45), p1=(0.0, 0.15, 1.38),
                  t0=(0.0, 2.75, 1.42), t1=(0.0, 2.75, 1.30),
                  lens0=62, lens1=68, fstop=2.2, focus=(0, 2.75, 1.3), shake=0.18),
         exposure=0.10, lights=dict(door_glow=4200, rim_teal=260, rim_amber=220,
                                    practical=120, key=60, fill=40)),
    dict(id="04", start=168, end=223, set="room", name="Rack / steel macro",
         char=None,
         cam=dict(kind="orbit", center=(-2.30, 1.05, 1.05), r0=1.15, r1=0.72,
                  a0=-52, a1=18, h0=1.25, h1=1.05, target=(-2.30, 1.05, 1.10),
                  lens0=48, lens1=54, fstop=2.4, shake=0.26),
         exposure=-0.30, lights=dict(door_glow=1200, rim_teal=700, rim_amber=180,
                                     practical=160, key=120, fill=60)),
    dict(id="05", start=223, end=280, set="room", name="First silhouette",
         char=dict(pos=(0.0, 2.48, 0.0), yaw=4, pose="door"),
         cam=dict(kind="lerp", p0=(0.10, -0.30, 1.40), p1=(0.02, -0.10, 1.44),
                  t0=(0.0, 2.48, 1.30), t1=(0.0, 2.46, 1.34),
                  lens0=78, lens1=85, fstop=1.8, focus=(0, 2.48, 1.55), shake=0.16),
         exposure=-0.05, lights=dict(door_glow=3600, rim_teal=520, rim_amber=250,
                                     practical=90, key=40, fill=30)),
    dict(id="06", start=280, end=337, set="room", name="Hand to lapel",
         char=dict(pos=(0.0, 2.44, 0.0), yaw=-6, pose="lapel"),
         cam=dict(kind="lerp", p0=(0.42, 1.35, 1.52), p1=(0.30, 1.16, 1.44),
                  t0=(0.02, 2.40, 1.34), t1=(0.0, 2.36, 1.30),
                  lens0=82, lens1=95, fstop=1.5, focus=(0, 2.40, 1.35), shake=0.24),
         exposure=-0.12, lights=dict(door_glow=2200, rim_teal=760, rim_amber=420,
                                     practical=150, key=90, fill=40)),
    dict(id="07", start=337, end=399, set="room", name="Back of the head",
         char=dict(pos=(0.0, 2.44, 0.0), yaw=178, pose="back"),
         cam=dict(kind="lerp", p0=(0.46, 1.22, 1.56), p1=(0.30, 1.06, 1.50),
                  t0=(0.0, 2.52, 1.68), t1=(0.0, 2.50, 1.66),
                  lens0=92, lens1=104, fstop=1.6, focus=(0, 2.48, 1.68), shake=0.20),
         exposure=-0.20, lights=dict(door_glow=4000, rim_teal=420, rim_amber=640,
                                     practical=70, key=30, fill=25)),

    # ---------------- ACT II : escalation ----------------
    dict(id="08", start=399, end=489, set="room", name="Halo hero",
         char=dict(pos=(0.0, 2.42, 0.0), yaw=6, pose="halo"),
         cam=dict(kind="orbit", center=(0.0, 2.42, 1.42), r0=1.95, r1=1.72,
                  a0=-16, a1=10, h0=1.44, h1=1.30, target=(0.0, 2.42, 1.50),
                  lens0=76, lens1=86, fstop=1.7, shake=0.18),
         exposure=0.05, lights=dict(door_glow=4600, rim_teal=680, rim_amber=520,
                                    practical=110, key=45, fill=35)),
    dict(id="09", start=489, end=519, set="room", name="Eyes open",
         char=dict(pos=(0.0, 2.42, 0.0), yaw=2, pose="halo", head_turn=6),
         cam=dict(kind="lerp", p0=(0.30, 1.60, 1.62), p1=(0.20, 1.52, 1.62),
                  t0=(0.0, 2.40, 1.655), t1=(0.0, 2.40, 1.655),
                  lens0=92, lens1=104, fstop=1.3, focus=(0, 2.40, 1.655), shake=0.30),
         exposure=-0.05, lights=dict(door_glow=1800, rim_teal=900, rim_amber=700,
                                     practical=140, key=170, fill=55)),
    dict(id="10", start=519, end=541, set="room", name="Six arms",
         char=dict(pos=(0.0, 0.35, 0.0), yaw=0, pose="six"),
         cam=dict(kind="lerp", p0=(0.0, -1.62, 0.72), p1=(0.0, -1.48, 0.80),
                  t0=(0.0, 0.35, 1.30), t1=(0.0, 0.35, 1.34),
                  lens0=38, lens1=40, fstop=2.2, focus=(0, 0.35, 1.2), shake=0.42),
         exposure=-0.10, lights=dict(door_glow=700, rim_teal=1500, rim_amber=900,
                                     practical=60, key=60, fill=30), brood=1.0),
    dict(id="11", start=541, end=560, set="room", name="Brood face",
         char=dict(pos=(0.0, 0.35, 0.0), yaw=0, pose="six", head_turn=-4),
         cam=dict(kind="lerp", p0=(0.20, -0.34, 1.62), p1=(0.12, -0.26, 1.62),
                  t0=(0.0, 0.36, 1.650), t1=(0.0, 0.36, 1.652),
                  lens0=95, lens1=108, fstop=1.15, focus=(0, 0.36, 1.65), shake=0.55),
         exposure=-0.02, lights=dict(door_glow=260, rim_teal=1800, rim_amber=1200,
                                     practical=40, key=220, fill=25), brood=1.0),
    dict(id="12", start=560, end=582, set="room", name="Doorway, floor pool",
         char=dict(pos=(0.0, 2.50, 0.0), yaw=2, pose="door"),
         cam=dict(kind="lerp", p0=(0.95, -2.25, 1.10), p1=(0.70, -1.85, 0.86),
                  t0=(0.0, 2.10, 1.10), t1=(0.0, 2.20, 1.05),
                  lens0=30, lens1=32, fstop=2.8, focus=(0, 2.4, 1.2), shake=0.38),
         exposure=-0.18, lights=dict(door_glow=3400, rim_teal=420, rim_amber=880,
                                     practical=260, key=50, fill=60)),
    dict(id="13", start=582, end=616, set="room", name="Neon doorway pull",
         char=dict(pos=(0.0, 2.50, 0.0), yaw=0, pose="door"),
         cam=dict(kind="lerp", p0=(0.0, 1.05, 1.46), p1=(0.0, -0.85, 1.44),
                  t0=(0.0, 2.50, 1.38), t1=(0.0, 2.50, 1.34),
                  lens0=44, lens1=52, fstop=2.0, focus=(0, 2.50, 1.4), shake=0.26),
         exposure=0.0, lights=dict(door_glow=3800, rim_teal=820, rim_amber=420,
                                   practical=140, key=70, fill=45)),
    dict(id="14", start=616, end=732, set="corridor", name="Corridor walk",
         char=dict(pos=(0.05, -50.6, 0.0), yaw=0, pose="walk", walk_from=-50.6,
                   walk_to=-46.4, walk_frames=(616, 733)),
         cam=dict(kind="follow", follow=(-0.34, -2.35, 1.30), char_off=(0, 0, 1.30),
                  lens0=42, lens1=38, fstop=2.2, shake=0.34, aim="chest"),
         exposure=-0.12, lights=dict(corr0=210, corr1=210, corr2=210, corr3=210, corr4=210)),
    dict(id="15", start=732, end=766, set="corridor", name="Spark whip",
         char=dict(pos=(0.0, -46.0, 0.0), yaw=0, pose="door"),
         cam=dict(kind="whip", p0=(0.0, -44.2, 1.42), p1=(0.0, -44.6, 1.36),
                  yaw0=-58, yaw1=52, t0=(0.0, -46.0, 1.45), lens0=34, lens1=38,
                  fstop=2.4, shake=0.7),
         exposure=-0.05, lights=dict(corr0=90, corr1=30, corr2=320, corr3=120, corr4=60),
         sparks=1.0),
    dict(id="16", start=766, end=789, set="corridor", name="Halo blur",
         char=dict(pos=(0.0, -45.4, 0.0), yaw=-10, pose="halo"),
         cam=dict(kind="lerp", p0=(0.30, -46.9, 1.60), p1=(0.16, -46.35, 1.52),
                  t0=(0.0, -45.4, 1.55), t1=(0.0, -45.4, 1.52),
                  lens0=88, lens1=104, fstop=1.2, focus=(0, -45.4, 1.55), shake=0.95,
                  roll0=-6, roll1=7),
         exposure=0.08, lights=dict(corr0=260, corr1=520, corr2=120, corr3=380, corr4=90)),
    dict(id="17", start=789, end=830, set="room", name="In frame",
         char=dict(pos=(0.0, -0.55, 0.0), yaw=0, pose="halo"),
         cam=dict(kind="lerp", p0=(0.0, -2.85, 1.34), p1=(0.0, -2.45, 1.30),
                  t0=(0.0, -0.55, 1.24), t1=(0.0, -0.55, 1.26),
                  lens0=40, lens1=44, fstop=2.4, focus=(0, -0.55, 1.2), shake=0.22),
         exposure=-0.20, lights=dict(door_glow=1500, rim_teal=900, rim_amber=600,
                                     practical=120, key=110, fill=40)),
    dict(id="18", start=830, end=867, set="room", name="Tendril macro",
         char=dict(pos=(0.0, 0.10, 0.0), yaw=-14, pose="six"),
         cam=dict(kind="lerp", p0=(0.60, -0.55, 1.62), p1=(0.42, -0.30, 1.50),
                  t0=(0.18, 0.25, 1.52), t1=(0.14, 0.20, 1.46),
                  lens0=100, lens1=112, fstop=1.2, focus=(0.1, 0.2, 1.5), shake=0.40),
         exposure=-0.12, lights=dict(door_glow=400, rim_teal=1600, rim_amber=1100,
                                     practical=30, key=120, fill=20), tendril=1.0),
    dict(id="19", start=867, end=987, set="room", name="Framed wide",
         char=dict(pos=(0.0, -0.55, 0.0), yaw=0, pose="halo"),
         cam=dict(kind="lerp", p0=(0.0, 2.60, 1.52), p1=(0.0, 1.05, 1.46),
                  t0=(0.0, -0.55, 1.20), t1=(0.0, -0.55, 1.24),
                  lens0=34, lens1=40, fstop=2.6, focus=(0, -0.55, 1.2), shake=0.30),
         exposure=-0.15, lights=dict(door_glow=2600, rim_teal=760, rim_amber=520,
                                     practical=90, key=80, fill=30)),
    # shot 20 — measured sub-cuts at 34.12 / 34.88 / 35.75 / 36.50
    dict(id="20a", start=987, end=1025, set="room", name="Amber close",
         char=dict(pos=(0.0, 2.44, 0.0), yaw=-3, pose="six", head_turn=4),
         cam=dict(kind="lerp", p0=(0.24, 1.62, 1.62), p1=(0.14, 1.44, 1.60),
                  t0=(0.0, 2.42, 1.63), t1=(0.0, 2.40, 1.64),
                  lens0=100, lens1=112, fstop=1.2, focus=(0, 2.4, 1.64), shake=0.48),
         exposure=0.0, lights=dict(door_glow=900, rim_teal=900, rim_amber=1600,
                                   practical=220, key=200, fill=30)),
    dict(id="20b", start=1025, end=1047, set="room", name="Hand to lens",
         char=dict(pos=(0.0, 1.75, 0.0), yaw=0, pose="hand_cam"),
         cam=dict(kind="lerp", p0=(0.05, 0.72, 1.52), p1=(0.02, 0.60, 1.50),
                  t0=(0.0, 1.78, 1.48), t1=(0.0, 1.76, 1.47),
                  lens0=64, lens1=72, fstop=1.6, focus=(0, 1.78, 1.48), shake=0.6),
         exposure=-0.05, lights=dict(door_glow=1300, rim_teal=1200, rim_amber=700,
                                     practical=160, key=260, fill=30)),
    dict(id="20c", start=1047, end=1074, set="void", name="White void",
         char=dict(pos=(60.0, 0.0, 0.0), yaw=0, pose="six"),
         cam=dict(kind="lerp", p0=(60.6, -2.90, 1.30), p1=(60.3, -2.30, 1.20),
                  t0=(60.0, 0.0, 1.30), t1=(60.0, 0.0, 1.28),
                  lens0=44, lens1=52, fstop=2.6, focus=(60.0, 0.0, 1.3), shake=0.5),
         exposure=-0.6, lights=dict(void_key=400)),
    dict(id="20d", start=1074, end=1096, set="room", name="Wide, small figure",
         char=dict(pos=(0.0, 2.30, 0.0), yaw=6, pose="halo"),
         cam=dict(kind="lerp", p0=(1.95, -2.30, 1.62), p1=(1.70, -2.05, 1.50),
                  t0=(0.0, 2.20, 1.20), t1=(0.0, 2.15, 1.22),
                  lens0=30, lens1=33, fstop=2.8, focus=(0, 2.3, 1.3), shake=0.34),
         exposure=-0.2, lights=dict(door_glow=3000, rim_teal=520, rim_amber=760,
                                    practical=140, key=60, fill=40)),
    dict(id="20e", start=1096, end=1186, set="room", name="Strobe close",
         char=dict(pos=(0.0, 2.30, 0.0), yaw=-2, pose="six", head_turn=-3),
         cam=dict(kind="lerp", p0=(0.20, 1.42, 1.60), p1=(0.10, 1.28, 1.58),
                  t0=(0.0, 2.30, 1.63), t1=(0.0, 2.30, 1.64),
                  lens0=96, lens1=108, fstop=1.25, focus=(0, 2.3, 1.64), shake=0.7),
         exposure=-0.02, lights=dict(door_glow=700, rim_teal=1400, rim_amber=1200,
                                     practical=200, key=240, fill=25)),

    # ---------------- ACT III : out ----------------
    dict(id="21", start=1186, end=1211, set="void", name="Flash out",
         char=dict(pos=(60.0, 0.0, 0.0), yaw=0, pose="six"),
         cam=dict(kind="lerp", p0=(60.0, -3.40, 1.32), p1=(60.0, -2.95, 1.28),
                  t0=(60.0, 0.0, 1.30), t1=(60.0, 0.0, 1.30),
                  lens0=40, lens1=46, fstop=2.8, focus=(60.0, 0.0, 1.3), shake=0.30),
         exposure=-0.35, lights=dict(void_key=400)),
    dict(id="22", start=1211, end=1229, set="black", name="Silence, black",
         char=None,
         cam=dict(kind="static", p=(0.0, -61.0, 1.30), t=(0.0, -59.0, 1.30),
                  lens0=50, fstop=8.0, shake=0.0),
         exposure=-6.0, lights={}),
    dict(id="23", start=1229, end=1264, set="endcard", name="Emblem on",
         char=None,
         cam=dict(kind="lerp", p0=(-60.0, -1.30, 1.42), p1=(-60.0, -0.95, 1.415),
                  t0=(-60.0, 2.0, 1.42), t1=(-60.0, 2.0, 1.415),
                  lens0=72, lens1=78, fstop=2.0, focus=(-60, 2.0, 1.42), shake=0.0),
         exposure=-0.10, lights=dict(endcard_fill=40)),
    dict(id="24", start=1264, end=1333, set="endcard", name="Our endcard",
         char=None,
         cam=dict(kind="lerp", p0=(-60.0, -0.86, 1.30), p1=(-60.0, -0.80, 1.30),
                  t0=(-60.0, 2.0, 1.30), t1=(-60.0, 2.0, 1.30),
                  lens0=80, lens1=80, fstop=2.0, focus=(-60, 2.0, 1.30), shake=0.0),
         exposure=-0.10, lights=dict(endcard_fill=40)),
]

assert sum(s["end"] - s["start"] for s in SEGMENTS) == 1332, \
    sum(s["end"] - s["start"] for s in SEGMENTS)
assert SEGMENTS[0]["start"] == 1 and SEGMENTS[-1]["end"] == 1333


def segment_at(frame: int) -> dict:
    for s in SEGMENTS:
        if s["start"] <= frame < s["end"]:
            return s
    return SEGMENTS[-1]


# ---------------------------------------------------------------- performance
# angles are armature-space degrees: +X leans forward, +Z twists left.
POSES = {
    "door": dict(
        spine=(2, 0, 0), chest=(1, 0, 0), neck=(-2, 0, 0), head=(-3, 0, 4),
        upper_arm_l=(4, -6, 0), upper_arm_r=(4, 6, 0),
        forearm_l=(-8, 0, 0), forearm_r=(-8, 0, 0),
        hand_l=(-4, 0, 0), hand_r=(-4, 0, 0),
        fingers_l=(-10, 0, 0), fingers_r=(-10, 0, 0),
        thigh_l=(1, 0, 2), thigh_r=(1, 0, -2), shin_l=(-2, 0, 0), shin_r=(-2, 0, 0),
    ),
    "lapel": dict(
        spine=(3, 0, 2), chest=(2, 0, 3), neck=(-3, 0, -4), head=(-4, 0, -8),
        upper_arm_r=(-46, 12, -6), forearm_r=(-72, 0, 14), hand_r=(-18, 0, 10),
        fingers_r=(-38, 0, 0),
        upper_arm_l=(5, -7, 0), forearm_l=(-10, 0, 0), hand_l=(-5, 0, 0),
        fingers_l=(-12, 0, 0),
        thigh_l=(1, 0, 2), thigh_r=(1, 0, -2), shin_l=(-2, 0, 0), shin_r=(-2, 0, 0),
    ),
    "back": dict(
        spine=(-2, 0, 0), chest=(-2, 0, 0), neck=(3, 0, 0), head=(6, 0, -6),
        upper_arm_l=(6, -9, 0), upper_arm_r=(6, 9, 0),
        forearm_l=(-6, 0, 0), forearm_r=(-6, 0, 0),
        hand_l=(-3, 0, 0), hand_r=(-3, 0, 0),
        fingers_l=(-8, 0, 0), fingers_r=(-8, 0, 0),
        thigh_l=(0, 0, 2), thigh_r=(0, 0, -2), shin_l=(0, 0, 0), shin_r=(0, 0, 0),
    ),
    "halo": dict(
        spine=(-1, 0, 0), chest=(2, 0, 0), neck=(2, 0, 2), head=(3, 0, 1),
        upper_arm_l=(8, -13, 0), upper_arm_r=(8, 13, 0),
        forearm_l=(-12, 0, -4), forearm_r=(-12, 0, 4),
        hand_l=(-6, 0, 0), hand_r=(-6, 0, 0),
        fingers_l=(-14, 0, 0), fingers_r=(-14, 0, 0),
        thigh_l=(0, 0, 3), thigh_r=(0, 0, -3), shin_l=(-1, 0, 0), shin_r=(-1, 0, 0),
    ),
    "six": dict(
        spine=(-3, 0, 0), chest=(-4, 0, 0), neck=(4, 0, 0), head=(6, 0, 0),
        upper_arm_l=(14, -34, -6), upper_arm_r=(14, 34, 6),
        forearm_l=(-24, 0, -18), forearm_r=(-24, 0, 18),
        hand_l=(-10, 0, 0), hand_r=(-10, 0, 0),
        fingers_l=(-26, 0, 0), fingers_r=(-26, 0, 0),
        thigh_l=(0, 0, 4), thigh_r=(0, 0, -4), shin_l=(-2, 0, 0), shin_r=(-2, 0, 0),
    ),
    "hand_cam": dict(
        spine=(2, 0, 3), chest=(1, 0, 4), neck=(-2, 0, -3), head=(-4, 0, -6),
        upper_arm_r=(-72, 16, -10), forearm_r=(-46, 0, 20), hand_r=(-24, 0, 12),
        fingers_r=(6, 0, 0),
        upper_arm_l=(6, -8, 0), forearm_l=(-12, 0, 0), hand_l=(-6, 0, 0),
        fingers_l=(-14, 0, 0),
        thigh_l=(1, 0, 2), thigh_r=(1, 0, -2), shin_l=(-2, 0, 0), shin_r=(-2, 0, 0),
    ),
}

BONE_MAP = {
    "spine": "spine", "chest": "chest", "neck": "neck", "head": "head",
    "hips": "hips",
    "upper_arm_l": "upper_arm.L", "upper_arm_r": "upper_arm.R",
    "forearm_l": "forearm.L", "forearm_r": "forearm.R",
    "hand_l": "hand.L", "hand_r": "hand.R",
    "fingers_l": "fingers.L", "fingers_r": "fingers.R",
    "thigh_l": "thigh.L", "thigh_r": "thigh.R",
    "shin_l": "shin.L", "shin_r": "shin.R",
    "foot_l": "foot.L", "foot_r": "foot.R",
}


def _walk_pose(u: float):
    """u in 0..1 over the walk: a real contact-down-passing-up cycle, twice."""
    ph = u * TAU * 2.0
    swing = math.sin(ph)
    lift = max(0.0, math.sin(ph + math.pi / 2))
    p = dict(POSES["halo"])
    p["thigh_l"] = (-22 * swing, 0, 3)
    p["thigh_r"] = (22 * swing, 0, -3)
    p["shin_l"] = (30 * lift + 6, 0, 0)
    p["shin_r"] = (30 * max(0.0, -math.sin(ph + math.pi / 2)) + 6, 0, 0)
    p["foot_l"] = (-12 * swing, 0, 0)
    p["foot_r"] = (12 * swing, 0, 0)
    p["upper_arm_l"] = (14 * swing, -11, 0)
    p["upper_arm_r"] = (-14 * swing, 11, 0)
    p["forearm_l"] = (-16 - 8 * max(0, swing), 0, -4)
    p["forearm_r"] = (-16 + 8 * min(0, swing), 0, 4)
    p["hips"] = (0, 0, -5 * swing)
    p["chest"] = (2, 0, 6 * swing)
    return p


def pose_for(seg, frame):
    spec = seg.get("char")
    if not spec:
        return None
    u = (frame - seg["start"]) / max(1, (seg["end"] - seg["start"]))
    name = spec.get("pose", "door")
    if name == "walk":
        base = _walk_pose(u)
    else:
        base = dict(POSES[name])
    t = frame / 30.0
    breath = 1.1 * math.sin(TAU * 0.28 * t)
    sway = 0.9 * math.sin(TAU * 0.17 * t + 1.1)
    out = {}
    for k, v in base.items():
        out[k] = v
    # living detail on top of the chosen pose
    out["chest"] = (base.get("chest", (0, 0, 0))[0] + breath * 0.8,
                    base.get("chest", (0, 0, 0))[1] + sway * 0.5,
                    base.get("chest", (0, 0, 0))[2])
    out["spine"] = (base.get("spine", (0, 0, 0))[0] + breath * 0.4,
                    base.get("spine", (0, 0, 0))[1] - sway * 0.4,
                    base.get("spine", (0, 0, 0))[2])
    ht = spec.get("head_turn", 0)
    head = base.get("head", (0, 0, 0))
    out["head"] = (head[0] + 1.4 * math.sin(TAU * 0.21 * t + 0.6),
                   head[1] + 1.0 * math.sin(TAU * 0.13 * t),
                   head[2] + ht + 1.8 * math.sin(TAU * 0.11 * t + 2.0))
    out["neck"] = (base.get("neck", (0, 0, 0))[0],
                   base.get("neck", (0, 0, 0))[1] + 0.6 * sway,
                   base.get("neck", (0, 0, 0))[2])
    return out


def char_world(seg, frame):
    from mathutils import Vector
    spec = seg.get("char")
    if not spec:
        return None
    pos = Vector(spec["pos"])
    yaw = spec.get("yaw", 0.0)
    if spec.get("pose") == "walk" and "walk_from" in spec:
        a, b = spec["walk_frames"]
        u = min(1.0, max(0.0, (frame - a) / max(1, (b - a))))
        pos.y = lerp(spec["walk_from"], spec["walk_to"], u)
        pos.x += 0.02 * math.sin(u * TAU * 4)
    return pos, yaw
