#!/usr/bin/env bash
# Shared environment for the render box. Source this.
#   source gpu/jobs/env.sh
set -euo pipefail
export BRANCH="arena/faa9119c-monarch-studio"
export REPO="adil-chandio/Monarch-Studio"
export WORK="${WORK:-/content/chaos_work}"
export WF="$WORK/WF04-CHAOS04"
mkdir -p "$WORK"

fetch_repo() {
  echo "[env] fetching $BRANCH from codeload"
  curl -fsSL "https://codeload.github.com/$REPO/tar.gz/refs/heads/$BRANCH" -o "$WORK/repo.tgz"
  rm -rf "$WF"
  mkdir -p "$WF"
  local prefix
  prefix="$(tar -tzf "$WORK/repo.tgz" | head -1 | cut -d/ -f1)"
  tar -xzf "$WORK/repo.tgz" -C "$WF" --strip-components=5 \
    "$prefix/workflows/current/payload/WF04-CHAOS04"
  ls "$WF"
}

ensure_blender() {
  if command -v blender >/dev/null 2>&1; then
    export BL="$WORK/run_blender.sh"
    cat > "$BL" <<'EOS'
#!/usr/bin/env bash
exec blender -b --python "$@"
EOS
    chmod +x "$BL"
    blender --version | head -2
    return
  fi
  python3 - <<'EOP'
import importlib.util, sys
print("[env] blender binary not found, using the bpy wheel")
sys.exit(0 if importlib.util.find_spec("bpy") else 1)
EOP
  if [ $? -ne 0 ]; then
    pip install --quiet "bpy==4.2.0"
  fi
  export BL="$WORK/run_bpy.sh"
  cat > "$BL" <<'EOS'
#!/usr/bin/env bash
# run a chaos04 script through the bpy module: first arg is the script
script="$1"; shift
exec python3 "$script" "$@"
EOS
  chmod +x "$BL"
  python3 -c "import bpy; print('[env] bpy', bpy.app.version_string)"
}
