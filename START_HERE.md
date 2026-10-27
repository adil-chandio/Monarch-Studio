# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261027-WF06-H3-LAB`
- **Status:** `active`
- **Title:** WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan
- **Next action:** Poll Drive 05 · Projects/m-test-01/shots for the rendered mp4; when it exists, ingest the ZIP or bytes, then finish -> deliver.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
