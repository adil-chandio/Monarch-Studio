# Resume capsule — WF04-REF-INTAKE-2

**Status:** `waiting_external`  
**Title:** WF-04 · CHAOSGO reference inspection (no production) — awaiting user decision  
**Style:** `monarch-face-chaos`  
**Checkpoint sequence:** 4  
**Last checkpoint:** 2026-10-27T01:19:50Z

## Goal

Inspect the supplied Chaos 2 reference exactly like the earlier chat did, with no film production, and get explicit user approval before any further work.

## Acceptance criteria

- [ ] Inspection report grounded in decoded frames and audio
- [ ] No render/upload without explicit approval

## Exact next action

Get user's creative verdict on the preview. Then either (a) push quality: 1080p full-res render of the same scene (21.9 h measured on this box) or GPU polish via Wan2.2-Animate using this animatic as the driving video, (b) add the 22-blendshape face rig / open face if they want it unmasked, (c) fix the 2 remaining weak setups, (d) delete or keep the unapproved CHAOS 04 Drive files and decide the git-history purge.

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
- Latest checkpoint package: `operations/continuity/checkpoints/WF04-REF-INTAKE-2/0004-20261027T011950Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
