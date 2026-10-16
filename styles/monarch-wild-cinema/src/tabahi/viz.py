"""TABAHI VIZ — real information graphics, animated and honest.

The forensic audit found the channel's failure mode: "a cited, species-specific
encounter explainer — what every clip compilation skips". Information density
is the differentiator, so charts are first-class citizens of the engine, not
decoration.

Honesty law: a chart may not imply a comparison the sources do not support.
`range_chart` draws bars ONLY where the underlying samples are comparable, and
`note` exists so a caption can say why a comparison was refused.
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFilter

from . import core as C


def _panel(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, C.rec_draw(img)


def _subline(d: ImageDraw.ImageDraw, xy, s: str, size=26, fill=C.MIST, tracking=2.4):
    f = C.font("label", size)
    C.draw_tracked(d, xy, s.upper(), f, fill, tracking)


def _title(d: ImageDraw.ImageDraw, xy, s: str, size=40, fill=C.BONE, tracking=3.0):
    f = C.fit_font(d, "display", s, size, C.W - 260, tracking)
    C.draw_tracked(d, xy, s.upper(), f, fill, tracking)


def bar_chart(rows: list[tuple[str, float, str]], title: str = "", unit: str = "",
              accent: str = "amber", reveal: float = 1.0, width: int = 1180) -> Image.Image:
    """Horizontal bars. rows = [(label, value_0_1, value_text)]."""
    n = len(rows)
    row_h = 96
    h = 150 + n * row_h + 90
    img, d = _panel(width, h)
    accent_rgb = C.ACCENTS.get(accent, C.AMBER)

    if title:
        _title(d, (0, 6), title, 38)
        d.line([(0, 66), (width * 0.32, 66)], fill=accent_rgb + (235,), width=3)

    y = 130
    for label, val, vtxt in rows:
        f = C.fit_font(d, "label", label.upper(), 38, width * 0.40, 1.6)
        C.draw_tracked(d, (0, y + 2), label.upper(), f, C.BONE, 1.6)
        bar_x = width * 0.42
        bar_w = width * 0.58
        # track
        d.rounded_rectangle([bar_x, y + 6, bar_x + bar_w, y + 46], radius=6, fill=(255, 255, 255, 26))
        w = max(4, int(bar_w * C.clamp(val) * C.ease_out(reveal)))
        fillc = accent_rgb if val >= 0.5 else (150, 168, 186)
        d.rounded_rectangle([bar_x, y + 6, bar_x + w, y + 46], radius=6, fill=fillc + (240,))
        d.text((bar_x + bar_w - 8, y - 26), vtxt, font=C.font("display", 34),
               fill=C.BONE, anchor="rs")
        y += row_h

    if unit:
        _subline(d, (0, h - 46), unit, 24, C.MIST, 2.2)
    return img


def range_chart(rows: list[dict], title: str = "", note: str = "",
                reveal: float = 1.0) -> Image.Image:
    """Range bars for a value with a LOW-HIGH span.

    rows = [{"label": str, "lo": 0_1, "hi": 0_1, "mark": 0_1|None, "txt": str}]
    Ranges are drawn as ranges. A point estimate is drawn as a tick. If the
    sources are not comparable, do not draw two rows — draw a note instead.
    """
    n = len(rows)
    row_h = 132
    width = 1180
    h = 190 + n * row_h + (86 if note else 40)
    img, d = _panel(width, h)

    if title:
        _title(d, (0, 6), title, 38)
        d.line([(0, 66), (width * 0.32, 66)], fill=C.AMBER + (235,), width=3)

    axis_x0, axis_x1 = int(width * 0.40), width
    y0 = 140
    # axis
    d.line([(axis_x0, 104), (axis_x1, 104)], fill=(255, 255, 255, 60), width=2)
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        x = axis_x0 + int((axis_x1 - axis_x0) * frac)
        d.line([(x, 96), (x, 112)], fill=(255, 255, 255, 70), width=2)
        d.text((x, 118), f"{int(frac*100)}%", font=C.font("label", 24), fill=C.MIST, anchor="ma")

    y = y0 + 30
    for row in rows:
        label = row["label"]
        f = C.fit_font(d, "label", label.upper(), 40, width * 0.36, 1.6)
        C.draw_tracked(d, (0, y + 4), label.upper(), f, C.BONE, 1.6)
        tw = row.get("txt")
        if tw:
            d.text((0, y + 50), tw, font=C.font("label", 28), fill=C.MIST)
        lo, hi = C.clamp(row["lo"] * reveal), C.clamp(row["hi"] * reveal)
        x_lo = axis_x0 + int((axis_x1 - axis_x0) * lo)
        x_hi = axis_x0 + int((axis_x1 - axis_x0) * hi)
        d.rounded_rectangle([x_lo, y + 8, max(x_hi, x_lo + 6), y + 56], radius=8,
                            fill=C.AMBER + (232,))
        if row.get("mark") is not None:
            mx = axis_x0 + int((axis_x1 - axis_x0) * C.clamp(row["mark"] * reveal))
            d.line([(mx, y - 4), (mx, y + 68)], fill=C.BONE + (245,), width=4)
        y += row_h

    if note:
        d.line([(0, y - 6), (width, y - 6)], fill=(255, 255, 255, 46), width=2)
        nf = C.font("label_i", 28)
        d.text((0, y + 12), note, font=nf, fill=C.MIST)
    return img


def gauge(value: float, label: str, sub: str = "", accent: str = "amber",
          size: int = 520) -> Image.Image:
    """Arc gauge for a single proportion. Value in 0..1."""
    img, d = _panel(size, size + 120)
    accent_rgb = C.ACCENTS.get(accent, C.AMBER)
    pad = 34
    box = [pad, pad, size - pad, size - pad]
    d.arc(box, start=135, end=405, fill=(255, 255, 255, 40), width=22)
    end = 135 + 270 * C.clamp(value)
    d.arc(box, start=135, end=end, fill=accent_rgb + (245,), width=22)
    f = C.font("impact", 170)
    d.text((size / 2, size / 2 - 4), f"{value*100:.0f}%", font=f, fill=C.BONE, anchor="mm")
    # MEASURED (read back from the delivered master): draw_tracked anchors at the
    # LEFT edge, so starting at size/2 pushed half the label past the card —
    # "BEAR SPRAY" rendered as "BEAR SPRA". Fit to the card, then centre.
    tr = 3.0
    lf = C.fit_font(d, "display", label.upper(), 46, size - 60, tr)
    lw = C.text_w(d, label.upper(), lf, tr)
    C.draw_tracked(d, ((size - lw) / 2, size + 6), label.upper(), lf, C.BONE, tr)
    if sub:
        sf = C.font("label", 30)
        d.text((size / 2, size + 74), sub, font=sf, fill=C.MIST, anchor="ma")
    return img


def callout(text: str, accent: str = "amber", width: int = 620) -> Image.Image:
    """A labelled bracket card, for pointing at a thing inside a plate."""
    img, d = _panel(width, 132)
    accent_rgb = C.ACCENTS.get(accent, C.AMBER)
    d.rectangle([0, 0, 7, 132], fill=accent_rgb + (250,))
    d.rounded_rectangle([7, 0, width, 132], radius=10, fill=(8, 10, 14, 214))
    f = C.fit_font(d, "display", text.upper(), 42, width - 60, 2.0)
    C.draw_tracked(d, (34, 30), text.upper(), f, C.BONE, 2.0)
    d.text((34, 84), "MEASURED", font=C.font("label", 24), fill=accent_rgb)
    return img


def source_stamp(cites, width: int = 1180) -> Image.Image:
    """The citation card. This is the channel's honesty made visible.

    MEASURED BUG: the plan passed a single citation as a STRING, so `len(cites)`
    was its character count (38) and the card rendered 38 one-character rows —
    a 2435 px tall panel running off the frame (G06: 06:source@y900-2435). A
    string is now one citation, and a citation is capped at two rows.
    """
    if isinstance(cites, str):
        cites = [cites]
    cites = [c for c in (cites or []) if str(c).strip()][:2]
    h = 74 + len(cites) * 38
    img, d = _panel(width, h)
    d.rectangle([0, 0, width, 3], fill=C.AMBER + (230,))
    d.text((0, 18), "SOURCES", font=C.font("display", 32), fill=C.AMBER)
    y = 58
    for c in cites:
        f = C.fit_font(d, "label", c, 30, width, 0.4, floor=20)
        d.text((0, y), c, font=f, fill=C.MIST)
        y += 40
    return img


def composite(base: Image.Image, layer: Image.Image, xy, opacity: float = 1.0,
              blur: float = 0.0) -> Image.Image:
    """Place an RGBA layer on a base with optional fade/blur (used for reveals)."""
    if opacity <= 0.002:
        return base
    lay = layer.copy()
    if blur > 0.1:
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
    if opacity < 0.999:
        a = lay.getchannel("A").point(lambda v: int(v * opacity))
        lay.putalpha(a)
    out = base.copy()
    out.alpha_composite(lay, (int(xy[0]), int(xy[1])))
    return out


def reveal_progress(local_t: float, duration: float, delay: float = 0.0) -> float:
    return C.clamp((local_t - delay) / max(duration, 1e-3))
