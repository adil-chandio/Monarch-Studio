# Resume capsule — EMS-20261014-001

- **Status:** `active`
- **Title:** WF-04 · Chaos Video 1 v3 · true-3D character remake (no face warp)
- **Style:** `monarch-face-chaos`
- **Checkpoint sequence:** 1
- **Last checkpoint:** 2026-10-13T19:18:02Z

## Goal

Rebuild Chaos Video 1 from an actual rigged 3D Monarch character instead of warped still plates; match the supplied reference edit and locked REAL face v5 / body v2, eliminate jelly face deformation, deliver an honest cinematic 3D result with crown above MONARCH STUDIO.

## Acceptance criteria

- [ ] The face is rendered from a stable 3D head mesh (no 2.5D still-image warp); body and wardrobe use 3D meshes with deliberate head/torso/hand keyframes and physically coherent camera/light movement.
- [ ] Reference beats and locked identity/wardrobe are evaluated side by side; user can inspect a short 3D likeness/animation proof before any full master is labeled final.
- [ ] Final 1080x1920 30fps master, sound, crown over MONARCH STUDIO, objective and visual QA; preserve previous v2 unchanged until v3 is approved.

## Exact next action

Inspect reference timeline and locked identity sources; verify/install 3D renderer; scope likeness proof before full render.

## Running processes

- None recorded.

## Recovery command

```bash
python3 tools/continuity.py resume
```

## Durable evidence

- Active state: `workflows/current/ACTIVE_TASK.json`
- Hash-chained action journal: `workflows/current/JOURNAL.jsonl`
- Visible user/assistant transcript: `workflows/current/CHAT_TRANSCRIPT.jsonl`
- Active payload only: `workflows/current/payload/`
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261014-001/0001-20261013T191802Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
