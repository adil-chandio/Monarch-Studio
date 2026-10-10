# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261011-001`
- **Status:** `syncing`
- **Title:** Style Library + Crash-Proof Continuity System v1
- **Next action:** Create a portable Git bundle and repository snapshot, upload both to the dedicated Drive continuity folder, mark checkpoint deliveries, then wait only for the user GitHub repository URL/authorization.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
