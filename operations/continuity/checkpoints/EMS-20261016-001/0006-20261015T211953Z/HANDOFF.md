# Resume capsule — EMS-20261016-001

**Status:** `active`  
**Title:** KAANTA · Organic Motion v7 — render and delivery  
**Style:** `monarch-zackd-3d`  
**Checkpoint sequence:** 6  
**Last checkpoint:** 2026-10-15T21:19:53Z

## Goal

Finish the current V7 native render, verify actual encoded master, deliver a separate version on Drive and permanently preserve editable source without overwriting V6.

## Acceptance criteria

- [ ] 1080x1920, 30fps, 30.5s, all 915 frames decode
- [ ] Same four voice WAVs, script, captions and medical safety qualifiers preserved
- [ ] V7 organic membrane A/B, deterministic return and focus/caption tests pass
- [ ] Actual-master technical gates and sampled visual review pass
- [ ] Separate Drive master/source uploads verified by size and checksum, real IDs in SYNC.json
- [ ] Permanent style source and registries updated; previous releases preserved

## Exact next action

Review build/QA_CONTACT_SHEET.jpg and QA_FAST_ACTIONS.jpg; then upload verified master/source to folder 1YPpOkcm_hh843HI4V69cQL5rQrFL5tMI and permanently register V7.

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261016-001/0006-20261015T211953Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
