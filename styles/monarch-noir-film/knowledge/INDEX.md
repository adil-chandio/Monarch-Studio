# Monarch Noir Film knowledge index

This is the durable map for every reproducible fact in the style. Chat summaries never replace the implementation or measured evidence linked here.

## Start/resume authority

1. `README.md` — normalized style overview.
2. `workflow.json` — machine-readable contract and delivery classes.
3. `RESUME_STATE.md` — newest imported Drive state.
4. `HUB.md` — imported workflow hub snapshot.
5. `../../docs/RECONCILIATION.md` — authoritative drift treatment.
6. `SOURCE_INVENTORY.md` — complete current direct-child Drive inventory.

## THE SHADOW · Film #1

- Narrative/design: `SCRIPT_THE_SHADOW.md`, `DNA_THE_SHADOW.json`.
- Picture: `src/noir.py`, `src/film_shadow.py`.
- Audio: `src/audio_shadow.py`.
- Encode: `src/encode_shadow.sh`, `src/finish_shadow.sh`.
- Events/measurements: `data/events.json`, `data/beats.json`, `data/picture_metrics.json`, `data/mix_stats.json`.
- Certification: `src/gate_shadow.py`, `GATES_THE_SHADOW_v1.md`.
- Look/hero: `NOIRGO_LOOK_SHEET_v0.jpg`, `CHARSHEET_HERO_v2.jpg`.

## THE WINDOW · Film #2

- Narrative/design: `SCRIPT_THE_WINDOW.md`, `DNA_THE_WINDOW.json`.
- Picture: `src/world.py`, `src/human.py`, `src/stick3d.py`, `src/film_window.py`.
- World plates: `plates/` (ten final plates plus measured facade map).
- Voice: `vo/vo01.mp3` through `vo/vo10.mp3`.
- Audio: `src/audio_window.py`.
- Encode: `src/encode_window.sh`.
- Events/measurements: `data/events_window.json`, `data/beats_window.json`, `data/vo_window_info.json`.
- Certification: `src/gate_window.py`, `GATES_THE_WINDOW_v1.md`.
- Look/hero: `NOIRGO_LOOK_SHEET_v1_WINDOW.jpg`, `NOIRGO_LOOK_SHEET_v2_WINDOW.jpg`, `HERO_v2_motion_test.mp4`.

## Later evidence

- `films/04am/GATES_NOIRGO_4AM_v2.md` — R2 limited gate evidence, implementation absent.
- AB KARO ABHI is R3 external-delivery evidence only; current Drive ID/hash remain in `workflow.json` and `SOURCE_INVENTORY.md`.
- No future film number may be assigned until the Film-#3 conflict is resolved.

## Tools used

| Area | Tools/libraries |
|---|---|
| Procedural/raster film rendering | Python, NumPy, Pillow |
| 3-D-like character projection | custom `toon.py`/`shade.py`, `stick3d.py`, `human.py` |
| World construction | generated PNG plates, measured crop camera, rain/dust/light controls |
| Audio/score/sound design | Python/scipy/wave, generated speech, FFmpeg |
| Encode/splice | sequential x264 segments, concat demuxer, frame-exact replacement |
| Measurement/gates | custom Python gates, ffprobe, image/audio metrics, MD5 |
| State/provenance | JSON, Markdown, editor brain, Drive/Notion/Linear/Docs/Git |

## Resource and failure knowledge

- The original 2 GB environment OOM-killed multi-input FFmpeg graphs; one decoder and one encoder at a time is the preserved rule.
- Long holds are not static: micro-motion, motivated light and atmospheric movement carry them.
- Source truth and delivery truth are separate; a final MP4 without source/gates is never promoted to R1.
- Historical records remain immutable; corrections are appended through reconciliation records.

## Completion rule

Before a running noir task leaves `workflows/current/`, add its script, DNA, events, renderer, audio, inputs, gate implementation/report, measured master identity, decisions, failures and remote record IDs to this style; update this index and pass continuity/repository validation.