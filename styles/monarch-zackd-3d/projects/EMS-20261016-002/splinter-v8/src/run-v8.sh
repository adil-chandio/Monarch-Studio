#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${MONARCH_PYTHON:-python3}"
export FFMPEG="$("$PY" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
npm test
node src/check_motion.mjs
node src/check_upgrade.mjs
node src/render.cjs --stills --width 540 --times 9.3 --out build/proof
node src/check_determinism.cjs build/proof
node src/check_focus.cjs build/proof
node src/check_organic.cjs build/proof
for report in DETERMINISM_REPORT FOCUS_QA ORGANIC_QA; do cp "build/proof/$report.json" "data/$report.json"; done
MONARCH_PYTHON="$PY" bash src/preview-v8.sh
"$PY" src/check_preview.py
cp build/preview/PREVIEW_QA.json data/PREVIEW_QA.json
"$PY" src/assemble.py --out build/native --audio-only
node src/render.cjs --render --out build/native
"$PY" src/assemble.py --out build/native --reuse-audio
"$PY" src/gate.py build/native/KAANTA_CRAFT_v8_FINAL.mp4 --out build/native
