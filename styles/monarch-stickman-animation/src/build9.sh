#!/bin/bash
# AMEER KA KUTTA v9 — full build (after `bash husky/bootstrap9.sh blender && bash husky/render_husky.sh`)
#   VO + timing are expected in /home/user/build/kutta/vo (prep_vo_kutta.py -> fit_k*.wav + timing.json;
#   the v9 VO archive is on Drive: AMEER_KA_KUTTA_v9_VO_voice00.zip)
#   CHUNKS (default 4) chunks rendered PAR (default 2) at a time -> shard0..N.mp4 -> mix -> mux -> gate
set -e
export PATH=/tmp/venvs/render/bin:$PATH
SRC=$(cd "$(dirname "$0")" && pwd); W=/home/user/build/kutta/v2; mkdir -p $W; cd $W
NF=$(python3 -c "import sys; sys.argv=['x']; sys.path.insert(0,'$SRC'); import kutta2 as K; print(K.NF)" 2>/dev/null | tail -1)
N=${CHUNKS:-4}; PAR=${PAR:-2}
rm -f shard*.mp4 shard*.log
for s in $(seq 0 $((N-1))); do echo "$((NF*s/N)) $((NF*(s+1)/N)) shard$s.mp4"; done |
  xargs -P $PAR -L 1 sh -c 'python3 '$SRC'/kutta2.py $0 $1 $2 > $2.log 2>&1; echo "DONE $2 $?"'
OUTF=${KUTTA_OUT:-/home/user/work/AMEER_KA_KUTTA_v9.mp4}
python3 $SRC/mux_kutta2.py                      # music + SFX + VO -> mix_kutta2.wav
KUTTA_OUT=$OUTF python3 $SRC/mux_kutta2.py mux
python3 $SRC/gate_kutta2.py $OUTF | tee ${OUTF%.mp4}_gate.txt
echo BUILD9_DONE
