#!/bin/bash
# second half of the v2 build after the card-push fix: fix range 1100-1128 (shard 0 tail), shard 1, then a
# filter-concat mute master (shard0[0:1100) + fix + shard1), crf 16 intermediate.
set -e
cd /home/user
FF=$(python3 -c "import imageio_ffmpeg,sys;sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())")
log(){ echo "[$(date +%H:%M:%S)] $*"; }
log "RESPECT2: fix 1100-1128"
python3 src/respect2.py 1100 1128 build/r2_fix.mp4 > build/r2fix.log 2>&1 || { tail -n 8 build/r2fix.log; exit 1; }
log "RESPECT2: shard 1"
python3 src/respect2.py 1128 2256 build/r2_shard1.mp4 > build/r2s1.log 2>&1 || { tail -n 8 build/r2s1.log; exit 1; }
log "RESPECT2: concat"
"$FF" -y -loglevel error -i build/r2_shard0.mp4 -i build/r2_fix.mp4 -i build/r2_shard1.mp4 \
  -filter_complex "[0:v]trim=end_frame=1100,setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];[2:v]setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0,format=yuv420p[v]" \
  -map "[v]" -r 30 -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p build/respect2_mute.mp4
log "RESPECT2: mute master ready"
