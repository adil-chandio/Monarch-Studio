# CONCEPT DNA — option 1 — "TUMHARI RESERVED SEAT — 20 minutes a day, 90 days, 30-hour gap" · 78 s · 2026-10-10
score 0.891 · dominant moods: dark + epic · fresh slots 8/8 (never used before in any delivered video)

| slot | pick | how it is built on this engine | fresh |
|---|---|---|---|
| Hook archetype | **Confession** (`confession`) | 'Main paanch saal yeh galat karta raha' — hero sits, light from one side, caption in lower case. | NEW |
| Narrative device | **The autopsy** (`autopsy`) | What went wrong, cause by cause, on a blueprint of the failed day. | NEW |
| Visual world / metaphor | **The iceberg** (`iceberg`) | Visible 10 % (results) vs underwater 90 % (work); the camera dives. | NEW |
| Editing grammar | **Split-screen comparisons** (`split_screen`) | Two states side by side on the seam; the seam is the divider. | NEW |
| Camera language | **Orbit around the hero** (`orbit`) | The rig turns 90–180° while the set parallaxes; one per chapter at most. | NEW |
| Sonic identity | **Sub-drone build at 94 BPM, quiet ending** (`sub_drone_94`) | 53 % of the energy under 120 Hz, no air above 8 kHz, pulse 94 BPM, −16.6 LUFS integrated; the loudest minute is the grind, the last 13 s fall to −30 dB RMS. | NEW |
| Typographic twist | **Text revealed by light** (`light_reveal`) | The ray layer sweeps and the headline appears only where lit. | NEW |
| Ending device | **The mirror turn** (`mirror_turn`) | The hero's reflection turns to the camera first. | NEW |
| Signature move (never built before) | **A crowd of silhouettes morphs into a wall of text.** (`crowd_to_text`) | one set-piece shot; becomes a new engine capability | NEW |

## Measured targets for the build (carried into the gates)
- chapters: body → cause1 → cause2 → cause3 → fix → cta
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
Topic themes read as inner, mind. Opening: confession → story device: the autopsy, told inside 'The iceberg'; split-screen comparisons with orbit around the hero keeps the picture changing while the voice flows; the bed is sub-drone build at 94 bpm, quiet ending, the type does text revealed by light, and it closes with the mirror turn. Dominant mood dark/epic. Every slot is checked against the registry; nothing here repeats a delivered video inside its window.

## Next steps
1. User picks an option (or asks for a fresh set: `--seed` or `--mood`).  2. Script in that device's chapter template, VO measured first.  3. Build the signature move + ≥3 new transition kinds, luma-trace each.  4. Fill `transitions`, `sfx_voices`, `shots`, `pattern_interrupts`, `wtf_moments`, `rehooks_s` in the DNA json.  5. `concept.py gate <dna>` must PASS before the final mux.  6. After delivery: `concept.py commit <dna> --drive-id … --md5 …`.
