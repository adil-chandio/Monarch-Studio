# 01 · Look and grade

## One look per episode

The grade is a **series identity**, not a per-shot decision. Four looks exist;
an episode picks one and stays inside it. The look is declared once in
`PLAN.json` (`"look": "nocturne"`) and may only be overridden at a deliberate
beat — the alarm spike, or the archive segment.

| look | when | character |
|---|---|---|
| `nocturne` | night, forest, danger, the flagship tone | deep teal shadows, warm bone highlights, vignette 0.52 |
| `first_light` | conservation, family, hopeful resolution | lifted blacks, softer vignette, more bloom |
| `archive` | evidence, data, a cited segment | flat, truthful, desaturated, heavier grain |
| `alarm` | the threat or mortality beat | crushed blacks, hard contrast, cold-warm split |

Switching look inside an episode is an **edit decision**, the same class of
choice as a transition. It must be motivated the way a cut is motivated.

## The pipeline order is fixed and load-bearing

```
TONE LUT -> FADE -> SPLIT-TONE -> SATURATION -> BLOOM -> VIGNETTE -> GRAIN
```

The order matters:

1. **Tone first.** A filmic shoulder (`_hable` curve, 55 % strength by default)
   compresses the highlights before anything else touches them. Correcting a
   clipped highlight after split-toning is no longer possible.
2. **Split-tone second.** Shadows and highlights get different hue vectors.
   `nocturne` pushes shadows toward blue-teal and highlights toward amber —
   the two-tone separation is what makes a frame read "cinematic" instead of
   "colour corrected".
3. **Saturation after tone.** Desaturating before the curve would remove
   colour the curve is about to redistribute.
4. **Bloom, vignette, grain last.** They are lens and stock properties. Putting
   them before the tone curve would tone the flare, which is wrong.

## Why the scene is graded BEFORE the type

Type is a **designed object**, not a photograph. If it passed through the grade
it would inherit the vignette (edges darker than the centre — the exact
opposite of what legibility needs), the grain (which softens thin strokes) and
the saturation change (which shifts the accent hue away from the brand amber).
Type is composited after the grade, so it arrives on screen at its designed
contrast ratio. This is measured, not assumed: `kinetic.contrast_report()`
returns the type-vs-background ratio for every headline.

## The performance story (measured, not guessed)

The first implementation of this grade ran at **1.10 s/frame**. Every stage was
measured and every slow one was rewritten against an OpenCV SIMD path:

| stage | naive | optimised | method |
|---|---|---|---|
| saturation | 278 ms | 20 ms | Rec.601 luma blend via `cvtColor` + `addWeighted` |
| vignette | 73 ms | 15 ms | cached mask, `cv2.multiply(..., scale=1/255)` |
| bloom | 91 ms | 22 ms | 1/8-scale glow, additive `addWeighted` |
| grain | 23 ms | 23 ms | already a cached tile, moving crop |
| split-tone | 69 ms | 34 ms | quarter-scale luma mask, expanded |
| **total grade** | **~520 ms** | **~172 ms** | |

The lesson generalises: **a float32 numpy pass over 2 MP is ~40 ms.** Three of
them per stage and you have lost a second per frame. Any time a stage can be
expressed as a cached mask plus an OpenCV primitive, it must be.

## What the grade must never do

- **Clip.** `tone_lut` carries a `ceiling=0.985` so nothing lands at 255 before
  the encoder. `grade.measure()` reports `clipped_hi_pct` and
  `crushed_lo_pct`; the gates read them.
- **Flood.** Accents tint the frame; they never fill it. The M14 entry in the
  stickman ledger measured 49 frames with an >8 luma jump from saturated
  colour panels sweeping the frame. That is a defect class, not a style.
- **Tone the type.** See above.
- **Be different per shot without a reason.** Sameness is the leak the editor
  doctrine warns about, but so is noise: a grade that changes every four
  seconds has no identity left to recognise.
