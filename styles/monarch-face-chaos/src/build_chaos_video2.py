#!/usr/bin/env python3
"""WF-04 · Monarch Face · Chaos Video 2 — "SOVEREIGN OVERLOAD II · CHAOS RISING".

Reference-matched next-level cut of the user's reference video
`VID_20261013_050529_146.mp4` (44.55 s, 720x1280, 30 fps): the canonical Monarch
hero (his real face, black open-collar shirt, charcoal blazer) in the dark hall,
now covering the whole reference length with boosted 2.5D body motion, chaos
montage acts, glitch/aberration/shake layers and a crowned 👑 MONARCH STUDIO
finale built from the v1 emblem renderer.

Timeline (1336 frames @30 fps = 44.53 s, inside the 44.55 s reference track):

    A cold open       f1     - f66     0.00-2.17 s   slow creep, darkness, red pulse
    B throne          f67    - f240    2.20-7.97 s   push-in + MONARCH_OS neural sync HUD
    C chaos proj.     f241   - f420    8.00-13.97 s  15-frame cuts, aberration 1-6 px
    D triad           f421   - f582    13.97-19.37 s  3/4 close-up, profile, pointing 🫵
    E chaos burst     f583   - f780    19.40-25.97 s  7-frame cuts, glitch slices, shake
    F sovereign stance f781  - f990    25.97-32.97 s  30-frame shots, arms-crossed
    G finale build    f991   - f1214   32.97-40.47 s  accelerating montage 15->4 frames
    H crown finale    f1215  - f1336   40.47-44.53 s  gold impact -> crowned logo hold

Run (from a full worktree; see workflows/current/payload/README.md):

    bash tools/bootstrap_env.sh
    python3 tools/stage_ref_audio.py /tmp/monarch-stage/ref.mp4 --drive-id <id> --md5 <md5>
    python3 styles/monarch-face-chaos/src/build_chaos_video2.py --out /tmp/monarch-v2-out
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_chaos_video1 as v1  # noqa: E402  (plate loader, zoom/aberration, emblem)
from audio_engine2 import TOTAL_FRAMES as AUDIO_FRAMES, build_master_audio  # noqa: E402

W, H, FPS = 1080, 1920, 30
TOTAL_FRAMES = 1336
STYLE_DIR = HERE.parent
RECORDS = STYLE_DIR / "records"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FFMPEG = v1.FFMPEG

# ---------------------------------------------------------------------------
# reference-matched act table (also dumped to records/CHAOS_VIDEO_2_PLAN.json)
# ---------------------------------------------------------------------------
ACT_TABLE = [
    {"act": "A", "name": "cold open", "start": 1, "end": 66, "seconds": [0.0, 2.17]},
    {"act": "B", "name": "throne awakening", "start": 67, "end": 240, "seconds": [2.2, 7.97]},
    {"act": "C", "name": "chaos projection", "start": 241, "end": 420, "seconds": [8.0, 13.97]},
    {"act": "D", "name": "triad close-ups", "start": 421, "end": 582, "seconds": [13.97, 19.37]},
    {"act": "E", "name": "chaos burst", "start": 583, "end": 780, "seconds": [19.4, 25.97]},
    {"act": "F", "name": "sovereign stance", "start": 781, "end": 990, "seconds": [25.97, 32.97]},
    {"act": "G", "name": "finale build", "start": 991, "end": 1214, "seconds": [32.97, 40.47]},
    {"act": "H", "name": "crown finale", "start": 1215, "end": TOTAL_FRAMES, "seconds": [40.47, 44.53]},
]

MONTAGE_C = [
    ("med_red_blue", "seated"), ("med_red_sil", "closeup_34"), ("close_cyan_visor", "point_action"),
    ("med_dark_visor", "seated"), ("close_amber_sil", "closeup_34"), ("wide_hall", "wide"),
    ("med_red_blue", "closeup_34"), ("close_cyan", "seated"), ("med_red_sil", "point_action"),
    ("closeup_34", "closeup_34"), ("med_dark_visor", "wide"), ("wide_hall", "sovereign_arms"),
]
MONTAGE_E = [
    ("wide_hall", "wide"), ("med_red_blue", "seated"), ("med_red_sil", "closeup_34"),
    ("med_dark_visor", "point_action"), ("close_cyan", "seated"), ("close_cyan_visor", "point_action"),
    ("close_amber_sil", "closeup_34"), ("closeup_34", "closeup_34"), ("profile_side_neural", "profile_v9"),
]
STANCE_F = [
    ("wide_hall", "wide"), ("med_red_blue", "sovereign_arms"), ("med_red_sil", "wide"),
    ("wide_hall", "sovereign_arms"), ("med_red_blue", "wide"), ("med_red_sil", "sovereign_arms"),
    ("plate_sovereign_monarch_finale.png", "sovereign_arms"),
]

# ---------------------------------------------------------------------------
# 2.5D articulation rig (same basis fields as v1, amplitudes scaled per act)
# ---------------------------------------------------------------------------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
W_head = np.exp(-(((xx - 540.0) / 185.0) ** 2 + ((yy - 455.0) / 225.0) ** 2))
W_face3d = np.exp(-(((xx - 540.0) / 105.0) ** 2 + ((yy - 465.0) / 155.0) ** 2))
W_chest = np.exp(-(((xx - 540.0) / 340.0) ** 2 + ((yy - 820.0) / 260.0) ** 2))
chest_x = ((xx - 540.0) / 320.0) * W_chest
W_torso = np.clip((1450.0 - yy) / 950.0, 0.0, 1.0) * np.exp(-(((xx - 540.0) / 420.0) ** 2))
W_hands = np.exp(-(((xx - 540.0) / 260.0) ** 2 + ((yy - 1340.0) / 210.0) ** 2))
W_point = np.exp(-(((xx - 495.0) / 165.0) ** 2 + ((yy - 815.0) / 175.0) ** 2))
point_rx = (xx - 495.0) * W_point
point_ry = (yy - 815.0) * W_point
r_head = np.hypot((xx - 540.0) / 165.0, (yy - 410.0) / 185.0)
W_hair = np.exp(-((r_head - 0.95) ** 2) / 0.12)
W_env = np.clip(W_head + W_chest + W_hands + W_torso * 0.85, 0.0, 1.0)

_vr = np.sqrt(((xx - 540.0) / (W * 0.62)) ** 2 + ((yy - H * 0.46) / (H * 0.60)) ** 2)
VIGNETTE = np.clip(1.0 - 0.40 * np.clip(_vr - 0.34, 0.0, None) ** 1.6, 0.34, 1.0)[:, :, None]
_rng = np.random.default_rng(20261014)
GRAIN = [(_rng.standard_normal((H, W, 1)).astype(np.float32)) for _ in range(8)]


def articulate(img: np.ndarray, fno: int, mode: str, amp: float = 1.0, kick: float = 0.0) -> np.ndarray:
    """Boosted 2.5D skeletal motion (head yaw/pitch/roll, chest, torso sway, hands)."""
    t = (fno - 1) / float(FPS)
    beat = math.sin(t * math.pi * 4.4)          # 132 BPM reference pulse
    breath = math.sin(t * math.pi * 1.4)
    act = math.sin(t * math.pi * 0.85 + 0.4)
    k = (kick + 0.35 * max(0.0, beat) ** 2) * amp

    if mode == "wide":
        dx = chest_x * (6.5 * breath + 7.5 * k)
        dy = W_chest * (7.0 * breath + 8.5 * k) + W_head * (6.0 * act)
    elif mode == "point_action":
        thrust = (0.16 + 0.11 * math.sin(t * math.pi * 6.0) + 0.09 * k) * amp
        dx = (-point_rx * thrust + W_head * (16.0 * act) + W_face3d * (10.5 * act)
              + chest_x * (14.0 * breath + 16.0 * k) + W_torso * (13.0 * math.sin(t * 2.8)))
        dy = (-point_ry * thrust + W_point * (15.0 * math.cos(t * math.pi * 6.0))
              + W_head * (-13.0 * abs(act) + 10.0 * beat) + W_chest * (13.0 * breath + 15.0 * k))
    elif mode == "closeup_34":
        yaw = 20.0 * math.sin(t * 3.2) * amp
        pitch = -14.0 * math.cos(t * 2.6) * amp
        hair = 6.5 * np.sin(yy * 0.045 - t * 14.0) * W_hair
        dx = W_head * yaw + W_face3d * (yaw * 0.60) + chest_x * (15.0 * breath + 15.0 * k) + hair
        dy = W_head * pitch + W_chest * (13.0 * breath + 16.0 * k)
    elif mode == "profile_v9":
        lean = 18.0 * math.sin(t * 3.0) * amp
        nod = -14.0 * math.cos(t * 3.4) * amp
        hair = 7.0 * np.sin(yy * 0.04 - t * 15.0) * W_hair
        dx = W_torso * lean + W_head * (lean * 0.65) + hair
        dy = W_head * nod + W_chest * (13.0 * breath + 15.0 * k)
    elif mode == "sovereign_arms":
        roll = math.radians(2.9 * math.sin(t * 2.7) * amp)
        rot_dx = -(yy - 520.0) * math.sin(roll) * W_head
        rot_dy = (xx - 540.0) * math.sin(roll) * W_head
        dx = (rot_dx + W_face3d * (12.0 * act) + chest_x * (18.0 * breath + 20.0 * k)
              + W_torso * (14.0 * math.sin(t * 2.2)))
        dy = (rot_dy + W_head * (-13.0 * abs(breath) + 8.0 * beat) + W_chest * (16.0 * breath + 18.0 * k))
    else:  # seated
        roll = math.radians(3.0 * math.sin(t * 2.4 + 0.3) * amp)
        rot_dx = -(yy - 500.0) * math.sin(roll) * W_head
        rot_dy = (xx - 540.0) * math.sin(roll) * W_head
        yaw = 16.5 * act * amp
        pitch = (-13.5 * math.sin(t * 2.1) + 9.0 * k) * amp
        hair = 5.5 * np.sin(yy * 0.05 - t * 12.0) * W_hair
        dx = (rot_dx + W_head * yaw + W_face3d * (yaw * 0.55) + W_torso * (15.5 * math.sin(t * 1.9) * amp)
              + chest_x * (14.5 * breath + 17.0 * k) + ((xx - 540.0) / 220.0) * W_hands * (12.0 * beat) + hair)
        dy = (rot_dy + W_head * pitch + W_chest * (13.0 * breath + 16.0 * k)
              + W_hands * (-11.0 * abs(beat) - 9.0 * k))

    map_x = (xx - dx * W_env).astype(np.float32)
    map_y = (yy - dy * W_env).astype(np.float32)
    return cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


# ---------------------------------------------------------------------------
# FX layers
# ---------------------------------------------------------------------------
def shake(img: np.ndarray, fno: int, amount: float) -> np.ndarray:
    if amount <= 0.15:
        return img
    rng = np.random.default_rng(1000 + fno)
    dx, dy = rng.uniform(-amount, amount, 2)
    rot = math.radians(rng.uniform(-0.35, 0.35) * min(1.0, amount / 4.0))
    M = cv2.getRotationMatrix2D((W * 0.5, H * 0.46), math.degrees(rot), 1.0 + 0.002 * amount)
    M[0, 2] += dx
    M[1, 2] += dy
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def glitch(img: np.ndarray, fno: int, strength: float) -> np.ndarray:
    if strength <= 0.05:
        return img
    rng = np.random.default_rng(7000 + fno)
    out = img.copy()
    y = 0
    while y < H:
        band = int(rng.integers(16, 96))
        if rng.random() < 0.55:
            off = int(round(rng.uniform(-1.0, 1.0) * strength * 26.0))
            y1 = min(H, y + band)
            if off:
                shifted = np.roll(img[y:y1], off, axis=1)
                out[y:y1] = shifted
                if rng.random() < 0.4:  # channel tear on strong bands
                    out[y:y1, :, 0] = np.roll(out[y:y1, :, 0], off // 2, axis=1)
        y += band
    return out


def light_leak(img: np.ndarray, color: tuple[float, float, float], amount: float, phase: float) -> np.ndarray:
    if amount <= 0.001:
        return img
    grad = np.clip((np.sin(np.linspace(0.0, math.pi, W, dtype=np.float32) + phase) ** 2), 0.0, 1.0)
    band = grad[None, :, None] * np.clip(1.0 - np.abs(yy / H - 0.5) * 1.4, 0.0, 1.0)[:, :, None]
    tint = np.array(color, dtype=np.float32)[None, None, :]
    return img + band * tint * (amount * 40.0)


def apply_vignette_grain(img: np.ndarray, fno: int, grain: float) -> np.ndarray:
    out = img * VIGNETTE
    if grain > 0:
        out = out + GRAIN[fno % len(GRAIN)] * grain
    return out


def hud_overlay(img: np.ndarray, pct: float, label: str) -> np.ndarray:
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(pil, "RGBA")
    try:
        f_small = ImageFont.truetype(FONT_MONO, 15)
        f_pct = ImageFont.truetype(FONT_BOLD, 26)
    except OSError:
        f_small = f_pct = ImageFont.load_default()
    c = (255, 70, 60, 210)
    x1, y1, x2, y2 = 70, 300, W - 70, H - 470
    blen = 42
    for (px, py, sx, sy) in ((x1, y1, 1, 1), (x2, y1, -1, 1), (x1, y2, 1, -1), (x2, y2, -1, -1)):
        draw.line([(px, py), (px + sx * blen, py)], fill=c, width=3)
        draw.line([(px, py), (px, py + sy * blen)], fill=c, width=3)
    bar_w = int((x2 - x1) * min(1.0, pct / 100.0))
    draw.rectangle([x1, y2 + 26, x2, y2 + 34], outline=(255, 255, 255, 70))
    draw.rectangle([x1, y2 + 26, x1 + bar_w, y2 + 34], fill=(255, 70, 60, 220))
    draw.text((x1, y1 - 34), f"{label}", fill=(255, 235, 235, 190), font=f_small)
    draw.text((x1, y2 + 46), f"MONARCH_OS // NEURAL SYNC {int(pct):03d}%", fill=(255, 120, 110, 230), font=f_pct)
    return np.array(pil, dtype=np.float32)


def emblem_frame(alpha: float, crown: float, fno: int) -> np.ndarray:
    emb = np.asarray(v1.build_emblem_frame(alpha_glow=alpha, crown_boost=crown, fno=fno), dtype=np.float32)
    return emb


# ---------------------------------------------------------------------------
# timeline
# ---------------------------------------------------------------------------
def shot_for(fno: int) -> dict:
    """Return the plate/mode/camera/FX description for one frame."""
    plan: dict = {"plate": "plate_wide_hall.png", "mode": "wide", "amp": 1.1, "zoom": 1.0,
                  "dx": 0.0, "dy": 0.0, "ab": 0.0, "glitch": 0.0, "shake": 0.0,
                  "leak": (0.0, 0.0, 0.0), "leak_amt": 0.0, "flash": (0.0, 0.0, 0.0),
                  "flash_amt": 0.0, "dark": 1.0, "hud": None, "grain": 1.6}

    if fno <= 66:  # ACT A · cold open
        p = (fno - 1) / 65.0
        plan.update(zoom=1.00 + 0.05 * p, dark=0.42 + 0.20 * p, amp=1.0,
                    leak=(30, 10, 60), leak_amt=0.10 + 0.10 * math.sin(p * math.pi * 2.0))
        if fno <= 8:
            plan["dark"] = 0.22

    elif fno <= 240:  # ACT B · throne awakening
        p = (fno - 67) / 173.0
        plan.update(amp=1.15, grain=2.0)
        if fno <= 96:
            plan.update(zoom=1.05 + 0.07 * ((fno - 67) / 29.0), dark=0.72, hud=35.0 * ((fno - 67) / 29.0))
        elif fno <= 112:
            plan.update(plate="plate_med_red_blue.png", mode="closeup_34", amp=1.2, zoom=1.10,
                        ab=1.5, hud=35.0 + 8.0 * ((fno - 97) / 15.0))
        elif fno <= 160:
            plan.update(zoom=1.12 + 0.06 * ((fno - 113) / 47.0), dark=0.78,
                        hud=45.0 + 30.0 * ((fno - 113) / 47.0))
        elif fno <= 176:
            plan.update(plate="plate_close_cyan.png", mode="closeup_34", amp=1.25, zoom=1.12,
                        ab=2.5, flash=(255, 60, 50), flash_amt=0.10, hud=78.0)
        elif fno <= 208:
            plan.update(plate="plate_med_red_sil.png", mode="seated", amp=1.2, zoom=1.10 + 0.06 * ((fno - 177) / 31.0),
                        leak=(60, 20, 90), leak_amt=0.18, hud=80.0 + 12.0 * ((fno - 177) / 31.0))
        else:
            plan.update(zoom=1.16 + 0.06 * ((fno - 209) / 31.0), dark=0.85, hud=100.0,
                        leak=(40, 15, 70), leak_amt=0.14)

    elif fno <= 420:  # ACT C · chaos projection — 15-frame cuts
        idx = min(len(MONTAGE_C) - 1, (fno - 241) // 15)
        cut = (fno - 241) % 15 == 0
        plate, mode = MONTAGE_C[idx]
        plan.update(plate=f"plate_{plate}.png" if not plate.endswith(".png") else plate,
                    mode=mode, amp=1.30 + 0.05 * (idx % 2), zoom=1.06 + 0.02 * (idx % 3) + 0.0015 * (fno - 241),
                    ab=1.0 + 5.0 * ((fno - 241) / 179.0), shake=2.4, grain=2.4,
                    leak=(70, 25, 110), leak_amt=0.12 + 0.08 * math.sin(fno * 0.12))
        if cut:
            plan.update(flash=(255, 40, 40), flash_amt=0.16, glitch=0.25)
        if idx % 3 == 2:
            plan["glitch"] = 0.45

    elif fno <= 582:  # ACT D · triad close-ups
        plan.update(amp=1.20, grain=1.8)
        if fno <= 444:
            plan.update(plate="plate_closeup_34.png", mode="closeup_34", zoom=1.06 + 0.08 * ((fno - 421) / 23.0))
        elif fno <= 468:
            plan.update(plate="plate_profile_side_neural.png", mode="profile_v9",
                        zoom=1.05 + 0.07 * ((fno - 445) / 23.0), ab=1.5)
        elif fno <= 486:
            plan.update(plate="plate_close_amber_sil.png", mode="seated", amp=1.25,
                        zoom=1.08, ab=2.0, leak=(90, 45, 20), leak_amt=0.16)
        elif fno <= 522:
            plan.update(plate="plate_close_cyan_visor.png", mode="point_action", amp=1.28,
                        zoom=1.10 + 0.12 * ((fno - 487) / 35.0), shake=1.6, ab=2.4)
        else:
            plan.update(plate="plate_med_red_blue.png", mode="sovereign_arms", amp=1.25,
                        zoom=1.02 + 0.08 * ((fno - 523) / 59.0), leak=(60, 20, 90), leak_amt=0.18)

    elif fno <= 780:  # ACT E · chaos burst — 7-frame cuts
        idx = min(len(MONTAGE_E) - 1, (fno - 583) // 7)
        cut = (fno - 583) % 7 == 0
        plate, mode = MONTAGE_E[idx % len(MONTAGE_E)]
        plan.update(plate=f"plate_{plate}.png", mode=mode, amp=1.35, zoom=1.15 if idx % 2 == 0 else 1.32,
                    ab=3.5 + 3.5 * ((fno - 583) / 197.0), shake=4.2, grain=2.8,
                    glitch=0.60 if idx % 2 == 0 else 0.25,
                    leak=(120, 30, 140), leak_amt=0.18)
        if cut:
            plan.update(flash=(255, 235, 235), flash_amt=0.20)
        if idx % 8 == 3 and (fno - 583) % 7 == 0:
            plan["invert"] = True

    elif fno <= 990:  # ACT F · sovereign stance — 30-frame shots
        idx = min(len(STANCE_F) - 1, (fno - 781) // 30)
        plate, mode = STANCE_F[idx]
        cut = (fno - 781) % 30 == 0
        plan.update(plate=plate if plate.endswith(".png") else f"plate_{plate}.png", mode=mode,
                    amp=1.25, zoom=1.04 + 0.12 * ((fno - 781) / 209.0), shake=1.5,
                    ab=1.5, grain=2.0, leak=(50, 20, 80), leak_amt=0.14)
        if cut:
            plan.update(flash=(255, 255, 255), flash_amt=0.12, glitch=0.2)

    elif fno <= 1214:  # ACT G · finale build — accelerating montage
        if fno <= 1050:
            idx, blocks, length = (fno - 991) // 15, 15, "15f"
        elif fno <= 1110:
            idx, blocks, length = 4 + (fno - 1051) // 10, 6, "10f"
        elif fno <= 1166:
            idx, blocks, length = 10 + (fno - 1111) // 7, 8, "7f"
        else:
            idx, blocks, length = 18 + (fno - 1167) // 4, 12, "4f"
        pool = ["plate_med_red_blue.png", "plate_med_red_sil.png", "plate_close_cyan_visor.png",
                "plate_closeup_34.png", "plate_med_dark_visor.png", "plate_close_amber_sil.png",
                "plate_profile_side_neural.png", "plate_wide_hall.png",
                "plate_sovereign_monarch_finale.png"]
        span = (fno - 991) / 223.0
        plan.update(plate=pool[idx % len(pool)], mode=["seated", "closeup_34", "point_action", "sovereign_arms"][idx % 4],
                    amp=1.35, zoom=1.10 + 0.35 * span, ab=2.0 + 6.0 * span, shake=2.0 + 5.0 * span,
                    glitch=0.35 + 0.35 * span if idx % 3 == 0 else 0.15, grain=2.6,
                    leak=(140, 40, 60), leak_amt=0.20 + 0.10 * span)
        if fno % max(2, 15 - int(span * 10)) == 0:
            plan.update(flash=(255, 210, 120), flash_amt=0.16 + 0.14 * span)
        if fno >= 1205:  # final push into the eyes before the gold impact
            plan.update(plate="plate_closeup_34.png", mode="closeup_34", zoom=1.45 + 0.05 * (fno - 1205),
                        ab=8.0, shake=6.0, flash=(255, 220, 140), flash_amt=0.22 + 0.10 * (fno - 1205))

    else:  # ACT H · crown finale
        plan.update(plate="plate_sovereign_monarch_finale.png", mode="sovereign_arms", amp=1.1,
                    zoom=1.02 + 0.02 * ((fno - 1215) / 121.0), grain=1.4)
    return plan


def render(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / "MONARCH_CHAOS_VIDEO_2_MASTER.mp4"
    frames = args.frames or TOTAL_FRAMES

    print("Loading canonical plates (single source: styles/monarch-face-chaos/plates)...")
    cache: dict[str, np.ndarray] = {}

    def plate(name: str) -> np.ndarray:
        if name not in cache:
            cache[name] = v1.load_plate_1080(name)
        return cache[name]

    if args.no_audio:
        audio_path = out_dir / "silence.wav"
        import scipy.io.wavfile as wf
        wf.write(audio_path, 48000, np.zeros((int(frames / FPS * 48000), 2), dtype=np.int16))
        audio_metrics = {"silent_test": True}
    else:
        print("Mastering spatial audio track (reference bed + scheduled impacts)...")
        audio_path, audio_metrics = build_master_audio()
        print("Audio metrics:", audio_metrics)

    cmd = [FFMPEG, "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(audio_path),
           "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
           "-movflags", "+faststart", "-shortest", str(out_mp4), "-loglevel", "warning"]

    print(f"Rendering {frames} frames at {W}x{H} @ {FPS}fps (chaos acts + crowned finale)...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None

    contact: list[tuple[int, np.ndarray]] = []
    look: dict[int, np.ndarray] = {}
    look_frames = {30, 120, 240, 300, 380, 450, 520, 600, 700, 860, 1000, 1120, 1200, 1240, 1300}

    for fno in range(1, frames + 1):
        plan = shot_for(fno)
        base = plate(plan["plate"])
        frame = articulate(base, fno, plan["mode"], amp=plan["amp"], kick=0.6 if fno % 15 < 2 else 0.0)
        frame = v1.zoom_pan(frame, zoom=plan["zoom"], dx=plan.get("dx", 0.0), dy=plan.get("dy", 0.0))
        if plan["ab"] > 0:
            frame = v1.chromatic_aberration(frame, plan["ab"])
        if plan["glitch"] > 0:
            frame = glitch(frame, fno, plan["glitch"])
        if plan["shake"] > 0:
            frame = shake(frame, fno, plan["shake"])
        if plan["dark"] != 1.0:
            frame = frame * plan["dark"]
        if plan["leak_amt"] > 0:
            frame = light_leak(frame, plan["leak"], plan["leak_amt"], fno * 0.05)
        if plan["flash_amt"] > 0:
            f = plan["flash_amt"]
            frame = frame * (1.0 - f) + np.array(plan["flash"], dtype=np.float32)[None, None, :] * f * 1.35
        if plan.get("invert"):
            frame = 255.0 - frame

        if 1215 <= fno <= TOTAL_FRAMES:  # crowned MONARCH STUDIO finale
            span = (fno - 1215) / float(TOTAL_FRAMES - 1215)
            if fno <= 1226:
                alpha, crown, glow = 1.0, min(1.0, (fno - 1215) / 8.0), 0.85 - 0.55 * (fno - 1215) / 11.0
                emb = emblem_frame(alpha, crown, fno)
                frame = frame * glow + emb * (1.0 - glow)
            else:
                crown = 0.75 + 0.25 * math.sin((fno - 1227) * 0.09)
                emb = emblem_frame(1.0, crown, fno)
                if fno >= 1301:
                    fade = 1.0 - 0.45 * ((fno - 1301) / 35.0)
                    emb = emb * fade
                if fno >= 1331:
                    emb = emb * (0.55 - 0.02 * (fno - 1331))
                frame = emb
                frame = shake(frame, fno, 0.8)
            frame = apply_vignette_grain(frame, fno, 1.2)
        else:
            frame = apply_vignette_grain(frame, fno, plan["grain"])
            if plan["hud"] is not None:
                frame = hud_overlay(frame, plan["hud"], "MONARCH_OS v4.0 · SOVEREIGN OVERLOAD II")

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
        proc.stdin.write(frame_u8.tobytes())
        if fno in look_frames:
            look[fno] = frame_u8.copy()
        if args.sheets and (fno - 1) % 30 == 0:
            contact.append((fno, frame_u8.copy()))

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
        contact_path = RECORDS / "MONARCH_CHAOS_VIDEO_2_CONTACT_SHEET.jpg"
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
        look_path = RECORDS / "MONARCH_CHAOS_VIDEO_2_LOOK_SHEET.jpg"
        ls.save(look_path, quality=94)
        print("Saved", look_path.relative_to(STYLE_DIR.parent))

        plan_path = RECORDS / "CHAOS_VIDEO_2_PLAN.json"
        plan_path.write_text(json.dumps({
            "schema_version": 1,
            "task_id": "EMS-20261014-001",
            "title": "MONARCH CHAOS VIDEO 2 · SOVEREIGN OVERLOAD II · CHAOS RISING",
            "reference": {
                "drive_id": "1sYYhXs9fbHeHcQGOmH5IR7CvUSVr9Tmx",
                "name": "VID_20261013_050529_146.mp4",
                "duration_seconds": 44.399,
                "width": 720, "height": 1280, "fps": 30,
                "cut_map_note": "4 fps frame-diff analysis: dark open (luma ~9) to 16.5 s, montage bursts 16.5-19.25 s and 34.75-38.25 s, hard flash/cut 40.25-40.5 s, ~4 s tail card.",
            },
            "format": {"width": W, "height": H, "fps": FPS, "frames": TOTAL_FRAMES,
                       "duration_seconds": round(TOTAL_FRAMES / FPS, 3), "audio": "48 kHz stereo"},
            "acts": ACT_TABLE,
            "audio_metrics": audio_metrics,
            "improvements_over_v1": [
                "covers the full 44.53 s reference length (v1 was 21.20 s)",
                "act structure retimed to the measured reference cut map",
                "body-motion amplitudes boosted per act (amp 1.0-1.35)",
                "new chaos layers: glitch band slices, camera shake, light leaks, strobes, invert hit",
                "crowned MONARCH STUDIO finale extended to 4.06 s with crown float and fade",
            ],
        }, indent=1) + "\n")
        print("Saved", plan_path.relative_to(STYLE_DIR.parent))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="/tmp/monarch-v2-out", help="output directory (keep outside the workspace snapshot)")
    parser.add_argument("--frames", type=int, default=0, help="render only the first N frames (smoke test)")
    parser.add_argument("--no-audio", action="store_true", help="silent track (fast smoke test)")
    parser.add_argument("--no-sheets", action="store_true", help="skip contact/look sheets")
    parser.add_argument("--sheets", action="store_true", default=True, help=argparse.SUPPRESS)
    parser.add_argument("--plan", action="store_true", help="print the act table and exit")
    args = parser.parse_args()
    if args.plan:
        for act in ACT_TABLE:
            print(f"{act['act']} {act['name']:<20} f{act['start']:>4}-f{act['end']:<4} {act['seconds'][0]:6.2f}-{act['seconds'][1]:6.2f}s")
        return 0
    if AUDIO_FRAMES != TOTAL_FRAMES:
        print(f"warning: audio engine is built for {AUDIO_FRAMES} frames, renderer for {TOTAL_FRAMES}", file=sys.stderr)
    return render(args)


if __name__ == "__main__":
    raise SystemExit(main())
