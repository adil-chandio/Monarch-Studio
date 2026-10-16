# Resume capsule — EMS-20261014-001

**Status:** `syncing`  
**Title:** WF-02 Splinter 3D reference-based Urdu-English film  
**Style:** `monarch-zackd-3d`  
**Checkpoint sequence:** 8  
**Last checkpoint:** 2026-10-14T21:24:47Z

## Goal

Study the supplied How Splinters Get Unstuck video and the live WF-02 Drive folder, produce an original accurate 3D explainer in easy Urdu-English, and deliver video plus source in that folder without overwriting earlier work.

## Acceptance criteria

- [ ] Reference topic and shots inspected; source lineage retained
- [ ] Actual animated 3D, not a still-image slideshow; clear easy Urdu-English narration and Roman Urdu captions
- [ ] Medical caveats and no-guaranteed-spontaneous-expulsion distinction included
- [ ] Playable rendered video checked and uploaded in the confirmed WF-02 Drive folder

## Exact next action

Promote checked source with PROMOTE_WF02.py and continuity.py complete; mark final Drive sync using real receipt ID 1YUZKEpAVScbVvJBlCXEQ63V9vPOKZVyF. Mark unrelated platforms not_requested, refresh manifest, run studio validate and full tests with scoped cleanup.

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261014-001/0008-20261014T212447Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
