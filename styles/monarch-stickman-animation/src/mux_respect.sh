#!/bin/bash
# 90 s IZZAT short: mute master + ASMR bed + 9 fitted VO clips -> shade_respect_90s.mp4 (chain = locked POWER chain)
# Chain = v9 vertical chain (MONARCH_SKILL_MOTION_EDIT.md §6: bed 0.60, duck .024/5/6/260)
# with the two later safety rules folded in (episode ledger): TP -1.6 + alimiter 0.63
# because AAC overshoots the PCM peak by ~2.4 dB, and apad ALWAYS bounded.
# Optional overrides:  I=<lufs target>  LIM=<limiter ceiling>  XS=<extrastereo m>  OUT=<path>
# Locked by measurement (see VIDEO_POWER_NOTES.md §5): BEDV .70, DRV 1.25 into alimiter .74, extrastereo 2.4
# -> -11.7 LUFS, decoded peak -1.5 dBFS, L/R corr .75, side/mid .38 (v9: -11.7 / .7547 / .374).
set -e
FF=$(python3 -c "import imageio_ffmpeg,sys;sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())")
B=/home/user/build
A=/home/user/assets
D=90.0
PADD=90.4
I=${I:--11}
LIM=${LIM:-0.71}       # 0.74 in POWER; voice-01 sibilants flat-topped the limiter and AAC overshot to 0 dBFS (ledger 56: de-esser + 0.71)
XS=${XS:-1.7}         # 2.4 in POWER; 25 % of this cut is bed-only and extrastereo 2.4 drives bed-only passages anti-phase (lr_corr .45) — 1.7 lands .65
BUS=${BUS:-}            # optional bus stage before loudnorm (unused in the shipped build)
BEDV=${BEDV:-0.70}       # bed level into the duck (v9 0.60; +1.3 dB because the brighter cut air lowers the peak-normalised bed)
DRV=${DRV:-1.25}        # drive into the lookahead limiter (loudness vs. the -1.0 dBFS decoded-peak gate)
OUT=${OUT:-/home/user/shade_respect_90s.mp4}

VOF="highpass=f=90,equalizer=f=250:t=q:w=1.0:g=-4.2,equalizer=f=430:t=q:w=1.4:g=-1.6,equalizer=f=3100:t=q:w=1.3:g=3.6,treble=g=2.8:f=7400,deesser=i=0.7:m=0.75:f=0.4,acompressor=threshold=0.045:ratio=3.6:attack=10:release=170:makeup=1.5,volume=1.92"

CLIPS=(r1_fit r2_fit r3_fit r4_fit r5_fit r6_fit r7_fit r8_fit r9_fit)
OFFS=(1200 9288 18614 25508 35638 44846 53924 63364 73472)          # timeline_respect.py ADELAY_MS

INS=()
for c in "${CLIPS[@]}"; do INS+=(-i "$A/$c.wav"); done

FC=""
MIXIN=""
n=${#CLIPS[@]}
for i in $(seq 0 $((n-1))); do
  idx=$((i+2))
  FC+="[$idx:a]aresample=48000,aformat=channel_layouts=stereo,adelay=${OFFS[$i]}|${OFFS[$i]}[v$i];"
  MIXIN+="[v$i]"
done
FC+="${MIXIN}amix=inputs=${n}:normalize=0:dropout_transition=0,${VOF},apad=whole_dur=${PADD},asplit=2[VOa][VOb];"   # ledger 55: the VO bus is padded to full length, otherwise the sidechain pair ends with the last clip and the bed goes silent for the tail
FC+="[1:a]volume=${BEDV}[BED];"
FC+="[BED][VOa]sidechaincompress=threshold=0.024:ratio=5:attack=6:release=260:makeup=1.0[DUCK];"
FC+="[VOb][DUCK]amix=inputs=2:weights=1 1:normalize=0,${BUS}treble=g=3.4:f=9000,extrastereo=m=${XS},loudnorm=I=${I}:TP=-1.6:LRA=9,volume=${DRV},alimiter=limit=${LIM}:attack=5:release=60:level=disabled,apad=whole_dur=${PADD},atrim=0:${D},asetpts=N/SR/TB[AOUT]"

if [ -n "$AUDIO_ONLY" ]; then       # fast audio iteration: same chain, AAC only
  "$FF" -y -v error -i "$B/respect_mute.mp4" -i "$B/asmr_bed_respect.wav" "${INS[@]}" \
    -filter_complex "$FC" -map "[AOUT]" -vn -c:a aac -b:a 192k -ar 48000 -t "$D" "$B/respect_audio_test.m4a"
  echo "AUDIO TEST -> $B/respect_audio_test.m4a"; exit 0
fi
"$FF" -y -i "$B/respect_mute.mp4" -i "$B/asmr_bed_respect.wav" "${INS[@]}" \
  -filter_complex "$FC" -map 0:v -map "[AOUT]" \
  -c:v libx264 -preset slow -crf 23 -maxrate 2800k -bufsize 5600k \
  -profile:v high -level 4.0 -g 60 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart -threads 2 \
  -t "$D" "$OUT"
echo "RESPECT MUX DONE -> $OUT"
