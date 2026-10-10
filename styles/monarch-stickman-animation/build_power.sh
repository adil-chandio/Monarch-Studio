#!/bin/bash
# One-shot rebuild of the 42 s POWERFUL MAN short. Order follows ledger 36:
# the audio build runs only after both render shards have exited.
set -e
cd /home/user
mkdir -p build
FF=$(python3 -c "import imageio_ffmpeg,sys;sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())")
log(){ echo "[$(date +%H:%M:%S)] $*"; }
log "POWER: launching 2 render shards (1260 frames)"
python3 src/power.py 0   630  build/pw0.mp4 > build/pw0.log 2>&1 & P0=$!
python3 src/power.py 630 1260 build/pw1.mp4 > build/pw1.log 2>&1 & P1=$!
wait $P0; R0=$?; wait $P1; R1=$?
log "POWER: shards exited rc=$R0/$R1"
[ $R0 -ne 0 ] || [ $R1 -ne 0 ] && { tail -n 5 build/pw0.log build/pw1.log; exit 1; }
log "POWER: building bed"
python3 src/make_asmr_power.py > build/asmr_power.log 2>&1 || { tail -n 10 build/asmr_power.log; exit 1; }
printf "file '/home/user/build/pw0.mp4'\nfile '/home/user/build/pw1.mp4'\n" > build/pwlist.txt
"$FF" -y -loglevel error -f concat -safe 0 -i build/pwlist.txt -c copy build/power_mute.mp4
log "POWER: mux"
bash src/mux_power.sh > build/mux_power.log 2>&1 || { tail -n 20 build/mux_power.log; exit 1; }
log "POWER: gate"
python3 src/gate_power.py | tee build/gate_power.log | tail -n 20
printf "%-28s %10s B  sha256[:16] %s\n" stickman_power_42s.mp4 "$(stat -c%s stickman_power_42s.mp4)" "$(sha256sum stickman_power_42s.mp4 | cut -c1-16)"
