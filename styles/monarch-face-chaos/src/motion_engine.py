#!/usr/bin/env python3
"""Real-motion engine for WF-04 · MONARCH FACE · CHAOS VIDEO · MOTION EDITION.

The user's brief (Urdu/Roman Urdu, 2026-10-15): *"images me real movement lao na
ki yeh jelly type effects add karke do"* — i.e. put **real motion** in the
keyframe images instead of wobbling them with jelly-style warps.

This module therefore does two things and nothing else:

1. **Dense-flow action hops** — two authored action keyframes (start pose ->
   end pose) are turned into a short, hand-timed hop where the *body itself*
   moves: optical flow is estimated both ways, forward/backward consistency
   carves out occlusion zones, and each output pixel is taken from the nearest
   source frame instead of being averaged.  That removes the translucent
   "jelly" look: limbs travel, they never become rubber.

2. **Living-shot micro motion** — rigid camera moves (translate / zoom /
   rotate / handheld shake) plus small, local, physically-plausible alives:
   chest breathing, weight shift, head drift, blinks, cable/cloth sway and
   floor ripples.  Every one of them is a *local* deformation with a feathered
   boundary, so nothing turns into a global wobble.

Keyframes live outside the workspace snapshot (identity media, rule 13) in
``MONARCH_KEYFRAME_DIR`` (default ``/tmp/monarch-stage/keys``); see
``records/KEYFRAME_SOURCE.json`` for the Drive IDs so they can be re-staged.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Iterable, Sequence

import cv2
import numpy as np

CANON_W, CANON_H = 1080, 1920
VIGNETTE_KEYS = ("s1_walk_f1", "s1_walk_f2", "s2_point_f1", "s2_point_f2",
                 "s3_throne_f1", "s3_throne_f2", "s4_guard_f1",
                 "s6_turn_f0", "s6_turn_f1", "s7_burst_f1")


def _repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "styles").is_dir() and (candidate / "workflows").is_dir():
            return candidate
    raise RuntimeError("repository root not found above " + str(Path(__file__).resolve()))


ROOT = _repo_root()
STYLE = ROOT / "styles" / "monarch-face-chaos"
PLATES = STYLE / "plates"


def keyframe_dir() -> Path:
    return Path(os.environ.get("MONARCH_KEYFRAME_DIR", "/tmp/monarch-stage/keys"))


# --------------------------------------------------------------------------- #
# image plumbing
# --------------------------------------------------------------------------- #
_BASE_GRID: tuple[np.ndarray, np.ndarray] | None = None


def base_grid() -> tuple[np.ndarray, np.ndarray]:
    """Identity remap grid for the canonical raster (built once)."""
    global _BASE_GRID
    if _BASE_GRID is None:
        xs = np.arange(CANON_W, dtype=np.float32)[None, :].repeat(CANON_H, axis=0)
        ys = np.arange(CANON_H, dtype=np.float32)[:, None].repeat(CANON_W, axis=1)
        _BASE_GRID = (xs, ys)
    return _BASE_GRID


def cover_fit(img: np.ndarray, w: int = CANON_W, h: int = CANON_H) -> np.ndarray:
    """Scale + center-crop to the canonical raster without distorting faces."""
    ih, iw = img.shape[:2]
    scale = max(w / iw, h / ih)
    nw, nh = int(round(iw * scale)), int(round(ih * scale))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
    x0, y0 = (nw - w) // 2, (nh - h) // 2
    out = resized[y0:y0 + h, x0:x0 + w]
    # a light unsharp keeps the 1.4x upscale crisp instead of mushy
    blur = cv2.GaussianBlur(out, (0, 0), 1.1)
    return cv2.addWeighted(out, 1.28, blur, -0.28, 0.0)


def remap(img: np.ndarray, dx: np.ndarray, dy: np.ndarray) -> np.ndarray:
    xs, ys = base_grid()
    return cv2.remap(img, xs + dx, ys + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


# --------------------------------------------------------------------------- #
# dense optical flow + occlusion-aware action hops
# --------------------------------------------------------------------------- #
_FLOW_CACHE: dict[tuple[str, str], tuple[np.ndarray, np.ndarray, np.ndarray]] = {}


def _dis() -> "cv2.DISOpticalFlow":
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    dis.setUseSpatialPropagation(True)
    return dis


def pair_flows(a_gray: np.ndarray, b_gray: np.ndarray, tag: tuple[str, str] | None = None):
    """Forward (a->b) and backward (b->a) flow at full resolution + occlusion mask.

    Flow is estimated at half resolution (fast, and half res already captures the
    body-scale motion of a hop) and upsampled with a bicubic resize of the field.
    ``ok`` is 1.0 where the two fields agree (visible in both frames) and 0.0 in
    occlusion zones, feather-smoothed so the composite seam is invisible.
    """
    if tag is not None and tag in _FLOW_CACHE:
        return _FLOW_CACHE[tag]

    small = (CANON_W // 2, CANON_H // 2)
    ga = cv2.resize(a_gray, small, interpolation=cv2.INTER_AREA)
    gb = cv2.resize(b_gray, small, interpolation=cv2.INTER_AREA)
    dis = _dis()
    f_small = dis.calc(ga, gb, None)
    b_small = dis.calc(gb, ga, None)

    fwd = cv2.resize(f_small * 2.0, (CANON_W, CANON_H), interpolation=cv2.INTER_CUBIC)
    bwd = cv2.resize(b_small * 2.0, (CANON_W, CANON_H), interpolation=cv2.INTER_CUBIC)

    xs, ys = base_grid()
    # forward-backward consistency: sample the backward field at the forward target
    bx = np.clip(xs + fwd[..., 0], 0, CANON_W - 1)
    by = np.clip(ys + fwd[..., 1], 0, CANON_H - 1)
    bwd_at = cv2.remap(bwd, bx, by, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    fb_err = np.sqrt((fwd[..., 0] + bwd_at[..., 0]) ** 2 + (fwd[..., 1] + bwd_at[..., 1]) ** 2)
    thr = max(1.6, 0.035 * float(np.percentile(fb_err, 90)))
    ok = np.clip(1.0 - fb_err / (thr * 1.8), 0.0, 1.0)
    ok = cv2.GaussianBlur(ok.astype(np.float32), (0, 0), 12.0)[..., None]

    if tag is not None:
        _FLOW_CACHE[tag] = (fwd, bwd, ok)
    return fwd, bwd, ok


def eased(t: float, kind: str = "inout") -> float:
    t = min(1.0, max(0.0, t))
    if kind == "linear":
        return t
    if kind == "out":
        return 1.0 - (1.0 - t) ** 3
    if kind == "in":
        return t ** 3
    if kind == "snap":
        # fast attack, slow settle: reads as a real limb drive
        return 1.0 - (1.0 - t) ** 5
    return 0.5 - 0.5 * math.cos(math.pi * t)


def hop(a: np.ndarray, b: np.ndarray, n: int, tag: tuple[str, str] | None = None,
        ease: str = "inout") -> list[np.ndarray]:
    """n frames of *real* movement from pose ``a`` to pose ``b`` (exclusive of a).

    Occlusion zones are filled from whichever source frame actually sees them, so
    arms/legs stay solid instead of turning into ghost-jelly.
    """
    ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    fwd, bwd, ok = pair_flows(ga, gb, tag)
    xs, ys = base_grid()

    out: list[np.ndarray] = []
    for i in range(1, n + 1):
        t = eased(i / float(n + 1), ease)
        wa = cv2.remap(a, xs + fwd[..., 0] * t, ys + fwd[..., 1] * t,
                       cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        wb = cv2.remap(b, xs - bwd[..., 0] * (1.0 - t), ys - bwd[..., 1] * (1.0 - t),
                       cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        blend = np.where(ok > 0.5, 0.5, np.where(t < 0.5, 1.0, 0.0)).astype(np.float32)
        mixed = wa.astype(np.float32) * blend + wb.astype(np.float32) * (1.0 - blend)
        out.append(np.clip(mixed, 0, 255).astype(np.uint8))
    return out


# --------------------------------------------------------------------------- #
# living-shot micro motion (all local + feathered, never a global wobble)
# --------------------------------------------------------------------------- #
def _feather(y0: float, y1: float, soft: float = 0.06) -> np.ndarray:
    """Smooth 1-D mask over image rows between two fractional heights."""
    row = np.arange(CANON_H, dtype=np.float32) / CANON_H
    m = np.clip((row - y0) / max(1e-6, soft), 0.0, 1.0) * np.clip((y1 - row) / max(1e-6, soft), 0.0, 1.0)
    return m[:, None]


def rigid(img: np.ndarray, dx: float = 0.0, dy: float = 0.0, zoom: float = 1.0,
          rot_deg: float = 0.0) -> np.ndarray:
    """Rigid camera: translate/zoom/rotate the whole frame (no rubber)."""
    if dx == 0 and dy == 0 and zoom == 1.0 and rot_deg == 0.0:
        return img
    cx, cy = CANON_W / 2.0, CANON_H / 2.0
    xs, ys = base_grid()
    x = (xs - cx) / zoom
    y = (ys - cy) / zoom
    if rot_deg:
        th = math.radians(rot_deg)
        xr = x * math.cos(th) - y * math.sin(th)
        yr = x * math.sin(th) + y * math.cos(th)
        x, y = xr, yr
    return cv2.remap(img, (x + cx + dx).astype(np.float32), (y + cy + dy).astype(np.float32),
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def handheld(fno: int, amp: float = 2.2) -> tuple[float, float, float]:
    """Deterministic hand-held camera offsets (sum of incommensurate sines)."""
    f = float(fno)
    dx = amp * (0.55 * math.sin(f * 0.31) + 0.30 * math.sin(f * 0.73 + 1.1) + 0.15 * math.sin(f * 1.7 + 0.4))
    dy = amp * (0.55 * math.cos(f * 0.27 + 0.7) + 0.30 * math.cos(f * 0.61 + 2.0) + 0.15 * math.cos(f * 1.3))
    rot = 0.10 * math.sin(f * 0.19 + 0.3)
    return dx, dy, rot


def _rows() -> np.ndarray:
    return (CANON_H - np.arange(CANON_H, dtype=np.float32))[:, None] / CANON_H


def breathe_field(phase: float, amount: float = 0.004) -> tuple[np.ndarray, np.ndarray]:
    """Chest breathing: torso below the collar travels up/down a hair."""
    m = _feather(0.42, 0.99, 0.10)
    dy = (-amount * CANON_H * math.sin(phase) * m).astype(np.float32)
    dy = dy * (np.clip(_rows(), 0.0, 1.0) * 0.75 + 0.25)
    return np.zeros_like(dy), dy


def weight_field(phase: float, amount: float = 0.003) -> tuple[np.ndarray, np.ndarray]:
    """Stance sway from the ankles: zero at the feet, largest at the shoulders."""
    dx = (amount * CANON_W * math.sin(phase) * (1.0 - _rows()) ** 0.9).astype(np.float32)
    return dx, np.zeros_like(dx)


def head_field(phase: float, amount: float = 0.004, y1: float = 0.34) -> tuple[np.ndarray, np.ndarray]:
    """Head/neck drift: the top band leans, feathered out by the chest."""
    m = _feather(0.0, y1, 0.09)
    dx = (amount * CANON_W * math.sin(phase) * m).astype(np.float32)
    dy = (amount * 0.35 * CANON_H * math.sin(phase * 0.7 + 1.2) * m).astype(np.float32)
    return dx, dy


def cable_field(phase: float, amount: float = 2.4, y1: float = 0.50) -> tuple[np.ndarray, np.ndarray]:
    """Hanging cables / cloth: phase-shifted horizontal sway in the upper band."""
    m = _feather(0.0, y1, 0.12)
    dx = (amount * m * np.sin(phase + 5.0 * base_grid()[0] / CANON_W)).astype(np.float32)
    return dx, np.zeros_like(dx)


def ripple_field(phase: float, amount: float = 3.0, y0: float = 0.68) -> tuple[np.ndarray, np.ndarray]:
    """Wet floor: low-amplitude travelling ripple confined below the feet line."""
    m = _feather(y0, 1.15, 0.16)
    dy = (amount * m * np.sin(18.0 * math.pi * base_grid()[0] / CANON_W - phase)).astype(np.float32)
    dy = dy * (np.clip((np.arange(CANON_H, dtype=np.float32)[:, None] / CANON_H - 0.5) * 2.0, 0.4, 1.4))
    return np.zeros_like(dy), dy


def micro(img: np.ndarray, fno: int, breathe: float = 0.0, weight: float = 0.0,
          head: float = 0.0, cable: float = 0.0, ripple: float = 0.0,
          rate: float = 0.055, phase: float = 0.0) -> np.ndarray:
    """One feathered remap carrying every living-shot layer at once.

    Each layer is a *local* deformation (breathing torso, stance sway, head
    drift, cable sway, floor ripple); summing the fields and doing a single
    remap is both faster and cleaner than stacking warps, and nothing here can
    turn the plate into a global jelly wobble.
    """
    dx = np.zeros((CANON_H, CANON_W), np.float32)
    dy = np.zeros((CANON_H, CANON_W), np.float32)
    p = phase + fno * rate
    if breathe:
        fx, fy = breathe_field(p * 1.35, breathe)
        dx += fx; dy += fy
    if weight:
        fx, fy = weight_field(p * 0.75, weight)
        dx += fx; dy += fy
    if head:
        fx, fy = head_field(p * 1.05 + 0.6, head)
        dx += fx; dy += fy
    if cable:
        fx, fy = cable_field(p * 1.55 + 1.4, cable)
        dx += fx; dy += fy
    if ripple:
        fx, fy = ripple_field(p * 2.1 + 0.9, ripple)
        dx += fx; dy += fy
    return remap(img, dx, dy)


def eye_boxes(img: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Haar eye detector: used to place blinks on whatever plate is on screen."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
    found = cascade.detectMultiScale(gray, scaleFactor=1.06, minNeighbors=7, minSize=(28, 28))
    return [tuple(int(v) for v in box) for box in found]


def blink(img: np.ndarray, boxes: Sequence[Sequence[int]], closure: float) -> np.ndarray:
    """Vertical squeeze of the lid band: 0 = open, 1 = shut.

    Pixels inside the detected eye band are pulled up from just below it, which
    is what a closing lid actually does to the image; the weight is a feathered
    triangle in both axes so nothing outside the eye is touched.
    """
    if closure <= 0.001 or not len(boxes):
        return img
    xs, ys = base_grid()
    src_y = ys.copy()
    for (x, y, w, h) in boxes:
        cy = y + h * 0.45
        band = max(6.0, h * 0.9)
        my = np.clip(1.0 - np.abs(ys - cy) / band, 0.0, 1.0) ** 1.4
        mx = np.clip(1.0 - np.abs(xs - (x + w / 2.0)) / max(4.0, w * 0.85), 0.0, 1.0) ** 1.2
        src_y = src_y + closure * my * mx * (h * 0.80)
    return cv2.remap(img, xs, src_y.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def floor_ripple(img: np.ndarray, phase: float, amp: float = 3.0, y0: float = 0.68) -> np.ndarray:
    """Wet-floor life: low-amplitude travelling ripple confined below the feet line."""
    m = _feather(y0, 1.15, 0.16)
    xs = base_grid()[0]
    dy = (amp * m * np.sin(18.0 * math.pi * xs / CANON_W - phase)).astype(np.float32)
    dy *= np.clip((np.arange(CANON_H, dtype=np.float32)[:, None] / CANON_H - 0.5) * 2.0, 0.4, 1.4)
    return remap(img, np.zeros_like(dy), dy)


def cable_sway(img: np.ndarray, phase: float, amp: float = 2.4, y1: float = 0.50) -> np.ndarray:
    """Cables / cloth: small horizontal sway in the upper background band.

    Different cables move out of phase because the sine is phase-shifted across
    x; the whole thing is faded out before it reaches mid-frame.
    """
    m = _feather(0.0, y1, 0.12)
    xs = base_grid()[0]
    dx = (amp * m * np.sin(phase + 5.0 * xs / CANON_W)).astype(np.float32)
    return remap(img, dx, np.zeros_like(dx))


# --------------------------------------------------------------------------- #
# keyframe warehouse
# --------------------------------------------------------------------------- #
class Keyframes:
    """Canonical-raster action keyframes, loaded once per render."""

    def __init__(self, directory: Path | None = None, names: Iterable[str] = VIGNETTE_KEYS):
        self.dir = Path(directory) if directory else keyframe_dir()
        self.frames: dict[str, np.ndarray] = {}
        missing: list[str] = []
        for name in names:
            path = self.dir / f"{name}.jpg"
            if not path.exists():
                missing.append(str(path))
                continue
            img = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if img is None:
                missing.append(str(path))
                continue
            self.frames[name] = cover_fit(img)
        if missing:
            raise SystemExit(
                "motion engine: missing action keyframes:\n  " + "\n  ".join(missing) +
                "\nstage them with the Drive IDs in styles/monarch-face-chaos/records/KEYFRAME_SOURCE.json"
                " (or set MONARCH_KEYFRAME_DIR)."
            )

    def __getitem__(self, name: str) -> np.ndarray:
        return self.frames[name]

    def plate(self, plate_name: str) -> np.ndarray:
        path = PLATES / plate_name
        img = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if img is None:
            raise SystemExit(f"motion engine: missing canonical plate {path}")
        return cover_fit(img)

    def has(self, name: str) -> bool:
        return name in self.frames
