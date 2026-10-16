# KAANTA · Macro Director Cut v6

**WF-02 · native1080×1920 · 30fps · 30.5s**

The user explicitly selected **new cinematic shots with the same voice/script**, rather than another small polish pass or a rewritten hook. V6 changes how the story is photographed and staged; the original narration, reading copy and timings are retained.

[**Watch the final v6 MP4**](https://drive.google.com/file/d/1c-o5LKg11MAZOLNOLQHIXqwBn3ozUGEx/view)

[New v6 delivery folder](https://drive.google.com/drive/folders/196_t6HSE2xpNp77g8aZK86Mq9X7-gR9M) · [Preserved v5](https://drive.google.com/file/d/18kKI_5vkVOJKFUmTAEr7Tp4ZaVK6wb2M/view)

## A different shot design

1. **Oblique fingertip entry macro** — pad/wood contact becomes the opening subject.
2. **Metal-contact macro** — a closer opposite-side view of the closing jaws, then a move with the extraction.
3. **Intact-skin surface insert** — newly authored radial slit geometry, surface relief and a buried wood fragment, before the internal response.
4. **Hero-cell tracking shot** — follow a real animated cell into the cluster. Three hero cells have membrane/cytoplasm/segmented inner forms rather than only the inherited outer blobs.
5. **Elevated swelling macro** — attention follows the affected surface.
6. **Low-angle possible-emergence shot** — a focus handoff follows the fragment.
7. **Wider no-guarantee reversal** — one restrained wide anchor and the short3D `NAHI.` beat remain.
8. **Diagonal warning-detail shot** — focus moves from depth toward the affected surface without graphic panels.
9. **Professional-care removal close-up** — camera/focus follow the freed fragment while the safe ending is spoken.

Eight of the nine mid-shot camera views materially differ from v5; the no-guarantee wide anchor is deliberately preserved. These are **declared semantic camera cuts**, not accidental discontinuities or a claim that the entire film is one continuous take. The surfaces/actors continue to be evaluated at absolute time.

## New geometry and actual depth-derived focus

- Independent intact-skin macro insert:21809 surface vertices with a narrow radial opening, tissue backing and buried wood. It is not a flat photograph or a square missing-grid-cell effect.
- Three stylized hero immune-cell groups, each with a membrane, cytoplasmic core and three connected inner lobes. These are illustrative, not clinical microscopy or subtype certification.
- Geometry-depth selective focus: an actual depth render controls a separable Gaussian scene blend before display colour conversion. Blur is restrained (up to7 native pixels), with focus points tied to the photographed subject.
- The original sparse focus-kernel prototype produced visible duplicate contours; it was replaced. Surface topology/winding and backing were also corrected during proofing.
- Captions are drawn afterward at center time. The on/off regression verifies that focus changes the scene PNG while the raw caption canvas stays identical.
- Existing short real-scene shutter sampling is used only in selected action windows and is disabled around **every** declared cut.

This is an art-directed depth-focus approximation, not a calibrated optical lens or ray-traced clinical simulation. All images are rendered from geometry; no reference video/image plates or optical-flow in-betweens are used.

## Retained constraints

Same4 voice WAVs, same spoken script, same19 caption phrases/placements, same30.5s duration. No speech resynthesis or time stretch. V2–V5 sources/masters remain unchanged.

Clean frame remains binding: no HUD, chapter cards, counters, progress rails, caption pills, alert panels, generic page-turn or game/UI pings. Two brief genuine extruded-word beats remain subordinate to the action.

The8 tactile cues are rebalanced for macro perspective: closer contact/release presence, a softer surface bridge and a longer subdued hero-cell texture. The existing original arranged score is rebalanced by shot, not represented as a newly recorded soundtrack or a reference-song copy. Voice stays clear.

## Source authorities

| File | Purpose |
|---|---|
|`data/shot_plan.json`|Shot scopes/cuts, new camera rails, cell tracking and focus targets|
|`src/director.mjs`|Pure shot-camera/focus evaluator, separate from actor motion|
|`src/focus-pass.js`|Geometry-depth render and selective Gaussian scene focus|
|`data/motion.json`, `src/motion.mjs`|Retained fast actor controls and cut-aware short shutter|
|`data/design.json`|Minimal type/palette and hero-cell selection|
|`src/film.js`|Actual meshes, intact-surface insert, hero cells, scene visibility and compositing|
|`data/mix_direction.json`|Macro-perspective gain/score automation, not new voice|
|`src/sound_design.py`, `assemble.py`|Credited score/tactile generation, retained voice placement, loudness and mux|
|`data/NARRATION_LOCK.json`, `VOICE_LOCK.json`|Exact user-selected script/placement and source-voice locks|
|`src/check_motion.mjs`, `check_determinism.cjs`, `check_focus.cjs`, `gate.py`|Director, pixel-return, focus/caption and actual-master verification|

Camera positions are Y-up world coordinates. The inherited cutaway actors remain local Z-up under their conversion root. The separate intact-surface insert is an illustrative macro view; it does not pretend the earlier cutaway's front-offset presentation meshes physically lie beneath an intact surface.

## Rebuild on Linux

Node20+, Python3.11+, `tar`; disposable environment outside tracked source:

```bash
VENV=/path/to/Monarch-Studio/.runtime/wf02-python
python3 -m venv "$VENV"
"$VENV/bin/pip" install -r requirements.txt
npm ci
export FFMPEG="$("$VENV/bin/python" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"

npm test
node src/check_motion.mjs
node src/render.cjs --stills --width 540 --out build
node src/check_determinism.cjs build
node src/check_focus.cjs build
node src/render.cjs --render --out build
"$VENV/bin/python" src/assemble.py --out build
"$VENV/bin/python" src/gate.py build/KAANTA_MACRO_v6_FINAL.mp4 --out build
```

`assemble.py --audio-only` can run while frames render; use `--reuse-audio` for an already-current mix. Native rendering is substantial on a software GPU. Do not duplicate a live process or change its signature inputs. After a genuine interruption the same command resumes only matching completed chunks.

The renderer uses an allowlisted virtual local origin, not a public server or arbitrary external web content. No credentials are required/bundled. The isolated focus test exposes diagnostic handles only in its in-memory served module; it does not modify frozen production source.

The GLB remains the inherited tissue asset, not a retroactively complete v6 scene. New geometry/cameras/focus/type/edit live in JavaScript/Python. No `.blend` or Blender/Cycles claim is made.

## Publishing music credit — retain

> Original score: Monarch Studio. Instrument samples: FluidR3 GM via MIDI.js Soundfonts (Benjamin Gleitzman), CC BY3.0 US. https://github.com/gleitz/midi-js-soundfonts — https://creativecommons.org/licenses/by/3.0/us/ . Samples arranged and processed for this film.

The instrument-note recordings are credited samples; the score arrangement/mix is original and rebalanced for this edit. See `assets/music/ATTRIBUTION.md`, `SAMPLE_PROVENANCE.json` and upstream notices. Credits go in the description/caption/accompanying credits, not over the clean image. Montserrat retains its included SIL OFL1.1; other packages retain their respective licenses.

## Honest scope / delivery evidence

Stylized educational visualization; simplified scale/time/cell forms, not patient-specific advice, real surgical footage, exact reference duplication or independent clinician-reviewed simulation. The conditional-expulsion, do-not-wait, doctor/help and do-not-dig messages remain unchanged. Phrase timing is not claimed as forced word alignment.

Technical checks do not certify artistic perfection, ASMR response or retention. Actual-master metadata, encoded chapter/action review, source hashes and real upload IDs are added after completion. Final receipt is retained in Git and as a separate Drive companion, excluded from the ZIP to avoid circular hashing. User artistic acceptance remains open.
