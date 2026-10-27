# Resume capsule — EMS-20261027-WF06-H3-LAB

**Status:** `active`  
**Title:** WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan  
**Style:** `minimax-h3-video`  
**Checkpoint sequence:** 21  
**Last checkpoint:** 2026-10-27T22:03:29Z

## Goal

Document how to run MiniMax-H3 from Google Colab, deliver a runnable notebook + stdlib CLI, and plan the WF-04 Monarch-face to H3 to WF-05 pipeline

## Acceptance criteria

- [ ] knowledge base (model facts, Colab runbook, prompting, routes/cost, face integration); runnable validated Colab notebook; offline-tested CLI; registries + manifest updated; studio validate green

## Exact next action

hand the owner the 3-shot reel link (voice + foley ON) as one tap

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261027-WF06-H3-LAB/0021-20261027T220329Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
