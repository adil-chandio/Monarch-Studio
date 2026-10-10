# CONCEPT DNA — option 1 — "comparison — stop watching other people's windows" · 170 s · 2026-10-09
score 0.85 · dominant moods: dark + tense · fresh slots 8/8 (never used before in any delivered video)

| slot | pick | how it is built on this engine | fresh |
|---|---|---|---|
| Hook archetype | **Mirror accusation** (`mirror_accusation`) | The hero turns to the lens: 'tum bhi yahi karte ho' — eyes ignite, the rest of the frame dims. | NEW |
| Narrative device | **Callback ladder** (`callback_ladder`) | Three or four motifs planted early (alarm, mirror, room, villain) each return once, changed; the ending is the first scene replayed with the change. | NEW |
| Visual world / metaphor | **The calendar of X** (`calendar_of_x`) | A wall calendar fills with red X marks as the counter climbs; the one cutaway that proves time. | NEW |
| Editing grammar | **Freeze-frame annotations** (`freeze_annotate`) | Hard freeze, dimension lines + labels draw on, then release with a whip. | NEW |
| Camera language | **Dutch tilt tension** (`dutch_tilt`) | 4–7° roll that levels at the fix; roll measured in the luma trace. | NEW |
| Sonic identity | **Clock-tick motif** (`clock_motif`) | Tick as the only rhythmic element; it stops at the turn (silence as a weapon). | NEW |
| Typographic twist | **Text on the seam** (`text_on_seam`) | Half paper, half charcoal letters split by the hybrid diagonal. | NEW |
| Ending device | **The villain left small in the room** (`villain_left_small`) | The ending replays the first room at dawn; the hero walks out of frame; the Shadow stays, small, beside the clock. | NEW |
| Signature move (never built before) | **Chapters as dominoes knocked over by the hero's finger.** (`domino_chapters`) | one set-piece shot; becomes a new engine capability | NEW |

## Measured targets for the build (carried into the gates)
- chapters: plant1 → plant2 → plant3 → turn → return1 → return2 → return3 → end
- shots ≥ 47 (something new on screen every 3–6 (a hold must carry a line, a light or a music change) s), transitions = 46, kinds ≥ 4 with ≥ 3 kinds never used before, overlap with the last video ≤ 40 %
- pattern interrupts ≥ 14 (one every ≈6.5 s), 'wtf' set-pieces ≥ 3, re-hooks (open loop / callback) at ≈ [42.5, 85.0, 127.5] s
- hook: word one by 0.6 s, a visual question by 0.8 s, the promise by 3.0 s; frame 1 already in motion
- sound: ≥ 50 % of SFX voices new to the catalogue, one matched cue per transition kind, no noise floor, no repeated cue
- stillness never longer than 1.5 s; identity constants unchanged (palette, type, SHADE rig, grid, safe area, 19 gates)
- format film (1920x1080): loudness -16.5 ± 1.0, LRA ≈ 4.5, last 10 s ≤ −26 dB RMS; holds: 7–14 s allowed when carried; bursts on the beat between them; callbacks planted and returned ≥ 3; payoff written as 2 quotable lines

## Story architecture first (reference lessons, brain/references.json)
- Emotional architecture beats transition variety: 2 transition kinds, 1.8 M views. Story devices go first in every brief; transitions are seasoning.
- A hold is allowed when something carries it (a line, a light, a music change). A boring second is a hold with no event — not a hold.
- Give the villain a body (the shadow double) so every chapter is a fight you can draw.
- A counter (DAY n) tells time without a word; the false Day 1 → true Day 1 reset is the plot.
- Colour-code the voices (white truth / red critic); the full stop is the tone.
- Colour is the arc: start monochrome, let the first warm colour be an event, end at first light.
- (references are lessons, never templates: hero, palette, type, grid and gates stay ours)

## Why this combination
Topic themes read as social. Opening: mirror accusation → story device: callback ladder, told inside 'The calendar of X'; freeze-frame annotations with dutch tilt tension keeps the picture changing while the voice flows; the bed is clock-tick motif, the type does text on the seam, and it closes with the villain left small in the room. Dominant mood dark/tense. Every slot is checked against the registry; nothing here repeats a delivered video inside its window.

## Next steps
1. User picks an option (or asks for a fresh set: `--seed` or `--mood`).  2. Script in that device's chapter template, VO measured first.  3. Build the signature move + ≥3 new transition kinds, luma-trace each.  4. Fill `transitions`, `sfx_voices`, `shots`, `pattern_interrupts`, `wtf_moments`, `rehooks_s` in the DNA json.  5. `concept.py gate <dna>` must PASS before the final mux.  6. After delivery: `concept.py commit <dna> --drive-id … --md5 …`.
