#!/bin/bash
# AMEER KA KUTTA v9 — full build (after `bash husky/bootstrap9.sh blender && bash husky/render_husky.sh`)
#   VO + timing are expected in /home/user/build/kutta/vo (prep_vo_kutta.py / fit_k*.wav + timing.json)
set -e
export PATH=/tmp/venvs/render/bin:$PATH
SRC=$(cd "$(dirname "$0")" && pwd); W=/home/user/build/kutta/v2; mkdir -p $W; cd $W
NF=$(python3 -c "import sys; sys.argv=['x']; sys.path.insert(0,'$SRC'); import kutta2 as K; print(K.NF)")
N=${SHARDS:-2}
pids=""
for s in $(seq 0 $((N-1))); do
  a=$((NF*s/N)); b=$((NF*(s+1)/N))
  python3 $SRC/kutta2.py $a $b shard$s.mp4 > shard$s.log 2>&1 &
  pids="$pids $!"
done
for p in $pids; do wait $p; done
python3 $SRC/mux_kutta2.py                      # music + SFX + VO -> mix_kutta2.wav
KUTTA_OUT=${KUTTA_OUT:-/home/user/work/AMEER_KA_KUTTA_v9.mp4} python3 $SRC/mux_kutta2.py mux
python3 $SRC/gate_kutta2.py ${KUTTA_OUT:-/home/user/work/AMEER_KA_KUTTA_v9.mp4}
