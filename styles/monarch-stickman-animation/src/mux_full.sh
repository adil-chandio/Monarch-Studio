#!/bin/bash
# Full-episode mux: 34-scene mute master + bed + 16 VO clips -> deliverable.
set -e
FF=$(python3 -c "import imageio_ffmpeg,sys;sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())")
B=/home/user/build
A=/home/user/assets
D=263.5
PADD=263.9

VOF="highpass=f=90,equalizer=f=250:t=q:w=1.0:g=-4.2,equalizer=f=430:t=q:w=1.4:g=-1.6,equalizer=f=3100:t=q:w=1.3:g=3.6,treble=g=2.8:f=7400,acompressor=threshold=0.045:ratio=3.6:attack=10:release=170:makeup=1.5,volume=1.92"

# VO clip list and start offsets (seconds)
CLIPS=(w1 w2 w3 w4 w5 w6 b1 b2 b3 b4 b5 b6 b7 b8 b9 b10)
OFFS=(350 7250 13350 19550 25050 37750 53450 74110 96700 117470 135730 155190 178490 195890 215920 237940)

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

"$FF" -y -i "$B/full_mute.mp4" -i "$B/full_bed.wav" "${INS[@]}" \
  -filter_complex "$FC" -map 0:v -map "[AOUT]" \
  -c:v libx264 -preset slow -crf 24 -maxrate 1900k -bufsize 3800k \
  -profile:v high -level 4.0 -g 60 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart -threads 2 \
  -t "$D" /home/user/stickman_wide_episode_full.mp4
echo "MUX DONE"
