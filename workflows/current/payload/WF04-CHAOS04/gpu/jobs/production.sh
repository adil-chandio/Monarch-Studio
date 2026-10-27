#!/usr/bin/env bash
# Gate 3: 1080x1920 in resumable batches, then the delivery encode.
#   source gpu/jobs/env.sh && fetch_repo && ensure_blender
#   bash gpu/jobs/production.sh 1 300
set -euo pipefail
cd "${WF:?source gpu/jobs/env.sh first}"
START="${1:-1}"; END="${2:-1332}"; SAMPLES="${SAMPLES:-20}"
python3 chaos04/score.py --out build/score_48k.wav
if [ ! -f build/chaos04.blend ]; then
  $BL chaos04/build.py -- --out build/chaos04.blend --width 1080 --height 1920 \
    --samples "$SAMPLES" --device GPU
fi
$BL chaos04/render.py -- --out render/frames --start "$START" --end "$END" \
  --samples "$SAMPLES" --device AUTO
echo "[production] batch $START-$END done; rerun with the next range"
