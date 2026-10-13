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

## V-012 · 2026-10-13 · AMEER_KA_KUTTA_v3_candidate · status: reviewed

- **File:** /home/user/build/AMEER_KA_KUTTA_v3_candidate.mp4
- **Drive ID:** 1hOFRUF7DHZxyRT1uGeoHNrGS9CFYKpFy
- **Settings:** v2.1 engine + headline 860 px safe margin (shrink, same breaks), VO re-generated voice-03 ur-PK, EQ presence +2 dB, PLAN card->flare, ink->blur, zoom kept; dog unchanged (2D kutta dog; 2D and 3D redraws NOT used)
- **Timing:** VO 16.2s speech, 20.39s total
- **Review:** gate 20/21: trans_jerk 8.04 at zoom@9.04 (limit 8.0, marginal). Not frame-by-frame reviewed. Not accepted.

## V-013 · 2026-10-13 · AMEER_KA_KUTTA_v4 · status: reviewed

- **File:** /home/user/build/AMEER_KA_KUTTA_v4.mp4
- **Drive ID:** 11Nn6GaxLROBA4wEhL2Xf60DIOCJRnxGL
- **Settings:** v3 + licensed SFX placed per moment (crack_flash hook, gleam bed, conjure_charge throne, synth_sparkle crown settle, riser_click before final shot, procedural AC click kept for stereo width); headline 9-layer 3D extrusion; blanket riser removed; PLAN throne-zoom->cube_h at 9.04 (jerk); gate 21/21
- **Timing:** 20.39 s total
- **Review:** gate 21/21 PASS; 1 s contact sheet only; dog design NOT premium (bean body, stub legs); not accepted

## V-014 · 2026-10-13 · AMEER_KA_KUTTA_v5 · status: reviewed

- **File:** /home/user/build/AMEER_KA_KUTTA_v5.mp4
- **Drive ID:** not uploaded
- **Settings:** dog: CC0 Husky rig (Quaternius Ultimate Animated Animal Pack, animals_pack, CC0-1.0) rendered in Blender 4.3 Cycles, recoloured gold, ink outline; poses: stand/sit=Idle, walk=Walk, eat=Eating, lie=Death final frame; split-shot dog lies on cushion; v4 SFX and headline kept; gate 21/21 PASS
- **Timing:** 20.39 s total
- **Review:** gate PASS; frames checked at 4/10/17 s; transitions, captions, BG music and videos 2-4 SFX mapping NOT upgraded; sit uses standing Idle (no sit clip in pack); not accepted

## V-015 · 2026-10-13 · AMEER_KA_KUTTA_v6 · status: draft

- **File:** /home/user/build/AMEER_KA_KUTTA_v6.mp4
- **Drive ID:** 1RY803aqjzXtCthdd6OGk98Dv8FL4Yz-B
- **Settings:** n/a
- **Timing:** 20.16s; shots 12; PLAN page(3D hinge) cube_h cube_v flare slices blur cube_h flare blur sweep flare
- **Review:** v6 gate 21/21 PASS. 3D transitions via transitions3d.py (page hinge, cube_h, cube_v); VO voice-03 regenerated after sandbox wipe; SFX lib cut from Drive pack (crack_flash, gleam, conjure_charge, synth_sparkle, riser_click, digital_click, modern_shutter, lighter_ignite); sit pose not available in Husky rig (limitation); dog look stylised low-poly; not accepted by user yet

## V-016 · 2026-10-13 · v7 · status: draft

- **File:** /home/user/build/AMEER_KA_KUTTA_v7.mp4
- **Drive ID:** 1tZWOw1sBN788x87_p7fxWLNdUG0gqvlp
- **Settings:** n/a
- **Timing:** 20.90s; shots 12; PLAN page depth cube_v flare depth shatter cube_h depth fold cube_h flare; SFX shatter=crack_flash, fold=modern_shutter, others procedural whoosh
- **Review:** v7 gate 21/21 ALL PASS (max_dluma 7.42, trans_jerk 6.07, lufs -12.4, peak -1.29 dBFS). 3D/parallax transitions replace v6 slides. VO voice-03 regenerated. Sit pose: no sit clip in Husky, Idle used (limitation). Not accepted by user yet.

## V-017 · 2026-10-13 · v8 · status: delivered (pending user review)

- **File:** /home/user/work/AMEER_KA_KUTTA_v8.mp4 (1080x1920, 30 fps, 20.77 s, AAC stereo)
- **Drive ID:** 1D44AE8qc4wFwuAFu1UPrKPyuC-T8oshr (link-viewable, reader)
- **Settings:** cards3d.py real 3D stage (perspective cards, side walls, cast shadows, sheen, neon edge, floor grid, streak particles, chroma split). Transitions: carousel (4-card ring turns 90 deg), tunnel (A flies past lens, B swings in from depth), deck (A thrown up, B's fanned deck rises). PLAN carousel tunnel deck shatter carousel tunnel deck shatter carousel tunnel_long flare; tunnel_long = 1.6 s on pave->crouch. Shatter TDX 0.80. Motion eased at window edges (particles, grid, sheen gain) so no step at the cut-in or cut-out.
- **Audio:** Drive SFX pack (VID_20261011_*: 4 MP4s) cut via cut_sfx.py; crack_flash, gleam, conjure_charge, synth_sparkle, riser_click, digital_click, modern_shutter, lighter_ignite placed by moment. VO voice-03 (ur-PK) regenerated this session with generate_speech (k1-k4), fitted by prep_vo_kutta.py. BG music + whooshes from mux_kutta2.py, loudnorm I=-10.6.
- **Timing:** 20.77 s total; boundaries 1.5 / 3.0 / 4.25 / 5.16 / 6.52 / 7.54 / 8.68 / 10.87 / 12.66 / 15.90 / 18.18 s.
- **Gate:** gate_kutta2.py 21/21 ALL PASS. max_dluma 7.843, frames_dluma_gt8 0, black_edge_frames 0, trans_jerk_max 6.944, decoded_peak -1.64 dBFS, lufs -12.1, av_delta 0.01, vo_longest_gap 0.24 s.
- **Fixes during v8 render (for the record):** front-card scale switched hard at cos>0.99 (one-frame jump at p~.18), fixed to a continuous function; deck B overscan so the top row is never uncovered; tunnel B coverage and shade ramped (bright-in/dark-out luma steps); carousel sheen gain eased.
- **Review:** sit pose uses Husky Idle (no sit clip in pack, limitation). SFX mapped by title and features, not verified by ear. Correction: V-016 said VO was regenerated for v7, which was not backed by a generate_speech call; the v8 VO is the one generated this session.
- **Status:** delivered; awaiting user review.

