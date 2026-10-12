# Monarch Zack-D 3D Power · video brain

Style `monarch-zackd-3d-power` · workflow WF-02. Created 2026-10-13 03:17 PKT.

## Skills (append-only)

Use `tools/brain.py` to add entries. Do not edit old entries.
## K-001 · 2026-10-13 · Headless Blender bpy in a locked-down sandbox

- **When to use:** Any Cycles render in the sandbox
- **How:** pip install bpy==4.3.0 in py3.11 venv. Build stub .so files for libXrender, libXxf86vm, libXfixes, libXi, libxkbcommon, libSM, libICE, libGL with gcc -shared -Wl,-soname. Run with LD_LIBRARY_PATH=/tmp/stublib and sys.setdlopenflags(RTLD_LAZY|RTLD_GLOBAL). Or run tools/bootstrap/setup_3d.sh
- **Evidence:** BPY_OK 4.3.0 verified after reset; lookdev stills rendered

## K-002 · 2026-10-13 · Lookdev at reveal time, one variable per iteration

- **When to use:** Judging any still before a full render
- **How:** Pick the time the key element is on screen. Change one variable. Log the change in VIDEO_LOG
- **Evidence:** Cube reveal and text reveal caused false alarms until timing was checked

## K-003 · 2026-10-13 · Portrait camera framing for 9:16

- **When to use:** Any 9:16 Blender camera
- **How:** With AUTO sensor fit in portrait, the 36 mm sensor applies to the height. Set distance from the tallest object, about 13.7 m visible height at 50 mm and 19 m
- **Evidence:** Lookdev framing fixed after the change

## K-004 · 2026-10-13 · Emission range under AgX

- **When to use:** Any neon or emissive text
- **How:** Keep emission between about 1 and 3. Above 3 the text clips to white blocks
- **Evidence:** Blocky glyphs at 270x480 with emission above 3

## K-005 · 2026-10-13 · Metal needs an environment

- **When to use:** Chrome, gold or any reflective material
- **How:** Use a gradient or HDRI-style world. A flat dark world makes metal black and a flat grey world makes it dull
- **Evidence:** Lookdev stills r5 and r4 (open problem P-003)

