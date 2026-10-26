# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `WF04-REF-INTAKE-2`
- **Status:** `waiting_external`
- **Title:** WF-04 · CHAOSGO reference inspection (no production) — awaiting user decision
- **Next action:** User decides: (a) run notebook on Colab/Kaggle free GPU now, or (b) approve Track C hybrid starting with CPU 3D base, or (c) ask for history-rewrite/make-private to purge third-party master from public git history. Also still pending: film number/length, character input, masked-vs-open face, and G1 shotlist approval.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
