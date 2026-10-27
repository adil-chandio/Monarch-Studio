# Resume capsule — EMS-20261027-WF06-H3-LAB

**Status:** `active`  
**Title:** WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan  
**Style:** `minimax-h3-video`  
**Checkpoint sequence:** 4  
**Last checkpoint:** 2026-10-27T14:12:25Z

## Goal

Document how to run MiniMax-H3 from Google Colab, deliver a runnable notebook + stdlib CLI, and plan the WF-04 Monarch-face to H3 to WF-05 pipeline

## Acceptance criteria

- [ ] knowledge base (model facts, Colab runbook, prompting, routes/cost, face integration); runnable validated Colab notebook; offline-tested CLI; registries + manifest updated; studio validate green

## Exact next action

Run the first real project end to end: copy the example into workflows/current/payload/, add Monarch reference crops + one voice line, then videogen plan -> render -> verify -> assemble

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261027-WF06-H3-LAB/0004-20261027T141225Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
