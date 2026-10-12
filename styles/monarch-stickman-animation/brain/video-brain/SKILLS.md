# Monarch Stickman Animation (WF-01 Paper Cinema) · video brain

Style `monarch-stickman-animation` · workflow WF-01. Created 2026-10-13 03:17 PKT.

## Skills (append-only)

Use `tools/brain.py` to add entries. Do not edit old entries.
## K-001 · 2026-10-13 · Raking light for paper layers

- **When to use:** Paper or card layers need depth
- **How:** Narrow area light, low angle, size about 2.5, energy about 380 at 6 m. Wide bright lights wash out
- **Evidence:** Lookdev r2_wf01 vs wf01_v2

## K-002 · 2026-10-13 · Three-plane parallax with camera slide

- **When to use:** Paper cinema shots
- **How:** Three planes at different depths. Camera slides on a sine ease per cut
- **Evidence:** Lookdev r3_wf01_t6 shows depth

## K-003 · 2026-10-13 · Texture a cube face for paper cards

- **When to use:** Printed paper or timetable textures on Blender cards
- **How:** Generate the PNG with PIL in the render venv. Pre-rotate it by 90 degrees (ROTATE_90) to match the cube UV. Card = thin cube with a Bevel modifier (width 0.004, 2 segments) for edge highlight
- **Evidence:** lookdev r7b orientation corrected

