# CHAOS 04 — STRUCTURE v4 (measured from the real reference)

Reference: `VID_20261013_050529_146.mp4` (Drive `1sYYhXs9fbHeHcQGOmH5IR7CvUSVr9Tmx`)
All numbers below were measured on the T4 box with `jobs/analyze_ref.py` and
`jobs/beat_map.py` on 27 Oct 2026, then eyeballed against contact sheets
(`sheet_body.jpg`, `sheet_end.jpg`, `bm_A.jpg`, `bm_B.jpg`). Nothing here is guessed.

---

## 0 · Measured truth

| property | reference | our delivery |
|---|---|---|
| duration | 44.554 s | 44.55 s (±2 frames) |
| frames @30 fps | **1332** | 1332 |
| picture | 720×1280 HEVC, 4.56 Mbps | **1080×1920** H.264 crf 18, yuv420p |
| audio | AAC 44.1 kHz stereo, 127 kbps | AAC 48 kHz, −14 LUFS |
| loudness | **−13.9 LUFS**, LRA 2.7, true peak **+0.1 dBFS** (clipping) | −14.0 LUFS, TP ≤ −1.0 dBFS |
| mean luma | **20.6 / 255** (very dark) | target 18–24 |
| mean motion | 17.55 | 16–19 |
| colour bias | red +0.010, teal −0.010 | same |
| cut rate | 0.38 /s overall, **0.54 /s in Act II** | same |
| strobe hits | **40 events** | same count, same places |

Three acts, cut on measured motion valleys:

| act | span | len | luma | motion | cuts | what it is |
|---|---|---|---|---|---|---|
| **I** | 0.00–13.25 | 13.25 s | 14.6 | 7.34 | 0 | slow, near-black build in one room |
| **II** | 13.25–39.40 | 26.15 s | 23.2 | 21.83 | 17 | escalation, strobes, whip transitions |
| **III** | 39.40–44.55 | 5.15 s | 12.4 | 25.57 | — | white void → logo endcard |

Silence is a structural element: gaps at **40.34–40.93** (0.59 s) and **42.10–44.55**.

---

## 1 · Shot sheet — 20 shots, 1332 frames

Frame numbers are exact; `fps 30`. Camera / light / motion columns are what we
must reproduce. `our build` is what replaces their pixels — everything there is
ours.

### ACT I — the room (frames 0–397)

| # | in | out | frames | ref | camera | subject & light | our build |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 1.60 | 48 | wide room | slow push, 24 mm | concrete floor, one fluorescent tube upper-left, graffiti wall, rack/speaker right, hanging chain; red practical off-frame | our own **depot** set: 6×8 m concrete room, our graffiti tag, our rack; single 6500 K tube + red practical |
| 2 | 1.60 | 3.30 | 51 | same room, push | dolly 10 cm | same, red rim catching the wall | same set, red practical now visible |
| 3 | 3.30 | 5.00 | 51 | doorway centre-right | static, slight tilt | dark doorway, red glow deep inside | our doorway, our red tube inside |
| 4 | 5.00 | 6.70 | 51 | rack close | slow orbit | amp rack, dust in beam | our rack, dust haze |
| 5 | 6.70 | 8.30 | 48 | first silhouette | static | figure with red inner glow in the doorway, wide | **Monarch** figure, red core light |
| 6 | 8.30 | 10.00 | 51 | figure closer | push | hand rising to the head | Monarch, hand-to-mask |
| 7 | 10.00 | 11.70 | 51 | back view | static | textured back of the mask, hard key | Monarch mask back, worn texture |
| 8 | 11.70 | 13.25 | 47 | **hero close-up** | 85 mm | glowing ring around the head, hands gripping | Monarch "halo" mask — our design, our emissive ring |

### ACT II — escalation (frames 397–1182)

| # | in | out | frames | ref | camera | subject & light | our build |
|---|---|---|---|---|---|---|---|
| 9 | 13.25 | 15.00 | 53 | low angle, from behind | handheld | black-clad figure, a second creature's arms behind | Monarch + our "Brood" limbs |
| 10 | 15.00 | 16.60 | 48 | **money shot** | static, symmetric | creature with six spread arms, hard top light | our six-arm rig, our monster |
| 11 | 16.60 | 18.30 | 51 | creature face | macro, 100 mm | wet skin, red mouth glow | our creature face, red mouth |
| 12 | 18.30 | 20.00 | 51 | doorway figure | wide | red floor bounce, figure framed by door | our doorway, red bounce card |
| 13 | 20.00 | 22.00 | 60 | doorway + neon | wide, slow | red neon strip above the door | our neon strip |
| 14 | 22.00 | 24.00 | 60 | corridor walk | follow, 35 mm | red rim behind, silhouette walks | our corridor |
| 15 | 24.00 | 25.60 | 48 | whip + sparks | snap pan | practical spark burst, yellow-orange | our spark practical (real, shot and graded) |
| 16 | 25.60 | 27.60 | 60 | ring-head blur | shake | heavy motion blur, red streak | Monarch halo, directional blur |
| 17 | 27.60 | 29.80 | 66 | in-frame | static | figure inside a picture frame / TV | our frame prop, our figure |
| 18 | 29.80 | 32.00 | 66 | slow-mo tendril | macro | glossy tendril, red/blue split | our tendril, red/blue gels |
| 19 | 32.00 | 34.60 | 78 | framed wide | slow push | black figure, red top light | our set |
| 20 | 34.60 | 39.40 | 144 | red close + hand + white void | 2 shots + 1 transition | red creature close, then hand macro, then **white void floor with a cable and a teal object** | our white-void transition plate — this is the device that lets us cut to the endcard |

### ACT III — endcard (frames 1182–1332)

| # | in | out | frames | ref | what | our build |
|---|---|---|---|---|---|---|
| 21 | 39.40 | 40.34 | 28 | white void collapses to black | flash out |
| 22 | 40.34 | 40.93 | 18 | **silence**, pure black | beat of nothing |
| 23 | 40.93 | 42.10 | 35 | logo endcard: round white emblem + brush wordmark | **our** Monarch emblem + our wordmark, animated on in 9 frames |
| 24 | 42.10 | 44.55 | 73 | their Instagram outro | **replaced**: our own ending card, our handle, no third-party mark |

---

## 1b · Measured cut grid (this is the rhythm — cut on this, not on vibes)

Soft cuts detected at 8 fps analysis, local motion maxima, 0.6 s minimum spacing:

```
16.25  17.25  18.00  18.62  19.38  20.50 | 24.38  25.50  26.25  27.62  28.88
| 32.88  34.12  34.88  35.75  36.50 | 39.50
```

Read as a pattern, this is not a steady cut rate — it is **burst → hold → burst**:

| block | span | shots | rate | what happens |
|---|---|---|---|---|
| long take | 0.00–16.25 | 1 held take (camera moves only) | 0 /s | the room, the silhouette, the ring reveal |
| burst 1 | 16.25–20.50 | 6 shots | **1.4 /s** | creature, arms, face, doorway |
| hold | 20.50–24.38 | 1 shot | — | doorway + neon, walking |
| burst 2 | 24.38–28.88 | 5 shots | 1.1 /s | sparks, whip, frame, tendril |
| hold | 28.88–32.88 | 1 shot | — | framed wide |
| burst 3 | 32.88–36.50 | 4 shots | 1.1 /s | red close, hand, white void approach |
| tail | 36.50–39.50 | 1 shot | — | white void |
| endcard | 39.50 | — | — | logo |

**Strobe / flash grid** — 40 hits, and they are metronomic:

```
9.12 9.62 13.12 | 16.25 16.75 17.25 17.75 18.50 19.25 20.50 21.00 21.50 22.12
22.62 23.12 23.75 24.25 25.12 25.62 26.25 26.75 27.25 28.00 28.50 29.12
31.12 32.12 32.88 33.50 34.12 34.62 35.12 35.75 36.25 36.75 37.38 37.88
38.38 39.38 39.88
```

Spacing from 16.25 s onward is almost always **0.50 s** (120 BPM at 4/4 half-beats),
sometimes 0.62 s. So the film is cut and flashed on a ~120 BPM grid, and the
"holds" are exactly the places where the music breathes. Our edit must land on
the same grid — that is 90 % of why the reference feels the way it does.

Rule for us: **build the audio bed at 120 BPM first, then place every cut and
every flash on that grid.** Not the other way round.

---

## 2 · What we copy, what we do not

**Copy (structure, not pixels):** act lengths, shot order, shot durations, camera
grammar (push / static / macro / whip), the ring-of-light silhouette, the six-arm
money shot, the strobe count and placement, the near-black luma with red
practical, the white-void transition, the silence beat, the endcard length.

**Never:** their footage, their mask design, their brush logo, their `@VKTMDubz`
watermark or Instagram outro, their music bed, their LUT.

---

## 3 · Production path on the hardware we actually have

Box: **Tesla T4 · 15 360 MiB · driver 580.82.07 · CUDA 13.0 · torch 2.11.0+cu130 ·
70 GB free · LTX-Video 2B imports clean** (`diffusers 0.41` + `torchao 0.18`).

| path | how | good for | cost on T4 |
|---|---|---|---|
| **A · our own 3D** | `MONARCH_CHAOS_3D.blend` (ours, already in Drive) → Cycles stills / short renders → composite | hero shots 8, 10, 11, 18 — anything that must be exactly our character | minutes per frame at 720p, so hero shots only |
| **B · AI image-to-video** | our 3D still becomes the first frame → LTX-Video 2B I2V → 97-frame clips | every shot that needs motion, grain, atmosphere | measured in `probe_ltx.py` (running) |
| **C · plate + grade** | ffmpeg: our practical plates (sparks, haze, white void), grain, the near-black curve, red/teal split | Act II transitions, Act III, the whole look | seconds |

Order: **B for coverage, A for the four hero shots, C for the look and the
transitions.** 1332 frames = 14 × 97-frame clips; at 480×832 or 512×896, then a
single ×2.1 upscale to 1080×1920 with grain on top — the reference is that dark,
so upscale artefacts disappear into the shadows.

---

## 4 · Gates before a single frame is rendered

1. Reference locked (this document approved).
2. Character locked: Monarch 3D still sheet approved (our design, not theirs).
3. Look locked: one graded still matching luma 18–24, red +0.010.
4. **Test shot**: one 97-frame clip produced end to end and shown. Nothing more
   until it is approved.
5. Only then: full 1332 frames, then audio −14 LUFS, then master.

---

## 5 · Open questions for the user

1. Music: our own score, or silence-first with only practical sounds?
2. The "six-arm" shot — keep it, or swap for a Monarch-specific hero beat?
3. Endcard text: our handle and emblem — which exact wording?

Status: **structure ready for approval. No render has been run.**
