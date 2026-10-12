# Monarch Stickman Animation (WF-01 Paper Cinema) · video brain

Style `monarch-stickman-animation` · workflow WF-01. Created 2026-10-13 03:17 PKT.

## Problems and fixes (append-only)

Use `tools/brain.py` to add entries. Do not edit old entries.
## P-001 · 2026-10-13 · status: fixed

- **Symptom:** Paper layers looked washed out, world and key light too bright
- **Cause:** World strength 0.9 plus area energy 900 at size 6
- **Fix:** World 0.3 colour (0.22,0.21,0.2). Key area size 2.5, energy 380, raking angle
- **Verified by:** Lookdev r2_wf01 and r3_wf01_t6: layers readable

## P-002 · 2026-10-13 · status: open

- **Symptom:** Still looks flat and grey, paper reads as boards
- **Cause:** No edge highlight, no shadow pass between layers, no paper texture
- **Fix:** Not fixed. Next: paper-layer shadows and edge highlights (NEXT_LEVEL)
- **Verified by:** Not yet

## P-003 · 2026-10-13 · status: open

- **Symptom:** Stick figure reads cheap next to the premium target
- **Cause:** Primitive shapes (sphere head, cube torso, cylinder limbs)
- **Fix:** Not fixed. Design a paper cut-out figure with a proper silhouette
- **Verified by:** Not yet

## P-004 · 2026-10-13 · status: open

- **Symptom:** Title text placement off-frame at some times
- **Cause:** Title sits at z 2.6 and 2.05 with camera framing that changes per shot
- **Fix:** Partly fixed. Check at each shot time before accepting
- **Verified by:** Lookdev r3_wf01_t6 shows both lines

## P-005 · 2026-10-13 · status: fixed

- **Symptom:** Timetable texture rotated 90 degrees on the cube face (EXPRE read vertically)
- **Cause:** Default cube UV on the -Y face is rotated relative to the portrait texture
- **Fix:** Pre-rotate the texture PNG by ROTATE_90 in the texture step
- **Verified by:** lookdev r7b: texture orientation corrected

## P-006 · 2026-10-13 · status: fixed

- **Symptom:** Wall card cropped, dark edges visible in frame
- **Cause:** Wall plane 14x9 too small for the 32 mm camera frame
- **Fix:** Wall plane 40x26 at y=7
- **Verified by:** lookdev r7b: wall covers frame

## P-007 · 2026-10-13 · status: fixed

- **Symptom:** Import failure libusd glXGetProcAddress when bpy imported before wf_scenes
- **Cause:** dlopen flags set in wf_scenes, but the new script imported bpy first
- **Fix:** Import wf_scenes before bpy in wf01_paper10s.py
- **Verified by:** lookdev renders after reorder

## P-008 · 2026-10-13 · status: open

- **Symptom:** Timetable text and ticket text not legible at 270x480 (lookdev), card reads as plain grey
- **Cause:** Key light 260 W too weak for the paper card; text strokes at 34-80 px too thin at low res
- **Fix:** Open. Next: raise key energy or move to brighter key, bigger type in texture, test at 360x640
- **Verified by:** Not yet

## P-009 · 2026-10-13 · status: open

- **Symptom:** Seated figure reads as primitive shapes, not a premium cut-out
- **Cause:** Figure built from thin cards and disks with no silhouette design
- **Fix:** Open. Next: design a proper paper cut-out silhouette (bezier outline extruded thin, with shadow offset)
- **Verified by:** Not yet

## P-010 · 2026-10-13 · status: open

- **Symptom:** shade.py is a 2D PIL drawing, not a 3D model, so there is no 3D SHADE to reuse
- **Cause:** The toon/shade rig solves 2D joints and draws with PIL
- **Fix:** Open. Build SHADE as a Blender mesh (hood, blazer, trousers, shoes, glowing wedge eyes) and port pose functions (p_*) to 3D joint angles
- **Verified by:** Not yet

## P-011 · 2026-10-13 · status: open

- **Symptom:** 1080x1920 Cycles render is too slow here (about 35 s per frame, 2 CPU, 3 GB RAM)
- **Cause:** Sandbox has 2 CPUs and 3 GB RAM. Measured with the WF-01 test scene
- **Fix:** Pilot at 540x960 (about 6-8 s per frame). Final 1080p on a GPU machine or in chunks across sessions
- **Verified by:** Timing in this session: 540x960 13 s, 1080x1920 43 s incl. startup

## P-012 · 2026-10-13 · status: fixed

- **Symptom:** finish_respect2.sh default mux OUT is /home/user/shade_respect_v2.mp4 and its gate reads the same path. Running it on a symlink would overwrite the reference video
- **Cause:** Hardcoded output and gate paths in mux_respect2.sh and finish_respect2.sh
- **Fix:** build_respect3.sh overrides OUT=/home/user/build/respect3_v3.mp4 and passes the v3 path to the gate. Baseline finish step stopped before it ran
- **Verified by:** Reference md5 8d91be52ab969e0b23f21bf6bab0df85 unchanged after the stop

## P-013 · 2026-10-13 · status: fixed

- **Symptom:** Respect2 VO assets r1-r9_fit.wav were missing from the repo and the workspace
- **Cause:** Audio assets are not in Git and were only in the Drive package shade_respect_v2_package.zip
- **Fix:** Downloaded the package to /tmp, extracted assets/ to /tmp/shade_build/assets, kept it out of the repo. Recorded the Drive ID in TOOLCHAIN next
- **Verified by:** 9 wav files extracted, sizes match the zip listing

## P-014 · 2026-10-13 · status: fixed

- **Symptom:** Punch on cut boundaries made trans_jerk_max 12.6 (limit 8)
- **Cause:** Scale pop added on top of a shot transition
- **Fix:** Punch only on VO onsets (_BEATS excludes BOUNDS)
- **Verified by:** Draft rev2 gate: trans_jerk 8.19 at card@66

## P-015 · 2026-10-13 · status: fixed

- **Symptom:** trans_jerk_max 8.19 at card@66 (limit 8.0). Reference re-encoded with the same CRF 23 settings scores 8.03
- **Cause:** Encode noise sensitivity of the transition-step metric at the limit; grade adds a little
- **Fix:** Final video CRF 21 maxrate 4000k (audio copied). Measured 7.874
- **Verified by:** Gate 19/19 on /home/user/build/respect3_v3.mp4

