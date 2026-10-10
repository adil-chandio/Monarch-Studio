# POWERFUL MAN — 42 s short (v9 engine, next build)

`stickman_power_42s.mp4` · 1080×1920 · 30 fps · **42.000 s** · 1260 frames · 15.88 MB
sha256[:16] `4c5a5c79c4408386` (rebuilt on a fresh box; the first build was `3af2f5fda7a99b2d` — frames are identical, the container sha is not reproducible across libx264 thread scheduling; the gate measures the file, every number below re-measured identical) · **−11.7 LUFS** · decoded peak **−1.49 dBFS** · L/R corr .752 · side/mid .376
Gate: `python3 src/gate_power.py` → **ALL 18 GATES PASS** (log `build/gate_power.log`).

Same editing as the shipped money short (v9 `30a5f761d3f14ad6`): paper/ink Style B,
extruded type, 3D-rig hero, one tinted swipe per cut, ASMR bed, chapter chrome,
locked vertical grid (safe area y 180–1500). New topic, new timeline, six new
poses, and every animation weakness that was measured in v9 is fixed here.

---

## 1. What is new on top of v9 (each one is a measured v9 weakness)

| # | v9 | this build | proof |
|---|---|---|---|
| 1 | pose changes were **hard switches** (`p_point if lt > .9 else p_think`) | `blend(fa, fb, t, t0, d, s)` — every pose change is a 0.5–0.75 s eased blend with overshoot (`e_back`), feet re-grounded by the solver | jerk p95 **1.77** (v9 1.62, gate < 2.0) with 3× more pose changes per scene |
| 2 | 5 stock poses | **6 new poses on the v9 3D contract**: squat cycle `p_squat(t,q)`, double-biceps `p_flex`, hands-on-hips `p_power`, `p_read`, calm breathing `p_calm`, `p_flinch` | S2 three real squats, feet planted within 15 px (measured on the lowest-sole band) |
| 3 | hero stared ahead | `look=` — the hero **glances at the prop the viewer should read next** (`glance()` on the dumbbell, ring, scale) | law 6 "eye-line leads the eye" |
| 4 | odd scenes dipped to z 0.990 → **black slivers** (ledger 32) | zoom floor `Z0 = 1.020`, per-frame assert that the sampled rect is inside the source, `black_edge_frames` gate | **0** black-edge frames |
| 5 | eased camera (zero-velocity apex) | linear-dominant ramp + **triangle pans** (ledger 33) | per-scene p10 ≥ **0.177** on all six scenes (v9 S2 0.24, S5 0.22; gate > 0.12) |
| 6 | VO time-stretched (`atempo` 1.35–1.53) | **no atempo** — pauses capped at 0.30 s, head/tail trimmed (`src/vo_fit.py`), picture cut to the voice | natural voice; all six clips land within +5 ms of plan (cross-correlation on the delivered file) |
| 7 | captions a fixed 50 px | `caption_fit()` measures the text extent and scales to the 936 px safe width (floor 40) | five long captions no longer touch/clip the frame edge |
| 8 | expressions: 8 | `calm` / `calm_smile` (eyes shut) added to `toon.EXPR` for the breathing beat | S4 |
| 9 | props froze when revealed (fixed in v9 with `fl`) | kept — ring, book stack, scale pans, ticks all breathe; **new**: page turns, +1 badges, 10-second drain, scale tilt with physics-eased pans, confetti with per-piece tumble | p10 table below |

Per-scene p10 frame-diff on the delivered file (180×320 probe, swipes excluded):
S1 .205 · S2 .206 · S3 .228 · S4 .186 · S5 .202 · S6 .177 — darkest frame luma 208.6, global min diff .072 (nothing frozen).

---

## 2. Timing contract (immutable once the first frame was drawn)

`src/timeline_power.py` — the voice is the clock.

| scene | name | start | end | dur | VO at | VO len | lead | tail |
|---|---|---|---|---|---|---|---|---|
| 1 | HOOK | 0.000 | 6.376 | 6.376 | 0.300 | 5.626 | .30 | .45 |
| 2 | JISM | 6.376 | 12.362 | 5.986 | 6.426 | 5.516 | .05 | .42 |
| 3 | DIMAGH | 12.362 | 19.348 | 6.986 | 12.412 | 6.516 | .05 | .42 |
| 4 | CONTROL | 19.348 | 26.068 | 6.720 | 19.398 | 6.250 | .05 | .42 |
| 5 | VALUE | 26.068 | 33.084 | 7.016 | 26.118 | 6.546 | .05 | .42 |
| 6 | GO | 33.084 | 42.000 | 8.916 | 33.134 | 8.122 | .05 | .744 |

`ADELAY_MS = [300, 6426, 12412, 19398, 26118, 33134]` — used verbatim by `src/mux_power.sh`.

### VO fit (no time-stretch)
| clip | raw TTS | pauses cut | edges cut | fitted |
|---|---|---|---|---|
| p1 | 6.72 | 0.55 | 0.52 | **5.626** |
| p2 | 6.84 | 0.69 | 0.61 | **5.516** |
| p3 | 7.60 | 0.62 | 0.44 | **6.516** |
| p4 | 7.76 | 1.02 | 0.45 | **6.250** |
| p5 | 8.16 | 0.95 | 0.64 | **6.546** |
| p6 | 9.88 | 1.18 | 0.53 | **8.122** |

47.3 s of raw TTS → 38.58 s of voice at pitch, in 42.0 s of picture. Internal pauses > 0.30 s were shortened to 0.30 s (−34 dB, ≥ 0.16 s detector); nothing inside a word was touched. **Please listen once** — the pause tightening is measured, not auditioned.

### Word-locked beats (scene-local seconds, from the fitted clips)
S1 0.34 *Powerful man banna hai?* · 1.80 *Taqat muscles se nahi* (dumbbell in 1.80, crossed 2.55) · 3.36 *aadaton se aati hai* (rise to power stance 3.30, four boxes 3.42) · 4.59 *Yeh chaar aadatein pakdo* (payoff 4.60)
S2 0.09 *Pehli aadat* · 0.96 *roz subah 20 min jism ko tapao* (ring 0.95, squats 0.75→3.45, fill 1.30→3.40) · 3.63 *Jism mazboot* (flex 3.45) · 4.57 *toh dimagh mazboot* (payoff 3.65)
S3 0.09 *Dusri aadat* · 1.09 *roz das page padho* (book 0.35, pages 1.10+, stack 1.15+) · 2.71 *Saal ke* (×365 label 2.75) · 3.41 *teen hazaar page* (counter 3.40→4.65) · 4.79 *Jaanne wala hi kamra chalata hai*
S4 0.09 *Teesri aadat* · 1.02 *self-control* · 2.10 *Gussa aaye* (burst 2.08, flinch 2.10) · 2.97 *das second chup* (ring 2.90, drain 3.10→4.95, eyes shut) · 3.97 *Jo khud ko jeete* (tick 4.95) · 5.20 *woh sab jeet leta hai* (payoff 5.15)
S5 0.09 *Chauthi aadat* · 1.03 *apni value banao* (scale 1.00) · 2.44 *Ek skill* (+1 badges 2.45/2.95/3.45) · 3.29 *roz behtar* · 4.26 *Powerful aadmi mangta nahi* (cross 4.30, tilt 4.40→5.70) · 5.99 *deta hai* (tick 5.95, payoff 5.90)
S6 0.09 *Jism* · 0.98 *dimagh* · 1.84 *control* · 2.82 *value* (four ticks on the words) · 3.52 *bas chaar* · 4.21 *Aaj se* · 4.77 *shuru* (cheer 4.70) · 5.60 *Follow karo part two ke liye* (pill 5.55, confetti 5.40) · 6.92 *aur save karna mat bhoolna* (bookmark 6.90)

---

## 3. Grid, type, colour (unchanged v9 contract)

chrome 142–210 · headline 300–520 · graphic 560–1060 · stage to GY 1298 · payoff 1374 · caption **1440** (v9 1452 — see §6 #44) · safe area y 180–1500.
Accents per scene (v9 palette, 4.69–9.17:1 on paper): HOOK red · JISM blue · DIMAGH violet · CONTROL rust · VALUE green · GO ochre.
S1 headline is two lines (POWERFUL / BANNA HAI?) — the one-line version measured 1206 px at 112 px type.

Under the camera (z 1.020–1.044, pans 7/9 px) the worst-case output positions are: caption glyph bottom **1495**, headline top **209**, payoff/caption gap 14 px — all inside the safe area, measured over all 1260 frames.

---

## 4. Audio — `src/make_asmr_power.py` (+ `ASMR_POWER_LEDGER.csv`, 316 events)

Same instrument as v9 (`make_asmr.py` imported, voices / `place()` / `pad()` / `silk()` / mastering reused), new song:

* 42.0 s, six chapters from the timeline module (cues cannot drift).
* **100 BPM** (SPB 0.600; v9 112). D minor **Dm Bb F C Gm Dm**, nothing below 110 Hz in the pads.
* Pad swells are **measured, not hard-coded**: `vo_holes()` scans the fitted VO at the timeline offsets and drops a swell into every gap ≥ 0.5 s (the five scene breaths + the tail).
* New voice `air()` — band-limited noise 4.2–9.2 kHz. The v9 `tap` voice is capped at 3.2 kHz and physically cannot carry the 4–8 kHz "air" gate.
* Transitions: v9 shape (riser → swipe → thud + drop → bell), with the drop/thud trimmed (.34/.24 → .08/.11) and a swipe-air, paper-flick and two shimmers added.
* ~190 word-locked cues: footsteps, slump, dumbbell + cross swishes, four habit boxes, squat down/up ×3 with sub, ring quarter-ticks, flex whoosh+bell, book open, 8 page turns, 10 stack pops, counter roll, trigger burst (pop+thud+air), breath-in, ten clock ticks, scale metal, +1 ×3, tilt creak, cheer, confetti scatter ×10, pill thud+bell+sheen shimmer, bookmark, outro D6 bell.

### Mux chain — `src/mux_power.sh` (locked by measurement)
```
VO : 6× [aresample 48k, stereo, adelay] → amix → highpass 90, eq 250 −4.2, eq 430 −1.6,
     eq 3100 +3.6, treble +2.8@7400, acompressor .045/3.6/10/170/mk1.5, volume 1.92 → asplit
bed: volume 0.70  (v9 0.60)
duck: sidechaincompress thr .024 ratio 5 attack 6 release 260          (v9 values)
mix: amix "1 1" normalize=0 → treble +3.4@9000 → extrastereo m=2.4 → loudnorm I=-11:TP=-1.6:LRA=9
     → volume 1.25 → alimiter limit=0.74 attack 5 release 60 level=disabled
     → apad=whole_dur=42.4, atrim=0:42.0, asetpts=N/SR/TB
vid: libx264 preset slow crf 23 maxrate 2800k bufsize 5600k high@4.0 g 60 yuv420p · aac 192k 48k · +faststart · -t 42.000
```

### How the four audio parameters were found (audio-only test muxes, `AUDIO_ONLY=1`)
| step | change | LUFS | dec. peak | L/R corr | bed 4–8 k | result |
|---|---|---|---|---|---|---|
| v9 chain verbatim (bed .60, lim .63) | — | −13.2 | −3.61 | .835 | 1.4 % | 4 fails |
| + extrastereo 1.85, lim .80 | width | −12.3 | −1.40 | .627 | 1.9 % | air still missing |
| bed re-voiced (no D2 root, `air()`, trims) | spectrum | −12.4 | −0.43 | .751 | 10.6 % | peak over |
| lim .74, I −10.5 | ceiling | −12.8 | −2.13 | .790 | 11.0 % | **loudness wall** — LUFS no longer follows I |
| drive 1.25 into the lookahead limiter | crest | −11.3 | −1.16 | .764 | 10.2 % | loud, air thin |
| pads .80, swells .048 | air margin | −11.7 | −1.42 | .815 | 12.6 % | corr up — pads *are* the width |
| bed .70, extrastereo **2.4**, drive **1.25**, lim **.74** | balance | **−11.7** | **−1.49** | **.752** | **11.7 %** | all pass — v9's stereo signature (.7547 / .374 / −11.7) reproduced |

---

## 5. Forensic scorecard — delivered file

| test | result | gate |
|---|---|---|
| frames | 1260 | == 1260 |
| identical consecutive frames | **0** | == 0 |
| max frame-to-frame Δluma | 6.48 | < 8 |
| frames Δluma > 8 | 0 | == 0 |
| black-edge frames (slivers) | **0** | == 0 |
| worst scene p10 frame-diff | 0.177 (S6) | > 0.12 |
| jerk p95 | 1.77 | < 2.0 |
| L/R correlation | 0.752 | 0.55–0.80 |
| side/mid | 0.376 | > 0.25 |
| 120–500 Hz, whole file | 54.3 % | < 58 % |
| 4–8 kHz, bed-only windows | 11.7 % | > 10 % |
| 4–8 kHz, voice windows | 10.7 % | > 5 % |
| 20–120 Hz, bed-only windows | 15.3 % | < 48 % |
| decoded peak (after AAC) | **−1.49 dBFS** | ≤ −1.0 |
| integrated loudness | **−11.7 LUFS** | −12.5 … −10.5 |
| short-term minimum | −12.7 LUFS | > −30 (never breathes out) |
| audio − video duration | 0.037 s | ≤ 0.1 |
| longest silence | 0.25 s | < 1.2 |
| VO placement (xcorr vs plan) | +5 ms on all six clips | — |
| caption bottom / headline top (worst frame) | 1495 / 209 | inside 180–1500 |

---

## 6. Ledger — what this build taught (39–45, appended to `MONARCH_SKILL_MOTION_EDIT.md §13`)

39 blend poses, never switch · 40 the rig's `lean` is a body-space (lateral) bend — a forward lean needs yaw ≥ 60 · 41 `tap` is capped at 3.2 kHz; a 4–8 kHz gate needs a dedicated air voice, and a D2 pad root buries it · 42 a clamping limiter is a loudness wall — drive it, then measure the decoded AAC peak (overshoot 0.9–2.1 dB and erratic; one setting hit 0.0 dBFS) · 43 pads are the width: trading them for air raises L/R corr; extrastereo restores it without touching the bed · 44 captions that mirror full sentences overflow a 1080 frame — measure text extents and the camera's worst-case Y at build time · 45 fit the voice by cutting pauses, not by `atempo`.

---

## 7. Rebuild

```bash
pip install numpy pillow scipy imageio-ffmpeg
bash build_power.sh            # 2 render shards → bed → concat → mux → gate (≈ 6 min on 2 cores)
# or step by step
python3 src/power.py 0 630 build/pw0.mp4 & python3 src/power.py 630 1260 build/pw1.mp4 & wait
python3 src/make_asmr_power.py             # never while both shards are live (ledger 36)
printf "file '/home/user/build/pw0.mp4'\nfile '/home/user/build/pw1.mp4'\n" > build/pwlist.txt
$FF -y -f concat -safe 0 -i build/pwlist.txt -c copy build/power_mute.mp4
bash src/mux_power.sh && python3 src/gate_power.py
python3 src/power.py still 7.65            # any frame → build/still_7.65.png
python3 src/sheet_power.py 0.6 7.65 22.7   # contact sheet of chosen times → build/sheet_power.png
```

Files: `SCRIPT_POWER.md` (script + TTS text + copy table) · `src/timeline_power.py` · `src/vo_fit.py` · `src/power.py` · `src/make_asmr_power.py` · `src/mux_power.sh` · `src/gate_power.py` · `src/ameasure.py` (audio-only metrics) · `src/sheet_power.py` · `assets/p1–p6.mp3` (raw TTS) · `assets/p1–p6_fit.wav` (fitted, what the mix uses) · `contact_power_42s.png` · `ASMR_POWER_LEDGER.csv` · `BUILD_MANIFEST_POWER.json`.

## 8. Open items
* Workspace snapshots are capped at ~128 MB; the restored project alone is 130 MB, so the mp4 masters do not survive a turn boundary here — keep them on Drive/catbox (litterbox 72 h copy: https://litter.catbox.moe/wvlqbh.mp4) or rebuild with `build_power.sh` (≈ 6 min).
* The fitted VO has been measured, not auditioned — one listen for the 0.30 s pause cap.
* `vo_fit` is a cut-and-splice; if a word boundary ever sounds clipped, raise the pause cap to 0.36 s and re-time (`timeline_power.py` recomputes everything; the picture follows the voice).
* TTS voice id `voice-00` (Urdu, masculine, entertainment) — recorded here so the clips can be regenerated with the same voice.
