# Resume capsule — WF04-REF-INTAKE-2

**Status:** `waiting_external`  
**Title:** WF-04 · CHAOSGO reference inspection (no production) — awaiting user decision  
**Style:** `monarch-face-chaos`  
**Checkpoint sequence:** 2  
**Last checkpoint:** 2026-10-26T21:04:27Z

## Goal

Inspect the supplied Chaos 2 reference exactly like the earlier chat did, with no film production, and get explicit user approval before any further work.

## Acceptance criteria

- [ ] Inspection report grounded in decoded frames and audio
- [ ] No render/upload without explicit approval

## Exact next action

Await user choice: Track A/B/C, GPU availability, character input, film number+length, masked-vs-open face. Then write SHOTLIST_3D.json (G1) only.

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
- Latest checkpoint package: `operations/continuity/checkpoints/WF04-REF-INTAKE-2/0002-20261026T210427Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
