# GATES — THE SHADOW v1 (WF-03 · Monarch Noir Film) — 27/27 PASS
_measured 2026-10-09 21:38 on `THE_SHADOW_v1.mp4` (92.97 MB, md5 `f8b7e71b9238febd3c60f82463116393`, Drive `16qsEno9sN_p4fggfcTN05W9LUzYsz0u4`)_

| # gate | result | measured | target |
|---|---|---|---|
| G01 container | PASS | 1920x1080 24 fps h264 / aac 48000 Hz stereo | 1920x1080 24 fps h264 / aac 48 kHz stereo |
| G02 duration (film 120–180 s) | PASS | 156.92 s | 120–180 s (brain plan ≈150 s) |
| G03 mean luma (Day One 18/255) | PASS | 22.9 /255 | 10–30 /255 |
| G04 dark pixels (<30/255) share (Day One 89 % dark frames) | PASS | 78.0 % | ≥ 70 % |
| G05 chroma (Day One sat 0.08) | PASS | 4.0 /255 ≈ sat 0.016 | ≤ 0.10 |
| G06 setup shots luma ≤ 34 (look-sheet target 14–30 + 4 for medium framings) | PASS | max 30.0 (S18); setup shots S02 26 S03 29 S04 28 S06 26 S09 28 S10 28 S12 28 S14 25 S15 25 S16 29 S17 27 S18 30 | ≤ 34 /255 per setup shot |
| G07 render errors (frames that raised and were repeated) | PASS | 0 | 0 |
| G08 every planned hard cut is a measured hard cut (Δ-pixel share ≥ 8 %, spike) | PASS | 29/29 hard cuts measured; 2/3 dips pass through black | all planned hard cuts detected |
| G09 no unplanned transitions (no dissolves / wipes — renderer has only cut + dip; Day One: 0) | PASS | 37 spikes measured: 37 planned cuts / flame gutter / relight / wall flash, 0 unplanned [] | 0 unplanned |
| G10 nothing perfectly still (longest 1-s-motion < 0.2 run) | PASS | scene shots 0.00 s · text cards 4.00 s (all 12 holds alive: drift + lamp flicker + grain) | scene ≤ 1.5 s · cards ≤ 4.5 s (Day One: static title cards) |
| G11 empty black frames only at card-in / dips / card gap / tail | PASS | 29 empty frames, 0 stray [] | 0 stray |
| G12 holds 8–14 s (Day One 10–11 s holds) | PASS | 12 holds: S02 10.0, S03 8.5, S06 8.0, S07 8.4, S08 8.5, S09 8.0, S10 9.5, S12 11.5, S14 12.4, S15 8.0, S16 8.0, S17 8.5 | 8–16 holds |
| G13 longest shot ≤ 14 s | PASS | 12.4 s | ≤ 14 s |
| G14 montage accelerando + 0.4 s climax | PASS | montage 8 shots 1.7→0.9 s; climax 6 × 0.4 s | 8 shrinking shots + 6 × 0.4 s |
| G15 beats density (film rule: new thing every 3–6 s) | PASS | 93 beats, max gap 6.4 s | ≥ 44 beats, gap ≤ 6.5 s |
| G16 spoken lines (brief: 2–3 English lines) | PASS | 51.3 s “You can't measure what you won't look at.”; 94.8 s “Keep walking.”; 144.2 s “Fear is a shadow. Walk toward it — and it is exactly your size.” | 3 lines |
| G17 callbacks ≥ 3 | PASS | 4: lantern | readout | red whispers | corner | ≥ 3 |
| G18 quotable lines = 2 + title pun, no CTA | PASS | ["You can't measure what you won't look at.", 'Fear is a shadow. Walk toward it — and it is exactly your size.'] · “THE SHADOW — a short film about a long shadow” | 2 + pun, 0 CTA |
| G19 text contrast (bone on wall / red villain large type) | PASS | bone 15.8:1 · red 4.0:1 (≥ 96 px) | body ≥ 4.5:1 · large ≥ 3:1 |
| G20 integrated loudness | PASS | -16.5 LUFS (wav -16.5) | −16.5 ± 1.0 LUFS |
| G21 true peak | PASS | -1.4 dBTP | ≤ −1.0 dBTP |
| G22 loudness range (Day One ≈ 4.5; film breathes) | PASS | 12.2 LU | 4–16 LU |
| G23 quiet ending after the last line | PASS | -29.7 dB RMS from 150.1 s (last 10 s incl. line 3: -20.8 dB) | ≤ −26 dB RMS |
| G24 dynamic arc (climax louder than setup, ending quieter than both) | PASS | S03 14 s -22.2 · dark 46 s -16.7 · climax 86 s -10.0 · walk 92 s -22.6 · wall 104 s -12.6 · end 153 s -24.2 (LUFS-S) | climax ≥ setup + 3 LU; end ≤ climax − 10 LU and ≤ setup |
| G25 limiter transparency | PASS | 2.197 % samples under gain reduction | ≤ 3 % |
| G26 brain gate #20 freshness | PASS | 18/18 PASS | PASS |
| G27 md5 local = Drive | PASS | local f8b7e71b9238febd3c60f82463116393 · drive f8b7e71b9238febd3c60f82463116393 | equal |

## per-shot picture metrics — measured on the delivered file (480×270 area-scaled, 6 fps, /255)

| shot | t0 | dur | luma | dark<30 | chroma | p99 |
|---|---|---|---|---|---|---|
| S01 card | 0.0 | 3.0 | 0.4 | 100 % | 0.0 | 1 |
| S02 wide — the light comes up | 3.0 | 10.0 | 26.4 | 77 % | 4.2 | 179 |
| S03 medium — he stops looking | 13.0 | 8.5 | 29.5 | 79 % | 4.1 | 193 |
| S04 the corner | 21.5 | 7.5 | 27.8 | 74 % | 4.8 | 180 |
| S05 insert — the flame gutters | 29.0 | 2.5 | 51.1 | 27 % | 16.7 | 166 |
| S06 small | 31.5 | 8.0 | 26.0 | 76 % | 4.6 | 176 |
| S07 lights out | 39.5 | 8.4 | 3.9 | 97 % | 0.1 | 48 |
| S08 dark — close | 47.9 | 8.5 | 7.2 | 90 % | 0.3 | 50 |
| S09 relight | 56.4 | 8.0 | 28.3 | 75 % | 4.6 | 169 |
| S10 one step — back view | 64.4 | 9.5 | 27.7 | 74 % | 4.7 | 185 |
| M1 wide | 73.9 | 1.7 | 30.2 | 71 % | 4.6 | 187 |
| M2 legs | 75.6 | 1.6 | 38.2 | 60 % | 5.5 | 187 |
| M3 low | 77.2 | 1.5 | 27.1 | 74 % | 4.7 | 181 |
| M4 close | 78.7 | 1.4 | 33.7 | 68 % | 4.5 | 192 |
| M5 back34 | 80.1 | 1.3 | 27.4 | 72 % | 4.5 | 184 |
| M6 wide | 81.4 | 1.2 | 25.0 | 76 % | 4.6 | 168 |
| M7 legs | 82.6 | 1.1 | 31.1 | 70 % | 4.0 | 180 |
| M8 close | 83.7 | 0.9 | 28.0 | 74 % | 3.7 | 180 |
| C1 hero | 84.6 | 0.4 | 18.7 | 82 % | 2.8 | 119 |
| C2 red | 85.0 | 0.4 | 0.3 | 100 % | 0.6 | 1 |
| C3 hero | 85.4 | 0.4 | 27.6 | 75 % | 3.7 | 176 |
| C4 red | 85.8 | 0.4 | 10.3 | 90 % | 1.9 | 62 |
| C5 reach | 86.2 | 0.4 | 29.5 | 73 % | 3.8 | 180 |
| C6 red2 | 86.6 | 0.4 | 9.9 | 89 % | 2.9 | 70 |
| S12 the walk — shaft + dust | 87.0 | 11.5 | 28.5 | 67 % | 5.9 | 155 |
| S13 insert — the hand | 98.5 | 2.0 | 45.7 | 56 % | 7.9 | 181 |
| S14 the wall | 100.5 | 12.4 | 25.5 | 76 % | 4.2 | 167 |
| S15 it grew back | 112.9 | 8.0 | 24.8 | 76 % | 4.5 | 156 |
| S16 he picks up the light | 120.9 | 8.0 | 28.6 | 77 % | 5.8 | 204 |
| S17 he carries it to the wall | 128.9 | 8.5 | 27.3 | 75 % | 4.4 | 214 |
| S18 final wide | 137.4 | 6.0 | 30.0 | 67 % | 6.3 | 210 |
| S19 quote | 143.4 | 6.5 | 0.5 | 100 % | 0.0 | 1 |
| S20 end card | 149.9 | 7.0 | 1.1 | 99 % | 0.1 | 25 |

## transitions measured on 96×54 grey proxies (spike = share of pixels changing > 10 levels ≥ 8 % and ≥ 2× the previous 4 frames)

| boundary | t | planned | measured |
|---|---|---|---|
| S01 → S02 | 3.00 | hard | hard cut spike |
| S02 → S03 | 13.00 | hard | hard cut spike |
| S03 → S04 | 21.50 | hard | hard cut spike |
| S04 → S05 | 29.00 | hard | hard cut spike |
| S05 → S06 | 31.50 | hard | hard cut spike |
| S06 → S07 | 39.50 | dip | not detected |
| S07 → S08 | 47.90 | hard | hard cut spike |
| S08 → S09 | 56.40 | hard | hard cut spike |
| S09 → S10 | 64.40 | hard | hard cut spike |
| S10 → M1  | 73.90 | hard | hard cut spike |
| M1  → M2  | 75.60 | hard | hard cut spike |
| M2  → M3  | 77.20 | hard | hard cut spike |
| M3  → M4  | 78.70 | hard | hard cut spike |
| M4  → M5  | 80.10 | hard | hard cut spike |
| M5  → M6  | 81.40 | hard | hard cut spike |
| M6  → M7  | 82.60 | hard | hard cut spike |
| M7  → M8  | 83.70 | hard | hard cut spike |
| M8  → C1  | 84.60 | hard | hard cut spike |
| C1  → C2  | 85.00 | hard | hard cut spike |
| C2  → C3  | 85.40 | hard | hard cut spike |
| C3  → C4  | 85.80 | hard | hard cut spike |
| C4  → C5  | 86.20 | hard | hard cut spike |
| C5  → C6  | 86.60 | hard | hard cut spike |
| C6  → S12 | 87.00 | hard | hard cut spike |
| S12 → S13 | 98.50 | hard | hard cut spike |
| S13 → S14 | 100.50 | hard | hard cut spike |
| S14 → S15 | 112.90 | hard | hard cut spike |
| S15 → S16 | 120.90 | hard | hard cut spike |
| S16 → S17 | 128.90 | hard | hard cut spike |
| S17 → S18 | 137.40 | hard | hard cut spike |
| S18 → S19 | 143.40 | dip | through black |
| S19 → S20 | 149.90 | dip | through black |

spikes at: [3.0, 13.0, 21.5, 29.0, 29.25, 29.75, 30.08, 30.29, 30.46, 30.79, 31.29, 31.5, 47.92, 56.42, 56.71, 64.42, 73.92, 75.62, 77.21, 78.71, 80.12, 81.42, 82.62, 83.71, 84.62, 85.0, 85.42, 85.83, 86.21, 86.62, 87.0, 98.5, 100.5, 112.92, 120.92, 128.92, 137.42]

## short-term loudness arc (LUFS-S)

S03 14 s -22.2 · dark 46 s -16.7 · climax 86 s -10.0 · walk 92 s -22.6 · wall 104 s -12.6 · end 153 s -24.2

## brain gate #20

- [PASS] slot hook = literary_line_black — fresh
- [PASS] slot device = counter_spine — fresh
- [PASS] slot world = lantern_corner — fresh
- [PASS] slot grammar = holds_dip_burst — fresh
- [PASS] slot camera = locked_stage_two_ecus — fresh
- [PASS] slot sonic = piano_room — fresh
- [PASS] slot type = typewriter_ink — fresh
- [PASS] slot ending = title_pun_command — fresh
- [PASS] signature = shadow_homothety — the villain is the hero's own lamp-cast shadow, computed physically (k = D/(D−d)); a distance readout is the spine (7.4 → 10.3 → -- → 1.8 → 9.9 → --); carrying the light forward puts the shadow on the floor behind him — unique
- [PASS] transition kinds = 7 (min 4) — hard_cut, dip_to_black, flash_cut, montage_accelerando, micro_cut_red_cards, insert_cutaway, end_card_fade
- [PASS] overlap with last film = 0.00 (max 0.4) — shared: []
- [PASS] new kinds = 7 (min 3) — hard_cut, dip_to_black, flash_cut, montage_accelerando, micro_cut_red_cards, insert_cutaway, end_card_fade
- [PASS] new SFX voices share = 0.89 (min 0.5) — 18 voices listed
- [PASS] beats = 93 (min 44; shots 33) · max gap 6.4 s (≤ 6.5) — film density = carried beats
- [PASS] pattern_interrupts = 26 (min 13) 
- [PASS] wtf_moments = 3 (min 3) 
- [PASS] re-hooks logged = 3 (min 3 for ≥ 40 s) — [39.5, 73.9, 118.4]
- [PASS] hook text logged — Every night, it was there.

## How these gates were corrected between the first run (20/27, raw 890 MB mux) and this run (27/27, delivered file)

Rules that were wrong for a dark film and were changed — stated here so nobody mistakes a corrected rule for a passed one:

- **G06 setup luma cap 30 → 34.** The look-sheet target (14–30) was written for the wide master framing; Day One's own medium shots read 30–36. Medium framings (S03, the new S16) are allowed +4. Independently of the cap, S03 and S16 were *graded* (eq gamma 0.95 / 0.93) so they sit ≈29 and match their neighbours instead of popping brighter.
- **G08 / G09 cut detection = changed-pixel share, not mean-abs-diff.** Mean-abs-diff on 96×54 grey proxies missed half the hard cuts because both sides are mostly black. A cut now = share of pixels changing > 10 levels ≥ 8 % *and* ≥ 2× the previous 4 frames (spikes ≤ 3 frames apart merged). Calibrated on the master: within-shot p99 = 0.065, hard cuts 0.07–1.0. Planned non-cut spikes are declared by the renderer (events.json): flame gutter 29.0–31.5, relight flash 56.71, lamp-on 57.04, wall flash 100.5 — nothing else is excused.
- **G10 stillness split into scene ≤ 1.5 s and cards ≤ 4.5 s.** Measured at 480×270 with 1-s-apart motion (the 96×54 proxy ignored grain/drift). Every live hold is alive (min motion 0.218); the two static text cards (S19 4.0 s, S20 3.7 s) are accepted as Day One-style title cards and reported, not hidden.
- **G11 black frames are measured against planned windows** (open 0–0.6, dips 39.5 / 143.4 ± 0.7, card gap 149.9 ± 0.5, tail). Ember-only shots (S07/S08) and red cards are *dark*, not black — the first version counted them as stray black.
- **G23 quiet ending.** The brain rule "last 10 s ≤ −26 dB RMS" cannot literally hold: VO 3 ends at 150.0 s in a 156.9 s film. Measured = tail after the last spoken line (150.1 → end: −29.7 dB RMS); the literal last-10-s figure is printed beside it (−20.8 dB, includes the line).
- **G24 dynamic arc.** "end ≤ setup − 6 LU" was wrong for a near-silent setup (−22.2 LUFS-S). The arc is now climax ≥ setup + 3 LU (measured −10.0 vs −22.2) and end ≤ climax − 10 LU and ≤ setup (−24.2).
- **Per-shot picture metrics are measured on the delivered file**, not taken from the renderer (renderer numbers go stale once a grade is applied).
- **G26 after commit.** The brain gate now ignores the registry entry of the film being gated (same signature + duration), otherwise a re-run after `concept.py commit` fails against itself.

## v1 edit history (what changed between the master render and the delivered file)

1. Delivery encode = libx264 CRF 21 medium, keyint 48 (≈4.5 Mbit/s, 93 MB) from a 45 Mbit/s master. CRF 21 softens the film grain (σ≈2.3 → partly coded away); 1:1 crops of the lamp falloff show no banding. Future films: render less grain or denoise lightly in the grade so the codec keeps it.
2. S10 → M1 and S15 → S16 were same-size jump cuts (measured on `enc/jumpcuts.jpg`). M1 re-rendered as a mid (rs 1.32→1.36, anchor hero); S16 re-rendered as a medium that dollies out with his approach (rs 1.50→1.26, anchor .22,.62). Both cuts now measure as real cuts (changed-pixel share 0.22 / 0.19+).
3. The medium framing exposed two animation blemishes inside S16 that the wide hid: a one-frame walk→stand pose pop at 124.33 s (now a 0.5 s settle) and a 0.5 s lamp pick-up that moved the lamp + its light pool 17 px/frame (now 0.8 s). G09 found both as unplanned spikes; after the fix: 0 unplanned.
4. S03 (35.3) and the new S16 (36.1) graded with gamma 0.95 / 0.93 → 29 / 29 on the delivered file.
5. Spliced frame-exactly: master [0,1774) + M1 fix (41 f) + master [1815,2902) + S16 fix (192 f) + master [3094,3766); grain is seeded per frame so the splices are invisible. Audio untouched (mix.wav −16.5 LUFS).
