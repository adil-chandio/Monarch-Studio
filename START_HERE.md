# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `WF04-20261014-NOJELLY`
- **Status:** `waiting_external`
- **Title:** Monarch Face: original scenes and articulated motion, no plate warps
- **Next action:** Do not redo the delivered character/images or ask the user to attach the master: recover them from the verified Drive IDs in character-first/records/ASSETS.json if needed. The only remaining requested production stage is actual new-body animation and final edit via a capable temporal video-generation or detailed rig pipeline. No such direct photoreal video tool is currently exposed; do not fabricate progress with still pans, warps, old video compositing or the rejected mannequin.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
