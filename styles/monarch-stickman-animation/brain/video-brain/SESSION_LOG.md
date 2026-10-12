# Monarch Stickman Animation (WF-01 Paper Cinema) · video brain

Style `monarch-stickman-animation` · workflow WF-01. Created 2026-10-13 03:17 PKT.

## Session log (append-only)

Use `tools/brain.py` to add entries. Do not edit old entries.
## S-001 · 2026-10-13 03:19 PKT

- **Request:** WF-01 first: improve to next level with paper-cinema concept (paper timetable, reserved seat, page turns, parallax)
- **Action:** Built lookdev in Blender Cycles (270x480) for paper layers, title, shade figure and ticket. Iterated on world and key light
- **Result:** Paper parallax reads. Look still flat grey and the stick figure reads cheap. Not accepted
- **Files:** `tools/render/blender-vertical/wf_scenes.py`

## S-002 · 2026-10-13 03:36 PKT

- **Request:** Make one next-level 10 s WF-01 Paper Cinema video, any topic, with script (user chose WF-01)
- **Action:** Chose topic Har subah ki pehli 10 minute (paper timetable, reserved seat). Wrote tools/render/blender-vertical/wf01_paper10s.py (timetable and ticket textures via PIL, bevelled paper cards, seated cut-out figure, page flip on a Z pivot). Fixed import order (wf_scenes before bpy). Three lookdev stills r7 at 1.5/5.0/8.5 s, fixed texture rotation and wall size, one more still r7b
- **Result:** Not premium. Timetable text is not legible at 270x480, figure is crude primitives, key light too weak. Full render, voice and sound NOT done. Stopped before a 300-frame run
- **Files:** `tools/render/blender-vertical/wf01_paper10s.py`

## S-003 · 2026-10-13 03:42 PKT

- **Request:** Improve shade_respect_v2 (Drive 1fu_g2HTNZVRqE3XBKdUKZoj6O8tIdkpu) to the next level. User chose: full 3D rebuild, voice-02 ur-PK
- **Action:** Downloaded the Drive file to /tmp (not the repo). Extracted contact sheets at 2-73 s. Read VIDEO_RESPECT_NOTES and CHARACTER_SPEC. Found src/shade.py is a 2D PIL drawing of a 3D skeleton, not a 3D mesh. Timed Blender at 540x960 and 1080x1920 on this sandbox (2 CPU, 3 GB RAM)
- **Result:** Reference video is 75 s, 1080x1920, 30 fps, 9 chapters, gate 19/19. A 3D rebuild needs a new SHADE mesh and rig in Blender. Measured ~6-8 s per frame at 540x960 and ~35 s per frame at 1080x1920 (32 spp), so the full 2256-frame 1080p render is ~22 h CPU here. Not started
- **Files:** `tools/render/blender-vertical/wf01_paper10s.py`

