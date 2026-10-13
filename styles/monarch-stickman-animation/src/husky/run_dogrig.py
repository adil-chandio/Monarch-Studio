import os, sys
sys.setdlopenflags(os.RTLD_LAZY | os.RTLD_GLOBAL)   # P-007: lazy-bind GL symbols (libusd_ms glXGetProcAddress)
import runpy
runpy.run_path('/home/user/Monarch-Studio/styles/monarch-stickman-animation/src/husky/dogrig.py', run_name='__main__')
