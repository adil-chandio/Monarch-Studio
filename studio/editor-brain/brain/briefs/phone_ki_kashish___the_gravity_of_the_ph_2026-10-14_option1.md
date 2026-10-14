# CONCEPT DNA — option 1 — "Phone ki kashish — the gravity of the phone" · 20 s · 2026-10-14
score 0.92 · dominant moods: tense + dark · fresh slots 8/8 (never used before in any delivered video)

| slot | pick | how it is built on this engine | fresh |
|---|---|---|---|
| Hook archetype | **ECU the eye cannot explain** (`eye_cannot_explain`) | Extreme close-up of an object doing what it cannot (a pupil shaped like a keyhole, ink climbing a glass); the pull-back arrives after the question. | NEW |
| Narrative device | **One law broken** (`one_law_broken`) | NORMAL → CRACK → IMPOSSIBLE (one uncut shot, lands 6–12 s) → CONSEQUENCE → MEANING (≤ 7 words) → LOOP SEAM; one physical law, one metaphor. | NEW |
| Visual world / metaphor | **The room where the phone is a planet** (`phone_planet_room`) | A plain bedroom; every prop has mass and a tether to the phone on the table; the only accent is the phone's glow. | NEW |
| Editing grammar | **Dolly-zoom moments** (`dolly_zoom`) | Background scale breathes against a locked hero at the turn of each chapter. | NEW |
| Camera language | **Handheld micro-shake** (`handheld_micro`) | ±2 px Perlin drift + hit-shake on impacts (measured against jerk). | NEW |
| Sonic identity | **Sub pulse + breath** (`sub_breath`) | A 40 Hz pulse under the hero's heartbeat; breath sounds in the holes (bed_20_120 gate watched). | NEW |
| Typographic twist | **Word slam + hit shake** (`word_slam_shake`) | Hot word drops from above; 2-frame camera hit (jerk-gated). | NEW |
| Ending device | **Freeze on the hot word** (`freeze_hot_word`) | Hard freeze, hot word extrudes, cut to black on the bell. | NEW |
| Signature move (never built before) | **Every prop in the room slides toward the phone as if it were a planet; letting go of the phone drops everything flat (law: gravity).** (`radial_gravity_release`) | one set-piece shot; becomes a new engine capability | NEW |

## Measured targets for the build (carried into the gates)
- chapters: normal → crack → impossible → consequence → meaning → loop
- shots ≥ 5 (something new on screen every ≤ 2.5 (a physical event: light, prop, scale, readout, line — measured as beats) s), transitions = 4, kinds ≥ 3 with ≥ 1 kinds never used before, overlap with the last video ≤ 40 %
- pattern interrupts ≥ 3 (one every ≈6.5 s), 'wtf' set-pieces ≥ 2, re-hooks (open loop / callback) at ≈ [5.0, 10.0, 15.0] s
- hook: word one by 0.6 s, a visual question by 0.8 s, the promise by 3.0 s; frame 1 already in motion
- sound: ≥ 50 % of SFX voices new to the catalogue, one matched cue per transition kind, no noise floor, no repeated cue
- stillness never longer than 0.4 s; identity constants unchanged (palette, type, SHADE rig, grid, safe area, 19 gates)
- format wtf30 (1080x1920 (4:5 safe centre y 285–1635)): loudness -14.0 ± 1.0, TP ≤ −1.0 dBTP, no noise floor; holds: exactly one uncut set-piece ≥ 3 s containing the impossible moment; no other shot > 4 s; callbacks planted and returned ≥ 1; payoff written as 2 quotable lines

## WTF-30 law (MONARCH_WTF30_DOCTRINE.md) — ek qanoon todo, sirf ek; baqi duniya sach rehne do
- **law broken: `gravity` — gravity lies** (things fall up, sideways, or toward the thing that owns him; tends to mean: attachment, addiction, what pulls you) — set by the signature move; the world and the spine follow it
- duration 20–30 s; `law_broken` = exactly one of gravity, scale, time, light, mirror, material, continuity, count, space, causality
- the impossible moment lands between 4.8 s and 8.0 s, in ONE uncut shot ≥ 3.0 s, preceded by a silence hole of 0.3–0.6 s; no text over it; the trick is never explained or repeated
- density = physical events: beats ≥ 14, max gap ≤ 2.5 s; shots ≥ 5 (cuts are few; events are many)
- muted-pass: ≤ 7 on-screen words in total; meaning line ≤ 7 words, one hot word, full stop, between 14.0 s and 18.0 s
- loop seam: last frame rejoins frame 1 (≤ 6/255 mean abs difference or a designed match-cut); CTA: none in picture (caption only)
- consistency law: everything except the one broken law obeys physics — light vs shadow, contact shadows, parallax order, cloth lag, anticipation/settle
- the ten laws: `gravity` gravity lies · `scale` scale lies · `time` time lies · `light` light lies · `mirror` the reflection lies · `material` matter lies · `continuity` space joins impossibly · `count` number lies · `space` geometry lies · `causality` effect before cause

## Story architecture first (reference lessons, brain/references.json)
- Emotional architecture beats transition variety: 2 transition kinds, 1.8 M views. Story devices go first in every brief; transitions are seasoning.
- A hold is allowed when something carries it (a line, a light, a music change). A boring second is a hold with no event — not a hold.
- Give the villain a body (the shadow double) so every chapter is a fight you can draw.
- A counter (DAY n) tells time without a word; the false Day 1 → true Day 1 reset is the plot.
- Colour-code the voices (white truth / red critic); the full stop is the tone.
- Colour is the arc: start monochrome, let the first warm colour be an event, end at first light.
- (references are lessons, never templates: hero, palette, type, grid and gates stay ours)

## Why this combination
Topic themes read as inner, mind. Opening: ecu the eye cannot explain → story device: one law broken, told inside 'The room where the phone is a planet'; dolly-zoom moments with handheld micro-shake keeps the picture changing while the voice flows; the bed is sub pulse + breath, the type does word slam + hit shake, and it closes with freeze on the hot word. Dominant mood tense/dark. Every slot is checked against the registry; nothing here repeats a delivered video inside its window.

## Next steps
1. User picks an option (or asks for a fresh set: `--seed` or `--mood`).  2. Script in that device's chapter template, VO measured first.  3. Build the signature move + ≥3 new transition kinds, luma-trace each.  4. Fill `transitions`, `sfx_voices`, `shots`, `pattern_interrupts`, `wtf_moments`, `rehooks_s` in the DNA json.  5. `concept.py gate <dna>` must PASS before the final mux.  6. After delivery: `concept.py commit <dna> --drive-id … --md5 …`.
