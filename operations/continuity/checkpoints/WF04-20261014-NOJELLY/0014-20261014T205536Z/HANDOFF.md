# Resume capsule — WF04-20261014-NOJELLY

**Status:** `rendering`  
**Title:** Monarch Face: original scenes and articulated motion, no plate warps  
**Style:** `monarch-face-chaos`  
**Checkpoint sequence:** 14  
**Last checkpoint:** 2026-10-14T20:55:36Z

## Goal

Replace the user-rejected recycled image-warp film with new scene design and verified joint-driven motion; validate identity and natural movement before attempting a full-length final.

## Acceptance criteria

- [ ] New visuals, not old plates; no image-space body/face mesh warps; real 3D joint movement with stable feet and neck; crown above MONARCH STUDIO ending; no claims of photoreal likeness or final approval without visual evidence.

## Exact next action

Finish and inspect render_brand_outro.py output: 108 native 1080x1920 graphic frames at 30fps with original stereo sting. Verify full decode/audio limits and upload the completed component. Do not count these as character-motion frames or claim the full 44.4s film is complete.

## Running processes

- `monarch-original-3d-motion-check-30451e5f` — Vault sample-frame render — completed
- `monarch-finish-export-from-saved-3287176f` — Completed 44.4s draft export — completed
- `monarch-corrected-joint-motion-r-ce4914d5` — Corrected 3D QA samples — completed
- `monarch-native-motion-frames-431c3ea6` — Native skinning-space QA samples — completed
- `monarch-full-44-4-second-draft-e-767b7d57` — Initial full export attempt — failed

## Recovery command

```bash
python3 tools/continuity.py resume
```

## Durable evidence

- Active state: `workflows/current/ACTIVE_TASK.json`
- Hash-chained action journal: `workflows/current/JOURNAL.jsonl`
- Visible user/assistant transcript: `workflows/current/CHAT_TRANSCRIPT.jsonl`
- Active payload only: `workflows/current/payload/`
- Latest checkpoint package: `operations/continuity/checkpoints/WF04-20261014-NOJELLY/0014-20261014T205536Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
