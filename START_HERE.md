# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `WF05-20261026-REF-INTAKE`
- **Status:** `waiting_external`
- **Title:** WF-05 · resume supplied reference work in this repository session
- **Next action:** Ask user: attach the MP4 (Route A) or confirm topic-only start (Route B); on receipt decode frames with ffmpeg before any content claim.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
