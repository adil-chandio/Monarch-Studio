#!/usr/bin/env bash
# freevideo_start.sh — GPU box par ek hi paste: FreeVideo + Monarch ke 12 stickman scenes.
#
#   curl -fsSL https://raw.githubusercontent.com/adil-chandio/Monarch-Studio/arena/3d8cfad7-monarch-studio/scripts/freevideo_start.sh | bash
#
# Kya karta hai:
#   1. GPU/driver/disk check (Ampere/Ada/Hopper/Blackwell lazmi — Colab T4 nahi chalega)
#   2. FreeVideo clone + setup.sh (models download; ek baar)
#   3. 12 scenes render (keyframe -> video), resume-safe
#   4. clips + receipts ek folder me; /tmp/fv_clips.tar.gz bhi ban jata hai
#
# Owner ke liye kuch technical nahi: bas ek line paste karni hai.
set -uo pipefail

BRANCH="${MONARCH_BRANCH:-arena/3d8cfad7-monarch-studio}"
RAW="https://raw.githubusercontent.com/adil-chandio/Monarch-Studio/${BRANCH}"
HOME_ROOT="${HOME:-/root}"
FV_DIR="${FV_DIR:-$HOME_ROOT/FreeVideo}"
REPO_DIR="${REPO_DIR:-$HOME_ROOT/Monarch-Studio}"
OUT_DIR="${OUT_DIR:-$HOME_ROOT/monarch-clips}"

say() { printf '\n\033[1;36m== %s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31m!! %s\033[0m\n' "$*"; exit 1; }

say "1/5 GPU check"
command -v nvidia-smi >/dev/null 2>&1 || die "GPU nahi mila. Colab ka free T4 yahan kaam nahi karta — Ampere/Ada GPU wali machine chahiye (e.g. Lightning L4/A10G)."
nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader
CAP=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1 | tr -d ' ')
case "$CAP" in
  8.6*|8.9*|9.0*|10.0*|12.0*) : ;;
  *) die "compute capability $CAP supported nahi (chahiye 8.6 / 8.9 / 9.0 / 12.0 = Ampere/Ada/Hopper/Blackwell)" ;;
esac
FREE_GB=$(df -BG --output=avail "$HOME_ROOT" | tail -1 | tr -dc '0-9')
[ "${FREE_GB:-0}" -ge 60 ] || die "disk ${FREE_GB}GB hai, ~60GB chahiye"
command -v git >/dev/null 2>&1 || die "git nahi mila (Studio me: apt-get install -y git)"

say "2/5 FreeVideo"
if [ -x "$FV_DIR/freevideo" ]; then
  echo "already installed: $FV_DIR"
else
  [ -d "$FV_DIR/.git" ] || git clone --depth 1 https://github.com/FlashML-org/FreeVideo.git "$FV_DIR" || die "clone fail"
  ( cd "$FV_DIR" && ./setup.sh ) || die "setup.sh fail — log: $FV_DIR/launcher"
fi
"$FV_DIR/freevideo" plan --width 768 --height 1344 --seconds 3 >/dev/null 2>&1 \
  || echo "note: plan check skip (chalega bhi)"

say "3/5 Monarch tools"
if [ -d "$REPO_DIR/.git" ]; then
  ( cd "$REPO_DIR" && git fetch -q origin "$BRANCH" && git checkout -q FETCH_HEAD ) || true
else
  mkdir -p "$REPO_DIR"
  ( cd "$REPO_DIR" && git init -q && git remote add origin https://github.com/adil-chandio/Monarch-Studio.git \
    && git fetch -q --depth 1 origin "$BRANCH" && git checkout -q FETCH_HEAD ) || die "repo fetch fail"
fi
python3 -c "import sys; print('python', sys.version.split()[0])"

say "4/5 keyframes"
python3 - "$RAW" "$REPO_DIR" <<'PY'
import pathlib, sys, urllib.request
raw, repo = sys.argv[1], pathlib.Path(sys.argv[2])
kf = repo / "studio/films/stick-i2v/keyframes"
kf.mkdir(parents=True, exist_ok=True)
for i in range(1, 13):
    sid = f"k{i:02d}.png"
    f = kf / sid
    if not f.exists() or f.stat().st_size < 10000:
        urllib.request.urlretrieve(f"{raw}/studio/films/stick-i2v/keyframes/{sid}", f)
print(len(list(kf.glob('*.png'))), "keyframes ready")
PY

say "5/5 render (12 scenes — chai pee lo)"
mkdir -p "$OUT_DIR"
python3 "$REPO_DIR/tools/freevideo_run.py" \
  --job "$REPO_DIR/cloud/freevideo_jobs/stick-h3.json" \
  --out "$OUT_DIR" --work "$FV_DIR" --skip-setup
STATUS=$?

tar -czf /tmp/fv_clips.tar.gz -C "$OUT_DIR" . 2>/dev/null && echo "backup: /tmp/fv_clips.tar.gz"

DONE=$(ls "$OUT_DIR"/k*.mp4 2>/dev/null | wc -l | tr -d ' ')
say "RESULT: ${DONE}/12 clips in $OUT_DIR (exit $STATUS)"
echo "Agla step: agent ko bolo 'freevideo clips ready' — woh baqi sab karega."
