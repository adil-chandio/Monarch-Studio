# Resume capsule — WF04-20261014-NOJELLY

**Status:** `waiting_external`  
**Title:** Monarch Face: original scenes and articulated motion, no plate warps  
**Style:** `monarch-face-chaos`  
**Checkpoint sequence:** 15  
**Last checkpoint:** 2026-10-14T21:10:04Z

## Goal

Replace the user-rejected recycled image-warp film with new scene design and verified joint-driven motion; validate identity and natural movement before attempting a full-length final.

## Acceptance criteria

- [ ] New visuals, not old plates; no image-space body/face mesh warps; real 3D joint movement with stable feet and neck; crown above MONARCH STUDIO ending; no claims of photoreal likeness or final approval without visual evidence.

## Exact next action

Preserve completed character/shot designs and separately uploaded crown outro. Recover the exact outro via VIDEO_COMPONENTS.json if local media disappears; never re-render completed components merely on Continue. Remaining work is actual new-character motion for beats 01–08 plus final assembly/audio-to-action edit; photoreal motion renderer remains unavailable and Runway/Replicate connectors are unsupported. Do not substitute old live-action footage, still warps or the rejected mannequin.

## Running processes

- `monarch-original-3d-motion-check-30451e5f` — Vault sample-frame render — completed
- `monarch-finish-export-from-saved-3287176f` — Completed 44.4s draft export — completed
- `monarch-corrected-joint-motion-r-ce4914d5` — Corrected 3D QA samples — completed
- `monarch-native-motion-frames-431c3ea6` — Native skinning-space QA samples — completed
- `monarch-full-44-4-second-draft-e-767b7d57` — Initial full export attempt — failed
- `monarch-crown-outro-0ee7e859` — Native 3.6s crown outro plus original sound — completed

## Recovery command

```bash
python3 tools/continuity.py resume
```

## Durable evidence

- Active state: `workflows/current/ACTIVE_TASK.json`
- Hash-chained action journal: `workflows/current/JOURNAL.jsonl`
- Visible user/assistant transcript: `workflows/current/CHAT_TRANSCRIPT.jsonl`
- Active payload only: `workflows/current/payload/`
- Latest checkpoint package: `operations/continuity/checkpoints/WF04-20261014-NOJELLY/0015-20261014T211004Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
