# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `WF04-20261014-NOJELLY`
- **Status:** `rendering`
- **Title:** Monarch Face: original scenes and articulated motion, no plate warps
- **Next action:** Run composite_live.py for all 11 shots, then finish_live.py to synthesize original sound, mux, verify 1332 frames and save the video. Do not redo completed matching shots.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
