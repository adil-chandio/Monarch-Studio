# Resume capsule — EMS-20261012-001

**Status:** `blocked`  
**Title:** Zack-D style 3-D video (WF-02 Drive source) · tumhari reserved seat script · cloned monarch voice  
**Style:** `zackd-3d-premium (proposed; no style yet)`  
**Checkpoint sequence:** 4  
**Last checkpoint:** 2026-10-12T02:33:31Z

## Goal

Build a premium 3-D animated video in Zack D Films style from the Drive source files, same topic/script (Tumhari Reserved Seat), with the user's monarch voice; report real capability limits honestly.

## Acceptance criteria

- None recorded.

## Exact next action

Await user: (a) provide/confirm MuAPI key entry in the app UI for generation, (b) build EffectCraft on a machine with Rust, or (c) choose next render path.

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261012-001/0004-20261012T023331Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
