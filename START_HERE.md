# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261014-002`
- **Status:** `active`
- **Title:** WTF-30 #1 · THE GRAVITY OF THE PHONE · 20 s vertical impossible-moment short (paper/ink, WF-01 identity)
- **Next action:** User review of the delivered video. If approved: continuity.py complete (archive EMS-20261014-002). If changes requested: edit src/scene.py or src/render.py, re-render only the affected half (render.py --range), build.py, gate.py, concept.py gate, re-upload.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
