#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${MONARCH_PYTHON:-python3}"
export FFMPEG="$("$PY" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
"$PY" src/assemble.py --out build/audio --audio-only
node src/render.cjs --render --width 270 --out build/preview
"$FFMPEG" -hide_banner -loglevel error -y -i build/preview/picture.mp4 -i build/audio/mix.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 160k -t 30.5 -movflags +faststart -metadata title='KAANTA V8 REVIEW ONLY 270x480' build/preview/KAANTA_v8_REVIEW_270x480.mp4
