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
         exposure=-0.8, lights=dict(door_glow=612, rim_teal=94, rim_amber=77,
                                     practical=43, key=27, fill=13)),
    dict(id="02", start=57, end=112, set="room", name="Practical / floor",
         char=None,
         cam=dict(kind="lerp", p0=(2.05, -0.55, 1.62), p1=(1.62, 0.35, 1.12),
                  t0=(1.30, 0.85, 2.22), t1=(0.55, 0.35, 0.10),
                  lens0=50, lens1=58, fstop=2.0, focus=(1.3, 0.85, 2.2), shake=0.22),
         world=0.1, world_color="#101A1D", exposure=0.9, lights=dict(door_glow=240, rack_key=0, floor_pool=2600, practical=160, key=200, fill=90)),
    dict(id="03", start=112, end=168, set="room", name="Doorway glow",
         char=None,
         cam=dict(kind="lerp", p0=(0.34, -1.35, 1.50), p1=(0.10, -0.30, 1.42),
                  t0=(0.0, 2.78, 1.34), t1=(0.0, 2.78, 1.26),
                  lens0=34, lens1=40, fstop=2.2, focus=(0, 2.75, 1.3), shake=0.18),
         world=0.05, world_color="#0C1518", exposure=-1.1, lights=dict(door_glow=900, rim_teal=90, rim_amber=70, practical=60, key=110, fill=50)),
    dict(id="04", start=168, end=223, set="room", name="Rack / steel macro",
         char=None,
         cam=dict(kind="orbit", center=(-1.95, 0.75, 1.12), r0=0.95, r1=0.66,
                  a0=-34, a1=22, h0=1.24, h1=1.04, target=(-2.20, 0.85, 1.16),
                  lens0=40, lens1=48, fstop=2.0, shake=0.22),
         world=0.18, world_color="#16262A", exposure=0.35, lights=dict(door_glow=200, rack_key=900, rim_teal=260, practical=90, key=160, fill=60)),
    dict(id="05", start=223, end=280, set="room", name="First silhouette",
         char=dict(pos=(0.0, 2.48, 0.0), yaw=4, pose="door"),
         cam=dict(kind="lerp", p0=(0.10, -0.30, 1.40), p1=(0.02, -0.10, 1.44),
                  t0=(0.0, 2.48, 1.30), t1=(0.0, 2.46, 1.34),
                  lens0=78, lens1=85, fstop=1.8, focus=(0, 2.48, 1.55), shake=0.16),
         exposure=-0.6, lights=dict(door_glow=648, rim_teal=94, rim_amber=45,
                                     practical=16, key=7, fill=5)),
    dict(id="06", start=280, end=337, set="room", name="Hand to lapel",
         char=dict(pos=(0.0, 2.44, 0.0), yaw=-6, pose="lapel"),
         cam=dict(kind="lerp", p0=(0.42, 1.35, 1.52), p1=(0.30, 1.16, 1.44),
                  t0=(0.02, 2.40, 1.34), t1=(0.0, 2.36, 1.30),
                  lens0=82, lens1=95, fstop=1.5, focus=(0, 2.40, 1.35), shake=0.24),
         exposure=-0.67, lights=dict(door_glow=396, rim_teal=137, rim_amber=76,
                                     practical=27, key=16, fill=7)),
    dict(id="07", start=337, end=399, set="room", name="Back of the head",
         char=dict(pos=(0.0, 2.44, 0.0), yaw=178, pose="back"),
         cam=dict(kind="lerp", p0=(0.46, 1.22, 1.56), p1=(0.30, 1.06, 1.50),
                  t0=(0.0, 2.52, 1.68), t1=(0.0, 2.50, 1.66),
                  lens0=92, lens1=104, fstop=1.6, focus=(0, 2.48, 1.68), shake=0.20),
         exposure=-0.75, lights=dict(door_glow=720, rim_teal=76, rim_amber=115,
                                     practical=13, key=5, fill=4)),

    # ---------------- ACT II : escalation ----------------
    dict(id="08", start=399, end=489, set="room", name="Halo hero",
         char=dict(pos=(0.0, 2.42, 0.0), yaw=6, pose="halo"),
         cam=dict(kind="orbit", center=(0.0, 2.42, 1.42), r0=1.95, r1=1.72,
                  a0=-16, a1=10, h0=1.44, h1=1.30, target=(0.0, 2.42, 1.50),
                  lens0=76, lens1=86, fstop=1.7, shake=0.18),
         exposure=-0.5, lights=dict(door_glow=828, rim_teal=122, rim_amber=94,
                                    practical=20, key=8, fill=6)),
    dict(id="09", start=489, end=519, set="room", name="Eyes open",
         char=dict(pos=(0.0, 2.42, 0.0), yaw=2, pose="halo", head_turn=6),
         cam=dict(kind="lerp", p0=(0.30, 1.60, 1.62), p1=(0.20, 1.52, 1.62),
                  t0=(0.0, 2.40, 1.655), t1=(0.0, 2.40, 1.655),
                  lens0=92, lens1=104, fstop=1.3, focus=(0, 2.40, 1.655), shake=0.30),
         exposure=-0.6, lights=dict(door_glow=324, rim_teal=162, rim_amber=126,
                                     practical=25, key=31, fill=10)),
    dict(id="10", start=519, end=541, set="room", name="Six arms",
         char=dict(pos=(0.0, 0.35, 0.0), yaw=0, pose="six"),
         cam=dict(kind="lerp", p0=(0.0, -1.62, 0.72), p1=(0.0, -1.48, 0.80),
                  t0=(0.0, 0.35, 1.30), t1=(0.0, 0.35, 1.34),
                  lens0=38, lens1=40, fstop=2.2, focus=(0, 0.35, 1.2), shake=0.42),
         exposure=-0.65, lights=dict(door_glow=126, rim_teal=270, rim_amber=162,
                                     practical=11, key=11, fill=5), brood=1.0),
    dict(id="11", start=541, end=560, set="room", name="Brood face",
         char=dict(pos=(0.0, 0.35, 0.0), yaw=0, pose="six", head_turn=-4),
         cam=dict(kind="lerp", p0=(0.20, -0.34, 1.62), p1=(0.12, -0.26, 1.62),
                  t0=(0.0, 0.36, 1.650), t1=(0.0, 0.36, 1.652),
                  lens0=95, lens1=108, fstop=1.15, focus=(0, 0.36, 1.65), shake=0.55),
         exposure=0.3, lights=dict(door_glow=140, rim_teal=460, rim_amber=320,
                                     practical=24, key=180, fill=50), brood=1.0),
    dict(id="12", start=560, end=582, set="room", name="Doorway, floor pool",
         char=dict(pos=(0.0, 2.50, 0.0), yaw=2, pose="door"),
         cam=dict(kind="lerp", p0=(0.95, -2.25, 1.10), p1=(0.70, -1.85, 0.86),
                  t0=(0.0, 2.10, 1.10), t1=(0.0, 2.20, 1.05),
                  lens0=30, lens1=32, fstop=2.8, focus=(0, 2.4, 1.2), shake=0.38),
         exposure=-0.73, lights=dict(door_glow=612, rim_teal=76, rim_amber=158,
                                     practical=47, key=9, fill=11)),
    dict(id="13", start=582, end=616, set="room", name="Neon doorway pull",
         char=dict(pos=(0.0, 2.50, 0.0), yaw=0, pose="door"),
         cam=dict(kind="lerp", p0=(0.0, 1.05, 1.46), p1=(0.0, -0.85, 1.44),
                  t0=(0.0, 2.50, 1.38), t1=(0.0, 2.50, 1.34),
                  lens0=44, lens1=52, fstop=2.0, focus=(0, 2.50, 1.4), shake=0.26),
         exposure=-0.55, lights=dict(door_glow=684, rim_teal=148, rim_amber=76,
                                   practical=25, key=13, fill=8)),
    dict(id="14", start=616, end=732, set="corridor", name="Corridor walk",
         char=dict(pos=(0.05, -49.2, 0.0), yaw=0, pose="walk", walk_from=-49.2,
                   walk_to=-45.4, walk_frames=(616, 733)),
         cam=dict(kind="follow", follow=(-0.34, -2.10, 1.30), char_off=(0, 0, 1.30),
                  lens0=42, lens1=38, fstop=2.2, shake=0.34, aim="chest"),
         world=1.15, world_color="#22383D", exposure=-0.15, lights=dict(corr0=620, corr1=620, corr2=700, corr3=620, corr4=520, corr_fill=500, corr_end=900)),
    dict(id="15", start=732, end=766, set="corridor", name="Spark whip",
         char=dict(pos=(0.0, -45.6, 0.0), yaw=0, pose="door"),
         cam=dict(kind="whip", p0=(0.0, -43.9, 1.42), p1=(0.0, -44.3, 1.36),
                  yaw0=-58, yaw1=52, t0=(0.0, -45.6, 1.45), lens0=34, lens1=38,
                  fstop=2.4, shake=0.7),
         world=1.3, world_color="#2A4046", exposure=0.05, lights=dict(corr0=300, corr1=120, corr2=700, corr3=260, corr4=120, corr_fill=300, corr_end=600),
         sparks=1.0),
    dict(id="16", start=766, end=789, set="corridor", name="Halo blur",
         char=dict(pos=(0.0, -45.2, 0.0), yaw=-10, pose="halo"),
         cam=dict(kind="lerp", p0=(0.30, -46.7, 1.60), p1=(0.16, -46.15, 1.52),
                  t0=(0.0, -45.2, 1.55), t1=(0.0, -45.2, 1.52),
                  lens0=88, lens1=104, fstop=1.2, focus=(0, -45.2, 1.55), shake=0.95,
                  roll0=-6, roll1=7),
         world=1.1, world_color="#1E3338", exposure=-0.05, lights=dict(corr0=520, corr1=640, corr2=240, corr3=520, corr4=180, corr_fill=420, corr_end=400)),
    dict(id="17", start=789, end=830, set="room", name="In frame",
         char=dict(pos=(0.0, -0.55, 0.0), yaw=0, pose="halo"),
         cam=dict(kind="lerp", p0=(0.0, -2.85, 1.34), p1=(0.0, -2.45, 1.30),
                  t0=(0.0, -0.55, 1.24), t1=(0.0, -0.55, 1.26),
                  lens0=40, lens1=44, fstop=2.4, focus=(0, -0.55, 1.2), shake=0.22),
         world=0.14, world_color="#152427", exposure=0.3, lights=dict(door_glow=520, rim_teal=300, rim_amber=230, practical=60, key=620, fill=220)),
    dict(id="18", start=830, end=867, set="room", name="Tendril macro",
         char=dict(pos=(0.0, 0.10, 0.0), yaw=-14, pose="six"),
         cam=dict(kind="lerp", p0=(0.52, -0.70, 1.64), p1=(0.40, -0.52, 1.58),
                  t0=(0.02, 0.12, 1.62), t1=(0.02, 0.12, 1.58),
                  lens0=58, lens1=66, fstop=1.6, focus=(0.03, 0.12, 1.60), shake=0.36),
         world=0.12, world_color="#142226", exposure=0.35, lights=dict(door_glow=520, rim_teal=900, rim_amber=600, practical=60, key=520, fill=160), tendril=1.0),
    dict(id="19", start=867, end=987, set="room", name="Framed wide",
         char=dict(pos=(0.0, -0.55, 0.0), yaw=0, pose="halo"),
         cam=dict(kind="lerp", p0=(0.0, 2.60, 1.52), p1=(0.0, 1.05, 1.46),
                  t0=(0.0, -0.55, 1.20), t1=(0.0, -0.55, 1.24),
                  lens0=34, lens1=40, fstop=2.6, focus=(0, -0.55, 1.2), shake=0.30),
         world=0.16, world_color="#16272B", exposure=0.45, lights=dict(door_glow=900, rim_teal=360, rim_amber=280, practical=140, key=600, fill=220)),
    # shot 20 — measured sub-cuts at 34.12 / 34.88 / 35.75 / 36.50
    dict(id="20a", start=987, end=1025, set="room", name="Amber close",
         char=dict(pos=(0.0, 2.44, 0.0), yaw=-3, pose="six", head_turn=4),
         cam=dict(kind="lerp", p0=(0.24, 1.62, 1.62), p1=(0.14, 1.44, 1.60),
                  t0=(0.0, 2.42, 1.63), t1=(0.0, 2.40, 1.64),
                  lens0=100, lens1=112, fstop=1.2, focus=(0, 2.4, 1.64), shake=0.48),
         exposure=-0.55, lights=dict(door_glow=162, rim_teal=162, rim_amber=288,
                                   practical=40, key=36, fill=5)),
    dict(id="20b", start=1025, end=1047, set="room", name="Hand to lens",
         char=dict(pos=(0.0, 1.75, 0.0), yaw=0, pose="hand_cam"),
         cam=dict(kind="lerp", p0=(0.05, 0.72, 1.52), p1=(0.02, 0.60, 1.50),
                  t0=(0.0, 1.78, 1.48), t1=(0.0, 1.76, 1.47),
                  lens0=64, lens1=72, fstop=1.6, focus=(0, 1.78, 1.48), shake=0.6),
         exposure=-0.6, lights=dict(door_glow=234, rim_teal=216, rim_amber=126,
                                     practical=29, key=47, fill=5)),
    dict(id="20c", start=1047, end=1074, set="void", name="White void",
         char=dict(pos=(60.0, 0.0, 0.0), yaw=0, pose="six"),
         cam=dict(kind="lerp", p0=(60.6, -2.90, 1.30), p1=(60.3, -2.30, 1.20),
                  t0=(60.0, 0.0, 1.30), t1=(60.0, 0.0, 1.28),
                  lens0=44, lens1=52, fstop=2.6, focus=(60.0, 0.0, 1.3), shake=0.5),
         exposure=-2.20, lights=dict(void_key=160)),
    dict(id="20d", start=1074, end=1096, set="room", name="Wide, small figure",
         char=dict(pos=(0.0, 2.30, 0.0), yaw=6, pose="halo"),
         cam=dict(kind="lerp", p0=(1.95, -2.30, 1.62), p1=(1.70, -2.05, 1.50),
                  t0=(0.0, 2.20, 1.20), t1=(0.0, 2.15, 1.22),
                  lens0=30, lens1=33, fstop=2.8, focus=(0, 2.3, 1.3), shake=0.34),
         exposure=-0.75, lights=dict(door_glow=540, rim_teal=94, rim_amber=137,
                                    practical=25, key=11, fill=7)),
    dict(id="20e", start=1096, end=1186, set="room", name="Strobe close",
         char=dict(pos=(0.0, 2.30, 0.0), yaw=-2, pose="six", head_turn=-3),
         cam=dict(kind="lerp", p0=(0.20, 1.42, 1.60), p1=(0.10, 1.28, 1.58),
                  t0=(0.0, 2.30, 1.63), t1=(0.0, 2.30, 1.64),
                  lens0=96, lens1=108, fstop=1.25, focus=(0, 2.3, 1.64), shake=0.7),
         exposure=-0.57, lights=dict(door_glow=126, rim_teal=252, rim_amber=216,
                                     practical=36, key=43, fill=4)),

    # ---------------- ACT III : out ----------------
    dict(id="21", start=1186, end=1211, set="void", name="Flash out",
         char=dict(pos=(60.0, 0.0, 0.0), yaw=0, pose="six"),
         cam=dict(kind="lerp", p0=(60.0, -3.40, 1.32), p1=(60.0, -2.95, 1.28),
                  t0=(60.0, 0.0, 1.30), t1=(60.0, 0.0, 1.30),
                  lens0=40, lens1=46, fstop=2.8, focus=(60.0, 0.0, 1.3), shake=0.30),
         exposure=-1.60, lights=dict(void_key=120)),
    dict(id="22", start=1211, end=1229, set="black", name="Silence, black",
         char=None,
         cam=dict(kind="static", p=(0.0, -160.0, 1.30), t=(0.0, -150.0, 1.30),
                  lens0=50, fstop=8.0, shake=0.0),
         exposure=-1.0, lights={}),
    dict(id="23", start=1229, end=1264, set="endcard", name="Emblem on",
         char=None,
         cam=dict(kind="lerp", p0=(-59.94, -1.55, 1.40), p1=(-59.94, -1.36, 1.40),
                  t0=(-60.0, 2.0, 1.44), t1=(-60.0, 2.0, 1.44),
                  lens0=62, lens1=62, fstop=2.8, focus=(-60, 2.0, 1.45), shake=0.0),
         exposure=-0.65, lights=dict(endcard_fill=7)),
    dict(id="24", start=1264, end=1333, set="endcard", name="Our endcard",
         char=None,
         cam=dict(kind="lerp", p0=(-60.06, -2.45, 1.42), p1=(-60.06, -2.20, 1.42),
                  t0=(-60.0, 2.0, 1.43), t1=(-60.0, 2.0, 1.43),
                  lens0=54, lens1=54, fstop=2.8, focus=(-60, 2.0, 1.43), shake=0.0),
         exposure=-0.55, lights=dict(endcard_fill=9)),
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
        upper_arm_l=(5, -2, 0), upper_arm_r=(5, 2, 0),
        forearm_l=(-8, 0, 0), forearm_r=(-8, 0, 0),
        hand_l=(-4, 0, 0), hand_r=(-4, 0, 0),
        fingers_l=(-10, 0, 0), fingers_r=(-10, 0, 0),
        thigh_l=(1, 0, 2), thigh_r=(1, 0, -2), shin_l=(-2, 0, 0), shin_r=(-2, 0, 0),
    ),
    "lapel": dict(
        spine=(3, 0, 2), chest=(2, 0, 3), neck=(-3, 0, -4), head=(-4, 0, -8),
        upper_arm_r=(-40, 3, -8), forearm_r=(-78, 0, 16), hand_r=(-16, 0, 10),
        fingers_r=(-38, 0, 0),
        upper_arm_l=(6, -2, 0), forearm_l=(-12, 0, 0), hand_l=(-5, 0, 0),
        fingers_l=(-12, 0, 0),
        thigh_l=(1, 0, 2), thigh_r=(1, 0, -2), shin_l=(-2, 0, 0), shin_r=(-2, 0, 0),
    ),
    "back": dict(
        spine=(-2, 0, 0), chest=(-2, 0, 0), neck=(3, 0, 0), head=(6, 0, -6),
        upper_arm_l=(7, -3, 0), upper_arm_r=(7, 3, 0),
        forearm_l=(-6, 0, 0), forearm_r=(-6, 0, 0),
        hand_l=(-3, 0, 0), hand_r=(-3, 0, 0),
        fingers_l=(-8, 0, 0), fingers_r=(-8, 0, 0),
        thigh_l=(0, 0, 2), thigh_r=(0, 0, -2), shin_l=(0, 0, 0), shin_r=(0, 0, 0),
    ),
    "halo": dict(
        spine=(-1, 0, 0), chest=(2, 0, 0), neck=(2, 0, 2), head=(3, 0, 1),
        upper_arm_l=(9, -4, 0), upper_arm_r=(9, 4, 0),
        forearm_l=(-16, 0, -5), forearm_r=(-16, 0, 5),
        hand_l=(-6, 0, 0), hand_r=(-6, 0, 0),
        fingers_l=(-14, 0, 0), fingers_r=(-14, 0, 0),
        thigh_l=(0, 0, 3), thigh_r=(0, 0, -3), shin_l=(-1, 0, 0), shin_r=(-1, 0, 0),
    ),
    "six": dict(
        spine=(-3, 0, 0), chest=(-4, 0, 0), neck=(4, 0, 0), head=(6, 0, 0),
        upper_arm_l=(16, -16, -6), upper_arm_r=(16, 16, 6),
        forearm_l=(-30, 0, -16), forearm_r=(-30, 0, 16),
        hand_l=(-10, 0, 0), hand_r=(-10, 0, 0),
        fingers_l=(-26, 0, 0), fingers_r=(-26, 0, 0),
        thigh_l=(0, 0, 4), thigh_r=(0, 0, -4), shin_l=(-2, 0, 0), shin_r=(-2, 0, 0),
    ),
    "hand_cam": dict(
        spine=(2, 0, 3), chest=(1, 0, 4), neck=(-2, 0, -3), head=(-4, 0, -6),
        upper_arm_r=(-72, 16, -10), forearm_r=(-46, 0, 20), hand_r=(-24, 0, 12),
        fingers_r=(6, 0, 0),
        upper_arm_l=(7, -2, 0), forearm_l=(-14, 0, 0), hand_l=(-6, 0, 0),
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
    p["upper_arm_l"] = (14 * swing, -4, 0)
    p["upper_arm_r"] = (-14 * swing, 4, 0)
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
