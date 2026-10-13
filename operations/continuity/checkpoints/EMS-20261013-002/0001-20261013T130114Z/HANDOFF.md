# Resume capsule — EMS-20261013-002

**Status:** `completed`  
**Title:** WF-04 · Monarch Face · Chaos Video 1 v2 (Canonical Boss Wardrobe & Face + Dynamic Body Movement + Crown Finale)  
**Style:** `monarch-face-chaos`  
**Checkpoint sequence:** 1  
**Last checkpoint:** 2026-10-13T13:01:14Z

## Goal

Upgrade Chaos Video 1 to v2: fix character face, body proportions, and signature wardrobe (fitted black shirt + charcoal blazer / canonical look from REAL face v5 & REAL body v2), add dynamic body/head/hand movement across shots, elevate VFX to next-level tabahi, and place a bold golden Crown (👑) directly above MONARCH STUDIO in the finale.

## Acceptance criteria

- [ ] 100% locked face/body/wardrobe consistency across all shots, organic dynamic body & head movement, next-level VFX enhancements, iconic Crown (👑) above MONARCH STUDIO in finale, 21/21 gates passed, uploaded to Google Drive.

## Exact next action

Await user review or next workflow trigger

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261013-002/0001-20261013T130114Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
