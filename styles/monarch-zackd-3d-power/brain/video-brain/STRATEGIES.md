# Monarch Zack-D 3D Power · video brain

Style `monarch-zackd-3d-power` · workflow WF-02. Created 2026-10-13 03:17 PKT.

## Strategies and decisions (append-only)

Use `tools/brain.py` to add entries. Do not edit old entries.
## ST-001 · 2026-10-13

- **Decision:** Use Blender Cycles (CPU) for the 3-D look, not Mitsuba
- **Alternatives rejected:** Mitsuba 3 demo (640x360, 12 fps, 6 s) was used only as a proof. Its look and speed did not fit the 9:16 premium target
- **Outcome:** Blender lookdev reached readable text and a full tower. Chrome still open

## ST-002 · 2026-10-13

- **Decision:** Keep the Blender scene builders in the shared tools/render/blender-vertical folder for now, not inside the style
- **Alternatives rejected:** Move the renderer into styles/monarch-zackd-3d-power/src now
- **Outcome:** Pending a split. WF-01 and WF-03 use the same builders. Revisit when a WF-02-only renderer is needed

## ST-003 · 2026-10-13

- **Decision:** Trigger POWERGO <topic> approved by the user on 2026-10-13. Style state stays PROPOSED_LOOKDEV until an accepted film exists
- **Alternatives rejected:** Custom token (user declined)
- **Outcome:** Trigger active in both registries

