# GATES — THE WINDOW v1 (WF-03 · Monarch Noir Film · film #2 · NOIRGO MAX) — 27/27 PASS
_measured 2026-10-10 02:55 on `THE_WINDOW_v1.mp4` (68.55 MB, md5 `cfe189f9c09e47e6728d2f2aba017f8d`, Drive `1WaMfEroWgzuYHeSCpyU9CPY7gJ0a0iGy`)_

| # gate | result | measured | target |
|---|---|---|---|
| G01 container | PASS | 1920x1080 24 fps h264 / aac 48000 Hz stereo | 1920x1080 24 fps h264 / aac 48 kHz stereo |
| G02 duration (film 120–180 s; timeline 155.0) | PASS | 155.00 s (timeline 155.0) | 120–180 s, = timeline ± 0.25 |
| G03 mean luma (NOIRGO MAX: lit rooms are the villain — Day One 18, look sheet v2 target 20–36) | PASS | 26.9 /255 | 20–36 /255 |
| G04 dark pixels (<30/255) share | PASS | 68.1 % | ≥ 50 % |
| G05 chroma (Day One sat 0.08; amber act allowed) | PASS | 12.2 /255 ≈ sat 0.048 | ≤ 0.10 |
| G06 night bedroom / facade ambience shots luma ≤ 34 (S21 phone-lit face insert excluded by design) | PASS | max 31.9 (S26); S01 32 S02 21 S03 27 S04 27 S05 23 S13 22 S22 18 S23 23 S24 16 S25 28 S26 32 S27 26 S29 24 S31 24 S32 24 | ≤ 34 /255 per shot |
| G07 render integrity (4 segments, metrics every 24 frames, no frame raised) | PASS | 4 segments, 155 metric rows (3720 frames / 24) | 4 segments · 155 rows |
| G08 every planned hard cut is a measured hard cut (Δ-pixel share ≥ 8 %, spike); continuous takes show no spike | PASS | 38/38 hard cuts measured; 5 soft boundaries (fades / card gaps); 1/1 continuous takes seamless (S38→S39 @127.0) | all planned hard cuts detected |
| G09 no unplanned transitions (only cuts, dips, planned light events, the flurry) | PASS | 49 spikes measured: 49 planned, 0 unplanned [] | 0 unplanned |
| G10 nothing perfectly still (longest 1-s-motion < 0.2 run) | PASS | scene shots 0.00 s · cards 3.58 s (rain, breathing, saccades, drift, grain) | scene ≤ 1.5 s · cards ≤ 4.5 s |
| G11 empty black frames only at fade-in / cards / fades / the dead phone / tail | PASS | 4 empty frames, 0 stray [] | 0 stray |
| G12 carried holds 4–7 s (every hold carries a VO phrase, a light or a music change) | PASS | 14 holds: S08 4.2, S13 4.3, S16 5.1, S19 5.0, S22 5.3, S24 5.0, S26 5.4, S33 4.8, S35 6.8, S39 4.0, S40 4.0, S43 5.0, S44 4.2, S45 4.2 | 8–20 holds |
| G13 longest shot ≤ 7 s | PASS | 6.8 s (S35 DAY 23 · running past) | ≤ 7 s |
| G14 montage: 3 × 0.6 s readouts → 6 × 0.25 s flurry → red card + 0.35 s hole | PASS | 9 readouts, gaps [0.6, 0.6, 0.6, 0.25, 0.25, 0.25, 0.25, 0.25] | 9 readouts, non-increasing gaps, flurry 0.25 s |
| G15 beats density (new thing ≤ 4.8 s apart; ≥ 120 beats) | PASS | 162 beats, max gap 4.7 s at 141.9 s | ≥ 120 beats, gap ≤ 4.8 s |
| G16 full voiceover (brief: 10 clips, voice-03, each at its planned start) | PASS | 10 clips, 123.6 s of voice = 80 % of runtime; starts 1.2 20.6 38.4 46.8 51.8 59.1 69.6 89.6 104.0 124.2 | 10 clips |
| G17 callbacks ≥ 3 | PASS | 5: 'You only ever see the lit room.' | red lines → white answers in the same gl | 31 windows counted at 7.0 → 'his own ref | the three windows return as his days | his window | ≥ 3 |
| G18 quotable lines = 2 + title pun, no CTA | PASS | ['Every window you have ever envied has someone standing in it, looking at yours.', 'The only window you will ever see from the inside is your own.'] · “THE WINDOW — a window is also a screen; the only one you can” | 2 + pun, 0 CTA |
| G19 text contrast (bone on wall / red villain large type / white answers) | PASS | bone 15.8:1 · red 4.0:1 (≥ 60 px) | body ≥ 4.5:1 · large ≥ 3:1 |
| G20 integrated loudness | PASS | -16.5 LUFS (wav -16.5) | −16.5 ± 1.0 LUFS |
| G21 true peak | PASS | -3.5 dBTP | ≤ −1.0 dBTP |
| G22 loudness range (narrated film: 4–16) | PASS | 6.2 LU | 4–16 LU |
| G23 quiet ending (from the second end card to the end) | PASS | -43.5 dB RMS from 146.6 s (last line ends 138.4 s) | ≤ −26 dB RMS |
| G24 dynamic arc of the score/SFX bed (VO-muted bus; with a full voiceover the mix short-term loudness is the voice) | PASS | bed: hook 5 s -42.4 · windows 30 s -28.4 · dead phone 76 s -33.4 · clock stop 88.5 s -30.6 · climax 141 s -21.9 · end 153 s -43.1 (LUFS-S) · full mix: hook -17.8 · windows -17.4 · phone -15.3 · climax -19.7 · end -43.1 | dead phone ≤ windows − 1.5; climax ≥ hook + 6; end ≤ climax − 10 |
| G25 limiter transparency | PASS | 0.357 % samples under gain reduction | ≤ 3 % |
| G26 brain gate #20 freshness | PASS | 18/18 PASS | PASS |
| G27 md5 local = Drive | PASS | local cfe189f9c09e47e6728d2f2aba017f8d · drive cfe189f9c09e47e6728d2f2aba017f8d | equal |

## per-shot picture metrics — measured on the delivered file (480×270 area-scaled, 6 fps, /255)

| shot | t0 | dur | luma | dark<30 | chroma | p99 |
|---|---|---|---|---|---|---|
| S01 face · phone POV | 0.0 | 3.4 | 31.7 | 77 % | 15.8 | 171 |
| S02 bed wide · lying, glowing | 3.4 | 3.2 | 20.6 | 78 % | 18.1 | 73 |
| S03 facade · 31 windows lit | 6.6 | 3.1 | 27.3 | 75 % | 15.2 | 149 |
| S04 facade drift · people | 9.7 | 2.9 | 27.4 | 76 % | 14.9 | 152 |
| S05 his window · blue | 12.6 | 3.8 | 22.9 | 72 % | 11.3 | 65 |
| S06 title | 16.4 | 3.8 | 5.1 | 98 % | 2.5 | 27 |
| S07 push → B4 | 20.2 | 2.9 | 26.7 | 76 % | 14.8 | 145 |
| S08 the runner | 23.1 | 4.2 | 34.6 | 56 % | 11.8 | 138 |
| S09 push → I3 | 27.3 | 2.3 | 29.7 | 73 % | 15.8 | 160 |
| S10 the couple · two plates | 29.6 | 3.7 | 40.8 | 51 % | 16.4 | 168 |
| S11 push → D5 | 33.3 | 2.0 | 27.8 | 76 % | 15.3 | 158 |
| S12 two monitors | 35.3 | 2.8 | 27.8 | 71 % | 16.5 | 117 |
| S13 bed · he looks up | 38.1 | 4.3 | 22.1 | 76 % | 18.6 | 96 |
| S14 montage + flurry | 42.4 | 3.3 | 28.1 | 60 % | 13.7 | 115 |
| S15 red card · look at them. | 45.7 | 0.8 | 3.0 | 100 % | 2.0 | 3 |
| S16 the lit room | 46.5 | 5.1 | 25.8 | 79 % | 15.1 | 164 |
| S17 runner · the knee | 51.6 | 3.5 | 36.0 | 53 % | 12.2 | 146 |
| S18 couple · the silence | 55.1 | 3.8 | 31.2 | 61 % | 11.1 | 118 |
| S19 two monitors · at the glass | 58.9 | 5.0 | 27.2 | 72 % | 16.8 | 113 |
| S20 at yours | 63.9 | 2.4 | 24.9 | 65 % | 10.9 | 71 |
| S21 face · so calm | 66.3 | 3.0 | 36.7 | 68 % | 18.8 | 195 |
| S22 the phone dies | 69.3 | 5.3 | 18.2 | 82 % | 16.6 | 77 |
| S23 his window goes dark | 74.6 | 2.4 | 23.4 | 72 % | 11.7 | 58 |
| S24 he stands · the walk | 77.0 | 5.0 | 16.4 | 87 % | 14.8 | 59 |
| S25 at the glass | 82.0 | 1.6 | 28.4 | 58 % | 14.4 | 125 |
| S26 the reflection | 83.6 | 5.4 | 31.9 | 51 % | 12.1 | 110 |
| S27 he turns away | 89.0 | 3.9 | 26.2 | 62 % | 13.7 | 118 |
| S28 card · The boring part. | 92.9 | 1.3 | 5.7 | 96 % | 3.4 | 14 |
| S29 the bed | 94.2 | 2.9 | 24.1 | 73 % | 15.5 | 87 |
| S30 the dishes | 97.1 | 2.5 | 30.8 | 71 % | 11.4 | 194 |
| S31 the desk | 99.6 | 2.3 | 24.3 | 72 % | 15.3 | 90 |
| S32 the shoes | 101.9 | 1.7 | 23.8 | 73 % | 15.2 | 87 |
| S33 DAY 1 · the run | 103.6 | 4.8 | 27.4 | 71 % | 13.2 | 140 |
| S34 DAY 9 · the lamp | 108.4 | 3.2 | 31.8 | 59 % | 15.3 | 112 |
| S35 DAY 23 · running past | 111.6 | 6.8 | 46.7 | 46 % | 13.1 | 179 |
| S36 DAY 40 · he looks up | 118.4 | 2.5 | 36.8 | 50 % | 11.9 | 127 |
| S37 a new window | 120.9 | 2.7 | 33.3 | 48 % | 6.1 | 85 |
| S38 facade at dawn | 123.6 | 3.4 | 36.6 | 37 % | 8.8 | 94 |
| S39 someone standing in it | 127.0 | 4.0 | 36.2 | 40 % | 8.4 | 99 |
| S40 from the inside | 131.0 | 4.0 | 42.4 | 43 % | 8.2 | 142 |
| S41 Light it. | 135.0 | 3.4 | 42.9 | 41 % | 17.8 | 148 |
| S42 his window · amber wide | 138.4 | 3.2 | 32.1 | 50 % | 4.4 | 81 |
| S43 end card | 141.6 | 5.0 | 4.3 | 99 % | 1.8 | 28 |
| S44 end card 2 | 146.6 | 4.2 | 3.2 | 100 % | 1.7 | 3 |
| S45 quiet | 150.8 | 4.2 | 3.0 | 100 % | 1.7 | 3 |

## transitions measured on 96×54 grey proxies (spike = share of pixels changing > 10 levels ≥ 8 % and ≥ 2× the previous 4 frames)

| boundary | t | planned | measured |
|---|---|---|---|
| S01 → S02 | 3.40 | hard | hard cut spike |
| S02 → S03 | 6.60 | hard | hard cut spike |
| S03 → S04 | 9.70 | hard | hard cut spike |
| S04 → S05 | 12.60 | hard | hard cut spike |
| S05 → S06 | 16.40 | dip | hard cut spike + through black |
| S06 → S07 | 20.20 | hard | hard cut spike |
| S07 → S08 | 23.10 | hard | hard cut spike |
| S08 → S09 | 27.30 | hard | hard cut spike |
| S09 → S10 | 29.60 | hard | hard cut spike |
| S10 → S11 | 33.30 | hard | hard cut spike |
| S11 → S12 | 35.30 | hard | hard cut spike |
| S12 → S13 | 38.10 | hard | hard cut spike |
| S13 → S14 | 42.40 | hard | hard cut spike |
| S14 → S15 | 45.70 | hard | hard cut spike |
| S15 → S16 | 46.50 | hard | hard cut spike |
| S16 → S17 | 51.60 | hard | hard cut spike |
| S17 → S18 | 55.10 | hard | hard cut spike |
| S18 → S19 | 58.90 | hard | hard cut spike |
| S19 → S20 | 63.90 | hard | hard cut spike |
| S20 → S21 | 66.30 | hard | hard cut spike |
| S21 → S22 | 69.30 | hard | hard cut spike |
| S22 → S23 | 74.60 | hard | hard cut spike |
| S23 → S24 | 77.00 | hard | hard cut spike |
| S24 → S25 | 82.00 | hard | hard cut spike |
| S25 → S26 | 83.60 | hard | hard cut spike |
| S26 → S27 | 89.00 | hard | hard cut spike |
| S27 → S28 | 92.90 | dip | through black |
| S28 → S29 | 94.20 | hard | hard cut spike |
| S29 → S30 | 97.10 | hard | hard cut spike |
| S30 → S31 | 99.60 | hard | hard cut spike |
| S31 → S32 | 101.90 | hard | hard cut spike |
| S32 → S33 | 103.60 | hard | hard cut spike |
| S33 → S34 | 108.40 | hard | hard cut spike |
| S34 → S35 | 111.60 | hard | hard cut spike |
| S35 → S36 | 118.40 | hard | hard cut spike |
| S36 → S37 | 120.90 | hard | hard cut spike |
| S37 → S38 | 123.60 | hard | hard cut spike |
| S38 → S39 | 127.00 | continuous | not detected |
| S39 → S40 | 131.00 | hard | hard cut spike |
| S40 → S41 | 135.00 | hard | hard cut spike |
| S41 → S42 | 138.40 | hard | hard cut spike |
| S42 → S43 | 141.60 | dip | soft |
| S43 → S44 | 146.60 | dip | soft |
| S44 → S45 | 150.80 | dip | soft |

spikes at: [3.42, 6.62, 9.71, 12.62, 16.29, 20.21, 23.12, 27.33, 29.62, 33.33, 35.33, 38.12, 42.42, 43.0, 43.62, 44.46, 44.71, 44.96, 45.21, 45.46, 45.71, 46.5, 51.62, 55.12, 58.92, 63.92, 66.33, 69.33, 71.5, 74.62, 77.0, 82.0, 83.62, 89.0, 92.75, 94.21, 97.12, 99.62, 101.92, 103.62, 108.42, 109.96, 111.62, 118.42, 120.92, 123.62, 131.0, 135.0, 138.42]

## short-term loudness arc (LUFS-S)

hook 5 s -42.4 · windows 30 s -28.4 · dead phone 76 s -33.4 · clock stop 88.5 s -30.6 · climax 141 s -21.9 · end 153 s -43.1

## brain gate #20

- [PASS] slot hook = clock_readout_face_pov — fresh
- [PASS] slot device = windows_comparison_facade — fresh
- [PASS] slot world = apartment_facade_real_plates — fresh
- [PASS] slot grammar = vo_led_pushins_flurry_inserts — fresh
- [PASS] slot camera = crop_camera_pushes_reflection — fresh
- [PASS] slot sonic = felt_bells_dminor_72_picardy — fresh
- [PASS] slot type = clock_readout_mirror_lines — fresh
- [PASS] slot ending = picardy_dawn_two_cards — fresh
- [PASS] signature = window_mirror — the villain is a real facade of 31 lit windows (measured rects); four red lines on the glass get four white answers in the same positions; the phone dies and the hero's reflection is laid over all 31 windows; the clock stops at 88.0 and never ticks again; the first amber light in the film is his own lamp; DAY 40 somebody across the street looks up at a new window (Picardy third D minor → D major) — unique
- [PASS] transition kinds = 7 (min 4) — hard_cut, dip_to_black, push_in_crop, montage_flurry_readouts, light_state_cut, reflection_overlay_fade, reverse_angle_pair
- [PASS] overlap with last film = 0.29 (max 0.4) — shared: ['dip_to_black', 'hard_cut']
- [PASS] new kinds = 5 (min 3) — push_in_crop, montage_flurry_readouts, light_state_cut, reflection_overlay_fade, reverse_angle_pair
- [PASS] new SFX voices share = 0.87 (min 0.5) — 30 voices listed
- [PASS] beats = 161 (min 44; shots 45) · max gap 4.7 s (≤ 6.5) — film density = carried beats
- [PASS] pattern_interrupts = 31 (min 13) 
- [PASS] wtf_moments = 4 (min 3) 
- [PASS] re-hooks logged = 4 (min 3 for ≥ 40 s) — [38.4, 69.6, 104.0, 124.2]
- [PASS] hook text logged — 11:48 PM — It's eleven forty-eight at night. He's lying in t
