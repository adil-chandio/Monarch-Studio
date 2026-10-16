# Resume capsule — EMS-20261015-004

**Status:** `active`  
**Title:** WF-02 KAANTA v5 fast precision motion and material/sound refinement  
**Style:** `monarch-zackd-3d`  
**Checkpoint sequence:** 6  
**Last checkpoint:** 2026-10-15T15:21:42Z

## Goal

Make the clean KAANTA film noticeably more decisive and reference-paced through shorter object/camera moves, improved material/detail/colour treatment and tightly synchronized premium tactile sound; do not restore rejected clutter or speed up the narration.

## Acceptance criteria

- [ ] Preserve v2/v3/v4 and fixed Urdu narration; separate new v5 source/master in the confirmed WF-02 folder
- [ ] Quantifiably shorter approach/close/pull/move windows, C2 smooth acceleration and intentional settles; no global speed-up or optical-flow interpolation
- [ ] Material/detail and colour/lighting changes visible in actual encoded frames, not merely a filename/version change
- [ ] No HUD/panels/counters/coloured pills/UI pings/page flips; restrained type and captions retained
- [ ] Tactile cues follow the new physical action moments, music/voice hierarchy remains clear; measured completed MP4 and source uploaded/hash verified with music credit

## Exact next action

Run assemble.py --reuse-audio then gate.py on KAANTA_PRECISION_v5_FINAL.mp4; inspect encoded chapter and fast-action sheets. Present/upload/hash verify new master/source/receipt with music credit, then PROMOTE_V5/continuity completion and repo validation.

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261015-004/0006-20261015T152142Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
