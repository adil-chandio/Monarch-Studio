#!/usr/bin/env python3
"""
CHAOS · NEXT FILM — v3 true-3D
G1: SHOTLIST builder.

Source of truth for timing = analysis/ARC_STATS.json ``cut_times`` (171 real cuts,
measured from decoded reference frames). We do NOT copy pixels: we rebuild the
same rhythm, act structure and mood with our own 3D character and our own sets.

Output: v3/SHOTLIST_3D.json   (171 shots, frames 0..1331, 30 fps, 1332 frames)
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

PAYLOAD = Path(__file__).resolve().parent.parent
ANALYSIS = PAYLOAD / "analysis" / "ARC_STATS.json"
OUT = Path(__file__).resolve().parent / "SHOTLIST_3D.json"

FPS = 30
FRAMES = 1332  # 44.40 s

# ---------------------------------------------------------------- act map ----
# Boundaries taken from INSPECTION.md (measured, not guessed).
ACTS = [
    dict(id="A1", name="hall_reveal", f0=0, f1=289,
         feel="two long wides, no cutting, only drift", luma_target=9.4),
    dict(id="A2", name="doorway_figure", f0=289, f1=489,
         feel="figure in doorway, scarlet practical, long hold", luma_target=19.0),
    dict(id="A3", name="masked_closeups", f0=489, f1=876,
         feel="masked hero, crescent visor, rapid cutting begins", luma_target=27.0),
    dict(id="A4", name="doorway_hold", f0=876, f1=987,
         feel="3.7 s breathe: wide doorway, red floor light", luma_target=20.0),
    dict(id="A5", name="climax", f0=987, f1=1275,
         feel="fastest cutting, blade reveal, red strobes, overhead", luma_target=29.0),
    dict(id="A6", name="end_card", f0=1275, f1=1332,
         feel="OUR OWN outro card (reference's IG card is replaced, never reused)", luma_target=8.0),
]

# Which 3D set-up each act draws from. A setup = camera rig + light state + subject pose.
SETUPS = {
    "A1": ["hall_wide_a", "hall_wide_a"],
    "A2": ["doorway_wide", "doorway_wide", "hall_wide_b"],
    "A3": ["masked_cu_low", "masked_cu_high", "masked_profile", "tie_detail",
           "visor_insert", "masked_cu_low", "masked_cu_high"],
    "A4": ["doorway_hold"],
    "A5": ["climax_blade", "climax_overhead", "climax_strobe", "climax_whip",
           "masked_cu_low", "climax_blade", "climax_overhead", "climax_strobe"],
    "A6": ["end_card"],
}

MOTION = {  # motion vocabulary per setup -> (kind, strength)
    "hall_wide_a": ("drift", 1.0),
    "hall_wide_b": ("drift", 0.6),
    "doorway_wide": ("push", 0.5),
    "doorway_hold": ("push", 0.25),
    "masked_cu_low": ("handheld_push", 0.9),
    "masked_cu_high": ("handheld_pull", 0.8),
    "masked_profile": ("orbit", 0.7),
    "tie_detail": ("handheld_push", 0.5),
    "visor_insert": ("push", 0.4),
    "climax_blade": ("whip", 1.0),
    "climax_overhead": ("crane", 0.9),
    "climax_strobe": ("shake", 1.0),
    "climax_whip": ("whip", 1.2),
    "end_card": ("static", 0.0),
}


def act_for_frame(f: int) -> dict:
    for a in ACTS:
        if a["f0"] <= f < a["f1"]:
            return a
    return ACTS[-1]


def main() -> int:
    stats = json.loads(ANALYSIS.read_text())
    cut_times = list(stats["cut_times"])
    assert stats["frames"] == FRAMES, stats["frames"]

    # Cut frames from measured times. Only cuts inside acts A2..A5 are honoured;
    # A1 is intentionally cut-free and A6 is our own end card.
    cut_frames = sorted({int(round(t * FPS)) for t in cut_times})
    cut_frames = [f for f in cut_frames if 289 < f < 1275]

    act_cuts = sorted({a["f0"] for a in ACTS[1:]} | {a["f1"] for a in ACTS})
    bounds = [0] + sorted(set(cut_frames) | set(act_cuts)) + [FRAMES]
    # merge any <1 frame slivers so every shot is renderable
    merged = [bounds[0]]
    for b in bounds[1:]:
        if b - merged[-1] >= 2:
            merged.append(b)
    if merged[-1] != FRAMES:
        merged[-1] = FRAMES

    rng = random.Random(20261026)
    shots = []
    for i in range(len(merged) - 1):
        f0, f1 = merged[i], merged[i + 1]
        act = act_for_frame(f0)
        pool = SETUPS[act["id"]]
        setup = pool[i % len(pool)] if act["id"] != "A1" else ("hall_wide_a" if i == 0 else "hall_wide_b")
        if act["id"] == "A6":
            setup = "end_card"
        kind, strength = MOTION[setup]
        shots.append(dict(
            idx=i, shot=f"{act['id']}_{i:03d}",
            act=act["id"], f0=f0, f1=f1, frames=f1 - f0,
            dur=round((f1 - f0) / FPS, 3),
            setup=setup, motion=kind, motion_strength=strength,
            seed=rng.randrange(1, 2 ** 31),
            luma_target=act["luma_target"],
        ))

    # sanity: contiguous coverage, no gaps, exact frame count
    assert shots[0]["f0"] == 0 and shots[-1]["f1"] == FRAMES
    for a, b in zip(shots, shots[1:]):
        assert a["f1"] == b["f0"], (a["shot"], b["shot"])
    total = sum(s["frames"] for s in shots)

    doc = dict(
        schema_version=2,
        kind="wf04_chaos_v3_shotlist",
        generated_by="v3/build_shotlist.py",
        rights=("Timing derived from measured cut instances of the supplied reference "
                "(structure only). No reference pixels, audio or assets are used; every "
                "frame is rendered from our own 3D scene and our own score."),
        fps=FPS, frames=FRAMES, duration=round(FRAMES / FPS, 3),
        resolution=[1080, 1920], preview_resolution=[405, 720],
        acts=ACTS,
        measured_cuts=len(cut_frames),
        shots=shots,
        totals=dict(shots=len(shots), frames=total),
    )
    OUT.write_text(json.dumps(doc, indent=1))
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    long_shots = [s for s in shots if s["frames"] >= 60]
    print(f"SHOTLIST ok  shots={len(shots)} frames={total} cuts={len(cut_frames)}")
    print(f"  holds(>=2s): {len(long_shots)} -> " +
          ", ".join(f"{s['shot']}({s['dur']}s)" for s in long_shots))
    print("  per-act: " + ", ".join(
        f"{a['id']}={sum(1 for s in shots if s['act'] == a['id'])}" for a in ACTS))
    print(f"  sha256={digest[:16]}…  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
