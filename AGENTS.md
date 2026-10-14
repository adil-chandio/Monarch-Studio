# Mandatory instructions for every Arena agent

Before doing any work in this repository:

1. Run `python3 tools/continuity.py resume`.
2. Treat `workflows/current/ACTIVE_TASK.json` and the latest checkpoint as authoritative.
3. Log the visible user message verbatim with `continuity.py log --kind user`.
4. Never restart a completed operation or discard a newer active task because an older chat summary appears.
5. Record every material action/result/error and every long-running process ID.
6. Checkpoint before/after long operations, after material results, on errors, before ending the turn, and at least every 55 minutes while active.
7. Keep permanent accepted knowledge inside the named style under `styles/`; keep only running work in `workflows/current/payload/`.
8. Do not mark remote sync complete without updating the target's `SYNC.json` entry with its real ID/result.
9. Do not commit credentials, hidden system instructions, private connector tokens or raw sensitive identity media.
10. Run `python3 tools/studio.py validate` before a milestone commit.

11. Starting a finite render is not delivery. Stay with the operation through completion, encoding and inspection where feasible; use a blocking process wait rather than ending with only “working on it.” If interrupted, record the real process ID and exact resumable command.
12. Distinguish platform/service errors from local program errors. Do not claim to have repaired Arena's service, promise uninterrupted execution, or assert that every turn resets branches/files without evidence. A screenshot of a service-error banner does not establish its backend cause.
13. A technical gate pass is not visual acceptance. In WF-04, the user rejected recycled still plates and rubber/jelly body warps. Do not reuse that approach or call a static-picture warp, live-action composite, or rough motion study a new photoreal 3D performance.
14. Exclude private identity media, model/download caches and private deliverables from both Git AND the studio manifest. Preserve recovery IDs/hashes and small source/records instead.

If a response/process stops, query the recorded process and execute the exact next action in `RESUME.md`; do not begin again from zero.