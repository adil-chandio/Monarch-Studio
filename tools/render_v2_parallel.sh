#!/usr/bin/env bash
# Deterministic two-way segment renderer for the 2-vCPU Arena workspace.
set -euo pipefail
if [[ $# -ne 5 ]]; then
  echo "usage: $0 PACKAGE FPS TOTAL_FRAMES STEM FINAL_MUTE" >&2
  exit 2
fi
pkg=$1 fps=$2 total=$3 stem=$4 final=$5
cd "$pkg"
mkdir -p build
half=$(( total / 2 ))
seg0="build/${stem}-part0.mp4"
seg1="build/${stem}-part1.mp4"
log0="build/${stem}-part0.log"
log1="build/${stem}-part1.log"
rm -f "$seg0" "$seg1" "$final" "$log0" "$log1"
python3 src/render.py --output "$seg0" --start-frame 0 --end-frame "$half" >"$log0" 2>&1 &
p0=$!
python3 src/render.py --output "$seg1" --start-frame "$half" --end-frame "$total" >"$log1" 2>&1 &
p1=$!
rc0=0; rc1=0
wait "$p0" || rc0=$?
wait "$p1" || rc1=$?
# A 2-vCPU/2-GiB runner can occasionally kill one encoder under transient
# memory pressure. Preserve the successful half and deterministically rerun only
# the failed half by itself; never restart the whole 74-second render.
if [[ $rc0 -ne 0 ]]; then
  echo "part0 failed in parallel (rc=$rc0); retrying solo" >&2
  rm -f "$seg0"
  python3 src/render.py --output "$seg0" --start-frame 0 --end-frame "$half" >>"$log0" 2>&1
fi
if [[ $rc1 -ne 0 ]]; then
  echo "part1 failed in parallel (rc=$rc1); retrying solo" >&2
  rm -f "$seg1"
  python3 src/render.py --output "$seg1" --start-frame "$half" --end-frame "$total" >>"$log1" 2>&1
fi
cat > build/concat.txt <<EOF
file '${stem}-part0.mp4'
file '${stem}-part1.mp4'
EOF
ffmpeg=$(python3 - <<'PY'
import imageio_ffmpeg
print(imageio_ffmpeg.get_ffmpeg_exe())
PY
)
"$ffmpeg" -y -v error -f concat -safe 0 -i build/concat.txt -c copy -movflags +faststart "$final"
echo "$final"
