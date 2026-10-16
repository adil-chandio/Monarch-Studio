#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${MONARCH_PYTHON:-python3}"
export FFMPEG="$("$PY" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
cd "$ROOT"
npm test
node src/check_motion.mjs
node src/render.cjs --stills --width 540 --times 9.3 --out build
node src/check_determinism.cjs build
node src/check_focus.cjs build
node src/check_organic.cjs build
for report in DETERMINISM_REPORT FOCUS_QA ORGANIC_QA; do cp "build/$report.json" "data/$report.json"; done
"$PY" src/assemble.py --out build --audio-only
node src/render.cjs --render --out build
"$PY" src/assemble.py --out build --reuse-audio
"$PY" src/gate.py build/KAANTA_ORGANIC_v7_FINAL.mp4 --out build
