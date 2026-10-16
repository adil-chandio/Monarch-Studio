# KAANTA · Motion Edition v3

**Monarch Studio / WF-02 · 30.5 seconds · native 1080 × 1920 · 30 fps**

A motion-and-sound enhancement of the **user-liked KAANTA v2**, not a replacement of its source or master. The topic, Urdu narration, Roman Urdu-English reading copy, visual identity and medical caveats are retained.

[**Watch the final v3 MP4**](https://drive.google.com/file/d/1Wl8S1M6jT3SNU6vEHJt9Kw3sePz0TH-i/view)

[New v3 delivery folder](https://drive.google.com/drive/folders/1mK5uWa-34OjxYhvrujG0E5Odb5s6Nu3z) · [Preserved v2](https://drive.google.com/file/d/10YyHXoz1avbHTrSzOW7xWZwiZUvTEMOT/view)

## What is actually enhanced

1. **Continuous camera rails.** Six internal camera resets become a C2 quintic-Hermite path with shared velocities and accelerations. The anatomy shot can orbit, approach, reframe and pull out without teleporting at chapter boundaries.
2. **New closing forceps rig.** Joined beveled branches close around the measured wood-cap width. Grip happens before pulling; the wood and tool remain on the same extraction axis.
3. **Authored secondary motion.** Fingertip compression, a restrained resistance/release beat, eased swelling and continuous post-extraction movement. These are illustrative animation controls, not tissue mechanics.
4. **Earlier, clearer cell migration.** Individual curved paths and controlled settling bring all 32 cells in by 10.69s, during the spoken gathering sentence—not after it.
5. **A reference-informed turn-over transition.** The single hand-to-cutaway scene change at 7s is covered by a 0.6s perspective card turn. Each source frame is independently animated; no still-image plates or optical-flow frames are introduced.
6. **23 original sound cues instead of 11.** Metal contacts, release/strain details, stereo air sweeps, cell/fluid accents and restrained caution/resolve tones, with a new harmonic texture. Grip/release cues read the same motion controls; the transition sweep peaks at the transition center.
7. **Native 30 fps instead of 24 fps.** 915 separately rendered frames, not a 24fps export with duplicated or generated in-between frames.
8. **Refined graphics.** Smoother subtitle/callout entrances and exits, improved phrase timings, proper variable-font weight selection and stable full-frame canvas rasterization.

The voice WAVs and raw placed voice timeline are byte-identical to v2. Narration is not regenerated, pitch-shifted or time-stretched. The overall mix targets −16 LUFS so the upgrade is not simply a louder voice.

## Editable controls and source

| File | Role |
|---|---|
| `data/motion.json` | Camera keyframes, grip/pull/release timings, cell/swelling cues |
| `src/motion.mjs` | Pure, deterministic C2 controller; no accumulated transforms |
| `data/timeline.json` | Spoken clips, narrative chapter markers, captions, sound cue list |
| `data/postfx.json` | Turn-over duration/perspective; center follows `scene_change` |
| `src/film.js` | Actual 3D geometry, materials, new tool rig, scene composition and graphics |
| `src/render.cjs` | Offline native-frame lossless-PNG capture and resumable encoding |
| `src/transition.py` | Recompose only the transition-containing chunk, with a cache receipt |
| `src/sound_design.py` | Newly synthesized original stereo sound design / ducking |
| `src/assemble.py` | Preserved voice placement, shared-cue timing, mix normalization and mux |
| `src/check_motion.mjs` | Numerical camera continuity / actor timing / cue checks |
| `src/check_determinism.cjs` | Full-frame repeated/out-of-order image regression |
| `src/gate.py` | Decode and measure the actual delivered master |
| `assets/models/cutaway.glb` | Original inherited WF-02 tissue asset, with its older animation preserved |
| `assets/vo/` | Four unchanged v2 Urdu voice clips |

Camera keys use `[x, y, z, lookX, lookY, lookZ, fovDegrees]` in the scene's Y-up world. The inherited anatomy's actor coordinates remain local Z-up, under its conversion root. Keep these spaces distinct when editing.

`motion.json` is the authority for grip/release action timing. The assembler resolves corresponding SFX from these cues. The dive-sound peak follows the post transition center. Other sounds are editorially placed in `timeline.json`. If changing narration duration, re-time the complete edit rather than stretching the voice blindly.

The inherited GLB can be imported into Blender. **The new v3 tool rig, camera rail and final animation are implemented in JavaScript**, not embedded retroactively in that GLB or supplied as a `.blend` project. No Blender/Cycles render is claimed.

## Rebuild on Linux

Requirements: Node 20+, Python 3.11+, `tar`. Native portrait rendering on a two-core software GPU takes substantial time; completed chunks are resumable.

```bash
# Install Python dependencies in a disposable directory, not tracked source.
VENV=/path/to/Monarch-Studio/.runtime/wf02-python
python3 -m venv "$VENV"
"$VENV/bin/pip" install -r requirements.txt
npm ci
export FFMPEG="$("$VENV/bin/python" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"

npm test
node src/check_motion.mjs
node src/render.cjs --stills --width 540 --out build
node src/check_determinism.cjs build

# Native 1080x1920 / 30 fps. Do not edit visual source while it is running.
node src/render.cjs --render --out build

# The same command resumes valid, completed chunks after an actual stop.
# Never start a duplicate render while the previous process is still alive.

# Assemble voice + new sound. Automatically applies/reuses the turn-over
# post chunk and concatenates the polished picture before muxing.
"$VENV/bin/python" src/assemble.py --out build
"$VENV/bin/python" src/gate.py build/KAANTA_WF02_MOTION_v3_FINAL.mp4 --out build
```

`assemble.py --audio-only --out build` may run while frames render; use `--reuse-audio` for the final mux if the mix is already current. `transition.py --prepare-only --out build` can prepare the turnover after `chunk-00180.mp4` completes. It reuses its result only if the source/config/code fingerprint matches.

The offline browser does not expose a web server or fetch external scene content. Requests are fulfilled only from allowlisted project/Three.js paths. Dependencies are pinned; no credentials are stored or required.

## QA, provenance and limits

- `data/MOTION_QA.json`: 9 numerical motion/control checks.
- `data/DETERMINISM_REPORT.json`: strict **full-frame** pixel equality when revisiting times.
- `data/DETERMINISM_COLD_DIAGNOSTIC.json`: retained earlier experiment; the small brand-mark cold-raster difference was subsequently fixed by explicit stable 2D canvas contexts.
- `data/VOICE_LOCK.json`: retained voice hashes.
- `data/SOUND_DESIGN_REPORT.json`, `AUDIO_REPORT.json`, `SOUND_COMPARISON.json`: actual sound sources and measurements.
- `data/POSTFX_REPORT.json`, `RENDER_RECEIPTS.json`, `QUALITY_REPORT.json`: added from the actual encoded master.
- `data/SOURCES.json` and `docs/SCRIPT_AND_PRODUCTION.md`: exact lineage, original Urdu text, medical references and limitations.
- Final `DELIVERY_RECEIPT.json` is stored in Git and as a separate Drive companion; it is omitted from the source ZIP to avoid circular self-hashing.

This is a **stylized educational 3D explainer**, not a frame-for-frame copy, real surgical footage or a clinically validated simulation. Scale/time are simplified, expulsion is conditional, and the warning/professional-care ending is preserved. Phrase timing is refined against the retained clips, not represented as word-level forced alignment. Technical checks are not a claim of artistic perfection or independent pronunciation/clinician certification.

The user-supplied reference audio/video is not copied into the film. The earlier tissue asset, finger base, voice clips and style are explicitly inherited, not claimed as newly created from scratch. The source GLB and original voice files are provided for reproducibility.

Montserrat retains its SIL Open Font License 1.1; its notice and license are included in `assets/fonts/`. Three.js, Playwright and Chromium retain their own package licenses.
