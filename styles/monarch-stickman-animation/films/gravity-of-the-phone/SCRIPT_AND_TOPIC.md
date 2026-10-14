# THE GRAVITY OF THE PHONE — idea, script, shot list

## Why this idea (chosen from slate v1, doctrine §13)

- The phone is the one object every viewer has within arm's reach while watching — the WTF happens to *their* object.
- One law (gravity), one room, one hero, one light source: the brain can verify the impossibility in a single uncut shot, so it cannot dismiss it as an edit trick.
- The metaphor needs no words: the phone pulls everything in; flip it face-down and the room stands up again. The meaning line only names what the eye already understood.
- Brain card: `eye_cannot_explain · one_law_broken · phone_planet_room · dolly_zoom · handheld_micro · sub_breath · word_slam_shake · freeze_hot_word`, signature `radial_gravity_release` (score 0.92, freshness 28/28).

## The script (what the viewer sees, second by second)

**0.00** A desk. A phone face-down, buzzing. A pencil beside it starts rolling — toward the phone, *uphill* along the desk's tilt. (First sound at 0.000 s; frame 1 already moving; no title.)
**1.45** The phone flips itself face-up. Amber floods the desk.
**2.00** Cut (1-frame amber tint flash). The room. Monarch walks in reading a book. The wall clock's pendulum leans toward the desk. A page corner lifts on its own. He stops.
**3.80** ECU. His eyes go wide.
**4.60** Cut to the room — and hold. **4.90** Everything goes silent for 0.4 s, then a ring expands from the phone: the field is on.
**5.00–5.60** Pages fly. His book is torn out of his hands. He lunges and grabs the door frame. The clock rips off the wall (ding 1).
**6.40–8.80** Books, plant, chair slide toward the desk. Monarch rises to horizontal — a human flag off the lintel (ding 2, ding 3). Sub drone, heartbeat.
**9.00 / 9.42** His hands slip. Twice.
**9.80** He looks at the lens.
**11.00** He lets go. **11.42** He lands on the desk. **11.58** Slaps the phone face-down. **12.00** The glow dies. Second silence hole.
**12.30** Everything drops flat — books, plant, clock, chair — one thud.
**13.00** He stands up on the desk and looks at the fallen room.
**14.60** Push-in. **15.40** *Phone ulta.* **16.66** *Zindagi seedhi.* **17.15** the word **seedhi.** turns amber and pops (VO lands on it; 2-frame hit).
**18.20** The desk again. **19.30** The buzz returns. **20.00 → 0.00** loop.

VO (Urdu, `voice-00`): «فون الٹا۔ زندگی سیدھی۔» — *Phone ulta. Zindagi seedhi.* — 4 words, full stop at 86 % of the runtime.

## Shot list

| # | In | Out | Len | Kind | Camera |
| --- | --- | --- | --- | --- | --- |
| S1 | 0.00 | 2.00 | 2.0 | desk, phone, pencil | static + micro-drift |
| S2 | 2.00 | 3.80 | 1.8 | room, hero enters | handheld micro |
| S3 | 3.80 | 4.60 | 0.8 | ECU eyes | insert cutaway |
| S4 | 4.60 | 14.60 | 10.0 | **the impossible moment, uncut** | dolly-zoom on onset, then settle |
| S5 | 14.60 | 18.20 | 3.6 | hero on desk + meaning line | push-in, 2-frame hit on hot word |
| S6 | 18.20 | 20.00 | 1.8 | desk at τ = t − 20 | loop seam match |

Transitions: tint_flash_cut, insert_cutaway, push_in_cut, phone_match_cut, loop_seam_match (5 kinds, 4 new to the registry).

## Physics notes (`src/scene.py`)

- Field: radial acceleration toward the phone centre, ramped in over 4.90 → 5.60 s and switched off at 12.30 s; floor grid is warped by the same field for the eye.
- Props carry mass, friction and a start delay so the room empties in a readable order (pages → book → clock → floor books → plant → chair).
- Hero: planted walk → lunge → lintel grab → pendulum flag whose angle follows the field strength, with two slip events (hands move, angle drops, recovers) → release → desk landing (feet anchored left of the phone so the reach is honest for the rig) → squat → stand.
- Everything is a pure function of time, so halves render in parallel and any frame can be re-rendered alone.

## Sound design (`src/audio.py`)

- One cue per physical event (150 cues, 78 voices): phone buzz, pencil roll, phone flip, glow swell, pendulum creak, page lift, book slap, desk slam, clock dings, sliding wood/pot/metal, hand grabs and slips, cloth flutter, sub drone, heartbeat, glass note, power-down, drop thud, footsteps, word slams, VO.
- Two silences: 4.50 → 4.88 s before the field onset; 12.15 → 12.28 s before the drop.
- Master: linear gain to −14 LUFS + numpy look-ahead true-peak limiter at −1.3 dBTP ceiling (measured −14.2 / −1.1 after AAC), LRA 7.4 preserved.
