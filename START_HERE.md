# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261014-001`
- **Status:** `waiting_external`
- **Title:** WF-04 · Chaos Video 1 v3 · true-3D character remake (no face warp)
- **Next action:** Await a textured 3D head/body scan or neutral unfiltered face/full-body 360-degree capture, and clarify whether photo-derived PBR textures on true 3D meshes are permitted. The user did not answer those clarifications. Recreate ignored assets/venv if needed, then replace prototype hair/neck/blazer/hands with professional geometry, inspect an actual 3D motion proof with the user, and only after visual approval render the complete reference-timed Chaos 1 v3 master with crown-above-title and quality gates. Never substitute v2 image plates or mark remote delivery synced before a real video exists.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
