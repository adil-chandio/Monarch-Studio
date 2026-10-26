# Resume capsule — WF04-REF-INTAKE-2

**Status:** `waiting_external`  
**Title:** WF-04 · CHAOSGO reference inspection (no production) — awaiting user decision  
**Style:** `monarch-face-chaos`  
**Checkpoint sequence:** 3  
**Last checkpoint:** 2026-10-26T21:12:04Z

## Goal

Inspect the supplied Chaos 2 reference exactly like the earlier chat did, with no film production, and get explicit user approval before any further work.

## Acceptance criteria

- [ ] Inspection report grounded in decoded frames and audio
- [ ] No render/upload without explicit approval

## Exact next action

User decides: (a) run notebook on Colab/Kaggle free GPU now, or (b) approve Track C hybrid starting with CPU 3D base, or (c) ask for history-rewrite/make-private to purge third-party master from public git history. Also still pending: film number/length, character input, masked-vs-open face, and G1 shotlist approval.

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
- Latest checkpoint package: `operations/continuity/checkpoints/WF04-REF-INTAKE-2/0003-20261026T211204Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
