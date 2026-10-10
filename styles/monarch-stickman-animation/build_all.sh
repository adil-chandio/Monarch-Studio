#!/bin/bash
# Regenerates the two deliverables that were not inside "video edit workflow.zip":
#   1. /home/user/stickman_wide_episode_full.mp4   (1080p master, 263.5 s)  — VIDEO_EPISODE_NOTES.md §8
#   2. /home/user/stickman_wide_hook_53s.mp4        (53 s hook)             — VIDEO_WIDE_NOTES.md §8
# Order follows ledger entry 36: never run an audio build while both render shards are live.
set -u
cd /home/user
mkdir -p build
FF=$(python3 -c "import imageio_ffmpeg,sys;sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())")
log(){ echo "[$(date +%H:%M:%S)] $*"; }

# ───────────────────────── 1. FULL EPISODE ─────────────────────────
log "EPISODE: launching 2 render shards (7905 frames)"
printf "file '/home/user/build/fc0.mp4'\nfile '/home/user/build/fc1.mp4'\n" > build/fclist.txt
python3 src/wide_full.py 0    3953 build/fc0.mp4 > build/fc0.log 2>&1 &
P0=$!
python3 src/wide_full.py 3953 7905 build/fc1.mp4 > build/fc1.log 2>&1 &
P1=$!
wait $P0; R0=$?
wait $P1; R1=$?
log "EPISODE: shards exited rc=$R0/$R1  sizes: $(stat -c%s build/fc0.mp4 2>/dev/null) / $(stat -c%s build/fc1.mp4 2>/dev/null)"
if [ $R0 -ne 0 ] || [ $R1 -ne 0 ]; then log "EPISODE: SHARD FAILURE"; tail -n 5 build/fc0.log build/fc1.log; exit 1; fi

log "EPISODE: building bed (shards finished, memory free)"
python3 src/wide_full_audio.py > build/full_audio.log 2>&1; RA=$?
log "EPISODE: bed rc=$RA  $(ls -la build/full_bed.wav 2>/dev/null)"
[ $RA -ne 0 ] && { log "EPISODE: AUDIO FAILURE"; tail -n 10 build/full_audio.log; exit 1; }

log "EPISODE: concat"
"$FF" -y -loglevel error -f concat -safe 0 -i build/fclist.txt -c copy build/full_mute.mp4 || { log "concat failed"; exit 1; }

log "EPISODE: mux"
bash src/mux_full.sh > build/mux_full.log 2>&1; RM=$?
log "EPISODE: mux rc=$RM  $(ls -la /home/user/stickman_wide_episode_full.mp4 2>/dev/null)"
[ $RM -ne 0 ] && { log "EPISODE: MUX FAILURE"; tail -n 20 build/mux_full.log; exit 1; }

log "EPISODE: gate"
python3 src/gate_full.py > build/gate_full.log 2>&1; RG=$?
log "EPISODE: gate rc=$RG"
cat build/gate_full.log

# ───────────────────────── 2. 53 s HOOK ─────────────────────────
log "HOOK: launching 2 render shards (1590 frames)"
printf "file '/home/user/build/wc0.mp4'\nfile '/home/user/build/wc1.mp4'\n" > build/wclist.txt
python3 src/wide.py 0   795  build/wc0.mp4 > build/wc0.log 2>&1 &
P0=$!
python3 src/wide.py 795 1590 build/wc1.mp4 > build/wc1.log 2>&1 &
P1=$!
wait $P0; R0=$?
wait $P1; R1=$?
log "HOOK: shards exited rc=$R0/$R1"
if [ $R0 -ne 0 ] || [ $R1 -ne 0 ]; then log "HOOK: SHARD FAILURE"; tail -n 5 build/wc0.log build/wc1.log; exit 1; fi

log "HOOK: building bed"
python3 src/wide_audio.py > build/wide_audio.log 2>&1; RA=$?
log "HOOK: bed rc=$RA  $(ls -la build/wide_bed.wav 2>/dev/null)"
[ $RA -ne 0 ] && { log "HOOK: AUDIO FAILURE"; tail -n 10 build/wide_audio.log; exit 1; }

log "HOOK: concat + mux"
"$FF" -y -loglevel error -f concat -safe 0 -i build/wclist.txt -c copy build/wide_mute.mp4 || { log "concat failed"; exit 1; }
bash src/mux_hook.sh > build/mux_hook.log 2>&1; RM=$?
log "HOOK: mux rc=$RM  $(ls -la /home/user/stickman_wide_hook_53s.mp4 2>/dev/null)"

log "ALL DONE"
for f in stickman_wide_episode_full.mp4 stickman_wide_hook_53s.mp4; do
  [ -f "$f" ] && printf "%-38s %12s B  sha256[:16] %s\n" "$f" "$(stat -c%s $f)" "$(sha256sum $f | cut -c1-16)"
done
