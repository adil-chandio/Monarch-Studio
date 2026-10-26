#!/usr/bin/env python3
"""Render the CHAOS 04 delivery report from the measured gate JSON."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
rep = json.loads((HERE / 'output' / 'GATE_REPORT_CHAOS04_v1.json').read_text())

rows = '\n'.join(
    f"| `{g['id']}` | {g['description']} | {'PASS' if g['passed'] else 'FAIL'} | `{g['measured']}` |"
    for g in rep['gates'])
acts = '\n'.join(
    f"| {k} | {v['mean_luma']} | {v['shots']} | {v['mean_shot']} s |"
    for k, v in rep['act_stats'].items())

md = f"""# WF-04 · MONARCH CHAOS 04 — DELIVERY GATES REPORT

- **Master:** `{rep['master_file']}` (`{rep['master_size_bytes']:,}` bytes · MD5 `{rep['master_md5']}`)
- **SHA-256:** `{rep['master_sha256']}`
- **Format:** `{rep['resolution']}` (9:16) · `{rep['fps']:.2f} fps` · `{rep['frames']}` frames (`{rep['duration_s']} s`)
- **Audio:** {rep['audio']['sample_rate']} Hz stereo AAC · `{rep['audio']['lufs']} LUFS` · true peak `{rep['audio']['true_peak_dbfs']} dBFS` · corr `{rep['audio']['stereo_correlation']}`
- **Source:** raw supplied footage (`{rep['source']['bytes']:,}` bytes, {rep['source']['source_shot_count']} analysed shots)
- **Result:** **{rep['gates_passed']} GATES PASSED**

| Gate | Check | Status | Measured |
|---|---|---|---|
{rows}

## Act structure (measured on the master)

| Act | Mean luma | Shots | Mean shot length |
|---|---|---|---|
{acts}

## What this edit is

A cinematic re-edit of the supplied raw footage: per-act grade (contrast, split tone, vignette,
bloom, midtone exposure), animated light leaks, a neural-sync HUD act, beat-snapped cut rhythm
({rep['transitions_detected']} detected transitions), three impact strobes into the climax, the gold
crowned MONARCH STUDIO end card, and mastered 48 kHz stereo audio at {rep['audio']['lufs']} LUFS.

## Honest limitations

- The raw reference carries a third-party **@VKTMDUBZ** watermark in every frame. It was **not**
  removed or covered. This master is a private style/proof cut, not a cleared publication asset.
- The source is HEVC 720×1280 and is upscaled to 1080×1920; detail cannot exceed the source.
- No new generation was used: every frame comes from the supplied video.
- Gates are measured, not asserted: a failed gate stays failed in this file.
"""
out = HERE / 'output' / 'DELIVERY_GATES_CHAOS04_v1.md'
out.write_text(md)
print(out, len(md))
