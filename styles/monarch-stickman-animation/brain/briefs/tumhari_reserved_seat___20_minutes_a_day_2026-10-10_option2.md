# CONCEPT DNA — option 2 — "TUMHARI RESERVED SEAT — 20 minutes a day, 90 days, 30-hour gap" · 78 s · 2026-10-10
score 0.84 · dominant moods: calm + epic · fresh slots 8/8 (never used before in any delivered video)

| slot | pick | how it is built on this engine | fresh |
|---|---|---|---|
| Hook archetype | **Number shock** (`number_shock`) | One giant extruded numeral turns in the dark (90 %, 3650, 0); the hero is small beside it. | NEW |
| Narrative device | **Callback ladder** (`callback_ladder`) | Three or four motifs planted early (alarm, mirror, room, villain) each return once, changed; the ending is the first scene replayed with the change. | NEW |
| Visual world / metaphor | **The desert and the well** (`desert_well`) | Heat haze, one well; the crowd digs everywhere, the hero digs deep in one spot. | NEW |
| Editing grammar | **Dolly-zoom moments** (`dolly_zoom`) | Background scale breathes against a locked hero at the turn of each chapter. | NEW |
| Camera language | **Handheld micro-shake** (`handheld_micro`) | ±2 px Perlin drift + hit-shake on impacts (measured against jerk). | NEW |
| Sonic identity | **ASMR paper / pencil foley** (`paper_foley`) | Every prop appearance has a paper sound; the bed is almost only foley. | NEW |
| Typographic twist | **Tracking-out whisper** (`tracking_whisper`) | Letter spacing expands as the voice drops; for confessions. | NEW |
| Ending device | **Question returned to the viewer** (`question_back`) | The hero asks the lens; hold 1.0 s; card. | NEW |
| Signature move (never built before) | **People become chess pieces mid-walk.** (`chess_people`) | one set-piece shot; becomes a new engine capability | NEW |

## Measured targets for the build (carried into the gates)
- chapters: plant1 → plant2 → plant3 → turn → return1 → return2 → return3 → end
- shots ≥ 32 (something new on screen every 2–3 s), transitions = 31, kinds ≥ 8 with ≥ 3 kinds never used before, overlap with the last video ≤ 40 %
- pattern interrupts ≥ 12 (one every ≈6.5 s), 'wtf' set-pieces ≥ 3, re-hooks (open loop / callback) at ≈ [19.5, 39.0, 58.5] s
- hook: word one by 0.6 s, a visual question by 0.8 s, the promise by 3.0 s; frame 1 already in motion
- sound: ≥ 50 % of SFX voices new to the catalogue, one matched cue per transition kind, no noise floor, no repeated cue
- stillness never longer than 0.4 s; identity constants unchanged (palette, type, SHADE rig, grid, safe area, 19 gates)
- format short (1080x1920): loudness -11.6 ± 0.9 (gate −12.5..−10.5); holds: none > 4 s; callbacks planted and returned ≥ 1; payoff written as 2 quotable lines

## Story architecture first (reference lessons, brain/references.json)
- Emotional architecture beats transition variety: 2 transition kinds, 1.8 M views. Story devices go first in every brief; transitions are seasoning.
- A hold is allowed when something carries it (a line, a light, a music change). A boring second is a hold with no event — not a hold.
- Give the villain a body (the shadow double) so every chapter is a fight you can draw.
- A counter (DAY n) tells time without a word; the false Day 1 → true Day 1 reset is the plot.
- Colour-code the voices (white truth / red critic); the full stop is the tone.
- Colour is the arc: start monochrome, let the first warm colour be an event, end at first light.
- (references are lessons, never templates: hero, palette, type, grid and gates stay ours)

## Why this combination
Topic themes read as inner, mind. Opening: number shock → story device: callback ladder, told inside 'The desert and the well'; dolly-zoom moments with handheld micro-shake keeps the picture changing while the voice flows; the bed is asmr paper / pencil foley, the type does tracking-out whisper, and it closes with question returned to the viewer. Dominant mood calm/epic. Every slot is checked against the registry; nothing here repeats a delivered video inside its window.

## Next steps
1. User picks an option (or asks for a fresh set: `--seed` or `--mood`).  2. Script in that device's chapter template, VO measured first.  3. Build the signature move + ≥3 new transition kinds, luma-trace each.  4. Fill `transitions`, `sfx_voices`, `shots`, `pattern_interrupts`, `wtf_moments`, `rehooks_s` in the DNA json.  5. `concept.py gate <dna>` must PASS before the final mux.  6. After delivery: `concept.py commit <dna> --drive-id … --md5 …`.
