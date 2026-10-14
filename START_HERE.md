# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `WF04-20261014-NOJELLY`
- **Status:** `waiting_external`
- **Title:** Monarch Face: original scenes and articulated motion, no plate warps
- **Next action:** Use the verified Drive link in records/DRIVE_DELIVERY.json if Arena viewer fails. Do not repeat rendering/upload or recreate PR #2. Await review or a capable approved high-detail character/video-generation pipeline for the still-unmet original photoreal 3D request; service banner backend cause remains unverified.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
