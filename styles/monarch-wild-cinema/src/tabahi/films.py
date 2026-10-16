"""TABAHI FILMS — procedural atmosphere, impact and speed elements.

Everything here is generated from math, per frame, at render time. No stock
overlays, no downloaded assets: the atmospheric layer is a property of the
scene, not a sticker on top of it.

These are the "next level" ingredients that a Ken Burns slideshow can never
have: light that moves through haze, dust that reacts to a footfall, rays that
sweep, motes that float in depth, and impacts that shake the lens.
"""
from __future__ import annotations

import math

import cv2
import numpy as np

from . import core as C


# ─────────────────────────────────────────────────────────────────────────────
# CAMERA SHAKE  (returns a warp matrix; never a random per-frame jitter)
# ─────────────────────────────────────────────────────────────────────────────

def shake_matrix(t: float, amp: float = 9.0, freq: float = 17.0, seed: float = 0.0):
    """Damped two-frequency shake that DECAYS. Sustained shake reads as a bug."""
    decay = math.exp(-t * 7.0)
    dx = amp * decay * math.sin(2 * math.pi * freq * t + seed)
    dy = amp * decay * 0.62 * math.sin(2 * math.pi * freq * 1.37 * t + seed + 1.1)
    roll = 0.22 * decay * math.sin(2 * math.pi * freq * 0.71 * t)
    m = cv2.getRotationMatrix2D((C.W / 2, C.H / 2), roll, 1.0 + 0.004 * decay)
    m[0, 2] += dx
    m[1, 2] += dy
    return m


def apply_shake(img: np.ndarray, m) -> np.ndarray:
    return cv2.warpAffine(img, m, (img.shape[1], img.shape[0]), borderMode=cv2.BORDER_REPLICATE)


# ─────────────────────────────────────────────────────────────────────────────
# IMPACT  (ring + spark burst, additive, frame-accurate to the sound cue)
# ─────────────────────────────────────────────────────────────────────────────

def impact(img: np.ndarray, t: float, cx=0.5, cy=0.5, strength=1.0,
           color=(255, 236, 206), rings=2) -> np.ndarray:
    if t < 0 or t > 0.55:
        return img
    h, w = img.shape[:2]
    x, y = int(cx * w), int(cy * h)
    # the burst is local: build and blur it inside a bounded ROI, not the frame
    span = int(min(0.62 * min(w, h), 420))
    x0, y0 = max(x - span, 0), max(y - span, 0)
    x1, y1 = min(x + span, w), min(y + span, h)
    layer = np.zeros((y1 - y0, x1 - x0), np.float32)
    for i in range(rings):
        age = t - i * 0.055
        if age <= 0:
            continue
        r = int(40 + 1500 * age)
        # 2-frame attack: an instant burst is a 10+ level frame jump (G04)
        atk = min(age / 0.066, 1.0)
        a = max(0.0, 1.0 - age / 0.42) ** 2.2 * strength * (0.85 ** i) * atk
        if r < 2 or a <= 0.004 or r > span * 2:
            continue
        cv2.circle(layer, (x - x0, y - y0), r, a, max(int(16 * (1 - age)), 2), lineType=cv2.LINE_AA)
    # hot core that decays fastest
    core = max(0.0, 1.0 - t / 0.13) ** 2.4 * strength * 0.85
    if core > 0.01:
        cv2.circle(layer, (x - x0, y - y0), max(int(120 * (1 - t * 4)), 2), core * 0.9, -1,
                   lineType=cv2.LINE_AA)
    layer = cv2.GaussianBlur(layer, (0, 0), 2.2)
    roi = img[y0:y1, x0:x1].astype(np.float32) + layer[..., None] * np.array(color, np.float32)
    out = img.copy()
    out[y0:y1, x0:x1] = np.clip(roi, 0, 255).astype(np.uint8)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# FLASH  (bounded: a flash brighter than the gate ceiling is a defect)
# ─────────────────────────────────────────────────────────────────────────────

def flash(img: np.ndarray, t: float, strength: float = 0.34, color=(255, 244, 226),
          decay: float = 5.5, attack: float = 0.13) -> np.ndarray:
    """A frame-lifting bloom with a controlled RISE.

    MEASURED: an instant flash lifts the whole frame in one frame — at the
    default 0.34 that is a 55-level jump, which is a strobe by the gate's own
    rule (G04 < 8 per frame, and BT.1702's flash threshold for G15). With a
    0.13 s (4 frame) rise the same total lift costs < 7 levels per frame, so
    the hit still lands and nothing blinks.
    """
    if t < 0 or strength <= 0:
        return img
    rise = min(t / max(attack, 1e-3), 1.0)
    a = strength * rise * math.exp(-t * decay)
    if a < 0.004:
        return img
    # MEASURED: a 0.55 alpha flash is a 77-luma frame jump, which fails the
    # flash threshold (G15, BT.1702). The ceiling now matches the gate.
    return C.mix(img, np.zeros_like(img) + np.array(color, np.uint8), min(a, 0.30))


# ─────────────────────────────────────────────────────────────────────────────
# HAZE / DUST  (drifting volumetric layer; two octaves of blurred noise)
# ─────────────────────────────────────────────────────────────────────────────

_HAZE_CACHE: dict[int, np.ndarray] = {}


def _haze_base(seed: int) -> np.ndarray:
    if seed not in _HAZE_CACHE:
        rng = np.random.default_rng(seed)
        n = rng.random((C.H // 4, C.W // 4)).astype(np.float32)
        b = cv2.GaussianBlur(n, (0, 0), 12)
        b = (b - b.min()) / (b.max() - b.min() + 1e-6)
        _HAZE_CACHE[seed] = b
    return _HAZE_CACHE[seed]


def haze(img: np.ndarray, t: float, strength: float = 0.16, seed: int = 3,
         speed: float = 0.020, tint=(196, 208, 220)) -> np.ndarray:
    if strength <= 0.002:
        return img
    base = _haze_base(seed)
    # two offset reads of one cached field = parallax drift without new noise
    oy = int((t * speed * C.H) % base.shape[0])
    ox = int((t * speed * 0.6 * C.W) % base.shape[1])
    a = np.roll(np.roll(base, oy, axis=0), ox, axis=1)
    b = np.roll(np.roll(base, -int(oy * 0.6), axis=0), int(ox * 1.7), axis=1)
    f = 0.62 * a + 0.38 * b
    f = cv2.resize(f, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    f = np.clip((f - 0.35) * 1.5, 0, 1) * strength
    m8 = (f * 255.0).astype(np.uint8)
    tint_img = np.empty_like(img)
    tint_img[...] = np.array(tint, np.uint8)
    inv = cv2.bitwise_not(np.repeat(m8[..., None], 3, axis=2))
    return cv2.add(cv2.multiply(img, inv, scale=1.0 / 255.0),
                   cv2.multiply(tint_img, np.repeat(m8[..., None], 3, axis=2), scale=1.0 / 255.0))


# ─────────────────────────────────────────────────────────────────────────────
# GOD RAYS  (directional volumetric shafts from the key light)
# ─────────────────────────────────────────────────────────────────────────────

def god_rays(img: np.ndarray, t: float, strength: float = 0.22, angle_deg: float = 68.0,
             sweep: float = 0.9, seed: int = 11) -> np.ndarray:
    """Shafts of light from the upper left, peaked and renormalised.

    MEASURED CORRECTION: the first version added `ray * (colour * strength *
    60)` — a 2800x tint multiplied by the ray field, which at the plan's 0.20
    strength blew the frame to white (read back from a rendered frame; the
    numeric self-check had no ceiling, so it never noticed). The field is now
    peak-normalised, so `strength` reads directly as "peak brightness added, as
    a fraction of full scale": 0.20 adds ~18 % in the brightest shaft.
    """
    if strength <= 0.002:
        return img
    h, w = img.shape[:2]
    sw, sh = max(w // 4, 8), max(h // 4, 8)          # build the field at quarter res
    a = math.radians(angle_deg + sweep * 6.0 * math.sin(2 * math.pi * 0.045 * t))
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    u = (xx / sw) * math.cos(a) + (yy / sh) * math.sin(a)
    v = -(xx / sw) * math.sin(a) + (yy / sh) * math.cos(a)
    stripes = (0.5 + 0.5 * np.sin(u * 22.0 + 1.6 * math.sin(2 * math.pi * 0.03 * t))) ** 3.0
    src = np.exp(-((v - (0.10 + 0.05 * math.sin(2 * math.pi * 0.017 * t))) ** 2) / (2 * 0.20 ** 2))
    falloff = np.clip(1.05 - (yy / sh) * 0.95, 0, 1)
    ray = cv2.GaussianBlur(stripes * src * falloff, (0, 0), 2.2)
    ray8 = cv2.resize(ray, (w, h), interpolation=cv2.INTER_LINEAR)
    peak = max(float(ray8.max()), 1e-6)
    ray8 = ray8 / peak
    tint = np.array((214, 200, 168), np.float32) / 255.0
    add = ray8[..., None] * tint * 255.0 * float(np.clip(strength, 0.0, 1.0)) * 0.9
    return np.clip(img.astype(np.float32) + add, 0, 255).astype(np.uint8)


# ─────────────────────────────────────────────────────────────────────────────
# MOTES  (floating particles that respect the DEPTH field — they parallax)
# ─────────────────────────────────────────────────────────────────────────────

def motes(img: np.ndarray, t: float, count: int = 90, strength: float = 0.55,
          depth_alpha: np.ndarray | None = None, seed: int = 5) -> np.ndarray:
    if count <= 0 or strength <= 0.002:
        return img
    rng = np.random.default_rng(seed)
    h, w = img.shape[:2]
    px = rng.random(count)
    py = rng.random(count)
    pz = 0.25 + 0.75 * rng.random(count)          # depth: near ones drift faster
    ph = rng.random(count) * 6.283
    sp = 0.06 + 0.22 * pz
    x = ((px + t * sp * 0.07 + 0.5 * np.sin(2 * np.pi * (0.03 * pz) * t + ph)) % 1.0) * w
    y = ((py - t * sp * 0.045) % 1.0) * h
    layer = np.zeros((h, w), np.float32)
    # a mote behind the subject must be smaller and dimmer than one in front:
    # sample the scene depth field where the mote actually is
    depth_gain = np.ones(count, np.float32)
    if depth_alpha is not None:
        xi = np.clip((x / w * depth_alpha.shape[1]).astype(np.int32), 0, depth_alpha.shape[1] - 1)
        yi = np.clip((y / h * depth_alpha.shape[0]).astype(np.int32), 0, depth_alpha.shape[0] - 1)
        depth_gain = 0.45 + 0.55 * depth_alpha[yi, xi, 0]
    rad = np.maximum((( 1.0 + 3.4 * pz) * depth_gain).astype(np.int32), 1)
    for i in range(count):
        cv2.circle(layer, (int(x[i]), int(y[i])), int(rad[i]),
                   float(strength * (0.35 + 0.65 * pz[i]) * depth_gain[i]), -1,
                   lineType=cv2.LINE_AA)
    layer = cv2.GaussianBlur(layer, (0, 0), 1.6)
    add = layer[..., None] * np.array((236, 226, 206), np.float32)
    return np.clip(img.astype(np.float32) + add, 0, 255).astype(np.uint8)


# ─────────────────────────────────────────────────────────────────────────────
# SPEED STREAKS  (for the "SPRINT" beat — directional, not a lens flare)
# ─────────────────────────────────────────────────────────────────────────────

def speed_streaks(img: np.ndarray, t: float, strength: float = 0.5, angle_deg: float = 12.0) -> np.ndarray:
    if strength <= 0.004:
        return img
    h, w = img.shape[:2]
    rng = np.random.default_rng(23)
    n = 46
    layer = np.zeros((h, w), np.float32)
    a = math.radians(angle_deg)
    base = rng.random(n)
    for i in range(n):
        y = int((base[i] * 0.92 + 0.04) * h)
        off = (t * (900 + 1400 * base[i])) % (w * 1.6) - w * 0.3
        x0 = int(off)
        ln = int(180 + 900 * base[i])
        x1 = x0 + int(ln * math.cos(a))
        y1 = y + int(ln * math.sin(a))
        cv2.line(layer, (x0, y), (x1, y1), float((0.4 + 0.6 * base[i]) * strength), 2, lineType=cv2.LINE_AA)
    layer = cv2.GaussianBlur(layer, (0, 0), 3.2)
    add = layer[..., None] * np.array((226, 232, 240), np.float32)
    return np.clip(img.astype(np.float32) + add, 0, 255).astype(np.uint8)


# ─────────────────────────────────────────────────────────────────────────────
# CHROMA / OPTICAL CHARACTER
# ─────────────────────────────────────────────────────────────────────────────

def chroma(img: np.ndarray, amount: float = 1.6) -> np.ndarray:
    """Lateral chromatic aberration, scaled from the centre. Subtle by law."""
    if amount <= 0.05:
        return img
    h, w = img.shape[:2]
    c = (w / 2.0, h / 2.0)
    ch = cv2.split(img.astype(np.float32))
    out = []
    for i, s in enumerate((1 + amount / 4000.0, 1.0, 1 - amount / 4000.0)):
        m = cv2.getRotationMatrix2D(c, 0, s)
        out.append(cv2.warpAffine(ch[i], m, (w, h), borderMode=cv2.BORDER_REPLICATE))
    return np.clip(cv2.merge(out), 0, 255).astype(np.uint8)


def letterbox(img: np.ndarray, bar: int = 0, color=(0, 0, 0)) -> np.ndarray:
    if bar <= 0:
        return img
    out = img.copy()
    out[:bar] = color
    out[-bar:] = color
    return out
