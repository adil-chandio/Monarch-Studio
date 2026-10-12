# Tumhari Reserved Seat: premium 3-D video (9:16)

**Status:** in progress. Not accepted. Lookdev stills are test quality. No 240-frame render yet.

## What this project makes

Three 10-second 9:16 vertical films, one per approved concept, on the same script as the Tumhari Reserved Seat film (74 s, Roman Urdunglish). Each style has its own editing, animation and sound.

| Style | Concept | Status |
|---|---|---|
| WF-01 Paper Cinema | Paper timetable with a reserved seat | Lookdev test quality. Priority. |
| WF-02 Zack-D 3D Power | 20 min × 90 days = 30 hours, one cube per second, voxel 3-D text | Lookdev test quality. Next. |
| WF-03 Midnight Platform Noir | Reserved ticket as a timer that runs out | Lookdev test quality. After WF-01. |

## Files in this folder

| File | What it holds |
|---|---|
| `RESUME.md` | Start here: where things are, start commands, next action |
| `PROCESS_LOG.md` | Step-by-step history: what was done, with which tool, what came out |
| `DECISIONS.md` | Standing instructions, locked concepts, consequential decisions, open questions |
| `TOOLS.md` | Every tool, version, command, and the dead ends to avoid |
| `SKILLS.md` | Skills learned in this project, where they live, what is missing |
| `ARTIFACTS.md` | Index of big files kept outside the workspace (Drive links, sizes, checksums) |

## Where the code and skills live

- Render scripts: `tools/render/blender-vertical/`, `tools/render/zackd3d-demo/`, `tools/render/react-bits-preview/`
- Bootstrap and vendor restore: `tools/bootstrap/setup_3d.sh`, `tools/vendor/materialize.sh`
- Render method and blockers: `docs/runbooks/3D_VIDEO_PIPELINE.md`
- Vendor pins: `vendor/` (submodules), `docs/VENDOR_INTEGRATION.md`
- Skill text copies: `docs/skills/vendored/`

## Visibility

The repository `adil-chandio/Monarch-Studio` is **public**. Do not commit private voice samples, credentials, or unreleased material here.
