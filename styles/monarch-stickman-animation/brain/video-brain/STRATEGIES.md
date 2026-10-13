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

## ST-005 · 2026-10-13

- **Decision:** Keep the v2 chain. Ship v3 as a candidate. Next levers for a bigger upgrade need the user's pick (more fun beats, new inserts, or text motion)
- **Alternatives rejected:** Full 3D rebuild (rejected by user). Frame-by-frame new scenes (large scope)
- **Outcome:** v3 candidate on Drive; user review pending

## ST-006 · 2026-10-13

- **Decision:** New topic in the same editing grammar: re-used respect2 transitions and the v3 grade, own chapter scenes, characters and captions, own gate (gate_kutta = gate_respect2 with a kutta timeline shim)
- **Alternatives rejected:** Reuse respect scenes (they are IZZAT content, not usable). Full 3D (user rejected 3D for this style)
- **Outcome:** KUTTA v1 candidate on Drive; user review pending

## ST-007 · 2026-10-13

- **Decision:** VO runs continuously (LEAD/TAIL 0 between chapters, 0.05 s clip edges), music is tonal (A minor 96 BPM, chapter-wise layer gains), no noise anywhere in the audio
- **Alternatives rejected:** keep 0.45 s chapter gaps (rejected: user asked for no voice gaps); noise bed or hiss air (rejected by user); sample library (not licensed)
- **Outcome:** gate: vo_longest_gap 0.24 s, bed_flatness ~0, longest silence 0.0 s

## ST-008 · 2026-10-13

- **Decision:** Gate recalibration for v2: bed_4000_8000 threshold 10 pct -> 1.5 pct (tonal air only); v1 needed hiss to reach 10 pct, which the user rejected. Added vo_longest_gap_s <= 0.35 and bed_flatness_1k_8k < 0.20
- **Alternatives rejected:** keep the v1 threshold (would force noise air); drop the check (would hide the air loss)
- **Outcome:** gate_kutta2.py 20/22 pass; the 2 fails are reported, not hidden

## ST-009 · 2026-10-14

- **Decision:** v9 'cinema' pass on AMEER KA KUTTA (user gave full creative freedom: chaos level, absolutely cinema). Picture: per-chapter colour grades (HOOK warm, LUXURY cool teal/blue, RAJA royal purple+gold, GAREEB desaturated cold) blended over 0.6 s; new post chain in kutta2.render(): frame -> chapter_grade -> bloom(.38, streak .26, thresh 185) -> handheld camera (sine mixes, chapter amplitude 1.0/1.25/.85/.6, roll .55 deg x signed punch) -> chromatic split + radial rush on punches -> respect3 grade -> vignette -> flash -> grain. Moments: slam title AMEER KA KUTTA? at 0.30 s (shockwave+dust), hot-word punches at the 8 caption keywords, money rain (notes+coins) in bowl/bed, god rays + crown drop with shockwave+confetti at 10.78 s, rain layer + lightning (12.5 / 15.36 s) + breath fog in GAREEB, end stamp (crown + AMEER KA KUTTA. / insaan ya janwar?) at 15.68 s. Dog rides inside the car (head through the rear window, same glass mask as the driver). Husky sprites gold-tinted. Sound: sfx9.py synthesises every cue by design (braam at 0, impact on slam/crown/stamp, coins, confetti, thunder x2, diegetic rain bed from GAREEB, sub drop before the last line, stamp ring), whoosh_air layered under the tonal sweep; music dips to .16 for the sub drop and swells back under line 4.
- **Alternatives rejected:** Keep the v8 flat look and only add SFX (rejected: the user asked for a visible next level). Big per-frame flashes/strobes for chaos (rejected: gate max_dluma<8 and the user's earlier flicker complaints; every new element fades in over 3-5 frames and punches have a 3-frame attack instead). Noise-based rain/whoosh at full level (rejected: ST-007 no-hiss rule; rain is droplet bursts kept at 0.42 per sheet so the bed flatness median stays 0.08).
- **Outcome:** v9 contact sheets approved by eye at 18+8+4 frames; luma probes after tuning: slam 1.2, hook->luxury 5.5 (was 10.9 before tunnel_long), crown 5.8, thunder 5.2/3.2, stamp 2.4 (all < 8). Mix: LUFS -12.2, TP -2.0 dBFS, bed flatness median 0.078, lr_corr 0.59, bed_20_120 25.8 %. Full render + gate result logged in V-018.

