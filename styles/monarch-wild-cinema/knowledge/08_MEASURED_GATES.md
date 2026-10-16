# 08 · The measured gates

> Never trust the eye. Every rule in this style has a number and a gate.

`src/tabahi/gates.py` runs the table below over a delivered master plus its
plan, and writes every measurement it took — including the ones that failed.
A production ships with its gate table attached, not with its intentions.

| # | gate | threshold | reads | why it exists |
|---|---|---|---|---|
| G01 | frames produced | ≥ 99.5 % of planned | ffprobe | a missing shot is not a style choice |
| G02 | duplicate frames | 0 | sampled frame diff | a frozen frame reads as a broken upload |
| G03 | per-shot motion p10 | > 0.12 | frame diff inside each shot | a still that never moves is a slideshow |
| G04 | max Δluma between frames | < 8 | luma trace | no strobe transitions (ledger M14) |
| G05 | type contrast vs plate | ≥ 4.5:1 | `kinetic.contrast_report` over every layer | small words die before big ones |
| G06 | type inside the safe band | y 60–970 (16:9) | layer bounding boxes | the stickman film shipped with every caption under the phone UI |
| G07 | decoded sample peak | ≤ −1.0 dBFS | `volumedetect` **after decode** | AAC overshoots the PCM limiter by ~2.4 dB |
| G08 | integrated loudness | −16.5 ± 1.0 LUFS | `loudnorm=print_format=json` | delivery reference for this channel |
| G09 | true peak | ≤ −1.0 dBTP | loudnorm report | headroom is not optional |
| G10 | L/R correlation | 0.55 – 0.85 | `score.stereo_report` | outside the band the mix is mono or phase-sick |
| G11 | side/mid energy | > 0.25 | `score.stereo_report` | width must actually reach the listener |
| G12 | audio vs video duration | ≤ 0.10 s | container | a tail that runs long is a defect |
| G13 | 4–8 kHz share, voice absent | > 10 % | `score.band_energy` | the bed must not be mud |
| G14 | 120–500 Hz share, whole file | < 58 % | `score.band_energy` | three bass instruments is a rumble |

## How the gates were calibrated here

Three of them are direct inheritances from measured failures in this
repository, and the numbers are not arbitrary:

- **G06 (safe band)** — the stickman project's caption baseline sat at
  y = 1718 on a 1920 frame: **202 px from the bottom**. Reels/Shorts UI covers
  roughly the bottom 320–420 px. Every caption in that film was covered on a
  real phone and nothing in the editor revealed it. The fix moved the grid into
  y ∈ [180, 1500]. This gate refuses to rely on anyone noticing.
- **G03 (motion p10)** — the stickman ledger recorded `p10 frame-diff = 0.06`
  in two scenes and a **0.53 s dead zone at t = 5.93**, inside the first-seven-
  second retention window. The cause was properties that froze the instant they
  finished revealing. `breathe = 1.6 px` exists so a card is never perfectly
  still.
- **G04 (luma jump)** — 49 frames exceeded an 8-point luma jump in a 37-second
  film driven by saturated colour panels sweeping the frame. The transition
  set here is bounded and `transitions.luma_profile()` measures each kind.

- **G07 (decoded peak)** — the noir delivery measured a pre-encode peak of
  −1.52 dBFS that decoded at **+0.85 dBFS**. The measurement must happen after
  the codec, or it is measuring the wrong signal.

## Reading a gate report

```
GATE      VALUE            TARGET          VERDICT
G01       960/960           >= 99.5%        PASS
G02       0                0               PASS
G04       3.1              < 8             PASS
...
RESULT    14/14 PASS
```

A gate that cannot be measured is reported as `UNMEASURED` and **fails**. An
unknown is not a pass. The only path to shipping with a failed gate is a
recorded human override in `OVERRIDES.log` naming the gate, the measured value
and the reason — the same mechanism the WF-06 compliance agent uses.

## What the gates deliberately do not measure

- **Taste.** No gate can tell you the hook is boring.
- **Truth.** G05 measures whether a claim is *readable*, not whether it is
  *correct*. Correctness is A07's job with `CLAIMS.md` and the source lock.
- **Novelty.** "Is this the same video as last week" is the editor brain's
  `concept.py gate` (freshness), a separate check with a separate registry.

---

## G15 and the three gate revisions (2026-10-16)

`data/gates.json` carries a `revisions` block. Read it before touching the table: each entry
records what the gate used to measure, what it measures now, the measurement that forced the
change, and why the new version is not a loosening.

| Gate | Was | Now | Why it is stricter |
|---|---|---|---|
| G04 | max dLuma between **any** two frames < 8 | max dLuma **inside a shot** < 8, 0.35 s cut windows excluded | The old target read a hard cut as a strobe. Measured on PROOF-01, the six largest jumps (77.2, 72.5, 70.2, 51.7, 47.7, 47.0) **all** sat on shot boundaries while the in-shot mean dLuma was 0.5–2.8. The cut moved to its own gate. |
| G15 (new) | — | cut-point luma delta < 26 | BT.1702's flash threshold. It constrains the frames the old G04 could not describe, and it is what forced the flash/impact rise times: an instant 0.34-alpha flash is a 55-level jump. |
| G05 | ink vs the **plate's** mean luma | ink vs the **surrounding pixels of the delivered frame** (WCAG) | A proxy cannot see the scrim, the shadow, the bloom or the grade. The proxy scored 2.25:1 on a headline the renderer had already fixed — and would have passed type on a blown highlight. |
| G06 | layer **canvas** extent vs the safe band | **alpha-ink bbox** vs the safe band | Three layer kinds are full-frame canvases with the ink in a corner; the canvas measurement called a corner mark at y 77–123 "mark@y0-1080". |

**Rule for future revisions:** a gate may only be re-scoped with (a) the measured evidence that
the old scope was describing the wrong thing, (b) a replacement that covers the real risk, and
(c) an entry in `data/gates.json` `revisions`. Removing a gate because the render failed it is
not a revision, it is a cover-up.

## G16 — text runs are recorded, not eyeballed (2026-10-16)

`core.RecDraw` is an `ImageDraw` subclass that records the rect of every `text()` and
`draw_tracked()` call and exposes the list as `img.info["text_rects"]`. Gate G16 fails the build
when any recorded run leaves its own canvas.

It exists because of a defect that no other gate could see: `draw_tracked` anchors at the **left**
edge, and `viz.gauge` passed the card's **centre**, so the label started mid-card and ran off the
right side. Nothing raised, the plan was valid, the audio was clean, the frames moved — and the
delivered master said **"BEAR SPRA"**. It was found by extracting a frame from the finished file
and *looking at it*, which is the same loop that caught the inverted depth map and the blown-out
rays.

| | |
|---|---|
| Violations the first rule had | The panel of every card layer is drawn edge-to-edge on purpose, so a raw alpha-bbox check flagged all four cards; the second rule (glyph core vs the far edges) still flagged decorative accent bars. That is why the check is now a **contract** rather than a heuristic. |
| What it cannot do | G16 validates the **builder against the plan**, so the picture must be re-rendered whenever type code changes. G05 samples delivered frames and is the backstop for a stale render. |
| Cost | Free — the rects are recorded during layer construction, which already happens once per unique spec. |

## G05 measures the HOLD, and the hold can be darker than the entry

`_frame_rgb` is decode-accurate (`-ss` after `-i`), and the sample lands at `t_in + 1.0 s`, clamped
to the middle of a short beat: `min(1.0, max((out - in) * 0.5, 0.25))`. That is deliberate — the
question "can this be read?" is about the **hold**, not the entry frame, which is semi-transparent
by design (the entrance ramps alpha from 0.25).

Consequence, measured: a layer that passes in the long-form cut can fail in the vertical cut while
the *same layer* at the *same position* passes, because the tracked crop moved the plate underneath
it. The 16:9 mark measured 6.5:1 on shot 03; the 9:16 crop of the same shot measured **4.03:1** —
the crop pulls a lit patch of fog under the mark. That is not a gate bug, it is the vertical cut
needing its own treatment (`vertical_type`), which is why that key exists.

## G17–G19 — the gates that exist because of the 9:16 cut (2026-10-17)

| Gate | Question | Target | Where measured | Why |
|---|---|---|---|---|
| G17 | portrait type inside the Shorts band | 0 violations | `gates.py --vertical`, from the **fitted** position | a Short's chrome owns the top and bottom of the frame; type inside the canvas but under the buttons is still covered (T19, T20) |
| G18 | vertical geometry | 1080×1920 | `film.render_vertical` | the first vertical cut was a correct 1080×1920 file with **no type in it** — geometry is not composition |
| G19 | worst delivered vertical type contrast | ≥ 4.5 | `gates.py --vertical`, decode-accurate frames | a crop changes the plate under the type: the same mark on the same shot measured 6.5:1 in 16:9 and 3.85:1 in 9:16 |

G19 reuses the G05 sampling law exactly (WCAG ink-vs-surroundings on the delivered frame, hold
time, eroded core, glyph-sized ring or panel-band background) because two contrast gates that
measure different things cannot be compared. **G05 is not evidence about the vertical cut and G19 is
not evidence about the landscape cut**; a style that ships both must run both.

### The mark treatment, in one law

Small type cannot be made legible by blurring. The mark is 25 px, so a stroke is ~4 px and a
gaussian of that stroke has almost no alpha left at the ring the gate samples — v1 (blur 7) 3.90,
v2 (three-radius halo) 3.98, v3 (wider halo) 3.90 on the vertical cut: three attempts, all under
target. What works is **coverage**: dilate the glyph mask by 7/14/26 px with an elliptical kernel,
blur 2.5/7/16 px so no edge is visible, and stack at alpha 225/180/105 under the letters. Measured
on the shot that failed: **7.37:1 (vertical) / 7.37:1 (landscape)**. It reads as a broadcast drop
shadow at 2× and leaves no shape of its own — the soft-oval version that also fixed the number was
rejected on sight (T24).

### A PASS line must be derived from the rows, last

The report's summary used to be computed before the vertical block appended G17–G19, so a report
could print `RESULT 16/16 PASS` while both vertical gates had failed (T25). The summary is now the
last thing built, from the full row list — and the printed verdict is re-derived, never carried.

