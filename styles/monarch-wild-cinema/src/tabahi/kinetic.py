"""TABAHI KINETIC — typography as an animated object, not a caption.

The channel's own forensic audit is unambiguous: the videos that died used
AI narration over stills; the video that won used a strong on-screen idea.
Type here is therefore treated as a physical object: extruded, lit, tilted,
slammed and settled — and then it STOPS moving so it can be read.

Laws enforced in code:
  * a headline is readable for the majority of its life (entry is 0.34 s)
  * no endless distortion, no per-syllable bounce, no type over a face
  * one hot word per headline, measured for contrast
  * captions never sit in the platform UI band (bottom 320-420 px on Shorts,
    bottom 100 px on long-form 16:9)
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import core as C

ENTRY = 0.34          # seconds; the settled pose must dominate the shot
SAFE_BOTTOM_16x9 = 110


# ─────────────────────────────────────────────────────────────────────────────
# TEXT OBJECTS
# ─────────────────────────────────────────────────────────────────────────────

def _extruded(d: ImageDraw.ImageDraw, xy, s: str, f, tracking: float,
              face, side, depth: int = 13, angle: float = 40.0):
    """Draw extruded type: an offset stack in shadow colour, then the face."""
    x, y = xy
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    for i in range(depth, 0, -1):
        t = i / depth
        col = (int(side[0] * (1 - 0.35 * t)), int(side[1] * (1 - 0.35 * t)), int(side[2] * (1 - 0.35 * t)))
        C.draw_tracked(d, (x + dx * i * 1.6, y + dy * i * 1.6), s, f, col, tracking)
    C.draw_tracked(d, (x, y), s, f, face, tracking)


def _glow(img: Image.Image, xy, s: str, f, tracking: float, radius: float = 24,
          color=(0, 0, 0, 235)) -> Image.Image:
    g = Image.new("RGBA", img.size, (0, 0, 0, 0))
    C.draw_tracked(ImageDraw.Draw(g), xy, s, f, color, tracking)
    return g.filter(ImageFilter.GaussianBlur(radius))


def headline(text: str, size: int = 132, accent_word: str | None = None,
             align: str = "center", accent: str = "amber",
             max_width: int = None, face=C.BONE, y: int = None,
             pos: str = "lower", depth: int = 13, shadow: bool = True) -> Image.Image:
    """Build a headline layer (RGBA, full frame). One hot word, extruded."""
    layer = Image.new("RGBA", (C.W, C.H), (0, 0, 0, 0))
    d = C.rec_draw(layer)
    max_width = max_width or (C.W - 224)
    f = C.fit_font(d, "display", text, size, max_width, 3.0)
    tw = C.text_w(d, text, f, 3.0)
    if align == "center":
        x = (C.W - tw) / 2
    elif align == "left":
        x = 112.0
    else:
        x = C.W - 112.0 - tw
    if y is None:
        # PORTRAIT: "lower" means "the bottom of the SAFE band", not "300 px from
        # the canvas edge". In a 1920-tall Short the last 300 px are platform UI.
        lower = (C.SAFE[1] - f.size - 40) if C.PORTRAIT else (C.H - 300 - f.size)
        upper = (C.SAFE[0] + 20) if C.PORTRAIT else 150
        y = {"lower": lower, "center": (C.H - f.size) / 2,
             "upper": upper, "cinema": int(C.H * 0.62)}.get(pos, lower)

    accent_rgb = C.ACCENTS.get(accent, C.AMBER)
    if shadow:
        layer.alpha_composite(_glow(layer, (x, y), text, f, 3.0, 30, (0, 0, 0, 230)))

    if accent_word and accent_word.lower() in text.lower():
        idx = text.lower().find(accent_word.lower())
        pre, hot, post = text[:idx], text[idx:idx + len(accent_word)], text[idx + len(accent_word):]
        cx = x + (C.text_w(d, pre, f, 3.0) if pre else 0)
        _extruded(d, (x, y), pre, f, 3.0, face, (60, 62, 70), depth)
        _extruded(d, (cx, y), hot, f, 3.0, accent_rgb, (96, 64, 20), depth)
        if post:
            _extruded(d, (cx + C.text_w(d, hot, f, 3.0), y), post, f, 3.0, face, (60, 62, 70), depth)
    else:
        _extruded(d, (x, y), text, f, 3.0, face, (60, 62, 70), depth)

    # the rule under the headline — the brand's underline habit
    if pos in ("lower", "cinema"):
        d.rectangle([x, y + f.size + 30, x + min(tw, 168), y + f.size + 37], fill=accent_rgb)
    return layer


def stat_slam(value: str, unit: str = "", note: str = "", accent: str = "amber",
              pos: str = "center", big: int = 260) -> Image.Image:
    """The number beat. Type is the loudest thing on screen, then it holds."""
    layer = Image.new("RGBA", (C.W, C.H), (0, 0, 0, 0))
    d = C.rec_draw(layer)
    accent_rgb = C.ACCENTS.get(accent, C.AMBER)
    f = C.fit_font(d, "impact", value, big, C.W - 300, 6.0)
    tw = C.text_w(d, value, f, 6.0)
    x = (C.W - tw) / 2
    y = {"center": C.H / 2 - f.size * 0.62, "lower": C.H - 420, "upper": 180}.get(pos, C.H / 2 - f.size * 0.6)
    layer.alpha_composite(_glow(layer, (x, y), value, f, 6.0, 34, (0, 0, 0, 240)))
    _extruded(d, (x, y), value, f, 6.0, accent_rgb, (92, 58, 16), depth=16, angle=38)
    yy = y + f.size + 18
    if unit:
        fu = C.font("display", 52)
        uw = C.text_w(d, unit, fu, 6.0)
        C.draw_tracked(d, ((C.W - uw) / 2, yy), unit, fu, C.BONE, 6.0)
        yy += 74
    if note:
        fn = C.font("label", 40)
        nw = C.text_w(d, note, fn, 5.0)
        C.draw_tracked(d, ((C.W - nw) / 2, yy), note.upper(), fn, C.MIST, 5.0)
    return layer


def rule_card(number: int, text: str, accent: str = "amber", width: int = 1100) -> Image.Image:
    """A numbered rule. Used in the closing "three things" beat."""
    h = 150
    layer = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    d = C.rec_draw(layer)
    accent_rgb = C.ACCENTS.get(accent, C.AMBER)
    d.rounded_rectangle([0, 0, width, h], radius=14, fill=(8, 10, 14, 208))
    d.rectangle([0, 0, 10, h], fill=accent_rgb)
    fn = C.font("impact", 84)
    d.text((40, h / 2), str(number), font=fn, fill=accent_rgb, anchor="lm")
    ft = C.fit_font(d, "display", text.upper(), 54, width - 230, 3.0)
    C.draw_tracked(d, (150, h / 2 - ft.size * 0.62), text.upper(), ft, C.BONE, 3.0)
    return layer


def species_card(name: str, answer: str, accent: str = "amber", width: int = 1180) -> Image.Image:
    """Species identity -> the correct response. The episode's core payload."""
    h = 300
    layer = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    d = C.rec_draw(layer)
    accent_rgb = C.ACCENTS.get(accent, C.AMBER)
    d.rounded_rectangle([0, 0, width, h], radius=18, fill=(6, 8, 12, 214),
                        outline=accent_rgb + (150,), width=3)
    fn = C.fit_font(d, "display", name.upper(), 56, width - 80, 6.0)
    C.draw_tracked(d, (44, 34), name.upper(), fn, accent_rgb, 6.0)
    fa = C.fit_font(d, "display", answer.upper(), 92, width - 90, 2.5)
    C.draw_tracked(d, (44, 130), answer.upper(), fa, C.BONE, 2.5)
    d.line([(44, 112), (width - 44, 112)], fill=(255, 255, 255, 40), width=2)
    return layer


def lower_third(kicker: str, main: str, accent: str = "amber", width: int = 1080) -> Image.Image:
    h = 176
    layer = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    d = C.rec_draw(layer)
    accent_rgb = C.ACCENTS.get(accent, C.AMBER)
    d.rectangle([0, 0, 8, h], fill=accent_rgb)
    d.rounded_rectangle([8, 0, width, h], radius=8, fill=(8, 10, 14, 200))
    fk = C.font("label", 32)
    C.draw_tracked(d, (38, 26), kicker.upper(), fk, accent_rgb, 4.0)
    fm = C.fit_font(d, "display", main.upper(), 58, width - 76, 2.0)
    C.draw_tracked(d, (38, 76), main.upper(), fm, C.BONE, 2.0)
    return layer


def corner_mark(series: str = "MONARCH", sub: str = "FILES", ep: str = "") -> Image.Image:
    """Persistent brand mark. Same coordinates in every production (brand law)."""
    layer = Image.new("RGBA", (C.W, C.H), (0, 0, 0, 0))
    d = C.rec_draw(layer)
    f = C.font("display", 25)
    # safe band: G06 wants the ink inside the canvas's safe band, and the mark's
    # ascender starts above its anchor — 72 horizontally, just under the platform
    # UI in a Short (a portrait frame puts the handle over the top 13 %)
    # Portrait note (measured, not assumed): the type keeps its point size, so the
    # mark occupies ~25 % of a 1080-wide portrait frame against ~14 % of a
    # 1920-wide landscape one. Read back on the delivered vertical master this
    # reads as a deliberate brand tag rather than a bug, and it is the right size
    # for a frame consumed at arm's length — so it stays, as a decision: a mark
    # scaled to landscape proportion (≈14 px) is unreadable on a phone.
    x, y = 64, (C.SAFE[0] + 12) if C.PORTRAIT else 72
    # A soft dark HALO, not a scrim panel. MEASURED on a delivered frame: the mark
    # is bone/amber over a graded plate and, on a lit shot (03, a fog-lit grizzly),
    # it measured 3.70:1 against the surrounding sky — under the 4.5:1 gate. A
    # rectangular scrim fixes the number and leaves a hard black box on the plate
    # (T21); a blurred copy of the mark's own glyphs darkens exactly the pixels the
    # letters sit on, which is how broadcast marks are cut for bright footage.
    # A glyph-shaped SHADOW, not a scrim panel and not a smudge. Three measured
    # attempts are recorded in the failure register: (T21) a rectangular scrim
    # left a hard-cornered black box on the plate; a gaussian halo alone reached
    # only 3.85:1 on the vertical cut of shot 03, because a wide blur of a THIN
    # glyph stroke (25 px type, ~4 px stroke) has almost no coverage at the 2-5 px
    # ring the gate samples; a pad+blur round-rect "cloud" fixed the number and
    # put a visible dark oval on the fog. What works is what broadcast does:
    # dilate the glyph mask so the dark area FULLY covers the ring, then blur it
    # just enough to lose the hard edge, and stack a wide low-alpha pass under it
    # so there is no boundary at all.
    _halo = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    _hd = ImageDraw.Draw(_halo)
    C.draw_tracked(_hd, (x, y), series, f, (0, 0, 0, 255), 3.4)
    C.draw_tracked(_hd, (x + C.text_w(d, series, f, 3.4) + 15, y), sub, f, (0, 0, 0, 255), 3.4)
    if ep:
        _hd.text((x, y + 36), ep, font=C.font("label", 21), fill=(0, 0, 0, 255))

    import cv2 as _cv2
    _bb = _halo.getbbox()
    if _bb:
        import numpy as _np
        _pad = 72
        _box = (max(_bb[0] - _pad, 0), max(_bb[1] - _pad, 0),
                min(_bb[2] + _pad, layer.size[0]), min(_bb[3] + _pad, layer.size[1]))
        _a = _np.array(_halo.crop(_box))[..., 3]
        for _dia, _blur, _alpha in ((26, 16, 105), (14, 7, 180), (7, 2.5, 225)):
            _k = _cv2.getStructuringElement(_cv2.MORPH_ELLIPSE, (_dia * 2 + 1,) * 2)
            _m = _cv2.dilate(_a, _k)
            _im = Image.fromarray(_np.clip(_m.astype(_np.float32) * (_alpha / 255.0),
                                           0, 255).astype(_np.uint8))
            _im = _im.filter(ImageFilter.GaussianBlur(_blur))
            _lay = Image.new("RGBA", (_box[2] - _box[0], _box[3] - _box[1]), (0, 0, 0, 0))
            _lay.putalpha(_im)
            _dark = Image.new("RGBA", layer.size, (0, 0, 0, 0))
            _dark.paste(_lay, (_box[0], _box[1]))
            layer.alpha_composite(_dark)
    C.draw_tracked(d, (x, y), series, f, C.BONE, 3.4)
    xe = x + C.text_w(d, series, f, 3.4) + 15
    C.draw_tracked(d, (xe, y), sub, f, C.AMBER, 3.4)
    if ep:
        d.text((x, y + 36), ep, font=C.font("label", 21), fill=(255, 255, 255, 215))
    return layer


def chapter_tag(text: str, accent: str = "amber") -> Image.Image:
    """The only persistent chrome in long-form: a small act tag."""
    layer = Image.new("RGBA", (C.W, 74), (0, 0, 0, 0))
    d = C.rec_draw(layer)
    accent_rgb = C.ACCENTS.get(accent, C.AMBER)
    f = C.font("label", 30)
    tw = C.text_w(d, text.upper(), f, 5.0)
    d.rectangle([0, 0, tw + 44, 60], fill=(8, 10, 14, 180))
    d.rectangle([0, 0, 6, 60], fill=accent_rgb)
    C.draw_tracked(d, (24, 15), text.upper(), f, C.BONE, 5.0)
    return layer


def progress_spine(p: float, width: int = C.W, height: int = 5,
                   accent: str = "amber") -> Image.Image:
    """A thin measured spine. Callback device: it closes exactly at the payoff."""
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = C.rec_draw(layer)
    d.rectangle([0, 0, width, height], fill=(255, 255, 255, 40))
    d.rectangle([0, 0, int(width * C.clamp(p)), height], fill=C.ACCENTS.get(accent, C.AMBER) + (235,))
    return layer


# ─────────────────────────────────────────────────────────────────────────────
# ENTRANCE ANIMATION  (settle fast, then hold still so it can be read)
# ─────────────────────────────────────────────────────────────────────────────

def animate(layer: Image.Image, local_t: float, index: int = 0,
            mode: str = "extrude_tilt", entry: float = ENTRY,
            overshoot: float = 1.12, direction: int = 1) -> Image.Image:
    """Return the layer transformed for this instant. After `entry` it is flat."""
    import cv2

    delay = 0.04 * index if mode == "stagger" else 0.0
    u = C.clamp((local_t - delay) / max(entry, 1e-3))
    if mode == "stagger":
        mode = "extrude_tilt"
    if u >= 0.999 and mode in ("extrude_tilt", "pop"):
        return layer

    w, h = layer.size
    if mode == "pop":
        sc = 1.0 - 0.10 * (1 - C.e_back(u, overshoot))     # lands exactly at 1.0
        m = cv2.getRotationMatrix2D((w / 2, h / 2), 0, max(sc, 0.6))
        out = cv2.warpAffine(np.array(layer), m, (w, h), flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        arr = out
    elif mode == "rise":
        dy = int(64 * (1 - C.e_back(u, overshoot)))
        m = np.float32([[1, 0, 0], [0, 1, dy]])
        arr = cv2.warpAffine(np.array(layer), m, (w, h), flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    elif mode == "slide":
        dx = int(direction * 140 * (1 - C.e_back(u, overshoot)))
        m = np.float32([[1, 0, dx], [0, 1, 0]])
        arr = cv2.warpAffine(np.array(layer), m, (w, h), flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    elif mode == "wipe":
        arr = np.array(layer).copy()
        cut = int(w * C.e_io(u) * 1.06)
        arr[:, cut:] = 0
        arr = np.clip(arr.astype(np.float32), 0, 255).astype(np.uint8)
    else:  # extrude_tilt
        p = C.e_io(u)
        a = 1.0 - p
        src = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
        xp = w * 0.055 * a
        ys = h * 0.085 * a
        if direction > 0:
            dst = np.float32([[xp, ys], [w - 1 - xp, 0], [w - 1, h - 1], [0, h - 1 - ys]])
        else:
            dst = np.float32([[xp, 0], [w - 1 - xp, ys], [w - 1, h - 1 - ys], [0, h - 1]])
        m = cv2.getPerspectiveTransform(src, dst)
        arr = cv2.warpPerspective(np.array(layer), m, (w, h), flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        arr[..., 3] = (arr[..., 3].astype(np.float32) * (0.25 + 0.75 * p)).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def hold_fade(local_t: float, duration: float, fade_out: float = 0.28) -> float:
    """Opacity multiplier: never let type hard-cut off mid-read."""
    if local_t > duration - fade_out:
        return C.clamp((duration - local_t) / fade_out)
    return C.clamp(local_t / 0.12)


def contrast_report(layer: Image.Image, bg_luma: float = 0.06) -> dict:
    """Measure the hot words against the frame so 'readable' is a number."""
    arr = np.array(layer)
    a = arr[..., 3] > 40
    if a.sum() < 200:
        return {"pixels": int(a.sum()), "ok": False}
    px = arr[..., :3][a].astype(np.float32)
    f = px / 255.0
    l = 0.2126 * f[:, 0] + 0.7152 * f[:, 1] + 0.0722 * f[:, 2]
    def lin(c):
        return np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    L1 = float(lin(np.array(l)).mean())
    L2 = float(lin(np.array([bg_luma])).mean())
    hi, lo = max(L1, L2), min(L1, L2)
    return {"pixels": int(a.sum()), "mean_type_luma": float(l.mean()),
            "contrast_vs_bg": (hi + 0.05) / (lo + 0.05), "ok": (hi + 0.05) / (lo + 0.05) >= 4.5}
