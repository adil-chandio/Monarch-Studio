# SHADE × POWERFUL MAN — 42 s short, remake notes

`shade_power_42s.mp4` · 1080×1920 · 30 fps · 1260 frames · 42.000 s
Built by `build_shade.sh` → `src/power2.py` (2 render shards) → `src/make_asmr_power.py` (bed) →
`src/mux_power.sh` (locked v1 audio chain, `OUT=` override) → `src/gate_shade.py` (18 gates).

Delivery hashes / gate numbers: see §7 (filled from the build log).

## 0. What this is
The same 42 s film as `stickman_power_42s.mp4` (same script `SCRIPT_POWER.md`, same six fitted
VO clips `assets/p1–p6_fit.wav`, same `timeline_power.py` cut, same camera rig, same caption
contract, same ASMR bed and mux) with the hero replaced by the user's personal character
**SHADE** (`src/shade.py`, approved via `shade_character_sheet.png`) and the frame rebuilt in the
**hybrid look** (`src/hybrid.py`): paper/ink engine below, charcoal wedge above the character's
diagonal — the split of the reference portrait.

## 1. Character — SHADE on the toon 3D rig
* Same solver (`toon._skeleton`) → every pose generator of the shipped film runs unchanged:
  idle, walk, squat cycle, double-biceps flex, hands-on-hips power stance, reading, calm
  breathing, flinch, present, point, hold, cheer, plus SHADE's own pocket stance (the reference).
* Own proportions `shade.SP` (head ≈ 1/5.2 of height, shoulders .122, arms .342, legs .400).
* Black cloth is lit, not shaded: key rim (222,226,236)·70 % upper-left, fill rim ·34 % lower-right,
  form lift 30 %, AO 42 %, knit crackle on the hood only, satin on the lapels.
* Face = void + glowing wedge eyes + crescent smirk; 15 expressions in `shade.EXPR`; the glow
  level is animated per beat (`hero(..., glow=)`), the eyes can open from closed (`blink=`) and
  be re-tinted (`eyes=` — the red flash in S4 swaps `GLOW/GLOW_T/GLOW_C` for one draw).
* Two fit changes versus the stickman film, both measured on stills:
  `p_read2` (hands lower: az 52 / ef 14, chin 18°) and `book2` (panel width .48·hand-span + 12)
  so the open book sits under the face instead of on it; `squat_shift()` uses SHADE's leg lengths.

## 2. Hybrid look — the diagonal is a character
* Split from (0, 1000) to (1080, 540), both ends drifting (±28 / ±22 px, two slow periods) —
  nothing is ever still. Dark = (38,36,41) with a top-left lift and a whisper of the scene accent;
  seam = accent glow (quarter-res blur) + 4 px hairline.
* Contract (asserted on every frame at build time, `on_paper()`): every ink-on-paper element —
  dumbbell, habit boxes, 20-min ring, book stack + label, balance, S4 tick, payoff line, caption
  left end — sits ≥ 40 px under the LIVE wedge. Elements allowed in the dark are self-lit:
  "+1" badges, "!!!" burst, S6 glow ticks, the S2 sun; the rings are paper discs.
* Chrome and headlines live on the dark in paper-coloured extruded type; hot words use
  `hybrid.hot(si)` — measured ≥ 4.8:1 on the dark (4.9 / 5.13 / 4.87 / 5.57 / 5.35 / 6.39),
  paper-on-dark 12.6:1.
* Scene-driven wedge offsets (`wedge_drop`): S1 +400 px lifting on "Powerful man banna hai?"
  (0.50–1.35 s), S4 +260 px surge on "Gussa aaye" (0.36 s in, 2.25 s recede with the ring),
  S6 −44 px flinch on "shuru". Each was sized so the per-frame luma step stays under the
  gate (`max_dluma < 8`): S1 ≈ 3.7 / frame peak, S4 ≈ 5.1 / frame peak.
* Transition: the v9 tinted swipe, slanted parallel to the seam and two-toned — every band
  element (tint, glow stripe, ink hairline) has a paper variant below the wedge line and a
  charcoal variant above it, so crossing the dark zone is not a luma step. Build 1 measured
  the single-tone version at +7 / frame when the stripes entered the wedge, and +11.4 / frame
  when the band crossed SHADE (a 7 % dark mass; the thin v1 stickman never showed this). Fix:
  the outgoing scene layer dissolves over the band's first half (7 frames, `e_io`), so the hero's
  luma is spread instead of stepped. Build 2: max step 5.95 / frame, 0 frames over 8.

## 3. Beats (what changed per scene)
| S | VO cue | SHADE beat |
|---|--------|-----------|
| 1 | 0.10–0.45 / 0.55 / 0.50–1.35 | eyes open in the dark → smirk → the light arrives (wedge lifts 400 px); pocket stance |
| 1 | 1.80 "muscles se nahi" | slow head-shake at the dumbbell (yaw ±8°, two cycles), 'determined' |
| 1 | 3.30 "aadaton se" | pocket → power stance (0.7 s eased blend), glow flare, habit boxes tick |
| 2 | 0.96 "roz subah" | paper-toned sun rises out of the seam (clipped exactly to the dark side) |
| 2 | 3.45 flex | eyes flare 1.35× with the double-biceps, 'grin' on "dimagh mazboot" |
| 3 | 3.40–4.65 count | eye glow climbs with the 3,650 counter |
| 3 | 4.75 "kamra chalata hai" | chin lifts from the book to the lens (`p_read_up`), 'proud' |
| 4 | 2.08 "Gussa aaye" | eyes flash RED, the dark surges 260 px over him, "!!!" cracks in |
| 4 | 2.80–5.05 | eyes close ('calm'); the dark recedes as the 10-second ring drains |
| 5 | 2.45 / 2.95 / 3.45 | "+1" badges rise from the hand out of the paper into the dark |
| 6 | 0.09 / 0.98 / 1.84 / 2.82 | JISM · DIMAGH · CONTROL · VALUE switch on as glowing ticks inside his dark |
| 6 | 4.74 "shuru" | the dark flinches back 44 px once, eyes flare, cheer; pill + bookmark as v1 |

## 4. Layout (1080 × 1920, safe area y 180–1500)
chrome 142 / 198 · headlines 318+436 (S1), 348 (S2–S5), 318+426 (S6) · hero feet GY 1298 ·
payoff 1374 · captions 1440 (fit ≤ 936 px, floor 40 px) · camera Z0 1.020, AMP ≤ .024 (caption
bottom ≤ 1497 measured in v1, unchanged rig).
Hero: S1 x 470 s 580 · S2 x 340 s 540 · S3 x 320 s 520 · S4 x 350 s 540 · S5 x 290 s 510 · S6 x 540 s 500
(≈ +8 % versus the stickman because SHADE's head is 1/5.2 of the height, not 1/4).

## 5. Audio
Unchanged from v1 (`VIDEO_POWER_NOTES.md` §5): bed .70 into the duck, VO chain, loudnorm −11,
DRV 1.25 → alimiter .74, extrastereo 2.4, apad bounded, `-t 42`. The mute master is the only input
that changed, so the delivered loudness/peak/correlation numbers are expected to match v1 within
measurement noise — see §7.

## 6. Gate changes
`gate_shade.py` = `gate_power.py` with one instrument re-calibrated: the black-sliver detector
counted edge pixels < 40/255 (> 50 % of the frame edge). The hybrid frame has a deliberate
charcoal wedge (38,36,41 → ≈ 37 grey) on the top/left edges, so that test would flag the look
itself. A transform sliver is 0 and the charcoal never decodes under ~28, so a sliver is now
"an edge line ≥ 95 % below 12/255". The geometric guarantee (sampled rectangle inside the
source) is still asserted on every frame in `render()`.

## 7. Delivery (filled by the build)
| item | value |
|---|---|
| file | `shade_power_42s.mp4` — 1080 × 1920 · 30 fps · 1260 frames · 42.000 s · H.264 + AAC |
| size | 15,908,959 B |
| sha256[:16] | `3a0de99bc85e1caa` |
| md5 | `c9f8c2f4fedb36d80d16edbd60953c05` |
| Drive | folder `stickman POWERFUL MAN 42s` (`1YSvMC-paJWQHVJEBpBZ0Mybp-WxshcPO`) → file id `1rsJq7Y4wpQaKEsK7Zd7LNhiTqBYBUlJM` (Drive md5 matches local) |
| build | `bash build_shade.sh` — shards 18:47:21–18:51:56 UTC (0.44 s / frame × 2 shards), bed, mux (locked v1 chain, `OUT` override), gate 18:53 UTC |
| loudness | integrated −11.7 LUFS · decoded peak −1.49 dBFS · true peak −1.1 dBTP · short-term min −12.7 LUFS |
| video gates | frames 1260 · identical 0 · max_dluma 5.954 (< 8) · frames > 8: 0 · black-edge (sliver) 0 · min_scene_p10 0.1521 · jerk_p95 1.697 |
| audio gates | lr_corr 0.7515 · side_mid 0.377 · 120–500 Hz 54.3 % · bed 4–8 kHz 11.7 % · VO 4–8 kHz 10.7 % · bed 20–120 Hz 15.3 % · av_delta 0.037 s · longest silence 0.25 s |
| result | **ALL 18 GATES PASS** (`build/gate_shade.log`) |

Build 1 (18:35–18:41 UTC) failed two gates — `max_dluma 11.392`, `frames_dluma_gt8 3` — all three frames
were the swipe crossing SHADE at the S1→S2, S3→S4 and S4→S5 cuts (frames 191, 580, 782). The fix is
described in §2 (two-tone stripes + dissolve-under-wipe); nothing else changed between the builds.

Comparison with v1 (`stickman_power_42s.mp4`): same VO, same bed, same mux constants, same 42.000 s,
same caption timing; audio numbers are identical to v1 within the gate's print precision, as expected
(the audio chain was not touched). Video: v1 max_dluma was the v9 swipe over a thin stickman; v2 adds a
dark wedge, a 7 % hero and three scene-driven wedge moves and still lands at 5.95.
