# shade_respect_90s.mp4 — "LOG AAPKI IZZAT KYUN NAHI KARTE" (90 s, SHADE hero, hybrid look, cinematic layer)

**Deliverable:** `shade_respect_90s.mp4` · 1080×1920 · 30 fps · exactly **2700 frames = 90.000 s** · H.264 yuv420p + AAC 48 kHz stereo.
Hashes, size and the forensic gate table are in `BUILD_RESULT` at the bottom of this file (filled by the build).

## What it is
The third short on the same pipeline identity (v9 vertical → POWER v1 → SHADE v2 → **RESPECT**):
the hooded black-suit character **SHADE** (the user's own main character, 3D-rigged in `src/shade.py`),
the **hybrid** charcoal/paper split (`src/hybrid.py`), extruded two-tone chapter type, paper tags,
word-locked ASMR bed, chrome (chapter counter `01/09`, progress line, labels).

New in this short — the **cinematic layer** (`src/respect.py`):
- **Dolly** — a per-scene world scale about the floor centre (`dolly(si, lt)`), UI stays static; nine
  camera amplitudes `AMP` (slow push-ins, one pull-back for the payoff).
- **Parallax** — the far plane (room silhouettes, dust) is pulled at 0.5× of the camera pan (`par`).
- **Depth of field** — far-plane figures are SHADE's rig flattened to one tone, Gaussian-blurred per
  distance (`silhouette`, blur 4–6 for the back row, 1.5 for the near "loud" man).
- **Light** — soft shaft from the top edge at the turn (S3) and the payoff (S9), quarter-res blurred;
  dust motes only in the dark half ("paper has no air to catch the light").
- **Slow-mo moments** — the head lift in S3 (ignition), the five heads turning one by one in S9.
- **Reflection** — the hero's soft floor reflection in S7 (the walk).

## Story (9 chapters, Roman Urdu on screen, Urdu script to the TTS voice `voice-01`)
| # | chapter | VO at | beat |
|---|---|---|---|
| 1 | HOOK | 1.200 | you walk into the room — nobody looks up. "Jawab kadwa hai." |
| 2 | VILLAIN | 9.288 | every HAAN is a tag that lands on the pile; "Kisi ka nahi" |
| 3 | TURN | 18.614 | he lifts his head; the light shaft; five chips: "5 RULES AAJ SE" |
| 4 | KAM BOLO | 25.508 | the loud man's bubbles shrink to nothing; one word → the room leans in |
| 5 | WAQT | 35.638 | the phone buzzes, he doesn't look; his time has a price bar |
| 6 | NA | 44.846 | the HAAN pile, the NA stamp slams, the tags blow away, the excuse is crossed out |
| 7 | KAMAR | 53.924 | slumped → the spine draws → the slow walk, "Jism pehle bolta hai" |
| 8 | LAFZ | 63.364 | a hundred ticks, one crack, the shatter, the wax seal |
| 9 | PAYOFF | 73.472 | he walks back into the same room; five heads turn; "IZZAT KHAMOSHI HAI"; recap; FOLLOW · SAVE |

Timeline is locked in `src/timeline_respect.py` (SCENE_START/END, VO_AT, ADELAY_MS, PHRASES = measured
phrase onsets from the fitted clips). Voice runs at the recorded tempo — no `atempo`, clips are trimmed and
padded only (`src/vo_fit.py` → `assets/r{1..9}_fit.wav`, 67.84 s of speech in 90 s).

## Audio
`src/make_asmr_respect.py` — the POWER instrument (pads with nothing under 110 Hz, pulse/hat/shaker grid,
swipe recipe, air band, swells in every VO hole ≥ 0.5 s) with a 9-chord plan (Dm · Bb · F · Dm · Bb · C · Gm · F · Dm)
and 539 word-locked cues (tag lands, nods, stamp, blow-away, spine riser, ticks/crack/shatter, seal, five head turns,
pill). Mix chain is the locked POWER chain (`src/mux_respect.sh`): bed 0.70 / VO drive 1.25 / limiter 0.74 /
stereo 2.4, loudnorm I=-11 TP=-1.6, VO centred, bed wide.

## Forensic gate (`src/gate_respect.py`, same 18 instruments and thresholds as POWER/SHADE)
See `BUILD_RESULT`. Thresholds: max_dluma < 8, frames_dluma_gt8 = 0, black_edge = 0, min_scene_p10 > .12,
jerk_p95 < 2, lr_corr .55–.80, side_mid > .25, all_120_500 < 58, bed_4000_8000 > 10, vo_4000_8000 > 5,
bed_20_120 < 48, peak ≤ −1 dBFS, LUFS −12.5..−10.5, short_term_min > −30, av_delta ≤ .1, silence < 1.2 s.

## Ledger additions (50–53)
50. Wedge offset must be continuous across cuts — a 160 px jump under the band ≈ 15 luma. `wedge_drop` eases inside the receiving scene.
51. Far-plane silhouettes = the hero rig flattened to one tone, blurred by distance; cached per 1/6 s pose bucket.
52. **Never key a sprite cache on a continuously animated value.** Dolly size, head angle and fade alpha each multiplied the cache until the shard was OOM-killed (first build attempt). Quantise (size /16 px, head /2°), apply alpha at paste time, bound the cache (72 entries ≈ 80 MB).
53. Dolly = world scale about the floor centre; UI static. Props placed in world space go through `wx()`; the on_paper assert is evaluated on screen coordinates.

## Rebuild
`bash build_respect.sh` → 2 render shards (0–1350, 1350–2700) → bed → concat → mux → gate → hashes (≈15 min).
Stills/contact: `python3 src/respect.py still 28.6` · `python3 src/respect.py contact 0.6 5 12 ...`.

## BUILD_RESULT (final — build 4, 2026-10-08 21:17 UTC)

| file | frames / dur | bytes | sha256[:16] | md5 |
|---|---|---|---|---|
| `shade_respect_90s.mp4` | 2700 f / 90.000 s (1080×1920, 30 fps, H.264 + AAC) | 33,808,670 | `f3d0f1a21ec59b00` | `839b95bbf35d96bf4fa26eb811f680e1` |

Shards (sequential): `respect_shard0.mp4` 25,205,384 B (frames 0–1349) · `respect_shard1.mp4` 21,233,712 B (1350–2699) ·
render 441 s + 428 s · bed 7 s · mux 109 s · gate 26 s.

### Gate table (src/gate_respect.py, thresholds = POWER)
| gate | value | rule |
|---|---|---|
| frames | 2700 | == 2700 |
| identical_frames | 0 | == 0 |
| max_dluma | 5.702 | < 8 |
| frames_dluma_gt8 | 0 | == 0 |
| black_edge_frames | 0 | == 0 |
| min_scene_p10 | 0.1309 | > 0.12 |
| jerk_p95 | 0.681 | < 2.0 |
| lr_corr | 0.6492 | 0.55–0.80 |
| side_mid | 0.462 | > 0.25 |
| all_120_500_pct | 55.9 | < 58 |
| bed_4000_8000_pct | 10.7 | > 10 |
| vo_4000_8000_pct | 8.5 | > 5 |
| bed_20_120_pct | 5.2 | < 48 |
| decoded_peak_dBFS | −1.77 | ≤ −1.0 |
| lufs_integrated | −12.0 | −12.5..−10.5 |
| short_term_min_LUFS | −15.9 | > −30 |
| av_delta | 0.005 s | ≤ 0.1 |
| longest_silence_s | 0.0 | < 1.2 |
**ALL 18 PASS.** (true_peak −1.6 dBTP.)

### Build history
| build | result | cause → fix |
|---|---|---|
| 1 (20:17) | shard 0 OOM | sprite cache keyed on animated values → quantise + bound (ledger 52) |
| 2 (20:21) | shard-0 encoder OOM | two parallel shards → sequential (ledger 54) |
| gate 1 (20:48) | 16/18 | VO bus ended at 84.94 s → bed silent 4.56 s; lr_corr .45 → `apad` the VO bus (ledger 55) |
| gate 2 (20:52) | 15/18 | voice-01 sibilants flat-topped the limiter, AAC overshoot → decoded peak 0 dBFS; bed air 9.3 % → de-esser i.7 m.75 f.4, LIM .71, XS 1.7, hiss +2.4 dB, tail air (ledger 56) |
| gate 3 (20:59) | 18/18 | contact sheet: S2 caption 1014 px and S8 caption 1147 px over CAP_MAX_W 936 (S8 clipped at the right edge) → captions shortened, all ≤ 936 px at the 40 px floor |
| **4 (21:17)** | **18/18** | delivered; contact sheet re-generated from the delivered file and reviewed |

### Final mix constants (src/mux_respect.sh)
BEDV .70 · DRV 1.25 · LIM .71 · XS 1.7 · VOF: highpass 90 → EQ +3.6 dB @ 3.1 k → treble +2.8 @ 7.4 k → **deesser i=0.7 m=0.75 f=0.4** → compressor; VO bus `apad=whole_dur=90.4` before `asplit`;
sidechaincompress thr .024 ratio 5; loudnorm I −11 TP −1.6; treble +3.4 @ 9 k; D 90 / PADD 90.4.
Bed (src/make_asmr_respect.py): side boost 2.30, hiss .0082, tail_air + 3× tail_shimmer + 5× tail_tick after end_bell.

### Incidents
2 OOM kills (sprite cache, parallel encoders) · 1 resume-script frame-count bug (ffmpeg 7 `-c copy` prints no `frame=`) ·
VO-bus tail silence · voice-01 sibilance vs limiter/AAC · two captions over CAP_MAX_W (one clipped) — all fixed before delivery.

---

# v2 — `shade_respect_v2.mp4` (75.19 s · 33 shots · 32 distinct transitions · new bed)

## Why a v2 (the user's four notes on v1)
1. v1 reached 90 s through long pauses (22 s of air; chapter tails 1.3–2.6 s) — the voice must flow.
2. Something new must happen on screen every 2–3 s — "wtf yeh kya ho raha hai" level, 3-D, cinematic.
3. The continuous "radio" sound (noise floor) must go; SFX were good but one cue repeated.
4. Transitions must not repeat — varied, 3-D, something different each time.

## What changed (same identity: SHADE hero, hybrid look, cinematic layer, voice-01, chrome, caption rules)
- **Timeline** `src/timeline_respect2.py`: identical nine fitted clips (`assets/r1–r9_fit.wav`); chapter
  breath 0.55–0.70 s split lead 42 % / tail 58 %; cold open 0.60 s; end card 1.85 s → **75.19 s / 2256 f**,
  voice share 90.2 % (v1 75 %). VO_AT 0.600 · 7.538 · 15.814 · 20.558 · 29.488 · 37.496 · 45.424 · 53.564 · 61.872.
- **Shots** `src/respect2.py` (imports `respect.py`, re-points its timeline globals): 33 shots, 0.94–4.96 s,
  median ≈ 2.2 s. Each chapter keeps its v1 scene as the "wide" and gains 1–4 inserts
  (`ins_*`): bowed heads, the question close-up, the HAAN nod, the crowd grid, the head lift, the rule
  numeral card (3-D extruded numeral turning in the dark, rule words in ink on paper, hero small), the
  sound-ring, the turning room, the clock, the pings, the NA stamp, the pile, the walk with ghost trails,
  the hood close-up (eyes ignite, anamorphic flare, clipped at the seam), the broken plate, the scale,
  the three heads, the flatline, the recap carousel, the follow/save end card.
- **Transitions** (`respect2.TRANS`, 15 kinds, `PLAN` = 32 boundaries, never the same kind twice in a row):
  cube_h · cube_v (two faces of a box turning), zoom-through, whip_h · whip_v (motion-blur pass),
  iris, slices (five strips), ink (coarse ink-bleed field), wedge (the seam itself wipes), card
  (horizontal push with a shadow edge), spin, sweep (light bar), blur (defocus cross), doors, shatter
  (RGBA tiles). Durations .34–.70 s; `fillcolor=DARK` on every warp; both neighbours on the hybrid palette.
  Plan: S1 zoom/whip_h/sweep/cube_h · S2 blur/whip_v/iris/wedge · S3 zoom/doors · S4 spin/whip_h/slices/cube_v ·
  S5 ink/blur/card · S6 whip_v/zoom/iris · S7 sweep/whip_h/whip_v/slices/cube_h · S8 shatter/ink/wedge ·
  S9 blur/card/doors/zoom.
- **Bed** `src/make_asmr_respect2.py` → `build/asmr_bed_respect2.wav`, `ASMR_RESPECT2_LEDGER.csv` (419 events):
  no `room`/`hiss` floor, no 0.6 s hat/shaker/pulse grid. New voices: braam (once, the hero's entrance),
  reverse swell, glass ting, metal ring, paper slide, doppler whip, impact, heartbeat (S2 only), glass
  burst, click. One matched cue per transition kind (`tr_cue`), read from `respect2.PLAN`; nine different
  payoff instruments (bell · glass · metal · pluck · glass-hi · low chime · shimmer+bell · metal-hi · end bell);
  pads + per-chapter pluck patterns + swells in the VO holes kept. Bed-only passages (8.2 s) measured before
  the mux: 20–120 Hz 6 % · 120–500 Hz 50 % · 4–8 kHz 18 %.
- **Mux** `src/mux_respect2.sh` = v1 chain (de-esser, BEDV .70, DRV 1.25, LIM .71, XS 1.7, I −11), only D/PADD/OFFS changed.
  **Gate** `src/gate_respect2.py` = v1's 18 instruments on `timeline_respect2` (scene p10 skips 10 f at each cut).
- **Build** `build_respect2.sh` (shard 0) → card-push fix → `build_respect2_b.sh` (fix range 1100–1128, shard 1,
  filter-concat mute master crf 16) → `finish_respect2.sh` (bed → mux → gate).

## Fixes made during the build (measured, not eyeballed)
- Rule numeral cards: the rule words at y 860 crossed the seam (light text on paper) → ink words on paper at y 1130,
  measured ≤ 700 px, hero moved right (x 930, s 300). Hood close-up: hero at s 1500 clipped to the dark half, headline
  moved to an ink line at 1130 (the 84 px line overflowed 1080 → `ink_line` fits to W − 160).
- Ink reveal: the 27×48 noise field read as a maze → 6×11 field, blur 22 at quarter size (big organic blobs).
- Card push, vertical: B's dark top slid over A's bright paper → frame mean dipped 18/frame (12 frames > 8 at 37.2 s in
  shard 0). Rewritten horizontal (both halves keep their dark/paper structure): 4.7 / 6.0 per frame at 37.27 / 66.00.
- Bed: `pad1` at t = −0.25 was silently dropped by `place_st` in every earlier bed (the hiss hid it) → clamp to 0.
- Gate found (ledger 61): wedge ran B→A→B (inverted mask) → fixed, soft 110 px edge, TD .64; iris radius 2300 → 1260·√e (area-uniform); quintic ease `e_q` on whips/cube/doors/iris/sweep/wedge; carousel chips fade+scale in; S1 payoff sweep ends ON the beat (boundary 5.59 → 5.29); whips TD .34 → .50, cubes .50 → .60 with lighter face shading, doors/sweep .60.
- Mix: without the hiss the honest `all_120_500` was 60.9 % → VO 250 Hz −5.4 dB + 160 Hz −1.5 dB and a five-partial pad → 56.0 %.

## BUILD_RESULT_V2 (final — 2026-10-09 13:34 UTC)
`shade_respect_v2.mp4` · 2256 f / 75.190 s · 1080×1920 30 fps H.264 (crf 23, maxrate 2800k) + AAC 192k · **28,432,377 B** ·
md5 `8d91be52ab969e0b23f21bf6bab0df85` · Drive `1fu_g2HTNZVRqE3XBKdUKZoj6O8tIdkpu` (folder "stickman IZZAT 90s" `1_MhRILyCB86LWHYqLDzBPvmneA6Y2uqo`, md5 verified on upload).
Gate `src/gate_respect2.py` — **19/19 PASS** (18 v1 instruments + `trans_jerk_max`; `jerk_p95` now on shot frames — ledger 61):

| gate | value | threshold |
|---|---|---|
| frames | 2256 | == 2256 |
| identical_frames | 0 | == 0 |
| max_dluma | 6.749 | < 8 |
| frames_dluma_gt8 | 0 | == 0 |
| black_edge_frames | 0 | == 0 (no slivers |
| min_scene_p10 | 0.1415 | > 0.12 |
| jerk_p95 | 0.501 | < 2.0 (shot frames |
| trans_jerk_max | 7.964 | < 8.0 (no step inside a transition larger than the cut cap |
| lr_corr | 0.6535 | 0.55-0.80 |
| side_mid | 0.458 | > 0.25 |
| all_120_500_pct | 56.0 | < 58 % |
| bed_4000_8000_pct | 13.1 | > 10 % (sound-design air |
| vo_4000_8000_pct | 9.0 | > 5 % (speech presence |
| bed_20_120_pct | 7.6 | < 48 % (no boom |
| decoded_peak_dBFS | -1.26 | <= -1.0 dBFS |
| lufs_integrated | -11.6 | -12.5 .. -10.5 LUFS |
| short_term_min_LUFS | -13.3 | > -30 LUFS (never breathes out |
| av_delta | 0.0 | <= 0.1 s |
| longest_silence_s | 0.0 | < 1.2 s |

Transition windows (final master, 180×320 probe): worst `trans_jerk_max` whip_v@49.37 7.96 · sweep@5.29 7.79 · slices@27.78 7.62 · doors@68.64 7.48; worst Δluma 6.75. Render: shard 0 10.3 min + shard 1 10.1 min (0.55 s/frame, sequential — ledger 54), transition windows re-rendered three times via `src/patch_windows.py` / `src/splice_windows.py` (streaming splice; a full-film float32 probe array in RAM hung the 2 GB sandbox for 25 min — keep probes uint8 and per-window). Audio: VO 250 Hz −5.4 dB / 160 Hz −1.5 dB (`LM250`/`LM160` in `src/mux_respect2.sh`), everything else the v1 chain.
Mixdown numbers: −11.6 LUFS · TP −0.8 dBTP · decoded peak −1.26 dBFS · L/R corr .654 · side/mid .458 · all 120–500 56.0 % · bed 4–8 k 13.1 % · VO 4–8 k 9.0 %.
Companion files: `shade_respect_v2_contact.png` (33 shot mid-frames), `ASMR_RESPECT2_LEDGER.csv` (419 events), `src/timeline_respect2.py`, `src/respect2.py`, `src/make_asmr_respect2.py`, `src/mux_respect2.sh`, `src/gate_respect2.py`, `build_respect2.sh`, `build_respect2_b.sh`, `finish_respect2.sh`, `src/patch_windows.py`, `src/splice_windows.py`.
v1 (`shade_respect_90s.mp4`, Drive `1FtRyxIvEnBldm6_DGnGPWHcvNRPznzAQ`) stays on Drive as the 90 s cut; the local copy was moved out of the persisted tree (cap).
