# Monarch Zack-D 3D Power · video brain

Style `monarch-zackd-3d-power` · workflow WF-02. Created 2026-10-13 03:17 PKT.

## Problems and fixes (append-only)

Use `tools/brain.py` to add entries. Do not edit old entries.
## P-001 · 2026-10-13 · status: fixed

- **Symptom:** Lookdev at 3.5 s showed only four cubes and looked broken
- **Cause:** Cube k appears only at t = k, and the text reveal starts at 6.5 s. The early time is correct but partial
- **Fix:** Rule: lookdev at the time the key element is on screen (9.5 s). Written into MINDSET
- **Verified by:** Stills r4_wf02_t3 vs r4_wf02_t95 in the lookdev set

## P-002 · 2026-10-13 · status: fixed

- **Symptom:** Tower too small and cropped; 30 HRS text above frame
- **Cause:** Camera distance and cube spacing 1.05 m made the tower a thin column; text at z 11.4 sat outside the frame
- **Fix:** Cube spacing 1.25 m; text moved to z 13.4; camera distance 21 m with target z 6.8
- **Verified by:** t=9.5 lookdev: full tower and text visible at 270x480

## P-003 · 2026-10-13 · status: open

- **Symptom:** Chrome and gold cubes look black or flat grey
- **Cause:** Metal reflects the world. A dark world makes chrome black; a flat mid-blue world at strength 1.1 makes everything grey
- **Fix:** Not fixed. Next: gradient or HDRI-style world, bright top, dark floor, reflection bands (NEXT_LEVEL P1-1)
- **Verified by:** Not yet

## P-004 · 2026-10-13 · status: open

- **Symptom:** Neon text blows out to white blocks at 270x480
- **Cause:** Emission above about 3 under AgX clips to white; glyph shapes read as blobs
- **Fix:** Emission now ramps 1.2 to 3.4. Still blocky at low resolution
- **Verified by:** t=9.5 lookdev, visual check

## P-005 · 2026-10-13 · status: open

- **Symptom:** Sandbox reset deleted the WF-02 v2 render and sound scripts (render_v2_power.py, make_sound_wf02.py)
- **Cause:** Working files lived outside Git and outside Drive during the sandbox reset
- **Fix:** Not recoverable. Final v2 MP4 exists on Drive (id 16pfe4ZwNfSE4Fgj0ktTZniRN1EcjmLJ9). Rebuild the sound and render from PIPELINE
- **Verified by:** Drive id recorded in VIDEO_LOG

## P-006 · 2026-10-13 · status: fixed

- **Symptom:** bpy import failed with numpy _ARRAY_API / multiarray error once
- **Cause:** Intermittent numpy import inside the bpy process
- **Fix:** Rerun once. If it repeats, check LD_LIBRARY_PATH and the blender venv numpy
- **Verified by:** Rerun succeeded in the same session

