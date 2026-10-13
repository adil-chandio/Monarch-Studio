#!/usr/bin/env bash
# Rebuild the 3D render environment after a fresh clone or a sandbox reset.
# Idempotent: skips anything that already works.
#
#   tools/bootstrap/setup_3d.sh          # venvs + stub libraries + bpy check
#
# Creates:
#   /tmp/venvs/render   numpy, pillow, imageio-ffmpeg, scipy
#   /tmp/venvs/blender  bpy==4.3.0 (Blender Cycles, CPU) + numpy
#   /tmp/stublib        stub .so files for X11/GL sonames (apt is blocked here)
# Then verifies `import bpy` and prints BPY_OK.
# Vendor source is separate: tools/vendor/materialize.sh.
set -euo pipefail

VENVS=/tmp/venvs
STUB=/tmp/stublib
mkdir -p "$VENVS"

if [ ! -x "$VENVS/render/bin/python" ]; then
  python3 -m venv "$VENVS/render"
  "$VENVS/render/bin/pip" install -q numpy pillow imageio-ffmpeg scipy
  echo "render venv: ok"
else
  echo "render venv: present"
fi

if [ ! -x "$VENVS/blender/bin/python" ]; then
  python3 -m venv "$VENVS/blender"
  "$VENVS/blender/bin/pip" install -q "bpy==4.3.0" numpy
  echo "blender venv: ok"
else
  echo "blender venv: present"
fi

LIBS="libXrender.so.1 libXxf86vm.so.1 libXfixes.so.3 libXi.so.6 libxkbcommon.so.0 libSM.so.6 libICE.so.6 libGL.so.1"
mkdir -p "$STUB"
for lib in $LIBS; do
  if [ ! -f "$STUB/$lib" ]; then
    (cd "$STUB" && echo 'int stub_dummy(void){return 0;}' > "s_$lib.c" \
      && gcc -shared -fPIC -Wl,-soname,"$lib" -o "$lib" "s_$lib.c")
  fi
done
echo "stub libs: ok"

LD_LIBRARY_PATH="$STUB" "$VENVS/blender/bin/python" -c \
  "import os,sys; sys.setdlopenflags(os.RTLD_LAZY|os.RTLD_GLOBAL); import bpy; print('BPY_OK', bpy.app.version_string)" 2>/dev/null | grep BPY_OK

FF=$("$VENVS/render/bin/python" -c "import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())")
echo "ffmpeg: $FF"
echo "SETUP_3D_DONE"
