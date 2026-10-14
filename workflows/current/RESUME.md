# Resume capsule — WF04-20261014-NOJELLY

**Status:** `waiting_external`  
**Title:** Monarch Face: original scenes and articulated motion, no plate warps  
**Style:** `monarch-face-chaos`  
**Checkpoint sequence:** 17  
**Last checkpoint:** 2026-10-14T22:36:43Z

## Goal

Replace the user-rejected recycled image-warp film with new scene design and verified joint-driven motion; validate identity and natural movement before attempting a full-length final.

## Acceptance criteria

- [ ] New visuals, not old plates; no image-space body/face mesh warps; real 3D joint movement with stable feet and neck; crown above MONARCH STUDIO ending; no claims of photoreal likeness or final approval without visual evidence.

## Exact next action

Work only against the confirmed main reference and unchanged source music. Read main-reference/REFERENCE_LOCK.md and MAIN_REFERENCE_AUDIT.json. Previous eight-beat plan is not a verified reference cut map; 295 transition candidates need classification. Other-chat rig source is a limited 2.5D photographic puppet, not proof of exact 3D human/weapon/camera motion. Do not relabel an outro, old composite, other-chat movie or image-warp study as the requested full film.

## Running processes

- `monarch-original-3d-motion-check-30451e5f` — Vault sample-frame render — completed
- `monarch-finish-export-from-saved-3287176f` — Completed 44.4s draft export — completed
- `monarch-corrected-joint-motion-r-ce4914d5` — Corrected 3D QA samples — completed
- `monarch-native-motion-frames-431c3ea6` — Native skinning-space QA samples — completed
- `monarch-full-44-4-second-draft-e-767b7d57` — Initial full export attempt — failed
- `monarch-crown-outro-0ee7e859` — Native 3.6s crown outro plus original sound — completed
- `main-reference-timing-and-music--b24e5955` — Canonical main reference frame/audio analysis — completed

## Recovery command

```bash
python3 tools/continuity.py resume
```

## Durable evidence

- Active state: `workflows/current/ACTIVE_TASK.json`
- Hash-chained action journal: `workflows/current/JOURNAL.jsonl`
- Visible user/assistant transcript: `workflows/current/CHAT_TRANSCRIPT.jsonl`
- Active payload only: `workflows/current/payload/`
- Latest checkpoint package: `operations/continuity/checkpoints/WF04-20261014-NOJELLY/0017-20261014T223643Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
