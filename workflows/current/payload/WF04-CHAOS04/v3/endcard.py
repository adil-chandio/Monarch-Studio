#!/usr/bin/env python3
"""
CHAOS · NEXT FILM — v3 end card.

The reference film ends on ITS creator's Instagram card. We do not recycle that:
frames 1275..1331 are replaced with our own card — our crest, our wordmark, our
credit line. Drawn here with PIL, no external asset.

Output: v3/card/f_%04d.png  (1080x1920, 30 fps, 57 frames = 1.90 s)
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "card"
FONT = "/usr/local/lib/python3.11/dist-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans-Bold.ttf"
FONT_L = "/usr/local/lib/python3.11/dist-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf"
W, H = 1080, 1920
N = 57


def crescent_mask(w, h, R, tube, bow=0.30, arc=(-72, 72)):
    """Anti-aliased crescent, drawn 4x then downsampled."""
    ss = 4
    img = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(img)
    cx, cy = w * ss / 2, h * ss / 2
    R *= ss
    steps = 90
    outer, inner = [], []
    for i in range(steps + 1):
        t = i / steps
        a = math.radians(arc[0] + (arc[1] - arc[0]) * t)
        th = tube * ss * (math.sin(math.pi * t) ** 0.7)
        z = bow * ss * (1 - math.cos(a))
        for dx, dy, lst in ((R + th, 0, outer), (R - th, 0, inner)):
            lst.append((cx + math.sin(a) * dx, cy - math.cos(a) * dx * 0.16 + z))
    d.polygon(outer + inner[::-1], fill=255)
    return img.resize((w, h), Image.LANCZOS)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    f_big = ImageFont.truetype(FONT, 132)
    f_mid = ImageFont.truetype(FONT_L, 44)
    f_small = ImageFont.truetype(FONT_L, 30)

    for i in range(N):
        t = i / 30.0
        # fade in over 0.55 s, hold, tiny fade at the very end
        fade = min(1.0, t / 0.55)
        if t > 1.72:
            fade *= max(0.0, 1.0 - (t - 1.72) / 0.18)

        base = Image.new("RGB", (W, H), (4, 3, 4))
        # ember glow behind the crest
        glow = Image.new("RGB", (W, H), (0, 0, 0))
        gd = ImageDraw.Draw(glow)
        pulse = 0.86 + 0.14 * math.sin(t * 5.4)
        gd.ellipse([W / 2 - 300, 700, W / 2 + 300, 1180],
                   fill=(int(150 * pulse), int(16 * pulse), int(8 * pulse)))
        glow = glow.filter(ImageFilter.GaussianBlur(120))
        base = Image.blend(base, glow, 0.55 * fade)

        mask = crescent_mask(W, H, 210, 26, bow=0.26)
        crest = Image.new("RGB", (W, H), (0, 0, 0))
        crest.paste((255, 96, 52), (0, 0), mask)
        crest = crest.filter(ImageFilter.GaussianBlur(1.2))
        hot = crest.filter(ImageFilter.GaussianBlur(26))
        base = Image.blend(base, hot, 0.55 * fade)
        base = Image.blend(base, crest, 0.92 * fade)

        d = ImageDraw.Draw(base)
        title = "MONARCH"
        tw = d.textlength(title, font=f_big)
        col = tuple(int(c * fade) for c in (240, 236, 234))
        d.text((W / 2 - tw / 2, 1005), title, font=f_big, fill=col)

        sub = "CHAOS  ·  NEXT FILM"
        sw = d.textlength(sub, font=f_mid)
        d.text((W / 2 - sw / 2, 1180), sub, font=f_mid,
               fill=tuple(int(c * fade) for c in (198, 74, 44)))

        line_w = 260 * fade
        d.line([W / 2 - line_w, 1268, W / 2 + line_w, 1268],
               fill=tuple(int(c * fade) for c in (120, 40, 26)), width=2)

        tail = "ORIGINAL 3D BUILD  ·  ALL FRAMES OURS"
        tw2 = d.textlength(tail, font=f_small)
        d.text((W / 2 - tw2 / 2, 1305), tail, font=f_small,
               fill=tuple(int(c * fade * 0.8) for c in (170, 168, 168)))

        # fine grain so the card sits in the same film stock
        arr = np.asarray(base).astype(np.int16)
        arr += np.random.default_rng(1000 + i).normal(0, 3.0, arr.shape).astype(np.int16)
        Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(
            OUT / f"f_{1275 + i:04d}.png")
    print(f"CARD ok  {N} frames -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
