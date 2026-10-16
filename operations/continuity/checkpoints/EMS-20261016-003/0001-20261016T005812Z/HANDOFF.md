# Resume capsule — EMS-20261016-003

**Status:** `active`  
**Title:** WF-02 permanent style memory and cross-platform preservation  
**Style:** `monarch-zackd-3d`  
**Checkpoint sequence:** 1  
**Last checkpoint:** 2026-10-16T00:58:12Z

## Goal

Consolidate available V2–V8 sources, history, mistakes/fixes, creative workflow and new-chat handoff; verify Drive knowledge archive and push current session branch to GitHub.

## Acceptance criteria

- [ ] Evidence-linked comprehensive style handbook, machine-readable contract and onboarding
- [ ] Available transcripts/journals preserved with explicit coverage limits
- [ ] Test/validation pass, actual Drive and GitHub receipts; prior versions preserved

## Exact next action

Build/verify recovery ZIP and consolidated human-readable handbook, create knowledge subfolder under verified WF02 parent, upload/read-back, then validate/commit/push session branch and record remote SHA.

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261016-003/0001-20261016T005812Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
