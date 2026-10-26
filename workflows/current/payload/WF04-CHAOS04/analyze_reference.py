#!/usr/bin/env python3
"""WF-05 reference analysis: real decode of the supplied footage.

Outputs (all derived from actual pixels/samples, nothing assumed):
  analysis/frames/f_XX.XX.png   representative frames per shot
  analysis/sheet_*.png          contact sheets for visual review
  analysis/audio.wav            48 kHz mono decode of the reference audio
  ANALYSIS.json                 shot boundaries, motion/brightness/audio stats
"""
from __future__ import annotations
import json, subprocess, wave
from pathlib import Path
import numpy as np
import cv2
import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
SRC = HERE / 'media' / 'reference_source.mp4'
OUT = HERE / 'analysis'
FR = OUT / 'frames'
FF = imageio_ffmpeg.get_ffmpeg_exe()
SW, SH = 216, 384          # analysis resolution (9:16)
CUT_THRESHOLD = 26.0       # mean abs luma diff on 216x384 that reads as a hard cut


def decode_small():
    cap = cv2.VideoCapture(str(SRC))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    small = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(f, (SW, SH), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        small.append(g)
        if len(small) % 200 == 0:
            print(f'  decoded {len(small)}', flush=True)
    cap.release()
    return small, fps, n


def shots_from_diffs(small):
    diffs = [0.0] + [float(np.abs(small[i].astype(np.int16) - small[i - 1].astype(np.int16)).mean())
                     for i in range(1, len(small))]
    cuts = []
    for i, d in enumerate(diffs):
        if i and d >= CUT_THRESHOLD and (not cuts or i - cuts[-1] >= 8):
            cuts.append(i)
    bounds = [0] + cuts + [len(small)]
    shots = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        seg = small[a:b]
        inner = diffs[a + 1:b]
        shots.append({
            'index': len(shots), 'start_frame': a, 'end_frame': b,
            'frames': b - a,
            'mean_internal_diff': round(float(np.mean(inner)) if inner else 0.0, 2),
            'max_internal_diff': round(float(np.max(inner)) if inner else 0.0, 2),
            'entry_diff': round(diffs[a], 2) if a else 0.0,
            'mean_luma': round(float(np.mean([g.mean() for g in seg])), 1),
            'brightness_drift': round(float(np.mean([g.mean() for g in seg[-5:]]) -
                                            np.mean([g.mean() for g in seg[:5]])), 1),
        })
    return shots, diffs


def full_frame(t: float) -> np.ndarray:
    out = subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-ss', f'{t:.3f}', '-i', str(SRC),
                          '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'],
                         capture_output=True)
    return np.frombuffer(out.stdout, np.uint8).reshape(1280, 720, 3).copy()


def label(img, text, scale=0.52):
    h, w = img.shape[:2]
    bar = np.zeros((30, w, 3), np.uint8)
    bar[:] = 18
    cv2.putText(bar, text, (6, 21), cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 1, cv2.LINE_AA)
    return np.vstack([bar, img])


def contact_sheet(frames, cols, out_path, thumb_w=300):
    rows = []
    th = int(thumb_w * 1280 / 720) + 30
    for i in range(0, len(frames), cols):
        chunk = frames[i:i + cols]
        cells = [label(f, t, 0.5) for f, t in chunk]
        while len(cells) < cols:
            cells.append(np.zeros((th, thumb_w, 3), np.uint8))
        rows.append(np.hstack([cv2.resize(c, (thumb_w, th)) for c in cells]))
    cv2.imwrite(str(out_path), np.vstack(rows))


def audio_stats():
    wav = OUT / 'audio.wav'
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(SRC), '-ac', '1',
                    '-ar', '48000', '-c:a', 'pcm_s16le', str(wav)], check=True)
    with wave.open(str(wav), 'rb') as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32768
    win = int(0.05 * sr)
    env = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, 'same'))
    thr = np.percentile(env, 60) * 1.6
    active = env > thr
    # crude speech/silence segmentation on 50 ms envelope
    segs, cur = [], None
    step = win
    for i in range(0, len(env) - step, step):
        on = bool(active[i:i + step].mean() > 0.5)
        if on and cur is None:
            cur = i / sr
        elif not on and cur is not None:
            if i / sr - cur > 0.18:
                segs.append([round(cur, 2), round(i / sr, 2)])
            cur = None
    if cur is not None:
        segs.append([round(cur, 2), round(len(env) / sr, 2)])
    peak = float(np.max(np.abs(x)))
    rms = float(np.sqrt(np.mean(x ** 2)))
    spec = np.abs(np.fft.rfft(x[:sr * 4]))
    freqs = np.fft.rfftfreq(sr * 4, 1 / sr)
    centroid = float((spec * freqs).sum() / (spec.sum() + 1e-9))
    return {'sample_rate': sr, 'duration': round(len(x) / sr, 2),
            'peak_dbfs': round(20 * np.log10(peak + 1e-9), 2),
            'rms_dbfs': round(20 * np.log10(rms + 1e-9), 2),
            'spectral_centroid_hz': round(centroid, 1),
            'voiced_segments': segs, 'voiced_seconds': round(sum(b - a for a, b in segs), 2),
            'silence_seconds': round(len(x) / sr - sum(b - a for a, b in segs), 2)}


if __name__ == '__main__':
    FR.mkdir(parents=True, exist_ok=True)
    print('decoding …', flush=True)
    small, fps, n = decode_small()
    print(f'frames={len(small)} fps={fps} reported={n}', flush=True)
    shots, diffs = shots_from_diffs(small)
    for s in shots:
        s['start'] = round(s['start_frame'] / fps, 3)
        s['end'] = round(s['end_frame'] / fps, 3)
        s['duration'] = round(s['frames'] / fps, 3)

    imgs = []
    seen = set()
    for s in shots:
        mid = (s['start'] + s['end']) / 2
        times = sorted({round(s['start'] + 0.35, 2), round(mid, 2), round(s['end'] - 0.35, 2)})
        if s['end'] - s['start'] < 0.7:
            times = [round(mid, 2)]
        for t in times:
            if t in seen:
                continue
            seen.add(t)
            img = full_frame(t)
            cv2.imwrite(str(FR / f'f_{t:06.2f}.png'), img)
            imgs.append((img, f'{t:.2f}s #{s["index"]}'))
    for i in range(0, len(imgs), 9):
        contact_sheet(imgs[i:i + 9], 3, OUT / f'sheet_{i // 9 + 1}.png')

    a = audio_stats()
    data = {
        'source': {'file': 'media/reference_source.mp4', 'bytes': SRC.stat().st_size,
                   'decoded_frames': len(small), 'fps': fps,
                   'duration': round(len(small) / fps, 3),
                   'container_note': 'HEVC Main / hvc1, 720x1280, bt709, 30 fps; AAC-LC 44.1 kHz stereo 127 kb/s'},
        'cut_threshold_mean_abs_luma_diff': CUT_THRESHOLD,
        'shot_count': len(shots),
        'shots': shots,
        'audio': a,
        'diff_percentiles': {'p50': round(float(np.percentile(diffs[1:], 50)), 2),
                             'p90': round(float(np.percentile(diffs[1:], 90)), 2),
                             'p99': round(float(np.percentile(diffs[1:], 99)), 2),
                             'max': round(float(np.max(diffs)), 2)},
    }
    (OUT / 'ANALYSIS.json').write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'shots': len(shots), 'audio': {k: a[k] for k in ('duration', 'rms_dbfs', 'voiced_seconds', 'silence_seconds')},
                      'durations': [s['duration'] for s in shots]}, indent=1))
