# 04 · Kinetic type

## Type is a physical object in this style

Not a caption. Not a lower third bolted on. The words are extruded, lit, tilted,
slammed and then **held perfectly still so they can be read.** That sequence —
motion to earn attention, stillness to spend it — is the whole mechanism.

The channel's own audit is the reason this is not negotiable: the video that
died was *AI narration over stills*, and the video that won was *a strong
on-screen idea*. In a footage-free production, the type **is** the footage.

## The eight layer kinds

| kind | function | typical use |
|---|---|---|
| `headline` | the idea, one hot word per line | the thesis of the beat |
| `stat` | the number | 35 MPH, 3 IN 4, 40 METRES |
| `species` | identity → correct response | GRIZZLY / DON'T RUN. DON'T FIGHT. |
| `rule` | a numbered takeaway | the closing three rules |
| `lower` | kicker + subject | episode and chapter titles |
| `chart` / `range` / `gauge` / `source` / `callout` | data and evidence | see chapter 07 |
| `mark` | the persistent brand corner | MONARCH **FILES** · EP 01 |

## The entrance contract

```
entry 0.34 s  ·  settle  ·  hold still  ·  fade out 0.26 s
```

- The entry is a **perspective tilt with extrusion**, or a `pop`, or a `rise`.
  Never a fade-in from nothing (a fade-in says "I am a graphic overlay"; a
  tilt-in says "this object arrived").
- After `entry`, the layer is returned untouched — literally zero transform.
  Endless distortion is the single fastest way to make premium work look cheap.
- The exit fades. Type never hard-cuts off mid-read.

Overshoot is **1.12**, not 1.5. The stickman ledger measured `p95(jerk)` of
3.1–4.1 with a 1.5 overshoot; dropping to 1.12 brought the worst scene to 1.62.

## The safe band

| format | band | reason |
|---|---|---|
| long-form 16:9 | y 60–970 | YouTube's transport bar eats ~100 px at the bottom |
| vertical 9:16 | y 180–1500 | Reels/Shorts UI covers ~320–420 px at the bottom, ~130 px at the top |

The stickman project shipped an entire film with captions **202 px from the
bottom** — every one of them under the phone UI, invisible in the editor and
invisible in the delivery check. This style enforces the band in `gates.py`
(G06) because the eye cannot catch it and the measurement can.

## Legibility is measured

`kinetic.contrast_report()` computes the WCAG contrast ratio of the type layer
against the plate's luma and returns `ok: False` below 4.5:1. The stickman
palette failed this for **every** accent colour (coral 3.40, amber 2.78, gold
2.17, white-on-gold 2.39) — big headline words survived on size alone, small
keywords did not.

In this style the type colour set is already contrast-safe against the graded
plates: `BONE` reads ≈ 12:1 on the `nocturne` floor, `AMBER` ≈ 6:1, `BLOOD` ≈
4.7:1. Anything below 4.5:1 must be enlarged, moved onto a panel, or removed.

## Composition rules

- **One hero, one idea, one hot word per frame.** Two competing text clusters
  is the M1 defect that got a stickman build rejected outright.
- **The hot word is the accent colour** and it is the *only* accent on screen.
- **Type never covers the subject's face or eyes.**
- **Type never sits over a high-detail region.** A headline over foliage is
  unreadable at thumbnail scale even at 12:1 contrast.
- **Words on screen are not the same words in the ear.** If the narration has
  just said it, the frame does not need to print it — that is what makes a
  narrated video feel like a slideshow with subtitles.
- **The persistent mark is one object in one place.** `MONARCH FILES · EP 01`
  appears in the same corner in every episode of the series. Brand recognition
  is a coordinate, not a mood.

## Performance

Type compositing was 82 ms/frame when it round-tripped through PIL at full
frame size. Cropping each layer to its content bounding box, warping only that
crop, and alpha-blending inside its own numpy ROI made it **12.7 ms** — a 6.5×
win — and produces an identical frame. The general principle: **never touch
2 MP to move 200 k px.**

---

## 4.x · Legibility is a scrim plus a measurement (2026-10-16)

Display type over a lit wildlife plate does **not** reach the gate's 4.5:1 on its own. Measured on
delivered frames, ink against the pixels around it, before the scrim existed: headline 1.00–1.61,
stat 2.07, mark 1.21–1.33, gauge 1.17, lower 2.48 — one layer of twelve passed.

- **The scrim is per-layer and sized in the plan** (`scrim: 0.42–0.62`), built by
  `film._add_scrim` in **layer coordinates** (subtracting the on-screen position pushed shot 05's
  panel 620 px above its text). Pad 48 px, feather 34 px — a panel that ends at a hard edge reads
  as a rendering accident.
- **Positions are clamped to the frame** (`film._clamp_pos`): a positioned layer is kept inside
  with a 24 px margin. Full-frame layers keep their `(0,0)` anchor.
- **Text runs are recorded** (`core.RecDraw` → `img.info["text_rects"]`) and gated by **G16**.
  This exists because `draw_tracked` anchors at the LEFT edge and `viz.gauge` passed the card's
  centre: the delivered master said **"BEAR SPRA"**.
- **Contrast is measured on the delivered frame with the glyph core** (alpha > 250) against the
  panel it sits on, or against the surrounding pixels when the layer has no panel. Measuring
  "ink" as every pixel above alpha 40 made a cream-on-black species card score 1.11:1 while its
  glyphs measure 14.85:1.

After the fix, the same twelve layers measure **6.33–15.63:1**, worst 6.33.
