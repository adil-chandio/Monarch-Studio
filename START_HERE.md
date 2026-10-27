# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `WF04-REF-INTAKE-2`
- **Status:** `waiting_external`
- **Title:** WF-04 · CHAOSGO reference inspection (no production) — awaiting user decision
- **Next action:** Get user's creative verdict on the preview. Then either (a) push quality: 1080p full-res render of the same scene (21.9 h measured on this box) or GPU polish via Wan2.2-Animate using this animatic as the driving video, (b) add the 22-blendshape face rig / open face if they want it unmasked, (c) fix the 2 remaining weak setups, (d) delete or keep the unapproved CHAOS 04 Drive files and decide the git-history purge.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
