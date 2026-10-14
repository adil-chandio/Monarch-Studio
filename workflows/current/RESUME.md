# Resume capsule — EMS-20261014-001

**Status:** `waiting_external`  
**Title:** WTF-30 format · 20–30 s impossible-moment AI cinema for social — doctrine, brain format, concept slate  
**Style:** `studio-operation`  
**Checkpoint sequence:** 1  
**Last checkpoint:** 2026-10-14T16:58:38Z

## Goal

Answer 'kaise hoga yeh sab' durably: define the 20–30 second vertical impossible-moment short format (WTF-30) for showing AI creativity on social media — format law, second-by-second structure, impossible-moment taxonomy, the studio tool pipeline (brain DNA → AI plates → procedural animation → VO → sound → gates → delivery), format-specific gates, series strategy, and a first concept slate for the user to pick from.

## Acceptance criteria

- [ ] A permanent doctrine document for the WTF-30 format exists under studio/editor-brain and is linked from MONARCH_EDITOR_BRAIN.md.
- [ ] brain/concept.py accepts --format wtf30 with format-aware targets and freshness-gate rules; status/propose/gate run without error and existing short/film behaviour is unchanged.
- [ ] A concept slate of original impossible-moment ideas is written, each checked against currently blocked worlds/signatures in the brain registry.
- [ ] Honest feasibility is recorded: which steps run inside this studio (procedural render, AI plates, generated VO, synthesized sound) and what must be installed (numpy, Pillow, ffmpeg) before the first render.
- [ ] The user receives the plan in chat and picks a concept or orders changes; the exact next action is recorded in RESUME.md.

## Exact next action

Wait for the user to pick a slate number (doctrine §13) or send 'WTFGO <topic>' plus a style (paper = WF-01 / noir = WF-03); then: pip install --user --break-system-packages numpy pillow scipy imageio-ffmpeg → concept.py propose --format wtf30 --dur 25 → fill law/moment/meaning → three-still look sheet for approval.

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261014-001/0001-20261014T165838Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
