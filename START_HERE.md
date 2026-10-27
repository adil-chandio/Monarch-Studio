# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261027-WF06-H3-LAB`
- **Status:** `active`
- **Title:** WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan
- **Next action:** Owner opens the colab-test-03 link, taps the single play button, and sends the last cell or the ZIP; then mobile_ops ingest -> check -> finish.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
