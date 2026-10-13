# Monarch Zack-D 3D Power · video brain

Style `monarch-zackd-3d-power` · workflow WF-02. Created 2026-10-13 03:17 PKT.

## Video and lookdev log (append-only)

Use `tools/brain.py` to add entries. Do not edit old entries.
## V-001 · 2026-10-13 · lookdev r5 t=9.5 270x480 32spp · status: rejected

- **File:** lookdev stills in the lookdev set (not in repo)
- **Drive ID:** not uploaded
- **Settings:** Cycles CPU, 270x480, 32 spp, world 0.22/0.27/0.36 at 1.1, key area 2600 W, rim 1500-2500 W, fill 2500 W
- **Timing:** about 2.8 s per frame
- **Review:** FAIL: dark grey, chrome not reading as chrome, neon blocky at low resolution

## V-002 · 2026-10-13 · WF-02 v2 30HRS 10s (earlier Drive delivery, not from this Blender path) · status: draft

- **File:** WF-02_zackd3d_v2_30HRS_10s.mp4
- **Drive ID:** 16pfe4ZwNfSE4Fgj0ktTZniRN1EcjmLJ9
- **Settings:** 640x360, 28 spp, 24 fps, 240 frames, cut boundaries 0 2.5 5.0 7.5 s
- **Timing:** about 0.7 s per frame
- **Review:** Not accepted by user. Test quality. Superseded by the Blender path

## V-003 · 2026-10-13 · lookdev r6a t=9.5 270x480 32spp, flat world (r5 baseline re-run) · status: rejected

- **File:** none (still only)
- **Drive ID:** not uploaded
- **Settings:** WF02_WORLD=flat, Cycles CPU, 32 spp
- **Timing:** 2.5 s per frame
- **Review:** FAIL: grey, chrome dull, tower tiny at top of frame

## V-004 · 2026-10-13 · lookdev r6b t=9.5 270x480 32spp, Nishita sky world strength 0.6 · status: rejected

- **File:** none (still only)
- **Drive ID:** not uploaded
- **Settings:** WF02_WORLD=sky WF02_SKY=0.6, sun elev 14, rot 200, air 1.0, dust 0.6
- **Timing:** 2.5 s per frame
- **Review:** FAIL: washed out, pale cubes, no contrast. Sky reads as haze

## V-005 · 2026-10-13 · lookdev r6c t=9.5 270x480 32spp, Nishita sky world strength 0.25 · status: rejected

- **File:** none (still only)
- **Drive ID:** not uploaded
- **Settings:** WF02_WORLD=sky WF02_SKY=0.25
- **Timing:** 2.7 s per frame
- **Review:** FAIL: nearly identical to r6b. Sky strength is not the lever. Framing and material are

