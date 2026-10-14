#!/usr/bin/env python3
"""WF-04 · Monarch Face · CHAOS VIDEO 3 — "MOTION EDITION" (real movement cut).

Why this cut exists (user, Roman Urdu, 2026-10-15): *"images me real movement lao
na ki yeh jelly type effects add karke do"* — every previous cut moved the
camera and warped still plates, which reads as jelly.  Chaos Video 3 is built on
`motion_engine.py`: authored action keyframes plus occlusion-aware dense flow
(`hop`) so limbs, torso and steps actually travel, and every "alive" layer is a
small local deformation (breathing, stance sway, head drift, blinks, cable sway,
wet-floor ripple) instead of a global wobble.

Same contract as the reference and as v2 (so the audio master, the 8-act
structure and the delivery gates all line up):

    A cold open 1-66 | B throne 67-240 | C walk + chaos proj. 241-420 |
    D triad close-ups 421-582 | E chaos burst 583-780 | F stance 781-990 |
    G finale build 991-1214 | H crowned finale 1215-1336     (1336 f / 44.53 s)

Run:
    bash tools/bootstrap_env.sh
    python3 tools/stage_ref_audio.py /tmp/monarch-stage/ref.mp4 --drive-id 1sYYhXs9fbHeHcQGOmH5IR7CvUSVr9Tmx --md5 42e52d770f6b53338639d2d1a01e2e48
    python3 styles/monarch-face-chaos/src/build_chaos_video3.py --out /tmp/monarch-v3-out
"""

from __future__ import annotations

import argparse
import json
import math
import gc
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_chaos_video1 as v1  # noqa: E402
import build_chaos_video2 as v2  # noqa: E402  (FX layers: glitch, shake, leak, HUD, emblem)
import motion_engine as me  # noqa: E402  (keyframes, dense-flow hops, living-shot micro motion)
from audio_engine2 import build_master_audio  # noqa: E402

W, H, FPS = 1080, 1920, 30
TOTAL_FRAMES = 1336
STYLE_DIR = HERE.parent
RECORDS = STYLE_DIR / "records"
OUT_NAME = "MONARCH_CHAOS_VIDEO_3_MOTION_MASTER.mp4"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FFMPEG = v1.FFMPEG

ACT_TABLE = [
    {"act": "A", "name": "cold open", "start": 1, "end": 66, "seconds": [0.0, 2.17]},
    {"act": "B", "name": "throne rise", "start": 67, "end": 240, "seconds": [2.20, 7.97]},
    {"act": "C", "name": "walk + chaos projection", "start": 241, "end": 420, "seconds": [8.00, 13.97]},
    {"act": "D", "name": "triad close-ups", "start": 421, "end": 582, "seconds": [13.97, 19.37]},
    {"act": "E", "name": "chaos burst", "start": 583, "end": 780, "seconds": [19.40, 25.97]},
    {"act": "F", "name": "sovereign stance", "start": 781, "end": 990, "seconds": [25.97, 32.97]},
    {"act": "G", "name": "finale build", "start": 991, "end": 1214, "seconds": [32.97, 40.47]},
    {"act": "H", "name": "crown finale", "start": 1215, "end": 1336, "seconds": [40.47, 44.53]},
]


# --------------------------------------------------------------------------- #
# FX finishing (face-safe: strobes never erase the hero's face)
# --------------------------------------------------------------------------- #
def finish(frame: np.ndarray, fno: int, fx: dict, grain: float = 1.4) -> np.ndarray:
    frame = frame.astype(np.float32)
    if fx.get("ab", 0) > 0:
        frame = v1.chromatic_aberration(frame, fx["ab"])
    if fx.get("glitch", 0) > 0:
        frame = v2.glitch(frame, fno, fx["glitch"])
    if fx.get("shake", 0) > 0:
        frame = v2.shake(frame, fno, fx["shake"])
    if fx.get("dark", 1.0) != 1.0:
        frame = frame * fx["dark"]
    if fx.get("leak_amt", 0) > 0:
        frame = v2.light_leak(frame, fx["leak"], fx["leak_amt"], fno * 0.05)
    if fx.get("flash_amt", 0) > 0:
        f_map = fx["flash_amt"] * (1.0 - 0.55 * v2.FACE_MASK)
        frame = frame * (1.0 - f_map) + np.array(fx["flash"], np.float32)[None, None, :] * f_map * 1.35
    if fx.get("invert"):
        frame = 255.0 - frame
    frame = v2.apply_vignette_grain(frame, fno, grain)
    if fx.get("hud") is not None:
        frame = v2.hud_overlay(frame, fx["hud"], "MONARCH_OS v5.0 · MOTION ENGINE")
    return frame


def blink_curve(i: int, start: int, period: int) -> float:
    t = (i - start) % period
    if t > 4:
        return 0.0
    return [0.0, 0.45, 0.95, 0.55, 0.15][t]


# --------------------------------------------------------------------------- #
# segment generators: every segment contains real movement
# --------------------------------------------------------------------------- #
def seg_still(name: str, length: int, K: me.Keyframes, *, micro: dict, track: dict | None = None,
              blink_on: bool = False, fx: dict | None = None, grain: float = 1.4, fno0: int = 0):
    """A living shot: one rigid camera move + local micro motion (+ optional blink)."""
    if K.has(name):
        img = K[name]
    else:
        img = K.plate(name if name.endswith(".png") else name + ".png")
    boxes = me.eye_boxes(img) if blink_on else []
    track = track or {}

    def gen():
        for i in range(length):
            t = i / max(1, length - 1)
            z = track.get("zoom0", 1.0) + (track.get("zoom1", track.get("zoom0", 1.0)) - track.get("zoom0", 1.0)) * t
            out = me.micro(img, i, phase=(fno0 % 997) * 0.037, **micro)
            if boxes:
                out = me.blink(out, boxes, blink_curve(i, 12, 96))
            if track:
                out = me.rigid(out, dx=track.get("dx0", 0.0) + (track.get("dx1", 0.0) - track.get("dx0", 0.0)) * t,
                               dy=track.get("dy0", 0.0) + (track.get("dy1", 0.0) - track.get("dy0", 0.0)) * t,
                               zoom=z, rot_deg=track.get("rot", 0.0) * math.sin(i * 0.03))
            yield finish(out, fno0 + i, fx or {}, grain)

    return gen()


def seg_hop(src: str, dst: str, length: int, K: me.Keyframes, *, ease: str = "inout",
            micro: dict | None = None, track: dict | None = None, fx: dict | None = None,
            grain: float = 1.4, fno0: int = 0, hold: int = 0):
    """Real body movement between two authored action keyframes, then an optional hold."""
    a, b = K[src], K[dst]

    def gen():
        for i, frame in enumerate(me.hop(a, b, length, tag=(src, dst), ease=ease)):
            if micro:
                frame = me.micro(frame, i, **micro)
            if track:
                t = i / max(1, length - 1)
                frame = me.rigid(frame, dx=track.get("dx0", 0.0) + (track.get("dx1", 0.0) - track.get("dx0", 0.0)) * t,
                                 dy=track.get("dy0", 0.0) + (track.get("dy1", 0.0) - track.get("dy0", 0.0)) * t,
                                 zoom=track.get("zoom0", 1.0) + (track.get("zoom1", track.get("zoom0", 1.0)) - track.get("zoom0", 1.0)) * t)
            yield finish(frame, fno0 + i, fx or {}, grain)
        if hold:
            for i in range(hold):
                frame = me.micro(b, i, **(micro or {}))
                yield finish(frame, fno0 + length + i, fx or {}, grain)

    return gen()


def seg_emblem(length: int, fno0: int):
    """Crowned MONARCH STUDIO hold with real geometric motion (rotation + chest-beat zoom)."""
    def gen():
        for i in range(length):
            p = i / max(1, length)
            crown = 0.75 + 0.25 * math.sin(p * math.pi * 2.0)
            emb = v2.emblem_frame(1.0, crown, fno0 + i)
            emb = me.rigid(emb, zoom=1.0 + 0.012 * math.sin(p * math.pi * 2.4),
                           rot_deg=0.35 * math.sin(p * math.pi * 1.6))
            if i < 6:  # gold impact: the crowned logo lands hot, then settles
                a = 0.55 - 0.09 * i
                emb = emb * (1.0 - a) + np.full_like(emb, 245.0) * a
            if i >= length - 36:
                emb = emb * (1.0 - 0.42 * ((i - (length - 36)) / 35.0))
            yield finish(emb, fno0 + i, {"hud": None}, 1.2)

    return gen()


def build_timeline(K: me.Keyframes) -> list[tuple[int, callable]]:
    """(length, generator_factory) pairs laid out over the 8 acts; total = 1336."""
    T: list[tuple[int, callable]] = []

    # A — cold open (66)
    T.append((40, lambda n, f: seg_still("plate_wide_hall", n, K, fno0=f,
                                         micro=dict(cable=3.0, ripple=3.6, breathe=0.0016),
                                         track={"zoom0": 1.02, "zoom1": 1.055, "dy0": 6.0, "dy1": -4.0},
                                         fx={"dark": 0.20, "leak": (150, 25, 45), "leak_amt": 0.05, "hud": 8.0})))
    T.append((26, lambda n, f: seg_still("plate_med_red_sil", n, K, fno0=f,
                                         micro=dict(head=0.0035, breathe=0.0035, cable=2.6),
                                         track={"zoom0": 1.0, "zoom1": 1.05},
                                         fx={"dark": 0.40, "leak": (160, 30, 60), "leak_amt": 0.05, "hud": 22.0})))

    # B — throne rise (174): push-in, then a real stand-up hop, then the hold
    T.append((94, lambda n, f: seg_still("s3_throne_f1", n, K, fno0=f,
                                         micro=dict(breathe=0.006, ripple=3.2, cable=2.4, head=0.0022),
                                         track={"zoom0": 1.10, "zoom1": 1.015, "rot": 0.12},
                                         fx={"hud": 34.0, "leak": (170, 25, 30), "leak_amt": 0.08})))
    T.append((48, lambda n, f: seg_hop("s3_throne_f1", "s3_throne_f2", n, K, ease="out", fno0=f,
                                       micro=dict(breathe=0.0035, ripple=3.0),
                                       track={"zoom0": 1.01, "zoom1": 1.0}, fx={"hud": 78.0})))
    T.append((32, lambda n, f: seg_still("s3_throne_f2", n, K, fno0=f,
                                         micro=dict(breathe=0.006, weight=0.0035, ripple=2.4),
                                         track={"zoom0": 1.0, "zoom1": 1.035, "rot": 0.10},
                                         fx={"hud": 100.0, "leak": (170, 25, 30), "leak_amt": 0.09})))

    # C — walk act (real two-step cycles) + burst + pointing snap (180)
    for src, dst in (("s1_walk_f1", "s1_walk_f2"), ("s1_walk_f2", "s1_walk_f1"),
                     ("s1_walk_f1", "s1_walk_f2"), ("s1_walk_f2", "s1_walk_f1")):
        T.append((11, (lambda s, d: lambda n, f: seg_hop(s, d, n, K, ease="inout", fno0=f,
                                                         micro=dict(weight=0.0022, ripple=2.2),
                                                         fx={"ab": 1.2, "leak": (90, 20, 60), "leak_amt": 0.05}))(src, dst)))
    T.append((36, lambda n, f: seg_still("s7_burst_f1", n, K, fno0=f,
                                         micro=dict(breathe=0.007, weight=0.004, ripple=3.4),
                                         track={"zoom0": 1.06, "zoom1": 1.12, "rot": 0.25},
                                         fx={"ab": 2.2, "glitch": 0.22, "shake": 1.4, "leak": (120, 30, 150), "leak_amt": 0.09})))
    T.append((10, lambda n, f: seg_hop("s2_point_f1", "s2_point_f2", n, K, ease="snap", fno0=f,
                                       fx={"ab": 1.4, "leak": (150, 25, 120), "leak_amt": 0.06})))
    T.append((40, lambda n, f: seg_still("s2_point_f2", n, K, fno0=f,
                                         micro=dict(breathe=0.006, head=0.003, weight=0.003),
                                         track={"zoom0": 1.02, "zoom1": 1.07},
                                         fx={"leak": (150, 25, 120), "leak_amt": 0.07})))
    T.append((50, lambda n, f: seg_still("plate_close_cyan", n, K, fno0=f,
                                         micro=dict(head=0.0032, breathe=0.0042, cable=2.2),
                                         track={"zoom0": 1.05, "zoom1": 1.0, "rot": 0.18},
                                         fx={"ab": 1.8, "leak": (60, 120, 190), "leak_amt": 0.08})))

    # D — close-up triad (162): blink + real head turn
    T.append((50, lambda n, f: seg_still("plate_closeup_34", n, K, fno0=f, blink_on=True,
                                         micro=dict(head=0.0034, breathe=0.0042, weight=0.0022),
                                         track={"zoom0": 1.0, "zoom1": 1.045, "rot": 0.10},
                                         fx={"ab": 1.0, "leak": (190, 40, 90), "leak_amt": 0.07})))
    T.append((45, lambda n, f: seg_hop("s6_turn_f0", "s6_turn_f1", n, K, ease="inout", fno0=f,
                                       micro=dict(breathe=0.0035),
                                       fx={"ab": 1.2, "leak": (200, 60, 40), "leak_amt": 0.07})))
    T.append((67, lambda n, f: seg_still("s6_turn_f1", n, K, fno0=f,
                                         micro=dict(head=0.0032, breathe=0.0046, weight=0.002),
                                         track={"zoom0": 1.03, "zoom1": 1.0, "rot": 0.10},
                                         fx={"leak": (200, 60, 40), "leak_amt": 0.06})))

    # E — chaos burst (198): 8-frame cuts, every shot itself moves
    variants = [
        lambda n, f: seg_hop("s1_walk_f1", "s1_walk_f2", n, K, ease="inout", fno0=f, fx={"ab": 2.0, "glitch": 0.18, "shake": 1.2}),
        lambda n, f: seg_still("s7_burst_f1", n, K, fno0=f, micro=dict(breathe=0.008, weight=0.0045),
                               track={"zoom0": 1.04, "zoom1": 1.10}, fx={"glitch": 0.26, "shake": 1.8, "ab": 2.4}),
        lambda n, f: seg_hop("s2_point_f1", "s2_point_f2", n, K, ease="snap", fno0=f, fx={"ab": 1.8, "shake": 1.0}),
        lambda n, f: seg_still("s3_throne_f2", n, K, fno0=f, micro=dict(breathe=0.006, weight=0.003),
                               track={"zoom0": 1.0, "zoom1": 1.06}, fx={"glitch": 0.16, "leak": (180, 30, 30), "leak_amt": 0.08}),
        lambda n, f: seg_hop("s1_walk_f2", "s1_walk_f1", n, K, ease="inout", fno0=f, fx={"ab": 1.6, "shake": 1.1}),
        lambda n, f: seg_still("s6_turn_f1", n, K, fno0=f, micro=dict(head=0.0036, breathe=0.004),
                               track={"zoom0": 1.05, "zoom1": 1.0}, fx={"glitch": 0.12, "ab": 1.4}),
    ]
    for i in range(24):
        T.append((8, variants[i % len(variants)]))
    T.append((6, lambda n, f: seg_still("s7_burst_f1", n, K, fno0=f, micro=dict(breathe=0.008),
                                        fx={"flash": (255, 255, 255), "flash_amt": 0.10, "glitch": 0.3, "shake": 2.0})))

    # F — sovereign stance (210): the pointing snap, hold, lower, stance, walk-off
    T.append((8, lambda n, f: seg_hop("s2_point_f1", "s2_point_f2", n, K, ease="snap", fno0=f, fx={"ab": 1.2})))
    T.append((62, lambda n, f: seg_still("s2_point_f2", n, K, fno0=f,
                                         micro=dict(breathe=0.0065, weight=0.0034, head=0.0024),
                                         track={"zoom0": 1.0, "zoom1": 1.05, "rot": 0.12},
                                         fx={"leak": (150, 25, 120), "leak_amt": 0.06})))
    T.append((10, lambda n, f: seg_hop("s2_point_f2", "s2_point_f1", n, K, ease="inout", fno0=f, fx={"ab": 1.0})))
    T.append((65, lambda n, f: seg_still("s4_guard_f1", n, K, fno0=f,
                                         micro=dict(breathe=0.0068, weight=0.0036, cable=2.4),
                                         track={"zoom0": 1.04, "zoom1": 1.0, "rot": 0.10},
                                         fx={"leak": (90, 40, 170), "leak_amt": 0.07})))
    T.append((65, lambda n, f: seg_hop("s1_walk_f1", "s1_walk_f2", n, K, ease="inout", fno0=f,
                                       micro=dict(weight=0.002), fx={"ab": 1.0, "leak": (90, 30, 60), "leak_amt": 0.05})))

    # G — finale build (224): accelerating cuts, every shot in motion
    g_variants = [
        lambda n, f: seg_hop("s1_walk_f1", "s1_walk_f2", n, K, ease="inout", fno0=f, fx={"ab": 1.6, "shake": 0.8}),
        lambda n, f: seg_hop("s1_walk_f2", "s1_walk_f1", n, K, ease="inout", fno0=f, fx={"ab": 1.6, "shake": 0.8}),
        lambda n, f: seg_still("s7_burst_f1", n, K, fno0=f, micro=dict(breathe=0.009, weight=0.005),
                               track={"zoom0": 1.02, "zoom1": 1.12}, fx={"glitch": 0.28, "shake": 1.6, "ab": 2.2}),
        lambda n, f: seg_hop("s2_point_f1", "s2_point_f2", n, K, ease="snap", fno0=f, fx={"ab": 2.0, "shake": 1.0}),
        lambda n, f: seg_still("s3_throne_f2", n, K, fno0=f, micro=dict(breathe=0.007, weight=0.004),
                               track={"zoom0": 1.0, "zoom1": 1.08}, fx={"glitch": 0.2, "ab": 1.8}),
        lambda n, f: seg_hop("s6_turn_f0", "s6_turn_f1", n, K, ease="inout", fno0=f, fx={"ab": 1.6, "shake": 0.9}),
        lambda n, f: seg_still("s4_guard_f1", n, K, fno0=f, micro=dict(breathe=0.009, weight=0.005),
                               track={"zoom0": 1.06, "zoom1": 1.0}, fx={"glitch": 0.14, "ab": 1.6}),
        lambda n, f: seg_hop("s3_throne_f1", "s3_throne_f2", n, K, ease="out", fno0=f, fx={"glitch": 0.18, "shake": 1.2}),
    ]
    pattern = [15, 15, 13, 13, 11, 11, 9, 9, 7, 7, 6, 6, 5, 5, 5, 5] + [4] * 40
    remaining, k = 224, 0
    while remaining > 0:
        n = min(pattern[k % len(pattern)], remaining)
        variant = g_variants[k % len(g_variants)]
        if n <= 5:
            T.append((n, _strobe_factory(variant)))
        else:
            T.append((n, variant))
        remaining -= n
        k += 1

    # H — crowned finale (122)
    T.append((122, lambda n, f: seg_emblem(n, f)))
    return T


def _strobe_factory(variant):
    """Accelerating final montage: the 4-5 frame cuts also strobe (face-safe)."""
    def factory(length: int, fno0: int):
        def gen():
            for i, frame in enumerate(variant(length, fno0)):
                if i % 2 == 0:
                    f_map = 0.30 * (1.0 - 0.55 * v2.FACE_MASK)
                    frame = frame * (1.0 - f_map) + np.array((255, 235, 210), np.float32)[None, None, :] * f_map * 1.35
                yield frame
        return gen()
    return factory


# --------------------------------------------------------------------------- #
# render
# --------------------------------------------------------------------------- #
def render(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    chunk = (args.chunk_start, args.chunk_end)
    f0 = chunk[0] if chunk[0] else 1
    f1 = chunk[1] if chunk[1] else (args.frames or TOTAL_FRAMES)
    out_mp4 = Path(args.part_out) if args.part_out else out_dir / OUT_NAME

    print("Loading action keyframes (real movement) + canonical plates...")
    K = me.Keyframes()
    timeline = build_timeline(K)
    plan_total = sum(n for n, _ in timeline[:])
    if plan_total != TOTAL_FRAMES:
        raise RuntimeError(f"timeline mismatch: {plan_total} != {TOTAL_FRAMES}")

    if args.no_audio or args.part_out:
        import scipy.io.wavfile as wf
        audio_path = out_dir / "silence.wav"
        wf.write(audio_path, 48000, np.zeros((int(TOTAL_FRAMES / FPS * 48000), 2), dtype=np.int16))
    else:
        print("Mastering spatial audio track (reference bed + scheduled impacts)...")
        audio_path, audio_metrics = build_master_audio()
        print("Audio metrics:", audio_metrics)

    cmd = [FFMPEG, "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(audio_path),
           "-c:v", "libx264", "-preset", "fast", "-crf", str(args.crf), "-pix_fmt", "yuv420p",
           "-threads", "1", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
           "-movflags", "+faststart", "-shortest", str(out_mp4), "-loglevel", "warning"]

    print(f"Rendering frames {f0}-{f1} at {W}x{H} @ {FPS}fps (real movement: flow hops + living shots)...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None

    gens: list = []
    seg_zero: list[tuple[int, int]] = []
    start = 1
    for length, factory in timeline:
        seg_zero.append((start, start + length - 1))
        gens.append(factory(length, start))
        start += length

    look_frames = {30, 120, 240, 300, 380, 450, 520, 600, 700, 860, 1000, 1120, 1200, 1240, 1300}
    contact: list[tuple[int, np.ndarray]] = []
    look: dict[int, np.ndarray] = {}
    seg_idx = 0
    produced = 0  # frames already pulled from the active segment generator
    for fno in range(f0, f1 + 1):
        while seg_idx < len(seg_zero) and fno > seg_zero[seg_idx][1]:
            seg_idx += 1
            produced = 0
        want = fno - seg_zero[seg_idx][0]
        while produced <= want:
            frame = next(gens[seg_idx])
            produced += 1
            if produced <= want:
                del frame
        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
        proc.stdin.write(frame_u8.tobytes())
        small = None
        if fno in look_frames or (args.sheets and (fno - 1) % 30 == 0):
            small = cv2.resize(frame_u8, (540, 960), interpolation=cv2.INTER_AREA)
        if fno in look_frames:
            look[fno] = small
        if args.sheets and (fno - 1) % 30 == 0:
            contact.append((fno, small))
        del frame, frame_u8
        if fno % 120 == 0:
            gc.collect()

    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg exited with code {rc}")
    print(f"Rendered {out_mp4} ({out_mp4.stat().st_size:,} bytes)")

    if args.sheets and not args.no_sheets:
        cols, rows = 7, 6
        cw, ch = 270, 480
        cs = Image.new("RGB", (cols * cw, rows * ch), (10, 10, 12))
        d = ImageDraw.Draw(cs)
        try:
            fnt = ImageFont.truetype(FONT_MONO, 22)
        except OSError:
            fnt = ImageFont.load_default()
        for i, (fno, rgb) in enumerate(contact[: cols * rows]):
            im = Image.fromarray(rgb).resize((cw, ch), Image.Resampling.LANCZOS)
            r_i, c_i = divmod(i, cols)
            cs.paste(im, (c_i * cw, r_i * ch))
            d.rectangle([c_i * cw, r_i * ch, c_i * cw + 150, r_i * ch + 30], fill=(0, 0, 0))
            d.text((c_i * cw + 8, r_i * ch + 5), f"F{fno:04d} {(fno - 1) / FPS:05.1f}s", fill=(0, 255, 200), font=fnt)
        contact_path = RECORDS / "MONARCH_CHAOS_VIDEO_3_CONTACT_SHEET.jpg"
        cs.save(contact_path, quality=92)
        print("Saved", contact_path.relative_to(STYLE_DIR.parent))

        lw, lh = 360, 640
        keys = sorted(look)
        rows_n = max(1, math.ceil(len(keys) / 5))
        ls = Image.new("RGB", (5 * lw, rows_n * lh), (8, 8, 10))
        d2 = ImageDraw.Draw(ls)
        for i, k in enumerate(keys):
            im = Image.fromarray(look[k]).resize((lw, lh), Image.Resampling.LANCZOS)
            r_i, c_i = divmod(i, 5)
            ls.paste(im, (c_i * lw, r_i * lh))
            d2.rectangle([c_i * lw, r_i * lh, c_i * lw + 300, r_i * lh + 34], fill=(0, 0, 0))
            d2.text((c_i * lw + 8, r_i * lh + 8), f"F{k:04d} · {(k - 1) / FPS:05.1f}s", fill=(255, 210, 60), font=fnt)
        look_path = RECORDS / "MONARCH_CHAOS_VIDEO_3_LOOK_SHEET.jpg"
        ls.save(look_path, quality=94)
        print("Saved", look_path.relative_to(STYLE_DIR.parent))

        plan = {
            "task_id": "EMS-20261014-001",
            "generation": "v3 · MOTION EDITION (dense-flow action hops + living-shot micro motion)",
            "total_frames": TOTAL_FRAMES,
            "fps": FPS,
            "duration_s": round(TOTAL_FRAMES / FPS, 2),
            "acts": ACT_TABLE,
            "segments": [{"start": a, "end": b} for a, b in seg_zero],
            "keyframes": sorted(K.frames),
        }
        plan_path = RECORDS / "CHAOS_VIDEO_3_PLAN.json"
        plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        print("Saved", plan_path.relative_to(STYLE_DIR.parent))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True, help="output directory for the master + sidecars")
    ap.add_argument("--frames", type=int, default=0, help="render a prefix only (smoke test)")
    ap.add_argument("--crf", type=int, default=20, help="x264 CRF (20 keeps the master around 50 MB)")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--no-sheets", action="store_true")
    ap.add_argument("--sheets", action="store_true", default=True)
    ap.add_argument("--chunk-start", type=int, default=0, help="first frame of this pass (1-based)")
    ap.add_argument("--chunk-end", type=int, default=0, help="last frame of this pass (inclusive)")
    ap.add_argument("--part-out", default="", help="write this pass to a separate video-only file")
    ap.add_argument("--plan", action="store_true", help="print the act table and exit")
    args = ap.parse_args()
    if args.plan:
        for act in ACT_TABLE:
            print(f'{act["act"]} {act["name"]:26s} f{act["start"]:4d}-{act["end"]:4d}  '
                  f'{act["seconds"][0]:5.2f}-{act["seconds"][1]:5.2f}s')
        return 0
    return render(args)


if __name__ == "__main__":
    raise SystemExit(main())
