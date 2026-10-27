# Resume capsule — EMS-20261027-WF06-H3-LAB

**Status:** `active`  
**Title:** WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan  
**Style:** `minimax-h3-video`  
**Checkpoint sequence:** 1  
**Last checkpoint:** 2026-10-27T13:50:33Z

## Goal

Document how to run MiniMax-H3 from Google Colab, deliver a runnable notebook + stdlib CLI, and plan the WF-04 Monarch-face to H3 to WF-05 pipeline

## Acceptance criteria

- [ ] knowledge base (model facts, Colab runbook, prompting, routes/cost, face integration); runnable validated Colab notebook; offline-tested CLI; registries + manifest updated; studio validate green

## Exact next action

Run the L1 identity test: add Monarch reference crops + voice ref to styles/minimax-h3-video/assets/refs/, then estimate and run one 5 s 768P Ref2VA shot with MINIMAX_API_KEY

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261027-WF06-H3-LAB/0001-20261027T135033Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
