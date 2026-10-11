# CONCEPT DNA — option 3 — "TUMHARI RESERVED SEAT — 20 minutes a day, 90 days, 30-hour gap" · 78 s · 2026-10-10
score 0.805 · dominant moods: epic + tense · fresh slots 8/8 (never used before in any delivered video)

| slot | pick | how it is built on this engine | fresh |
|---|---|---|---|
| Hook archetype | **Mirror accusation** (`mirror_accusation`) | The hero turns to the lens: 'tum bhi yahi karte ho' — eyes ignite, the rest of the frame dims. | NEW |
| Narrative device | **The ladder / levels** (`ladder`) | Level 1…5 stacked in depth; the camera climbs; each level is a harder rule. | NEW |
| Visual world / metaphor | **The gauge** (`pressure_gauge`) | A big needle meter (anger, stress, trust); the needle is a character. | NEW |
| Editing grammar | **Beat-locked counter montage** (`beat_locked_montage`) | Every cut exactly on beat 1 of a bar; the HUD counter jumps with the cut; same framing, different day. | NEW |
| Camera language | **Low-angle hero** (`low_angle`) | Camera at the floor, the hero towering; for turns and payoffs. | NEW |
| Sonic identity | **Sub pulse + breath** (`sub_breath`) | A 40 Hz pulse under the hero's heartbeat; breath sounds in the holes (bed_20_120 gate watched). | NEW |
| Typographic twist | **Text in depth** (`depth_layers`) | Three parallax layers of type; the hero walks between them. | NEW |
| Ending device | **Hero walks into the light** (`walk_into_light`) | The wedge opens fully; the hero exits frame right into paper. | NEW |
| Signature move (never built before) | **The hero sprints up the last steps and punches through the giant shadow; the frame goes to white and the red letters of its last word shatter.** (`punch_through_shadow`) | one set-piece shot; becomes a new engine capability | NEW |

## Measured targets for the build (carried into the gates)
- chapters: level1 → level2 → level3 → level4 → level5 → cta
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
Topic themes read as inner, mind. Opening: mirror accusation → story device: the ladder / levels, told inside 'The gauge'; beat-locked counter montage with low-angle hero keeps the picture changing while the voice flows; the bed is sub pulse + breath, the type does text in depth, and it closes with hero walks into the light. Dominant mood epic/tense. Every slot is checked against the registry; nothing here repeats a delivered video inside its window.

## Next steps
1. User picks an option (or asks for a fresh set: `--seed` or `--mood`).  2. Script in that device's chapter template, VO measured first.  3. Build the signature move + ≥3 new transition kinds, luma-trace each.  4. Fill `transitions`, `sfx_voices`, `shots`, `pattern_interrupts`, `wtf_moments`, `rehooks_s` in the DNA json.  5. `concept.py gate <dna>` must PASS before the final mux.  6. After delivery: `concept.py commit <dna> --drive-id … --md5 …`.
