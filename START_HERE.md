# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261014-002`
- **Status:** `waiting_external`
- **Title:** WTF-30 #1 · THE GRAVITY OF THE PHONE · 20 s vertical impossible-moment short (paper/ink, WF-01 identity)
- **Next action:** Wait for the user's verdict on v4 (Drive 1Zi87F-qYb-tGENwdPdMGeP4jVAbeggGl). Accepted → continuity.py complete and archive the slot. Notes → iterate in workflows/current/payload/gravity-of-the-phone/ (render halves → build → gate → promote → registry → sync). Do not redo v1–v4 or the cp0004 platform sync.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
