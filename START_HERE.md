# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261016-003`
- **Status:** `syncing`
- **Title:** WF-02 permanent style memory and cross-platform preservation
- **Next action:** Commit/push library and preserved sources to arena/eba29c7c-monarch-studio, verify remote content SHA, then record actual sync and archive preservation task in follow-up receipt commit; no main merge.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
