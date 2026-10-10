#!/bin/bash
# after build_respect2.sh: bed -> mux -> gate (kept separate so the render script is never edited while running)
set -e
cd /home/user
log(){ echo "[$(date +%H:%M:%S)] $*"; }
test -s build/respect2_mute.mp4 || { echo "no mute master"; exit 1; }
log "bed"
python3 src/make_asmr_respect2.py
log "mux"
bash src/mux_respect2.sh
log "gate"
python3 src/gate_respect2.py /home/user/shade_respect_v2.mp4 | tee build/gate_respect2.txt
log "done"
