#!/bin/bash
# One-shot rebuild of the SHADE remake (42 s POWERFUL MAN, hybrid look). Same order as
# build_power.sh (ledger 36): the audio build runs only after both render shards have exited.
set -e
cd /home/user
mkdir -p build
FF=$(python3 -c "import imageio_ffmpeg,sys;sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())")
log(){ echo "[$(date +%H:%M:%S)] $*"; }
log "SHADE: launching 2 render shards (1260 frames)"
python3 src/power2.py 0   630  build/sh0.mp4 > build/sh0.log 2>&1 & P0=$!
python3 src/power2.py 630 1260 build/sh1.mp4 > build/sh1.log 2>&1 & P1=$!
wait $P0; R0=$?; wait $P1; R1=$?
log "SHADE: shards exited rc=$R0/$R1"
[ $R0 -ne 0 ] || [ $R1 -ne 0 ] && { tail -n 5 build/sh0.log build/sh1.log; exit 1; }
log "SHADE: building bed"
python3 src/make_asmr_power.py > build/asmr_power.log 2>&1 || { tail -n 10 build/asmr_power.log; exit 1; }
printf "file '/home/user/build/sh0.mp4'\nfile '/home/user/build/sh1.mp4'\n" > build/shlist.txt
"$FF" -y -loglevel error -f concat -safe 0 -i build/shlist.txt -c copy build/shade_mute.mp4
cp build/shade_mute.mp4 build/power_mute.mp4          # mux_power.sh reads build/power_mute.mp4
log "SHADE: mux (locked v1 chain, OUT overridden)"
OUT=/home/user/shade_power_42s.mp4 bash src/mux_power.sh > build/mux_shade.log 2>&1 || { tail -n 20 build/mux_shade.log; exit 1; }
log "SHADE: gate"
python3 src/gate_shade.py | tee build/gate_shade.log | tail -n 22
printf "%-24s %10s B  sha256[:16] %s  md5 %s\n" shade_power_42s.mp4 "$(stat -c%s shade_power_42s.mp4)" "$(sha256sum shade_power_42s.mp4 | cut -c1-16)" "$(md5sum shade_power_42s.mp4 | cut -c1-32)"
