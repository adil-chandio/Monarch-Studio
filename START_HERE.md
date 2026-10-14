# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `WF04-20261014-NOJELLY`
- **Status:** `waiting_external`
- **Title:** Monarch Face: original scenes and articulated motion, no plate warps
- **Next action:** Preserve completed character/shot designs and separately uploaded crown outro. Recover the exact outro via VIDEO_COMPONENTS.json if local media disappears; never re-render completed components merely on Continue. Remaining work is actual new-character motion for beats 01–08 plus final assembly/audio-to-action edit; photoreal motion renderer remains unavailable and Runway/Replicate connectors are unsupported. Do not substitute old live-action footage, still warps or the rejected mannequin.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
