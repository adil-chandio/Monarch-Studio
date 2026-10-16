# KAANTA · Cinema Cut v4

**WF-02 · native 1080 × 1920 · 30 fps · 30.5 seconds**

A subtractive redesign responding to the user's explicit feedback that unnecessary additions made the earlier version feel cluttered/cheap. This is **not another effects-heavy upgrade**. Earlier v2/v3 masters and source remain unchanged.

[**Watch the final v4 MP4**](https://drive.google.com/file/d/1Aw7InbA91uoiL2XHBTqPB_7J3vHQvolq/view)

[Cinema Cut delivery folder](https://drive.google.com/drive/folders/1Z2lk4C01uKThecQyUhbcYxINtUox34Q0)

## Direction

- Main action first: no chapter headers, top brand frame, countdown/progress rail, warning badges, caption pills, callout arrows or page-turn effect.
- Plain readable Roman Urdu captions; only **two** brief pieces of genuine extruded 3D type: `KAANTA` and `NAHI.`. They are lit meshes with separate face/side materials, not flat text with a fake shadow.
- Restrained slate-blue background, warm anatomical palette, palmar micro-ridges, refined cell/adipose surfaces and cleaner cut-face shading. Irrelevant duct detail and the large translucent pocket are removed from view.
- Motivated C2 camera rails, a measured closing jaw rig, monotonic tension/release motion instead of spring wobble, and a single clean scene change at 7s.
- **Eight** soft tactile textures instead of the previous 23-cue treatment. No game/UI pings, warning alarms or celebratory chimes.
- A new original short piano/cello/string arrangement, using credited sampled instrument notes. The music builds toward discovery and movement, steps back at “har baar nahi”, then resolves gently. Voice remains clear and centered.

The goal is premium, restrained and engaging. Artistic quality, an ASMR response and audience retention are **not guaranteed by technical measurements**.

## Editable source

| File | Authority |
|---|---|
| `data/motion.json` | Camera position/look/lens keys, object timing and grip/release cues |
| `data/design.json` | Palette, two 3D typography beats, caption treatment, reduced scene population |
| `data/timeline.json` | Original narration placement, chapter metadata, phrase captions and tactile-cue list |
| `src/film.js` | Actual 3D scene/rigs, revised materials/surfaces, glyph meshes and minimal subtitle compositor |
| `src/motion.mjs` | Stateless C2 motion controller |
| `src/render.cjs` | Native-pixel offline rendering, lossless PNG capture, resumable H.264 chunks |
| `src/sound_design.py` | Original score arrangement (`CHORDS`, `BASS`, `PIANO`), sample shaping, tactile textures and ducking |
| `src/assemble.py` | Retained voice placement, cue resolution, loudness normalization, subtitles and final mux |
| `src/build_typeface.py` | Included OFL Montserrat → true Three.js glyph outlines, weight600 subset |
| `src/check_motion.mjs` | Camera continuity, actor/cue timing and finite-frame checks |
| `src/check_determinism.cjs` | Full-frame repeated/out-of-order checks plus actual3D-type geometry report |
| `src/gate.py` | Decode/inspect actual-master metadata, continuity, visibility, sound priority, clutter and provenance gates |

The 9 timeline chapters are **edit metadata**, not 9 visible title cards. Camera coordinates are Y-up world space. The inherited anatomy's actors use local Z-up under the GLB conversion root.

The existing tissue asset is retained with attribution; the v4 look, geometry replacements, render-time animation and typography are implemented in the source code. The GLB does not retroactively contain the complete v4 cameras, type, new forceps or final edit. **No `.blend`, Blender/Cycles render or clinical tissue simulation is claimed.**

## Rebuild on Linux

Node20+, Python3.11+ and `tar` are required. Software-GPU native portrait rendering is substantial; use the chunk receipts rather than duplicating an active process.

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

# 915 separately rendered native1080x1920 frames; no optical-flow conversion.
node src/render.cjs --render --out build
"$VENV/bin/python" src/assemble.py --out build
"$VENV/bin/python" src/gate.py build/KAANTA_CINEMA_v4_FINAL.mp4 --out build
```

For parallel audio work, `assemble.py --audio-only --out build` produces the mix and separate voice/music/tactile stems. Use `--reuse-audio` when muxing an already-current mix. No page-turn post step exists in this version.

Do not edit visual signature inputs during a render. If genuinely interrupted, the same command reuses completed chunks only when source/size receipts match. The offline browser serves allowlisted local project/Three.js files at a virtual origin; no public server or credentials are required.

To change the 3D words, edit the glyph subset in `build_typeface.py`, regenerate the included typeface, update `design.json`, and re-test framing. Text styling should remain subordinate to the scene.

## Music credit for publishing

The musical arrangement is original; the instrument-note recordings are **FluidR3 GM**, credited under **CC BY3.0 US** as documented by the upstream MIDI.js Soundfonts repository. They are not claimed as newly recorded from scratch or as unconditionally attribution-free.

**Retain this credit in the published video's description/caption or accompanying credits:**

> Original score: Monarch Studio. Instrument samples: FluidR3 GM via MIDI.js Soundfonts (Benjamin Gleitzman), CC BY3.0 US. https://github.com/gleitz/midi-js-soundfonts — https://creativecommons.org/licenses/by/3.0/us/ . Samples arranged and processed for this film.

See `assets/music/ATTRIBUTION.md`, `SAMPLE_PROVENANCE.json`, upstream README and conversion license. Credits are in the delivery description/source/notes, **not overlaid on the picture**. No reference music, reference narration or source-video frames are reused in the film.

Montserrat retains its included SIL OFL1.1 notice/license. Three.js, Playwright, Chromium and fontTools retain their respective third-party licenses.

## QA and scope

Actual encoded-master evidence is stored in `data/QUALITY_REPORT.json`, `MASTER_IDENTITY.json`, `RENDER_RECEIPTS.json` and the encoded-frame contact sheet after final assembly. Motion/type regressions, voice locks, source lineage and music/sample attribution are included. Final Drive IDs/hashes are in `DELIVERY_RECEIPT.json` in Git and as a separate companion on Drive; it is excluded from the ZIP to avoid circular hashing.

This is a stylized educational visualization with simplified scale/time, not real surgery, patient-specific advice or an independently clinician-reviewed simulation. Conditional expulsion, “do not wait”, professional help and “do not dig” remain in the original voice/captions. Phrase timing is not represented as word-level forced alignment. Source narration clips are preserved, not newly synthesized or time-stretched.
