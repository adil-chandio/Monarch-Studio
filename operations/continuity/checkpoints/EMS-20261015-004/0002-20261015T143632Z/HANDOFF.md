# Resume capsule — EMS-20261015-004

**Status:** `rendering`  
**Title:** WF-02 KAANTA v5 fast precision motion and material/sound refinement  
**Style:** `monarch-zackd-3d`  
**Checkpoint sequence:** 2  
**Last checkpoint:** 2026-10-15T14:36:32Z

## Goal

Make the clean KAANTA film noticeably more decisive and reference-paced through shorter object/camera moves, improved material/detail/colour treatment and tightly synchronized premium tactile sound; do not restore rejected clutter or speed up the narration.

## Acceptance criteria

- [ ] Preserve v2/v3/v4 and fixed Urdu narration; separate new v5 source/master in the confirmed WF-02 folder
- [ ] Quantifiably shorter approach/close/pull/move windows, C2 smooth acceleration and intentional settles; no global speed-up or optical-flow interpolation
- [ ] Material/detail and colour/lighting changes visible in actual encoded frames, not merely a filename/version change
- [ ] No HUD/panels/counters/coloured pills/UI pings/page flips; restrained type and captions retained
- [ ] Tactile cues follow the new physical action moments, music/voice hierarchy remains clear; measured completed MP4 and source uploaded/hash verified with music credit

## Exact next action

Start one v5 render --render --out .runtime/wf02-v5-master, record process ID. Do not edit locked index/film/motion/render/timeline/design/typeface/model during rendering. Finish cue-locked shortened/tactile SFX mix and v5 gates/docs in parallel. Then verify actual finalMP4 and upload separate v5 release with credit.

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261015-004/0002-20261015T143632Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
