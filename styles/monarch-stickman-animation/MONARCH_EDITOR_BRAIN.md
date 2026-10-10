# MONARCH EDITOR BRAIN — the pro editor's mindset, as a system
**v1 · 2026-10-09 · turn 12 · companion of `MONARCH_SKILL_MOTION_EDIT.md` (how to build) — this file is how to THINK before building**

> **Law (Roman Urdu):** *Identity wahi, video kabhi wahi nahi.* Har video mein pehchaan same (SHADE hero, paper/ink, extruded type, measured gates) — lekin hook, kahani ka dhancha, metaphor ki duniya, cut ki grammar, camera, sound, type ka twist aur ending — **har baar naya, registry se check kiya hua, gate se paas kiya hua.** Novelty is a gate, not a vibe.

Tools: `brain/library.py` (idea libraries) · `brain/registry.json` (memory of what every delivered video used) · `brain/concept.py` (`status` · `propose` · `gate` · `cadence` · `commit` · `export`). Gate #20 = freshness. Identity constants never change (project body §4).

---

## 0. The one-page ritual (every video, in this order, no step skipped)

| # | step | output | measured by |
|---|---|---|---|
| 1 | **Brief** — topic, length, audience state (scrolling, tired, skeptical), the one feeling the viewer must leave with | 3 lines in the script file | — |
| 2 | **Memory check** — `concept.py status` | what is blocked (used recently) and what is fresh | registry windows (§3) |
| 3 | **Concept DNA** — `concept.py propose --topic … --dur …` → 3 options → user picks one | `brain/briefs/*.md` + `brain/dna/*.json` | score = coherence + novelty + mood + theme fit |
| 4 | **Script to the device** — write in the chapter template of the chosen narrative device; VO recorded and **measured first**; the picture is cut to the voice | `SCRIPT_<name>.md`, `assets/*_fit.wav`, `timeline_<name>.py` | voice share ≥ 85 %, chapter breath 0.55–0.70 s |
| 5 | **Hook engineering** (§4) — frame 1 in motion, visual question ≤ 0.8 s, word one ≤ 0.6 s, contrast spike 1.0–1.5 s, promise ≤ 3 s | the first 90 frames storyboarded shot by shot | luma trace + the hook checklist |
| 6 | **Retention architecture** (§5) — micro / meso / macro cadence planned on paper before any render; re-hooks at 25/50/75 % | shot list with event column | `concept.py cadence` |
| 7 | **Signature move + ≥ 3 new transition kinds** — built and luma-traced as windows before the shard render | new `tr_*` / set-piece code, probe PNGs | `max_dluma < 8`, `trans_jerk_max < 8` per window |
| 8 | **Sound design** (§8) — one matched cue per transition kind, ≥ 50 % new voices, no floor, no repeated cue, one deliberate silence | `make_asmr_<name>.py`, ledger CSV | bed-only passages measured before the mux |
| 9 | **Three-pass review** (§10) — muted pass, audio-only pass, 2× pass; the boring-second hunt | notes in `VIDEO_<name>_NOTES.md` | every second has a reason |
| 10 | **Gates** — the 19 measured gates + **gate #20 freshness** (`concept.py gate <dna>`) | gate table in the notes | 20/20 or it does not ship |
| 11 | **Deliver + remember** — Drive (md5), `concept.py commit`, ledger entry, notes, Notion, Linear | registry grows by one | — |
| 12 | **Post-mortem** (3 questions, §12) → one new library item or one new rule | ledger + library | — |

---

## 1. How a pro editor thinks (the twelve habits this system enforces)

1. **Edit for the thumb, not the eye.** The viewer decides in ≈ 1.3 s. Frame 1 is never a title card, never still, never neutral.
2. **Every cut is a promise kept or a question asked.** No neutral cuts. If a cut does neither, it is removed (premium = subtraction).
3. **Contrast is the engine; sameness is the leak.** Attention responds to *change* — size, luma, direction, speed, colour, sound, silence. Plan the change schedule (§5) instead of hoping for it.
4. **Pace is information rate, not cut rate.** "Something new every 2–3 s" means a new *idea on screen*, not merely a new frame.
5. **Motivate everything.** The camera moves because the hero moved or looked; the transition kind comes from the metaphor (the seam wipes, the plate shatters); the SFX comes from the object.
6. **One hero, one idea, one hot word per frame.** Density is the enemy of premium.
7. **Earn the big moment.** One set-piece per chapter; the rest is restraint, so the set-piece lands.
8. **The sound tells the eye where to look.** Visual onset and cue within ± 1 frame; a transition without a cue is a flaw; a cue without a visual is noise.
9. **The script is the edit.** Measure the voice first; cut to it; never pad the voice to fit a length.
10. **Setup → payoff.** Whatever the hook shows comes back changed at the end (the room turns, the counter completes, the ring closes).
11. **Never trust the eye; measure.** Every rule above has a number (§11) and a gate.
12. **Same identity, never the same video.** The brand is the constant; the story, the device, the world, the move — new every time, and the registry proves it.

---

## 2. Concept DNA — the eight slots + one signature move

Identity constants (never vary): 1080×1920 @ 30 fps · paper/ink palette + ACC hot words · Montserrat extruded headline with one hot word · SHADE on the 3-D rig, hybrid charcoal/paper look · chrome grid, safe area y 180–1500 · ASMR bed sidechained under a centred VO, no noise floor · the 19 measured gates.

Variables (chosen per video from `brain/library.py`, checked against `brain/registry.json`):

| slot | library size | what it decides |
|---|---|---|
| **Hook archetype** | 20 | the first 3 s — the question/contradiction/sting that stops the thumb |
| **Narrative device** | 16 | the chapter architecture (list, mini-story, trial, ladder, two doors, loop replay…) with a duration range |
| **Visual world / metaphor system** | 30 | the one world all props live in (chessboard, mirror hall, corridor of doors, river and dam…) — never reused |
| **Editing grammar** | 14 | how shots join (voice-led inserts, match-cut chain, jump-cut staccato, the oner, loop reprise…) |
| **Camera language** | 10 | how the lens behaves (push/parallax, orbit, crane, top-down, dutch, rack focus, POV…) |
| **Sonic identity** | 12 | the bed's instrument family (strings tension, glass mallet, sub + breath, piano + room, clock motif…) |
| **Typographic twist** | 14 | the one type behaviour of this video (typewriter + ink, text as object, light reveal, live counter…) |
| **Ending device** | 10 | how it closes (callback to frame 1, question returned, counter completes, silent word…) |
| **Signature move** | 24 ideas | ONE set-piece shot that has never been built — it becomes a new engine capability every video |

Also varied and gated: the **transition set** (15 built kinds + 24 families to build; ≥ 3 new kinds per video, overlap with the previous video ≤ 40 %) and the **SFX palette** (≥ 50 % voices new to the catalogue). Also planned: **pattern interrupts** (16 devices) at one per ≈ 6.5 s.

---

## 3. Anti-repetition laws (what "never the same video" means in numbers)

| item | rule | window |
|---|---|---|
| hook archetype | not used in the last **3** delivered videos | 3 |
| narrative device | not used in the last **3** | 3 |
| visual world | **never** reused (unless the user orders a series in the same world) | ∞ |
| signature move | **never** rebuilt | ∞ |
| editing grammar · camera · sonic · type twist · ending | not used in the last **2** | 2 |
| transition kinds | ≥ 8 kinds (≥ 40 s video), overlap with the previous video ≤ **40 %**, ≥ **3 kinds never used before** | 1 / ∞ |
| SFX voices | ≥ **50 %** of voices new to the whole catalogue; no cue repeated inside the video | ∞ |
| cadence | shots ≥ duration/2.4; pattern interrupts ≥ duration/6.5; set-pieces ≥ max(2, duration/30); re-hooks at 25/50/75 % | per video |
| hook text | never the same opening sentence pattern twice in a row | 1 |

`concept.py gate` checks all of these from the DNA json; `commit` refuses a failing DNA. The windows are deliberately asymmetric: a *world* defines a video, so it is burned after one use; a camera language is a tool, so it only rests for two videos.

---

## 4. Hook engineering — the first 90 frames

| time | law | engine |
|---|---|---|
| 0.00 s | frame 1 is already in motion (a fall, a turn, a light arriving); never a static title | wedge drop / rig pose blend already mid-ease at t = 0 |
| ≤ 0.6 s | voice word one | `LEAD[0] ≤ 0.60` in the timeline |
| ≤ 0.8 s | a *visual* question — something the eye cannot explain yet | an incomplete object, a wrong number, a crowd not looking |
| 1.0–1.5 s | the contrast spike: one change of scale, luma or direction | insert cut or seam move (luma step < 8) |
| ≤ 3.0 s | the promise stated by voice and shown by picture; the hot word lands | headline 300–520 band |
| 3–6 s | the open loop that pays at the end (the room, the ring, the counter) | logged in the DNA as `rehooks_s[0]` setup |

Hook archetype menu and recipes: `brain/library.py:HOOK_ARCHETYPES` (20). A hook is rejected if it could be the hook of a different topic — it must contain the topic's own noun.

---

## 5. Retention architecture — three cadences + re-hooks

- **Micro (2–3 s):** a new *idea* on screen — insert, prop, number, gesture, light change. Measured by `concept.py cadence` (longest shot ≤ 4 s, no two consecutive shots > 3 s).
- **Meso (≈ 6.5 s):** a *pattern interrupt* — a change of kind, not of content: scale jump 4×, direction flip, 1-frame tint flash, silence hole, ECU, slow-mo ramp, look at the lens, a prop breaks (16 devices in the library). Logged per video; gate counts them.
- **Macro (12–20 s):** a *chapter turn* with a set-piece: the signature move, a 3-D transition of the big family, a numeral card. One per chapter, never two in a row.
- **Re-hooks at 25 / 50 / 75 %:** an open loop in the voice ("lekin asli baat…"), a callback to the hook image, or a reversal. Logged as `rehooks_s`.
- **The boring-second hunt:** for every second, one phrase that answers "why would they keep watching?". A second without an answer is cut or given an event.

---

## 6. Visual grammar

- **One idea per shot**; the hot word is the idea's name.
- **Contrast ladder:** stillness → motion, small → huge, dark → paper, slow → snap, silence → hit. Use one rung per cut; never the same rung twice in a row.
- **Depth staging:** three planes (foreground prop, hero, world) — parallax on pushes; inserts are separate shots, never a scaled scene layer (clips the chrome).
- **Light as story:** rays, flares, the seam, lit windows — light arrives when the lesson arrives; the dark advances when the villain speaks.
- **Metaphor discipline:** one world per video; every prop belongs to it; a prop from another world is a flaw.
- **The "wtf" budget:** 2–3 set-pieces per minute, each one measured against the gates; more than that and nothing is special.
- **Subtraction pass:** the last pass before the gate removes 10 % of elements; if nothing can go, the design was already clean.

---

## 7. Motion design (rig + cinematic layer)

- **Easing families:** quintic `e_q` for anything that must not jerk (transitions, camera), `e_back` overshoot for props arriving, spring for badges; no linear motion anywhere.
- **Anticipation → action → settle** on every hero gesture (pose blend 0.5–0.7 s; a 2-frame anticipation before hits).
- **Overlap and follow-through:** cloth/hood lags the body by 2–3 frames; ghost trails on fast walks.
- **Arcs:** hands and camera travel on arcs; straight-line moves read as mechanical.
- **Nothing perfectly still:** every static element drifts (two slow periods, ± a few px) — the gates `p10 > .12` and `identical 0` enforce it.
- **The camera is a character:** it moves for a reason (hero looks, prop arrives, chapter turns), one motive per shot, measured so `jerk_p95 < 2` on shot frames.
- **Transitions end on the beat** (the entrance lands, it does not cut); first/last frame equal pure A/B; soft edges ≥ 100 px over figure-dense shots; one kind per boundary, never the same kind twice in a row, cue matched.

---

## 8. Sound design

- **Voice first:** centred, de-essed, LIM .71, XS 1.7; the bed ducks under it (sidechain) and never breathes out between sentences.
- **Bed = cues, not floor:** no room/hiss layer, no fixed grid; the 4–8 kHz air comes from the cues that sit exactly in the voice holes.
- **One matched cue per transition kind**, read from the same `PLAN` list the picture uses.
- **Sonic identity per video** (12 families); the payoff instrument changes per chapter; the end bell is the only recurring signature.
- **Silence is a weapon:** one deliberate hole (0.4–0.9 s, gate `silence < 1.2 s`) before the biggest word.
- **No repeat:** no cue twice; ≥ 50 % of voices new to the catalogue; every voice logged in the ledger CSV with its time, so the gate can count it.

---

## 9. Type and colour

- Constant: Montserrat extruded, one hot word per headline, paper on dark 12.6:1, hot words ≥ 4.5:1 (measured), every CAPS line ≤ 936 px.
- Variable: **one** typographic twist per video (14 in the library) — never two twists in one video.
- Colour: the ACC accent is assigned per chapter; the assignment order must differ from the previous video; accents tint, never flood.

---

## 10. The three-pass review (before the gates)

| pass | how | what it catches |
|---|---|---|
| **Muted** | watch with no sound | is the story clear from picture alone? is every hot word readable? where does the eye not know where to look? |
| **Audio only** | listen with the screen off | does the voice flow? does every cue have a reason? any repeated sound? any hole > 1.2 s? |
| **2× speed** | watch at double speed | rhythm flaws pop: sections with the same shape, transitions of the same family too close, a chapter with no set-piece |

Then the **boring-second hunt** (§5) and the **subtraction pass** (§6). Notes go in `VIDEO_<name>_NOTES.md` before the gate run.

---

## 11. Gate #20 — freshness (added to the 19 measured gates)

Input: `brain/dna/<slug>.json` (slots + signature from `propose`; `transitions`, `sfx_voices`, `shots`, `pattern_interrupts`, `wtf_moments`, `rehooks_s`, `hook_text` filled from the real build). Checks (18 rows): eight slot windows, signature uniqueness, transition kinds ≥ min, overlap ≤ 0.40, new kinds ≥ 3, new SFX share ≥ 0.50, shots / interrupts / set-pieces ≥ targets, re-hooks ≥ 3, hook text logged. PASS = all rows. `commit` refuses a FAIL. The 19 engine gates stay exactly as in IZZAT v2 (`gate_respect2.py`).

---

## 12. Memory and post-mortem

- **Registry** (`brain/registry.json`): newest last; six delivered videos recorded (money v9, episode/hook, POWER v1, SHADE v2, IZZAT v1, IZZAT v2) with slots, signature, transition kinds, SFX voices, hook text, Drive id.
- **Commit ritual:** after the Drive md5 check → `concept.py commit <dna> --drive-id … --md5 …` → ledger entry in `MONARCH_SKILL_MOTION_EDIT.md` → notes → Notion Doc 08/11 → Linear.
- **Post-mortem, three questions:** (1) which second would a stranger scroll on, and why? (2) which rule did the measurements prove wrong? (3) what did we build that the library did not have? — each answer becomes one new library item or one new ledger rule. The library grows faster than it is consumed; that is the point.
- **Where it lives:** workspace `brain/` + this file · Drive (SHADE folder) · Notion Doc 11 · Linear MON-53. Resume key "best video reel editing" → project body §0 → this ritual before any new video.

---

## 13. Library index (v1)
hooks 20 · devices 16 · worlds 30 · grammars 14 · cameras 10 · sonic 12 · type twists 14 · endings 10 · signature moves 24 · pattern interrupts 16 · transition kinds 15 built + 24 to build · SFX voices 21 used + 30 fresh. Any item can be added by the user in one line; the registry decides what is blocked, never taste alone.


## 14. Reference lessons (added turn 13 — Day One Films · DISCIPLINE, 1.8 M views in 12 days)

Full study: `REFERENCE_STUDY_DAYONE_DISCIPLINE.md` · data: `brain/references.json` · tool: `brain/study.py`.
Measured: 158 s, 44 shots, **2 transition kinds** (13 dips-to-black + hard cuts, 3 white flashes), median shot 1.3 s but
13 shots over 5 s, 58 % still frames, luma 18/255, 8 spoken lines, ≈ 22 on-screen lines, −16.6 LUFS, 94 BPM, 53 % of the
energy under 120 Hz, ending at −30 dB RMS.

What it corrects in this doctrine:
1. **Story architecture first.** The brief now opens with the story devices (counter spine, antagonist with a body, callback
   ladder, quotable payoff) and treats transitions as seasoning. Gate #20 keeps the novelty rules; it no longer *drives* the concept.
2. **A hold with an event is not a boring second.** In `--format film` a 7–14 s hold is legal when a line, a light or a music
   change carries it; bursts (beat-locked montage, 0.3 s impact cuts) sit between the holds. In `--format short` the 2–3 s rule stays.
3. **Two formats.** `short` = the vertical v9 identity (default). `film` = 16:9, 120–300 s, text narration allowed (voice kept
   for a leitmotif), loudness −16.5 ± 1, quiet ending, ≥ 3 callbacks, 2 quotable payoff lines, no CTA.
4. **Colour as arc, voices as colour.** White = truth, red = critic, full stop on every line; the first warm colour is an event.
5. **Give the villain a body.** The habit becomes a figure the hero can fight on screen (our hero already has a Shadow — SHADE v2).
6. **Never copy the surface.** Their bean character, flat 2-D, near-black default and lines stay theirs. Our hero, hybrid look,
   extruded type, grid and 19 + 1 gates stay ours. Lessons, not templates.

Ritual change: `python3 brain/concept.py propose --topic … --dur … --format short|film` — the brief prints the reference principles
under "Story architecture first". New reference studies: `python3 brain/study.py <mp4> --name <slug> --out <dir>` → add an entry
to `brain/references.json` with principles and a do-not-copy list.
