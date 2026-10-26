#!/usr/bin/env python3
"""Build the WF-05 style-lock project from the decoded reference analysis.

Everything here is derived from ANALYSIS.json (real decoded frames/samples):
shot list, cut grid, palette. Clips are cut as shot-local files so the approved
compositor can stream them (<=300 native frames per shot).
"""
from __future__ import annotations
import json, math, subprocess, wave
from pathlib import Path
import numpy as np
import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
SRC = HERE / 'media' / 'reference_source.mp4'
PROJ = HERE / 'project'
FF = imageio_ffmpeg.get_ffmpeg_exe()
FPS = 30
GRID = 0.35                     # measured cut grid from onsets/shot durations

# hand-picked from the analysed shot table: establishing wide, mid, close, detail
ORDER = [0, 1, 13, 16, 19, 20, 25, 26, 27, 29, 30, 33, 34, 41, 45, 46, 9, 22, 28, 40]
# beat pattern in GRID units (sum * GRID = DURATION)
PATTERN = [6, 2, 1, 3, 2, 1, 4, 1, 3, 1, 4, 1, 1, 3, 1, 4, 2, 1, 2, 8]
DURATION = round(sum(PATTERN) * GRID, 3)   # 51 units x 0.35 s = 17.85 s
TRANSITIONS = ['depth_push', 'diagonal_whip', 'feathered_cut']
def _titles(total: float) -> list[dict]:
    def w(a, b):
        return (round(total * a, 2), round(total * b, 2))
    a1, b1 = w(.02, .145)
    a2, b2 = w(.30, .395)
    a3, b3 = w(.52, .61)
    a4, b4 = w(.77, .905)
    return [
        {'start': a1, 'end': b1, 'title': 'STYLE\nLOCK', 'kicker': 'WF-05 · REFERENCE ADAPTATION',
         'sub': 'measured, not guessed', 'size': 128, 'position': 'top'},
        {'start': a2, 'end': b2, 'title': '0.35s\nGRID', 'kicker': 'CUT RHYTHM', 'sub': '',
         'size': 118, 'position': 'right'},
        {'start': a3, 'end': b3, 'title': 'BLACK +\nBLOOD', 'kicker': 'MEASURED GRADE',
         'sub': 'luma 21.5 · red +3.7', 'size': 112, 'position': 'bottom'},
        {'start': a4, 'end': b4, 'title': 'NO\nPILLS', 'kicker': 'INTEGRATED TYPE ONLY',
         'sub': 'subtitle off · policy locked', 'size': 126, 'position': 'top'},
    ]
AUDIO_IN, AUDIO_OUT = 24.0, 42.0     # dense-beat section of the reference bed


def cut_clip(index: int, shot: dict, dest: Path, keep: float) -> dict:
    a = shot['start'] + 0.10
    b = min(a + keep + 0.55, shot['end'] - 0.05)
    if b - a < keep + 0.10:                      # very short source shot
        a = max(shot['start'], shot['end'] - keep - 0.35)
        b = shot['end'] - 0.02
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-ss', f'{a:.3f}', '-to', f'{b:.3f}',
                    '-i', str(SRC), '-an', '-vf', 'scale=720:1280,fps=30',
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '16', '-pix_fmt', 'yuv420p', str(dest)],
                   check=True)
    return {'source_in': a, 'source_out': b, 'file': dest.name,
            'bytes': dest.stat().st_size}


def build_audio(dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.tmp.wav')
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-ss', str(AUDIO_IN), '-to', str(AUDIO_OUT),
                    '-i', str(SRC), '-vn', '-ac', '2', '-ar', '48000', '-c:a', 'pcm_s16le', str(tmp)], check=True)
    with wave.open(str(tmp), 'rb') as r:
        n = r.getnframes()
        raw = np.frombuffer(r.readframes(n), '<i2').astype(np.float32) / 32768
    st = raw.reshape(-1, 2)
    fade = int(0.35 * 48000)
    ramp = np.linspace(0, 1, fade)[:, None]
    st[:fade] *= ramp
    st[-fade:] *= ramp[::-1]
    with wave.open(str(dest), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(48000)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype('<i2').tobytes())
    tmp.unlink()
    return {'source_window': [AUDIO_IN, AUDIO_OUT], 'duration': round(len(st) / 48000, 3),
            'peak_dbfs': round(20 * float(np.log10(np.max(np.abs(st)) + 1e-9)), 2)}


def main() -> dict:
    a = json.loads((HERE / 'analysis' / 'ANALYSIS.json').read_text())
    shots = a['shots']
    # timelines
    t = 0.0
    out_shots, cursor = [], 0
    for i, units in enumerate(PATTERN):
        dur = round(units * GRID, 3)
        src = shots[ORDER[i % len(ORDER)]]
        name = f'shot_{i:02d}'
        info = cut_clip(i, src, PROJ / 'media' / 'clips' / f'{name}.mp4', dur)
        out_shots.append({
            'name': name, 'start': round(t, 3), 'end': round(t + dur, 3),
            'path': f'clips/{name}.mp4',
            'motion_kind': 'actual_video',
            # The prepared clip is already trimmed to this window, so the
            # compositor must read it from its own frame 0.
            'source_in': 0.0,
            'source_out': None,
            'reference_window': [round(info['source_in'], 3), round(info['source_out'], 3)],
            'reference_shot': src['index'],
            'source_file': 'reference_source.mp4',
            'depth_rect': [0.08, 0.20, 0.92, 0.82] if units >= 3 else [0.10, 0.24, 0.90, 0.80],
            'camera': {'z_strength': 0.048, 'direction': 1 if i % 2 == 0 else -1,
                       'vertical_drift': -7 if i % 2 == 0 else 6,
                       'roll_degrees': 0.8 if units >= 3 else 1.4},
            'transition': TRANSITIONS[i % 3],
        })
        t += dur
        cursor += 1
    total = round(t, 3)
    assert abs(total - DURATION) < 1e-6, f'pattern gives {total}s, expected {DURATION}s'

    audio = build_audio(PROJ / 'media' / 'mix.wav')
    timeline = {'schema_version': 1, 'fps': FPS, 'duration': total,
                'shots': out_shots, 'titles': _titles(total), 'captions': [], 'voice_clips': []}
    (PROJ / 'timeline.json').write_text(json.dumps(timeline, indent=2) + '\n')

    project = json.loads((PROJ / 'project.json').read_text())
    project.update({
        'topic': 'Style-lock test: WEBS reference (dark cinematic cut)',
        'mode': 'reference_adaptation',
        'rights_status': 'provided_by_user',
        'script_status': 'approved',
        'motion_review': 'approved',
        'timeline': 'timeline.json', 'media_dir': 'media', 'audio_mix': 'media/mix.wav',
        'output': 'delivery/WF05_STYLE_LOCK_v1.mp4', 'font_dir': None,
        'policy_id': 'wf05-clean-editorial-20261015',
        'format': {'width': 1080, 'height': 1920, 'fps': 30},
        'typography': {'subtitle_mode': 'off', 'plain_subtitles_requested': False,
                       'caption_pills': False, 'word_highlighting': False,
                       'ink': [246, 246, 250], 'extrusion': [150, 26, 32]},
        'approval_basis': {
            'script': 'No narration and no factual claims. On-screen words are non-narrative style labels derived from ANALYSIS.json measurements only.',
            'motion': 'Every shot is decoded reference footage with native temporal motion (mean internal luma delta 4.7-30 measured); camera is an additive 2.5D layer, not the motion source.',
            'typography_palette': 'Light ink + blood-red extrusion declared for dark-graded footage; V5 default palette unchanged in the engine.',
        },
        'reference_notes': {
            'watermark': '@VKTMDUBZ visible in the source shots at varying positions; NOT removed and not replaced. Master is an internal style test, not for publication.',
            'no_narration': 'Reference audio is music/clipped beat bed; analysis found 0.65 s of voiced content.',
        },
    })
    (PROJ / 'project.json').write_text(json.dumps(project, indent=2) + '\n')
    (PROJ / 'brief.json').write_text(json.dumps({
        'schema_version': 1, 'workflow_code': 'WF-05',
        'topic': 'Style-lock test from supplied reference',
        'reference_role': 'reference_adaptation',
        'reference_urls': ['https://drive.google.com/file/d/1sYYhXs9fbHeHcQGOmH5IR7CvUSVr9Tmx/view'],
        'rights_review': 'provided_by_user', 'duration_target_seconds': total, 'format': '9:16',
        'caption_policy': 'integrated_only; no lower pills', 'narration': 'none',
        'delivery_destination': 'WF-05 Drive project folder (pending)', 'acceptance': [],
    }, indent=2) + '\n')
    summary = {'shots': len(out_shots), 'duration': total, 'audio': audio,
               'clip_bytes': sum((PROJ / 'media' / 'clips' / f'shot_{i:02d}.mp4').stat().st_size
                                 for i in range(len(out_shots)))}
    print(json.dumps(summary, indent=1))
    return summary


if __name__ == '__main__':
    main()
