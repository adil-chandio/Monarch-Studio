#!/usr/bin/env python3
"""Mastered 48kHz stereo audio engine for WF-04 · Chaos Video 1."""

from __future__ import annotations

import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, filtfilt

ROOT = Path(__file__).resolve().parents[4]
PAYLOAD = ROOT / "workflows" / "current" / "payload"
REF_DIR = ROOT / ".runtime" / "ref_video"

FPS = 30
TOTAL_FRAMES = 636


def build_master_audio() -> tuple[Path, dict[str, Any]]:
    sr, ref_wav = wavfile.read(REF_DIR / "ref_audio.wav")
    ref_f = ref_wav.astype(np.float32) / 32768.0
    if ref_f.ndim == 1:
        ref_f = np.stack([ref_f, ref_f], axis=1)

    target_samples = int(round((TOTAL_FRAMES / float(FPS)) * sr))
    if len(ref_f) < target_samples:
        pad = np.zeros((target_samples - len(ref_f), 2), dtype=np.float32)
        base = np.vstack([ref_f, pad])
    else:
        base = ref_f[:target_samples].copy()

    sfx_l = np.zeros(target_samples, dtype=np.float32)
    sfx_r = np.zeros(target_samples, dtype=np.float32)

    def add_sub_hit(time_s: float, dur_s: float = 0.38, freq0: float = 95.0, freq1: float = 34.0, amp: float = 0.28) -> None:
        i0 = int(time_s * sr)
        n = int(dur_s * sr)
        if i0 >= target_samples:
            return
        i1 = min(target_samples, i0 + n)
        lt = np.arange(i1 - i0, dtype=np.float32) / float(sr)
        inst_f = freq0 * ((freq1 / freq0) ** (lt / dur_s))
        phase = 2.0 * np.pi * np.cumsum(inst_f) / float(sr)
        env = np.exp(-lt * 8.5) * np.minimum(1.0, lt / 0.006)
        wave = np.tanh(np.sin(phase) * 1.6) * env * amp
        sfx_l[i0:i1] += wave
        sfx_r[i0:i1] += wave

    def add_cyber_pulse(time_s: float, dur_s: float = 0.09, freq: float = 1480.0, pan: float = 0.0, amp: float = 0.10) -> None:
        i0 = int(time_s * sr)
        n = int(dur_s * sr)
        if i0 >= target_samples:
            return
        i1 = min(target_samples, i0 + n)
        lt = np.arange(i1 - i0, dtype=np.float32) / float(sr)
        env = np.exp(-lt * 32.0) * np.minimum(1.0, lt / 0.002)
        sig = (np.sin(2 * np.pi * freq * lt) + 0.5 * np.sin(2 * np.pi * (freq * 1.5) * lt)) * env * amp
        sfx_l[i0:i1] += sig * math.sqrt(0.5 * (1.0 - pan))
        sfx_r[i0:i1] += sig * math.sqrt(0.5 * (1.0 + pan))

    def add_whoosh(time_s: float, dur_s: float = 0.32, pan_start: float = -0.7, pan_end: float = 0.7, amp: float = 0.14) -> None:
        i0 = int(time_s * sr)
        n = int(dur_s * sr)
        if i0 >= target_samples:
            return
        i1 = min(target_samples, i0 + n)
        m = i1 - i0
        lt = np.linspace(0.0, 1.0, m, dtype=np.float32)
        rng = np.random.default_rng(int(time_s * 1000))
        noise = rng.standard_normal(m).astype(np.float32)
        b, a = butter(2, [350 / (sr * 0.5), 3600 / (sr * 0.5)], btype="band")
        shaped = filtfilt(b, a, noise).astype(np.float32)
        env = np.maximum(0.0, np.sin(np.pi * lt)) ** 1.6
        pan = pan_start + (pan_end - pan_start) * lt
        sfx_l[i0:i1] += shaped * env * amp * np.sqrt(0.5 * (1.0 - pan))
        sfx_r[i0:i1] += shaped * env * amp * np.sqrt(0.5 * (1.0 + pan))

    for st, pan in [(0.30, -0.4), (0.40, 0.5), (0.93, -0.5), (1.50, 0.4), (2.10, -0.4), (2.73, 0.4), (3.23, -0.3), (3.50, 0.0)]:
        add_cyber_pulse(st, dur_s=0.08, freq=1850.0, pan=pan, amp=0.09)

    add_sub_hit(3.72, dur_s=0.25, freq0=68.0, freq1=32.0, amp=0.20)
    add_sub_hit(4.18, dur_s=0.25, freq0=72.0, freq1=34.0, amp=0.24)
    r0, r1 = int(3.80 * sr), int(4.78 * sr)
    rt = np.linspace(0.0, 1.0, r1 - r0, dtype=np.float32)
    rfreq = 180.0 * (8.5 ** (rt ** 1.7))
    rphase = 2.0 * np.pi * np.cumsum(rfreq) / float(sr)
    riser = np.sin(rphase) * (rt ** 2.2) * 0.14
    sfx_l[r0:r1] += riser
    sfx_r[r0:r1] += riser
    add_cyber_pulse(4.68, dur_s=0.045, freq=2640.0, pan=-0.3, amp=0.12)
    add_cyber_pulse(4.74, dur_s=0.055, freq=3520.0, pan=0.3, amp=0.14)

    add_sub_hit(4.80, dur_s=0.48, freq0=110.0, freq1=32.0, amp=0.34)
    for gt, pan in [(5.33, -0.5), (6.73, 0.5), (6.93, -0.5), (7.43, 0.0), (7.90, 0.3), (8.13, -0.4), (8.37, 0.4), (8.73, 0.0)]:
        add_cyber_pulse(gt, dur_s=0.11, freq=1320.0, pan=pan, amp=0.11)
        add_sub_hit(gt, dur_s=0.26, freq0=88.0, freq1=36.0, amp=0.18)

    add_whoosh(9.40, dur_s=0.24, pan_start=-0.8, pan_end=0.6, amp=0.16)
    add_whoosh(9.98, dur_s=0.22, pan_start=0.7, pan_end=-0.7, amp=0.16)
    add_whoosh(10.48, dur_s=0.22, pan_start=-0.6, pan_end=0.6, amp=0.15)
    for idx, fno in enumerate(range(327, 368, 4)):
        st = fno / float(FPS)
        pan = -0.55 if (idx % 2 == 0) else 0.55
        add_cyber_pulse(st, dur_s=0.06, freq=1600.0 + idx * 90.0, pan=pan, amp=0.08)

    add_sub_hit(12.30, dur_s=0.45, freq0=105.0, freq1=33.0, amp=0.32)
    add_cyber_pulse(12.30, dur_s=0.22, freq=2200.0, pan=0.0, amp=0.13)
    add_sub_hit(12.80, dur_s=0.35, freq0=92.0, freq1=35.0, amp=0.24)
    add_whoosh(13.68, dur_s=0.36, pan_start=0.85, pan_end=-0.85, amp=0.20)
    add_cyber_pulse(14.33, dur_s=0.16, freq=1960.0, pan=0.0, amp=0.14)

    s17 = int(17.45 * sr)
    base[s17:] *= 0.68
    add_sub_hit(17.53, dur_s=0.65, freq0=98.0, freq1=31.0, amp=0.36)
    add_whoosh(17.50, dur_s=0.35, pan_start=-0.8, pan_end=0.8, amp=0.18)
    add_cyber_pulse(17.55, dur_s=0.25, freq=1760.0, pan=0.0, amp=0.12)

    t0, t1 = int(18.10 * sr), int(21.05 * sr)
    ct = np.linspace(0.0, 1.0, t1 - t0, dtype=np.float32)
    c_env = np.maximum(0.0, np.sin(np.pi * np.minimum(1.0, ct * 4.0))) * np.exp(-ct * 2.8)
    dur_chord = (t1 - t0) / float(sr)
    chord_l = (
        0.50 * np.sin(2 * np.pi * 55.0 * ct * dur_chord)
        + 0.30 * np.sin(2 * np.pi * 110.0 * ct * dur_chord)
        + 0.20 * np.sin(2 * np.pi * 164.81 * ct * dur_chord)
    ) * c_env * 0.14
    chord_r = (
        0.50 * np.sin(2 * np.pi * 55.0 * ct * dur_chord)
        + 0.30 * np.sin(2 * np.pi * 110.3 * ct * dur_chord)
        + 0.20 * np.sin(2 * np.pi * 220.0 * ct * dur_chord)
    ) * c_env * 0.14
    sfx_l[t0:t1] += chord_l
    sfx_r[t0:t1] += chord_r

    d0, d1 = int(16.40 * sr), int(17.55 * sr)
    dt = np.linspace(0.0, 1.0, d1 - d0, dtype=np.float32)
    drone = np.sin(2 * np.pi * 55.0 * dt * (d1 - d0) / float(sr)) * 0.045
    sfx_l[d0:d1] += drone
    sfx_r[d0:d1] += drone

    mix = np.stack([base[:, 0] + sfx_l, base[:, 1] + sfx_r], axis=1)
    mix = np.tanh(mix * 1.18) / np.tanh(1.18)
    peak = float(np.max(np.abs(mix)))
    target_linear_peak = 10.0 ** (-1.5 / 20.0)
    if peak > 0:
        mix = mix * (target_linear_peak / peak)

    out_wav = PAYLOAD / "master_audio_48k.wav"
    tmp_wav = PAYLOAD / "master_audio_44k.wav"
    wavfile.write(tmp_wav, sr, (mix * 32767.0).astype(np.int16))
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(tmp_wav), "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(out_wav), "-loglevel", "warning"],
        check=True,
    )
    tmp_wav.unlink(missing_ok=True)

    rms = float(np.sqrt(np.mean(mix ** 2)))
    tp_db = 20.0 * math.log10(max(1e-6, float(np.max(np.abs(mix)))))
    lufs_est = 20.0 * math.log10(max(1e-6, rms)) - 0.691
    return out_wav, {"rms": round(rms, 4), "true_peak_dbfs": round(tp_db, 2), "lufs_approx": round(lufs_est, 2)}
