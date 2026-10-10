#!/usr/bin/env bash
# encode_window.sh — THE WINDOW v1: concat the 4 crf-14 segments (stream copy) → single-input final encode with the mix.
# usage: bash src/encode_window.sh [crf]   (default 21; grain lesson: ≤19 codes the grain and doubles the size)
set -euo pipefail
CRF="${1:-21}"
B=/home/user/build/wf03_window
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
cd "$B"
for s in a b c d; do [ -s "seg_$s.mp4" ] || { echo "missing seg_$s.mp4"; exit 2; }; done
printf "file 'seg_a.mp4'\nfile 'seg_b.mp4'\nfile 'seg_c.mp4'\nfile 'seg_d.mp4'\n" > concat.txt
"$FF" -y -loglevel error -f concat -safe 0 -i concat.txt -c copy master_concat.mp4
"$FF" -i master_concat.mp4 2>&1 | grep -E "Duration" || true
# final: one decoder, one encoder, audio from the mix (−16.5 LUFS wav) — no filter graph beyond fps/format
"$FF" -y -loglevel error -stats -i master_concat.mp4 -i mix.wav -map 0:v:0 -map 1:a:0 \
  -vf "fps=24,format=yuv420p" -r 24 -c:v libx264 -preset medium -crf "$CRF" -profile:v high -level 4.1 -g 48 -bf 3 \
  -x264-params "aq-mode=3:aq-strength=1.1:deblock=-1,-1" -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart -shortest \
  THE_WINDOW_v1.mp4
ls -la THE_WINDOW_v1.mp4
"$FF" -i THE_WINDOW_v1.mp4 2>&1 | grep -E "Duration|Stream" || true
md5sum THE_WINDOW_v1.mp4
