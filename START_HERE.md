# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261027-WF06-H3-LAB`
- **Status:** `active`
- **Title:** WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan
- **Next action:** First real reel: user supplies Monarch reference crops + a voice line (or lets Kokoro speak it); run plan -> render (free queue) -> audio (Colab) -> upscale (Colab) -> mix -> verify -> assemble, then promote to 05 · Projects/<id>/ and 06 · Masters & Receipts/.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
