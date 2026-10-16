"""TABAHI CORE — shared primitives for the Monarch Wild Cinema engine.

Identity law of this file: every numeric constant here is either a MEASURED
value from a previous Monarch production or a labelled operating default.
Nothing in this module is a vibe.
"""
from __future__ import annotations

import functools
import json
import math
import pathlib
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────

SRC = pathlib.Path(__file__).resolve().parent
STYLE = SRC.parent.parent                      # styles/monarch-wild-cinema
ASSETS = STYLE / "assets"
FONTS = ASSETS / "fonts"
PLATES = ASSETS / "plates"

FFMPEG = None


def ffmpeg() -> str:
    """Locate ffmpeg through imageio-ffmpeg (no system ffmpeg on this box)."""
    global FFMPEG
    if FFMPEG is None:
        import imageio_ffmpeg
        FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    return FFMPEG


def ffprobe() -> str | None:
    cand = ffmpeg().replace("ffmpeg-linux", "ffprobe-linux").replace("/ffmpeg", "/ffprobe")
    return cand if pathlib.Path(cand).exists() else None


def run(cmd: list[str], label: str = "", quiet: bool = False) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print(f"  !! {label or 'command'} failed\n{p.stderr[-3000:]}", file=sys.stderr)
        raise SystemExit(1)
    if not quiet:
        print(f"  ok {label}")
    return p


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT CONSTANTS  (identity — never vary per video)
# ─────────────────────────────────────────────────────────────────────────────

W, H, FPS = 1920, 1080, 30
SR = 48000
VW, VH = 1080, 1920                      # vertical (Shorts) output

# Palette — the Monarch Wild Cinema identity.
INK = (10, 12, 16)
BONE = (242, 237, 227)                   # headline white; warmer than #fff
AMBER = (232, 163, 61)                   # identity accent / hot word
BLOOD = (196, 65, 43)                    # danger, mortality, warning
SIGNAL = (111, 168, 160)                 # safe / data / correct answer
MIST = (159, 176, 192)                   # secondary text, sources

ACCENTS = {"amber": AMBER, "blood": BLOOD, "signal": SIGNAL, "bone": BONE, "mist": MIST}


def hexrgb(s: str) -> tuple[int, int, int]:
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


# ─────────────────────────────────────────────────────────────────────────────
# EASING  (editor doctrine: no linear motion; triangle never sine for pans)
# ─────────────────────────────────────────────────────────────────────────────

def clamp(x, lo=0.0, hi=1.0):
    """Scalar or array clamp (numpy-aware)."""
    if isinstance(x, np.ndarray):
        return np.clip(x, lo, hi)
    return max(lo, min(hi, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x) if not isinstance(x, np.ndarray) else x * x * (3 - 2 * x)


def e_io(x):
    """Quintic in-out — the default for camera and transitions."""
    x = clamp(x)
    return x * x * x * (x * (x * 6 - 15) + 10)


def e_out(x, power=2.2):
    x = clamp(x)
    return 1 - (1 - x) ** power


def e_back(x, overshoot=1.12):
    """Prop arrival. Overshoot was cut 1.5 -> 1.12 after jerk measured 4.1."""
    x = clamp(x)
    c = overshoot
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def tri(x):
    """Triangle wave — constant speed, no zero-velocity apex (ledger #33)."""
    x = x % 1.0
    return 2 * x if x < 0.5 else 2 * (1 - x)


ease_out = e_out          # public alias used by the viz layer


def linear_dominant(u, io_weight=0.15):
    """Camera ramp: mostly linear so a typographic hold never reads frozen."""
    return io_weight * e_io(u) + (1 - io_weight) * u


# ─────────────────────────────────────────────────────────────────────────────
# TYPE SYSTEM  (Montserrat identity · Anton impact · Barlow Condensed labels)
# ─────────────────────────────────────────────────────────────────────────────

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

FONT_FILES = {
    "display": "Montserrat-VF.ttf",       # channel identity — headlines
    "impact": "Anton-Regular.ttf",        # huge numbers, thumbnails
    "label": "BarlowCondensed-Medium.ttf",
    "label_i": "BarlowCondensed-MediumItalic.ttf",
    "marker": "PermanentMarker.ttf",
}


def font(style: str, size: int) -> ImageFont.FreeTypeFont:
    key = (style, size)
    if key in _font_cache:
        return _font_cache[key]
    path = FONTS / FONT_FILES.get(style, FONT_FILES["display"])
    f = ImageFont.truetype(str(path), size)
    if style == "display":
        try:
            f.set_variation_by_axes([900])
        except Exception:
            pass
    _font_cache[key] = f
    return f


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT INSTRUMENTATION
# ─────────────────────────────────────────────────────────────────────────────

class RecDraw(ImageDraw.ImageDraw):
    """An ImageDraw that records every text call it makes.

    MEASURED NEED: a card that draws its label wider than the card is silently
    sliced by the canvas edge — and then reads as a typo in the finished film
    ("BEAR SPRAY" shipped as "BEAR SPRA" because `draw_tracked` anchors at the
    LEFT edge while the gauge passed the card's centre). Nothing in the plan
    was wrong, no exception was raised, and the render was "fine" — the only
    way to catch this class is to record where the text actually landed.
    Every recorded rect is exposed as `img.info["text_rects"]`, and gate G16
    fails the build when a rect leaves its own canvas.
    """

    def __init__(self, im, *a, **k):
        super().__init__(im, *a, **k)
        self.rects: list = []

    def note(self, x0, y0, x1, y1):
        self.rects.append((float(x0), float(y0), float(x1), float(y1)))
        try:
            self._image.info["text_rects"] = self.rects
        except Exception:
            pass

    def text(self, xy, text, *a, **k):
        font = k.get("font") or (a[0] if a else None)
        anchor = k.get("anchor") or None
        try:
            w = float(self.textlength(text, font=font))
            asc, desc = font.getmetrics() if hasattr(font, "getmetrics") else (0, 0)
        except Exception:
            w, asc, desc = 0.0, 0, 0
        x, y = float(xy[0]), float(xy[1])
        if anchor:
            if anchor[0] == "m":
                x -= w / 2.0
            elif anchor[0] == "r":
                x -= w
            if anchor[1] == "m":
                y -= (asc + desc) / 2.0
            elif anchor[1] in ("s", "b"):
                y -= float(asc + desc)
            elif anchor[1] == "a":
                y -= float(asc)
        self.note(x, y, x + w, y + asc + desc)
        return super().text(xy, text, *a, **k)


def rec_draw(im) -> "RecDraw":
    return RecDraw(im)


def text_w(d: ImageDraw.ImageDraw, s: str, f, tracking: float = 0.0) -> float:
    return float(sum(d.textlength(c, font=f) for c in s) + tracking * max(0, len(s) - 1))


def draw_tracked(d: ImageDraw.ImageDraw, xy, s: str, f, fill, tracking: float = 0.0):
    x, y = xy
    if hasattr(d, "note"):
        try:
            w = text_w(d, s, f, tracking)
            asc, desc = f.getmetrics() if hasattr(f, "getmetrics") else (0, 0)
            d.note(x, y, x + w, y + asc + desc)
        except Exception:
            pass
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + tracking
    return x


def fit_font(d: ImageDraw.ImageDraw, style: str, s: str, start: int, limit: float,
             tracking: float = 0.0, floor: int = 24) -> ImageFont.FreeTypeFont:
    """Refuse unreadable overflow instead of shrinking into dust (WF-05 law)."""
    size = start
    while size > floor:
        f = font(style, size)
        if text_w(d, s, f, tracking) <= limit:
            return f
        size -= 2
    return font(style, floor)


def rgba_layer(blur: float = 0.0, size=(W, H)) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def as_array(img: Image.Image, mode: str = "RGB") -> np.ndarray:
    return np.asarray(img.convert(mode), dtype=np.uint8)


# ─────────────────────────────────────────────────────────────────────────────
# COLOUR / IMAGE MATH
# ─────────────────────────────────────────────────────────────────────────────

def mix(a: np.ndarray, b: np.ndarray, t) -> np.ndarray:
    """t may be scalar or HxW (or HxWx1) float array."""
    if np.isscalar(t):
        return np.clip(a.astype(np.float32) * (1 - t) + b.astype(np.float32) * t, 0, 255).astype(np.uint8)
    t = np.asarray(t, dtype=np.float32)
    if t.ndim == 2:
        t = t[..., None]
    return np.clip(a.astype(np.float32) * (1 - t) + b.astype(np.float32) * t, 0, 255).astype(np.uint8)


def luma(a: np.ndarray) -> np.ndarray:
    f = a.astype(np.float32)
    return 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]


def resize(a: np.ndarray, w: int, h: int, interp=None) -> np.ndarray:
    import cv2
    if interp is None:
        interp = cv2.INTER_AREA if (w < a.shape[1]) else cv2.INTER_CUBIC
    return cv2.resize(a, (w, h), interpolation=interp)


def rel_luminance(rgb) -> float:
    def ch(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b) -> float:
    la, lb = rel_luminance(a), rel_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def paper_contrast(rgb) -> float:
    """Contrast of a type colour against the mean cinematic plate (INK-ish)."""
    return contrast_ratio(rgb, INK)


# ─────────────────────────────────────────────────────────────────────────────
# AUDIO IO
# ─────────────────────────────────────────────────────────────────────────────

def wav_write(path: pathlib.Path, data: np.ndarray, sr: int = SR):
    path = pathlib.Path(path)
    d = np.clip(data, -1.0, 1.0)
    pcm = (d * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(d.shape[1] if d.ndim > 1 else 1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def wav_read(path: pathlib.Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        n, _, ch = w.getnframes(), w.getsampwidth(), w.getnchannels()
        raw = w.readframes(n)
    a = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    return a.reshape(-1, ch) if ch > 1 else a.reshape(-1, 1)


# ─────────────────────────────────────────────────────────────────────────────
# JSON / LEDGER
# ─────────────────────────────────────────────────────────────────────────────

def read_json(path: pathlib.Path) -> dict:
    return json.loads(pathlib.Path(path).read_text())


def write_json(path: pathlib.Path, obj) -> pathlib.Path:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n")
    return path


def say(msg: str):
    print(msg, flush=True)
