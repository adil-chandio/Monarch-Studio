#!/usr/bin/env bash
# Rebuild the render environment for this sandbox.
#
# Why: heavy Python dependencies live outside the workspace and are NOT part of
# the Arena snapshot. Every fresh turn therefore starts without numpy/Pillow/
# scipy/ffmpeg; in earlier turns that cost the first 20-30 minutes of the session
# and looked to the user like the render had "stopped". Run this first instead of
# re-discovering it.
#
# Usage:
#   bash tools/bootstrap_env.sh          # install missing pieces, then verify
#   bash tools/bootstrap_env.sh --check  # verify only, install nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
STAMP_DIR="$ROOT/.runtime"
STAMP="$STAMP_DIR/env-bootstrap.stamp"
CHECK_ONLY=0
[[ "${1:-}" == "--check" ]] && CHECK_ONLY=1

PY="${PYTHON:-python3}"

verify() {
  "$PY" - <<'EOF'
import importlib, sys
need = ["numpy", "PIL", "scipy", "cv2", "imageio_ffmpeg"]
missing = []
for mod in need:
    try:
        importlib.import_module(mod)
    except Exception:
        missing.append(mod)
if missing:
    print("MISSING:" + ",".join(missing))
    sys.exit(1)
import imageio_ffmpeg, numpy, PIL, scipy, cv2
print(f"numpy {numpy.__version__} | Pillow {PIL.__version__} | scipy {scipy.__version__} | cv2 {cv2.__version__}")
print("ffmpeg " + imageio_ffmpeg.get_ffmpeg_exe())
EOF
}

if verify >/tmp/_envcheck.txt 2>&1; then
  cat /tmp/_envcheck.txt
  if [[ $CHECK_ONLY -eq 0 ]]; then
    mkdir -p "$STAMP_DIR"
    { date -u +"%Y-%m-%dT%H:%M:%SZ"; cat /tmp/_envcheck.txt; } > "$STAMP"
  fi
  echo "env: OK (render dependencies present)"
  exit 0
fi

if [[ $CHECK_ONLY -eq 1 ]]; then
  echo "env: INCOMPLETE — $(cat /tmp/_envcheck.txt)"
  echo "run: bash tools/bootstrap_env.sh"
  exit 1
fi

echo "env: installing render dependencies (pip, ~1-2 min, network: pypi.org)..."
PIP_ARGS=(--quiet --disable-pip-version-check)
if ! "$PY" -m pip install "${PIP_ARGS[@]}" -r requirements/render.txt >/tmp/_pip_render.log 2>&1; then
  echo "  plain pip failed (PEP 668 externally-managed env?); retrying with --break-system-packages"
  "$PY" -m pip install --break-system-packages "${PIP_ARGS[@]}" -r requirements/render.txt >>/tmp/_pip_render.log 2>&1 || {
    echo "pip install failed — tail of log:"; tail -20 /tmp/_pip_render.log; exit 1; }
fi

if verify >/tmp/_envcheck.txt 2>&1; then
  cat /tmp/_envcheck.txt
  mkdir -p "$STAMP_DIR"
  { date -u +"%Y-%m-%dT%H:%M:%SZ"; cat /tmp/_envcheck.txt; } > "$STAMP"
  echo "env: OK (render dependencies installed)"
  exit 0
fi

echo "env: STILL INCOMPLETE — $(cat /tmp/_envcheck.txt)"
echo "      ffmpeg note: renderers call imageio_ffmpeg.get_ffmpeg_exe(); there is no system ffmpeg binary."
exit 1
