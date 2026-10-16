# Resume capsule — EMS-20261016-003

**Status:** `active`  
**Title:** Monarch Cam — channel forensic audit + forward content plan  
**Style:** `channel-strategy`  
**Checkpoint sequence:** 0  
**Last checkpoint:** none

## Goal

Deep forensic analysis of the Monarch Cam YouTube channel (@monarch-cam, UCfYdmsLO4Q8_IHklTyYieLg) from live channel data, plus an evidence-backed 90-day content plan with packaging, cadence, compliance and kill criteria.

## Acceptance criteria

- [ ] Permanent forensic audit + data snapshot + content plan committed under channel/, all numbers traceable to captured evidence, gaps marked as unknown not invented.

## Exact next action

Write channel/ deliverables and commit.

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
