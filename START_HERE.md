# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `WF04-20261014-NOJELLY`
- **Status:** `waiting_external`
- **Title:** Monarch Face: original scenes and articulated motion, no plate warps
- **Next action:** Use character-first/records/ASSETS.json to recover exact existing art rather than regenerate or request it again. Actual image-to-video/detailed character animation capability is still needed for the remaining film; do not fall back to the rejected live-action composite, mannequin or photograph warps. Preserve the existing PR, update source/receipts on its same session branch, and do not claim an Arena backend repair.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
