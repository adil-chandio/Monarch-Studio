#!/bin/bash
# AMEER KA KUTTA v9 — rebuild the sandbox environment after a reset (idempotent)
set -e
mkdir -p /home/user/work/build9/kutta/vo /home/user/work/build9/kutta/v2 /home/user/work/build9/sfx_lib2 /home/user/work/build9/dog/out/v2
[ -L /home/user/build ] || { rm -rf /home/user/build; ln -sfn /home/user/work/build9 /home/user/build; }
ln -sfn /home/user/Monarch-Studio/styles/monarch-stickman-animation/fonts /home/user/fonts
ln -sfn /home/user/Monarch-Studio/styles/monarch-stickman-animation/src /home/user/src
if ! /tmp/venvs/render/bin/python -c "import numpy, PIL, scipy, imageio_ffmpeg" 2>/dev/null; then
  python3 -m venv /tmp/venvs/render && /tmp/venvs/render/bin/pip install -q numpy pillow imageio-ffmpeg scipy
fi
/tmp/venvs/render/bin/python -c "import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())" > /home/user/build/ff_path.txt
echo "RENDER_VENV_OK $(cat /home/user/build/ff_path.txt)"
STUB=/tmp/stublib; mkdir -p $STUB
for lib in libXrender.so.1 libXxf86vm.so.1 libXfixes.so.3 libXi.so.6 libxkbcommon.so.0 libSM.so.6 libICE.so.6 libGL.so.1; do
  [ -f $STUB/$lib ] || (cd $STUB && echo "int stub_dummy(void){return 0;}" > s_$lib.c && gcc -shared -fPIC -Wl,-soname,$lib -o $lib s_$lib.c)
done
[ -f /home/user/build/dog/Husky.glb ] || curl -sL -m 120 -H "Accept: application/vnd.github.raw" \
  "https://api.github.com/repos/trebeljahr/quaternius-showcase/contents/public/glb/animals_pack/Husky.glb" -o /home/user/build/dog/Husky.glb
ls -la /home/user/build/dog/Husky.glb
if [ "$1" = "blender" ]; then
  if ! LD_LIBRARY_PATH=$STUB /tmp/venvs/blender/bin/python -c "import os,sys; sys.setdlopenflags(os.RTLD_LAZY|os.RTLD_GLOBAL); import bpy" 2>/dev/null; then
    python3 -m venv /tmp/venvs/blender && /tmp/venvs/blender/bin/pip install -q "bpy==4.3.0" "numpy<2"
  fi
  LD_LIBRARY_PATH=$STUB /tmp/venvs/blender/bin/python -c "import os,sys; sys.setdlopenflags(os.RTLD_LAZY|os.RTLD_GLOBAL); import bpy; print('BPY_OK', bpy.app.version_string)"
fi
echo BOOTSTRAP9_DONE
