# Monarch Stickman Animation (WF-01 Paper Cinema) · video brain

Style `monarch-stickman-animation` · workflow WF-01. Created 2026-10-13 03:17 PKT.

## Strategies and decisions (append-only)

Use `tools/brain.py` to add entries. Do not edit old entries.
## ST-001 · 2026-10-13

- **Decision:** WF-01 Paper Cinema is built on the Blender path, with the stickman v2 picture kept as the accepted base
- **Alternatives rejected:** Keep only the v2 2D enhancement pass
- **Outcome:** Blender lookdev is test quality. The accepted 74 s long-form release is separate (see knowledge INDEX)

## ST-002 · 2026-10-13

- **Decision:** Do not start the 300-frame WF-01 10 s render until the lookdev passes review (legible text, real cut-out figure, adequate key)
- **Alternatives rejected:** Render now as a test and label it as not premium (rejected: wastes 20+ min of CPU for a known-bad frame)
- **Outcome:** Pending

## ST-003 · 2026-10-13

- **Decision:** Full 3D rebuild of the 9-chapter SHADE script (user choice), voice-02 ur-PK. Start with a 10 s hook pilot at 540x960 after a SHADE 3D mesh and rig exist in Blender
- **Alternatives rejected:** 2D enhancement of shade_respect_v2 (not chosen, does not meet the 3D rule). Full 1080p render in this sandbox (rejected: about 22 h CPU)
- **Outcome:** Pending: needs SHADE 3D model and pose port from shade.py joint solve. Final 1080p render needs the user's GPU/Blender machine or several sessions

## ST-004 · 2026-10-13

- **Decision:** Enhance shade_respect_v2 in place: keep script, timeline, VO and audio chain. Add a grade and beat punch in respect3.py (env SHADE_ENH). No 3D, no new character
- **Alternatives rejected:** 3D Blender rebuild (user rejected). Full 2D rewrite (too large). Audio chain changes (not needed)
- **Outcome:** Pending: v3 gate and frame review

