# KAANTA · Precision Cut v5

**WF-02 · native1080×1920 · 30fps · 30.5s**

A faster, more decisive reference-informed revision of the clean v4—not a global speed-up and not a return to graphic clutter.

[**Watch the final v5 MP4**](https://drive.google.com/file/d/18kKI_5vkVOJKFUmTAEr7Tp4ZaVK6wb2M/view)

[New v5 delivery folder](https://drive.google.com/drive/folders/1CmmK6Zc5QaPmsRXiP_EMXO6U9G-ikCWb) · [Preserved v4](https://drive.google.com/file/d/1Aw7InbA91uoiL2XHBTqPB_7J3vHQvolq/view)

## What changed measurably

| Authored action | V4 | V5 |
|---|---:|---:|
|Surface approach|1.02s|0.38s|
|Surface jaw close|0.41s|0.17s|
|Surface pull|1.17s|0.42s|
|Deep approach|0.63s|0.34s|
|Deep jaw close|0.35s|0.16s|
|Deep pull|1.97s|0.72s|
|Swelling rise|2.75s|0.95s|
|Possible outward movement|2.87s|0.82s|

Camera repositioning now uses eleven **0.40–0.58s move/settle windows**, mean0.482s, instead of whole-shot drift. Smooth acceleration and zero endpoint velocity/acceleration are preserved. Pauses remain intentional: “fast” means decisive actions, not frantic movement throughout every sentence.

The fixed Urdu narration, caption reading copy, placements, total duration and safety ending remain unchanged. See `data/MOTION_COMPARISON.json` and `MOTION_QA.json` for actual comparisons, not an unsupported percentage-quality claim.

## Detail / image treatment

- Localized generic fingertip ridge/pore detail, rather than a strong fingerprint pattern over the whole finger.
- Cellular epidermal relief and subtler fibrous dermal texture.
- Directional wood-grain mapping and brushed-metal roughness.
- Richer blue/warm separation and shaped key/rim lighting.
- Clean v4 composition preserved: no HUD, chapter cards, counters, caption pills, warning badges, page-turns or UI pings.
- Two real extruded-word beats remain, with shorter restrained entrances/exits.

### Short scene-only shutter

During bounded fast-motion windows, each output frame combines **three actual3D scene evaluations** with25/50/25% weights across1/150s exposure. Slow/held frames use one evaluation. The different scenes are never blended across the7s cut. Captions are drawn once at the center time, so they remain sharp.

This is renderer-time temporal sampling, **not optical-flow interpolation or duplicated v4 frames**. It does not turn30fps into60fps. Chunk receipts record output frames, shutter-frame count and total scene evaluations independently. An earlier2-sample trial showed more obvious double contours; the selected version uses a shorter center-weighted exposure.

## Sound

Eight story-linked textures stay—not more alerts. Steel closures are shorter/drier and wood-release cues include quiet friction leading into a non-tonal transient. Audio anchors come from the same motion cues; release pre-roll is explicit. The existing original piano/cello/string arrangement is rephrased around the quicker action, while the no-guarantee line retains breathing space.

`SOUND_DESIGN_REPORT.json` records actual source-effect transient times and mix hierarchy. These are pre-AAC measurements, not claims of independent listening certification, universal ASMR response or audience retention.

## Editable authorities

- `data/motion.json`: move/settle camera keys, action timings, short shutter settings.
- `data/design.json`: palette, type exposure and clean-caption treatment.
- `data/timeline.json`: retained voice/caption timing and SFX anchor list.
- `src/motion.mjs`: stateless C2 actor/camera evaluator.
- `src/film.js`: real geometry, materials, typography, renderer-time shutter and sharp-caption compositor.
- `src/render.cjs`: native frame capture, resumable chunks and scene-evaluation receipts.
- `src/sound_design.py`: note arrangement, tactile texture construction, pre-roll/transient envelopes and ducking.
- `src/assemble.py`: retained voice placement, cue resolution, normalization and mux.
- `src/check_motion.mjs`, `check_determinism.cjs`, `gate.py`: numerical, pixel-return and actual-master gates.

The earlier tissue GLB and voice sources are explicitly inherited. The full v5 scene/rig/cameras/type/material treatment lives in JavaScript, not retroactively inside that original GLB. No `.blend`, Blender/Cycles rendering or clinical tissue simulation is claimed.

## Rebuild on Linux

Node20+, Python3.11+, `tar`. Keep dependency environments/build outputs outside tracked source.

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
node src/render.cjs --render --out build
"$VENV/bin/python" src/assemble.py --out build
"$VENV/bin/python" src/gate.py build/KAANTA_PRECISION_v5_FINAL.mp4 --out build
```

Audio can be prepared with `assemble.py --audio-only`; use `--reuse-audio` once its mix is current. Rendering is offline at an allowlisted virtual browser origin, not a public server. Do not edit visual signature inputs or launch a duplicate while the renderer is alive. The same command resumes completed matching chunks after an actual interruption.

The source kit includes fixed narration and the selected instrument notes. Captions are phrase-timed, not claimed word-level forced alignment. The anatomy is a stylized educational visualization with simplified scale/time; medical caveats are retained. Technical gates do not certify artistic perfection.

## Publishing credit — retain it

> Original score: Monarch Studio. Instrument samples: FluidR3 GM via MIDI.js Soundfonts (Benjamin Gleitzman), CC BY3.0 US. https://github.com/gleitz/midi-js-soundfonts — https://creativecommons.org/licenses/by/3.0/us/ . Samples arranged and processed for this film.

The arrangement/performance/mix is original; the instrument-note recordings are credited samples, not claimed as newly recorded or attribution-free. See `assets/music/ATTRIBUTION.md` and `SAMPLE_PROVENANCE.json`. No reference song, reference narration or original reference frames are used in the output. Credits accompany the video/source rather than covering the clean frame.

Montserrat retains its included SIL OFL1.1 notice. Three.js, Playwright, Chromium and fontTools retain their own licenses.

Actual master QA, encoded sample review, hashes and real Drive IDs are added after completion. The final delivery receipt is in Git and separately on Drive; it is excluded from the source ZIP to avoid circular self-hashing. Previous versions are preserved.
