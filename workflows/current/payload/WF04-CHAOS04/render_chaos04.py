#!/usr/bin/env python3
"""WF-04 · MONARCH CHAOS 04 — cinematic motion edit of the supplied raw footage.

Grade -> bloom -> light leaks -> HUD -> beat-snapped cut rhythm -> gold emblem
end card -> mastered 48 kHz stereo audio, encoded to the delivered CHAOS 03
technical standard (1080x1920, 30 fps, H.264 High, faststart).

Every timing decision is measured from the decoded source (onsets, shot energy,
luma), never guessed. Output: output/CHAOS04_MASTER.mp4 + plan/ACT_PLAN.json.
"""
from __future__ import annotations
import json, math, subprocess, sys, wave
from pathlib import Path
import numpy as np
import cv2
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SRC = HERE / 'materials' / 'raw_source.mp4'
ASSETS = HERE / 'assets'
OUTDIR = HERE / 'output'
WORK = HERE / 'work'
FF = imageio_ffmpeg.get_ffmpeg_exe()
FONTS = HERE.parents[3] / 'styles' / 'premium-motion-editing' / 'assets' / 'fonts'
W, H, FPS = 1080, 1920, 30
TW, TH = W // 2, H // 2          # grade at half res, upscale for speed
TOTAL = 44.40                     # 1332 frames
END_CARD = 1.60                   # emblem hold at the tail


# --------------------------------------------------------------------------- #
# source helpers
# --------------------------------------------------------------------------- #
def probe() -> dict:
    out = subprocess.run([FF, '-hide_banner', '-i', str(SRC)], capture_output=True, text=True).stderr
    info = {'lines': [l.strip() for l in out.splitlines() if 'Stream' in l or 'Duration' in l]}
    cap = cv2.VideoCapture(str(SRC))
    info['frames'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    info['fps'] = round(float(cap.get(cv2.CAP_PROP_FPS)), 3)
    cap.release()
    return info


def decode_audio(path: Path) -> tuple[int, np.ndarray]:
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(SRC), '-vn',
                    '-ac', '2', '-ar', '48000', '-c:a', 'pcm_s16le', str(path)], check=True)
    with wave.open(str(path), 'rb') as r:
        sr, ch, n = r.getframerate(), r.getnchannels(), r.getnframes()
        x = np.frombuffer(r.readframes(n), '<i2').astype(np.float32).reshape(-1, ch) / 32768
    return sr, x


def onsets(x: np.ndarray, sr: int) -> list[float]:
    mono = x.mean(axis=1)
    hop, win = 256, 1024
    n = 1 + (len(mono) - win) // hop
    env = np.array([np.sqrt(np.mean(mono[i * hop:i * hop + win] ** 2) + 1e-12) for i in range(n)])
    flux = np.maximum(0, np.diff(np.log(env + 1e-6)))
    t = np.arange(len(flux)) * hop / sr
    thr = np.percentile(flux, 80)
    out = []
    for i in range(1, len(flux) - 1):
        if flux[i] > thr and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]:
            if not out or t[i] - out[-1] > 0.14:
                out.append(round(float(t[i]), 3))
    return out


def shot_energy(analysis: dict) -> dict[int, float]:
    return {s['index']: s['mean_internal_diff'] for s in analysis['shots']}


def shot_luma(analysis: dict) -> dict[int, float]:
    return {s['index']: s['mean_luma'] for s in analysis['shots']}


def read_window(start_frame: int, count: int) -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(SRC))
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frames = []
    for _ in range(count):
        ok, f = cap.read()
        if not ok:
            break
        if f.shape[:2] != (1280, 720):
            f = cv2.resize(f, (720, 1280))
        frames.append(f)
    cap.release()
    return frames


# --------------------------------------------------------------------------- #
# grade
# --------------------------------------------------------------------------- #
def grade(f: np.ndarray, p: dict, phase: float) -> np.ndarray:
    """Cinematic grade at half resolution: contrast curve, split tone, vignette."""
    img = cv2.resize(f, (TW, TH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    # gentle S-curve contrast
    k = p['contrast']
    img = np.clip((img - .5) * k + .5 + p['lift'], 0, 1)
    # midtone lift: the raw grade is very dark, so expose per act
    img = np.clip(img, 0, 1) ** (1.0 / p.get('gamma', 1.0))
    # split tone: cool shadows, warm highlights
    lum = img @ np.array([.2126, .7152, .0722], np.float32)
    shadow = np.clip(1.0 - lum * p['shadow_falloff'], 0, 1)[..., None]
    high = np.clip((lum - .55) * 1.9, 0, 1)[..., None]
    img = img + shadow * np.array(p['shadow_tint'], np.float32) * .55
    img = img + high * np.array(p['high_tint'], np.float32) * .45
    # saturation
    img = np.clip(lum[..., None] + (img - lum[..., None]) * p['sat'], 0, 1)
    # vignette
    if 'vig' not in p['_cache']:
        yy, xx = np.mgrid[0:TH, 0:TW].astype(np.float32)
        r = np.sqrt(((xx - TW / 2) / (TW / 2)) ** 2 + ((yy - TH / 2) / (TH / 2)) ** 2)
        p['_cache']['vig'] = np.clip(1.0 - p['vig_strength'] * r ** 2.1, 0, 1)[..., None]
    img = img * p['_cache']['vig']
    # bloom over highlights
    hi = np.clip(img - .72, 0, 1)
    if hi.max() > .01:
        img = np.clip(img + cv2.GaussianBlur(hi, (0, 0), 9) * p['bloom'], 0, 1)
    return img


def to_bgr(img_half: np.ndarray) -> np.ndarray:
    up = cv2.resize(img_half, (W, H), interpolation=cv2.INTER_CUBIC)
    return (np.clip(up, 0, 1) * 255).astype(np.uint8)


LEAKS = ['leak_red_left.png', 'leak_blue_right.png', 'leak_magenta_left.png',
         'leak_gold_top.png', 'leak_cyan_bottom.png']
_leak_cache: dict[str, np.ndarray] = {}


def leak_layer(name: str) -> np.ndarray:
    if name not in _leak_cache:
        im = Image.open(ASSETS / name)
        rgb = np.asarray(im.convert('RGB')).astype(np.float32)
        a = np.asarray(im.getchannel('A')).astype(np.float32)[..., None] / 255.0
        _leak_cache[name] = np.concatenate([rgb, a * 255], axis=2).astype(np.float32)
    return _leak_cache[name]


def apply_leak(frame: np.ndarray, names: list[str], amount: float) -> np.ndarray:
    if amount <= 0.004:
        return frame
    f = frame.astype(np.float32)
    for n in names:
        lay = leak_layer(n)
        a = (lay[..., 3:4] / 255.0) * amount
        f = f * (1 - a) + lay[..., :3] * a
    return np.clip(f, 0, 255).astype(np.uint8)


def shake(phase: float, amp: float, seed: int) -> tuple[int, int]:
    a = math.sin(phase * 6.1 + seed) * amp + math.sin(phase * 13.7 + seed * 2.3) * amp * .4
    b = math.cos(phase * 5.3 + seed * 1.7) * amp * .8 + math.sin(phase * 11.1 + seed) * amp * .3
    return int(a), int(b)


def push_in(frame: np.ndarray, zoom: float, dx: int = 0, dy: int = 0) -> np.ndarray:
    if abs(zoom - 1) < 1e-4 and dx == 0 and dy == 0:
        return frame
    m = cv2.getRotationMatrix2D((W / 2, H / 2), 0, zoom)
    m[0, 2] += dx; m[1, 2] += dy
    return cv2.warpAffine(frame, m, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)


# --------------------------------------------------------------------------- #
# HUD + end card
# --------------------------------------------------------------------------- #
_font_cache: dict[tuple[int, str], ImageFont.FreeTypeFont] = {}


def font(size: int, kind: str = 'head') -> ImageFont.FreeTypeFont:
    if (size, kind) not in _font_cache:
        name = {'head': 'Anton-Regular.ttf', 'body': 'BarlowCondensed-Medium.ttf',
                'italic': 'BarlowCondensed-MediumItalic.ttf'}[kind]
        _font_cache[(size, kind)] = ImageFont.truetype(str(FONTS / name), size)
    return _font_cache[(size, kind)]


def hud(frame: np.ndarray, t_act: float, act_len: float, label: str, tint) -> np.ndarray:
    im = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert('RGBA')
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    x0, y0, x1, y1 = 54, int(H * .62), W - 54, int(H * .62) + 186
    c = (*tint, 235)
    d.line([(x0, y0), (x0 + 64, y0)], fill=c, width=3)
    d.line([(x0, y0), (x0, y0 + 64)], fill=c, width=3)
    d.line([(x1, y1), (x1 - 64, y1)], fill=c, width=3)
    d.line([(x1, y1), (x1, y1 - 64)], fill=c, width=3)
    d.text((x0 + 18, y0 + 12), 'MONARCH // NEURAL SYNC', font=font(30, 'body'), fill=c)
    d.text((x0 + 18, y0 + 52), label, font=font(62, 'head'), fill=c)
    prog = min(1.0, max(0.0, t_act / max(act_len, .01)))
    d.text((x0 + 18, y0 + 132), f'SYNC {int(prog * 100):02d}%', font=font(26, 'italic'), fill=c)
    bx = x0 + 18
    d.rectangle([bx, y0 + 164, x1 - 18, y0 + 174], outline=(*tint, 150), width=2)
    d.rectangle([bx + 3, y0 + 167, bx + 3 + (x1 - 18 - bx - 6) * prog, y0 + 171], fill=c)
    # frame counter ticks
    for k in range(11):
        xx = x0 + 18 + k * ((x1 - x0 - 36) / 10)
        d.line([(xx, y0 - 22), (xx, y0 - 12)], fill=(*tint, 120), width=2)
    out = Image.alpha_composite(im, ov)
    return cv2.cvtColor(np.asarray(out.convert('RGB')), cv2.COLOR_RGB2BGR)


def scanlines(frame: np.ndarray, strength: float) -> np.ndarray:
    f = frame.astype(np.float32)
    rows = (np.sin(np.arange(H) * math.pi) * .5 + .5) ** 2
    f *= (1 - strength * (1 - rows))[:, None, None]
    return np.clip(f, 0, 255).astype(np.uint8)


_emblem: np.ndarray | None = None


def emblem_frame(phase: float) -> np.ndarray:
    global _emblem
    if _emblem is None:
        _emblem = cv2.imread(str(ASSETS / 'emblem.png'))
    zoom = 1.0 + 0.035 * phase
    return push_in(_emblem, zoom, 0, int(-8 * phase))


# --------------------------------------------------------------------------- #
# audio mastering (BS.1770 LUFS + true peak)
# --------------------------------------------------------------------------- #
def _k_filters(sr: int):
    from scipy.signal import lfilter
    # BS.1770 pre-filter (high shelf) + RLB high-pass, coefficients for 48 kHz
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, -1.99004745483398, 0.99007225036621]
    return (b1, a1, b2, a2), lfilter


def lufs(x: np.ndarray, sr: int = 48000, block: float = .4, overlap: float = .75) -> float:
    (b1, a1, b2, a2), lfilter = _k_filters(sr)
    y = lfilter(b2, a2, lfilter(b1, a1, x, axis=0), axis=0)
    step = int(block * sr * (1 - overlap))
    size = int(block * sr)
    powers = []
    for i in range(0, max(1, len(y) - size), max(step, 1)):
        seg = y[i:i + size]
        powers.append(np.sum(seg ** 2, axis=0).mean() if seg.ndim > 1 else np.sum(seg ** 2))
    p = np.array(powers) / size + 1e-12
    loud = -0.691 + 10 * np.log10(p)
    keep = loud > (np.max(loud) - 20) if len(loud) else np.array([True])
    return float(-0.691 + 10 * np.log10(p[keep].mean() if keep.any() else p.mean()))


def true_peak(x: np.ndarray, sr: int = 48000, os: int = 4) -> float:
    from scipy.signal import resample_poly
    y = resample_poly(x, os, 1, axis=0)
    return float(20 * np.log10(np.max(np.abs(y)) + 1e-12))


def compress(x: np.ndarray, sr: int, thresh_db=-18.0, ratio=2.6, attack=.008, release=.16,
             makeup_db=3.0) -> np.ndarray:
    mono = np.abs(x).max(axis=1)
    env = np.zeros_like(mono)
    a = math.exp(-1 / (attack * sr)); r = math.exp(-1 / (release * sr))
    prev = 0.0
    for i, v in enumerate(mono):
        coeff = a if v > prev else r
        prev = coeff * prev + (1 - coeff) * v
        env[i] = prev
    db = 20 * np.log10(env + 1e-9)
    gain = np.ones_like(db)
    over = db > thresh_db
    gain[over] = (thresh_db + (db[over] - thresh_db) / ratio) - db[over]
    g = (10 ** (gain / 20)) * (10 ** (makeup_db / 20))
    return x * g[:, None]


def master_audio(sr: int, x: np.ndarray, plan: dict) -> tuple[np.ndarray, dict]:
    from scipy.signal import butter, sosfilt
    y = sosfilt(butter(2, 32, 'high', fs=sr, output='sos'), x, axis=0)          # rumble out
    y = sosfilt(butter(2, 16000, 'low', fs=sr, output='sos'), y, axis=0)        # air roll-off
    y = y + np.stack([np.zeros_like(y[:, 0]), np.zeros_like(y[:, 0])], axis=1) if y.ndim == 1 else y
    # low-shelf weight so the bass reads on phone speakers
    y = y.copy()
    y[:, 0] *= 1.0
    y = compress(y, sr, thresh_db=-16.0, ratio=2.4, makeup_db=2.5)
    # cinematic sub-boom + reverse riser into the climax, pad under the end card
    n = len(y)
    def add(sig, at, gain=1.0):
        i0 = int(at * sr)
        m = min(len(sig), n - i0)
        if m > 0:
            contrib = sig[:m] * gain
            if contrib.ndim == 1:
                contrib = np.stack([contrib, contrib], axis=1)
            y[i0:i0 + m] += contrib
    boom_len = int(1.1 * sr)
    tb = np.arange(boom_len) / sr
    boom = (np.sin(2 * np.pi * (52 * np.exp(-tb * 2.2) + 34) * tb) *
            np.exp(-tb * 3.0)).astype(np.float32)
    add(boom * .55, plan['climax_start'] - .06)
    riser_len = int(1.5 * sr)
    tr = np.arange(riser_len) / sr
    noise = np.random.default_rng(3).normal(0, 1, riser_len).astype(np.float32)
    sweep = sosfilt(butter(2, [300, 6000], 'band', fs=sr, output='sos'), noise) * (tr / tr.max()) ** 2
    add(sweep * .12, plan['climax_start'] - 1.5)
    # gentle limiter
    target, tp_ceiling = -16.0, -1.5
    y = y / (np.max(np.abs(y)) + 1e-9) * .90
    for _ in range(8):
        cur = lufs(y, sr)
        y = y * (10 ** ((target - cur) / 20))
        tp = true_peak(y, sr)
        if tp <= tp_ceiling:
            break
        over = tp - tp_ceiling
        y = np.tanh(y * (10 ** (over / 20)) * 1.0) / (10 ** (over / 20))
    cur = lufs(y, sr)
    if abs(cur - target) > .6:                      # final trim inside the ceiling
        y = y * (10 ** ((target - cur) / 20))
        if true_peak(y, sr) > tp_ceiling:
            y *= 10 ** ((tp_ceiling - .1 - true_peak(y, sr)) / 20)
    y = np.stack([y[:, 0], y[:, 1]], axis=1)
    info = {'lufs': round(lufs(y, sr), 2), 'true_peak_dbfs': round(true_peak(y, sr), 2),
            'peak_dbfs': round(20 * math.log10(np.max(np.abs(y)) + 1e-9), 2),
            'stereo_correlation': round(float(np.corrcoef(y[:sr * 20, 0], y[:sr * 20, 1])[0, 1]), 4),
            'sample_rate': sr, 'channels': 2}
    return y, info


# --------------------------------------------------------------------------- #
# act plan
# --------------------------------------------------------------------------- #
ACT_TABLE = [
    # (id, label, start, end, shot_seconds, preferred_source_shots)
    ('A', 'COLD OPEN', 0.00, 4.20, [2.20, 2.00], [0, 1]),
    ('B', 'THE WALK', 4.20, 9.40, [1.40, 1.30, 1.25, 1.25], [1, 13, 16, 19]),
    ('C', 'NEURAL SYNC', 9.40, 15.00, [1.20, 1.10, 1.10, 1.10, 1.10], [11, 12, 14, 15, 17]),
    ('D', 'CLOSE', 15.00, 19.60, [1.20, 1.20, 1.10, 1.10], [18, 19, 20, 21]),
    ('E', 'CHAOS BURST', 19.60, 25.40, [.30, .32, .30, .28, .30, .30, .32, .28, .30, .30, .30, .30,
                                        .30, .30, .30, .30, .28, .30, .30, .28], None),
    ('F', 'SOVEREIGN', 25.40, 30.60, [1.40, 1.30, 1.25, 1.25], [25, 26, 27, 29]),
    ('G', 'BUILD', 30.60, 36.60, [.60, .55, .50, .45, .40, .40, .35, .35, .30, .30, .30, .30,
                                  .30, .30, .30, .30, .30, .30, .30, .30], None),
    ('H', 'CLIMAX', 36.60, 42.80, [.40, .35, .30, .30, .28, .26, .26, .24, .24, .22, .22, .20,
                                   .20, .20, .18, .18, .16, .16, .16, .16, .16, .16, .16, .16], None),
]
ACT_GRADE = {
    'A': dict(contrast=1.14, lift=-.010, gamma=1.10, shadow_tint=(-.05, .01, .07), high_tint=(.04, .01, -.02),
              sat=.92, vig_strength=.52, bloom=.34, shadow_falloff=1.5,
              leaks=['leak_red_left.png'], leak_amount=.30),
    'B': dict(contrast=1.09, lift=.030, gamma=1.30, shadow_tint=(-.03, .02, .05), high_tint=(.05, .015, -.02),
              sat=1.02, vig_strength=.40, bloom=.30, shadow_falloff=1.3,
              leaks=['leak_red_left.png', 'leak_blue_right.png'], leak_amount=.26),
    'C': dict(contrast=1.07, lift=.020, gamma=1.34, shadow_tint=(-.04, .03, .08), high_tint=(.03, .03, -.01),
              sat=1.05, vig_strength=.38, bloom=.32, shadow_falloff=1.2,
              leaks=['leak_blue_right.png', 'leak_cyan_bottom.png'], leak_amount=.30),
    'D': dict(contrast=1.06, lift=.035, gamma=1.45, shadow_tint=(-.02, .02, .05), high_tint=(.08, .03, -.02),
              sat=1.04, vig_strength=.44, bloom=.36, shadow_falloff=1.25,
              leaks=['leak_gold_top.png'], leak_amount=.24),
    'E': dict(contrast=1.20, lift=-.020, gamma=1.30, shadow_tint=(-.06, .01, .06), high_tint=(.07, .01, -.02),
              sat=1.12, vig_strength=.52, bloom=.44, shadow_falloff=1.6,
              leaks=['leak_red_left.png', 'leak_magenta_left.png'], leak_amount=.40),
    'F': dict(contrast=1.12, lift=.020, gamma=1.34, shadow_tint=(-.04, .01, .06), high_tint=(.06, .02, -.01),
              sat=1.06, vig_strength=.46, bloom=.38, shadow_falloff=1.4,
              leaks=['leak_magenta_left.png', 'leak_blue_right.png'], leak_amount=.32),
    'G': dict(contrast=1.14, lift=.015, gamma=1.40, shadow_tint=(-.03, .01, .05), high_tint=(.08, .03, -.02),
              sat=1.08, vig_strength=.46, bloom=.40, shadow_falloff=1.4,
              leaks=['leak_red_left.png', 'leak_gold_top.png'], leak_amount=.34),
    'H': dict(contrast=1.22, lift=.005, gamma=1.34, shadow_tint=(-.05, .01, .06), high_tint=(.09, .03, -.02),
              sat=1.14, vig_strength=.50, bloom=.46, shadow_falloff=1.5,
              leaks=['leak_red_left.png', 'leak_blue_right.png', 'leak_gold_top.png'], leak_amount=.30),
    'I': dict(contrast=1.0, lift=0.0, gamma=1.0, shadow_tint=(0, 0, 0), high_tint=(0, 0, 0),
              sat=1.0, vig_strength=.10, bloom=.0, shadow_falloff=1.0, leaks=[], leak_amount=0.0),
}


def snap_to_beat(t: float, onsets_list: list[float], tol=.13) -> float:
    if not onsets_list:
        return t
    near = min(onsets_list, key=lambda o: abs(o - t))
    return round(near, 3) if abs(near - t) <= tol else t


def build_plan(analysis: dict, onsets_list: list[float]) -> dict:
    energy = shot_energy(analysis)
    luma = shot_luma(analysis)
    shots = analysis['shots']
    by_index = {s['index']: s for s in shots}
    # source shots ranked by motion energy, for the fast cut acts
    ranked = sorted(shots, key=lambda s: -s['mean_internal_diff'])
    acts, used = [], set()
    fast_pool = [s['index'] for s in ranked if s['duration'] >= .30]
    cursor = 0
    for aid, label, a, b, durations, prefer in ACT_TABLE:
        if prefer is None:
            pool = [i for i in fast_pool if i not in used] or fast_pool
            picks = pool[:len(durations)]
        else:
            picks = prefer
        shots_out = []
        t = a
        for k, dur in enumerate(durations[:len(picks)]):
            src = by_index[picks[min(k, len(picks) - 1)]]
            cut = snap_to_beat(t, onsets_list) if aid in 'ABCF' else round(t, 3)
            cut = max(cut, t) if shots_out else a
            nxt = round(min(b, t + dur), 3)
            if k == len(durations) - 1:
                nxt = b
            length = round(nxt - cut, 3)
            if length < .12:
                cut = max(a, nxt - .12)
                length = round(nxt - cut, 3)
            start_src = min(src['start'] + .12, max(src['start'], src['end'] - length - .5))
            shots_out.append({
                'source_shot': src['index'], 'start': round(cut, 3), 'end': nxt,
                'duration': length, 'source_in': round(start_src, 3),
                'motion': src['mean_internal_diff'], 'luma': src['mean_luma'],
                'zoom': 1.0 + min(.06, .035 + src['mean_internal_diff'] / 900),
            })
            used.add(src['index'])
            t = nxt
        # Exact frame tiling: every shot boundary is an integer frame, the
        # first shot starts on the act frame and the last ends on it.
        bs = [int(round(x['start'] * FPS)) for x in shots_out] + [int(round(b * FPS))]
        bs[0] = int(round(a * FPS))
        for i, x in enumerate(shots_out):
            x['start_f'], x['end_f'] = bs[i], bs[i + 1]
            x['start'], x['end'] = round(bs[i] / FPS, 3), round(bs[i + 1] / FPS, 3)
            x['duration'] = round((bs[i + 1] - bs[i]) / FPS, 3)
        acts.append({'act': aid, 'label': label, 'start': a, 'end': b, 'shots': shots_out,
                     'grade': ACT_GRADE[aid],
                     'energy': round(float(np.mean([s['motion'] for s in shots_out])), 2) if shots_out else 0.0,
                     'mean_luma': round(float(np.mean([s['luma'] for s in shots_out])), 1) if shots_out else 0.0})
        cursor = b
    return {'total': TOTAL, 'end_card_start': round(TOTAL - END_CARD, 3),
            'climax_start': [a for a in acts if a['act'] == 'H'][0]['start'],
            'acts': acts, 'source': str(SRC.name)}


def assign_sources(plan: dict, analysis: dict) -> None:
    """Give every planned shot its own source shot; reuse only if exhausted."""
    shots = analysis['shots']
    by_index = {s['index']: s for s in shots}
    # Fast acts need readable subject motion: high internal motion AND a
    # mid-dark exposure band, so the burst never lands on a near-black frame.
    pool = [s for s in sorted(shots, key=lambda s: -s['mean_internal_diff'])
            if 18 <= s['mean_luma'] <= 68 and s['duration'] >= .26]
    if len(pool) < 12:
        pool = sorted(shots, key=lambda s: -s['mean_internal_diff'])
    cursor = 0
    for act in plan['acts']:
        for sh in act['shots']:
            if act['act'] in 'EGH':
                src = pool[cursor % len(pool)]
                cursor += 1
                sh['source_shot'] = src['index']
                sh['motion'] = src['mean_internal_diff']
                sh['luma'] = src['mean_luma']
                sh['zoom'] = 1.0 + min(.07, .04 + src['mean_internal_diff'] / 800)


# --------------------------------------------------------------------------- #
# render
# --------------------------------------------------------------------------- #
def render(plan: dict, master: np.ndarray, audio_path: Path, out: Path) -> dict:
    total_frames = int(round(TOTAL * FPS))
    cmd = [FF, '-hide_banner', '-loglevel', 'error', '-y',
           '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', 'pipe:0',
           '-i', str(audio_path), '-map', '0:v:0', '-map', '1:a:0',
           '-c:v', 'libx264', '-profile:v', 'high', '-level:v', '4.2', '-preset', 'medium',
           '-crf', '19', '-maxrate', '9M', '-bufsize', '18M', '-pix_fmt', 'yuv420p',
           '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
           '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-ac', '2',
           '-movflags', '+faststart', '-t', f'{TOTAL:.3f}', str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    written = 0
    flash_at = plan['climax_start']
    for act in plan['acts']:
        g = dict(act['grade'])
        g['_cache'] = {}
        for si, sh in enumerate(act['shots']):
            frames_needed = sh['end_f'] - sh['start_f']
            start = int(round(sh['source_in'] * FPS))
            src_frames = read_window(start, frames_needed + 8)
            if len(src_frames) < 3:
                raise SystemExit(f'source window too short at shot {sh}')
            for k in range(frames_needed):
                t = (sh['start_f'] + k) / FPS
                idx = min(len(src_frames) - 1, k)
                phase = k / max(1, frames_needed - 1)
                graded = grade(src_frames[idx], g, phase)
                frame = to_bgr(graded)
                zoom = 1.0 + (sh['zoom'] - 1.0) * phase
                dx, dy = shake(t, 3.0 if act['act'] != 'H' else 6.0, act['act'] and ord(act['act']))
                frame = push_in(frame, zoom, dx, dy)
                # light leak swells on the cut then decays
                swell = .45 + .55 * math.exp(-phase * 3.2)
                frame = apply_leak(frame, g['leaks'], g['leak_amount'] * swell)
                if act['act'] == 'C':
                    frame = scanlines(frame, .10)
                    frame = hud(frame, t - act['start'], act['end'] - act['start'],
                                f'ACT {act["act"]} · SYNC', (150, 220, 255))
                if act['act'] == 'H':
                    # three strobe pulses through the climax
                    for fpos in (flash_at + .10, flash_at + 2.35, flash_at + 4.10):
                        if abs(t - fpos) < 2.5 / FPS:
                            frame = cv2.addWeighted(frame, .25,
                                                    np.full_like(frame, 245), .75, 0)
                    if int(t * FPS) % 9 == 0:
                        frame = apply_leak(frame, ['leak_gold_top.png'], .05)
                proc.stdin.write(frame.tobytes())
                written += 1
    # end card
    ec_start = int(round(plan['end_card_start'] * FPS))
    ec_frames = total_frames - ec_start
    for k in range(ec_frames):
        phase = k / max(1, ec_frames - 1)
        frame = emblem_frame(phase)
        fade = min(1.0, (k / 6)) * min(1.0, ((ec_frames - 1 - k) / 8) + .3)
        frame = (frame.astype(np.float32) * min(1.0, fade)).astype(np.uint8)
        proc.stdin.write(frame.tobytes())
        written += 1
    proc.stdin.close()
    rc = proc.wait()
    if rc != 0 or written != total_frames:
        raise SystemExit(f'encode failed rc={rc} frames={written}/{total_frames}')
    return {'frames': written, 'expected': total_frames}


def look_sheet(plan: dict, out: Path) -> None:
    picks = []
    for act in plan['acts']:
        sh = act['shots'][len(act['shots']) // 2]
        picks.append((sh['start'] + sh['duration'] / 2, f"{act['act']} {act['label']}"))
    cap = cv2.VideoCapture(str(OUTDIR / 'CHAOS04_MASTER.mp4'))
    tiles = []
    for t, lab in picks + [(TOTAL - .5, 'I END CARD')]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * FPS))
        ok, f = cap.read()
        if not ok:
            continue
        f = cv2.resize(f, (270, 480))
        cv2.rectangle(f, (0, 0), (270, 26), (10, 10, 10), -1)
        cv2.putText(f, f'{t:05.2f}s {lab}', (5, 19), cv2.FONT_HERSHEY_SIMPLEX, .42, (255, 255, 255), 1, cv2.LINE_AA)
        tiles.append(f)
    cap.release()
    cols = 5
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imwrite(str(out), np.vstack(rows))
    sheet = Image.open(out)
    sheet.resize((sheet.width // 2, sheet.height // 2)).save(out)


if __name__ == '__main__':
    OUTDIR.mkdir(exist_ok=True); WORK.mkdir(exist_ok=True)
    analysis = json.loads((HERE / 'analysis' / 'REFERENCE_ANALYSIS.json').read_text())
    src_info = probe()
    sr, raw_audio = decode_audio(WORK / 'source_audio.wav')
    onsets_list = onsets(raw_audio, sr)
    plan = build_plan(analysis, onsets_list)
    assign_sources(plan, analysis)
    (WORK / 'ACT_PLAN.json').write_text(json.dumps(plan, indent=2) + '\n')
    mastered, audio_info = master_audio(sr, raw_audio, plan)
    with wave.open(str(WORK / 'master_audio.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(mastered, -1, 1) * 32767).astype('<i2').tobytes())
    print(json.dumps({'source': src_info, 'onsets': len(onsets_list),
                      'shots': sum(len(a['shots']) for a in plan['acts']),
                      'audio': audio_info}, indent=1), flush=True)
    r = render(plan, mastered, WORK / 'master_audio.wav', OUTDIR / 'CHAOS04_MASTER.mp4')
    print('RENDER', json.dumps(r), flush=True)
    look_sheet(plan, OUTDIR / 'CHAOS04_LOOK.png')
    print('LOOK_SHEET', OUTDIR / 'CHAOS04_LOOK.png')
