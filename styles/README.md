# Permanent editing-style library

`styles/` is the permanent, searchable source of truth for every Editing Monarch editing/animation style. A style receives a human-readable, stable name and keeps **all** of its implementation, assets, prompts, scripts, render logic, audio logic, tools, measurements, gates, decisions, failures, fixes, releases and provenance inside its own directory.

Current styles:

| Style ID | Name | Workflow trigger | Permanent path |
|---|---|---|---|
| `monarch-stickman-animation` | Monarch Stickman Animation | `SHADEGO <topic>` | [`monarch-stickman-animation/`](monarch-stickman-animation/) |
| `monarch-noir-film` | Monarch Noir Film | `NOIRGO <topic>` | [`monarch-noir-film/`](monarch-noir-film/) |
| `monarch-zackd-3d-power` | Monarch Zack-D 3D Power (proposed, lookdev) | `POWERGO <topic>` (proposed) | [`monarch-zackd-3d-power/`](monarch-zackd-3d-power/) |

## Video brain (every style)

Each style has a `brain/video-brain/` folder: the style's mindset, toolchain, production pipeline, next-level backlog, and append-only ledgers (sessions, problems and fixes, skills, strategies, videos). The standard is in [`BRAIN_STANDARD.md`](BRAIN_STANDARD.md). The CLI is `tools/brain.py`. Start any style with `python3 tools/brain.py resume <style-id>`.

## Hard boundary

- `styles/` contains permanent knowledge and completed/released work.
- `workflows/current/` contains only the one task currently running.
- When the current task is accepted, `continuity.py complete` promotes its durable outputs into the selected style and empties the active payload.
- A style is resolved by stable style ID plus external authority IDs—never by a similar display name.

The machine-readable catalogue is [`registry.json`](registry.json). The required structure for every future style is documented in [`../docs/STYLE_LIBRARY_STANDARD.md`](../docs/STYLE_LIBRARY_STANDARD.md).