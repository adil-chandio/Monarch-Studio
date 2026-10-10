#!/usr/bin/env bash
# THE SHADOW v1 — delivery encode (WF-03 · Monarch Noir Film)
# Memory-safe on a 2 GB sandbox: ONE decoder + ONE x264 at a time, segments concatenated losslessly.
#   seg1  master frames [0,1774)      + S03 trim  eq gamma 0.95 on t 13.0–21.49 (S03 luma 35 → ≈30)
#   seg2  fix_m1  (M1 re-rendered 'mid' framing, 41 f, kills the S10→M1 same-size jump cut)
#   seg3  master frames [1815,2902)
#   seg4  fix_s16 (S16 re-rendered as a medium 1.50→1.26 dolly-out / anchor .22,.62, 192 f, kills the S15→S16 jump cut) + gamma 0.93 (luma 36 → ≈30)
#   seg5  master frames [3094,end)
# then concat demuxer (-c copy) + mix.wav → aac 192k, faststart.  CRF 21 medium (grain-softened, no banding, ≈5 Mbit/s).
set -euo pipefail
cd /home/user
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
B=build/wf03_film; S=$B/seg; mkdir -p $S
X=(-r 24 -c:v libx264 -preset medium -crf 21 -pix_fmt yuv420p -x264-params keyint=48:min-keyint=24:scenecut=0 -an)
seg() { # name input filter
  echo "== $1  $(date +%H:%M:%S)"
  $FF -y -nostats -loglevel error -i "$2" -filter_complex "$3" -map "[v]" "${X[@]}" "$S/$1.mp4"
  n=$($FF -i "$S/$1.mp4" -map 0:v -f null - 2>&1 | grep -o "frame= *[0-9]*" | tail -1 | tr -dc 0-9)
  echo "   $1 frames=$n"
}
seg seg1 $B/picture.mp4 "[0:v]trim=start_frame=0:end_frame=1774,setpts=PTS-STARTPTS,fps=24,eq=gamma=0.95:enable='between(t,13.0,21.49)',format=yuv420p[v]"
seg seg2 $B/fix_m1.mp4  "[0:v]setpts=PTS-STARTPTS,fps=24,format=yuv420p[v]"
seg seg3 $B/picture.mp4 "[0:v]trim=start_frame=1815:end_frame=2902,setpts=PTS-STARTPTS,fps=24,format=yuv420p[v]"
seg seg4 $B/fix_s16.mp4 "[0:v]setpts=PTS-STARTPTS,fps=24,eq=gamma=0.93,format=yuv420p[v]"
seg seg5 $B/picture.mp4 "[0:v]trim=start_frame=3094,setpts=PTS-STARTPTS,fps=24,format=yuv420p[v]"
printf "file '%s'\n" seg1.mp4 seg2.mp4 seg3.mp4 seg4.mp4 seg5.mp4 > $S/list.txt
echo "== concat + mux  $(date +%H:%M:%S)"
$FF -y -nostats -loglevel error -f concat -safe 0 -i $S/list.txt -i $B/mix.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart -shortest $B/THE_SHADOW_v1.mp4
n=$($FF -i $B/THE_SHADOW_v1.mp4 -map 0:v -f null - 2>&1 | grep -o "frame= *[0-9]*" | tail -1 | tr -dc 0-9)
echo "   final frames=$n (expect 3766)"
ls -la $B/THE_SHADOW_v1.mp4; md5sum $B/THE_SHADOW_v1.mp4
echo ENCODE_DONE
