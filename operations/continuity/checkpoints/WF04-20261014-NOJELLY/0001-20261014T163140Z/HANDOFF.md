# Resume capsule — WF04-20261014-NOJELLY

**Status:** `active`  
**Title:** Monarch Face: original scenes and articulated motion, no plate warps  
**Style:** `monarch-face-chaos`  
**Checkpoint sequence:** 1  
**Last checkpoint:** 2026-10-14T16:31:40Z

## Goal

Replace the user-rejected recycled image-warp film with new scene design and verified joint-driven motion; validate identity and natural movement before attempting a full-length final.

## Acceptance criteria

- [ ] New visuals, not old plates; no image-space body/face mesh warps; real 3D joint movement with stable feet and neck; crown above MONARCH STUDIO ending; no claims of photoreal likeness or final approval without visual evidence.

## Exact next action

Build a new vault set and standing articulated character; render fixed-camera proof frames before a short native-frame video.

## Running processes

- None recorded.

## Recovery command

```bash
python3 tools/continuity.py resume
```

## Durable evidence

- Active state: `workflows/current/ACTIVE_TASK.json`
- Hash-chained action journal: `workflows/current/JOURNAL.jsonl`
- Visible user/assistant transcript: `workflows/current/CHAT_TRANSCRIPT.jsonl`
- Active payload only: `workflows/current/payload/`
- Latest checkpoint package: `operations/continuity/checkpoints/WF04-20261014-NOJELLY/0001-20261014T163140Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
