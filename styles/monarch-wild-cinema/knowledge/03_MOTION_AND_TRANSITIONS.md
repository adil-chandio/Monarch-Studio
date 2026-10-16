# 03 · Motion and transitions

## The law that governs every seam

From the editor doctrine, unchanged: **one kind per boundary, never the same
kind twice in a row, every kind matched to a sound cue, and every transition
motivated by the concept.**

A transition is a sentence's punctuation. Six commas in a row is not style.

## The four families

| kind | seconds | cue | motivated by |
|---|---|---|---|
| `hard` | 0.00 | `hard_hit` | a violent beat change; the eye needs no effect |
| `dip` | 0.22 | `impact_soft` | a change of state; through tinted dark, **never** a long black hold |
| `whip` | 0.24 | `doppler_whip` | fast causal hand-off — this caused that |
| `depth` | 0.26 | `riser_short` | conceptual escalation; entering a state |
| `wipe` | 0.24 | `whoosh_edge` | measured spatial hand-off, no white flash |
| `dissolve` | 0.60 | `pad_swell` | time passing. **Use once at most, never between action beats.** |

### The luma ceiling

The stickman ledger's M14 entry measured 49 frames with a luma jump above 8
caused by saturated colour panels sweeping the frame — a strobe, not a
transition. Every kind here is bounded: `transitions.luma_profile()` samples the
blend at 11 points and reports `max_step`, which the gates compare against the
ceiling of 8.

A transition may change the frame a lot. It may not **flash**.

### Freeze-frame blending, and why

The compositor blends a **frozen outgoing frame** into live incoming frames.
Three reasons:

1. It is what a real edit does — the out-point of A is a single frame.
2. It keeps the renderer single-pass and streaming: the renderer holds one
   frame, not two shots' worth.
3. It avoids the failure this doctrine names explicitly: a **long crossfade
   between two moving scenes** reads as an amateur slideshow, because the eye
   tries to track both motions and resolves neither.

## Cut grammar for a long-form episode

| boundary | default |
|---|---|
| chapter turn | `depth` or `hard` — the beat is conceptual |
| cause → effect | `whip`, direction matching the motion |
| scene → data | `wipe` |
| data → scene | `hard` |
| into the paid-off moment | `hard` (the impact carries it) |
| episode close | `dip` into the end card |

**Never**: the same kind at consecutive boundaries; a transition on every
boundary (an effect on every seam is roulette, not direction); a `dissolve`
between two action beats.

## Camera motion inside the shot

Declared per shot in `PLAN.json`:

```json
"cam": { "zoom": [0.030, 0.090], "orbit": 26, "roll": 0.45, "ramp": "linear" }
```

Rules learned here and in WF-05:

- **Monotonic or triangular, never eased at both ends** on a card (ledger #33).
- **The orbit direction follows the subject.** If the animal faces left, the
  camera drifts left; motion that contradicts the subject reads as drift.
- **Modest values.** The honest envelope is `zoom` 0.02–0.105, `orbit` 12–46 px,
  `roll` 0.22–0.60°. Beyond that, plates tear at the frame edge and the camera
  becomes the subject.
- **Always breathing.** `breathe = 1.6 px` guarantees `identical_frames = 0`.

## Speed, and the honest version of it

`films.speed_streaks()` draws directional streaks for a "sprint" beat. It is a
**stylisation**, and it must be used where the narration is already talking
about speed. Streaks on a slow beat is a lie about the content, and the audience
reads it as filler even when they cannot name why.

The same rule governs `flash`, `impact` and `shake`: each one is an *event*
with a cause, timed to the cue, with its own decay curve. Effects that never
decay (`shake` sustained, `flash` held) read as a broken codec, not as energy.
