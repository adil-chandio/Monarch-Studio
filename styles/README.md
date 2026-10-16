# Permanent editing-style library

`styles/` is the permanent, searchable source of truth for every Editing Monarch editing/animation style. A style receives a human-readable, stable name and keeps **all** of its implementation, assets, prompts, scripts, render logic, audio logic, tools, measurements, gates, decisions, failures, fixes, releases and provenance inside its own directory.

Current styles:

| Style ID | Name | Workflow trigger | Permanent path |
|---|---|---|---|
| `monarch-stickman-animation` | Monarch Stickman Animation | `SHADEGO <topic>` | [`monarch-stickman-animation/`](monarch-stickman-animation/) |
| `monarch-zackd-3d` | Monarch 3D Explainers · WF-02 | `WF2 <topic or reference>` | [`monarch-zackd-3d/`](monarch-zackd-3d/) |
| `monarch-noir-film` | Monarch Noir Film | `NOIRGO <topic>` | [`monarch-noir-film/`](monarch-noir-film/) |

## Hard boundary

- `styles/` contains permanent knowledge and completed/released work.
- `workflows/current/` contains only the one task currently running.
- When the current task is accepted, `continuity.py complete` promotes its durable outputs into the selected style and empties the active payload.
- A style is resolved by stable style ID plus external authority IDs—never by a similar display name.

The machine-readable catalogue is [`registry.json`](registry.json). The required structure for every future style is documented in [`../docs/STYLE_LIBRARY_STANDARD.md`](../docs/STYLE_LIBRARY_STANDARD.md).