# Resume capsule — EMS-20261014-001

**Status:** `rendering`  
**Title:** WF-02 Splinter 3D reference-based Urdu-English film  
**Style:** `monarch-zackd-3d`  
**Checkpoint sequence:** 6  
**Last checkpoint:** 2026-10-14T21:07:18Z

## Goal

Study the supplied How Splinters Get Unstuck video and the live WF-02 Drive folder, produce an original accurate 3D explainer in easy Urdu-English, and deliver video plus source in that folder without overwriting earlier work.

## Acceptance criteria

- [ ] Reference topic and shots inspected; source lineage retained
- [ ] Actual animated 3D, not a still-image slideshow; clear easy Urdu-English narration and Roman Urdu captions
- [ ] Medical caveats and no-guaranteed-spontaneous-expulsion distinction included
- [ ] Playable rendered video checked and uploaded in the confirmed WF-02 Drive folder

## Exact next action

Wait for registered render process wf-02-3d-video-render-af896fc1. On success: .venv/bin/python workflows/current/payload/splinter-v2/src/assemble.py --reuse-audio --out .runtime/wf02-master; then gate.py on final MP4. Inspect QC sheet, upload/hash-check master and source to folder 1SqX_S44eVowdTAyBVzAFerYUYFJd6NtF, write DELIVERY_RECEIPT.json, execute PROMOTE_WF02.py and continuity.py complete --destination styles/monarch-zackd-3d/projects. Refresh manifest and run validation/tests after promotion. Never run studio clean all.

## Running processes

- `wf-02-3d-video-render-af896fc1` — WF-02 native 1080p 3D master / 732 frames — running

## Recovery command

```bash
python3 tools/continuity.py resume
```

## Durable evidence

- Active state: `workflows/current/ACTIVE_TASK.json`
- Hash-chained action journal: `workflows/current/JOURNAL.jsonl`
- Visible user/assistant transcript: `workflows/current/CHAT_TRANSCRIPT.jsonl`
- Active payload only: `workflows/current/payload/`
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261014-001/0006-20261014T210718Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
