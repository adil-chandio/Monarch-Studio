#!/usr/bin/env python3
"""TABAHI THUMBS — the thumbnail system, with the legibility test that matters.

    python3 src/tabahi/thumbs.py --plan projects/<slug>/PLAN.json --out-dir build/thumbs

The channel's audit is blunt about thumbnails: the winning video's thumbnail
carried a short, violent statement; the losing uploads carried none. A
thumbnail is read at **213 x 120 px** in a subscription feed on a phone. That
is the size this tool tests at, not the 1280 x 720 it renders.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tabahi import core as C          # noqa: E402
from tabahi import depth as D         # noqa: E402
from tabahi import grade as G         # noqa: E402
from tabahi import kinetic as K       # noqa: E402

TW, TH = 1280, 720
FEED = (213, 120)


def base_frame(plate_path, look="nocturne", rect=(0.14, 0.10, 0.90, 0.98),
               cam=None, p=0.55) -> Image.Image:
    st = D.stage_from_file(plate_path, {"mode": "hybrid", "rect": rect})
    f = st.frame(p, cam or {"zoom": [0.05, 0.05], "orbit": 0})
    f = G.Grade(look).apply(f, 0)
    return Image.fromarray(C.resize(f, TW, TH)).convert("RGB")


def scrim(img: Image.Image, side: str = "left", strength: float = 0.80) -> Image.Image:
    """Directional scrim so type lives on a controlled ground, not on the plate."""
    w, h = img.size
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    if side == "left":
        for x in range(w):
            v = int(255 * strength * max(0.0, 1.0 - (x / (w * 0.62)) ** 1.35))
            d.line([(x, 0), (x, h)], fill=v)
    elif side == "bottom":
        for y in range(h):
            v = int(255 * strength * max(0.0, 1.0 - ((h - y) / (h * 0.60)) ** 1.35) ** 0.0
                    * min(1.0, ((y / h) - 0.42) / 0.58 + 1.0) if y / h > 0.42 else 0)
            d.line([(0, y), (w, y)], fill=v)
    else:
        m = Image.new("L", (w, h), int(255 * strength * 0.55))
    m = m.filter(ImageFilter.GaussianBlur(46))
    dark = Image.new("RGB", (w, h), (6, 8, 12))
    return Image.composite(dark, img, m)


def stamp(img: Image.Image, kicker: str, main: str, sub: str = "",
          accent: str = "amber", side: str = "left") -> Image.Image:
    """Place the concept text. Big condensed caps, one accent line."""
    out = img.convert("RGBA")
    d = ImageDraw.Draw(out)
    ar = C.ACCENTS.get(accent, C.AMBER)
    x0 = 62 if side == "left" else 62
    maxw = TW - 124

    fk = C.font("display", 30)
    C.draw_tracked(d, (x0 + 4, 92), kicker.upper(), fk, ar, 6.0)

    fm = C.fit_font(d, "display", main.upper(), 168, maxw, 2.0, floor=64)
    # two-line support: split at the widest break that fits
    lines = [main.upper()]
    if C.text_w(d, main.upper(), fm, 2.0) > maxw:
        words = main.upper().split()
        if len(words) > 1:
            best, bi = None, 1
            for i in range(1, len(words)):
                a, b = " ".join(words[:i]), " ".join(words[i:])
                w = max(C.text_w(d, a, fm, 2.0), C.text_w(d, b, fm, 2.0))
                if best is None or w < best:
                    best, bi = w, i
                    if w <= maxw:
                        break
            lines = [" ".join(words[:bi]), " ".join(words[bi:])]
        fm = C.fit_font(d, "display", max(lines, key=len), 168, maxw, 2.0, floor=52)

    y = 158
    for i, ln in enumerate(lines):
        col = ar if (i == len(lines) - 1 and len(lines) > 1) else C.BONE
        g = Image.new("RGBA", out.size, (0, 0, 0, 0))
        C.draw_tracked(ImageDraw.Draw(g), (x0, y), ln, fm, (0, 0, 0, 255), 2.0)
        out.alpha_composite(g.filter(ImageFilter.GaussianBlur(26)))
        C.draw_tracked(d, (x0, y), ln, fm, col, 2.0)
        y += int(fm.size * 1.02)

    if sub:
        fs = C.fit_font(d, "label", sub.upper(), 42, maxw, 3.0, floor=26)
        C.draw_tracked(d, (x0 + 4, y + 18), sub.upper(), fs, C.MIST, 3.0)
    # the brand underline habit
    d.rectangle([x0, y + 2, x0 + 132, y + 8], fill=ar)
    d.text((TW - 58, TH - 54), "MONARCH", font=C.font("display", 30), fill=(255, 255, 255, 205),
           anchor="rs")
    return out.convert("RGB")


def feed_test(img: Image.Image, thresh: int = 96) -> dict:
    """Downscale to feed size and measure whether the concept survives."""
    small = img.resize(FEED, Image.LANCZOS)
    a = np.asarray(small.convert("L"), dtype=np.float32)
    # local contrast: how much structure survives at 213x120
    gx = np.abs(np.diff(a, axis=1)).mean()
    gy = np.abs(np.diff(a, axis=0)).mean()
    hot = float((a > 200).mean() * 100.0)
    return {"local_contrast": float((gx + gy) / 2), "bright_pct": hot,
            "readable": bool((gx + gy) / 2 > 1.6 and 0.4 < hot < 34.0)}


def contact_sheet(thumbs: list[tuple[str, Image.Image]], path) -> pathlib.Path:
    cols = len(thumbs)
    sheet = Image.new("RGB", (cols * 440, 248 + 130), (10, 10, 12))
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(thumbs):
        sheet.paste(im.resize((420, 236), Image.LANCZOS), (i * 440 + 10, 10))
        sheet.paste(im.resize(FEED, Image.LANCZOS), (i * 440 + 10, 256))
        d.text((i * 440 + 118, 384), "213x120 FEED TEST", font=C.font("label", 22),
               fill=(150, 150, 160))
        d.text((i * 440 + 10, 404), name, font=C.font("display", 26), fill=(242, 237, 227))
    sheet.save(path, quality=93)
    return pathlib.Path(path)


CONCEPTS = [
    dict(key="A_threat", plate="01_hook_charge.jpg", look="nocturne",
         rect=(0.16, 0.10, 0.92, 0.98), side="left",
         kicker="BEAR COUNTRY", main="DON'T RUN.", sub="THE INSTINCT THAT GETS PEOPLE KILLED",
         accent="blood"),
    dict(key="B_testing", plate="12_grizzly.jpg", look="nocturne",
         rect=(0.14, 0.08, 0.94, 0.98), side="left",
         kicker="EVERY ENCOUNTER HAS A RULE", main="IT IS TESTING YOU", sub="FOUR BEARS. FOUR ANSWERS.",
         accent="amber"),
    dict(key="C_speed", plate="04_speed.jpg", look="alarm",
         rect=(0.08, 0.16, 0.96, 0.96), side="left",
         kicker="THE NUMBER THAT DECIDES IT", main="YOU CANNOT OUTRUN THIS", sub="27 MPH FOR SECONDS. 35 MPH SPRINT.",
         accent="amber"),
    dict(key="D_four", plate="13_polar_bear.jpg", look="first_light",
         rect=(0.16, 0.10, 0.90, 0.98), side="left",
         kicker="FOUR SPECIES, FOUR RULES", main="PLAY DEAD IS A LIE", sub="WHAT TO DO INSTEAD.",
         accent="signal"),
    dict(key="E_measured", plate="07_spray.jpg", look="first_light",
         rect=(0.18, 0.12, 0.88, 0.98), side="left",
         kicker="FIELD DATA, NOT OPINION", main="9 IN 10", sub="WHAT ACTUALLY STOPS A CHARGE.",
         accent="signal"),
]


def build(plate_dir, out_dir, concepts=None) -> dict:
    plate_dir, out_dir = pathlib.Path(plate_dir), pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    made, report = [], {}
    for c in (concepts or CONCEPTS):
        p = plate_dir / c["plate"]
        if not p.exists():
            continue
        img = base_frame(p, c["look"], c["rect"])
        img = scrim(img, c["side"])
        img = stamp(img, c["kicker"], c["main"], c.get("sub", ""), c["accent"], c["side"])
        f = out_dir / f"{c['key']}.jpg"
        img.save(f, quality=94, subsampling=0)
        t = feed_test(img)
        (out_dir / f"{c['key']}_feed_{FEED[0]}x{FEED[1]}.png").write_bytes(b"")
        img.resize(FEED, Image.LANCZOS).save(out_dir / f"{c['key']}_feed_{FEED[0]}x{FEED[1]}.png")
        report[c["key"]] = {**t, "file": str(f), "main": c["main"], "sub": c.get("sub", "")}
        made.append((c["key"], img))
    if made:
        contact_sheet(made, out_dir / "ALL_THUMBS.jpg")
    C.write_json(out_dir / "THUMB_METRICS.json", report)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plates", default=str(C.PLATES))
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    rep = build(args.plates, args.out_dir)
    for k, v in rep.items():
        C.say(f"  {k:<14} readable={str(v['readable']):<5} "
              f"local_contrast={v['local_contrast']:.2f}  bright={v['bright_pct']:.1f}%  {v['main']}")


if __name__ == "__main__":
    main()
