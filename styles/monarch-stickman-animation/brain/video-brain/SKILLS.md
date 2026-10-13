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

## K-004 · 2026-10-13 · Run the respect2/3 pipeline outside the repo

- **When to use:** Any SHADE short rebuild
- **How:** Make /home/user/src (repo src), /home/user/fonts (repo fonts), /home/user/build and /home/user/assets (in /tmp) as symlinks. Put PATH=/tmp/venvs/render/bin first. Shards: python3 src/respect2.py A B out.mp4, about 0.35 s per frame at 1080x1920
- **Evidence:** 48-frame test shard rendered in 19 s, output 1080x1920 30 fps

## K-005 · 2026-10-13 · cut-safe camera blend

- **When to use:** any shot-based edit with a per-shot camera (zoom, pan) and a transition between shots
- **How:** in the transition window, blend the two cameras, each evaluated at its own shot progress u (clamped), with the same eased p as the picture. Never take the new shot's u=0 camera at the cut
- **Evidence:** motion-energy spike 17.4 at the cut removed; max camera step 0.0075/frame

## K-006 · 2026-10-13 · wide stereo from a mono-heavy mix

- **When to use:** stereo corr above 0.8 after music + TTS mix
- **How:** Haas 14 ms on the wide layers, detuned L/R pads, then ffmpeg extrastereo=m=3.0 on the mix (side only; mono sum unchanged). Check mid RMS before/after
- **Evidence:** lr_corr 0.95 -> 0.648; mid RMS unchanged 3334.67 before/after

