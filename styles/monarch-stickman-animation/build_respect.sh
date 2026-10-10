#!/bin/bash
# One-shot rebuild of the 90 s IZZAT short (SHADE hero, hybrid look, cinematic layer).
# Shards render one after the other (ledger 54: two encoders + two renderers exceed 2 GB here),
# then bed -> concat -> mux (locked POWER chain) -> forensic gate. ~16 min.
set -e
cd /home/user
mkdir -p build
FF=$(python3 -c "import imageio_ffmpeg,sys;sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())")
log(){ echo "[$(date +%H:%M:%S)] $*"; }
log "RESPECT: rendering 2 shards SEQUENTIALLY (two x264 encoders + two renderers OOM-killed in the 2 GB sandbox — ledger 54)"
python3 src/respect.py 0    1350 build/respect_shard0.mp4 > build/rs0.log 2>&1 || { tail -n 5 build/rs0.log; exit 1; }
python3 src/respect.py 1350 2700 build/respect_shard1.mp4 > build/rs1.log 2>&1 || { tail -n 5 build/rs1.log; exit 1; }
log "RESPECT: shards done"
log "RESPECT: building bed"
python3 src/make_asmr_respect.py > build/asmr_respect.log 2>&1 || { tail -n 10 build/asmr_respect.log; exit 1; }
printf "file '/home/user/build/respect_shard0.mp4'\nfile '/home/user/build/respect_shard1.mp4'\n" > build/rlist.txt
"$FF" -y -loglevel error -f concat -safe 0 -i build/rlist.txt -c copy build/respect_mute.mp4
log "RESPECT: mux"
bash src/mux_respect.sh > build/mux_respect.log 2>&1 || { tail -n 20 build/mux_respect.log; exit 1; }
log "RESPECT: gate"
python3 src/gate_respect.py | tee build/gate_respect.log | tail -n 22
printf "%-24s %10s B  sha256[:16] %s  md5 %s\n" shade_respect_90s.mp4 "$(stat -c%s shade_respect_90s.mp4)" "$(sha256sum shade_respect_90s.mp4 | cut -c1-16)" "$(md5sum shade_respect_90s.mp4 | cut -c1-32)"
log "RESPECT: done"
