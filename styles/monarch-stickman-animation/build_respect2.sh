#!/bin/bash
# v2 of the IZZAT short: 75.2 s, 33 shots, 32 distinct transitions, new SFX palette. Sequential shards (ledger 54).
set -e
cd /home/user
mkdir -p build
FF=$(python3 -c "import imageio_ffmpeg,sys;sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())")
log(){ echo "[$(date +%H:%M:%S)] $*"; }
NF=2256
log "RESPECT2: shard 0"
python3 src/respect2.py 0 1128 build/r2_shard0.mp4 > build/r2s0.log 2>&1 || { tail -n 8 build/r2s0.log; exit 1; }
log "RESPECT2: shard 1"
python3 src/respect2.py 1128 $NF build/r2_shard1.mp4 > build/r2s1.log 2>&1 || { tail -n 8 build/r2s1.log; exit 1; }
log "RESPECT2: shards done"
printf "file '/home/user/build/r2_shard0.mp4'\nfile '/home/user/build/r2_shard1.mp4'\n" > build/r2list.txt
"$FF" -y -loglevel error -f concat -safe 0 -i build/r2list.txt -c copy build/respect2_mute.mp4
log "RESPECT2: mute master ready"
