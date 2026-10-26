# WF-04 · MONARCH CHAOS 04 — DELIVERY GATES REPORT

- **Master:** `CHAOS04_MASTER.mp4` (`44,741,521` bytes · MD5 `bf4a8925e3cb399bfcaaeaef1a4dfad5`)
- **SHA-256:** `dcd92d7b1f80803c56abecf11fd059c85060b5d7b7d84a1d2d3ac6488a4b433b`
- **Format:** `1080x1920` (9:16) · `30.00 fps` · `1332` frames (`44.4 s`)
- **Audio:** 48000 Hz stereo AAC · `-16.0 LUFS` · true peak `-5.11 dBFS` · corr `0.7363`
- **Source:** raw supplied footage (`26,397,151` bytes, 47 analysed shots)
- **Result:** **23/23 GATES PASSED**

| Gate | Check | Status | Measured |
|---|---|---|---|
| `G01` | Master MP4 exists and is non-empty | PASS | `44,741,521 B` |
| `G02` | Exact Full-HD 9:16 vertical resolution (1080x1920) | PASS | `1080x1920` |
| `G03` | Exact frame rate (30.00 fps) | PASS | `30.0 fps` |
| `G04` | Reference-length edit: 44.4 s +/- 0.5 s (raw source is 44.4 s) | PASS | `1332 frames (44.4s)` |
| `G05` | 48 kHz stereo mastered audio stream | PASS | `48000 Hz, 2 ch` |
| `G06` | Loudness in cinematic short range (-16.5 to -11.0 LUFS) | PASS | `-16.0 LUFS` |
| `G07` | True-peak ceiling safety (<= -1.0 dBFS) | PASS | `-5.11 dBFS` |
| `G08` | Stereo width active (L/R correlation < 0.98) | PASS | `corr=0.7363` |
| `G09` | Act A cold open stays dark (mean luma <= 45) | PASS | `mean=8.9` |
| `G10` | Act C neural-sync HUD act is brighter than the cold open | PASS | `C=35.0 vs A=8.9` |
| `G11` | Cut rhythm: every act has real shot variety (>= 2 shots per act) | PASS | `{'A': 2, 'B': 4, 'C': 5, 'D': 4, 'E': 20, 'F': 4, 'G': 9, 'H': 24}` |
| `G12` | Act D close-up act is readable, not blown out (35 <= mean luma <= 95) | PASS | `mean=49.0` |
| `G13` | Act E chaos burst fires >= 15 frame-locked cuts in 5.8 s | PASS | `54 cuts` |
| `G14` | Act F sovereign stance moves less than the burst (locked wide shots) | PASS | `F=16.71 vs E=23.71 per frame` |
| `G15` | Act H climax accelerates (>= 20 cuts in 6.2 s) | PASS | `71 cuts` |
| `G16` | Climax stays readable (no permanent white-out: peak luma < 235) | PASS | `peak=197.3` |
| `G17` | Gold emblem end card holds dark with a warm mark (end luma 4..70) | PASS | `end=16.8` |
| `G18` | Total shot count matches the built plan (no silent frame drops) | PASS | `1332 frames, plan shots=72` |
| `G19` | End card and look sheet assets exist | PASS | `emblem + look sheet present` |
| `G20` | Deterministic MD5 + SHA-256 recorded | PASS | `bf4a8925e3cb399bfcaaeaef1a4dfad5` |
| `G21` | REAL MOVEMENT: walk act advances the frame (>= 0.6 band diff/frame) | PASS | `13.1 per frame` |
| `G22` | REAL MOVEMENT: chaos burst is faster than the walk (burst > walk) | PASS | `23.71 vs 13.1 per frame` |
| `G23` | Every act uses decoded source footage (shots reference real source indexes) | PASS | `47 analysed source shots` |

## Act structure (measured on the master)

| Act | Mean luma | Shots | Mean shot length |
|---|---|---|---|
| A | 8.9 | 2 | 2.1 s |
| B | 33.2 | 4 | 1.3 s |
| C | 35.0 | 5 | 1.12 s |
| D | 49.0 | 4 | 1.15 s |
| E | 26.6 | 20 | 0.29 s |
| F | 29.0 | 4 | 1.3 s |
| G | 16.6 | 9 | 0.67 s |
| H | 41.5 | 24 | 0.26 s |

## What this edit is

A cinematic re-edit of the supplied raw footage: per-act grade (contrast, split tone, vignette,
bloom, midtone exposure), animated light leaks, a neural-sync HUD act, beat-snapped cut rhythm
(266 detected transitions), three impact strobes into the climax, the gold
crowned MONARCH STUDIO end card, and mastered 48 kHz stereo audio at -16.0 LUFS.

## Honest limitations

- The raw reference carries a third-party **@VKTMDUBZ** watermark in every frame. It was **not**
  removed or covered. This master is a private style/proof cut, not a cleared publication asset.
- The source is HEVC 720×1280 and is upscaled to 1080×1920; detail cannot exceed the source.
- No new generation was used: every frame comes from the supplied video.
- Gates are measured, not asserted: a failed gate stays failed in this file.
