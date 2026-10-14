# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `WF04-20261014-NOJELLY`
- **Status:** `active`
- **Title:** Monarch Face: original scenes and articulated motion, no plate warps
- **Next action:** Open PR from arena/ea72fe82-monarch-studio after validation and push. Do not rebuild delivered draft. Full photoreal generated 3D film needs an approved detailed avatar/action pipeline, not more image warps.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
