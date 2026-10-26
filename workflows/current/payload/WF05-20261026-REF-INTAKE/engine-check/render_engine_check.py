#!/usr/bin/env python3
"""WF-05 engine check — proves the decode → depth-motion → type → encode → verify
path works inside THIS sandbox, using the repository's real approved compositor
(src/motion.py camera/cut/tilt_title + src/render_project.py Compositor.overlay).

Honest scope:
  * Plates are procedurally generated "footage" (real temporal motion, H.264 on
    disk, decoded back through OpenCV) — they are NOT the user's reference video
    and NOT a topic deliverable.
  * Typography/format/policy come from data/approved-profile.json.
  * No project-level approval flags are claimed; this is not a delivery master.
"""
from __future__ import annotations
import json, math, subprocess, sys, hashlib, time
from pathlib import Path
import numpy as np
import cv2
import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
STYLE = REPO / 'styles' / 'premium-motion-editing'
sys.path.insert(0, str(STYLE / 'src'))
from motion import camera, cut                      # noqa: E402  (approved engine)
from render_project import Compositor, W, H, FPS    # noqa: E402

FF = imageio_ffmpeg.get_ffmpeg_exe()
PW, PH = 720, 1280            # engine-native plate size (motion.py W,H)
PLATE_FRAMES = 90             # 3.0 s per plate, <=300-frame adapter limit
OUT = REPO / 'demo' / 'engine-check' / 'WF05_ENGINE_CHECK_demo.mp4'
AUDIO = HERE / 'engine_check_mix.wav'


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def md5(p: Path) -> str:
    h = hashlib.md5()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# 1. procedural plate "footage" (independent subject motion, not a still)
# --------------------------------------------------------------------------- #
def base_plate(p: float, seed: int) -> np.ndarray:
    """Pale editorial 'paper' plate matching the accepted V5 clean direction.

    Light ground so the approved dark-ink integrated type keeps real contrast;
    light bands and the key glow drift over time (background plane motion).
    """
    yy = np.linspace(0, 1, PH, dtype=np.float32)[:, None, None]
    xx = np.linspace(0, 1, PW, dtype=np.float32)[None, :, None]
    top = np.array([240, 243, 247], np.float32)      # BGR warm paper
    bot = np.array([214, 219, 228], np.float32)
    img = np.broadcast_to(top + (bot - top) * yy, (PH, PW, 3)).astype(np.float32)
    band = 0.5 + 0.5 * np.sin(6.28318 * (yy * 0.75 + 0.11 * p) + seed)
    img *= (1.0 - 0.055 * band ** 2)
    cx = 0.26 + 0.50 * (0.5 - 0.5 * math.cos(math.pi * p))
    rad = np.sqrt((xx - cx) ** 2 + ((yy - 0.45) * 0.66) ** 2)
    glow = np.clip(1.0 - rad / 0.62, 0, 1) ** 2.0
    img += glow * np.array([10, 6, 18], np.float32)          # cool key light
    vig = np.clip(1.0 - 0.9 * ((xx - .5) ** 2 + (yy - .5) ** 2), 0, 1) ** .5
    img *= (0.90 + 0.10 * vig)
    return img


def subject(p: float, kind: int):
    """Ink geometry with genuine temporal motion, returned as (colour, alpha)."""
    colour = np.zeros((PH, PW, 3), np.float32)
    alpha = np.zeros((PH, PW, 1), np.float32)
    cy_off = {1: 0.60, 2: 0.30, 3: 0.58}[kind]          # keep clear of the type
    cx = PW * (0.5 + 0.17 * math.sin(math.pi * 1.05 * p + kind))
    cy = PH * (cy_off + 0.055 * math.cos(math.pi * 1.5 * p + kind * 0.7))
    ink = np.array([150, 96, 44], np.float32)           # deep plum ink (BGR)
    violet = np.array([188, 138, 96], np.float32)
    if kind == 1:
        r = int(92 + 22 * math.sin(2 * math.pi * p))
        cv2.circle(alpha, (int(cx), int(cy)), r, 0.85, 5, cv2.LINE_AA)
        cv2.circle(colour, (int(cx), int(cy)), r, ink.tolist(), 5, cv2.LINE_AA)
        cv2.ellipse(alpha, (int(cx), int(cy)), (int(r * 1.6), int(r * 0.6)),
                    210 * p + 20, 0, 360, 0.55, 2, cv2.LINE_AA)
        cv2.ellipse(colour, (int(cx), int(cy)), (int(r * 1.6), int(r * 0.6)),
                    210 * p + 20, 0, 360, violet.tolist(), 2, cv2.LINE_AA)
        cv2.circle(alpha, (int(cx), int(cy)), 15, 1.0, -1, cv2.LINE_AA)
        cv2.circle(colour, (int(cx), int(cy)), 15, ink.tolist(), -1, cv2.LINE_AA)
    elif kind == 2:
        for i, off in enumerate((-.16, -.03, .10, .23)):
            x0 = int(PW * (0.10 + off + 0.10 * math.sin(2 * math.pi * (p + i * .16))))
            y0 = int(PH * (0.20 + i * 0.075))
            w = int(230 + 80 * math.sin(3 * p + i))
            cv2.rectangle(alpha, (x0, y0), (x0 + w, y0 + 13), 0.9, -1)
            cv2.rectangle(colour, (x0, y0), (x0 + w, y0 + 13),
                          (188 - i * 8, 138 - i * 10, 96 - i * 12), -1)
        cv2.circle(alpha, (int(PW * (0.20 + 0.58 * p)), int(PH * .105)), 10, 1.0, -1, cv2.LINE_AA)
        cv2.circle(colour, (int(PW * (0.20 + 0.58 * p)), int(PH * .105)), 10, ink.tolist(), -1, cv2.LINE_AA)
    else:
        pts = np.array([[int(cx), int(cy - 130)], [int(cx + 112), int(cy + 78)],
                        [int(cx - 112), int(cy + 78)]], np.int32)
        cv2.polylines(alpha, [pts], True, 0.85, 3, cv2.LINE_AA)
        cv2.polylines(colour, [pts], True, ink.tolist(), 3, cv2.LINE_AA)
        cv2.circle(alpha, (int(cx), int(cy + 6)), 19, 1.0, -1, cv2.LINE_AA)
        cv2.circle(colour, (int(cx), int(cy + 6)), 19, ink.tolist(), -1, cv2.LINE_AA)
    colour = cv2.GaussianBlur(colour, (0, 0), 9) * 0.30 + colour * 0.85
    soft_a = cv2.GaussianBlur(alpha[..., 0], (0, 0), 5)[..., None]
    alpha = np.clip(soft_a * 0.55 + alpha, 0, 1)
    return colour, alpha


def build_plate(kind: int, out: Path) -> None:
    rng = np.random.default_rng(1000 + kind)
    cmd = [FF, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo',
           '-pix_fmt', 'rgb24', '-s', f'{PW}x{PH}', '-r', str(FPS), '-i', 'pipe:0',
           '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p', str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(PLATE_FRAMES):
        p = n / (PLATE_FRAMES - 1)
        colour, alpha = subject(p, kind)
        img = base_plate(p, kind)
        img = img * (1.0 - 0.80 * alpha) + colour * 0.80 * alpha
        grain = rng.normal(0, 2.6, (PH, PW, 1)).astype(np.float32)
        img = np.clip(img + grain, 0, 255).astype(np.uint8)
        proc.stdin.write(cv2.cvtColor(img, cv2.COLOR_BGR2RGB).tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit(f'plate encode failed: {out}')


# --------------------------------------------------------------------------- #
# 2. approved policy typography timeline (integrated headings, no lower pills)
# --------------------------------------------------------------------------- #
PROJECT = {
    'style_id': 'premium-motion-editing',
    'project_id': 'ENGINE-CHECK-WF05',
    'typography': {'subtitle_mode': 'off', 'plain_subtitles_requested': False,
                   'caption_pills': False, 'word_highlighting': False},
    'font_dir': None,
}
TIMELINE = {
    'fps': FPS,
    'titles': [
        {'start': 0.20, 'end': 2.55, 'title': 'ENGINE\nCHECK', 'kicker': 'WF-05 · PREMIUM MOTION EDITING',
         'sub': 'real temporal motion · 2.5D depth', 'size': 118, 'position': 'top'},
        {'start': 2.75, 'end': 4.35, 'title': 'NOT A\nSLIDESHOW', 'kicker': 'DEPTH PUSH · DIAGONAL WHIP',
         'sub': '', 'size': 104, 'position': 'bottom'},
        {'start': 4.55, 'end': 5.95, 'title': 'DELIVERY\nPATH OK', 'kicker': '1080×1920 · 30 FPS · H.264',
         'sub': 'AAC 48 kHz · faststart', 'size': 112, 'position': 'top'},
    ],
    'captions': [],
}
SHOTS = [
    {'name': 'plate-a', 'start': 0.0, 'end': 2.0, 'path': 'plate_a.mp4', 'motion_kind': 'independent_layers',
     'depth_rect': [.10, .22, .90, .80], 'camera': {'z_strength': .050, 'direction': 1,
                                                    'vertical_drift': -8, 'roll_degrees': .7},
     'transition': 'depth_push'},
    {'name': 'plate-b', 'start': 2.0, 'end': 4.2, 'path': 'plate_b.mp4', 'motion_kind': 'independent_layers',
     'depth_rect': [.08, .26, .92, .78], 'camera': {'z_strength': .045, 'direction': -1,
                                                    'vertical_drift': 6, 'roll_degrees': .5},
     'transition': 'diagonal_whip'},
    {'name': 'plate-c', 'start': 4.2, 'end': 6.0, 'path': 'plate_c.mp4', 'motion_kind': 'independent_layers',
     'depth_rect': [.06, .20, .94, .82], 'camera': {'z_strength': .055, 'direction': 1,
                                                    'vertical_drift': -6, 'roll_degrees': .6},
     'transition': 'feathered_cut'},
]
DURATION = SHOTS[-1]['end']


# --------------------------------------------------------------------------- #
# 3. audio: restrained bed + cut accents (no narration, nothing faked)
# --------------------------------------------------------------------------- #
def build_audio(path: Path) -> dict:
    from scipy.signal import butter, sosfilt
    sr = 48000
    n = int(DURATION * sr)
    t = np.arange(n) / sr
    rng = np.random.default_rng(7)
    bed = (0.30 * np.sin(2 * np.pi * 55 * t) + 0.18 * np.sin(2 * np.pi * 82.5 * t + 1.1)
           + 0.10 * np.sin(2 * np.pi * 110 * t + 2.3))
    bed *= (0.55 + 0.45 * np.sin(2 * np.pi * 0.11 * t)) * 0.06
    noise = sosfilt(butter(2, 420, 'low', fs=sr, output='sos'), rng.normal(0, 1, n)) * 0.035
    mix = bed + noise
    for at, dur, gain, f0, f1 in ((2.0, .42, .30, 300, 2600), (4.2, .38, .26, 380, 3200)):
        i0, m = int(at * sr), int(dur * sr)
        env = np.sin(np.linspace(0, np.pi, m)) ** 2.2
        sweep = np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, m)) / sr)
        burst = sosfilt(butter(2, [220, 5200], 'band', fs=sr, output='sos'), rng.normal(0, 1, m))
        mix[i0:i0 + m] += (burst * .8 + sweep * .35) * env * gain
    for at, gain in ((0.12, .22), (4.55, .14)):
        i0, m = int(at * sr), int(.30 * sr)
        env = np.exp(-np.linspace(0, 9, m))
        mix[i0:i0 + m] += np.sin(2 * np.pi * 58 * np.arange(m) / sr) * env * gain
    fade = int(.25 * sr)
    mix[:fade] *= np.linspace(0, 1, fade)
    mix[-fade:] *= np.linspace(1, 0, fade)
    peak = float(np.max(np.abs(mix))) or 1.0
    mix = mix / peak * 0.72
    stereo = np.repeat(mix[:, None], 2, axis=1)
    pcm = (np.clip(stereo, -1, 1) * 32767).astype('<i2')
    import wave
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
    return {'sample_rate': sr, 'channels': 2, 'peak_dbfs': round(20 * math.log10(0.72), 2),
            'accents': [2.0, 4.2, 4.55], 'narration': False}


# --------------------------------------------------------------------------- #
# 4. composite through the approved engine, encode with the approved settings
# --------------------------------------------------------------------------- #
def render() -> dict:
    media = HERE / 'plates'; media.mkdir(exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for kind, shot in zip((1, 2, 3), SHOTS):
        build_plate(kind, media / shot['path'])
    audio_info = build_audio(AUDIO)

    comp = Compositor(PROJECT, TIMELINE, HERE)
    expected = round(DURATION * FPS)
    cmd = [FF, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
           '-s', f'{W}x{H}', '-r', str(FPS), '-i', 'pipe:0', '-i', str(AUDIO),
           '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'libx264', '-profile:v', 'high', '-level:v', '4.1',
           '-crf', '18', '-maxrate', '7M', '-bufsize', '14M', '-preset', 'fast', '-threads', '2',
           '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
           '-movflags', '+faststart', '-t', str(DURATION), str(OUT)]
    started = time.monotonic()
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    prev = None; done = 0
    for si, shot in enumerate(SHOTS):
        cap = cv2.VideoCapture(str(media / shot['path']))
        frames = []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            frames.append(f)
        cap.release()
        if len(frames) < 2:
            raise SystemExit(f'plate not decodable: {shot["path"]}')
        print(f'COMPOSITE {si + 1}/{len(SHOTS)} {shot["name"]} decoded={len(frames)} frames', flush=True)
        for n in range(round(shot['start'] * FPS), round(shot['end'] * FPS)):
            at = n / FPS
            q = (at - shot['start']) / (shot['end'] - shot['start'])
            f = comp.sample(frames, q, shot)
            f = cut(f, prev, at - shot['start'], shot['transition'], shot['camera']['direction'])
            full = cv2.resize(f, (W, H), interpolation=cv2.INTER_CUBIC)
            proc.stdin.write(comp.overlay(full, at, shot).tobytes())
            done += 1
        prev = comp.sample(frames, 1.0, shot)
        del frames
    proc.stdin.close()
    if proc.wait() != 0 or done != expected:
        raise SystemExit(f'encode failed rc={proc.returncode} frames={done}/{expected}')
    return {'frames': done, 'expected': expected, 'elapsed_seconds': round(time.monotonic() - started, 2),
            'layout_boxes': comp.layout_receipts, 'audio': audio_info}


def probe() -> dict:
    out = subprocess.run([FF, '-hide_banner', '-i', str(OUT)], capture_output=True, text=True).stderr
    info = {'ffmpeg_probe_excerpt': [ln.strip() for ln in out.splitlines()
                                     if 'Stream' in ln or 'Duration' in ln]}
    cap = cv2.VideoCapture(str(OUT))
    frames = 0
    while True:
        ok, _ = cap.read()
        if not ok:
            break
        frames += 1
    info['decoded_frames'] = frames
    info['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    info['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    info['fps'] = round(float(cap.get(cv2.CAP_PROP_FPS)), 3)
    cap.release()
    info['full_decode_ok'] = frames == round(DURATION * FPS)
    return info


if __name__ == '__main__':
    r = render()
    p = probe()
    receipt = {
        'schema_version': 1,
        'artifact': 'ENGINE CHECK — capability proof, not a topic deliverable',
        'style_id': 'premium-motion-editing',
        'policy_id': 'wf05-clean-editorial-20261015',
        'engine_sources': {'render_project.py': sha256(STYLE / 'src/render_project.py'),
                           'motion.py': sha256(STYLE / 'src/motion.py')},
        'typography': {'mode': 'integrated_headings', 'subtitle_mode': 'off',
                       'caption_pills': False, 'word_highlighting': False},
        'plates': [{'file': s['path'], 'sha256': sha256(HERE / 'plates' / s['path']),
                    'frames': PLATE_FRAMES, 'size': f'{PW}x{PH}'} for s in SHOTS],
        'render': r, 'verify': p,
        'master': {'path': str(OUT.relative_to(REPO)), 'size': OUT.stat().st_size,
                   'md5': md5(OUT), 'sha256': sha256(OUT), 'duration_seconds': DURATION},
        'claim': 'Decode → approved depth motion/type → H.264 encode → decode verification all executed in this sandbox. '
                 'Reference footage was NOT used and no reference-content claim is made.',
    }
    (HERE / 'ENGINE_CHECK_RECEIPT.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'frames': p['decoded_frames'], 'size_bytes': OUT.stat().st_size,
                      'md5': receipt['master']['md5'], 'decode_ok': p['full_decode_ok']}, indent=2))
