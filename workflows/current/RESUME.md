# Resume capsule — EMS-20261014-001

- **Status:** `active`
- **Title:** WF-04 · Monarch Face · Chaos Video 2 (reference-matched next-level cut) + anti-stop continuity hardening
- **Style:** `monarch-face-chaos`
- **Checkpoint sequence:** 0
- **Last checkpoint:** none

## Goal

User (2026-10-14): make a video like the Drive reference VID_20261013_050529_146.mp4 with his canonical face/wardrobe, more body movement, next-level chaos/realism, ending on the crowned MONARCH STUDIO logo; and definitively fix why the session 'keeps stopping'.

## Acceptance criteria

- [ ] Cause of repeated stops identified with measurements and recorded; repo back under the snapshot cap; render env bootstrap + branch recovery + budget tools committed; Chaos Video 2 built from the WF-04 engine, gated 21/21, uploaded to Drive with MD5, synced and checkpointed.

## Exact next action

Render the WF-04 v2 pipeline verification pass, then author and render Chaos Video 2.

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
