#!/bin/bash
# finish_shadow.sh — after the picture render: verify → mux → measure → gates (no Drive md5 yet)
set -e
cd /home/user
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
B=build/wf03_film; WF=workflows/wf03_monarch_noir_film; OUT=$WF/THE_SHADOW_v1.mp4
echo "== render errors:"; python3 -c "import json;m=json.load(open('$B/picture_metrics.json'));print(len(m['errors']), 'errors;', m['render_seconds'], 's;', len(m['shots']), 'shots')"
echo "== mux"; $FF -y -loglevel error -i $B/picture.mp4 -i $B/mix.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart -shortest $OUT
ls -la $OUT; md5sum $OUT
echo "== probe"; $FF -i $OUT 2>&1 | grep -E "Duration|Stream"
echo "== gates"; python3 $WF/src/gate_shadow.py --mp4 $OUT --out $WF/GATES_THE_SHADOW_v1.md | head -40
