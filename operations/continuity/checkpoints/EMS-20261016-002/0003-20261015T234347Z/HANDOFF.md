# Resume capsule — EMS-20261016-002

**Status:** `active`  
**Title:** KAANTA V8 full-film visual and motion pass  
**Style:** `monarch-zackd-3d`  
**Checkpoint sequence:** 3  
**Last checkpoint:** 2026-10-15T23:43:47Z

## Goal

Enhance the whole film across opening, material treatment, camera/action staging and sound dynamics; preserve narration and clean-frame constraints. Preview first, native render only after proof.

## Acceptance criteria

- [ ] Meaningful changes across all three scene groups, not just hero cells
- [ ] Same narration, safety qualifiers and clean composition
- [ ] Preview and current-source tests before native rendering; verified final master and separate delivery

## Exact next action

Start one run-v8.sh native pipeline with restored venv interpreter, record process ID, wait for actual-master gate and encoded review before delivery.

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261016-002/0003-20261015T234347Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
