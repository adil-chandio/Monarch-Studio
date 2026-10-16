"""TABAHI GRADE — the cinematic look, as measured math.

Pipeline order is fixed: TONE -> SPLIT-TONE -> TEXTURE -> VIGNETTE -> GRAIN.
Every stage is LUT- or mask-based so a 1920x1080 frame grades in well under
100 ms; a full 3-minute episode must still render overnight on 2 cores.

The grade is deliberately NOT a "filter". It reproduces the shared visual
signature across the channel: deep teal shadows, warm bone highlights, soft
roll-off, restrained saturation and grain that survives YouTube compression.
"""
from __future__ import annotations

import cv2
import numpy as np

from . import core as C

# ─────────────────────────────────────────────────────────────────────────────
# LOOK PRESETS  (identity per series; one look per episode, never mixed)
# ─────────────────────────────────────────────────────────────────────────────

LOOKS = {
    # Night-forest, cold, dangerous. MF-01 shipped this grade.
    "nocturne": dict(contrast=1.13, lift=0.014, gamma=0.97, sat=0.93,
                     shadow_tint=(-0.030, 0.004, 0.052), hi_tint=(0.040, 0.012, -0.036),
                     vignette=0.52, grain=5.0, bloom=0.30, fade=0.06),
    # First light, documentary, hopeful. For conservation / family episodes.
    "first_light": dict(contrast=1.06, lift=0.030, gamma=1.02, sat=1.02,
                        shadow_tint=(-0.014, 0.002, 0.030), hi_tint=(0.052, 0.026, -0.028),
                        vignette=0.34, grain=4.0, bloom=0.46, fade=0.10),
    # Archive / evidence: flat, truthful, no romance. Compliance segments.
    "archive": dict(contrast=1.02, lift=0.018, gamma=1.00, sat=0.86,
                    shadow_tint=(-0.008, 0.000, 0.014), hi_tint=(0.016, 0.008, -0.012),
                    vignette=0.22, grain=6.0, bloom=0.14, fade=0.04),
    # Alarm: the one look reserved for a threat / mortality beat.
    "alarm": dict(contrast=1.20, lift=0.006, gamma=0.94, sat=0.88,
                  shadow_tint=(-0.052, -0.008, 0.030), hi_tint=(0.070, 0.004, -0.060),
                  vignette=0.66, grain=5.5, bloom=0.34, fade=0.06),
}


# ─────────────────────────────────────────────────────────────────────────────
# TONE LUT  (filmic shoulder, no clipping into the delivery ceiling)
# ─────────────────────────────────────────────────────────────────────────────

def _hable(x, a=0.22, b=0.30, c=0.10, d=0.20, e=0.01, f=0.30):
    return ((x * (a * x + c * b) + d * e) / (x * (a * x + b) + d * f)) - e / f


def tone_lut(contrast=1.10, lift=0.014, gamma=0.97, strength=0.55, ceiling=0.985) -> np.ndarray:
    x = np.linspace(0.0, 1.0, 256, dtype=np.float32)
    w = _hable(np.clip(x, 0, 1))
    white = _hable(1.0)
    filmic = np.clip(w / white, 0, 1)
    y = (1 - strength) * x + strength * filmic
    y = np.clip((y - 0.5) * contrast + 0.5 + lift, 0, 1) ** gamma
    y = y * ceiling
    return (np.clip(y, 0, 1) * 255.0).astype(np.uint8)


def _luma_mask(img: np.ndarray) -> np.ndarray:
    """Cheap luma at 1/4 scale, returned at full res for tint weighting."""
    small = cv2.resize(img, (C.W // 4, C.H // 4), interpolation=cv2.INTER_AREA)
    f = small.astype(np.float32) / 255.0
    l = 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]
    return cv2.resize(l, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)


def split_tone(img: np.ndarray, look: dict) -> np.ndarray:
    """Tint shadows and highlights along different hue vectors.

    Implemented on a quarter-resolution luma mask and re-expanded, so the
    operation costs ~15 ms instead of ~90 ms and the result is visually
    identical (the mask is smooth by construction).
    """
    l = _luma_mask(img)
    sh = (1.0 - l) ** 2.0
    hi = l ** 1.6
    st = np.array(look["shadow_tint"], np.float32) * 255.0
    ht = np.array(look["hi_tint"], np.float32) * 255.0
    add = sh[..., None] * st + hi[..., None] * ht
    return np.clip(img.astype(np.float32) + add, 0, 255).astype(np.uint8)


def saturation(img: np.ndarray, amount: float, vibrance: float = 0.0) -> np.ndarray:
    """Saturation as a luma blend through OpenCV's SIMD paths.

    The naive float implementation (per-channel max/min + per-pixel vibrance)
    measured 278 ms/frame — the single most expensive stage in the pipeline.
    A Rec.601 luma blend via cvtColor + addWeighted measures ~20 ms and is
    visually indistinguishable at these saturation deltas.
    """
    if abs(amount - 1.0) < 0.005:
        return img
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray3 = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    return cv2.addWeighted(img, amount, gray3, 1.0 - amount, 0.0)


def bloom(img: np.ndarray, amount: float) -> np.ndarray:
    """Highlight bloom, computed at 1/8 scale and added back through cv2.

    Screen blending in float32 cost 91 ms/frame. A downscaled glow added with
    `cv2.addWeighted` costs ~22 ms; on a dark cinematic plate the two are
    indistinguishable, and the halo risk is lower because the glow is softer.
    """
    if amount <= 0.01:
        return img
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    thr = cv2.threshold(gray, 165, 255, cv2.THRESH_TOZERO)[1]
    hot = cv2.cvtColor(cv2.multiply(gray, thr, scale=1.0 / 255.0).astype(np.uint8),
                       cv2.COLOR_GRAY2RGB)
    small = cv2.resize(hot, (max(w // 8, 8), max(h // 8, 8)), interpolation=cv2.INTER_AREA)
    glow = cv2.GaussianBlur(small, (0, 0), 3.2)
    glow = cv2.resize(glow, (w, h), interpolation=cv2.INTER_LINEAR)
    return cv2.addWeighted(img, 1.0, glow, amount, 0.0)


_GRAIN_CACHE: dict[tuple[int, int], np.ndarray] = {}


def grain_tile(seed: int = 17) -> np.ndarray:
    key = (C.W, C.H)
    if key not in _GRAIN_CACHE:
        rng = np.random.default_rng(seed)
        # oversized so a moving crop can never run off the tile
        n = rng.standard_normal((C.H + C.H // 2, C.W + C.W // 2)).astype(np.float32)
        _GRAIN_CACHE[key] = cv2.GaussianBlur(n, (0, 0), 0.55)
    return _GRAIN_CACHE[key]


def add_grain(img: np.ndarray, amount: float, frame_index: int) -> np.ndarray:
    """Grain that MOVES: a cropped offset of one cached tile per frame.

    A static grain tile reads as a dirty lens; offsetting the crop per frame
    reads as film. Because the tile is cached, per-frame cost is one add.
    """
    if amount <= 0.05:
        return img
    tile = grain_tile()
    oy = (frame_index * 37) % (C.H // 2)
    ox = (frame_index * 61) % (C.W // 2)
    g = tile[oy:oy + C.H, ox:ox + C.W]
    return np.clip(img.astype(np.float32) + g[..., None] * amount, 0, 255).astype(np.uint8)


_VIG_CACHE: dict[tuple[int, int, float], np.ndarray] = {}


def vignette_mask(h: int, w: int, strength: float) -> np.ndarray:
    """Cache the mask. Rebuilding a 2 MP mgrid per frame cost 73 ms."""
    key = (h, w, round(strength, 3))
    if key not in _VIG_CACHE:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        dx = (xx / w - 0.5) / 0.5
        dy = (yy / h - 0.5) / 0.5
        r = np.sqrt(dx * dx * 0.94 + dy * dy * 1.02)
        v = np.clip(1.0 - strength * np.clip(r - 0.42, 0, None) ** 1.55, 0.0, 1.0)
        m = np.repeat((v * 255.0).astype(np.uint8)[..., None], 3, axis=2)
        _VIG_CACHE.clear()
        _VIG_CACHE[key] = m
    return _VIG_CACHE[key]


def vignette(img: np.ndarray, strength: float) -> np.ndarray:
    if strength <= 0.01:
        return img
    m = vignette_mask(img.shape[0], img.shape[1], strength)
    return cv2.multiply(img, m, scale=1.0 / 255.0)


class Grade:
    """A prepared look: 3-channel LUT + parameters, applied in a fixed order."""

    def __init__(self, name: str = "nocturne", **overrides):
        look = dict(LOOKS.get(name, LOOKS["nocturne"]))
        look.update(overrides)
        self.name = name
        self.look = look
        # 1-D LUT: indexing a (H,W,3) uint8 image with a (256,) table maps
        # every channel through the same tone curve and returns (H,W,3).
        self.lut = tone_lut(contrast=look["contrast"], lift=look["lift"], gamma=look["gamma"])
        self.sat_amount = look["sat"]
        self.vig = look["vignette"]
        self.grain_amount = look["grain"]
        self.bloom_amount = look["bloom"]
        self.fade = look.get("fade", 0.0)

    def apply(self, img: np.ndarray, frame_index: int = 0,
              skip_texture: bool = False) -> np.ndarray:
        out = self.lut[img]                                     # tone (vectorised)
        if self.fade > 0:
            out = C.mix(out, np.full_like(out, int(self.look.get("fade_rgb", 12)), np.uint8), self.fade * 0.5)
        out = split_tone(out, self.look)
        out = saturation(out, self.sat_amount)
        if not skip_texture:
            out = bloom(out, self.bloom_amount)
        out = vignette(out, self.vig)
        if not skip_texture:
            out = add_grain(out, self.grain_amount, frame_index)
        return out


def measure(img: np.ndarray) -> dict:
    f = img.astype(np.float32) / 255.0
    l = 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]
    hs = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)[..., 1].astype(np.float32) / 255.0
    return {
        "mean_luma": float(l.mean()), "p05_luma": float(np.percentile(l, 5)),
        "p95_luma": float(np.percentile(l, 95)), "contrast": float(l.std()),
        "clipped_hi_pct": float((l > 0.995).mean() * 100),
        "crushed_lo_pct": float((l < 0.02).mean() * 100),
        "mean_sat": float(hs.mean()),
    }
