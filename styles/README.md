# Permanent editing-style library

`styles/` is the permanent, searchable source of truth for every Editing Monarch editing/animation style. A style receives a human-readable, stable name and keeps **all** of its implementation, assets, prompts, scripts, render logic, audio logic, tools, measurements, gates, decisions, failures, fixes, releases and provenance inside its own directory.

Current styles:

| Style ID | Name | Workflow trigger | Permanent path |
|---|---|---|---|
| `monarch-stickman-animation` | Monarch Stickman Animation | `SHADEGO <topic>` | [`monarch-stickman-animation/`](monarch-stickman-animation/) |
| `monarch-noir-film` | Monarch Noir Film | `NOIRGO <topic>` | [`monarch-noir-film/`](monarch-noir-film/) |
| `minimax-h3-video` | MiniMax-H3 Generative Video (WF-06) | `H3GO <topic or shot list>` | [`minimax-h3-video/`](minimax-h3-video/) |
| `premium-motion-editing` | Premium Motion Editing (WF-05) | `MOTIONGO <topic or reference>` | [`premium-motion-editing/`](premium-motion-editing/) |

**Generation engine:** all AI video generation for these styles runs through the studio's own
`tools/videogen.py` (VIPER-1) — see [`../docs/VIDEOGEN.md`](../docs/VIDEOGEN.md). Engine knowledge lives in
`minimax-h3-video/`; finish/typography stays in `premium-motion-editing/`.

## Hard boundary

- `styles/` contains permanent knowledge and completed/released work.
- `workflows/current/` contains only the one task currently running.
- When the current task is accepted, `continuity.py complete` promotes its durable outputs into the selected style and empties the active payload.
- A style is resolved by stable style ID plus external authority IDs—never by a similar display name.

The machine-readable catalogue is [`registry.json`](registry.json). The required structure for every future style is documented in [`../docs/STYLE_LIBRARY_STANDARD.md`](../docs/STYLE_LIBRARY_STANDARD.md).
## WF-05 · Premium Motion Editing (2026-10-15)

Permanent style: `styles/premium-motion-editing/`; trigger `MOTIONGO <topic or reference>`. Its current production policy retains V5 clean layout and accepted V6 motion/depth/transition/sound, rejecting the V6 bottom caption pills. Source history, a 17-chapter codex, reusable clean compositor, templates and regression tests are indexed in that style. Other workflows and historical identities are preserved.
