# CONCEPT DNA — option 3 — "comparison — stop watching other people's windows" · 170 s · 2026-10-09
score 0.78 · dominant moods: calm + dark · fresh slots 8/8 (never used before in any delivered video)

| slot | pick | how it is built on this engine | fresh |
|---|---|---|---|
| Hook archetype | **The question returned** (`question_returned`) | 'Tumse aakhri baar kab kisi ne izzat se baat ki?' — the hero waits one breath for the answer. | NEW |
| Narrative device | **Silent film + text narration** (`silent_film_text`) | No continuous VO: ≈ 20 on-screen lines in two colours carry the script; the voice is kept for one leitmotif line that returns changed; music and SFX do the rest. | NEW |
| Visual world / metaphor | **Anvil and hammer** (`anvil`) | Each rule is a strike; sparks are the particle layer; the blade is the result. | NEW |
| Editing grammar | **Split-screen comparisons** (`split_screen`) | Two states side by side on the seam; the seam is the divider. | NEW |
| Camera language | **Crane / boom reveal** (`crane_reveal`) | Vertical reveal: from the floor to the hero's eyes, or over a crowd. | NEW |
| Sonic identity | **ASMR paper / pencil foley** (`paper_foley`) | Every prop appearance has a paper sound; the bed is almost only foley. | NEW |
| Typographic twist | **The full stop** (`full_stop_voice`) | Every on-screen line and every thumbnail word ends with a period: calm, final, no exclamation marks. | NEW |
| Ending device | **Callback to frame 1, changed** (`callback_frame1`) | The opening shot returns with one difference (the room turns). | NEW |
| Signature move (never built before) | **The hybrid seam rotates 90° in one shot and the scene re-gravitates.** (`seam_rotates`) | one set-piece shot; becomes a new engine capability | NEW |

## Measured targets for the build (carried into the gates)
- chapters: open → problem → bottom → turn → grind → fight → payoff → title
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
Topic themes read as social. Opening: the question returned → story device: silent film + text narration, told inside 'Anvil and hammer'; split-screen comparisons with crane / boom reveal keeps the picture changing while the voice flows; the bed is asmr paper / pencil foley, the type does the full stop, and it closes with callback to frame 1, changed. Dominant mood calm/dark. Every slot is checked against the registry; nothing here repeats a delivered video inside its window.

## Next steps
1. User picks an option (or asks for a fresh set: `--seed` or `--mood`).  2. Script in that device's chapter template, VO measured first.  3. Build the signature move + ≥3 new transition kinds, luma-trace each.  4. Fill `transitions`, `sfx_voices`, `shots`, `pattern_interrupts`, `wtf_moments`, `rehooks_s` in the DNA json.  5. `concept.py gate <dna>` must PASS before the final mux.  6. After delivery: `concept.py commit <dna> --drive-id … --md5 …`.
