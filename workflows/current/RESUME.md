# Resume capsule — WF05-20261026-REF-INTAKE

**Status:** `waiting_external`  
**Title:** WF-05 · resume supplied reference work in this repository session  
**Style:** `premium-motion-editing`  
**Checkpoint sequence:** 1  
**Last checkpoint:** 2026-10-26T19:27:22Z

## Goal

Continue the WF-05 premium motion editing work shown in the supplied chat transcript: verify the supplied Drive reference, establish local capability, and take the reference through analysis into an edit delivery from this repository.

## Acceptance criteria

- [ ] Reference identity verified from a real connector result
- [ ] Local pipeline capability proven in this environment (decode/encode path)
- [ ] Reference footage staged locally or an explicit alternative confirmed by the user
- [ ] Style analysis grounded in decoded frames, not guessed from metadata

## Exact next action

Ask user: attach the MP4 (Route A) or confirm topic-only start (Route B); on receipt decode frames with ffmpeg before any content claim.

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
- Latest checkpoint package: `operations/continuity/checkpoints/WF05-20261026-REF-INTAKE/0001-20261026T192722Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
