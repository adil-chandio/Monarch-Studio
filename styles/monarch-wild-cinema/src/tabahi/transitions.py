"""TABAHI TRANSITIONS — four motivated families, never effect roulette.

Law inherited from the editor doctrine: one kind per boundary, never the same
kind twice in a row, every kind matched to a sound cue, and the hand-off must
be MOTIVATED (the concept escalates / the cause hands to the effect).

A transition here blends a FROZEN outgoing frame into live incoming frames.
That is deliberate: it is what a real edit does, it keeps the renderer
single-pass and streaming, and it avoids the long crossfade between two moving
scenes that reads as an amateur slideshow.
"""
from __future__ import annotations

import math

import cv2
import numpy as np

from . import core as C

KINDS = {
    "dip":       dict(seconds=0.22, cue="impact_soft"),
    "whip":      dict(seconds=0.24, cue="doppler_whip"),
    "depth":     dict(seconds=0.26, cue="riser_short"),
    "wipe":      dict(seconds=0.24, cue="whoosh_edge"),
    "hard":      dict(seconds=0.0,  cue="hard_hit"),
    "dissolve":  dict(seconds=0.60, cue="pad_swell"),
}


def _radial_blur(im: np.ndarray, strength: float) -> np.ndarray:
    if strength < 0.006:
        return im
    h, w = im.shape[:2]
    c = (w / 2.0, h / 2.0)
    acc = im.astype(np.float32) * 0.34
    for z, wgt in ((1 + strength, 0.33), (1 + strength * 2, 0.33)):
        m = cv2.getRotationMatrix2D(c, 0, z)
        acc += cv2.warpAffine(im, m, (w, h), borderMode=cv2.BORDER_REPLICATE).astype(np.float32) * wgt
    return np.clip(acc, 0, 255).astype(np.uint8)


def _render_dip(a, b, e) -> np.ndarray:
    """Fast dip — through a tinted dark, not a long black hold."""
    dark = np.full_like(a, 9)
    if e < 0.5:
        return C.mix(a, dark, C.smooth(e * 2) ** 0.85)
    return C.mix(dark, b, C.smooth((e - 0.5) * 2) ** 0.85)


def _render_whip(a, b, e, direction=1) -> np.ndarray:
    h, w = a.shape[:2]
    s = 1 if direction >= 0 else -1
    k = C.smooth(e)
    ma = np.float32([[1, 0, -s * w * 0.22 * k], [0, 1, h * 0.05 * k]])
    mb = np.float32([[1, 0, s * w * 0.20 * (1 - k)], [0, 1, -h * 0.05 * (1 - k)]])
    fa = cv2.warpAffine(a, ma, (w, h), borderMode=cv2.BORDER_REPLICATE)
    fb = cv2.warpAffine(b, mb, (w, h), borderMode=cv2.BORDER_REPLICATE)
    mix = C.mix(fa, fb, k)
    n = int(1 + 26 * math.sin(math.pi * k)) // 2 * 2 + 1
    return cv2.blur(mix, (n, 3))


def _render_depth(a, b, e, direction=1) -> np.ndarray:
    """Conceptual escalation: scale + roll + radial blur, both planes moving."""
    h, w = a.shape[:2]
    c = (w / 2.0, h / 2.0)
    k = C.smooth(e)
    s = _radial_blur(a, 0.020 * math.sin(math.pi * k))
    ma = cv2.getRotationMatrix2D(c, 1.8 * k, 1 + 0.16 * k)
    mb = cv2.getRotationMatrix2D(c, -1.1 * (1 - k), 1.14 - 0.14 * k)
    fa = cv2.warpAffine(s, ma, (w, h), borderMode=cv2.BORDER_REPLICATE)
    fb = cv2.warpAffine(b, mb, (w, h), borderMode=cv2.BORDER_REPLICATE)
    mix = C.mix(fa, fb, k ** 1.15)
    return _radial_blur(mix, 0.014 * math.sin(math.pi * k))


def _render_wipe(a, b, e, angle=0.17, softness=1.6) -> np.ndarray:
    """Measured diagonal wipe. No white flash (ledger M14: 49 luma jumps)."""
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    edge = xx / w + angle * (yy / h - 0.5)
    d = (e * (1.0 + 2 * abs(angle)) - edge) * (18.0 / softness) + 0.5
    m = np.clip(d, 0, 1)[..., None]
    return np.clip(a.astype(np.float32) * (1 - m) + b.astype(np.float32) * m, 0, 255).astype(np.uint8)


def apply(kind: str, outgoing: np.ndarray, incoming: np.ndarray, e: float,
          direction: int = 1, **kw) -> np.ndarray:
    """Blend one frame of a transition. e in [0,1]."""
    if kind in ("hard", None) or e >= 1.0:
        return incoming
    if kind == "dissolve":
        return C.mix(outgoing, incoming, C.smooth(e))
    if kind == "dip":
        return _render_dip(outgoing, incoming, e)
    if kind == "whip":
        return _render_whip(outgoing, incoming, e, direction)
    if kind == "depth":
        return _render_depth(outgoing, incoming, e, direction)
    if kind == "wipe":
        return _render_wipe(outgoing, incoming, e, kw.get("angle", 0.17) * (1 if direction >= 0 else -1))
    raise ValueError(f"unknown transition kind: {kind}")


def frames_for(kind: str) -> int:
    return int(round(KINDS.get(kind, KINDS["hard"])["seconds"] * C.FPS))


def plan(shot_count: int, seq: list[str] | None = None) -> list[str]:
    """Default grammar when an episode does not declare its own.

    Never the same kind twice in a row. `hard` is a legitimate cut and is used
    where the beat change is violent; the eye does not need an effect on every
    seam.
    """
    if seq:
        out = []
        prev = None
        for k in seq:
            if k == prev:
                k = "dip" if k != "dip" else "hard"
            out.append(k)
            prev = k
        return out
    cycle = ["hard", "dip", "whip", "hard", "depth", "wipe", "hard", "dip"]
    return [cycle[i % len(cycle)] for i in range(max(shot_count - 1, 0))]


def luma_profile(outgoing: np.ndarray, incoming: np.ndarray, kind: str) -> dict:
    """Gate helper: a whip/dip must not exceed the luma-jump ceiling."""
    vals = []
    for i in range(0, 11):
        e = i / 10.0
        f = apply(kind, outgoing, incoming, e)
        vals.append(float(C.luma(f).mean()))
    jumps = [abs(vals[i + 1] - vals[i]) for i in range(len(vals) - 1)]
    return {"start": vals[0], "mid": vals[5], "end": vals[-1],
            "max_step": max(jumps), "span": abs(vals[-1] - vals[0])}
