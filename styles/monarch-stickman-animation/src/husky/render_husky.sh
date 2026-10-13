#!/bin/bash
# renders the Husky sprite clips used by dog_husky.py (skips frames that already exist)
STUB=/tmp/stublib; PY=/tmp/venvs/blender/bin/python; OUT=/home/user/build/dog/out/v2; RES=${RES:-768}
cd /home/user/Monarch-Studio/styles/monarch-stickman-animation/src/husky
spec=""
need() { local clip=$1 a=$2 b=$3; local miss=""; for i in $(seq $a $b); do f=$(printf "%s/%s_%03d.png" $OUT $clip $i); [ -s "$f" ] || miss="$miss,$i"; done; [ -n "$miss" ] && spec="$spec $clip:${miss#,}"; }
need Idle 0 79; need Walk 0 24; need Eating 0 63; need Death 25 25
echo "to render: $spec"
[ -n "$spec" ] && LD_LIBRARY_PATH=$STUB $PY $(dirname $0)/run_dogrig.py -- $OUT $RES $spec 2>&1 | grep --line-buffered -E "RENDER|Error|Traceback"
ls $OUT | wc -l; echo HUSKY_DONE
