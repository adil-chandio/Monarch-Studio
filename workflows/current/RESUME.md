# Resume capsule — WF04-CHAOS04

**Status:** `active`  
**Title:** WF-04 · MONARCH CHAOS VIDEO 4 · cinematic motion edit of supplied raw footage  
**Style:** `monarch-face-chaos`  
**Checkpoint sequence:** 0  
**Last checkpoint:** none

## Goal

Produce CHAOS 04: grade, light leaks, HUD, beat-synced cut rhythm, crown emblem ending and mastered audio from the supplied 44.4s raw reference, matching the delivered CHAOS 03 gate standard (1080x1920, 30fps, 48k stereo, -16 LUFS, TP<=-1.5).

## Acceptance criteria

- [ ] 1080x1920 30fps H.264 master with 48kHz stereo mastered audio
- [ ] Real measured gate report (no invented passes)
- [ ] Verified checksum and Drive upload with independent read-back

## Exact next action

Build CHAOS 04 grade/HUD/emblem assets and render the master.

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
