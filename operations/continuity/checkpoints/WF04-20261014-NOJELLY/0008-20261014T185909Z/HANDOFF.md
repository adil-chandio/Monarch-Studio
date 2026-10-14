# Resume capsule — WF04-20261014-NOJELLY

**Status:** `waiting_external`  
**Title:** Monarch Face: original scenes and articulated motion, no plate warps  
**Style:** `monarch-face-chaos`  
**Checkpoint sequence:** 8  
**Last checkpoint:** 2026-10-14T18:59:09Z

## Goal

Replace the user-rejected recycled image-warp film with new scene design and verified joint-driven motion; validate identity and natural movement before attempting a full-length final.

## Acceptance criteria

- [ ] New visuals, not old plates; no image-space body/face mesh warps; real 3D joint movement with stable feet and neck; crown above MONARCH STUDIO ending; no claims of photoreal likeness or final approval without visual evidence.

## Exact next action

Recover the exact selected MASTER_FRONT image by user attachment or accessible link, inspect it, preserve a durable asset receipt, then generate matching profile/rear/face-detail views. Do not ask user to re-upload all original videos and do not silently substitute another front design.

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
- Latest checkpoint package: `operations/continuity/checkpoints/WF04-20261014-NOJELLY/0008-20261014T185909Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
