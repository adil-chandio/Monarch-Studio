# Monarch Stickman Animation (WF-01 Paper Cinema) · video brain

Style `monarch-stickman-animation` · workflow WF-01. Created 2026-10-13 03:17 PKT.

## Video and lookdev log (append-only)

Use `tools/brain.py` to add entries. Do not edit old entries.
## V-001 · 2026-10-13 · Long-form release TUMHARI RESERVED SEAT 74 s, 1920x1080 30 fps (accepted 2026-10-11 per knowledge INDEX) · status: accepted

- **File:** films/tumhari-reserved-seat/
- **Drive ID:** see records/DELIVERY_RECEIPT.json
- **Settings:** 74.00 s, 34 voice-led beats, voice-00, gates 21/21, freshness 18/18
- **Timing:** n/a
- **Review:** Accepted in the knowledge index. This is the reference release for WF-01

## V-002 · 2026-10-13 · WF-01 v4 enhanced 10s (enhancement pass on V2 picture) · status: reviewed

- **File:** WF-01_paper_v4_enhanced_10s.mp4
- **Drive ID:** 1puZyLWIX4YG43iX2G0u86hJT16_3_3ob
- **Settings:** CRF 21, grain 2.4, 1080p, about 80-100 s processing
- **Timing:** n/a
- **Review:** Not accepted. Enhancement only, not the concept rebuild

## V-003 · 2026-10-13 · lookdev r3 t=6.0 270x480 32spp (Blender paper cinema) · status: rejected

- **File:** lookdev still (not in repo)
- **Drive ID:** not uploaded
- **Settings:** Cycles CPU, 270x480, 32 spp, world 0.22 at 0.3, raking key area 2.5 at 380 W
- **Timing:** about 3 s per frame
- **Review:** FAIL: flat grey, stick figure cheap, paper reads as boards

## V-004 · 2026-10-13 · lookdev r7 t=1.5/5.0/8.5 270x480 32spp (paper cinema 10s test, first build) · status: rejected

- **File:** lookdev stills (not in repo)
- **Drive ID:** not uploaded
- **Settings:** Cycles CPU, 270x480, 32 spp, key area 260 W, rim point 700 W, world 0.35
- **Timing:** about 2 s per frame
- **Review:** FAIL: texture rotated, wall cropped, figure crude, text not legible

## V-005 · 2026-10-13 · lookdev r7b t=5.0 270x480 32spp (texture and wall fixed) · status: rejected

- **File:** none (still only)
- **Drive ID:** not uploaded
- **Settings:** texture pre-rotated, wall 40x26
- **Timing:** about 2 s per frame
- **Review:** PARTIAL: wall and texture orientation fixed. Text still not legible, figure still crude

## V-006 · 2026-10-13 · shade_respect_v2 (reference, delivered before this session) · status: reviewed

- **File:** shade_respect_v2.mp4
- **Drive ID:** 1fu_g2HTNZVRqE3XBKdUKZoj6O8tIdkpu
- **Settings:** 75.19 s, 1080x1920, 30 fps, 2256 frames, 9 chapters, voice-01 Urdu TTS, md5 8d91be52ab969e0b23f21bf6bab0df85, gate_respect2 19/19
- **Timing:** n/a (earlier build, about 21 min sequential)
- **Review:** Reference for the 3D rebuild. Hybrid 2D look, not 3D. Keep the script and timing

## V-007 · 2026-10-13 · lookdev r8 t=7.7 1080x1920 (v2 vs v3 still) · status: reviewed

- **File:** stills in /tmp only
- **Drive ID:** not uploaded
- **Settings:** SHADE_ENH=0 vs 1: S-curve, warm highlights, cool shadows, vignette 0.20
- **Timing:** about 3 s per still
- **Review:** PASS (visual): paper warmer, edges dark, figure and captions unchanged

## V-008 · 2026-10-13 · v3 (SHADE IZZAT v3) · status: reviewed

- **File:** Drive 1gZ6IcqEbp9G4RzeYsKKiABrOzL6WsCY- (shade_respect_v3.mp4, 32,091,526 B, folder 1_MhRILyCB86LWHYqLDzBPvmneA6Y2uqo)
- **Drive ID:** not uploaded
- **Settings:** respect3.py: S-curve 0.10 grade, warm highlights, cool shadows, vignette 0.20; beat punch 0.016 on VO onsets only; final CRF 21 maxrate 4000k; audio chain locked
- **Timing:** 2256 frames, shards about 10 min each on 2 CPUs
- **Review:** Gate 19/19 PASS (trans_jerk 7.874). Frame sheet ref vs v3 at t=3/25/66/70.5: same layout and beats, warmer paper, edge vignette. Subtle upgrade, not a style change. Awaiting user review

## V-009 · 2026-10-13 · KUTTA v1 (AMEER KA KUTTA, new script) · status: reviewed

- **File:** Drive 1P9tWlmRWqWNejVKifhjafyFx8BWjMIc2 (kutta_ameer_ka_kutta_v1.mp4, 9,326,867 B, folder 1_MhRILyCB86LWHYqLDzBPvmneA6Y2uqo)
- **Drive ID:** not uploaded
- **Settings:** src/kutta.py: 4 chapters, 10 shots, 9 transitions (whip_h cube_h slices blur card zoom ink sweep slices); VO voice-03 ur-PK (Urdu script TTS), captions Roman Urdu; mux_kutta.py: procedural bed (pad, bells, whooshes, sparkles, air), numpy sidechain, VO EQ, extrastereo 1.2, loudnorm -11
- **Timing:** 711 frames, 23.7 s, two shards ~3 min each on 2 CPUs
- **Review:** Gate 19/19 PASS (trans_jerk 7.34 at sweep@19.44; lr_corr 0.65; LUFS -12.4). Transition sheet reviewed: all 9 boundaries clean. Characters are simple 2-D cut-outs; not yet judged by the user

## V-010 · 2026-10-13 · AMEER_KA_KUTTA_v2 · status: reviewed

- **File:** /home/user/build/AMEER_KA_KUTTA_v2.mp4
- **Drive ID:** 1IMkOtvmUMyKRN6xTx6GYi70w8uP2pI8o
- **Settings:** 1080x1920 30fps, H.264 CRF17 (shards), AAC 192k 48k stereo, 20.13 s, 17629256 B, kutta2.py + mux_kutta2.py + prep_vo_kutta.py, voice-03 ur-PK
- **Timing:** VO_AT 0.30/2.92/9.02/12.47 s, K4 ends 16.04 s, end hold 4.1 s; 12 shots; PLAN page,cube_h,whip_h,flare,slices,blur,zoom,card,ink,sweep,flare
- **Review:** frame sheets 0.5-19.9 s reviewed; OK: SHADE walk + leash, door with dog, car, bowl, bed, throne, crown, split. OPEN: drive shot has no SHADE visible; jerk_p95 2.11 (limit 2.0). Gate 20/22 PASS (gate_kutta_v2.txt).

## V-011 · 2026-10-13 · AMEER_KA_KUTTA_v2.1 · status: reviewed

- **File:** /home/user/build/AMEER_KA_KUTTA_v2.1.mp4
- **Drive ID:** 18xdhJCn1YTsQ7oBf0XnsGPDMPLaoquJU
- **Settings:** same as v2 plus driver-in-windshield composite (P2.hero masked to GLASS_F/GLASS_R) and smootherstep drive easing; 17619961 B
- **Timing:** unchanged from v2
- **Review:** driver visible in all drive frames 5.3-6.5 s; gate 21/22 PASS, only jerk_p95 2.12 (limit 2.0) open; not claimed accepted

