#!/usr/bin/env bash
# Gate 2: the approval clip. Full 1332 frames at 360x640/6 samples, encoded 540x960.
set -euo pipefail
cd "${WF:?source gpu/jobs/env.sh first}"
python3 chaos04/score.py --out build/score_48k.wav
$BL chaos04/build.py -- --out build/preview.blend --preview --width 360 --height 640 --samples 6
$BL chaos04/render.py -- --out render/preview --samples 6
python3 chaos04/encode.py --frames render/preview --audio build/score_48k.wav \
  --out build/CHAOS04_PREVIEW_540x960.mp4 --preview --width 540 --height 960 --crf 22
