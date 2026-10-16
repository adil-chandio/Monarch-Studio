# MONARCH WILD CINEMA — `monarch-wild-cinema`

**The channel's flagship production engine.** This is the style that turns
Monarch Studio's accumulated editing doctrine into a single, declarative,
reproducible pipeline for long-form wildlife cinema on YouTube.

- **Style ID** `monarch-wild-cinema`
- **Workflow code** `WF-07`
- **Trigger** `CINEGO <topic>`
- **Format** 1920×1080 · 30 fps · 2–6 min (long-form) + 1080×1920 vertical cut
- **Engine path** `src/tabahi/`
- **Entry point** `src/run_film.py`
- **Evidence** [`PROOFS.md`](PROOFS.md) — every number read back off a delivered file
- **Why it looks like this** [`ANALYSIS.md`](ANALYSIS.md) — the study of WF-01/WF-03/WF-05 and what carried
- **Doctrine** [`knowledge/INDEX.md`](knowledge/INDEX.md) · **Gate table** [`data/gates.json`](data/gates.json)

---

## 1 · Why this style exists

The forensic audit of `@monarch-cam` (2026-10-16) found the channel's exact
failure mode, in numbers:

| what worked | what died |
|---|---|
| 955,681 views — clip montage with a 60-second spoken hook | **16 views** — AI narration over a static ranking |
| long-form = **94.7 %** of all channel views | Shorts-only weeks produced **0 subs in 30 days** |
| one topic family (bears) = **54 %** of views | uploading into a vacuum, no series identity, no reason to subscribe |

And the compliance finding underneath it: **reposted compilations are the
channel's single largest risk** under YouTube's inauthentic-content policy.
Permission does not exempt a channel; whole-channel evaluation does not care
that a clip was "free to use".

MONARCH FILES #01 was built to answer all of it at once: 100 % owned IP — own
script, own narration, own generated plates, own synthesised score, own type.
Zero third-party footage, zero copyright exposure, and a real reason to
subscribe.

`monarch-wild-cinema` is that production, generalised. It is not a filter pack
and not a template: it is a **measured pipeline** with declared gates, a
failure register, and a shot plan you can read in JSON.

---

## 2 · What is genuinely different from every other style in this studio

| capability | WF-01 stickman | WF-03 noir film | WF-05 motion editing | **WF-07 wild cinema** |
|---|---|---|---|---|
| source | code-drawn frames | coded film plates | supplied footage | **generated plates + real data** |
| camera | 3-D rig projection | crop pushes | near/far 2.5D | **hybrid auto depth 2.5D + atmospheric separation** |
| grade | paper/ink | noir | clean editorial | **4 cinematic LUT looks with split-tone** |
| atmosphere | none | rain/neon | none | **god rays, volumetric haze, depth-aware motes** |
| type | extruded headline | typewriter ink | integrated | **extruded kinetic, 8 layer kinds, animated entrances** |
| data | none | none | none | **animated charts, gauges, range plots, source stamps** |
| sound | ASMR ledger | leitmotif | restrained accents | **procedural score: beds + 12 cue voices, true stereo** |
| honesty | — | — | — | **charts refuse unsupported comparisons; sources on screen** |

The last row is not decoration. It is the channel's differentiation: a cited,
species-specific encounter explainer — the thing every clip compilation skips.

---

## 3 · The pipeline in one picture

```
PLAN.json  (data, written by A03)
    │
    ├─ 1  STAGE    2.5D parallax       depth.py     auto depth from focus energy
    ├─ 2  GRADE    cinematic look      grade.py     LUT -> split-tone -> texture
    ├─ 3  AIR      rays/haze/motes     films.py     volumetric life
    ├─ 4  ACTION   streaks/impact/shake films.py    physical event
    ├─ 5  TYPE     extruded kinetic    kinetic.py   the idea, readable
    ├─ 6  CUT      motivated hand-off  transitions.py
    ├─ 7  WRITE    raw frames → ffmpeg film.py      streaming, no scratch
    │
    ├─ 8  SCORE    beds + cues         score.py     true stereo at the source
    ├─ 9  MIX      duck → loudnorm     score.py     two passes, -4 dBFS ceiling
    └─ 10 MASTER   H.264 + AAC         film.py      measured, never assumed
```

Every stage is a module with a single responsibility. An agent can replace one
stage without touching the others, and the gates measure the result, not the
intent.

---

## 4 · Directory contract

```
monarch-wild-cinema/
  README.md              this guide
  style.json             permanent identity
  workflow.json          trigger / runtime / delivery contract
  knowledge/             the doctrine, chapter by chapter
  src/tabahi/            the engine
      core.py            constants, easing, type system, colour + audio IO
      depth.py           depth field, environment canvas, 2.5D camera, Stage
      grade.py           4 looks, tone LUT, split-tone, bloom, grain, vignette
      films.py           impact, flash, haze, god rays, motes, streaks, shake
      kinetic.py         type objects + entrance animation
      viz.py             charts, gauges, range plots, source stamps, callouts
      transitions.py     4 motivated families + luma gate
      score.py           beds, 12 cue voices, two-pass mix, measurement
      film.py            compositor, encoder, master, vertical cut, sheets
      gates.py           the measured acceptance gates
      thumbs.py          thumbnail system with the 120 px legibility test
      run.py             one-command recipe helpers
  src/run_film.py        CLI entry point
  assets/fonts/          Montserrat VF, Anton, Barlow Condensed (+ OFL texts)
  assets/plates/         the plate library (generated, owned)
  data/                  visual DNA, motion grammar, audio policy, gates
  projects/              delivered productions + their PLAN.json
  proofs/                engine proofs with their measurements
  records/               incidents, decisions, reconciliation
```

---

## 5 · Running a production

```bash
# once per sandbox (the venv is not snapshot-persisted)
python3 -m venv /home/user/.venv
/home/user/.venv/bin/python -m pip install pillow numpy imageio imageio-ffmpeg opencv-python-headless

# render a plan (picture + score + mix + master + measurements)
cd styles/monarch-wild-cinema
/home/user/.venv/bin/python src/run_film.py \
    --plan projects/<slug>/PLAN.json \
    --out-dir projects/<slug>/build \
    --vertical

# gate it
/home/user/.venv/bin/python src/tabahi/gates.py --master projects/<slug>/build/<EP>_MASTER.mp4 \
    --plan projects/<slug>/PLAN.json --out projects/<slug>/reports/GATES.json

# thumbnails
/home/user/.venv/bin/python src/tabahi/thumbs.py --plan projects/<slug>/PLAN.json \
    --out-dir projects/<slug>/build/thumbs
```

Cost on this sandbox (2 cores, no GPU): **≈ 0.40 s/frame** at 1080p, i.e.
**≈ 12 minutes per finished minute** of long-form. A 3-minute episode is a
coffee break, not an overnight job. Measured after the optimisations recorded in
`knowledge/09_FAILURE_REGISTER.md`.

---

## 6 · The measured gates (a finding is not a delivery)

| # | gate | threshold | why |
|---|---|---|---|
| G01 | frames produced | ≥ 99.5 % of planned | a missing shot is not a style choice |
| G02 | duplicate frames | 0 | dead air reads as a broken upload |
| G03 | per-shot motion p10 | > 0.12 | a still that never moves is a slideshow |
| G04 | max Δluma between frames | < 8 | no strobe transitions |
| G05 | type contrast vs plate | ≥ 4.5:1 | big words survive size; small ones do not |
| G06 | type in safe band | inside y 60–970 / x 60–1860 | platform chrome eats the edges |
| G07 | decoded audio peak | ≤ −1.0 dBFS | AAC overshoots the PCM limiter |
| G08 | integrated loudness | −16.5 ± 1.0 LUFS | YouTube's reference is −14, we deliver −16 |
| G09 | true peak | ≤ −1.0 dBTP | headroom is not optional |
| G10 | L/R correlation | 0.55 – 0.85 | outside that band the mix is mono or phase-sick |
| G11 | side/mid energy | > 0.25 | width must actually reach the listener |
| G12 | audio vs video duration | within 0.10 s | a tail that runs long is a defect |
| G13 | 4–8 kHz share (VO-absent) | > 10 % | the bed must not be mud |
| G14 | 120–500 Hz share (whole file) | < 58 % | three bass instruments is a rumble |

`gates.py` writes every number it measured, including the ones that failed.
A production is delivered with its gate table attached, not its intentions.

---

## 7 · What is forbidden here

Written down because each one has already cost this studio a delivery:

- **No full-frame still slideshow.** Camera motion must supplement real
  motion; it can never certify a static frame.
- **No stock overlay.** Every atmospheric element is generated per frame.
- **No third-party footage, music or SFX.** The score is synthesised; the
  plates are generated (`assets/plates/`). This is the compliance spine.
- **No unsupported comparison.** A chart may not imply that two samples are
  comparable when they are not. Say so in the `note` instead.
- **No claim without a source on screen.** `viz.source_stamp` exists so the
  citation can be visible, not just true.
- **No caption band.** Integrated scene type only; the rejected V6 pill
  treatment stays rejected.
- **No flooding the frame with colour.** Accents tint, they never flood.
- **No reported number that was not measured.** "Looks fine" is not a gate.

---

## 8 · Provenance

Built 2026-10-16 as `WF-07` after the complete survey of every editing system
in Monarch Studio: `monarch-stickman-animation` (WF-01, the mistake ledger
M1–M38 and the 19+1 gates), `monarch-noir-film` (WF-03, film grammar and
callbacks), `premium-motion-editing` (WF-05, approved V5/V6 policy: clean
layout, near/far 2.5D, transition families, caption-pill rejection), and
`studio/editor-brain` (the twelve habits, hooks, retention cadence, the
three-pass review).

The engine is the synthesis. Where the sources disagreed, the newer measured
result won and the disagreement is recorded in `knowledge/09_FAILURE_REGISTER.md`.
