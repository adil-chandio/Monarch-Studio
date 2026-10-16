# PROOF-01 — the first fully measured film from `monarch-wild-cinema` (WF-07 · TABAHI)

**Trigger:** `CINEGO bear charge behaviour` · **Plan:** `projects/proof-01-trailer/PLAN.json`
**Delivered:** 2026-10-16 · 1920×1080 · 30 fps · **31.0 s** · −16.00 LUFS · **16/16 gates PASS**

This proof exists to answer one question with evidence: *does the engine actually produce
something that stops a scroll, and can it prove it?* The plan is data, the renderer is generic,
and every claim below came off a delivered file.

---

## 1. The artefact

| | |
|---|---|
| Master | `projects/proof-01-trailer/delivery/PROOF-01-TRAILER_MASTER.mp4` — 49.22 MB, 31.0 s, 12 497 kb/s h264 + AAC 194 kb/s 48 kHz |
| Vertical 9:16 | `projects/proof-01-trailer/delivery/PROOF-01-TRAILER_VERTICAL.mp4` (1080×1920, subject-tracked crop) |
| Picture intermediate | `build/picture.mp4` (crf 12 · ultrafast, 930 frames, 535 s wall clock) |
| Gate report | `reports/GATES.json` — **16/16 PASS, 0 FAIL, 0 UNMEASURED** |
| Build report | `reports/BUILD.json` |
| Thumbnails | `reports/thumbs/` — 5 concepts + 5 feed-size tests + `ALL_THUMBS.jpg` |
| Score / mix | `build/score.wav`, `build/master.wav` |

---

## 2. Gate report (as delivered)

```
G01  frames produced                    930      >= 930    PASS
G02  duplicate frames                     0           0    PASS
G04  max dLuma inside shots            7.64          < 8    PASS
G15  cut-point luma delta              2.74         < 26    PASS
G03  per-shot motion p10 (worst)      0.394        > 0.12   PASS
G05  min type contrast (delivered)     6.33        >= 4.5   PASS
G06  type inside safe band                0             0   PASS
G16  card ink inside its canvas           0             0   PASS
G07  decoded sample peak dBFS          -3.4       <= -1.0   PASS
G08  integrated loudness LUFS        -16.10  -16.5 +- 1.0   PASS
G09  true peak dBTP                   -3.41       <= -1.0  PASS
G10  L/R correlation                 0.561    0.55 - 0.85   PASS
G11  side/mid energy                 0.282        > 0.25   PASS
G13  4-8 kHz share (whole)            25.2          > 10%   PASS
G14  120-500 Hz share (whole)         25.5          < 58%   PASS
G12  video/audio duration delta        0.0       <= 0.10 s   PASS
```

Three of these gates were **re-scoped** and one was **added** during this build; each change is
recorded in `data/gates.json → revisions` with its evidence, and the reasoning is in
`knowledge/08_MEASURED_GATES.md`. Short version: G04 was measuring the edit instead of the strobe
(cut → G15, whose BT.1702 threshold is stricter around a cut than the old rule); G05 was comparing
type against a plate *proxy* instead of the delivered pixels; G06 measured a layer's canvas
instead of its ink; G16 is new and exists because the delivered master said **"BEAR SPRA"**.

---

## 3. The film, shot by shot

| # | s | Plate | Look | Transition in | Type | Purpose |
|---|---|---|---|---|---|---|
| 01 | 4.0 | `01_hook_charge` | nocturne | hard | "40 METRES." → "THREE SECONDS." | the scroll-stop: distance + clock in the first 3 s |
| 02 | 3.6 | `03_running` | alarm | dip | "THEY RUN." | the visual question: how fast? |
| 03 | 4.4 | `12_grizzly` | nocturne | whip | "MOST CHARGES ARE NOT ATTACKS." + brand mark | the promise, and the first honest turn |
| 04 | 3.8 | `04_speed` | alarm | depth | **35 MPH** | the number the channel's audience came for |
| 05 | 4.2 | `05_watching` | nocturne | wipe | GRIZZLY · "DON'T RUN. DON'T FIGHT." | the answer card |
| 06 | 4.0 | `07_spray` | first_light | dip | **92 %** gauge + source stamp | the measured payoff, cited on screen |
| 07 | 3.8 | `09_bear_country` | nocturne | dip | "THREE THINGS TO REMEMBER" | the re-hook at 78 % of runtime |
| 08 | 3.2 | `10_endcard` | archive | dip | "MONARCH FILES" + lower third | the series promise |

Score: 29 cues placed against the cuts plus five beds (drone · air · shimmer · pad · tension).
Every cut point carries a cue; the cue table in `PLAN.json` **is** the edit.

---

## 4. Why this should stop a scroll (grammar, not vibes)

| Retention mechanism | Measured in this artefact |
|---|---|
| Motion in frame 1 (WF-05 hook law) | per-shot motion p10 **0.394** against a 0.12 floor; 0 duplicate frames in 930 |
| First promise inside 3 s | shot 01 carries two statements, the second lands at 2.5 s |
| A visual question by 3.6 s | "THEY RUN." over a running plate, then the number at 13.3 s |
| A re-hook past the halfway point | shot 07 headline at **25.15 s** = 81 % of runtime |
| Readable on a phone | worst-case type contrast **6.33:1** (WCAG), all five thumbs legible at 213×120 |
| Not a "content farm" signature | 100 % owned plates, a synthesized score (no licensed bed), an on-screen citation, no karaoke captions |
| Re-watchability | the endcard names the series and the episode, so the Shorts cut and the long-form advertise each other |

---

## 5. What the build cost, and what it did not prove

**Cost (2 cores, no GPU):** 535 s for 31 s of finished film, including score, mix, master and
measurement — **0.58 s/frame**. A 6-minute film is ≈ 1 h 45 m on this box; the documented scale
path is sharding shots across processes.

**Not proven yet (stated so nobody assumes otherwise):**
- No real narration has been through `build_voice_track` in this style. The report's audio is
  **music-led**; the VO path is built and untested with a human take.
- The vertical cut renders **camera + grade** into 1080×1920 and does not thread type or FX
  through the 9:16 canvas. It is a real Shorts master, not yet a designed one.
- Retention claims here are **grammar** claims. Only A08, with the channel's own 48-hour numbers,
  can convert them into a view-count claim.

---

## 6. Handoff

**Nothing in this proof needs a human decision except publishing.** If the trailer is wanted as a
channel upload, the remaining human steps are the same shape as MF-01: download the master, use
the recommended thumbnail (`B_testing` scored best on local contrast; see `reports/thumbs/`), paste
the description, and mark **altered/synthetic = YES**.

Recommended next actions for the crew (no human input required):
1. A03 writes the vertical-first plan (`origin: "vertical"` in the layout helper) and A05 re-cuts.
2. A04 records the narration for the 3:07 long-form episode this trailer advertises.
3. A06 assembles title/description/tags from the verified numbers in this file.
