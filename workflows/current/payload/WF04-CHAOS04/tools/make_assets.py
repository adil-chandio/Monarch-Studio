"""Build the CHAOS 04 asset textures locally (Pillow), so the render box needs nothing.

Outputs, all committed next to the scene code:
  chaos04/assets/face_tex.png    — Monarch v5 face, feathered alpha, planar-projection map
  chaos04/assets/emblem.png      — our Monarch emblem, white on alpha
  chaos04/assets/wordmark.png    — our MONARCH STUDIO wordmark, white on alpha
  chaos04/assets/face_rect.json  — the measured crop, so the shader and the mesh agree

Run:  python3 tools/make_assets.py
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]           # WF04-CHAOS04
REPO = ROOT.parents[3]                               # Monarch-Studio checkout
SHEET = REPO / "characters/monarch/previews/CUSTOM_HERO_REAL_SHEET_v5_preview.jpg"
OUT = ROOT / "chaos04/assets"

# measured off a 50 px grid overlay of the v5 hero panel (see work log)
FACE_CROP = (168, 396, 432, 752)      # hairline->chin, cheek->cheek, measured on a 25 px grid
FACE_FEATHER = 0.10                   # fraction of the short side


def face_texture() -> dict:
    """Crop the locked v5 face and pad it with its own skin, so the projection can
    use EXTEND (no alpha, no shader blending, no black smear at the silhouette)."""
    sheet = Image.open(SHEET).convert("RGB")
    crop = sheet.crop(FACE_CROP)
    w, h = crop.size
    scale = 1024 / max(w, h)
    crop = crop.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    w, h = crop.size

    skin = Image.new("RGB", (5, 5))
    skin_px = skin.load()
    src = crop.load()
    # median-ish skin tone straight off the forehead and cheeks, not a guess
    samples = [src[w // 2, int(h * 0.10)], src[int(w * 0.30), int(h * 0.45)],
               src[int(w * 0.70), int(h * 0.45)], src[int(w * 0.50), int(h * 0.62)]]
    tone = tuple(sorted(s[i] for s in samples)[len(samples) // 2] for i in range(3))
    for yy in range(5):
        for xx in range(5):
            skin_px[xx, yy] = tone

    pad = 0.34
    pw, ph = round(w * (1 + 2 * pad)), round(h * (1 + 2 * pad))
    canvas = Image.new("RGB", (pw, ph), tone)
    # soft elliptical alpha so the photo melts into the padded skin
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    inset = round(w * 0.035)
    d.ellipse([inset, inset * 0.8, w - inset, h - inset * 0.4], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=w * 0.055))
    canvas.paste(crop, (round(w * pad), round(h * pad)), mask)

    canvas.save(OUT / "face_tex.png")
    meta = {
        "source": "characters/monarch/previews/CUSTOM_HERO_REAL_SHEET_v5_preview.jpg",
        "source_size": [1520, 1260],
        "crop": list(FACE_CROP),
        "skin_tone_rgb": list(tone),
        "out_size": list(canvas.size),
        "face_aspect": w / h,
        # inner face rect inside the padded canvas, normalised 0..1
        "inner_rect": [pad / (1 + 2 * pad), pad / (1 + 2 * pad),
                       1 - pad / (1 + 2 * pad), 1 - pad / (1 + 2 * pad)],
        "proj": "planar -Y; uv = inner_rect mapped from face rect; extension=EXTEND",
    }
    (OUT / "face_rect.json").write_text(json.dumps(meta, indent=1))
    return meta


def character_sheet_still(crop_box, out_name, size=(1080, 1920), blur=0.0):
    """A graded still from the locked body sheet, used as the frame inset in shot 17."""
    sheet = Image.open(SHEET).convert("RGB")
    still = sheet.crop(crop_box).resize(size, Image.LANCZOS)
    if blur:
        still = still.filter(ImageFilter.GaussianBlur(blur))
    still.save(OUT / out_name, quality=93)


def emblem(size=2048) -> None:
    """Monarch mark: a thin ring around an M whose top edge is a three-point crown."""
    s = size
    img = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(img)
    cx = cy = s / 2
    ring_r = s * 0.462
    d.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
              outline=255, width=round(s * 0.0135))

    # everything below is in units of the mark box (-0.5 .. 0.5)
    def p(x, y):
        return (cx + x * s, cy + y * s)

    # M silhouette with a crown fused into its top edge
    poly = [
        (-0.240, 0.158), (-0.240, -0.132),      # left leg, outer edge
        (-0.112, -0.042),                        # crown valley
        (0.000, -0.152),                         # crown peak
        (0.112, -0.042),                         # crown valley
        (0.240, -0.132),                         # right leg, outer edge
        (0.240, 0.158),                          # right leg, bottom
        (0.166, 0.158),                          # inner right
        (0.166, -0.004),
        (0.000, 0.092),                          # the M's centre point
        (-0.166, -0.004),
        (-0.166, 0.158),                         # inner left
    ]
    d.polygon([p(x, y) for x, y in poly], fill=255)
    # base bar, the way a studio mark is grounded
    d.rectangle([p(-0.268, 0.198)[0], p(-0.268, 0.198)[1],
                  p(0.268, 0.198)[0], p(0.268, 0.226)[1]], fill=255)

    img = img.filter(ImageFilter.GaussianBlur(radius=s * 0.0012))
    rgba = Image.new("RGB", (s, s), (255, 255, 255)).convert("RGBA")
    rgba.putalpha(img)
    rgba.save(OUT / "emblem.png")


def wordmark() -> None:
    anton = REPO / "styles/premium-motion-editing/assets/fonts/Anton-Regular.ttf"
    barlow = REPO / "styles/premium-motion-editing/assets/fonts/BarlowCondensed-Medium.ttf"
    w, h = 1600, 780
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype(str(anton), 290)
    small = ImageFont.truetype(str(barlow), 104)
    t1, t2 = "MONARCH", "STUDIO"
    track = 26
    widths = []
    for ch in t1:
        widths.append(d.textlength(ch, font=big))
    total = sum(widths) + track * (len(t1) - 1)
    x = (w - total) / 2
    for ch, cw in zip(t1, widths):
        d.text((x, 130), ch, font=big, fill=255)
        x += cw + track
    # spaced small type under the wordmark
    letters = [(c, d.textlength(c, font=small)) for c in t2]
    st = 40
    tw = sum(l[1] for l in letters) + st * (len(letters) - 1)
    sx = (w - tw) / 2
    for c, cw in letters:
        d.text((sx, 560), c, font=small, fill=235)
        sx += cw + st
    rgba = Image.new("RGB", (w, h), (255, 255, 255)).convert("RGBA")
    rgba.putalpha(img)
    rgba.save(OUT / "wordmark.png")


if __name__ == "__main__":
    print(json.dumps(face_texture(), indent=1))
    emblem()
    wordmark()
    for p in sorted(OUT.iterdir()):
        print(p.name, p.stat().st_size)
