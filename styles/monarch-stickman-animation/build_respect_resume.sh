#!/bin/bash
# Resume path for build_respect.sh: renders shards SEQUENTIALLY (two x264 encoders + two renderers
# exceeded the 2 GB sandbox — ledger 54), skipping any shard whose mp4 already has 1350 frames.
set -e
cd /home/user
mkdir -p build
FF=$(python3 -c "import imageio_ffmpeg,sys;sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())")
FP=$(dirname "$FF")/ffprobe; [ -x "$FP" ] || FP=""
log(){ echo "[$(date +%H:%M:%S)] $*"; }
frames(){ python3 - "$1" <<'PY'
import sys, subprocess, imageio_ffmpeg
ff = imageio_ffmpeg.get_ffmpeg_exe()
try:
    out = subprocess.run([ff, '-i', sys.argv[1], '-map', '0:v:0', '-f', 'null', '-'], capture_output=True, text=True).stderr  # decode-count: '-c copy' prints no frame= in ffmpeg 7
    import re; m = re.findall(r'frame=\s*(\d+)', out); print(m[-1] if m else 0)
except Exception: print(0)
PY
}
for S in 0 1; do
  A=$((S*1350)); B=$((A+1350)); F=build/respect_shard$S.mp4
  if [ -f "$F" ] && [ "$(frames $F)" = "1350" ]; then log "shard $S present (1350 frames) — kept"; continue; fi
  log "rendering shard $S ($A-$B)"
  python3 src/respect.py $A $B $F > build/rs$S.log 2>&1 || { tail -n 8 build/rs$S.log; exit 1; }
  log "shard $S done: $(frames $F) frames"
done
log "building bed"
python3 src/make_asmr_respect.py > build/asmr_respect.log 2>&1 || { tail -n 10 build/asmr_respect.log; exit 1; }
printf "file '/home/user/build/respect_shard0.mp4'\nfile '/home/user/build/respect_shard1.mp4'\n" > build/rlist.txt
"$FF" -y -loglevel error -f concat -safe 0 -i build/rlist.txt -c copy build/respect_mute.mp4
log "mux"
bash src/mux_respect.sh > build/mux_respect.log 2>&1 || { tail -n 20 build/mux_respect.log; exit 1; }
log "gate"
python3 src/gate_respect.py | tee build/gate_respect.log | tail -n 22
printf "%-24s %10s B  sha256[:16] %s  md5 %s\n" shade_respect_90s.mp4 "$(stat -c%s shade_respect_90s.mp4)" "$(sha256sum shade_respect_90s.mp4 | cut -c1-16)" "$(md5sum shade_respect_90s.mp4 | cut -c1-32)"
log "done"
