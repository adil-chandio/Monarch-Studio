# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261027-WF06-H3-LAB`
- **Status:** `active`
- **Title:** WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan
- **Next action:** Run the L1 identity test: add Monarch reference crops + voice ref to styles/minimax-h3-video/assets/refs/, then estimate and run one 5 s 768P Ref2VA shot with MINIMAX_API_KEY
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
