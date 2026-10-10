# Monarch Stickman Animation knowledge index

This index prevents working knowledge from disappearing inside chat history. Permanent facts remain in the files below; new accepted knowledge must be added here or linked from here before an active task is completed.

## Start/resume authority

1. `README.md` — normalized style overview and process.
2. `workflow.json` — machine-readable workflow contract.
3. `SHADEGO.md` — exact activation/autopilot protocol.
4. `RESUME_STATE.md` — imported operational state.
5. `brain/registry.json` — delivered-concept memory.
6. `DRIVE_MANIFEST.md` — Drive delivery ledger.

## How the implementation works

- Picture/timeline: `src/respect2.py`, `src/timeline_respect2.py`.
- Hero/rig/world: `src/shade.py`, `src/toon.py`, `src/hybrid.py`, `src/character.py`, `CHARACTER_SPEC.md`.
- Audio/voice: `src/vo_fit.py`, `src/make_asmr_respect2.py`, `src/mux_respect2.sh`, `ASMR_RESPECT2_LEDGER.csv`.
- Gates: `src/gate_respect2.py` plus EDITOR BRAIN novelty gate in `brain/concept.py`.
- Build orchestration: `build_respect2.sh`, `build_respect2_b.sh`, `finish_respect2.sh`.
- Current contact sheet: `shade_respect_v2_contact.png`.

## Historical progression

- `VIDEO_V4_NOTES.md` through `VIDEO_V9_NOTES.md`.
- `VIDEO_POWER_NOTES.md`, `VIDEO_SHADE_NOTES.md`, `VIDEO_RESPECT_NOTES.md`.
- `VIDEO_WIDE_NOTES.md`, `VIDEO_EPISODE_NOTES.md`.
- `MASTER_PROMPT.md`, `MASTER_PROMPT_V2.md`, `MASTER_PROMPT_V3.md`, `MASTER_PROMPT_V4.md`.
- `MONARCH_STICKMAN_ANIMATION_SESSION_LOG.md` — detailed turn/session history.
- `records/archive/RESUME_STATE_archive-v3.md` — superseded resume preserved as history.

## Decisions, measured lessons, failures and fixes

- `MONARCH_SKILL_MOTION_EDIT.md` — primary skill/lesson ledger.
- `MONARCH_SKILL_LONGFORM_16x9.md` — long-form rules.
- `FORENSIC_AUDIT_V7.md` — measured forensic audit.
- `MONARCH_EDITOR_BRAIN.md` and `brain/` — novelty formula, libraries, references and memory.
- `BUILD_MANIFEST*.json`, `*_AUDIO_LEDGER.csv`, `ASMR_*_LEDGER.csv` — reproducible evidence.

## Tools used

| Area | Tools/libraries |
|---|---|
| Raster animation and composition | Python, NumPy, Pillow |
| Signal/audio generation and fitting | Python wave/scipy, generated speech clips, FFmpeg |
| Encode/mux/probe | imageio-ffmpeg supplied FFmpeg/ffprobe |
| PDF/inspection | ReportLab, PyMuPDF |
| State/novelty memory | JSON, Markdown, `brain/concept.py` |
| Delivery/provenance | Google Drive IDs + MD5, Notion, Linear, Google Docs, Git |

## Completion rule

Before a running task leaves `workflows/current/`, add its final source, assets, measurements, gate report, decisions, failed approaches and remote IDs under this style, update this index, then run repository validation and a continuity checkpoint.