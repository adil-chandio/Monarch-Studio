#!/bin/bash
# AMEER KA KUTTA v1 (23.7 s, 9:16): picture (src/kutta.py, 2 shards) + audio (src/mux_kutta.py) + gate.
# VO clips must exist in /home/user/build/kutta/vo/k1..k4.wav (voice-03, ur-PK, Urdu script TTS input).
# Media stays outside the repo (/home/user/build/kutta). Re-render time about 4 min on 2 CPUs.
set -e
export PATH=/tmp/venvs/render/bin:$PATH
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
OUT=/home/user/build/kutta
mkdir -p "$OUT"
FF=$(python3 -c "import imageio_ffmpeg,sys;sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())")
NF=711
python3 src/kutta.py 0 356 "$OUT/shard0.mp4" > "$OUT/s0.log" 2>&1 &
python3 src/kutta.py 356 $NF "$OUT/shard1.mp4" > "$OUT/s1.log" 2>&1
wait
printf "file '%s/shard0.mp4'\nfile '%s/shard1.mp4'\n" "$OUT" "$OUT" > "$OUT/list.txt"
"$FF" -y -v error -f concat -safe 0 -i "$OUT/list.txt" -c copy "$OUT/kutta_mute.mp4"
python3 src/mux_kutta.py mux
python3 src/gate_kutta.py "$OUT/kutta_v1.mp4" | tee "$OUT/gate.txt"
