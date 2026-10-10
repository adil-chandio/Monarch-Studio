# MONARCH SKILL — LONG-FORM 16:9 STICKMAN (ADDITIVE)

**Status:** new sibling skill. Adds to the repo; removes nothing.
Existing skills untouched:
- **Style A — image-compile** (still images → compile → zoom/transitions/captions → export). Unchanged.
- **Style B — frame renderer, vertical** (`src/clean.py`, 1080×1920, 37 s). Unchanged.
- **Style C — frame renderer, landscape** (`src/wide.py`, 1920×1080). *This document.*

---

## 0. READ THIS FIRST: what the reference tutorial actually teaches

Stripped of tool names, the tutorial's method is:

> script → AI voiceover → text-to-image scenes → animate only the first 5–10
> images → drop the rest in as stills → cut to the VO in a timeline → export.

**That is Style A, which this repo already has.** The genuinely new things in it
are three, and none of them are about animation:

| # | Genuinely new | Why it matters |
|---|---|---|
| 1 | **16:9, 8–15 minutes** | A different product from a 37 s short: watch-time and mid-roll ads, not loop rate. |
| 2 | **The niche** (ancient survival / anthropology) | Evergreen, zero face, zero music licensing, high RPM. |
| 3 | **The script architecture** | This is the actual product. See §1. |

The tutorial's weakest link is animating the first 5–10 scenes with an AI video
model: it costs credits per shot and it drifts — the character changes between
scenes. **Style C replaces exactly that part** and nothing else.

### The hybrid that this repo should run

```
0:00 – 0:50   opening hook   ->  Style C   frame renderer, 16:9
                                 deterministic, free, zero character drift,
                                 and retention is decided here
0:50 – 12:00  body           ->  Style A   image-compile (unchanged)
end card                     ->  Style A
```
Retention is won or lost in the first 30 seconds. Spend the deterministic
renderer there and let the cheap pipeline carry the other 11 minutes.

---

## 1. THE 8-BEAT HOOK ARCHITECTURE

Extracted from the reference channel's own two samples (the teeth hook and the
firelight hook). Both are the same machine:

| # | Beat | Rule |
|---|---|---|
| 1 | **DROP-IN** | 2nd person, present tense, ONE sensory verb. No preamble. |
| 2 | **ERA WITHOUT EXPOSITION** | A negation stack ("no mirror, no dentist, no toothbrush") or a scene detail. Never "in ancient times…". |
| 3 | **COUNTERINTUITIVE CLAIM** | "your teeth are about to outlast most people alive today" |
| 4 | **THREAT / STAKES** | One wrong turn and the body fails. Mortality, concretely. |
| 5 | **THE QUESTION** | Literally the video title, spoken. |
| 6 | **EVIDENCE** | place + date + artifact + number. All four. |
| 7 | **BRIDGE TO VIEWER** | "like yours" — collapse 200,000 years into the viewer's own body. |
| 8 | **APHORISM** | Short, symmetrical, quotable. |

### The retention engine is specificity density

> **One hard, verifiable fact every 5–8 seconds.**

Not jokes, not motion. The demo script lands **nine** verifiable specifics in
fifty seconds. If a sentence contains no number, no place and no name, it is
costing you the viewer.

### Accuracy is a survival requirement in this niche

One fabricated number in the comments ends a history channel. Rules:
1. Every claim gets a source recorded before it is written into the script.
2. Where the literature is **contested** (e.g. how central persistence hunting
   was to human evolution), state only the undisputed physiology and attribute
   field observations to the researchers who made them.
3. Never assert a contested evolutionary claim as settled fact.

Worked example with sources: `SCRIPT_HOOK_PERSISTENCE.md`.

---

## 2. THE 16:9 GRID (LOCKED)

```
1920 × 1080, 30 fps
title-safe   x  96 – 1824     y  54 – 1026
chrome       y  64 –  118     progress hairline + chapter tag
headline     y 170 –  300     one line, 80–116 px, 800 weight
stage        y 330 –  824     GY = 824  <- the horizon, held all film
statchip     y 859 –  917     CHIP_Y = 888
caption      y 952            CAP_Y  = 952
```

**Why the lower band is not at the bottom of the frame.** 16:9 has no Shorts
rail, so the instinct is to use the full height. Wrong: YouTube's transport bar
and its gradient occupy roughly the **bottom 100 px** of a 1080-tall player
whenever the viewer moves the mouse. v1 put the caption baseline at y 998 —
82 px of clearance — and the controls sat on it. This is the identical bug
class to the vertical build's y1718 captions sitting under the Reels UI.
Everything below the horizon was lifted 46 px.

### Composition law for landscape

Vertical stacks. **Landscape does not.** The single thing that makes eight
unrelated diagrams feel like one film is **one horizon line held across every
beat**, with the subject on one third and the graphic opposite. Never centre
both.

---

## 3. WHAT HAD TO CHANGE IN THE RIG (and what did not)

Carried over from v9 **unmodified**: the 3D skeleton, `_dirv`, the perspective
projection, depth-sorted two-pass silhouettes, `phys()` follow-through,
sub-pixel `Image.AFFINE` camera, the extruded type system, the ASMR engine
architecture, and the whole forensic QA gate.

Changed, and only in the new sibling file:

### 3.1 Yaw is the whole trick for a run

The v9 walk uses `yaw = 27°`. At 27° a sagittal stride is foreshortened to
almost nothing, and across a wide frame the figure reads as **hopping on the
spot**. Tested 44 / 62 / 78:

- 44° — stride still too short
- **60° — correct.** The stride projects at sin 60 = 0.87 of true length.
- 78° — shoulders collapse, the lead arm crosses the chest

> **Law:** foreshortening is a function of frame aspect. A pose that reads in
> 9:16 does not automatically read in 16:9. Re-tune `yaw` per format.

### 3.2 Hunter palette without touching `toon.py`

`toon()` exposes `shirt`, `pants`, `hair`. It does **not** expose the shoe or
the two shading darks. Those are rebound at import time *inside `wide.py`*:

```python
T.SHOE = (132, 96, 58); T.SOLE = (88, 62, 36)
T.SHIRT_D = (172, 128, 90); T.PANTS_D = (124, 90, 56)
```
`clean.py` never imports `wide.py`, so the vertical build cannot be affected.
A white sneaker in an ancient-survival film is a bigger immersion break than
anything else on screen.

### 3.3 Drawing an animal, not an insect

First attempt: round body, four symmetric splayed legs, horns standing up. It
read as a spider. What actually fixed it:

1. **A long wedge barrel**, deep at the chest, tucked at the flank — not an ellipse.
2. **`s` = withers height**, and the top of the back must land at `gy - s`.
   v1 put the barrel centre at 0.64 s and the animal was dachshund-legged. The
   belly belongs at ~0.66 s, leaving ~0.66 s of leg.
3. **Legs swing fore-aft, never sideways.**
4. **Opposed joints:** the carpus bends backward on the forelimb, the hock
   bends forward on the hind. Same bend direction on all four = insect.
5. **Horns rake back** over the shoulders. Vertical horns = antennae.
6. **Transverse gallop:** fore pair and hind pair in antiphase, plus a
   suspension lift. This is also the point being made on screen — that
   whole-body gait is what pins the animal's breathing to its stride.

---

## 4. AUDIO: THE TWO FAILURES WORTH MEMORISING

### 4.1 A widener multiplying zero is zero

The bed was built with the drone panned to `0.0`. The drone carries most of the
bed's energy, so the side channel was **identically zero** — and `side × 3.10`
of nothing is still nothing. Measured **L/R correlation 0.9817**: a mono file
with a stereo processing chain bolted to it.

> **Law:** width is created at the **source**, not at the bus. Generate the
> drone as a true stereo pair — independent detuning and independent random
> phases per channel — then the widener has something to work on.

After the fix: bed correlation 0.236, final mix **0.677** (target 0.55–0.80).

### 4.2 Budget the spectrum before you budget the loudness

v1 measurement: **34 % of all energy below 120 Hz, 74 % below 500 Hz, and
7.9 % in the 4–8 kHz presence band.** A low drone + sub cues on every
transition + a 104 Hz drum is three bass instruments stacked. It does not sound
cinematic, it sounds like a rumble.

Fixes, in order of effect: lift the drone an octave (fundamental becomes the
2nd partial), halve every `sub()` cue gain and raise their pitch, filter the
drum body `62–6200 Hz` with more skin and less boom, nearly double the shaker
(it is the only thing in 4–8 kHz), and a −0.58 low-shelf below 155 Hz on the bus.

### 4.3 AAC overshoots the limiter

Pre-encode peak **−1.52 dBFS** → decoded AAC peak **+0.85 dBFS**. A 2.4 dB
overshoot. The limiter protects the PCM, not the codec.

> **Law:** set `alimiter` ≈ **−4 dBFS** (`limit=0.63:level=disabled`) and let
> the codec overshoot into the headroom. Always re-measure the peak *after*
> decoding the delivered file, never before encoding it.

### 4.4 `apad` with no bound will swap the machine to death

`loudnorm` + `alimiter` latency makes the output ~0.37 s short. The reflex fix,
a bare `apad`, pads **infinitely**; with `-t` on the output ffmpeg still
buffered until the box hit load average 10 and `kswapd` took over. Use
`apad=whole_dur=53.4,atrim=0:53.0,asetpts=N/SR/TB`.

---

## 5. TIMING: THE RE-FIT LAW, INVERTED

The vertical build had a frozen 37.00 s target, so the **voice** was re-fitted
per scene with `atempo`.

Long-form has no duration target. So invert it: **measure the VO, then cut the
picture to the voice.** No `atempo` anywhere — the narration is never
time-stretched, which is the single biggest giveaway of an AI-assembled video.

```
measured  w1 6.11  w2 5.30  w3 5.46  w4 4.83  w5 11.86  w6 14.92
scene     0.000  6.900  13.000  19.200  24.700  31.000  37.300  45.400   end 53.000
vo at     0.350  7.250  13.350  19.550  25.050                37.750
```
Two of the six VO lines deliberately span **two** visual beats (w5 over S5+S6,
w6 over S7+S8). Cutting the picture mid-sentence is good: the viewer gets a new
image before the current thought has landed, which is the cheapest retention
trick there is.

Leave 0.3–0.5 s of air after each line. Do not trim the natural pauses out of
the VO — in this format they read as thought, not as dead space.

---

## 6. MISTAKE LEDGER — NEW ENTRIES (24–31)

Continues the 23-entry ledger in `MONARCH_SKILL_MOTION_EDIT.md`.

| # | Mistake | Fix |
|---|---|---|
| 24 | Reused the vertical `yaw` for a landscape run; the figure hopped on the spot | Re-tune yaw per aspect; 60° for a profile run |
| 25 | Drew an animal as an ellipse with four symmetric legs | Wedge barrel, fore-aft swing, opposed joints, raked horns |
| 26 | Defined `s` as withers height, then placed the barrel at 0.64 s | Top of the back lands at `gy - s`; belly at 0.66 s |
| 27 | Assumed 16:9 has no platform chrome | YouTube's transport bar eats the bottom ~100 px |
| 28 | Widened a bus whose side channel was identically zero | Build the drone as a true stereo pair at the source |
| 29 | Stacked drone + subs + low drum, then wondered why it rumbled | Budget the spectrum by band before mixing |
| 30 | Trusted the pre-encode peak | AAC overshoots ~2.4 dB; limit to −4 dBFS, re-measure after decode |
| 31 | Bare `apad` to fix a short tail | `apad=whole_dur=…,atrim=…` — unbounded pad thrashes the box |

---

## 7. REBUILD

```bash
pip install imageio-ffmpeg
mkdir -p build
printf "file '/home/user/build/wc0.mp4'\nfile '/home/user/build/wc1.mp4'\n" > build/wclist.txt

python3 src/wide.py   0  795 build/wc0.mp4     # ~5 min   } run both,
python3 src/wide.py 795 1590 build/wc1.mp4     # ~5 min   } one per core
python3 src/wide_audio.py                      # ~2 min -> build/wide_bed.wav

FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
$FF -y -f concat -safe 0 -i build/wclist.txt -c copy build/wide_mute.mp4
# then the mux in VIDEO_WIDE_NOTES.md §Mux
```

`build/` is **not** snapshot-persisted — recreate it and `wclist.txt` before
launching shards or the concat fails with "No such file or directory".

---

## 8. SCALING TO A FULL 8–15 MINUTE EPISODE

1. Write the full script first, beats 1–8 for the hook, then chaptered body.
2. Measure every VO line. Build the scene table from the measurements.
3. Hook (0:00–0:50) → Style C. Body → Style A stills with the existing
   zoom/transition/caption compile.
4. Hold **one** horizon line and **one** chapter-tag chrome across both
   pipelines so the seam is invisible.
5. Keep one accent per chapter, all ≥ 4.5:1 against the paper.
6. Run the forensic gate on the final file, not on the shards.

### Pass/fail gate (copy this)

| metric | target |
|---|---|
| identical frames | 0 |
| max abs ΔLuma between frames | < 8 |
| per-scene p10 frame-diff | > 0.12 |
| jerk p95 | < 2.0 |
| every accent vs paper | ≥ 4.5:1 |
| caption clearance from frame bottom | > 100 px |
| L/R correlation | 0.55 – 0.80 |
| side/mid | > 0.25 |
| energy 120–500 Hz | < 58 % |
| energy 4–8 kHz | > 10 % |
| decoded peak | ≤ −1.0 dBFS |
| audio duration vs video | within 0.1 s |

---

## 9. WHAT THE FULL 4:23 EPISODE ADDED (ledger 32–38)

Built `stickman_wide_episode_full.mp4` — 34 scenes, 5 acts, 263.5 s, 7905 frames,
from the same engine. Seven things were learned that the 53 s hook could not teach.

**32 — A zoom that dips below 1.0 puts black slivers in your master.**
`Image.transform(AFFINE)` fills anything outside the source with black. An
alternating push/pull camera that pulled back to z = 0.988 did exactly that on
**1852 of 7905 frames (23 %)** and no duration, luma or audio test caught it.
Enforce a zoom floor (`Z0 = 1.032`) and assert, over *every* frame, that the
sampled rectangle stays inside the source:

```python
iz = 1 / z
x0 = (W - W*iz)*.5 + px;  x1 = x0 + W*iz
assert x0 >= 0 and x1 <= W and y0 >= 0 and y1 <= H
```

**33 — Eased camera moves fail the motion test by design.**
`e_io()` ramps velocity to zero at both ends of a scene. On an action shot nobody
notices; on a typographic card nothing else is moving, so the frame reads as
frozen. Use a linear-dominant ramp (`.15*e_io(u) + .85*u`) and a **triangle-wave**
pan, never a sine — a triangle has constant speed and no zero-velocity apex.

**34 — The camera can only move what has gradient.**
Measured: at 1920×1080 flat vector art, 1 px/frame of pan buys only ~0.7 of
mean |Δluma| at a 320×180 probe. Dust motes and breathing buy ~0.01 — nothing.
If a card is near-blank, no amount of ambient animation will save it; the fix is
to put the content on screen sooner. S25 held an empty card for 0.5 s after the
cut and was the single scene that failed; pulling its first reveal from 0.50 s to
0.10 s fixed it outright.

**35 — A whole-file spectral target grades the wrong thing once voice dominates.**
Narration covers **93.5 %** of this episode. The hook's "4–8 kHz > 10 % of total
energy" rule therefore measures the narrator's sibilance, and the only way to
pass it is to EQ harshness into the voice. Split the measurement with a VO mask
built from the clip offsets and durations:

| window | metric | target |
|---|---|---|
| VO-absent (bed alone) | 4–8 kHz | > 10 % |
| VO-present | 4–8 kHz | > 5 % |
| VO-absent | 20–120 Hz | < 48 % |
| whole file | 120–500 Hz | < 58 % |

Delivered: 16.5 % / 6.8 % / 41.8 % / 54.7 %. Brightening the *bed* by +5 dB in
4–8 kHz moved the whole-file number by 0.1 points — proof the whole-file number
was never measuring the bed.

**36 — Never run the audio build while both render shards are live.**
2 cores, ~2 GB. The bed allocates ~500 MB; it was OOM-killed mid-run, the exit
code was swallowed by a pipe into `tail`, and the mux silently picked up the
**stale** bed from the previous run. Check the output file's mtime, not just the
log tail.

**37 — A filter output label can be consumed exactly once.**
`[VO]` feeding both the sidechain and the final `amix` makes ffmpeg re-interpret
the second one as a *file* stream specifier: `Stream specifier 'VO' matches no
streams`. Split it: `...amix=...,asplit=2[VOa][VOb]`.

**38 — Python scoping bites inside a long `main()`.**
`BUF += SFX` makes `BUF` local for the entire function, so the module-level
buffer is unreachable: `UnboundLocalError`. Declare `global BUF, SFX`. And
`del X if X is not None else None` is a **SyntaxError**, not a no-op.

### Episode-scale contract that worked

* 5 acts, named, with an act bar as the only persistent chrome.
* **Captions in the hook only.** In the body the typography *is* the script, so
  nothing is ever said and shown as the same sentence.
* One accent per act, 4.69–9.17:1 against paper.
* Act 4 is the counter-argument, and the music drops to near-silence for it.
* One hard, checkable fact every 5–8 s, with the source named on screen.
* Audio cues are walked out of the live scene table, so they cannot drift.
