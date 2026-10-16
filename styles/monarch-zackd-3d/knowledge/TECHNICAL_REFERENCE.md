# Technical architecture and exact reference points

The current executable reference lives at `projects/EMS-20261016-002/splinter-v8`. Preserve earlier versions; the implementation is readable source rather than a vague prompt pack.

| Layer | Current authority | Responsibility / caveat |
|---|---|---|
|Scene/meshes/materials|`src/film.js`|Three.js geometry, inherited GLB, new skin/tools/type/cells/fibres, lighting, visibility and compositor; no Blender/Cycles claim|
|Actor motion|`src/motion.mjs`, `data/motion.json`|absolute-time C2 controls, contact/pull/tension, cell/debris paths; simplified illustration|
|Photography|`src/director.mjs`, `data/shot_plan.json`|shot-local camera/focus, tracking and semantic cuts; Y-up camera vs local Z-up actors|
|Depth focus|`src/focus-pass.js`|geometry-depth separable Gaussian before output transform; approximate optics, restrained radius|
|Native capture|`src/render.cjs`|allowlisted virtual local origin, pinned Chromium/Playwright/Three, native lossless composite capture, resumable chunk signatures|
|Sound|`src/sound_design.py`, `data/mix_direction.json`|eight restrained cues, credited piano/cello/string-note arrangement, shared anchors, narrative gain automation|
|Assembly|`src/assemble.py`, `data/timeline.json`|fixed voice placement, phrase SRT, two-pass normalization, AAC mux/faststart and identity hashes|
|Current proofs|`check_motion.mjs`, `check_upgrade.mjs`, `check_determinism.cjs`, `check_focus.cjs`, `check_organic.cjs`, `check_preview.py`|director/voice lock, actual V7 comparison, full-frame returns, focus and feature A/B, complete low-res decode|
|Native gate|`src/gate.py`|34 case-specific actual-master checks; not artistic/clinical certification|
|Rebuild|`src/run-v8.sh`, `src/preview-v8.sh`|source proofs -> full review -> native picture/audio/gates; significant software-GPU runtime|

## Pinned toolchain and restore

Read the case-study package/lock and requirements, do not rely on an ephemeral environment surviving. Node20+; Three0.170.0, playwright-core1.51.1, @sparticuz/chromium133.0.0; Python3.11+ with pinned NumPy2.4.6, Pillow12.3.0, imageio-ffmpeg0.6.0, PyAV16.0.1 and fonttools4.60.1; `tar`. Chromium bundled runtime libraries are recreated by the renderer. No credentials are bundled. Arena's browser is not localhost; if exposing a preview server use0.0.0.0 and a compatible host/proxy. The offline renderer itself uses intercepted allowlisted URLs, not a public dev server.

```bash
python3 tools/continuity.py resume
python3 tools/wf02.py audit
python3 tools/studio.py hydrate wf02
# Or fork a current task; never edit preserved delivered source in place.
cd <working-copy-of-splinter-v8>
python3 -m venv <disposable-venv>
<disposable-venv>/bin/pip install -r requirements.txt
npm ci
MONARCH_PYTHON=<absolute-venv>/bin/python bash src/run-v8.sh
```

Repository tests should use a dependency-equipped interpreter. A system-Python `numpy` import failure in WF03's unrelated --help test was an environment issue; rerunning with the restored venv passed10/10. Do not rewrite working WF02 rendering to mask an unrelated missing package.

## Case-specific measured controls

- Native V8:1080×1920,30fps,30.5s,915frames.1101 colour-scene evaluations;93 shutter frames;775 depth-focus frames. These are not mandatory counts/duration for every new topic.
- Selected shutter:3 center-weighted scene evaluations, short exposure, no cross-cut blending; output caption canvas evaluated once at center time.
- Surface insert:21809vertices (inherited V6). Three hero cells with segmented inner forms; V7 independent membranes1617vertices each, bounded travelling folds. V8 dermal micro-bundles:36merged curves/8100vertices.
- V5 faster actions:surface approach1.02→0.38s,close0.41→0.17s,pull1.17→0.42s; deep approach0.63→0.34s,close0.35→0.16s,pull1.97→0.72s. Camera windows0.40–0.58s. Later revisions retain measured contact anchors rather than global speed-up.
- Source/native signatures include actual source/data/assets, render width and capture mode. A different preview width has a different signature and is not a native-final receipt.
- V8 encoded AAC:-16.03LUFS,-2.56dBTP; voice priority and dynamic breathing space measured. Not an independent ear/ASMR certificate.

## Licensing and provenance

Keep GLB/reference origins in SOURCES.json; original model is inherited. Montserrat retains SIL OFL1.1. FluidR3 instrument notes via MIDI.js Soundfonts retain CC BY3.0 US and source/provenance notices. Preserve upstream licenses and `assets/music/ATTRIBUTION.md` in every source kit and publishing companion. No reference audio/image plates are used.
