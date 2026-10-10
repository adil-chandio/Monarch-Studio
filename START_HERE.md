# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261011-001`
- **Status:** `waiting_external`
- **Title:** Style Library + Crash-Proof Continuity System v1
- **Next action:** User confirms whether https://github.com/adil-chandio/Monarch-Studio is the repository and confirms push authorization; then set origin, push main + continuity-v1, verify remote HEAD, synchronize receipts, and complete/archive the task.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
