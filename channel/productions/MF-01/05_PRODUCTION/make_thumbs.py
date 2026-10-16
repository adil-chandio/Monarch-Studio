#!/usr/bin/env python3
"""A06 PACKAGER — thumbnail candidates + the mandatory 120px legibility test."""
from __future__ import annotations
import pathlib
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

ROOT = pathlib.Path(__file__).resolve().parent
PLATES = ROOT / "plates"
OUT = ROOT / "thumbs"
OUT.mkdir(exist_ok=True)
FONTS = pathlib.Path("/home/user/Monarch-Studio/styles/monarch-stickman-animation/fonts")
W, H = 1280, 720
AMBER = (232, 163, 61)
WHITE = (255, 255, 255)


def font(size: int, weight: int = 900) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTS / "Montserrat-VF.ttf"), size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def tracked(d, xy, s, f, fill, tr=0):
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + tr
    return x


def tw(d, s, f, tr=0):
    return int(sum(d.textlength(c, font=f) for c in s) + tr * max(0, len(s) - 1))


def base(plate: str, zoom: float = 1.0, focus=(0.5, 0.42)) -> Image.Image:
    im = Image.open(PLATES / f"{plate}.jpg").convert("RGB")
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Color(im).enhance(1.06)
    iw, ih = im.size
    # crop to 16:9 around focus, then scale
    tr = W / H
    if iw / ih > tr:
        nw = int(ih * tr); x = int((iw - nw) * focus[0]); im = im.crop((x, 0, x + nw, ih))
    else:
        nh = int(iw / tr); y = int((ih - nh) * focus[1]); im = im.crop((0, y, iw, y + nh))
    sc = int(W * zoom)
    im = im.resize((sc, int(sc / tr)), Image.LANCZOS)
    x = (im.size[0] - W) // 2; y = (im.size[1] - H) // 2
    im = im.crop((x, y, x + W, y + H))

    # cinematic grade + bottom scrim for text
    im = ImageEnhance.Brightness(im).enhance(0.96)
    scrim = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(scrim)
    for i in range(320):
        sd.line([(0, H - 320 + i), (W, H - 320 + i)], fill=int(215 * (i / 320) ** 1.5))
    im = Image.composite(Image.new("RGB", (W, H), (4, 6, 10)), im, scrim)
    return im


def brand(d, im):
    f = font(21)
    x, y = 44, 38
    tracked(d, (x, y), "MONARCH", f, WHITE, 3)
    tracked(d, (x + tw(d, "MONARCH", f, 3) + 12, y), "FILES", f, AMBER, 3)
    # amber rule under the mark
    d.rectangle([x, y + 32, x + 74, y + 35], fill=AMBER)


def thumb_a() -> Image.Image:
    """The instinct. Close bear + the single instruction."""
    im = base("01_hook_charge", zoom=1.16, focus=(0.5, 0.30))
    d = ImageDraw.Draw(im)
    f1, f2 = font(152), font(40)
    t1 = "DON'T RUN"
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tracked(ImageDraw.Draw(glow), (58, H - 232), t1, f1, (0, 0, 0, 255), 2)
    im.paste(Image.alpha_composite(im.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(22))).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(im)
    tracked(d, (58, H - 232), t1, f1, WHITE, 2)
    tracked(d, (62, H - 62), "THE INSTINCT THAT GETS PEOPLE KILLED.", f2, AMBER, 2)
    brand(d, im)
    return im


def thumb_b() -> Image.Image:
    """The eyes. Predator reading you."""
    im = base("05_watching", zoom=1.05, focus=(0.5, 0.42))
    d = ImageDraw.Draw(im)
    f1, f2 = font(118), font(36)
    t1 = "IT IS TESTING YOU"
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tracked(ImageDraw.Draw(glow), (58, H - 214), t1, f1, (0, 0, 0, 255), 2)
    im.paste(Image.alpha_composite(im.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(22))).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(im)
    tracked(d, (58, H - 214), t1, f1, WHITE, 2)
    d.rectangle([58, H - 78, 240, H - 73], fill=AMBER)
    tracked(d, (258, H - 96), "FOUR BEARS. FOUR ANSWERS.", f2, WHITE, 2)
    brand(d, im)
    return im


def thumb_c() -> Image.Image:
    """Speed + the contradiction."""
    im = base("04_speed", zoom=1.10, focus=(0.5, 0.45))
    d = ImageDraw.Draw(im)
    f1, f2 = font(96), font(44)
    t1, t2 = "YOU CANNOT", "OUTRUN THIS"
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    tracked(gd, (58, H - 290), t1, f1, (0, 0, 0, 255), 2)
    tracked(gd, (58, H - 176), t2, f1, (0, 0, 0, 255), 2)
    im.paste(Image.alpha_composite(im.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(22))).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(im)
    tracked(d, (58, H - 290), t1, f1, WHITE, 2)
    tracked(d, (58, H - 176), t2, f1, AMBER, 2)
    tracked(d, (62, H - 56), "27 MPH FOR SECONDS. 35 MPH SPRINT.", f2, WHITE, 1)
    brand(d, im)
    return im


def legibility(path: pathlib.Path) -> int:
    """Shrink to a 120px-tall thumbnail — the size YouTube actually serves in a grid."""
    im = Image.open(path)
    h = 120
    w = int(im.width * h / im.height)
    small = im.resize((w, h), Image.LANCZOS)
    out = path.with_name(path.stem + "_120px.png")
    small.save(out)
    return w


def main():
    for name, fn in [("A_dont_run", thumb_a), ("B_testing_you", thumb_b), ("C_cannot_outrun", thumb_c)]:
        p = OUT / f"{name}.jpg"
        fn().save(p, quality=94, subsampling=0)
        w = legibility(p)
        print(f"  ✓ {p.name:22s} 1280x720  →  120px test: {w}x120")
    # side by side sheet
    ims = [Image.open(OUT / f"{n}.jpg") for n in ("A_dont_run", "B_testing_you", "C_cannot_outrun")]
    sheet = Image.new("RGB", (W, H * 3 + 40), (8, 10, 14))
    for i, im in enumerate(ims):
        sheet.paste(im, (0, i * (H + 20)))
    sheet.save(OUT / "ALL_THUMBS.jpg", quality=92)
    print(f"\n  contact: {OUT/'ALL_THUMBS.jpg'}")


if __name__ == "__main__":
    main()
