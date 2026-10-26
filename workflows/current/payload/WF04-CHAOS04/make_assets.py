#!/usr/bin/env python3
"""CHAOS 04 graphic assets: light leaks, impact flash, crown emblem end card.

Built to the delivered CHAOS 03 look: heavy edges of red/blue/magenta light,
gold crowned MONARCH STUDIO emblem on a star field.
"""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / 'assets'
OUT.mkdir(exist_ok=True)
REPO = HERE.parents[3]
FONTS = REPO / 'styles' / 'premium-motion-editing' / 'assets' / 'fonts'
W, H = 1080, 1920


def leak(name: str, cx: float, cy: float, rx: float, ry: float, colour, peak: int,
         streak: float = 0.0, angle: float = 0.0) -> Path:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    xx = xx / W; yy = yy / H
    dx, dy = (xx - cx), (yy - cy)
    if angle:
        ca, sa = math.cos(angle), math.sin(angle)
        dx, dy = dx * ca - dy * sa, dx * sa + dy * ca
    d = np.sqrt((dx / rx) ** 2 + (dy / ry) ** 2)
    a = np.clip(1.0 - d, 0, 1) ** 2.2
    if streak:
        band = np.exp(-((dy / (ry * .18)) ** 2)) * np.clip(1 - np.abs(dx) / rx, 0, 1) ** 1.4
        a = np.clip(a + streak * band, 0, 1)
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = colour
    rgba[..., 3] = (a * peak).astype(np.uint8)
    im = Image.fromarray(rgba, 'RGBA').filter(ImageFilter.GaussianBlur(26))
    p = OUT / name
    im.save(p)
    return p


def flash() -> Path:
    im = Image.new('RGBA', (W, H), (255, 244, 232, 255))
    p = OUT / 'flash.png'
    im.save(p)
    return p


def emblem() -> Path:
    """Gold crowned MONARCH STUDIO mark on a deep cosmic plate."""
    rng = np.random.default_rng(11)
    base = Image.new('RGB', (W, H), (4, 5, 12))
    d = ImageDraw.Draw(base)
    # star field + faint nebula
    for _ in range(900):
        x, y = rng.integers(0, W), rng.integers(0, H)
        v = int(rng.integers(40, 190))
        d.point((x, y), fill=(v, v, min(255, v + 20)))
    neb = Image.new('RGB', (W, H), (0, 0, 0))
    nd = ImageDraw.Draw(neb)
    nd.ellipse([W * .05, H * .18, W * .95, H * .82], fill=(14, 10, 34))
    nd.ellipse([W * .30, H * .30, W * .70, H * .70], fill=(26, 16, 44))
    base = Image.blend(base, neb.filter(ImageFilter.GaussianBlur(180)), .55)

    cx, cy = W // 2, int(H * .40)

    # sunburst rays behind the crown (the delivered CHAOS 03 end card has them)
    rays = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rays)
    for k in range(48):
        a = 2 * math.pi * k / 48 + .04
        long_ray = k % 2 == 0
        r0, r1 = 190, (620 if long_ray else 430)
        spread = .026 if long_ray else .018
        tip = (cx + r1 * math.cos(a), cy + r1 * math.sin(a) * .92)
        p1 = (cx + r0 * math.cos(a - spread), cy + r0 * math.sin(a - spread) * .92)
        p2 = (cx + r0 * math.cos(a + spread), cy + r0 * math.sin(a + spread) * .92)
        rd.polygon([tip, p1, p2], fill=(255, 196, 92, 105 if long_ray else 64))
    rays = rays.filter(ImageFilter.GaussianBlur(2.5))
    base = Image.alpha_composite(base.convert('RGBA'), rays.filter(ImageFilter.GaussianBlur(16)))
    base = Image.alpha_composite(base, rays).convert('RGB')

    mark = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = ImageDraw.Draw(mark)
    gold, gold_hi, gold_lo = (255, 208, 96, 255), (255, 240, 190, 255), (196, 138, 32, 255)

    # crown: three peaks + jewels + band
    cw, ch = 250, 150
    top = cy - 40
    crown = [(cx - cw, top + 62), (cx - cw * .66, top - 44), (cx - cw * .30, top + 40),
             (cx, top - 74), (cx + cw * .30, top + 40), (cx + cw * .66, top - 44),
             (cx + cw, top + 62), (cx + cw, top + 112), (cx - cw, top + 112)]
    m.polygon(crown, fill=gold, outline=gold_hi)
    m.line(crown + [crown[0]], fill=gold_hi, width=3, joint='curve')
    for jx in (-.66, 0, .66):
        m.ellipse([cx + jx * cw - 13, top - 62 if jx == 0 else top - 40,
                   cx + jx * cw + 13, top - 36 if jx == 0 else top - 14], fill=gold_hi)
    m.rectangle([cx - cw, top + 118, cx + cw, top + 132], fill=gold_lo)

    # lattice diamond below the crown
    ly = top + 232
    lw, lh = 142, 128
    m.polygon([(cx, ly - lh), (cx + lw, ly), (cx, ly + lh), (cx - lw, ly)],
              outline=gold, width=3)
    grid = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    step = 34
    for k in range(-lw, lw, step):
        gd.line([(cx + k, ly - (lh - abs(k) * lh / lw)), (cx + k, ly + (lh - abs(k) * lh / lw))],
                fill=(255, 208, 96, 190), width=2)
    for k in range(-lh, lh, step):
        gd.line([(cx - (lw - abs(k) * lw / lh), ly + k), (cx + (lw - abs(k) * lw / lh), ly + k)],
                fill=(255, 208, 96, 190), width=2)
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).polygon([(cx, ly - lh), (cx + lw, ly), (cx, ly + lh), (cx - lw, ly)], fill=255)
    grid.putalpha(Image.composite(grid.getchannel('A'), Image.new('L', (W, H), 0), mask))
    mark = Image.alpha_composite(mark, grid)
    m = ImageDraw.Draw(mark)

    big = ImageFont.truetype(str(FONTS / 'Anton-Regular.ttf'), 92)
    small = ImageFont.truetype(str(FONTS / 'BarlowCondensed-Medium.ttf'), 34)
    tiny = ImageFont.truetype(str(FONTS / 'BarlowCondensed-MediumItalic.ttf'), 26)
    t1 = 'MONARCH STUDIO'
    w1 = m.textlength(t1, font=big)
    m.text(((W - w1) / 2, ly + lh + 58), t1, font=big, fill=(255, 236, 186, 255))
    t2 = 'PREMIUM EDITORIAL  ·  VFX'
    w2 = m.textlength(t2, font=small)
    m.text(((W - w2) / 2, ly + lh + 176), t2, font=small, fill=(212, 174, 96, 255))
    t3 = 'CHAOS 04'
    w3 = m.textlength(t3, font=tiny)
    m.text(((W - w3) / 2, ly + lh + 226), t3, font=tiny, fill=(150, 126, 84, 255))

    glow = mark.filter(ImageFilter.GaussianBlur(34))
    comp = Image.alpha_composite(base.convert('RGBA'), glow)
    comp = Image.alpha_composite(comp, mark)
    p = OUT / 'emblem.png'
    comp.save(p)
    return p


if __name__ == '__main__':
    made = [
        leak('leak_red_left.png', .02, .5, .46, 1.05, (255, 34, 34), 168, streak=.55),
        leak('leak_blue_right.png', .99, .46, .42, 1.0, (46, 92, 255), 150, streak=.4),
        leak('leak_magenta_left.png', .03, .58, .38, .9, (255, 42, 168), 132, streak=.3),
        leak('leak_gold_top.png', .5, .04, .95, .30, (255, 186, 84), 96),
        leak('leak_cyan_bottom.png', .55, .97, .9, .26, (64, 200, 255), 74),
        flash(), emblem(),
    ]
    for p in made:
        print(p.relative_to(HERE), p.stat().st_size)
