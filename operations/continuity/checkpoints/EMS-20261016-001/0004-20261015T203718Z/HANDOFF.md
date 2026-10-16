# Resume capsule — EMS-20261016-001

**Status:** `rendering`  
**Title:** KAANTA · Organic Motion v7 — render and delivery  
**Style:** `monarch-zackd-3d`  
**Checkpoint sequence:** 4  
**Last checkpoint:** 2026-10-15T20:37:18Z

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

Wait for existing render kaanta-v7-native-render-532769f3; inspect gate/master on completion, then separate verified Drive uploads and permanent registration. Refresh repository manifest after continuity checkpoint.

## Running processes

- `kaanta-v7-native-render-532769f3` — KAANTA V7 native render and assembly — running

## Recovery command

```bash
python3 tools/continuity.py resume
```

## Durable evidence

- Active state: `workflows/current/ACTIVE_TASK.json`
- Hash-chained action journal: `workflows/current/JOURNAL.jsonl`
- Visible user/assistant transcript: `workflows/current/CHAT_TRANSCRIPT.jsonl`
- Active payload only: `workflows/current/payload/`
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261016-001/0004-20261015T203718Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
