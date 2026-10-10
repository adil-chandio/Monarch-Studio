# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261011-001`
- **Status:** `waiting_external`
- **Title:** Style Library + Crash-Proof Continuity System v1
- **Next action:** User supplies the GitHub repository URL (and confirms write access); then set origin, push main and tag continuity-v1, mark GitHub synced in the latest outbox, and complete/archive EMS-20261011-001.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
