# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `WF04-20261014-NOJELLY`
- **Status:** `waiting_external`
- **Title:** Monarch Face: original scenes and articulated motion, no plate warps
- **Next action:** If local media is absent again, download the recorded design ZIP and run recover_design_assets.py; do not ask for the master or regenerate art. Do not repeat finished design work. The Arena pending-question/interruption requires platform-side investigation (support handoff in operations/incidents/WF04-service-ui-handoff.md); actual new-character motion still needs a capable video-generation/rig pipeline not currently exposed.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
