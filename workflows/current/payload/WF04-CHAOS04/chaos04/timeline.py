"""CHAOS 04 — timeline. 30 fps, 1332 frames, 44.55 s.

Frame numbers come straight from the measured reference:
`ref_v4/BEAT_MAP.json` (8 fps motion analysis) and `STRUCTURE_v4.md`.

Blender frames are 1-based; `end` is exclusive, so a shot is `range(start, end)`.
Sum of (end-start) over SHOTS == TOTAL_FRAMES.
"""
from __future__ import annotations

FPS = 30
TOTAL_FRAMES = 1332
DURATION_S = 44.55

# reference strobe grid (seconds) — measured, 0.50 s spacing = 120 BPM half-beats
FLASH_TIMES = [
    9.12, 9.62, 13.12,
    16.25, 16.75, 17.25, 17.75, 18.50, 19.25, 20.50, 21.00, 21.50, 22.12,
    22.62, 23.12, 23.75, 24.25, 25.12, 25.62, 26.25, 26.75, 27.25, 28.00,
    28.50, 29.12, 31.12, 32.12, 32.88, 33.50, 34.12, 34.62, 35.12, 35.75,
    36.25, 36.75, 37.38, 37.88, 38.38, 39.38, 39.88,
]

# measured soft cuts (seconds)
CUT_TIMES = [16.25, 17.25, 18.00, 18.62, 19.38, 20.50, 24.38, 25.50, 26.25,
             27.62, 28.88, 32.88, 34.12, 34.88, 35.75, 36.50, 39.50]

SILENCE_GAPS = [(40.34, 40.93), (42.10, 44.55)]

SHOTS = [
    dict(id="01", name="Room, push in", start=1, end=57, set="room"),
    dict(id="02", name="Practical / floor", start=57, end=112, set="room"),
    dict(id="03", name="Doorway glow", start=112, end=168, set="room"),
    dict(id="04", name="Rack / steel macro", start=168, end=223, set="room"),
    dict(id="05", name="First silhouette", start=223, end=280, set="room"),
    dict(id="06", name="Hand to lapel", start=280, end=337, set="room"),
    dict(id="07", name="Back of the head", start=337, end=399, set="room"),
    dict(id="08", name="Halo hero", start=399, end=489, set="room"),
    dict(id="09", name="Eyes open", start=489, end=519, set="room"),
    dict(id="10", name="Six arms", start=519, end=541, set="room"),
    dict(id="11", name="Brood face", start=541, end=560, set="room"),
    dict(id="12", name="Doorway, floor pool", start=560, end=582, set="room"),
    dict(id="13", name="Neon doorway pull", start=582, end=616, set="room"),
    dict(id="14", name="Corridor walk", start=616, end=732, set="corridor"),
    dict(id="15", name="Spark whip", start=732, end=766, set="corridor"),
    dict(id="16", name="Halo blur", start=766, end=789, set="corridor"),
    dict(id="17", name="In frame", start=789, end=830, set="room"),
    dict(id="18", name="Tendril macro", start=830, end=867, set="room"),
    dict(id="19", name="Framed wide", start=867, end=987, set="room"),
    dict(id="20a", name="Amber close", start=987, end=1025, set="room"),
    dict(id="20b", name="Hand to lens", start=1025, end=1047, set="room"),
    dict(id="20c", name="White void", start=1047, end=1074, set="void"),
    dict(id="20d", name="Wide, small figure", start=1074, end=1096, set="room"),
    dict(id="20e", name="Strobe close", start=1096, end=1186, set="room"),
    dict(id="21", name="Flash out", start=1186, end=1211, set="void"),
    dict(id="22", name="Silence, black", start=1211, end=1229, set="black"),
    dict(id="23", name="Emblem on", start=1229, end=1264, set="endcard"),
    dict(id="24", name="Our endcard", start=1264, end=1333, set="endcard"),
]

assert sum(s["end"] - s["start"] for s in SHOTS) == TOTAL_FRAMES, \
    sum(s["end"] - s["start"] for s in SHOTS)


def shot_at(frame: int) -> dict:
    for s in SHOTS:
        if s["start"] <= frame < s["end"]:
            return s
    return SHOTS[-1]


def frames(step: int = 1):
    return list(range(1, TOTAL_FRAMES + 1, step))


def flash_frames():
    return sorted({max(1, min(TOTAL_FRAMES, int(round(t * FPS)) + 1)) for t in FLASH_TIMES})


def cut_frames():
    return sorted({max(1, min(TOTAL_FRAMES, int(round(t * FPS)) + 1)) for t in CUT_TIMES})
