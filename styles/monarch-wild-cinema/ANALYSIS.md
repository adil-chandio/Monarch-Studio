# ANALYSIS — every editing and animation system already in this studio, and what carries into `@monarch-cam`

Stage 1 of the brief ("monarch studio ke saari editing ko dekh kar…") is this file. Stage 2 is
`README.md` + `knowledge/01–11` (the style itself), Stage 3 is `PROOFS.md` (measured evidence).
Nothing here is a summary from memory: every claim below was read out of the repo, and the ones
that produced a rule are marked with the measurement that produced it.

- Style id: `monarch-wild-cinema` · Workflow code **WF-07** · trigger **`CINEGO <topic>`**
- Engine brand: **TABAHI** (`src/tabahi/`)
- Target channel: **`@monarch-cam`** (`UCfYdmsLO4Q8_IHklTyYieLg`), 3 830 subs, 2 147 271 views,
  long-form is 94.7 % of those views, bears ≈ 54 % of the catalogue, best video 955 681 views.

---

## 1. Inventory — what already exists

| Code | System | Root | What it actually is |
|---|---|---|---|
| WF-01 | Monarch Stickman Animation · `SHADEGO <topic>` | `styles/monarch-stickman-animation` | Hand-animated 2-D stickman shorts. 36 MB of prompts (`MASTER_PROMPT` → `_V4`), ledgers (`AUDIO_EVENT_LEDGER.csv`, `ASMR_*_LEDGER.csv`), `CHARACTER_SPEC.md`, `FORENSIC_AUDIT_V7.md`, own font set. Status **PARKED**. |
| WF-03 | Monarch Noir Film · `NOIRGO <topic>` | `styles/monarch-noir-film` | 1920×1080 / 24 fps, 120–180 s dark animated films. Two engines: `noir.py` (v1, black world + bone-white line hero + one amber light + one red villain colour, cast-shadow physics, text narration + 2–3 voice lines) and **NOIRGO MAX** (v2: illustrated plates + crop camera `world.py`/`film_window.py`, 3-D stick human `stick3d.py`, full VO + SFX + score `audio_window.py`, **27 gates** `gate_window.py`). Status **ACTIVE_WITH_DRIFT**. |
| WF-05 | Premium Motion Editing · `MOTIONGO <topic/reference>` | `styles/premium-motion-editing` | The studio's flagship *editing* system: 2.5-D motion over stills and refs, `knowledge/01–17` + `MASTER_CODEX`, `data/{visual-dna,motion-grammar,audio-policy,approved-profile,metaphor-bank,lessons}.json`, `src/{motion,render_project,policy,wf05,verify_output,…}.py`, delivered case `projects/einstein-flow-state` (V5 direction + accepted V6, lower caption pill **rejected**). Status **READY_WITH_USER_POLICY**. |
| — | Editor brain | `studio/editor-brain` | Cross-style memory: `MONARCH_EDITOR_BRAIN.md`, `brain/{concept,library,study}.py`, `briefs/`, `dna/`. |
| WF-06 | YT Agent Crew | `workflows/wf06_yt_agent_crew` | The production line that *consumes* all of the above: A01 manager (8-point rubric ≥ 4.0, 3-strike), A02 hunter, A03 architect (hook ≤ 3 s, re-hooks at 25/50/75 %), A04 voice (−16.5 ± 1 LUFS), A05 craftsman, A06 packager, A07 warden (12 checks, VETO), A08 oracle. |
| — | MF-01 production | `channel/productions/MF-01/05_PRODUCTION` | The first *shipped* build for this channel: 14 generated plates, 24 overlays, 4 thumbs, `build.py`, `make_thumbs.py`, 3:06.92 master at −16.17 LUFS. Shot-list format kept **CLOSE CALL FILES-compatible**. |
| — | Library standard | `docs/STYLE_LIBRARY_STANDARD.md` | The no-loss contract every style must satisfy (what a style folder must contain, and what may never be silently dropped). |

---

## 2. What each system actually does — mechanically

### 2.1 WF-01 Stickman (the audit that named the failure modes)

`FORENSIC_AUDIT_V7.md` is the most valuable document in the studio, because it is a defect
taxonomy rather than a wish list. Its tiers, verbatim in structure:

- **Tier 1 shipping defects** — *1.1* the caption band sits **underneath the platform UI**;
  *1.2* every accent colour **fails contrast on the cream paper**; *1.3* the transitions are
  **a dark strobe, not a smooth swipe**.
- **Tier 2 engagement leaks** — *2.1* a **0.53 s dead zone** right after the first cut;
  *2.2* **10 % of frames are effectively frozen**; *2.3* element reveals **pop instead of
  settling**; *2.4* the cut's visual peak lands **1–2 frames before the audio impact**.
- **Tier 3 audio** — *3.1* the mix is **effectively mono**; *3.2* the spectrum is **muddy and
  dull**; *3.3* twelve **loudness holes**.
- **Tier 4** — character and motion-graphics craft.

Every Tier-1 and Tier-2 item is a *measurable*, and all of them became gates in this style
(G02 frozen frames, G04 strobe, G05 contrast, G06 safe band, G12 sync, G10/G11 stereo,
G13/G14 spectrum). That is the single biggest inheritance from WF-01: **its failures are our
gate table.**

### 2.2 WF-03 Noir (two engines, and the proof that measurement scales)

`noir.py` established the studio's "own DNA per film" habit: a palette with **one** accent and
**one** danger colour, cast-shadow physics, narration as text. NOIRGO MAX rebuilt the same
identity out of **illustrated plates + a crop camera + a 3-D stick human + recorded VO + score**,
and — the important part — it wrote a **27-gate** validator (`gate_window.py`) instead of trusting
the eye. Two lessons carried over verbatim:

1. **A style is a gate table plus assets, not an aesthetic description.**
2. **Camera on stills works** (`world.py` crop camera) — this style extends the same idea into
   true per-pixel depth parallax rather than a crop window.

### 2.3 WF-05 Premium Motion Editing (the grammar this style extends)

`knowledge/05_MOTION_DEPTH_AND_TRANSITIONS.md`, `06_TYPOGRAPHY_AND_CAPTION_POLICY.md`,
`07_AUDIO_NARRATION_AND_PACING.md` and `data/motion-grammar.json` define the house motion
language, and the numbers below are lifted from them unchanged:

- Transitions: `depth_push` / `diagonal_whip` **0.25 s**, `feathered_cut` **0.22 s**; near-plane
  zoom deltas **0.025–0.09**; roll up to **0.65°**.
- Entrances: **0.34 s**, **13 extrusion steps** for the display type.
- Typography: a **caption pill, karaoke highlight and active-word strip were explicitly
  rejected** by the user. What survives is *display type* — a few large statements — which is
  exactly what a trailer needs.
- Hook laws: frame 1 in motion, first word ≤ **0.6 s**, visual question ≤ **0.8 s**, contrast
  spike at **1.0–1.5 s**, promise ≤ **3 s**, `TLAG = 0.050 s` (act the cut ahead of the sound).
- Audio laws: evaluate A-vs-B **on isolated stems**, put the width **at the source**, limit to
  **−4 dBFS**, **re-measure after decode**, duck at **5:1**.
- Motion laws: no `int()` in an animated pixel path, zoom floor ≥ 1.0, ramps linear-dominant,
  never `abs()` next to a signed direction.

### 2.4 WF-06 crew (who runs the machine)

The crew is the *process* half of the deliverable and it does not change here: A03 writes the
plan, A05 renders it, A07 gates it, A06 packages it, A08 reads the 48-hour numbers. This style
adds one artefact the crew can execute without judgement calls: **`PLAN.json` is the picture**,
and every number in it is either a WF-05 doctrine value or a value measured in `PROOFS.md`.

### 2.5 MF-01 (the channel's own grammar)

MF-01 already proves the channel's winning shape: **owned plate + one fact + one VO line + one
caption**, 187.5 s over 24 shots, 3 thumbs, all 213×120-legible. Two of its properties are hard
constraints on this style: the **plate set is 14 owned images** (no third-party footage, no
permissioned clips — the audit's standing blocker), and the **shot-list format must stay CLOSE
CALL FILES-compatible** so an episode can be re-planned in the old tooling.

---

## 3. Transferable laws (extracted, numbered, each with its origin)

1. **Metrics beat adjectives** (WF-01, WF-03). Any claim about the picture must be a number read
   off the delivered file.
2. **Cut on a designed transition or not at all** (WF-01 1.3). A hard cut is legal editing; a
   1-frame jump of 70 luma is a strobe.
3. **Type needs its own backdrop** (WF-01 1.2). Contrast is measured against what is *behind the
   ink in the render*, not against the plate.
4. **Every frame must move** (WF-01 2.2, 10 % frozen). A still plate needs parallax, haze, grain
   or motes in every single frame.
5. **The visual peak lands with the sound, never before** (WF-01 2.4, `TLAG = 0.050 s`).
6. **Reveals settle, they do not pop** (WF-01 2.3) — 0.34 s entry, 13 extrusion steps.
7. **Width is built at the source, and "mono" is a defect** (WF-01 3.1, WF-05). L/R correlation
   is a gate, not a taste.
8. **The spectrum is a target, not a by-product** (WF-01 3.2).
9. **Loudness holes are defects** (WF-01 3.3) — loudness is solved against a measured reference.
10. **Own DNA per film, one accent, one danger colour** (WF-03).
11. **A style ships as a gate table** (WF-03's 27 gates).
12. **The plan is data; the renderer is generic** (WF-05 `render_project.py` + MF-01 `build.py`).

---

## 4. What does NOT transfer (rejected here, with the reason)

| Pattern | Where it lives | Why it is rejected for `@monarch-cam` |
|---|---|---|
| Caption pill / karaoke / active-word strip | WF-05 (rejected by the user, `06_TYPOGRAPHY`) | Re-rejected. Mobile-first karaoke captions on a 16:9 wildlife trailer read as "faceless content farm" — the exact failure mode the channel's audit measured (AI-narrated ranking video: **16 views**). |
| 24 fps | WF-03 headline format | Channel truth is 30 fps (MF-01, and every reference upload in the audit). Changing fps for style would break the comparison. |
| Character rigs / stick humans | WF-01, WF-03 NOIRGO MAX | No characters exist in wildlife footage; a rig would be a fake. The subject is the animal, and the camera is the only "character". |
| Full-frame white flashes on the beat | common trailer shorthand | Measured as a **strobe** (55-level jump at alpha 0.34) and capped: rise **0.13 s**, strength ≤ 0.16, and the gate enforces < 8 luma per frame. |
| Sepia/archive look as a *default* | WF-03 noir palette | It is a **shot-level** look here (`archive`), not the film's identity. Wildlife needs believable colour; the noir world is available but optional. |
| A long 120–180 s runtime per artefact | WF-03 format | `@monarch-cam`'s winner is **7:27**, but the first mountain is a 30–60 s proof plus Shorts; a 3-minute episode already exists as MF-01. |

---

## 5. Gap analysis — what no existing system gives this channel

| # | Gap | Why it matters for retention | Filled by |
|---|---|---|---|
| 1 | **Depth on a single owned still** | A locked-off plate is the #1 "dead frame" source (WF-01 2.2). Per-pixel parallax turns one image into a moving camera. | `depth.py` focus-energy saliency → 2.5-D warped canvas, plus far-plane haze so the parallax reads even on low-contrast plates. |
| 2 | **Type that survives a phone at 213 px** | The audit's winning videos stop the scroll in the first 0.8 s with a *readable* statement. | `kinetic.py` display type + automatic scrim; `thumbs.py` feed test at 213×120. |
| 3 | **A score instead of a bed** | Music beds are the tell of a compilation channel. | `score.py`: 12 cues + 5 beds, synthesized, mixed to a measured target. |
| 4 | **An honest sound-and-gate contract** | A07's VETO is only as good as the numbers it can read. | `gates.py`: 15 gates, all measured on the delivered master, UNMEASURED = fail. |
| 5 | **Information density that is not a "chart slide"** | The channel's audience came for *facts about bears*. | `viz.py`: bar/range/gauge/source-stamp drawn in the same type system as the headlines. |
| 6 | **Reuse of the 14 owned plates** | Zero third-party footage is a *legal* constraint, not a preference. | Every plan composes from `assets/plates`; the engine has no concept of an external clip. |

---

## 6. Design decisions taken (and the alternative that was dropped)

| Decision | Taken because | Alternative dropped |
|---|---|---|
| Renderer in **Python + numpy + OpenCV**, encoder fed by raw frames | The studio's other engines already speak this language; no Remotion/Node dependency, no headless browser, runs on 2 cores. | Remotion/After Effects pipeline (adds a runtime nobody can debug in this repo). |
| **Per-shot declarative `PLAN.json`** | "The plan is data" (WF-05). A03 can write it; A05 never edits code. | Hard-coded shot functions (every episode would need a programmer). |
| **Four looks** (`nocturne`, `first_light`, `archive`, `alarm`) | Enough grammar to build a trailer arc, small enough to gate. | A full colour-science stack (nothing to measure it against yet). |
| **Procedural score** (`score.py`) | 100 % owned, no licensing, deterministic, and mixes to a numeric target. | Licensed music beds (the exact pattern the audit flagged in competitors). |
| **Two-pass loudnorm + linked numpy limiter** | ffmpeg's `alimiter` and `loudnorm` are per-channel and destroyed the stereo image on this material (measured: 0.580 → 0.320 → 0.055). | Trusting one ffmpeg filter chain. |
| **Corners softening at 80 % + grain** | Real optics never end at a straight edge; the plates are 16:9 but the grade must not look pasted. | Full-frame flat grade. |
| **Gate table split out of the renderer** | The warden must be able to fail the picture. | "It looks fine" self-review. |

---

### 6.1 The vertical cut is a delivery format, not a downscale (2026-10-17)

**Decision:** the style ships **two masters** from one plan — 1920×1080 and 1080×1920 — and the
vertical one is a first-class artefact: `core.canvas(VW, VH)` re-scopes every builder, the camera
and grade run at full size, a subject-tracked crop carries the frame to portrait, and the type is
composed *inside* the portrait canvas. Three gates (G17/G18/G19) run only against that file.

**Alternative dropped:** letterboxing the 16:9 master into a 9:16 frame, or an automatic centre
crop. Both are cheap, both put the subject off-frame on a phone, and neither answers the platform's
real constraint — the Shorts UI owns the top ~13 % and the bottom ~20 % of the picture. A viewer
looking at a Short sees the plate through a window the design must know about; ignoring it is how a
"perfect" landscape film reads as an amateur upload in the feed.

**What the measurement changed:** the first vertical attempt was a real 1080×1920 render with **no
type in it** — the type was threaded into the landscape canvas only, so the crop simply did not
carry it (T19). The second put a headline under the platform's button column (T20). The third left
a hard-cornered black scrim box on the plate around the brand mark (T21). Each was found by
**reading the delivered frame back as an image**, not by reasoning about the code — the same rule
that found the blown god-rays and the strobe flash.

**What it costs:** the portrait pass is ≈ 250 s for 31 s of film on 2 cores (full-size camera the
whole way; the crop is the cheap part), i.e. the vertical master adds roughly 60 % to a build. That
is the price of a Short that does not look like a re-upload.

---

## 7. Cost of the system (measured on this box, 2 cores, no GPU)

| Stage | Cost |
|---|---|
| Depth estimation per unique plate | ≈ 2.5 s |
| Picture render, 1920×1080 | ≈ **0.5 s/frame** end-to-end (≈ 15 min per finished minute) with the fast intermediate + final mux |
| Score build, 31 s | ≈ 4 s |
| Mix (two-pass, measured) | ≈ 10 s |
| Vertical 9:16 cut | Same per-frame cost, 1080×1920 canvas |
| Thumbnails (5 concepts + feed tests) | ≈ 17 s |

The renderer is the wall; the honest scale path is shot-sharding across processes (documented in
`knowledge/10_PRODUCTION_RUNBOOK.md`) rather than a rewrite.

---

## 8. What is still unproven

- The vertical path renders the **plate cut** (camera + grade) without threading the type and FX
  through the 9:16 canvas. It is a real 9:16 master, but it is not yet a *designed* Short.
- No real narration has been through `build_voice_track` in this style; the VO path is built and
  untested with an actual human-read take.
- A08 is blind until the channel gives 48-hour numbers; retention claims in this pack are
  *grammar* claims (hook timings, motion density, contrast) rather than view-count claims.
