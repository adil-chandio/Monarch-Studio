#!/usr/bin/env python3
"""stick_keyframes — poori video ke stickman keyframes (locked BUDDY, chalk on board).

Style authority: styles/monarch-stickman-animation (CHARACTER_SPEC v1).
Hero: seed 101, CHALK body, GOLD cap marker, hoodie — kabhi redesign nahi.

Ye frames hi I2V model ka pehla frame bante hain: model in images ko animate karta hai
(har aage ka frame AI se aata hai, koi slideshow nahi).

Kaam:  python3 tools/stick_keyframes.py --out studio/films/stick-i2v/keyframes
"""

from __future__ import annotations

import argparse
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
STYLE = ROOT / "styles" / "monarch-stickman-animation"
W, H = 1080, 1920


def link_renderer() -> None:
    """Renderer hardcoded /home/user/src aur /home/user/fonts maangta hai."""
    for name, target in (("src", STYLE / "src"), ("fonts", STYLE / "fonts")):
        link = pathlib.Path("/home/user") / name
        if not link.exists():
            link.symlink_to(target)
    sys.path.insert(0, str(STYLE / "src"))


link_renderer()

import numpy as np                                    # noqa: E402
from PIL import Image, ImageDraw, ImageFilter         # noqa: E402
from stickbase import (BOARD, GRAIN, CHALK, GOLD, CYAN, MINT, RED,        # noqa: E402
                       arc, box, circ, coin, laptop, poly, squiggle, star,
                       stick, tick, cross, clamp,
                       pose_idle, pose_sad, pose_walk, pose_shake,
                       pose_point, pose_think, pose_type, pose_cheer, pose_dance)
from character import hero, CHAR                       # noqa: E402

EXTRAS = (211, 231, 233, 235)      # crowd / client seeds (never the hero's 101)


# --------------------------------------------------------------------------- #
# board + finishing
# --------------------------------------------------------------------------- #

def board() -> Image.Image:
    """Near-black chalkboard with soft light falloff (renderer ka baked board)."""
    return BOARD.copy().convert("RGB")


def speckle(cv: Image.Image, n: int = 900, seed: int = 3) -> None:
    """Board par halka chalk dust — I2V ko texture pakadne me madad karta hai."""
    d = ImageDraw.Draw(cv)
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = rng.integers(0, W), rng.integers(0, H)
        a = int(rng.integers(10, 34))
        d.point((int(x), int(y)), fill=(200, 205, 215, a))
    del d


def finish(cv: Image.Image) -> Image.Image:
    """Grain + vignette: cinematic, magar camera move nahi (I2V khud motion dega)."""
    arr = np.asarray(cv).astype(np.float32)
    g = np.asarray(GRAIN)[:, :, 0]
    g = np.repeat(np.repeat(g, 2, axis=0), 2, axis=1)[:H, :W]
    arr += (g * 3.4)[:, :, None]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H * 0.46
    r = np.sqrt(((xx - cx) / (W * 0.78)) ** 2 + ((yy - cy) / (H * 0.72)) ** 2)
    vig = np.clip(1.06 - 0.42 * r ** 2.1, 0.42, 1.0)
    arr *= vig[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def ground_shadow(cv: Image.Image, cx: int, cy: int, rw: int, rh: int = 26) -> None:
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((cx - rw, cy - rh, cx + rw, cy + rh), fill=(0, 0, 0, 120))
    cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))


def glow(cv: Image.Image, layer: Image.Image, radius: int = 18) -> None:
    """Chalk ka halka bloom."""
    blur = layer.filter(ImageFilter.GaussianBlur(radius))
    cv.paste(Image.blend(cv, Image.composite(blur, cv, blur.convert("L")), 0.55), (0, 0))


# --------------------------------------------------------------------------- #
# scene furniture (simple chalk props)
# --------------------------------------------------------------------------- #

def sun(d, cx, cy, r, col=GOLD):
    for i in range(5):
        circ(d, (cx, cy), r * (1 - i * 0.14), col, 3 + i, 1.0, 7 + i)
    for k in range(9):
        a = math.radians(-175 + k * 21)
        poly(d, [(cx + math.cos(a) * r * 1.35, cy + math.sin(a) * r * 1.35),
                 (cx + math.cos(a) * r * 2.6, cy + math.sin(a) * r * 2.6)], col, 5, 1.0, 11 + k)


def rain(d, seed=5, n=70):
    rng = np.random.default_rng(seed)
    for i in range(n):
        x, y = rng.integers(40, W - 40), rng.integers(60, H - 120)
        ln = int(rng.integers(24, 70))
        poly(d, [(x, y), (x - 7, y + ln)], (170, 190, 210), 2, 1.0, seed + i)


def window(d, x0=120, y0=180, x1=960, y1=1180, bars=2):
    box(d, x0, y0, x1, y1, CHALK, 8, 1.0, 21)
    for b in range(1, bars + 1):
        xb = x0 + (x1 - x0) * b / (bars + 1)
        poly(d, [(xb, y0), (xb, y1)], (150, 165, 180), 5, 1.0, 31 + b)


def table(d, cy=1240):
    box(d, 250, cy, 830, cy + 44, CHALK, 6, 1.0, 41)
    for x in (300, 780):
        poly(d, [(x, cy + 44), (x - 16, cy + 250)], CHALK, 6, 1.0, 42 + x % 7)
    circ(d, (420, cy - 30), 34, CHALK, 5, 1.0, 51)
    circ(d, (660, cy - 26), 26, GOLD, 5, 1.0, 52)


def mic(d, cx=540, cy=980):
    box(d, cx - 90, cy - 150, cx + 90, cy + 130, CHALK, 8, 1.0, 61)
    for k in range(4):
        y = cy - 110 + k * 62
        poly(d, [(cx - 74, y), (cx + 74, y)], (170, 185, 200), 4, 1.0, 62 + k)
    poly(d, [(cx, cy + 130), (cx, cy + 430)], CHALK, 10, 1.0, 66)
    arc(d, (cx, cy + 300), 120, 20, 160, CHALK, 7, 1.0, 67)
    poly(d, [(cx - 110, cy + 520), (cx + 110, cy + 520)], CHALK, 9, 1.0, 68)


def rays(d, cx=540, cy=760):
    for k in range(12):
        a = math.radians(-90 + k * 15 - 82)
        poly(d, [(cx + math.cos(a) * 330, cy + math.sin(a) * 330),
                 (cx + math.cos(a) * 760, cy + math.sin(a) * 760)], GOLD, 3, 1.0, 71 + k)


# --------------------------------------------------------------------------- #
# the 12 beats (same story as personality film, stickman style)
# --------------------------------------------------------------------------- #

def scene_01(cv, d):
    rain(d, 5, 90)
    poly(d, [(80, 1500), (1000, 1440)], CHALK, 5, 1.0, 81)
    circ(d, (300, 1330), 22, GOLD, 4, 1.0, 82)
    circ(d, (760, 1290), 16, GOLD, 4, 1.0, 83)
    hero(d, 540, 1760, 940, pose_walk(0.35), "worried", w=16, tq=0, p=1.0, hoodie=False)


def scene_02(cv, d):
    window(d)
    rain(d, 9, 120)
    hero(d, 700, 1720, 690, dict(lean=-3, head=-6, al=16, el=26, ar=-12, er=-30,
                                 ll=10, kl=2, lr=-10, kr=2), "sad", w=15, tq=0, hoodie=False)


def scene_03(cv, d):
    table(d)
    stick(d, 830, 1620, 470, dict(lean=2, head=3, al=-18, el=-30, ar=14, er=18,
                                  ll=8, kl=2, lr=-8, kr=2),
          col=(150, 158, 170), w=7, seed=EXTRAS[0], face="neutral")
    hero(d, 300, 1600, 660, dict(lean=6, head=6, al=34, el=64, ar=-10, er=-8,
                                 ll=8, kl=3, lr=-9, kr=3), "focus", w=14, tq=0, hoodie=False)


def scene_04(cv, d):
    # over-the-shoulder: bara sar, haath bolte hue
    hero(d, 480, 1760, 1080, dict(lean=3, head=5, al=40, el=52, ar=-6, er=-14,
                                  ll=6, kl=2, lr=-6, kr=2), "focus", w=18, tq=0, hoodie=False)


def scene_05(cv, d):
    # eyes close-up: hero ka sar frame bhar de
    hero(d, 540, 1520, 1180, dict(lean=0, head=0, al=15, el=9, ar=-15, er=-9,
                                  ll=4, kl=1, lr=-4, kr=1), "determined", w=20, tq=0, hoodie=False)
    star(d, 830, 560, 22, GOLD, 1.0, 0, 91)


def scene_06(cv, d):
    rays(d)
    hero(d, 540, 1660, 820, dict(lean=0, head=-2, al=26, el=6, ar=-26, er=-6,
                                 ll=9, kl=1, lr=-9, kr=1), "proud", w=16, tq=0, hoodie=False)


def scene_07(cv, d):
    box(d, 140, 1300, 940, 1350, CHALK, 6, 1.0, 101)
    for i, x in enumerate((260, 430, 650, 820)):
        stick(d, x, 1620, 380 + i * 12, pose_idle(0.6),
              col=(120, 128, 140), w=6, seed=EXTRAS[1] + i, face="neutral")
    hero(d, 540, 1720, 700, dict(lean=2, head=4, al=12, el=30, ar=-12, er=-30,
                                 ll=8, kl=2, lr=-8, kr=2), "focus", w=15, tq=0, hoodie=False)


def scene_08(cv, d):
    for i, (x, s, sd) in enumerate(((250, 430, EXTRAS[1]), (830, 450, EXTRAS[2]))):
        stick(d, x, 1600, s, pose_dance(0.8 + i * 0.2), col=(160, 168, 180), w=7,
              seed=sd, face="neutral")
    hero(d, 540, 1590, 720, pose_dance(0.65), "happy", w=15, tq=0, hoodie=False)


def scene_09(cv, d):
    # mirror practice — reflection dim + flipped
    poly(d, [(540, 300), (540, 1700)], (110, 118, 130), 4, 1.0, 111)
    hero(d, 340, 1620, 640, dict(lean=-4, head=-5, al=30, el=44, ar=-8, er=-10,
                                 ll=9, kl=2, lr=-9, kr=2), "determined", w=13, tq=0, hoodie=False)
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    hero(rd, 340, 1620, 640, dict(lean=-4, head=-5, al=30, el=44, ar=-8, er=-10,
                                  ll=9, kl=2, lr=-9, kr=2), "determined", w=13, tq=0, hoodie=False)
    refl = refl.transpose(Image.FLIP_LEFT_RIGHT)
    refl.putalpha(refl.split()[3].point(lambda v: int(v * 0.42)))
    cv.paste(refl, (W, 0), refl)


def scene_10(cv, d):
    sun(d, 540, 780, 210)
    poly(d, [(0, 1240), (W, 1240)], CHALK, 5, 1.0, 121)
    hero(d, 540, 1240, 720, dict(lean=3, head=8, al=34, el=18, ar=-34, er=-18,
                                 ll=12, kl=2, lr=-12, kr=2), "proud", w=15, tq=0, hoodie=False)


def scene_11(cv, d):
    for i, x in enumerate((150, 330, 750, 930)):
        stick(d, x, 1680, 420, pose_walk(0.2 + i * 0.17), col=(105, 112, 124), w=6,
              seed=EXTRAS[3] + i, face="neutral")
    poly(d, [(0, 1500), (W, 1400)], (140, 150, 165), 4, 1.0, 131)
    hero(d, 540, 1640, 780, pose_walk(0.55), "determined", w=16, tq=0, hoodie=False)


def scene_12(cv, d):
    mic(d)
    for k in range(5):
        circ(d, (240 + k * 150, 300), 3 + k, (200, 210, 225), 2, 1.0, 141 + k)
    tick(d, 900, 1700, 60, MINT, 1.0, 0, 147)


SCENES = {
    "k01": scene_01, "k02": scene_02, "k03": scene_03, "k04": scene_04,
    "k05": scene_05, "k06": scene_06, "k07": scene_07, "k08": scene_08,
    "k09": scene_09, "k10": scene_10, "k11": scene_11, "k12": scene_12,
}


def render(scene_id: str, out: pathlib.Path) -> pathlib.Path:
    cv = board().convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    SCENES[scene_id](cv, d)
    ground_shadow(cv, 540, 1790, 260, 26)
    cv.alpha_composite(layer)
    glow(cv, layer, 14)
    rgb = cv.convert("RGB")
    speckle(rgb, 700, seed=int(scene_id[1:]) * 7)
    img = finish(rgb)
    path = out / f"{scene_id}.png"
    img.save(path, "PNG")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="stick_keyframes")
    ap.add_argument("--out", default=str(ROOT / "studio/films/stick-i2v/keyframes"))
    ap.add_argument("--only", default="", help="k01,k02 ...")
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    wanted = [s for s in (args.only.split(",") if args.only else SCENES) if s]
    for sid in wanted:
        p = render(sid, out)
        print(f"{sid}: {p.name} {p.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
