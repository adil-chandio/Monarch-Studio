#!/usr/bin/env python3
"""
WF-04 · Monarch Face · Chaos Video 1 v2 (Canonical Boss Wardrobe & Face + Dynamic 2.5D Body Motion + Crown Finale)
Full 1080x1920 30fps production renderer.
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_engine import build_master_audio

PAYLOAD = Path(__file__).resolve().parents[1]
PLATES_DIR = PAYLOAD / "plates"

W, H = 1080, 1920
FPS = 30
TOTAL_FRAMES = 636


def load_plate_1080(name: str, shift_x: float = 0.0, shift_y: float = 0.0) -> np.ndarray:
    im = Image.open(PLATES_DIR / name).convert("RGB")
    sw, sh = W, int(round(im.height * (W / float(im.width))))
    im = im.resize((sw, sh), Image.Resampling.LANCZOS)
    arr = np.array(im, dtype=np.float32)
    y0 = max(0, (sh - H) // 2)
    cropped = arr[y0 : y0 + H, :W, :]
    if shift_x != 0.0 or shift_y != 0.0:
        M = np.float32([[1.0, 0.0, shift_x], [0.0, 1.0, shift_y]])
        cropped = cv2.warpAffine(cropped, M, (W, H), borderMode=cv2.BORDER_REPLICATE)
    return cropped


def zoom_pan(img: np.ndarray, zoom: float, dx: float = 0.0, dy: float = 0.0, cx: float = W * 0.5, cy: float = H * 0.46) -> np.ndarray:
    if abs(zoom - 1.0) < 1e-4 and abs(dx) < 0.1 and abs(dy) < 0.1:
        return img
    M = np.float32([[zoom, 0.0, (1.0 - zoom) * cx + dx], [0.0, zoom, (1.0 - zoom) * cy + dy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def chromatic_aberration(img: np.ndarray, shift_px: float) -> np.ndarray:
    s = int(round(shift_px))
    if s <= 0:
        return img
    out = img.copy()
    out[:, s:, 0] = img[:, :-s, 0]
    out[:, :-s, 2] = img[:, s:, 2]
    return out


def draw_star_glint(draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float, color_core: tuple[int, int, int], color_ray: tuple[int, int, int]) -> None:
    r = int(round(radius))
    if r <= 1:
        return
    draw.line([(cx - r, cy), (cx + r, cy)], fill=color_ray, width=3)
    draw.line([(cx, cy - r), (cx, cy + r)], fill=color_ray, width=3)
    d = int(round(r * 0.55))
    draw.line([(cx - d, cy - d), (cx + d, cy + d)], fill=color_ray, width=2)
    draw.line([(cx - d, cy + d), (cx + d, cy - d)], fill=color_ray, width=2)
    cr = max(3, r // 4)
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=color_core)


def build_emblem_frame(alpha_glow: float = 1.0, crown_boost: float = 0.0, fno: int = 450) -> np.ndarray:
    """
    Renders the Monarch Studio royal crest with a large, sculpted 24K Gold Crown (👑)
    prominently ABOVE the geometric Monarch sigil and MONARCH STUDIO title.
    """
    t = fno / float(FPS)
    pulse = 0.5 + 0.5 * math.sin(t * 9.0)
    emblem = np.zeros((H, W, 3), dtype=np.float32)
    emblem[:, :, 0], emblem[:, :, 1], emblem[:, :, 2] = 5.0, 4.0, 7.0

    cx, cy = W // 2, H // 2 + 20
    R = 112

    # 1. Volumetric golden god-rays bursting from behind the Crown (👑)
    crown_cx, crown_cy = cx, cy - R - 135
    pil_rays = Image.new("RGB", (W, H), (0, 0, 0))
    r_draw = ImageDraw.Draw(pil_rays)
    num_rays = 18
    for i in range(num_rays):
        ang = (i / float(num_rays)) * math.pi * 2.0 + t * 0.35
        spread = 0.045
        len_r = (340.0 + 90.0 * math.sin(i * 2.3 + t * 4.0)) * (0.65 + 0.45 * crown_boost) * alpha_glow
        x1 = crown_cx + math.cos(ang - spread) * len_r
        y1 = crown_cy + math.sin(ang - spread) * len_r
        x2 = crown_cx + math.cos(ang + spread) * len_r
        y2 = crown_cy + math.sin(ang + spread) * len_r
        ray_col = (
            int(min(255, 110 * alpha_glow * (0.7 + 0.3 * crown_boost))),
            int(min(255, 68 * alpha_glow * (0.7 + 0.3 * crown_boost))),
            int(min(255, 14 * alpha_glow)),
        )
        r_draw.polygon([(crown_cx, crown_cy), (x1, y1), (x2, y2)], fill=ray_col)
    rays_arr = cv2.GaussianBlur(np.array(pil_rays, dtype=np.float32), (75, 75), 28.0)
    emblem = np.clip(emblem + rays_arr, 0, 255)

    pil_emb = Image.fromarray(emblem.astype(np.uint8))
    draw = ImageDraw.Draw(pil_emb)

    c_main = (
        int(min(255, 242 * alpha_glow)),
        int(min(255, (140 + 40 * crown_boost) * alpha_glow)),
        int(min(255, 32 * alpha_glow)),
    )
    c_bright = (
        int(min(255, 255 * alpha_glow)),
        int(min(255, (195 + 40 * crown_boost) * alpha_glow)),
        int(min(255, (75 + 45 * crown_boost) * alpha_glow)),
    )
    c_gold_hi = (
        int(min(255, 255 * alpha_glow)),
        int(min(255, 238 * alpha_glow)),
        int(min(255, 165 * alpha_glow)),
    )
    c_gold_mid = (
        int(min(255, 250 * alpha_glow)),
        int(min(255, 178 * alpha_glow)),
        int(min(255, 38 * alpha_glow)),
    )
    c_gold_dark = (
        int(min(255, 175 * alpha_glow)),
        int(min(255, 102 * alpha_glow)),
        int(min(255, 16 * alpha_glow)),
    )

    # 2.LARGE SCULPTED 24K GOLDEN CROWN (👑) ABOVE THE SIGIL & NAME
    bob_y = int(round(4.0 * math.sin(t * 4.5)))
    cb_y = crown_cy + 55 + bob_y  # Crown base Y
    cw_half = 128                 # Crown half-width (256px wide total!)

    # Crown base jewel band
    base_top = cb_y - 24
    base_bot = cb_y
    draw.polygon([
        (cx - cw_half + 14, base_top),
        (cx + cw_half - 14, base_top),
        (cx + cw_half - 22, base_bot),
        (cx - cw_half + 22, base_bot),
    ], fill=c_gold_dark, outline=c_gold_hi, width=3)
    draw.line([(cx - cw_half + 16, base_top + 6), (cx + cw_half - 16, base_top + 6)], fill=c_gold_hi, width=2)
    draw.line([(cx - cw_half + 20, base_bot - 5), (cx + cw_half - 20, base_bot - 5)], fill=c_gold_hi, width=2)

    # 5 Sculpted Royal Crown Peaks (left outer, left inner, center sovereign spire, right inner, right outer)
    peaks = [
        (cx - cw_half - 4, base_top - 68),   # P0: far left peak
        (cx - 66,          base_top - 96),   # P1: inner left peak
        (cx,               base_top - 126),  # P2: tall center sovereign peak
        (cx + 66,          base_top - 96),   # P3: inner right peak
        (cx + cw_half + 4, base_top - 68),   # P4: far right peak
    ]
    valleys = [
        (cx - 88, base_top - 26),
        (cx - 32, base_top - 38),
        (cx + 32, base_top - 38),
        (cx + 88, base_top - 26),
    ]
    base_anchors = [
        (cx - cw_half + 14, base_top),
        (cx - 64, base_top),
        (cx - 26, base_top),
        (cx + 26, base_top),
        (cx + 64, base_top),
        (cx + cw_half - 14, base_top),
    ]

    # Fill main crown silhouette
    crown_poly = [
        base_anchors[0],
        peaks[0],
        valleys[0],
        peaks[1],
        valleys[1],
        peaks[2],
        valleys[2],
        peaks[3],
        valleys[3],
        peaks[4],
        base_anchors[5],
    ]
    draw.polygon(crown_poly, fill=c_gold_mid, outline=c_gold_hi, width=4)

    # 3D bevel facets on each spire (left facet bright champagne gold, right facet warm burnished gold)
    spire_bases = [
        (base_anchors[0], valleys[0]),
        (valleys[0], valleys[1]),
        (valleys[1], valleys[2]),
        (valleys[2], valleys[3]),
        (valleys[3], base_anchors[5]),
    ]
    for idx_p, (px, py) in enumerate(peaks):
        (lx, ly), (rx, ry) = spire_bases[idx_p]
        mx = (lx + rx) * 0.5
        draw.polygon([(px, py), (lx, ly), (mx, base_top)], fill=c_gold_hi, outline=c_gold_hi, width=1)
        draw.polygon([(px, py), (mx, base_top), (rx, ry)], fill=c_gold_dark, outline=c_gold_mid, width=1)
        draw.line([(px, py), (mx, base_top)], fill=c_gold_hi, width=2)

    # Jewels inside the base band (alternating ruby, diamond, cyan-sapphire)
    band_y = (base_top + base_bot) // 2
    for jx, jcol in [
        (cx - 82, (int(255 * alpha_glow), int(50 * alpha_glow), int(70 * alpha_glow))),
        (cx - 42, c_gold_hi),
        (cx,      (int(120 * alpha_glow), int(235 * alpha_glow), int(255 * alpha_glow))),
        (cx + 42, c_gold_hi),
        (cx + 82, (int(255 * alpha_glow), int(50 * alpha_glow), int(70 * alpha_glow))),
    ]:
        draw.polygon([(jx, band_y - 7), (jx + 9, band_y), (jx, band_y + 7), (jx - 9, band_y)], fill=jcol, outline=c_gold_hi)

    # Jewels & star glints at each of the 5 Crown Tips!
    for idx_p, (px, py) in enumerate(peaks):
        orb_r = 9 if idx_p == 2 else 7
        draw.ellipse([px - orb_r, py - orb_r, px + orb_r, py + orb_r], fill=c_gold_hi, outline=c_main, width=2)
        glint_r = (22.0 if idx_p == 2 else 14.0) * (0.75 + 0.35 * math.sin(t * 11.0 + idx_p * 1.4)) * alpha_glow
        draw_star_glint(draw, px, py, glint_r, (255, 255, 255), c_gold_hi)

    # 3. Monarch Geometric Lattice Diamond Sigil below the Crown
    for offset in range(-3, 4):
        d = offset * 22
        pts_a = [(cx + s, cy + s + d) for s in np.linspace(-R, R, 160) if abs(s) + abs(s + d) <= R]
        if len(pts_a) >= 2:
            draw.line([pts_a[0], pts_a[-1]], fill=c_main, width=8)
        pts_b = [(cx + s, cy - s + d) for s in np.linspace(-R, R, 160) if abs(s) + abs(-s + d) <= R]
        if len(pts_b) >= 2 and offset % 2 == 0:
            draw.line([pts_b[0], pts_b[-1]], fill=c_bright, width=8)

    draw.polygon([(cx, cy - R - 10), (cx + R + 10, cy), (cx, cy + R + 10), (cx - R - 10, cy)], outline=c_gold_hi, width=6)

    # Expanding shockwave ring on bass pulse
    ring_rad = int(round(R * (1.25 + 0.55 * ((t * 1.4) % 1.0))))
    ring_alpha = max(0.0, 1.0 - ((t * 1.4) % 1.0)) * alpha_glow * (0.5 + 0.5 * crown_boost)
    if ring_alpha > 0.08:
        rc = (int(255 * ring_alpha), int(185 * ring_alpha), int(45 * ring_alpha))
        draw.polygon([(cx, cy - ring_rad), (cx + ring_rad, cy), (cx, cy + ring_rad), (cx - ring_rad, cy)], outline=rc, width=3)

    # 4. Bold, Unmistakable MONARCH STUDIO Typography + Mini Crown Dividers
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
        sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except Exception:
        title_font = ImageFont.load_default()
        sub_font = title_font

    label = "MONARCH STUDIO"
    bbox = draw.textbbox((0, 0), label, font=title_font)
    tw_txt = bbox[2] - bbox[0]
    tx = cx - tw_txt // 2
    ty = cy + R + 46

    # Drop shadow / gold bevel for MONARCH STUDIO
    draw.text((tx + 2, ty + 3), label, fill=c_gold_dark, font=title_font)
    draw.text((tx, ty), label, fill=c_gold_hi, font=title_font)

    # Glowing horizontal gold underline bar with center diamond
    bar_y = ty + 62
    bar_w = int(round(240 * (0.85 + 0.15 * pulse)))
    draw.line([(cx - bar_w, bar_y), (cx + bar_w, bar_y)], fill=c_gold_mid, width=4)
    draw.polygon([(cx, bar_y - 7), (cx + 10, bar_y), (cx, bar_y + 7), (cx - 10, bar_y)], fill=c_gold_hi)

    sub = "S O V E R E I G N   E D I T I O N   ·   W F - 0 4"
    sb = draw.textbbox((0, 0), sub, font=sub_font)
    c_sub = (
        int(min(255, 235 * alpha_glow * (0.65 + 0.35 * crown_boost))),
        int(min(255, 168 * alpha_glow * (0.65 + 0.35 * crown_boost))),
        int(min(255, 65 * alpha_glow * (0.65 + 0.35 * crown_boost))),
    )
    draw.text((cx - (sb[2] - sb[0]) // 2, bar_y + 18), sub, fill=c_sub, font=sub_font)

    # 5. Rising Molten Gold Embers / Sparks
    for s_idx in range(28):
        seed_x = (s_idx * 137 + 89) % W
        speed = 110.0 + (s_idx % 5) * 35.0
        sy = (H - ((fno * speed / FPS + s_idx * 73) % H))
        sx = seed_x + 28.0 * math.sin(sy * 0.012 + s_idx)
        if abs(sx - cx) < 420:
            sr = 2 + (s_idx % 3)
            sc = (
                int(min(255, 255 * alpha_glow)),
                int(min(255, (160 + (s_idx % 80)) * alpha_glow)),
                int(min(255, 50 * alpha_glow)),
            )
            draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=sc)

    arr = np.array(pil_emb, dtype=np.float32)
    glow = cv2.GaussianBlur(arr, (65, 65), 24.0)
    return np.clip(arr + glow * (0.52 + 0.38 * crown_boost), 0, 255)


def main() -> None:
    print("Loading 1080x1920 v2 canonical blazer+shirt master plates...")
    wide = load_plate_1080("plate_wide_hall.png")
    med_rb = load_plate_1080("plate_med_red_blue.png")
    med_rs = load_plate_1080("plate_med_red_sil.png")
    med_dv_tactical = load_plate_1080("plate_med_dark_visor.png")
    close_34 = load_plate_1080("plate_closeup_34.png")
    side_prof = load_plate_1080("plate_profile_side_neural.png")
    close_cy = load_plate_1080("plate_close_cyan.png")
    close_cv = load_plate_1080("plate_close_cyan_visor.png")
    close_am = load_plate_1080("plate_close_amber_sil.png")
    sovereign = load_plate_1080("plate_sovereign_monarch_finale.png")

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    # -------------------------------------------------------------------------
    # PRECOMPUTE 2.5D ARTICULATED BODY & HEAD MOTION BASIS FIELDS
    # -------------------------------------------------------------------------
    # 1. Head & Face Zone (for 3D Yaw turn, Pitch chin lift, and Roll tilt)
    W_head = np.exp(-(((xx - 540.0) / 185.0) ** 2 + ((yy - 455.0) / 225.0) ** 2))
    # 3D perspective bell curve across nose/eyes so front of face turns more than ears
    W_face_3d = np.exp(-(((xx - 540.0) / 105.0) ** 2 + ((yy - 465.0) / 155.0) ** 2))

    # 2. Shoulders & Upper Chest Zone (for breathing & beat-reactive shoulder heave)
    W_chest = np.exp(-(((xx - 540.0) / 340.0) ** 2 + ((yy - 820.0) / 260.0) ** 2))
    chest_expand_x = ((xx - 540.0) / 320.0) * W_chest

    # 3. Upper-Body Torso Sway & Lean Zone (pivoting smoothly from waist y=1450)
    W_upper_body = np.clip((1450.0 - yy) / 950.0, 0.0, 1.0) * np.exp(-(((xx - 540.0) / 420.0) ** 2))

    # 4. Forearms & Clasped Hands Zone (seated knee grip & flex motion)
    W_hands_seated = np.exp(-(((xx - 540.0) / 260.0) ** 2 + ((yy - 1340.0) / 210.0) ** 2))

    # 5. Pointing Hand & Arm Zone (for close_cyan_visor 🫵 forward thrust!)
    W_point_hand = np.exp(-(((xx - 495.0) / 165.0) ** 2 + ((yy - 815.0) / 175.0) ** 2))
    point_radial_x = (xx - 495.0) * W_point_hand
    point_radial_y = (yy - 815.0) * W_point_hand

    # 6. Hair & Blazer Lapel Wind Ripple Zone
    r_head = np.hypot((xx - 540.0) / 165.0, (yy - 410.0) / 185.0)
    W_hair_rim = np.exp(-((r_head - 0.95) ** 2) / 0.12)

    # Subject matte so background monolith screen edges stay rock-solid while body moves
    W_subject_envelope = np.clip(W_head + W_chest + W_hands_seated + W_upper_body * 0.85, 0.0, 1.0)

    def articulate_body(
        img: np.ndarray,
        fno: int,
        mode: str = "seated",
        beat_kick: float = 0.0,
    ) -> np.ndarray:
        """
        Applies smooth 30fps 2.5D skeletal articulation (3D head turn/nod/tilt,
        shoulder/chest breathing & bass heave, torso sway, hand action, and hair wind)
        using cv2.remap.
        """
        t = fno / float(FPS)
        # Rhythmic 132 BPM pulse (2.2 Hz) + slower organic breathing/acting waves
        beat_wave = math.sin(t * math.pi * 4.4)
        breath = math.sin(t * math.pi * 1.4)
        act_slow = math.sin(t * math.pi * 0.85 + 0.4)
        kick = beat_kick + 0.35 * max(0.0, beat_wave) ** 2

        if mode == "wide":
            # Pronounced seated breathing & head lift in the wide throne shot
            dx = chest_expand_x * (6.5 * breath + 7.5 * kick)
            dy = W_chest * (7.0 * breath + 8.5 * kick) + W_head * (6.0 * act_slow)
        elif mode == "point_action":
            # Dynamic pointing hand 🫵 thrusting toward lens + assertive head nod & shoulder lean!
            thrust = 0.14 + 0.10 * math.sin(t * math.pi * 6.0) + 0.08 * kick
            dx = (
                -point_radial_x * thrust
                + W_head * (16.0 * act_slow)
                + W_face_3d * (10.5 * act_slow)
                + chest_expand_x * (14.0 * breath + 16.0 * kick)
                + W_upper_body * (13.0 * math.sin(t * 2.8))
            )
            dy = (
                -point_radial_y * thrust
                + W_point_hand * (15.0 * math.cos(t * math.pi * 6.0))
                + W_head * (-13.0 * abs(act_slow) + 10.0 * beat_wave)
                + W_chest * (13.0 * breath + 15.0 * kick)
            )
        elif mode == "closeup_34":
            # Expressive 3/4 head turn (3D yaw) + chin raise + shoulder breathing + hair ripple
            yaw = 20.0 * math.sin(t * 3.2)
            pitch = -14.0 * math.cos(t * 2.6)
            hair_wave = 6.5 * np.sin(yy * 0.045 - t * 14.0) * W_hair_rim
            dx = W_head * yaw + W_face_3d * (yaw * 0.60) + chest_expand_x * (15.0 * breath + 15.0 * kick) + hair_wave
            dy = W_head * pitch + W_chest * (13.0 * breath + 16.0 * kick)
        elif mode == "profile_v9":
            # Side profile forward lean + chin tilt + jawline/neck pulse + hair wind
            lean = 18.0 * math.sin(t * 3.0)
            nod = -14.0 * math.cos(t * 3.4)
            hair_wave = 7.0 * np.sin(yy * 0.04 - t * 15.0) * W_hair_rim
            dx = W_upper_body * lean + W_head * (lean * 0.65) + hair_wave
            dy = W_head * nod + W_chest * (13.0 * breath + 15.0 * kick)
        elif mode == "sovereign_arms":
            # Arms-crossed boss stance expansion + confident head tilt + floating crown energy
            roll_rad = math.radians(2.8 * math.sin(t * 2.7))
            rot_dx = -(yy - 520.0) * math.sin(roll_rad) * W_head
            rot_dy = (xx - 540.0) * math.sin(roll_rad) * W_head
            dx = (
                rot_dx
                + W_face_3d * (12.0 * act_slow)
                + chest_expand_x * (18.0 * breath + 20.0 * kick)
                + W_upper_body * (14.0 * math.sin(t * 2.2))
            )
            dy = (
                rot_dy
                + W_head * (-13.0 * abs(breath) + 8.0 * beat_wave)
                + W_chest * (16.0 * breath + 18.0 * kick)
            )
        else:
            # Default "seated": 3D head turn/tilt + torso lean/sway + shoulder heave + clasped hands flex
            roll_rad = math.radians(3.0 * math.sin(t * 2.4 + 0.3))
            rot_dx = -(yy - 500.0) * math.sin(roll_rad) * W_head
            rot_dy = (xx - 540.0) * math.sin(roll_rad) * W_head
            yaw = 16.5 * act_slow
            pitch = -13.5 * math.sin(t * 2.1) + 9.0 * kick
            hair_wave = 5.5 * np.sin(yy * 0.05 - t * 12.0) * W_hair_rim
            dx = (
                rot_dx
                + W_head * yaw
                + W_face_3d * (yaw * 0.55)
                + W_upper_body * (15.5 * math.sin(t * 1.9))
                + chest_expand_x * (14.5 * breath + 17.0 * kick)
                + ((xx - 540.0) / 220.0) * W_hands_seated * (12.0 * beat_wave)
                + hair_wave
            )
            dy = (
                rot_dy
                + W_head * pitch
                + W_chest * (13.0 * breath + 16.0 * kick)
                + W_hands_seated * (-11.0 * abs(beat_wave) - 9.0 * kick)
            )

        # Notice: in remap, output(y, x) samples input(y - dy, x - dx)
        map_x = (xx - dx * W_subject_envelope).astype(np.float32)
        map_y = (yy - dy * W_subject_envelope).astype(np.float32)
        return cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    # -------------------------------------------------------------------------
    # WIDE THRONE HALL VARIATIONS (WITH WET FLOOR REFLECTIONS)
    # -------------------------------------------------------------------------
    red_w = wide[:, :, 0] - np.maximum(wide[:, :, 1], wide[:, :, 2])
    screen_matte = np.zeros((H, W), dtype=np.float32)
    screen_matte[740:1170, 235:845] = np.clip((red_w[740:1170, 235:845] - 45.0) / 70.0, 0.0, 1.0)
    screen_matte = cv2.GaussianBlur(screen_matte, (9, 9), 2.0)

    refl_matte = np.zeros((H, W), dtype=np.float32)
    refl_matte[1170:1650, 200:880] = np.clip((red_w[1170:1650, 200:880] - 35.0) / 70.0, 0.0, 1.0)
    refl_matte = cv2.GaussianBlur(refl_matte, (15, 15), 4.0)
    valid_wide_proj = np.clip(screen_matte + refl_matte, 0.0, 1.0)

    led_keep = np.clip((np.minimum(wide[:, :, 1], wide[:, :, 2]) - 140.0) / 80.0, 0.0, 1.0)[:, :, None]
    dark_hall = wide.copy()
    dark_hall[:, :, 0] *= 0.06
    dark_hall[:, :, 1] *= 0.08
    dark_hall[:, :, 2] *= 0.10
    wide_blackout = dark_hall * (1.0 - led_keep) + wide * led_keep
    cv2.circle(wide_blackout, (531, 922), 2, (255, 150, 45), -1, lineType=cv2.LINE_AA)
    cv2.circle(wide_blackout, (549, 922), 2, (255, 150, 45), -1, lineType=cv2.LINE_AA)

    wide_f013 = wide_blackout.copy()
    green_panel = np.zeros((H, W), dtype=np.float32)
    cv2.rectangle(green_panel, (145, 750), (225, 1150), 1.0, -1)
    cv2.rectangle(green_panel, (855, 750), (935, 1150), 1.0, -1)
    cv2.rectangle(green_panel, (145, 1200), (225, 1520), 0.35, -1)
    cv2.rectangle(green_panel, (855, 1200), (935, 1520), 0.35, -1)
    green_blur = cv2.GaussianBlur(green_panel, (25, 25), 8.0)
    for c, col in enumerate([165, 255, 35]):
        wide_f013[:, :, c] += (green_panel * 0.75 + green_blur * 0.45) * col
    wx_mask = np.zeros((H, W), dtype=np.float32)
    cv2.line(wx_mask, (310, 810), (770, 1120), 1.0, 26, lineType=cv2.LINE_AA)
    cv2.line(wx_mask, (310, 1120), (770, 810), 1.0, 26, lineType=cv2.LINE_AA)
    cv2.line(wx_mask, (310, 1240), (770, 1510), 0.45, 28, lineType=cv2.LINE_AA)
    cv2.line(wx_mask, (310, 1510), (770, 1240), 0.45, 28, lineType=cv2.LINE_AA)
    wx_blur = cv2.GaussianBlur(wx_mask, (21, 21), 7.0)
    for c, col in enumerate([255, 45, 15]):
        wide_f013[:, :, c] += (wx_mask * 0.9 + wx_blur * 0.6) * valid_wide_proj * col
    wide_f013 = np.clip(wide_f013, 0, 255)

    wide_f100 = wide_blackout.copy()
    bar_m = np.zeros((H, W), dtype=np.float32)
    cv2.rectangle(bar_m, (760, 680), (835, 1120), 1.0, -1)
    cv2.rectangle(bar_m, (760, 1210), (835, 1500), 0.4, -1)
    bar_blur = cv2.GaussianBlur(bar_m, (31, 31), 10.0)
    for c, col in enumerate([255, 52, 18]):
        wide_f100[:, :, c] += (bar_m * 0.85 + bar_blur * 0.5) * col
    wide_f100 = np.clip(wide_f100, 0, 255)

    wide_f106 = wide_blackout.copy()
    slash_m = np.zeros((H, W), dtype=np.float32)
    pts = np.array([[280, 1080], [440, 830], [790, 960], [720, 1150], [340, 1150]], np.int32)
    cv2.fillPoly(slash_m, [pts], 1.0)
    pts_r = np.array([[280, 1250], [440, 1480], [790, 1360], [720, 1200], [340, 1200]], np.int32)
    cv2.fillPoly(slash_m, [pts_r], 0.45)
    slash_blur = cv2.GaussianBlur(slash_m, (35, 35), 12.0)
    for c, col in enumerate([255, 92, 24]):
        wide_f106[:, :, c] += (slash_m * 0.95 + slash_blur * 0.6) * valid_wide_proj * col
    wide_f106 = np.clip(wide_f106, 0, 255)

    # -------------------------------------------------------------------------
    # DEPTH-AWARE BACKGROUND SCREEN PROJECTION COMPOSITING (BEHIND BLAZER & CABLES)
    # -------------------------------------------------------------------------
    redness_rs = med_rs[:, :, 0] - np.maximum(med_rs[:, :, 1], med_rs[:, :, 2])
    redness_rb = med_rb[:, :, 0] - np.maximum(med_rb[:, :, 1], med_rb[:, :, 2])
    redness = np.maximum(redness_rs, redness_rb)
    bg_matte = np.clip((redness - 95.0) / 85.0, 0.0, 1.0)
    bg_matte[1580:, :] = 0.0
    bg_matte = cv2.GaussianBlur(bg_matte, (7, 7), 1.5)
    bg3 = bg_matte[:, :, None]

    dark_bg = np.zeros_like(med_rs)
    dark_bg[:, :, 0], dark_bg[:, :, 1], dark_bg[:, :, 2] = 6.0, 2.0, 4.0
    fg_dark = med_rs.copy()
    fg_dark[:, :, 0] *= 0.42
    fg_dark[:, :, 1] *= 0.32
    fg_dark[:, :, 2] *= 0.34
    # Boost the glowing orange HUD visor region on med_rs so it shines brightly in blackout
    visor_boost = np.zeros((H, W), dtype=np.float32)
    cv2.ellipse(visor_boost, (538, 432), (88, 36), 0, 0, 360, 1.0, -1)
    visor_boost = cv2.GaussianBlur(visor_boost, (31, 31), 10.0)[:, :, None]
    fg_dark = np.clip(fg_dark + med_rs * visor_boost * 0.95, 0, 255)
    # Smoothly vignette below y=1300 so the throne pedestal base does not distract in blackout
    lower_vig = np.ones((H, W, 1), dtype=np.float32)
    lower_vig[1300:, :, 0] = np.linspace(1.0, 0.08, H - 1300, dtype=np.float32)[:, None]
    fg_dark = fg_dark * lower_vig
    locked_dv = np.clip(fg_dark * (1.0 - bg3) + dark_bg * bg3, 0, 255)

    np.random.seed(42)
    noise_low = cv2.GaussianBlur(np.random.rand(H // 4, W // 4).astype(np.float32), (9, 9), 2.5)
    grunge = cv2.resize(noise_low, (W, H), interpolation=cv2.INTER_LINEAR)

    def project_behind(base_plate: np.ndarray, graphic_mask: np.ndarray, color_rgb=(255, 64, 20), bg_darken: float = 0.18) -> np.ndarray:
        out = base_plate.copy()
        darkened_wall = out * bg_darken
        out = out * (1.0 - bg3) + darkened_wall * bg3
        g_blur = cv2.GaussianBlur(graphic_mask, (31, 31), 10.0)
        g_wide = cv2.GaussianBlur(graphic_mask, (91, 91), 32.0)
        vis_g = (graphic_mask * 0.88 + g_blur * 0.55 + g_wide * 0.35) * bg_matte
        for c in range(3):
            out[:, :, c] += vis_g * color_rgb[c]
        fg_edge = (1.0 - bg_matte) * cv2.GaussianBlur(bg_matte, (25, 25), 8.0)
        wrap = g_wide * fg_edge * 1.45
        for c in range(3):
            out[:, :, c] += wrap * color_rgb[c]
        return np.clip(out, 0, 255)

    slash_tr = np.zeros((H, W), dtype=np.float32)
    cv2.line(slash_tr, (620, 420), (1040, 80), 1.0, 78, lineType=cv2.LINE_AA)
    slash_tr *= np.clip(0.6 + 0.7 * grunge, 0.0, 1.2)
    med_slash_tr = project_behind(med_rs, slash_tr, color_rgb=(255, 72, 22), bg_darken=0.35)

    ring_m = np.zeros((H, W), dtype=np.float32)
    cv2.circle(ring_m, (540, 490), 275, 1.0, 44, lineType=cv2.LINE_AA)
    cv2.line(ring_m, (355, 740), (725, 240), 1.0, 46, lineType=cv2.LINE_AA)
    ring_m *= np.clip(0.65 + 0.75 * grunge, 0.0, 1.25)
    med_ring = project_behind(med_rs, ring_m, color_rgb=(255, 78, 26), bg_darken=0.42)

    x_m = np.zeros((H, W), dtype=np.float32)
    cv2.line(x_m, (80, 210), (980, 790), 1.0, 68, lineType=cv2.LINE_AA)
    cv2.line(x_m, (160, 830), (980, 170), 1.0, 72, lineType=cv2.LINE_AA)
    x_m *= np.clip(0.65 + 0.75 * grunge, 0.0, 1.25)
    med_x_cross = project_behind(locked_dv, x_m, color_rgb=(255, 72, 22), bg_darken=0.26)

    arc_m = np.zeros((H, W), dtype=np.float32)
    cv2.circle(arc_m, (540, 420), 340, 1.0, 58, lineType=cv2.LINE_AA)
    cv2.ellipse(arc_m, (620, 160), (380, 140), -12, 0, 360, 0.85, -1)
    arc_m *= np.clip(0.55 + 0.75 * grunge, 0.0, 1.2)
    med_arc = project_behind(locked_dv, arc_m, color_rgb=(255, 60, 18), bg_darken=0.15)

    rays_m = np.zeros((H, W), dtype=np.float32)
    for angle_deg in [-68, -42, -18, 8, 34, 62]:
        rad = np.deg2rad(angle_deg - 90)
        x2, y2 = int(540 + np.cos(rad) * 900), int(520 + np.sin(rad) * 900)
        cv2.line(rays_m, (540, 520), (x2, y2), 1.0, 54, lineType=cv2.LINE_AA)
    rays_m *= np.clip(0.65 + 0.6 * grunge, 0.0, 1.2)
    med_rays = project_behind(med_rs, rays_m, color_rgb=(255, 78, 22), bg_darken=0.20)

    close_34_laser = close_34.copy()
    lbar = np.zeros((H, W), dtype=np.float32)
    cv2.line(lbar, (380, 260), (620, 90), 1.0, 64, lineType=cv2.LINE_AA)
    lbar_blur = cv2.GaussianBlur(lbar, (45, 45), 16.0)
    for c, col in enumerate([255, 85, 35]):
        close_34_laser[:, :, c] += (lbar * 0.9 + lbar_blur * 0.65) * col
    close_34_laser = np.clip(close_34_laser, 0, 255)

    f431_base = close_cv * 0.25 + close_am * 0.15
    ring_f431 = np.zeros((H, W), dtype=np.float32)
    cv2.circle(ring_f431, (540, 920), 310, 1.0, 48, lineType=cv2.LINE_AA)
    cv2.line(ring_f431, (320, 1260), (740, 600), 1.0, 50, lineType=cv2.LINE_AA)
    ring_f431 *= np.clip(0.55 + 0.85 * grunge, 0.0, 1.25)
    r_blur = cv2.GaussianBlur(ring_f431, (35, 35), 12.0)
    for c, col in enumerate([255, 95, 65]):
        f431_base[:, :, c] += (ring_f431 * 0.95 + r_blur * 0.65) * col
    f431_plate = np.clip(f431_base, 0, 255)

    cable_zone = np.zeros((H, W), dtype=np.float32)
    cable_zone[440:1480, :360] = 1.0
    cable_zone[440:1480, 720:] = 1.0
    local_red_max = cv2.dilate(redness_rs, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35)))
    is_cable = (redness_rs < 55.0) & (local_red_max > 130.0) & (cable_zone > 0)
    cable_mask = cv2.GaussianBlur(is_cable.astype(np.float32), (9, 9), 2.2)

    u_coord = (xx - W * 0.52) * 0.88 + (yy - H * 0.50) * 0.47
    np.random.seed(7)
    streak_1d = cv2.GaussianBlur(np.random.rand(1, 256).astype(np.float32), (1, 15), 3.0)
    streak_tex = cv2.resize(streak_1d, (W, H), interpolation=cv2.INTER_LINEAR)
    streak_mod = 0.72 + 0.52 * streak_tex

    face_keep = np.zeros((H, W), dtype=np.float32)
    cv2.ellipse(face_keep, (540, 460), (155, 195), 0, 0, 360, 0.44, -1)
    face_keep = cv2.GaussianBlur(face_keep, (51, 51), 18.0)[:, :, None]

    def render_prismatic_flare(base_img: np.ndarray, sweep_offset: float, intensity: float) -> np.ndarray:
        u = u_coord - sweep_offset
        b_core = np.exp(-(u - 20.0) ** 2 / (2.0 * 125.0 ** 2))
        b_cyan = np.exp(-(u + 150.0) ** 2 / (2.0 * 165.0 ** 2))
        b_gold = np.exp(-(u - 135.0) ** 2 / (2.0 * 145.0 ** 2))
        b_mag = np.exp(-(u - 245.0) ** 2 / (2.0 * 120.0 ** 2))
        flare = np.zeros((H, W, 3), dtype=np.float32)
        flare[:, :, 0] = (b_core * 215 + b_gold * 255 + b_mag * 210 + b_cyan * 40) * streak_mod
        flare[:, :, 1] = (b_core * 230 + b_gold * 195 + b_cyan * 235 + b_mag * 55) * streak_mod
        flare[:, :, 2] = (b_core * 250 + b_cyan * 255 + b_mag * 225 + b_gold * 85) * streak_mod
        eff_int = intensity * (1.0 - face_keep)
        out = base_img * (1.0 - 0.25 * eff_int) + flare * eff_int
        return chromatic_aberration(np.clip(out, 0, 255), shift_px=6.0 * intensity)

    def render_tension_blackout(fno: int) -> np.ndarray:
        p = (fno - 109) / 35.0
        pulse = 0.10 + 0.16 * (math.sin(p * math.pi * 4.0) ** 2) + (0.42 * (p ** 3) if p > 0.65 else 0.0)
        moved = articulate_body(locked_dv, fno, mode="seated", beat_kick=0.35 * pulse)
        frame = moved * pulse
        if fno >= 122:
            hp = min(1.0, (fno - 122) / 18.0)
            pil_f = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8))
            draw = ImageDraw.Draw(pil_f)
            c_hud = (int(255 * hp), int(120 * hp), int(35 * hp))
            pad = int((1.0 - hp) * 45)
            x1, y1, x2, y2 = 395 - pad, 395 - pad, 685 + pad, 475 + pad
            blen = 24
            draw.line([(x1, y1), (x1 + blen, y1)], fill=c_hud, width=2)
            draw.line([(x1, y1), (x1, y1 + blen)], fill=c_hud, width=2)
            draw.line([(x2, y1), (x2 - blen, y1)], fill=c_hud, width=2)
            draw.line([(x2, y1), (x2, y1 + blen)], fill=c_hud, width=2)
            draw.line([(x1, y2), (x1 + blen, y2)], fill=c_hud, width=2)
            draw.line([(x1, y2), (x1, y2 - blen)], fill=c_hud, width=2)
            draw.line([(x2, y2), (x2 - blen, y2)], fill=c_hud, width=2)
            draw.line([(x2, y2), (x2, y2 - blen)], fill=c_hud, width=2)
            try:
                fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
            except Exception:
                fnt = ImageFont.load_default()
            pct = int(min(100, round(hp * 100)))
            draw.text((405, y2 + 12), f"MONARCH_OS // NEURAL SYNC {pct:03d}%", fill=c_hud, font=fnt)
            frame = np.array(pil_f, dtype=np.float32)
        return frame

    print("Mastering spatial audio track...")
    audio_path, audio_metrics = build_master_audio()
    print("Audio metrics:", audio_metrics)

    out_mp4 = PAYLOAD / "MONARCH_CHAOS_VIDEO_1_MASTER.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-",
        "-i", str(audio_path),
        "-c:v", "libx264", "-preset", "medium", "-crf", "16",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart",
        "-shortest",
        str(out_mp4),
        "-loglevel", "warning",
    ]

    print(f"Rendering {TOTAL_FRAMES} frames at {W}x{H} @ {FPS}fps with 2.5D articulated body motion & Crown finale...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None

    contact_frames: list[tuple[int, np.ndarray]] = []
    look_samples: dict[str, np.ndarray] = {}

    for fno in range(1, TOTAL_FRAMES + 1):
        t = (fno - 1) / float(FPS)

        if fno <= 108:
            p = (fno - 1) / 107.0
            zoom = 1.00 + 0.25 * (p ** 1.15)
            if fno in (10, 11, 12, 29, 30, 31, 32, 33, 34, 46, 47, 48, 49, 50, 51, 64, 65, 66, 67, 68, 83, 84, 85, 86, 87):
                base = wide_blackout
            elif fno in (13, 14, 15):
                base = wide_f013
            elif 98 <= fno <= 105:
                base = wide_f100
            elif 106 <= fno <= 108:
                base = wide_f106
            else:
                base = articulate_body(wide, fno, mode="wide", beat_kick=0.3 if fno % 12 < 3 else 0.0)
            frame = zoom_pan(base, zoom=zoom, cx=W * 0.5, cy=H * 0.50)

        elif fno <= 144:
            frame = render_tension_blackout(fno)

        elif fno <= 283:
            p = (fno - 145) / (283 - 145)
            zoom = 1.00 + 0.07 * p
            kick = 0.0
            if fno in (145, 146):
                base = med_slash_tr
                kick = 0.8
            elif fno in (161, 162):
                base = med_ring
                kick = 0.85
            elif fno in (203, 204, 209, 210):
                base = med_x_cross
                kick = 0.9
            elif 245 <= fno <= 250:
                base = med_arc
                kick = 0.65
            elif 263 <= fno <= 265:
                base = med_rays
                kick = 0.8
            elif (224 <= fno <= 230) or (238 <= fno <= 244) or (252 <= fno <= 258):
                base = med_rb
                zoom += 0.03
                kick = 0.55
            elif (217 <= fno <= 223) or (231 <= fno <= 237):
                base = med_dv_tactical
            elif fno in (147, 148, 153, 154, 155, 156, 163, 164, 169, 170, 171, 172, 177, 178, 179, 180, 185, 186, 187, 188, 193, 194, 195, 196, 201, 202, 211, 212, 251, 259, 260, 261, 262, 273, 274, 275, 276, 277, 278, 279):
                base = locked_dv
            else:
                base = med_rs

            # Apply 2.5D articulated body, shoulder, chest, head & hand motion!
            frame = articulate_body(base, fno, mode="seated", beat_kick=kick)

            wave_y = H * (1.0 - ((t * 1.85) % 1.0))
            pulse_band = np.exp(-((yy - wave_y) ** 2) / (2.0 * 95.0 ** 2))
            cable_glow = cable_mask * pulse_band * 1.45
            frame[:, :, 0] += cable_glow * 255.0
            frame[:, :, 1] += cable_glow * 55.0
            frame[:, :, 2] += cable_glow * 25.0
            frame = np.clip(frame, 0, 255)
            if kick >= 0.75:
                frame = chromatic_aberration(frame, shift_px=3.0 * kick)
            frame = zoom_pan(frame, zoom=zoom, dx=8.0 * math.sin(t * 2.1), dy=-5.0 * math.cos(t * 1.8), cx=W * 0.5, cy=H * 0.42)

        elif fno <= 369:
            if 284 <= fno <= 290:
                p = (fno - 284) / 6.0
                moved = articulate_body(close_34, fno, mode="closeup_34", beat_kick=0.6)
                frame = zoom_pan(moved, zoom=1.02 + 0.05 * p, dx=-10.0 * (1.0 - p))
            elif 291 <= fno <= 294:
                moved = articulate_body(med_rb, fno, mode="seated", beat_kick=0.5)
                frame = zoom_pan(moved, zoom=1.06)
            elif 295 <= fno <= 296:
                moved = articulate_body(locked_dv, fno, mode="seated", beat_kick=0.4)
                frame = zoom_pan(moved, zoom=1.06)
            elif 297 <= fno <= 298:
                moved = articulate_body(med_rays, fno, mode="seated", beat_kick=0.8)
                frame = zoom_pan(moved, zoom=1.07)
            elif 299 <= fno <= 300:
                moved = articulate_body(med_rb, fno, mode="seated", beat_kick=0.5)
                frame = zoom_pan(moved, zoom=1.07)
            elif 301 <= fno <= 307:
                if fno <= 304:
                    p = (fno - 301) / 3.0
                    moved = articulate_body(side_prof, fno, mode="profile_v9", beat_kick=0.65)
                    frame = zoom_pan(moved, zoom=1.03 + 0.04 * p, dx=12.0 * (1.0 - p))
                else:
                    p = (fno - 305) / 2.0
                    moved = articulate_body(close_34, fno, mode="closeup_34", beat_kick=0.6)
                    frame = zoom_pan(moved, zoom=1.04 + 0.03 * p)
            elif 308 <= fno <= 310:
                moved = articulate_body(med_rb, fno, mode="seated", beat_kick=0.5)
                frame = zoom_pan(moved, zoom=1.08)
            elif 311 <= fno <= 314:
                moved = articulate_body(med_dv_tactical, fno, mode="seated", beat_kick=0.4)
                frame = zoom_pan(moved, zoom=1.08)
            elif fno == 315:
                moved = articulate_body(med_rb, fno, mode="seated", beat_kick=0.7)
                frame = zoom_pan(moved, zoom=1.09)
            elif 316 <= fno <= 321:
                p = (fno - 316) / 5.0
                moved = articulate_body(close_34, fno, mode="closeup_34", beat_kick=0.65)
                frame = zoom_pan(moved, zoom=1.03 + 0.05 * p)
            elif fno == 322:
                moved = articulate_body(close_34_laser, fno, mode="closeup_34", beat_kick=0.95)
                frame = chromatic_aberration(zoom_pan(moved, zoom=1.09), shift_px=4.0)
            elif 323 <= fno <= 326:
                moved = articulate_body(med_rb, fno, mode="seated", beat_kick=0.5)
                frame = zoom_pan(moved, zoom=1.09)
            else:
                idx = fno - 327
                cycle = (idx // 4) % 2
                p = (fno - 327) / 42.0
                zoom = 1.00 + 0.09 * p
                if cycle == 0:
                    base = med_dv_tactical if (idx // 8) % 2 == 0 else locked_dv
                    moved = articulate_body(base, fno, mode="seated", beat_kick=0.45)
                    frame = zoom_pan(moved, zoom=zoom)
                else:
                    base = med_rb if fno <= 334 else close_am
                    moved = articulate_body(base, fno, mode="seated", beat_kick=0.75)
                    frame = zoom_pan(moved, zoom=zoom)

        elif fno <= 432:
            if 370 <= fno <= 376:
                # Crisp action cut: Pointing at Camera 🫵 (370..373) -> Seated Cyan Boss Smirk (374..376)
                if fno <= 373:
                    base = articulate_body(close_cv, fno, mode="point_action", beat_kick=0.9)
                    frame = zoom_pan(base, zoom=1.02 + 0.025 * (fno - 370))
                else:
                    base = articulate_body(close_cy, fno, mode="seated", beat_kick=0.7)
                    frame = zoom_pan(base, zoom=1.03 + 0.015 * (fno - 374))
            elif 377 <= fno <= 383:
                moved = articulate_body(close_am, fno, mode="seated", beat_kick=0.6)
                frame = zoom_pan(moved, zoom=1.04)
            elif 384 <= fno <= 390:
                p = (fno - 384) / 6.0
                moved = articulate_body(close_cy, fno, mode="seated", beat_kick=0.7)
                frame = zoom_pan(moved, zoom=1.04 + 0.04 * p)
            elif 391 <= fno <= 397:
                if fno in (395, 396):
                    moved = articulate_body(side_prof, fno, mode="profile_v9", beat_kick=0.75)
                    frame = zoom_pan(moved, zoom=1.06)
                else:
                    moved = articulate_body(close_am, fno, mode="seated", beat_kick=0.6)
                    frame = zoom_pan(moved, zoom=1.06)
            elif 398 <= fno <= 404:
                if fno >= 401:
                    base = articulate_body(close_cv, fno, mode="point_action", beat_kick=0.9)
                else:
                    base = articulate_body(close_cy, fno, mode="seated", beat_kick=0.7)
                if fno >= 403:
                    base = render_prismatic_flare(base, sweep_offset=220.0 - (fno - 403) * 60.0, intensity=0.38)
                frame = zoom_pan(base, zoom=1.07)
            elif 405 <= fno <= 411:
                moved = articulate_body(close_am, fno, mode="seated", beat_kick=0.65)
                frame = zoom_pan(moved, zoom=1.08)
            elif 412 <= fno <= 418:
                intensities = {412: 0.45, 413: 0.78, 414: 0.96, 415: 0.88, 416: 0.75, 417: 0.65, 418: 0.40}
                sweep = (fno - 414) * 55.0
                if fno % 2 == 0:
                    base = articulate_body(close_cv, fno, mode="point_action", beat_kick=0.95)
                else:
                    base = articulate_body(close_cy, fno, mode="seated", beat_kick=0.85)
                frame = render_prismatic_flare(base, sweep_offset=sweep, intensity=intensities[fno])
                frame = zoom_pan(frame, zoom=1.09)
            elif 419 <= fno <= 425:
                if fno >= 423:
                    moved = articulate_body(sovereign, fno, mode="sovereign_arms", beat_kick=0.85)
                    frame = zoom_pan(moved, zoom=1.08)
                else:
                    moved = articulate_body(close_am, fno, mode="seated", beat_kick=0.65)
                    frame = zoom_pan(moved, zoom=1.08)
            elif 426 <= fno <= 430:
                sweep = -180.0 - (fno - 426) * 45.0
                moved = articulate_body(close_cv, fno, mode="point_action", beat_kick=0.8)
                frame = render_prismatic_flare(moved * 0.58, sweep_offset=sweep, intensity=0.58)
            else:
                moved = articulate_body(f431_plate, fno, mode="point_action", beat_kick=0.9)
                frame = zoom_pan(moved, zoom=1.0 + 0.03 * (fno - 431))

        else:
            if 433 <= fno <= 525:
                p = (fno - 433) / float(525 - 433)
                glow_a = 1.0 - 0.30 * (p ** 1.5)
                frame = build_emblem_frame(alpha_glow=glow_a, crown_boost=0.5, fno=fno)
                if fno <= 442:
                    carry = (443 - fno) / 10.0
                    frame[:, :, 1] += 12.0 * carry
                    frame[:, :, 2] += 18.0 * carry
                    frame = np.clip(frame, 0, 255)
            elif 526 <= fno <= 558:
                idx = fno - 526
                if fno in (526, 527):
                    moved = articulate_body(sovereign, fno, mode="sovereign_arms", beat_kick=1.0)
                    frame = np.clip(moved * 1.35 + 45.0, 0, 255)
                elif fno in (536, 537, 538):
                    moved = articulate_body(side_prof, fno, mode="profile_v9", beat_kick=0.8)
                    frame = zoom_pan(moved, zoom=1.08)
                elif fno in (544, 545, 546):
                    moved = articulate_body(close_34_laser, fno, mode="closeup_34", beat_kick=0.9)
                    frame = zoom_pan(moved, zoom=1.08)
                else:
                    p = idx / 32.0
                    moved = articulate_body(sovereign, fno, mode="sovereign_arms", beat_kick=0.75)
                    frame = zoom_pan(moved, zoom=1.02 + 0.09 * p)
            else:
                p = (fno - 559) / float(TOTAL_FRAMES - 559)
                emb = build_emblem_frame(alpha_glow=max(0.42, 1.0 - 0.45 * (p ** 1.6)), crown_boost=1.0, fno=fno)
                if fno <= 562:
                    # Never blend the Crown/sigil/title *over the actor's face*.
                    # Two hero-only frames, one full-frame molten-gold shutter, then
                    # an emblem-only afterglow make a clean 4-frame lightning cut.
                    gold_flash = np.empty_like(emb)
                    gold_flash[:, :, 0] = 255.0
                    gold_flash[:, :, 1] = 205.0
                    gold_flash[:, :, 2] = 75.0
                    if fno <= 560:
                        moved_sov = articulate_body(sovereign, fno, mode="sovereign_arms", beat_kick=1.0)
                        hero_z = zoom_pan(moved_sov, zoom=1.12 + 0.05 * (fno - 559))
                        flare = 0.08 if fno == 559 else 0.36
                        frame = hero_z * (1.0 - flare) + gold_flash * flare
                    elif fno == 561:
                        frame = np.clip(gold_flash * 0.93 + emb * 0.10, 0, 255)
                    else:
                        frame = np.clip(emb * 0.86 + gold_flash * 0.14, 0, 255)
                else:
                    frame = emb

        frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
        proc.stdin.write(frame_u8.tobytes())

        if (fno - 1) % 15 == 0:
            contact_frames.append((fno, frame_u8.copy()))
        if fno in (16, 138, 161, 209, 241, 286, 302, 340, 372, 414, 455, 532):
            look_samples[f"F{fno:03d}"] = frame_u8.copy()

    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg exited with code {rc}")
    print(f"Successfully rendered {out_mp4} ({out_mp4.stat().st_size:,} bytes)")

    cols, rows_cnt = 7, 6
    cw, ch = 270, 480
    cs = Image.new("RGB", (cols * cw, rows_cnt * ch), (10, 10, 12))
    cs_draw = ImageDraw.Draw(cs)
    for i, (fno, rgb) in enumerate(contact_frames[:42]):
        im = Image.fromarray(rgb).resize((cw, ch), Image.Resampling.LANCZOS)
        r_i, c_i = divmod(i, cols)
        cs.paste(im, (c_i * cw, r_i * ch))
        cs_draw.rectangle([c_i * cw, r_i * ch, c_i * cw + 118, r_i * ch + 26], fill=(0, 0, 0))
        cs_draw.text((c_i * cw + 6, r_i * ch + 5), f"F{fno:03d} {(fno-1)/FPS:04.1f}s", fill=(0, 255, 200))
    cs.save(PAYLOAD / "MONARCH_CHAOS_VIDEO_1_CONTACT_SHEET.jpg", quality=93)

    lw, lh = 360, 640
    ls = Image.new("RGB", (6 * lw, 2 * lh), (8, 8, 10))
    ls_draw = ImageDraw.Draw(ls)
    ordered_keys = ["F016", "F138", "F161", "F209", "F241", "F286", "F302", "F340", "F372", "F414", "F455", "F532"]
    labels = {
        "F016": "0.5s · WIDE THRONE HALL",
        "F138": "4.6s · NEURAL SYNC HUD",
        "F161": "5.3s · CHAOS Ø PROJECTION",
        "F209": "6.9s · X-CROSS + VISOR HUD",
        "F241": "8.0s · CRIMSON/BLUE REVEAL",
        "F286": "9.5s · 3/4 CLOSE-UP",
        "F302": "10.0s · SIDE PROFILE V9",
        "F340": "11.3s · FIERY SILHOUETTE",
        "F372": "12.4s · POINTING ACTION 🫵",
        "F414": "13.8s · PRISMATIC FLARE",
        "F455": "15.1s · 👑 MONARCH STUDIO",
        "F532": "17.7s · SOVEREIGN CROWN",
    }
    for i, k in enumerate(ordered_keys):
        if k not in look_samples:
            continue
        im = Image.fromarray(look_samples[k]).resize((lw, lh), Image.Resampling.LANCZOS)
        r_i, c_i = divmod(i, 6)
        ls.paste(im, (c_i * lw, r_i * lh))
        ls_draw.rectangle([c_i * lw, r_i * lh, c_i * lw + 260, r_i * lh + 32], fill=(0, 0, 0))
        ls_draw.text((c_i * lw + 8, r_i * lh + 8), labels[k], fill=(255, 210, 60))
    ls.save(PAYLOAD / "MONARCH_CHAOS_VIDEO_1_LOOK_SHEET.jpg", quality=95)
    print("Saved Contact Sheet and Look Sheet.")


if __name__ == "__main__":
    main()
