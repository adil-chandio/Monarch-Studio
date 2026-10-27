# CHAOS 04 — how to run it

Monarch (locked v5 face / v2 body) in 3D, cut on the measured 120 BPM grid,
1332 frames, 1080 × 1920, 30 fps, our own score, our own endcard.

## What runs where
| step | where | needs |
|---|---|---|
| `tools/make_assets.py` | already done, assets committed | Pillow (local only) |
| `chaos04/score.py` | anywhere | numpy |
| `chaos04/build.py` | **Blender box** | `blender -b` or the `bpy` wheel |
| `chaos04/render.py` | **Blender box** | same |
| `chaos04/encode.py` | anywhere with ffmpeg | numpy + ffmpeg |

Assets are prebuilt PNGs (`chaos04/assets/`), so the render box needs no fonts
and no Pillow.

## On the GPU box (fresh Colab runtime)
```bash
cd /content && mkdir -p chaos_work && cd chaos_work
curl -fsSL https://raw.githubusercontent.com/adil-chandio/Monarch-Studio/refs/heads/arena/faa9119c-monarch-studio/workflows/current/payload/WF04-CHAOS04/gpu/jobs/env.sh -o env.sh
bash env.sh                       # fetch repo + choose blender binary or bpy wheel
source env.sh                      # actually: use the steps below
```

The three commands, in order:

```bash
# 0) repo into /content/chaos_work/WF04-CHAOS04 and a Blender binary/wheel
source "$PWD/env.sh"; fetch_repo; ensure_blender

# 1) gate 1 — does it build and render at all (12 frames, 360x640)
$BL "$WF/gpu/jobs/selftest.py" -- --work "$WF"

# 2) gate 2 — the full 44.4 s approval clip (360x640 -> 540x960 mp4, real audio)
bash "$WF/gpu/jobs/preview.sh"

# 3) gate 3 — production, resumable batches of ~300 frames
cd "$WF"
bash gpu/jobs/production.sh 1 300
bash gpu/jobs/production.sh 301 600
bash gpu/jobs/production.sh 601 900
bash gpu/jobs/production.sh 901 1332
# then the delivery encode + verification
python3 chaos04/encode.py --frames render/frames --audio build/score_48k.wav \
  --out build/CHAOS04_MONARCH_1080x1920.mp4
```

`render.py` skips frames that already exist and appends timings to
`render/progress.jsonl`, so a dead runtime costs one frame, not the batch.

## Local (no GPU) checks that still mean something
```bash
python3 chaos04/score.py --out build/score_48k.wav     # our 120 BPM score
python3 chaos04/encode.py --help                       # encoder/verifier
```
The timeline, the direction table, the score and the encoder are all plain
Python; only `build.py` / `render.py` / `camera.py` / `world.py` /
`character.py` / `bl.py` touch Blender.

## What must stay true
- 1332 frames, 30 fps, 1080 × 1920, H.264 crf 18–19, yuv420p, AAC 48 kHz, faststart.
- Strobes land on the 40 measured half-beat times; cuts on the 17 measured cuts.
- Monarch is the locked character: `characters/monarch/character.json`
  (`state: LOCKED`, `directive: USE, DO NOT REDESIGN`).
- None of the reference creator's footage, mask, logo, watermark or music.
