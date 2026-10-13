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

## S-004 · 2026-10-13 03:52 PKT

- **Request:** Drop 3D. Stay in the same style as shade_respect_v2 and enhance it to next level, fun and tabahi
- **Action:** Set up runnable layout outside the repo (symlinks /home/user/src, build, assets, fonts to /tmp and repo). Downloaded VO assets r1-r9_fit.wav from Drive package shade_respect_v2_package.zip (16dY7R5PpdwbOZnA4nMeFJPT1QJjoQB2M). Verified repo src matches the package. Test shard 48 frames at 1080x1920 (about 0.35 s/frame). Wrote respect3.py (copy of respect2 + grade + beat punch, env SHADE_ENH). Still comparison at 7.7 s. Wrote build_respect3.sh and started the v3 build
- **Result:** Pipeline runs. Baseline rebuild stopped on purpose before finish: the default mux OUT would overwrite the reference file through the symlink. Reference md5 verified intact. v3 build running
- **Files:** `styles/monarch-stickman-animation/src/respect3.py`, `styles/monarch-stickman-animation/build_respect3.sh`

## S-005 · 2026-10-13 06:43 PKT

- **Request:** AMEER KA KUTTA v2: fix v1 failures (SHADE missing, flat car, voice gaps, radio bed, copied editing)
- **Action:** rebuilt kutta2.py (12 shots, 11 transitions, 3-plane backdrops, real car geometry, SHADE walk with leash), prep_vo_kutta.py (continuous VO), mux_kutta2.py (tonal music + tonal SFX, no noise), gate_kutta2.py; fixed camera pop at cuts, luma steps, caption legibility
- **Result:** kutta_v2.mp4 20.13 s 1080x1920 30fps; gate 20/22 pass; open: jerk_p95 2.11 (limit 2.0), drive shot has no SHADE visible; Drive 1IMkOtvmUMyKRN6xTx6GYi70w8uP2pI8o
- **Files:** `styles/monarch-stickman-animation/src/kutta2.py`, `styles/monarch-stickman-animation/src/mux_kutta2.py`, `styles/monarch-stickman-animation/src/gate_kutta2.py`, `styles/monarch-stickman-animation/src/prep_vo_kutta.py`

## S-006 · 2026-10-13 06:49 PKT

- **Request:** Continue: fix open v2 items (drive-shot SHADE, jerk)
- **Action:** masked driver in windshield, smootherstep drive easing, full re-render, gate, drive-section frame review, Drive upload v2.1
- **Result:** v2.1 Drive 18xdhJCn1YTsQ7oBf0XnsGPDMPLaoquJU; gate 21/22; jerk_p95 still marginal and documented
- **Files:** `styles/monarch-stickman-animation/src/kutta2.py`

## S-007 · 2026-10-13 19:27 PKT

- **Request:** AMEER KA KUTTA v6 finish: 3D transitions, captions, SFX mapping, music, sandbox recovery
- **Action:** bpy stubs fixed; Husky re-rendered; transitions3d; SFX lib from Drive; gate 21/21; Drive upload
- **Result:** v6 gated and uploaded 1RY803aqjzXtCthdd6OGk98Dv8FL4Yz-B; awaiting user review
- **Files:** `styles/monarch-stickman-animation/src/transitions3d.py`, `styles/monarch-stickman-animation/src/kutta2.py`, `styles/monarch-stickman-animation/src/mux_kutta2.py`

## S-008 · 2026-10-14 02:45 PKT

- **Request:** Continue AMEER KA KUTTA; read /home/user/work/HANDOFF_v8.md; check branch arena/a188bd4a-monarch-studio. v8 delivered, user feedback pending
- **Action:** Fresh sandbox: /home/user/work and all build media gone (only the repo persisted). Fetched arena/a188bd4a (35 commits ahead of main, head 4867ac8) and fast-forwarded this session branch arena/ab4ba9f7 onto it. Rebuilt /tmp/venvs/render (numpy 2.4.6, pillow 12.3, scipy 1.17, imageio-ffmpeg 7.0.2); all picture modules import, kutta2/gate need only VO timing.json. Verified on Drive: v8 1D44AE8qc4wFwuAFu1UPrKPyuC-T8oshr intact (25,131,827 B, md5 8547b7e9c8c31319d9e149e7211f53e6), v1-v7 present, SFX pack 4 MP4s in folder 1AeMfK_DIcY4tkzWFwkJQM7XY0pOuPOgB. Wrote HANDOFF_KUTTA_v8.md inside the style folder (reconstruction + rebuild recipe) and copied it to /home/user/work/HANDOFF_v8.md
- **Result:** No v9 work started. Status unchanged: v8 delivered, awaiting user review. Rebuild in a fresh sandbox needs: new voice audition (voice ids are per session), SFX pack download + cut_sfx, Husky.glb + Blender sprites
- **Files:** `styles/monarch-stickman-animation/HANDOFF_KUTTA_v8.md`

