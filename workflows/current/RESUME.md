# Resume capsule — EMS-20261014-001

- **Status:** `active`
- **Title:** WF-04 · Monarch Face · Chaos Video 2 (reference-matched next-level cut) + anti-stop continuity hardening
- **Style:** `monarch-face-chaos`
- **Checkpoint sequence:** 1
- **Last checkpoint:** 2026-10-14T15:51:53Z

## Goal

User (2026-10-14): make a video like the Drive reference VID_20261013_050529_146.mp4 with his canonical face/wardrobe, more body movement, next-level chaos/realism, ending on the crowned MONARCH STUDIO logo; and definitively fix why the session 'keeps stopping'.

## Acceptance criteria

- [ ] Cause of repeated stops identified with measurements and recorded; repo back under the snapshot cap; render env bootstrap + branch recovery + budget tools committed; Chaos Video 2 built from the WF-04 engine, gated 21/21, uploaded to Drive with MD5, synced and checkpointed.

## Exact next action

Answer the user's 'why does the session keep stopping' question with the recorded rules 1-14, then ask whether Chaos Video 2 should replace or sit beside the delivered Chaos Video 1 (v1's helmet-edge bleed + gun-in-front-of-face masking are still open) and offer the next upgrade pass.

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261014-001/0001-20261014T155153Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
