#!/bin/bash
# v3 of the IZZAT short = v2 timeline + audio chain, with the v3 picture pass (src/respect3.py):
#   grade (S-curve, warm highlights, cool shadows, vignette) + beat punch on each voice onset and cut.
# Writes only build/respect3_* (and the ASMR ledger the bed script always writes). Never writes
# /home/user/shade_respect_v2.mp4: the mux OUT default is overridden here.
# Note: mux_respect2.sh reads build/respect2_mute.mp4, so the v3 mute master is stored under that name.
# Run:  bash build_respect3.sh            (shards 0+1, about 15-20 min on 2 CPUs)
#       OUT=/home/user/build/respect3_v3.mp4 is set below.
set -e
export PATH=/tmp/venvs/render/bin:$PATH
cd /home/user
mkdir -p build
FF=$(python3 -c "import imageio_ffmpeg,sys;sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())")
log(){ echo "[$(date +%H:%M:%S)] $*"; }
NF=2256
log "RESPECT3: shard 0"
SHADE_ENH=1 python3 src/respect3.py 0 1128 build/r3_shard0.mp4 > build/r3s0.log 2>&1 || { tail -n 8 build/r3s0.log; exit 1; }
log "RESPECT3: shard 1"
SHADE_ENH=1 python3 src/respect3.py 1128 $NF build/r3_shard1.mp4 > build/r3s1.log 2>&1 || { tail -n 8 build/r3s1.log; exit 1; }
printf "file '/home/user/build/r3_shard0.mp4'\nfile '/home/user/build/r3_shard1.mp4'\n" > build/r3list.txt
"$FF" -y -loglevel error -f concat -safe 0 -i build/r3list.txt -c copy build/respect2_mute.mp4
log "RESPECT3: mute master ready"
log "bed"
python3 src/make_asmr_respect2.py
log "mux"
OUT=/home/user/build/respect3_v3.mp4 bash src/mux_respect2.sh
log "gate"
python3 src/gate_respect2.py /home/user/build/respect3_v3.mp4 | tee build/gate_respect3.txt
log "done"
