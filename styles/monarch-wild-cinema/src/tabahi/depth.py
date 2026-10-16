"""TABAHI DEPTH — image-space 2.5D parallax for landscape plates.

This is the single largest upgrade over a Ken Burns pan. A flat plate becomes a
stage with a near plane, a mid plane and a far plane that move at DIFFERENT
rates, so the frame reads as a camera in a place rather than a photo sliding
behind a window.

Honest scope (inherited law from WF-05):
  * this is 2.5D compositing of a 2D plate — it is NOT reconstructed 3D geometry
  * no foreground pixels are keyed out; the near/far blend feathers only in
    empty margin, and a constant-depth plateau keeps the subject cluster rigid
  * camera motion SUPPLEMENTS subject motion; it never certifies a static slide
"""
from __future__ import annotations

import functools
import math

import cv2
import numpy as np

from . import core as C

# Operating defaults (labelled, not commandments).
NEAR_PLATEAU_FLOOR = 0.30     # depth floor inside the subject plateau
FEATHER_PX = 190.0           # blend feather, must exceed max displacement
HAZE_MAX = 0.22              # far-plane atmospheric mix at full depth split
CANVAS_OVER = 1.22           # environment canvas overscan (kills edge reveal)


# ─────────────────────────────────────────────────────────────────────────────
# 1 · THE DEPTH FIELD
# ─────────────────────────────────────────────────────────────────────────────

def saliency(plate: np.ndarray) -> np.ndarray:
    """Soft subject saliency at 1/8 scale: darkness + local contrast + saturation.

    Dark-and-textured-and-saturated is what a photographic subject looks like
    against a lit, hazy wildlife background. It is a heuristic, and it is
    deliberately blended with the explicit plateau so a failed heuristic
    degrades to the safe rectangle instead of producing a visible tear.
    """
    h, w = plate.shape[:2]
    s = 8
    small = cv2.resize(plate, (max(w // s, 8), max(h // s, 8)), interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(small, cv2.COLOR_RGB2LAB).astype(np.float32)
    L = lab[..., 0] / 255.0
    hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV).astype(np.float32)
    sat = hsv[..., 1] / 255.0

    base = cv2.GaussianBlur(L, (0, 0), 1.6)
    detail = np.abs(L - base)
    detail = detail / (np.percentile(detail, 97) + 1e-6)
    dark = 1.0 - L

    sal = 0.46 * np.clip(dark, 0, 1) + 0.34 * np.clip(detail, 0, 1) + 0.20 * np.clip(sat, 0, 1)
    sal = cv2.GaussianBlur(sal, (0, 0), max(small.shape[1] * 0.055, 2.0))
    lo, hi = np.percentile(sal, 4), np.percentile(sal, 96)
    return np.clip((sal - lo) / (hi - lo + 1e-6), 0, 1)


def depth_field(plate: np.ndarray, hint: dict) -> np.ndarray:
    """0 = far, 1 = near. Returns float32 at plate resolution.

    hint keys
      mode    : "rect" | "auto" | "hybrid"   (default hybrid)
      rect    : (x0, y0, x1, y1) normalized subject plateau
      feather : (fx, fy) normalized outward feather
      floor   : depth floor inside the plateau (default 0.30)
    """
    h, w = plate.shape[:2]
    mode = hint.get("mode", "hybrid")
    floor = float(hint.get("floor", NEAR_PLATEAU_FLOOR))
    rect = hint.get("rect", (0.14, 0.12, 0.86, 0.94))
    fx, fy = hint.get("feather", (0.13, 0.11))

    x0, y0, x1, y1 = rect
    X = np.arange(w, dtype=np.float32)[None, :]
    Y = np.arange(h, dtype=np.float32)[:, None]
    dx = np.maximum(np.maximum((x0 * w) - X, X - (x1 * w)), 0) / max(fx * w, 1e-3)
    dy = np.maximum(np.maximum((y0 * h) - Y, Y - (y1 * h)), 0) / max(fy * h, 1e-3)
    plateau = 1.0 - C.smooth(np.maximum(dx, dy))

    if mode == "rect":
        d = plateau.copy()
    else:
        sal = saliency(plate)
        sal = cv2.resize(sal, (w, h), interpolation=cv2.INTER_LINEAR)
        auto = sal
        if mode == "auto":
            d = auto
        else:
            # the plateau gates the heuristic: silhouette detail inside,
            # guaranteed-safe falloff outside
            d = plateau * (floor + (1.0 - floor) * auto)
            d = np.maximum(d, plateau * floor * 0.85)

    d = cv2.GaussianBlur(d.astype(np.float32), (0, 0), max(w * 0.006, 2.0))
    return np.clip(d, 0.0, 1.0).astype(np.float32)


def far_colour(plate: np.ndarray, d: np.ndarray) -> tuple[int, int, int]:
    """Automatic atmospheric colour: the mean of the deepest pixels."""
    m = d < max(float(np.percentile(d, 25)), 0.12)
    if m.sum() < 64:
        m = d < float(np.percentile(d, 40))
    px = plate[m]
    return tuple(int(v) for v in px.mean(axis=0))


# ─────────────────────────────────────────────────────────────────────────────
# 2 · THE ENVIRONMENT CANVAS  (kills the mirror-smudge reveal edge)
# ─────────────────────────────────────────────────────────────────────────────

def make_canvas(plate: np.ndarray, far_rgb, over: float = CANVAS_OVER) -> tuple[np.ndarray, int, int]:
    """Overscan canvas: sharp plate in the middle, haze-smear environment around.

    A plain BORDER_REFLECT pull-back shows a mirrored smudge at the edges. Here
    the plate is embedded in a blurred, atmospheric extension of itself tinted
    toward the computed far colour, so a dolly-out reads as retreating into haze.
    """
    cw, ch = int(C.W * over), int(C.H * over)
    base = C.resize(plate, cw, ch)
    ox, oy = (cw - C.W) // 2, (ch - C.H) // 2

    small = C.resize(base, max(cw // 14, 8), max(ch // 14, 8))
    small = cv2.GaussianBlur(small, (0, 0), 3.0)
    env = C.resize(small, cw, ch, interp=cv2.INTER_CUBIC)
    env = C.mix(env, np.zeros_like(env) + np.array(far_rgb, np.uint8), 0.55)
    env = C.mix(env, np.zeros_like(env) + np.array(C.INK, np.uint8), 0.16)

    mask = np.zeros((ch, cw), np.float32)
    fx, fy = int(C.W * 0.10), int(C.H * 0.10)
    mask[oy:oy + C.H, ox:ox + C.W] = 1.0
    mask = cv2.GaussianBlur(mask, (0, 0), max(fx * 0.5, 12))
    mask = np.clip(mask * 1.85, 0, 1)

    canvas = C.mix(env, base, mask)
    return canvas, ox, oy


# ─────────────────────────────────────────────────────────────────────────────
# 3 · THE CAMERA  (independent near/far transforms, never fully static)
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_CAM = {
    "zoom": (0.030, 0.075),     # near-plane push across the shot
    "orbit": 26.0,              # px of lateral near-plane travel
    "roll": 0.42,               # degrees
    "drift": -9.0,              # px vertical
    "breathe": 1.6,             # px of never-still micro drift
    "ramp": "linear",           # linear | in | out
    "yaw": 0.000020,            # coherent perspective shear
}


def _ramp(mode: str, p: float) -> float:
    """Linear-dominant by default: an eased ramp parks at both ends and a
    typographic card then measures as frozen (ledger #33)."""
    if mode == "in":
        return C.e_io(p)
    if mode == "out":
        return C.e_io(1 - p)
    return C.linear_dominant(p)


def camera_maps(d: np.ndarray, p: float, ox: int, oy: int, cw: int, ch: int,
                cam: dict, direction: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Return full-resolution remap coordinates (float32) into the canvas."""
    cam = {**DEFAULT_CAM, **(cam or {})}
    p = C.clamp(p)
    u = _ramp(cam.get("ramp", "tri"), p)
    direction = 1 if direction >= 0 else -1

    z0, z1 = cam["zoom"]
    z = 1.0 + (z0 + (z1 - z0) * u)
    tx = direction * cam["orbit"] * (u - 0.5) * 2.0
    ty = cam["drift"] * math.sin(math.pi * p)
    roll = direction * cam["roll"] * math.sin(2.2 * p)
    br_z = 1.0 + cam["breathe"] / C.H * math.sin(2 * math.pi * 0.31 * p + 0.6)
    br_x = cam["breathe"] * math.sin(2 * math.pi * 0.21 * p)
    br_y = cam["breathe"] * 0.8 * math.cos(2 * math.pi * 0.17 * p)

    cxc, cyc = cw / 2.0, ch / 2.0
    near = cv2.getRotationMatrix2D((cxc, cyc), roll, z * br_z)
    near[0, 2] += tx + br_x
    near[1, 2] += ty + br_y
    near = np.vstack([near, [0, 0, 1]]).astype(np.float32)
    near[2, 0] = direction * cam["yaw"] * math.sin(math.pi * p)
    near[2, 1] = cam["yaw"] * 0.4 * math.sin(math.pi * p)

    far = cv2.getRotationMatrix2D((cxc, cyc), -roll * 0.16, 1.0 + (z - 1.0) * 0.22)
    far[0, 2] -= tx * 0.17
    far[1, 2] -= ty * 0.13
    far = np.vstack([far, [0, 0, 1]]).astype(np.float32)

    # Coarse grid, blended per pixel by depth, then upsampled to full res.
    step = 8          # the maps are smooth; a coarse grid + bilinear is invisible
    gy, gx = np.mgrid[0:C.H:step, 0:C.W:step].astype(np.float32)
    gx = gx + ox
    gy = gy + oy
    pts = np.dstack([gx, gy]).reshape(-1, 1, 2)
    pn = cv2.perspectiveTransform(pts, np.linalg.inv(near)).reshape(gy.shape + (2,))
    pf = cv2.perspectiveTransform(pts, np.linalg.inv(far)).reshape(gy.shape + (2,))
    dc = d[::step, ::step][..., None]
    coords = pn * dc + pf * (1 - dc)
    mx = cv2.resize(coords[..., 0], (C.W, C.H), interpolation=cv2.INTER_LINEAR)
    my = cv2.resize(coords[..., 1], (C.W, C.H), interpolation=cv2.INTER_LINEAR)
    return mx - ox, my - oy


# ─────────────────────────────────────────────────────────────────────────────
# 4 · THE PARALLAX PASS
# ─────────────────────────────────────────────────────────────────────────────

class Stage:
    """A prepared plate: canvas + depth field + far colour, ready to warp fast."""

    def __init__(self, plate: np.ndarray, hint: dict | None = None, over: float = CANVAS_OVER):
        hint = hint or {}
        self.plate = plate
        self.d = depth_field(plate, hint)
        self.far = far_colour(plate, self.d)
        self.canvas, self.ox, self.oy = make_canvas(plate, self.far, over)
        self.ch, self.cw = self.canvas.shape[:2]
        self.hint = hint
        self._soft = cv2.GaussianBlur(self.canvas, (0, 0), 1.1)
        # motes sample this to size themselves by scene depth (cheap, once)
        self._d_alpha = (1.0 - cv2.resize(self.d, (C.W, C.H),
                                          interpolation=cv2.INTER_LINEAR))[..., None]

    def frame(self, p: float, cam: dict | None = None, direction: int = 1,
              haze: float = HAZE_MAX) -> np.ndarray:
        mx, my = camera_maps(self.d, p, self.ox, self.oy, self.cw, self.ch, cam or {}, direction)
        out = cv2.remap(self.canvas, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

        # Far-plane atmospheric separation: distance is made visible, so modest
        # parallax reads even on a soft, low-contrast generative plate.
        if haze > 0.0:
            if self._d_alpha is None:
                a = cv2.resize(self.d, (C.W, C.H), interpolation=cv2.INTER_LINEAR)
                self._d_alpha = (1.0 - a)[..., None].astype(np.float32)
            amount = self._d_alpha * haze
            air = np.zeros_like(out, dtype=np.float32) + np.array(self.far, np.float32) + 16.0
            out = np.clip(out.astype(np.float32) * (1 - amount) + air * amount, 0, 255).astype(np.uint8)
        return out


def stage_from_file(path, hint: dict | None = None, over: float = CANVAS_OVER) -> Stage:
    from PIL import Image
    im = Image.open(path).convert("RGB")
    im = im.resize((C.W, C.H), Image.LANCZOS) if im.size != (C.W, C.H) else im
    return Stage(C.as_array(im), hint, over)


def depth_preview(stage: Stage) -> np.ndarray:
    """Diagnostic: the depth field as a heat image (measure, do not trust the eye)."""
    d = cv2.resize(stage.d, (C.W, C.H), interpolation=cv2.INTER_LINEAR)
    return cv2.applyColorMap((d * 255).astype(np.uint8), cv2.COLORMAP_TURBO)[..., ::-1].copy()
