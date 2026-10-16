# 09 · FAILURE REGISTER

Every defect found while building `monarch-wild-cinema`, with its cause, its
fix and its proof. The engine's value is in these rows: a style that has never
recorded a failure is a style that has never been measured.

Continues the ledger of `monarch-stickman-animation` (M1–M38). Entries here are
`T` (tabahi) numbered.

---

## T01 · The parallax ran backwards

- **Symptom:** the environment drifted while the animal stood still. Nothing
  errored; the motion looked *plausible*, which is exactly why this is first.
- **Cause:** the depth field's primary saliency term was darkness,
  `1 - luminance`. The channel's grade **lights the subject and drops the
  environment**, so darkness marked the background as near and the subject as
  far. The parallax was inverted on brand.
- **Fix:** focus energy is now the primary term (`0.62*focus + 0.24*tone +
  0.14*sat`), where focus is a box-filtered Laplacian. Tone deviation replaces
  raw darkness with a **symmetric** term, so the prior is no longer keyed to
  which side of the plate carries the light.
- **Proof:** `depth.depth_preview(stage)` renders the field as a TURBO heat
  image. Subject now reads near (red), environment far (cyan).
- **Law:** *derive a depth prior from the style's own design, never from a
  generic photographic assumption. And render the depth map — the inversion is
  invisible in the motion and obvious in the heat image.*

## T02 · Indexing a (256,3) LUT with a (H,W,3) image

- **Symptom:** `cv2.error: (-215:Assertion failed) m->dims <= 2`.
- **Cause:** `lut = np.repeat(tone[:,None], 3, axis=1)` builds a (256,3) table.
  NumPy advanced-indexing a (H,W,3) array **into** it broadcasts to
  `(H,W,3,3)` — a 4-D result that the next `cv2.resize` rejects.
- **Fix:** the tone curve is a **1-D** (256,) table; `lut[img]` then returns
  `(H,W,3)` and maps all three channels through the same curve.
- **Law:** *the shape a fancy-index produces is `index_shape + item_shape`.*

## T03 · Grain tile smaller than the frame

- **Symptom:** `operands could not be broadcast together with shapes
  (1080,1920,3) (1043,1859,1)` — the crop had run off the tile by exactly the
  animated offset.
- **Fix:** the tile is generated oversized (`H + H/2`, `W + W/2`) so a moving
  crop can never leave it.
- **Note:** the moving crop is deliberate. A static grain tile reads as a dirty
  lens; an offset crop per frame reads as film.

## T04 · A negative base with a fractional exponent

- **Symptom:** `TypeError: '>' not supported between instances of 'complex'
  and 'float'` inside the impact decay.
- **Cause:** `(1 - t/0.13) ** 2.4` — once `t > 0.13` the base is negative and
  Python promotes to complex. It worked for the first four frames and exploded
  on the fifth.
- **Fix:** guard the base first: `max(0.0, 1 - t/0.13) ** 2.4`.
- **Law:** *every envelope expression needs its base clamped, not just its
  result.*

## T05 · The grade cost 1.10 s per frame

- **Measured:** parallax 98 · tone 16 · **split-tone 69** · **saturation 278**
  · bloom 91 · vignette 73 · grain 23 · rays 109 · haze 62 · motes 44 ·
  streaks 47 · impact 125 · type 83.
- **Cause:** every stage was written as clear float32 numpy over 2 MP, and
  numpy allocates the whole intermediate at each step. **A float32 pass over
  2 MP is ~40 ms**; the grade alone was doing thirteen of them.
- **Fix:** rewrite each stage as a cached mask plus an OpenCV SIMD primitive:

  | stage | before | after | method |
  |---|---|---|---|
  | saturation | 278 | 20 | `cvtColor(RGB2GRAY)` + `addWeighted` |
  | vignette | 73 | 15 | cached uint8 mask + `cv2.multiply(scale=1/255)` |
  | bloom | 91 | 22 | 1/8-scale glow + additive `addWeighted` |
  | rays | 109 | 38 | field built at ¼ res, blurred small, upscaled |
  | impact | 125 | 13 | bounded ROI instead of the whole frame |
  | haze | 62 | 34 | `cv2.multiply` blend instead of a float mix |
  | type | 83 | 13 | cropped layers + numpy ROI compositing |

- **Proof:** total ≈ **0.40 s/frame** (3.4× faster), i.e. ~12 min per finished
  minute on 2 cores.
- **Law:** *profile before optimising, and then never touch 2 MP to move 200 k.*

## T06 · The encoder starved the renderer

- **Symptom:** ~1.6 s/frame during the first real render, while the same
  pipeline benched at 0.45 s/frame standalone.
- **Cause:** `top` showed ffmpeg at **133 % CPU** running `libx264 -preset
  medium` on 1080p, on a 2-core box. Python was left ~0.6 of a core.
- **Fix:** the picture master is an **intermediate** — encoded
  near-lossless and cheap (`ultrafast`, CRF 12) — and the delivery master is
  encoded for real exactly once at mux time with the requested preset and CRF.
- **Proof:** render rate returned to ~0.45 s/frame.
- **Law:** *on a small box, never run a quality encode while rendering. Encode
  once, at the end, on purpose.*

## T07 · `clamp()` was not array-aware

- **Symptom:** `ValueError: The truth value of an array with more than one
  element is ambiguous` from `max(lo, min(hi, x))` inside `smooth()`.
- **Cause:** the depth field is an array and the easing helpers are scalar.
- **Fix:** `clamp` branches on `isinstance(x, np.ndarray)` and uses
  `np.clip`. Every easing function then works on both.
- **Law:** *a helper on the hot path of an image pipeline is called with arrays
  more often than with floats.*

## T08 · `Montserrat.getname()` reports "Thin" at weight 900

- **Symptom:** the type system *looked* like it was silently falling back to
  the variable font's default thin instance.
- **Cause:** the variable font's `name` table reports the default instance,
  not the currently-set variation.
- **Fix:** measure, do not ask the name. Ink coverage of the same string:
  wght 100 → **4.86**, wght 500 → **21.41**, wght 900 → **42.91**. The
  variation axes are working; only the label lies.
- **Law:** *the name table reports the file, the pixels report the instance.*

## T09 · A stray non-Latin character in a comment

- **Symptom:** a docstring read `# px of 永不-still micro drift`, introduced by
  a moment of inattention.
- **Fix:** corrected to `never-still`; a grep for non-ASCII now runs over `src/`
  before a checkpoint.
- **Law:** *a repository that a human reads later must read like one.*

## T10 · The first proof render produced a file that could not be checked

- **Symptom:** `--limit-shots 2 --no-audio` finished and printed a size, with
  no measurement of what was inside.
- **Cause:** the quick path returned before the verify/mix steps.
- **Fix:** `BUILD.json` is written on every path, and `gates.py` runs against
  any master including a two-shot proof.
- **Law:** *an output without a measurement is a preview, not a delivery.*

---

## T11 · The god rays blew the frame to white

- **Symptom:** shot 01 of the first finished render was a white screen crossed by seven grey
  bands; the bear was gone.
- **Cause:** `god_rays` added `ray × (colour × strength × 60)` — a **2800×→ tint** multiplied by
  the ray field. At the plan's 0.20 strength the additive term was ~30× full scale.
- **Fix:** the ray field is peak-normalised, so `strength` reads directly as "peak brightness
  added, as a fraction of full scale". Measured back on a mid-grey frame: `god_rays(0.20)` now
  adds mean Δ 2.3, max Δ 38.
- **Law:** an additive effect's strength parameter must be expressed in the units of the thing it
  adds to, and its ceiling must be **measured on a frame**, not reasoned about.

## T12 · The flash was a strobe

- **Symptom:** no visible defect per frame; the wall clock said the picture flickered.
- **Cause:** `flash` applied its full alpha instantly. At the default 0.34 that is a **55-level
  frame-mean lift in one frame**; the engine's own gate allows 8.
- **Fix:** a 0.13 s rise (and the plan's flash capped at 0.10). Measured: peak lift 6.8 levels,
  max per-frame jump **2.7** — the hit still lands, nothing blinks. `impact` got a 2-frame attack
  for the same reason.

## T13 · The caption clipped itself: "BEAR SPRA"

- **Symptom:** the delivered master's shot 06 showed a gauge card reading **BEAR SPRA**.
- **Cause:** `draw_tracked` anchors text at its **left** edge; `viz.gauge` passed the card's
  **centre** (`size / 2`) as that edge, so half the label was drawn past the card and sliced by
  its own canvas. No exception, no plan error, every numeric check passed.
- **Fix:** the label is fitted to the card and centred; `core.RecDraw` now records where every
  text run lands and **gate G16** fails the build when a run leaves its canvas. A first rule
  based on the alpha bounding box was rejected — card panels are drawn edge-to-edge on purpose,
  so it flagged every card. The check is a builder contract, not a heuristic.
- **Law:** a text run that outgrows its container is undetectable by any pixel statistic of the
  finished frame. Record the layout at build time, and look at a frame from the finished file.

## T14 · A citation string rendered as 38 one-character rows

- **Symptom:** G06 reported `06:source@y900-2435` — a panel 2435 px tall, running off the frame.
- **Cause:** the plan passed a citation as a **string** where `source_stamp` expected a **list**, so
  `len(cites)` was the character count.
- **Fix:** a string counts as one citation, capped at two rows. Panel height 74 + 38·n.

## T15 · A scrim that landed 620 px above its own text

- **Symptom:** shot 05's species card measured 1.11–1.88:1 with a scrim that was demonstrably
  being drawn.
- **Cause:** `_add_scrim` subtracted the layer's on-screen position from the panel coordinates —
  correct for a full-frame canvas, wrong for a card layer, which is positioned *after* it is
  built.
- **Fix:** the panel is built in layer coordinates. Shot 05 measures **14.85:1**.
- **Law:** a function that operates on a layer must state which coordinate space it lives in, in
  the docstring, on the first line.

## T16 · ffmpeg's limiter is not a linked limiter

- **Symptom:** a mix balanced to L/R correlation **+0.580** arrived at the master at **+0.320**,
  then at **+0.055** once `alimiter` was added.
- **Cause:** both `alimiter` and `loudnorm`'s limiter derive gain reduction **per channel**. A
  stereo cue whose two channels differ in peak gets compressed by different amounts per side,
  which rewrites the inter-channel relationship. And because the correlation sum is
  **gain-weighted**, even a *linked* limiter moves it — it re-weights toward the quiet, more
  coherent parts of the mix.
- **Fix:** no ffmpeg loudness stage on the bus. Gain → linked limiter → **balancer last** → common
  gain trim, all in numpy, solved against measurements (`score.solve_mix`).
- **Law:** the balancer is the last stereo operation, and any stage that changes level after it
  must be a **common** gain.

## T17 · A clipping master that measured as a success

- **Symptom:** the mix solved to **−16.06 LUFS** — on target — while the 16-bit master clipped
  (write peak 1.000, true peak **+1.70 dBTP**).
- **Cause:** a peak limiter with a fixed ceiling cannot raise the loudness of a wide-crest mix; it
  lowers it. The solver kept adding gain, the 16-bit write clipped, and the *clipping* produced
  the loudness being chased. The score's crest was **24.5 dB** where −16 LUFS with a −1 dBFS
  ceiling allows ≈ 14.2 dB.
- **Fix:** treat crest factor as a **content** problem — cue gains 0.7, `soft_clip(1.8)`, and a
  sustained mid pad at 440 Hz because the score's 2–4 kHz band held 2.4 % of its energy. Crest
  24.5 → **13.2 dB**; the master now has no clipped samples and TP −5.3 dBTP.
- **Law:** never let a 16-bit write be the element that decides loudness. Solve on float, and
  assert the ceiling before writing.

## T18 · Gate G04 was measuring the edit, not the strobe

- **Symptom:** G04 reported 77.27 on a film whose in-shot frames are steady (mean dLuma 0.5–2.8).
- **Cause:** the target ran over **every** frame pair, so a hard cut read as a strobe.
- **Fix:** G04 applies inside shots (0.35 s windows after each cut excluded) and the cut moved to
  **G15**, the BT.1702 flash threshold — stricter for the frames around a cut than the old rule.
  Revisions are recorded in `data/gates.json` with their evidence.
- **Law:** when a gate and the artefact disagree, first ask whether the gate is measuring the
  right thing; then either fix the art or **re-scope the gate with recorded evidence**. Never
  delete a gate because the render failed it.

---

## T19 · The vertical cut had no type at all

- **Symptom:** the first 9:16 master was a real, well-graded 1080×1920 render — of a landscape
  composition, with no words in it.
- **Cause:** every type builder reads `core.W` / `core.H` at call time and the canvas was fixed at
  1920×1080, so the vertical renderer simply skipped the type pass. `vertical_path` cropped the
  camera and the grade and left the reason to watch behind.
- **Fix:** `core.canvas(W, H)` (a context manager that repoints `W`, `H`, `PORTRAIT` and `SAFE`) plus
  `film.render_vertical`, which re-runs the type pass inside the portrait frame. A shot may carry
  `vertical_type` to compose the Short differently from the long-form cut.

## T20 · Portrait type sat under the platform's buttons

- **Symptom:** the first vertical render *with* type put the headline at **y 1459–1692** of 1920 and
  the species card reached **x 1204** of 1080.
- **Cause:** two things. (a) `"lower"` was hard-coded as `H - 300 - size`, which in a 1920-tall frame
  is inside the action bar; the safe band is **y 420–1620** in a Short. (b) placement used the
  layer's nominal anchor, but the ink extends past `anchor + size` by the extrusion depth (13
  steps), the glow and the underline — a headline placed by its nominal bottom measured **45 px**
  too low.
- **Fix:** `core.SAFE` is canvas-dependent, `kinetic.headline` treats portrait `"lower"` as the
  bottom of the safe band, cards clamp to `C.W - 96`, and `film._fit_safe` translates a layer by its
  **raw alpha-ink bbox** (scrim excluded — a soft gradient may bleed, the letters may not).
  **Gate G17** fails a build whose portrait ink leaves the band; **G18** checks the 9:16 geometry.

## T21 · A scrim painted a hard rectangle over the brand mark

- **Symptom:** read back from a delivered frame, the corner mark sat on a sharp black box with a
  visible straight edge — not a design choice, an artifact.
- **Cause:** the mark is ~1500 opaque pixels in a corner, so `_add_scrim` produced a tiny panel and
  the 34 px feather had nothing to fade into.
- **Fix:** no scrim on `kind == "mark"` (bone + amber over a graded plate measures **6.5:1** unaided).

## T22 · The gate sampled the wrong frame, and the wrong box

Two measurement bugs in G05, both caught by asking *what the numbers would look like if the gate
were right*:

1. **Fast seek.** `-ss` **before** `-i` is a keyframe seek; with a 2 s GOP the gate measured a frame
   up to two seconds early — a frame from the *previous shot*, which is why shot 03's corner mark
   reported exactly **1.00:1** (flat plate: fg == bg). Seeking after the input is decode-accurate.
2. **Two position sources.** G05/G06 asked the builder for the *pre-fit* position while the renderer
   drew at the *fitted* one, so the gate sampled a box the film never used. Fixed with one shared
   `film._build_pil_pair()` that returns the raw layer, the scrimmed layer and the fitted position —
   the gate and the renderer can no longer disagree by construction.
3. A minimum glyph-sample guard (< 400 px) keeps a tiny mask from being scored against a mush of
   its own surroundings.

**Law:** a gate that disagrees with a delivered frame must first prove it is looking at the same
pixels. Two of the last three G05 "failures" were the gate's fault, and the fix was never to lower
the target.

---

## Inherited laws this engine obeys by construction

Cross-referenced, not duplicated:

| law | source | how this engine obeys it |
|---|---|---|
| bounded `apad` | stickman ledger #31 | the voice track is built by concatenation; `apad` is unused |
| limit to −4 dBFS, re-measure after decode | ledger #30 / noir §4.3 | `alimiter=limit=0.63` + decoded `volumedetect` |
| a filter output label is consumed once | ledger #37 | the mix is two passes with no shared labels |
| never a bare zoom below 1.0 (black slivers) | ledger #32 | the canvas is pre-overscanned 1.22 and warps read from it |
| eased camera ramps measure as frozen | ledger #33 | default ramp is linear-dominant |
| whole-file spectrum grades the wrong thing once voice dominates | ledger #35 | band energy split by voice presence |
| no caption pill / karaoke band | WF-05 approved profile | the type system has no pill renderer at all |
| the scene carries the image; type highlights it | editor brain §6 | type is one layer per idea, never a paragraph |

### T23 — a gaussian halo alone does not raise contrast on thin type
*Symptom:* the corner mark measured **3.70:1** on shot 03 after its scrim was removed; a blurred
copy of the glyphs (black 235) lifted it only to 3.90, and a three-radius version (4/1.0 + 10/0.88
+ 22/0.5) to **3.90:1 in the vertical cut** and 3.98 in 16:9 — still under 4.5.
*Cause:* the mark is 25 px type, so its stroke is ~4 px wide. A gaussian blur of a 4 px stroke has
very little energy left at the 2–5 px ring the gate samples (measured: the ring stayed at RGB
89–91, i.e. the plate's own brightness). Widening the radius spreads the same ink further and
makes it *weaker*, not stronger — this is why the v1→v3 loop barely moved the number.
*Law:* for small type, darken by **coverage**, not by blur. Dilate the glyph mask so the dark area
fully contains the ring, then blur just enough to lose the hard edge.

### T24 — a pad+blur round-rect "cloud" fixes the number and is visible as a shape
*Symptom:* a rounded rectangle over the ink bbox (+20 px, radius 34, blur 26, black 165) raised the
vertical mark to **6.41:1** and put a dark oval on the fog that is plainly visible at 2× — a scrim
in soft clothing. Rejected on sight, not on the number.
*Law:* a contrast fix that can be seen as an object on the plate is a defect even when it passes
the gate. The correct test is both: the gate **and** the 2× crop read back as an image.

### T25 — the gate report counted the gates that ran FIRST
*Symptom:* a report printed `RESULT 16/16 PASS` while G17 and G19 had both failed: `report` and
`report["result"]` were built before the vertical block appended its rows, so `failed` was 0.
*Cause:* summary computed in the middle of the function, gates added after it.
*Law:* the summary is the last thing computed, from the complete row list — and a "PASS" line that
was never re-derived from the rows is worth nothing. Same family as T22: a gate must prove it
looks at what it claims to look at.

### T26 — `--vertical` shipped a silent Short, and `mux(size=…)` was a dead parameter
*Symptom:* `run_film.py --vertical` produced a correct 1080×1920 file with **no audio stream**.
`film.render_vertical` writes the picture-only pass by design (that is what keeps the crop cheap),
and nothing muxed `master.wav` into it. The gate set at the time could not see it: G17–G19 ask about
geometry and contrast, and the A/V-duration gate reads the *master*.
*Second finding in the same line of code:* `FM.mux(..., size=(C.W, C.H))` accepted a size and never
used it. Harmless while only 16:9 existed; a trap the moment the same function muxed a portrait file
— the failure mode would have been a silently letterboxed Short.
*Law:* a delivery flag must be proved end to end, not just for the step it names. The vertical path
now muxes the same `master.wav` and deletes the silent intermediate, and `mux` states that the
container's size comes from the picture.

