# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `WF04-REF-INTAKE-2`
- **Status:** `waiting_external`
- **Title:** WF-04 · CHAOSGO reference inspection (no production) — awaiting user decision
- **Next action:** Get user decision on Route A/B/C, performance video/turntable, wardrobe texture choice, film number and length, then write SHOTLIST_3D.json.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
