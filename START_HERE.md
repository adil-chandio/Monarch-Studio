# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261014-001`
- **Status:** `active`
- **Title:** WF-04 · Monarch Face · Chaos Video 2 (reference-matched next-level cut) + anti-stop continuity hardening
- **Next action:** Render the WF-04 v2 pipeline verification pass, then author and render Chaos Video 2.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
