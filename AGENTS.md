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

If a response/process stops, query the recorded process and execute the exact next action in `RESUME.md`; do not begin again from zero.

## WF-02 / WF2 style discovery

When the user requests WF2, Zack d3d animation or Monarch3D Explainers, read `styles/monarch-zackd-3d/START_HERE.md`, its local `AGENTS.md`, `STYLE_DNA.json`, `QUALITY_CONTRACT.json` and master playbook before proposing/producing work. Run `python3 tools/wf02.py audit` and `python3 tools/wf02.py brief "<topic>"`. This is the separate live WF-02 style, not the legacy Powerful Personality snapshot. Preserve the user no-clutter correction and current delivered baseline. Do not claim full chat recovery, automatic cross-chat context/voice transfer, new rendering or artistic/clinical perfection merely from onboarding.
