# KAANTA · WF-02 · v2

A **30.5-second, native 1080 × 1920, 24 fps** animated anatomical explainer with Urdu narration and Roman Urdu-English captions.

The main delivery is [KAANTA_WF02_1080x1920_FINAL.mp4](https://drive.google.com/file/d/10YyHXoz1avbHTrSzOW7xWZwiZUvTEMOT/view) in the [version's Drive folder](https://drive.google.com/drive/folders/1SqX_S44eVowdTAyBVzAFerYUYFJd6NtF). Large rendered outputs stay on Drive, not in the Git source tree.

## What is in this source

- `src/film.js`: new procedural fingertip, recovered cutaway animation, material/lighting treatment, cameras and graphics.
- `src/render.cjs`: offline native-frame capture with resumable, independently encoded chunks.
- `src/assemble.py`: voice placement, original synthesized sound design, two-pass loudness normalization, SRT and MP4 mux.
- `src/gate.py`: actual-master decode, frame/timing/loudness checks and encoded-video QC contact sheet.
- `src/check_determinism.cjs`: absolute-time rendering regression test.
- `assets/models/cutaway.glb`: recovered earlier WF-02 model, **not claimed as newly modelled in this task**.
- `assets/vo/`: the four user-auditioned Urdu narration WAVs; required to reproduce this exact voice.
- `assets/fonts/`: Montserrat variable font, SIL OFL 1.1 notice and license.
- `data/timeline.json`: narration, shots, captions and SFX timing authority.
- `docs/SCRIPT_AND_PRODUCTION.md`: easy Urdu-English script, source lineage, medical sources and scope.
- `data/*REPORT*.json`: measured production evidence.
- `data/DELIVERY_RECEIPT.json`: real Drive IDs and hashes in Git and as a separate Drive companion file. It is intentionally excluded from the ZIP to avoid a self-referential archive hash; the source-file manifest and actual master identity are included.

This is a **stylized educational 3D visualization**, not clinical footage, a physiological simulation, a Blender-rendered movie, or an exact copy of the supplied reference. No source-video frames, source audio, AI still plates, or copied creator branding are used in the film. The microscopic sizes and timing are intentionally simplified.

## Rebuild on Linux

Requirements: Node 20+; Python 3.11+; `tar`; enough disk/RAM for the Chromium renderer. The software-GPU fallback works without a physical GPU. On a two-core CPU, native portrait rendering is a substantial operation; use the resumable chunks rather than restarting.

Install Python dependencies in a disposable environment **outside the tracked project**, for example the repository's ignored `.runtime/` directory:

```bash
# From this project directory; choose any disposable path for VENV.
VENV=/path/to/Monarch-Studio/.runtime/wf02-python
python3 -m venv "$VENV"
"$VENV/bin/pip" install -r requirements.txt
npm ci

export FFMPEG="$("$VENV/bin/python" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"

# Static source contracts and useful proof stills.
npm test
node src/render.cjs --stills --width 540 --out build

# Native 1080x1920 picture, 732 individually rendered frames.
node src/render.cjs --render --out build

# If interrupted, run the SAME command. Valid completed chunk receipts are
# reused only if the source signature and dimensions still match.

"$VENV/bin/python" src/assemble.py --out build
"$VENV/bin/python" src/gate.py build/KAANTA_WF02_1080x1920_FINAL.mp4 --out build
node src/check_determinism.cjs build
```

`--audio-only` can assemble the audio while frames render:

```bash
"$VENV/bin/python" src/assemble.py --audio-only --out build
# After picture.mp4 finishes:
"$VENV/bin/python" src/assemble.py --reuse-audio --out build
```

The renderer uses a virtual browser origin whose requests are intercepted and fulfilled from allowlisted project / Three.js files. It **does not start a public server or fetch untrusted web pages**. NSS/NSPR libraries for minimal Linux systems are extracted into the build directory from the pinned Chromium package. No credentials are required or bundled.

## Editing

- Keep footage, captions and spoken claims consistent when editing `data/timeline.json`.
- Do not change render source mid-run. Changed signatures invalidate earlier chunks.
- Each rendered frame is evaluated from an absolute timeline time. Never multiply the splinter scale incrementally: use its assigned absolute scale.
- Cells use instancing, but their individual transforms still come from the animation clip. They are not camera-zoomed still images.
- Swelling uses position **and generated normal-delta morphs**; removing the normal correction flattens the dome's lighting.
- The source GLB can be imported into Blender. It does not include this version's new fingertip, final cameras, caption system or edit; those are constructed in `film.js`.

## Known boundaries / quality evidence

- Medical content has been checked against the linked general educational sources, **not reviewed by a clinician**.
- Captions are phrase-timed; no claim of word-level forced alignment is made.
- Voice audition was selected by the user. Automated checks measure speech assets and output audio; they do not certify every Urdu pronunciation by ear.
- The first full-frame determinism probe saw a very small brand-mark rasterization difference (0.052% of pixels exceeding an 8/255 difference at 270px width). The anatomy/caption region was bit-identical on repeated absolute-time renders. The original diagnostic is retained in `data/DETERMINISM_INITIAL_FULLFRAME.json`.
- GLB validation produced zero errors / warnings and 15 informational unused-UV notices, recorded without suppressing them.

## Provenance and licenses

The model originates from the user's existing **SPLINTER — Monarch 3D** Drive project. Exact source IDs and hashes are in `data/SOURCES.json`. The supplied reference video is used for topic/sequence study only and is not redistributed.

Montserrat: Copyright 2011 The Montserrat Project Authors (Julieta Ulanovsky), SIL Open Font License 1.1. Its license is included. Three.js, Playwright and Chromium retain their respective third-party licenses and are installed from pinned packages, not relicensed as Monarch assets.

This WF-02 registration reflects the live user-named **Zack d 3d animation** folder. It does not alter or overwrite the separately preserved **Powerful Personality** legacy WF-02 snapshot.
