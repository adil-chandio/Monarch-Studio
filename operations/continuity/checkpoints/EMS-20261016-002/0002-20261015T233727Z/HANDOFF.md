# Resume capsule — EMS-20261016-002

**Status:** `rendering`  
**Title:** KAANTA V8 full-film visual and motion pass  
**Style:** `monarch-zackd-3d`  
**Checkpoint sequence:** 2  
**Last checkpoint:** 2026-10-15T23:37:27Z

## Goal

Enhance the whole film across opening, material treatment, camera/action staging and sound dynamics; preserve narration and clean-frame constraints. Preview first, native render only after proof.

## Acceptance criteria

- [ ] Meaningful changes across all three scene groups, not just hero cells
- [ ] Same narration, safety qualifiers and clean composition
- [ ] Preview and current-source tests before native rendering; verified final master and separate delivery

## Exact next action

Query preview process kaanta-v8-full-film-review-rende-cbcd7c0d, verify full preview then start single native run-v8.sh and record its process. Never run legacy run-v7.sh from this fork.

## Running processes

- `kaanta-v8-full-film-review-rende-cbcd7c0d` — V8 full-film270px review and audio — running

## Recovery command

```bash
python3 tools/continuity.py resume
```

## Durable evidence

- Active state: `workflows/current/ACTIVE_TASK.json`
- Hash-chained action journal: `workflows/current/JOURNAL.jsonl`
- Visible user/assistant transcript: `workflows/current/CHAT_TRANSCRIPT.jsonl`
- Active payload only: `workflows/current/payload/`
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261016-002/0002-20261015T233727Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
