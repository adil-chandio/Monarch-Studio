#!/usr/bin/env python3
"""Mastered 48kHz stereo audio engine for WF-04 · Chaos Video 2 (44.53 s cut).

Same recipe as `audio_engine.py` (reference track as the bed + scheduled sub hits,
chords and risers), retimed to the 1336-frame timeline and the act structure of the
reference video (`VID_20261013_050529_146.mp4`, 44.55 s):

    A cold open 0.0-2.2s | B throne 2.2-8.0s | C chaos 8.0-14.0s | D triad 14.0-19.4s
    E burst 19.4-26.0s | F stance 26.0-33.0s | G finale build 33.0-40.5s
    H crown finale 40.5-44.53s

The reference WAV is a materialized input kept outside the workspace snapshot
(`/tmp/monarch-stage/ref_video/ref_audio.wav`, see docs/STORAGE_AND_MATERIALIZATION.md).
"""

from __future__ import annotations

import math
import os
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from scipy.io import wavfile


def _repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "styles").is_dir() and (candidate / "workflows").is_dir():
            return candidate
    raise RuntimeError("repository root not found above " + str(Path(__file__).resolve()))


ROOT = _repo_root()
PAYLOAD = ROOT / "styles" / "monarch-face-chaos"


def _ffmpeg_bin() -> str:
    """ffmpeg is not on PATH in this sandbox; imageio-ffmpeg ships a static build."""
    import shutil

    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("ffmpeg not found — run: bash tools/bootstrap_env.sh") from exc


FFMPEG = _ffmpeg_bin()

STAGE_DIR = Path(os.environ.get("MONARCH_STAGE_DIR", "/tmp/monarch-stage"))
REF_DIR = Path(os.environ.get("MONARCH_REF_DIR", STAGE_DIR / "ref_video"))

FPS = 30
TOTAL_FRAMES = 1336  # 44.53 s, inside the 44.55 s reference track

# Impact schedule (seconds → character). Acts and beats from the reference analysis
# recorded in workflows/current/payload (4 fps frame-diff cut map).
SUB_HITS = [
    (2.17, 0.45, 100.0, 36.0, 0.30),   # A→B throne reveal
    (7.97, 0.40, 96.0, 34.0, 0.34),    # B→C chaos projection start
    (10.3, 0.30, 110.0, 40.0, 0.22),
    (12.4, 0.30, 104.0, 38.0, 0.22),
    (13.97, 0.42, 98.0, 34.0, 0.32),   # C→D triad
    (16.5, 0.32, 116.0, 42.0, 0.24),
    (19.37, 0.50, 92.0, 30.0, 0.38),   # D→E chaos burst
    (21.0, 0.28, 118.0, 44.0, 0.24),
    (22.7, 0.30, 112.0, 42.0, 0.26),
    (24.9, 0.30, 106.0, 40.0, 0.26),
    (25.97, 0.48, 94.0, 32.0, 0.36),   # E→F sovereign stance
    (29.5, 0.32, 108.0, 40.0, 0.24),
    (32.97, 0.52, 90.0, 30.0, 0.40),   # F→G finale build
    (35.4, 0.30, 114.0, 42.0, 0.26),
    (37.6, 0.30, 118.0, 44.0, 0.28),
    (39.4, 0.30, 122.0, 46.0, 0.30),
    (40.47, 0.85, 84.0, 27.0, 0.52),   # G→H the big gold impact
    (41.10, 0.40, 72.0, 30.0, 0.28),   # crown lands
    (43.60, 0.50, 92.0, 34.0, 0.24),   # last button before black
]

CHORDS = [
    (8.0, 12.0, 55.0),
    (19.4, 6.0, 55.0),
    (26.0, 7.0, 61.74),
    (33.0, 7.0, 55.0),
    (40.47, 4.5, 82.41),
]

RISERS = [
    (16.6, 19.3),   # into the chaos burst
    (29.6, 33.0),   # into the finale build
    (37.2, 40.5),   # into the gold impact
]


def _ref_audio_path() -> Path:
    wav = REF_DIR / "ref_audio.wav"
    if not wav.exists():
        raise SystemExit(
            f"reference audio missing: {wav}\n"
            "materialize it once per turn (see docs/STORAGE_AND_MATERIALIZATION.md):\n"
            "  # 1. agent tool: download the reference video from Drive; the connector writes ./google_drive/\n"
            "  mv google_drive/<reference>.mp4 /tmp/monarch-stage/ref.mp4\n"
            "  python3 tools/stage_ref_audio.py /tmp/monarch-stage/ref.mp4 --drive-id <id> --md5 <md5>\n"
        )
    return wav


LAST_BED_KIND = "unknown"


def _synth_bed(sr: int, n: int) -> np.ndarray:
    """Original synthesized score bed, used when the reference WAV is not staged.

    No reference pixels or music are carried into the master either way; this is
    a dark drone + heartbeat sub + air shimmer written for the 44.53 s cut.
    """
    t = np.arange(n, dtype=np.float32) / float(sr)
    drone = (0.10 * np.sin(2 * np.pi * 55.0 * t) + 0.06 * np.sin(2 * np.pi * 82.5 * t + 0.7)
             + 0.04 * np.sin(2 * np.pi * 110.0 * t + 1.3))
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.09 * t)
    mono = drone * lfo
    beat = np.zeros(n, dtype=np.float32)
    for k in range(int(n / (sr * 1.6)) + 1):
        i0 = int(k * 1.6 * sr)
        if i0 >= n:
            break
        i1 = min(n, i0 + int(0.5 * sr))
        lt = np.arange(i1 - i0, dtype=np.float32) / float(sr)
        beat[i0:i1] += np.sin(2 * np.pi * 42.0 * lt) * np.exp(-lt * 7.0) * 0.35
    air = np.random.default_rng(11).standard_normal(n).astype(np.float32) * 0.012
    mono = (mono * 0.6 + beat + air) * 2.2
    return np.stack([mono, np.roll(mono, 37)], axis=1).astype(np.float32)


def build_master_audio() -> tuple[Path, dict[str, Any]]:
    global LAST_BED_KIND
    ref_path = REF_DIR / "ref_audio.wav"
    if ref_path.exists():
        sr, ref_wav = wavfile.read(ref_path)
        ref_f = ref_wav.astype(np.float32) / 32768.0
        if ref_f.ndim == 1:
            ref_f = np.stack([ref_f, ref_f], axis=1)
        target_samples = int(round((TOTAL_FRAMES / float(FPS)) * sr))
        if len(ref_f) < target_samples:
            base = np.vstack([ref_f, np.zeros((target_samples - len(ref_f), 2), dtype=np.float32)])
        else:
            base = ref_f[:target_samples].copy()
        LAST_BED_KIND = "reference-bed"
    else:
        sr = 48000
        target_samples = int(round((TOTAL_FRAMES / float(FPS)) * sr))
        base = _synth_bed(sr, target_samples)
        LAST_BED_KIND = "original-synth-bed"
        print("note: reference bed not staged this session -> original synthesized score bed")

    sfx_l = np.zeros(target_samples, dtype=np.float32)
    sfx_r = np.zeros(target_samples, dtype=np.float32)

    def add_sub_hit(time_s: float, dur_s: float, freq0: float, freq1: float, amp: float) -> None:
        i0 = int(time_s * sr)
        n = int(dur_s * sr)
        if i0 >= target_samples or n <= 0:
            return
        i1 = min(target_samples, i0 + n)
        lt = np.arange(i1 - i0, dtype=np.float32) / float(sr)
        inst_f = freq0 * ((freq1 / freq0) ** (lt / dur_s))
        phase = 2.0 * np.pi * np.cumsum(inst_f) / float(sr)
        env = np.exp(-lt * 8.5) * np.minimum(1.0, lt / 0.006)
        tone = np.sin(phase) * env * amp
        click = np.exp(-lt * 90.0) * amp * 0.35
        sfx_l[i0:i1] += tone + click
        sfx_r[i0:i1] += tone + click

    def add_chord(time_s: float, dur_s: float, root: float) -> None:
        i0 = int(time_s * sr)
        n = int(dur_s * sr)
        if i0 >= target_samples or n <= 0:
            return
        i1 = min(target_samples, i0 + n)
        lt = np.arange(i1 - i0, dtype=np.float32) / float(sr)
        env = np.minimum(1.0, lt / 0.05) * np.exp(-lt * (3.2 / max(0.4, dur_s)))
        partials = (1.0, 2.0, 3.0, 4.0)
        gains = (0.52, 0.28, 0.14, 0.07)
        for side, detune in ((0, 1.0), (1, 1.0009)):
            tone = np.zeros_like(lt)
            for p, g in zip(partials, gains):
                tone += g * np.sin(2 * np.pi * root * p * detune * lt)
            tone *= env * 0.13
            (sfx_l if side == 0 else sfx_r)[i0:i1] += tone

    def add_riser(t0: float, t1: float) -> None:
        i0, i1 = int(t0 * sr), min(target_samples, int(t1 * sr))
        if i0 >= target_samples or i1 <= i0:
            return
        lt = np.arange(i1 - i0, dtype=np.float32) / float(sr)
        dur = max(0.2, t1 - t0)
        sweep = 180.0 * (2.0 ** (lt / dur * 3.2))
        phase = 2.0 * np.pi * np.cumsum(sweep) / float(sr)
        env = (lt / dur) ** 1.7
        noise = np.random.default_rng(4).standard_normal(i1 - i0).astype(np.float32) * 0.06
        tone = (np.sin(phase) * 0.075 + noise) * env
        sfx_l[i0:i1] += tone
        sfx_r[i0:i1] += tone * 0.94

    for hit in SUB_HITS:
        add_sub_hit(*hit)
    for chord in CHORDS:
        add_chord(*chord)
    for riser in RISERS:
        add_riser(*riser)

    mix = np.stack([base[:, 0] + sfx_l, base[:, 1] + sfx_r], axis=1)
    mix = np.tanh(mix * 1.16) / np.tanh(1.16)
    peak = float(np.max(np.abs(mix)))
    target_linear_peak = 10.0 ** (-1.5 / 20.0)
    if peak > 0:
        mix = mix * (target_linear_peak / peak)

    out_wav = PAYLOAD / "monarch_chaos_video_2_master_audio_48k.wav"
    tmp_wav = PAYLOAD / "monarch_chaos_video_2_master_audio_44k.wav"
    wavfile.write(tmp_wav, sr, (mix * 32767.0).astype(np.int16))
    subprocess.run(
        [FFMPEG, "-y", "-i", str(tmp_wav), "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(out_wav), "-loglevel", "warning"],
        check=True,
    )
    tmp_wav.unlink(missing_ok=True)

    rms = float(np.sqrt(np.mean(mix ** 2)))
    tp_db = 20.0 * math.log10(max(1e-6, float(np.max(np.abs(mix)))))
    lufs_est = 20.0 * math.log10(max(1e-6, rms)) - 0.691
    return out_wav, {
        "rms": round(rms, 4),
        "true_peak_dbfs": round(tp_db, 2),
        "lufs_approx": round(lufs_est, 2),
        "samples": int(target_samples),
        "duration_seconds": round(TOTAL_FRAMES / float(FPS), 3),
    }
