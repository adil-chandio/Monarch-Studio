# Resume capsule — EMS-20261014-002

**Status:** `waiting_external`  
**Title:** WTF-30 #1 · THE GRAVITY OF THE PHONE · 20 s vertical impossible-moment short (paper/ink, WF-01 identity)  
**Style:** `monarch-stickman-animation`  
**Checkpoint sequence:** 5  
**Last checkpoint:** 2026-10-14T20:22:59Z

## Goal

Produce the first WTF-30 video: a 20.0 s 1080x1920 30 fps paper/ink short in which every object in a bedroom is pulled toward a glowing phone as if it were a planet (law: gravity), the Monarch hero holds the doorframe, lets go, flips the phone face-down and everything drops flat; meaning line 'Phone ulta. Zindagi seedhi.'; loop seam back to frame 1; sound designed, mastered at -14 LUFS; passes gate #20 (wtf30 rows) and the frame/mix WTF gates; promoted into styles/monarch-stickman-animation/films/.

## Acceptance criteria

- [ ] DNA from concept.py propose --format wtf30 with law_broken=gravity, signature radial_gravity_release, world phone_planet_room; gate #20 PASS before final mux.
- [ ] 20.0 s master 1080x1920 30 fps H.264 + AAC 48 kHz; impossible moment onset within 4.8-8.0 s in one uncut shot >= 3 s; meaning line <= 7 words at 14-18 s; loop seam last frame vs frame 1 <= 6/255 or designed match.
- [ ] Measured gate report: frame-1 motion, no still > 0.4 s, luma steps, silence hole 0.3-0.6 s before onset, integrated loudness -14 +/- 1 LUFS, TP <= -1 dBTP, 4:5 safe crop proof.
- [ ] Permanent package under styles/monarch-stickman-animation/films/gravity-of-the-phone/ with DNA, renderer, audio build, gate program, look sheet, event ledger, receipts; brain commit; knowledge index updated.

## Exact next action

Wait for the user's verdict on v4 (Drive 1Zi87F-qYb-tGENwdPdMGeP4jVAbeggGl). Accepted → continuity.py complete and archive the slot. Notes → iterate in workflows/current/payload/gravity-of-the-phone/ (render halves → build → gate → promote → registry → sync). Do not redo v1–v4 or the cp0004 platform sync.

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261014-002/0005-20261014T202259Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
