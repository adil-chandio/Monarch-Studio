# Resume capsule — NONE

**Status:** `idle`
**Title:** No active task
**Style:** `studio-operation`
**Checkpoint sequence:** 0
**Last checkpoint:** none

## Goal

No goal recorded.

## Acceptance criteria

- None recorded.

## Exact next action

Start the next task with continuity.py init.

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
- Latest checkpoint package: `none`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
