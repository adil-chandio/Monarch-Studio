#!/bin/bash
# 53 s hook mux: 8-scene mute master + wide bed + 6 VO clips -> stickman_wide_hook_53s.mp4
# Chain is verbatim from VIDEO_WIDE_NOTES.md §6 (same VO/bed/limiter chain as mux_full.sh, D=53.0).
set -e
FF=$(python3 -c "import imageio_ffmpeg,sys;sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())")
B=/home/user/build
A=/home/user/assets
D=53.0
PADD=53.4

VOF="highpass=f=90,equalizer=f=250:t=q:w=1.0:g=-4.2,equalizer=f=430:t=q:w=1.4:g=-1.6,equalizer=f=3100:t=q:w=1.3:g=3.6,treble=g=2.8:f=7400,acompressor=threshold=0.045:ratio=3.6:attack=10:release=170:makeup=1.5,volume=1.92"

CLIPS=(w1 w2 w3 w4 w5 w6)
OFFS=(350 7250 13350 19550 25050 37750)

INS=()
for c in "${CLIPS[@]}"; do INS+=(-i "$A/$c.mp3"); done

FC=""
MIXIN=""
n=${#CLIPS[@]}
for i in $(seq 0 $((n-1))); do
  idx=$((i+2))
  FC+="[$idx:a]adelay=${OFFS[$i]}|${OFFS[$i]},${VOF}[v$i];"
  MIXIN+="[v$i]"
done
FC+="${MIXIN}amix=inputs=${n}:normalize=0:dropout_transition=0,asplit=2[VOa][VOb];"
FC+="[1:a]volume=0.98[BED];"
FC+="[BED][VOa]sidechaincompress=threshold=0.022:ratio=6:attack=6:release=280[DUCK];"
FC+="[DUCK][VOb]amix=inputs=2:weights=1 1:normalize=0,treble=g=3.4:f=9000,extrastereo=m=1.85,loudnorm=I=-11:TP=-1.6:LRA=9,alimiter=limit=0.63:level=disabled,apad=whole_dur=${PADD},atrim=0:${D},asetpts=N/SR/TB[AOUT]"

"$FF" -y -i "$B/wide_mute.mp4" -i "$B/wide_bed.wav" "${INS[@]}" \
  -filter_complex "$FC" -map 0:v -map "[AOUT]" \
  -c:v libx264 -preset slow -crf 24 -maxrate 1900k -bufsize 3800k \
  -profile:v high -level 4.0 -g 60 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart -threads 2 \
  -t "$D" /home/user/stickman_wide_hook_53s.mp4
echo "HOOK MUX DONE"
