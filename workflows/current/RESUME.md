# Resume capsule — EMS-20261013-002

- **Status:** `active`
- **Title:** WF-04 · Monarch Face · Chaos Video 1 v2 (Canonical Boss Wardrobe & Face + Dynamic Body Movement + Crown Finale + Full 5-Platform Sync)
- **Style:** `monarch-face-chaos`
- **Checkpoint sequence:** 0
- **Last checkpoint:** none

## Goal

Finalize and polish Chaos Video 1 v2 with enhanced 2.5D body/head/hand movement, clean golden flash transition into the 👑 MONARCH STUDIO finale, 21/21 gates, and full synchronization across Google Drive, Notion, Linear, Google Docs, and GitHub.

## Acceptance criteria

- [ ] 21/21 gates passed, uploaded to Google Drive with MD5 verification, and synced across GitHub, Google Drive, Notion, Linear, and Google Docs.

## Exact next action

Enhance body motion amplitude & golden flash transition, render & gate-verify, upload to Drive, and sync Notion/Linear/Docs/GitHub

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
