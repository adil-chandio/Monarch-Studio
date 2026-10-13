"""6-second animated 3-D demo (Mitsuba 3, CPU path tracer). 12 fps, 640x360.
Frames -> frames/ ; encode separately with encode_demo.py."""
import os
import sys
import time
import math
import mitsuba as mi

mi.set_variant('scalar_rgb')
from mitsuba import ScalarTransform4f as T

W, H, SPP = 640, 360, 32
FPS, SECONDS = 12, 6
N = FPS * SECONDS
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frames')
os.makedirs(OUT, exist_ok=True)


def scene(u):
    """u in [0,1): normalised time. Camera orbits slightly, box spins, ball bobs."""
    cam_angle = math.radians(-18 + 36 * u)
    cx, cz = 6.5 * math.sin(cam_angle), 6.5 * math.cos(cam_angle)
    box_rot = 360 * u
    ball_y = 1.0 + 0.18 * math.sin(2 * math.pi * 2 * u)
    return mi.load_dict({
        'type': 'scene',
        'integrator': {'type': 'path', 'max_depth': 6},
        'sensor': {
            'type': 'perspective', 'fov': 38,
            'to_world': T.look_at(origin=[cx, 1.6, cz], target=[0, 0.9, 0], up=[0, 1, 0]),
            'film': {'type': 'hdrfilm', 'width': W, 'height': H, 'rfilter': {'type': 'gaussian'}},
            'sampler': {'type': 'independent', 'sample_count': SPP},
        },
        'floor': {
            'type': 'rectangle',
            'to_world': T.rotate([1, 0, 0], -90).scale(20),
            'bsdf': {'type': 'roughplastic', 'diffuse_reflectance': {'type': 'rgb', 'value': [0.05, 0.05, 0.07]}, 'alpha': 0.08},
        },
        'ball': {
            'type': 'sphere', 'center': [0, ball_y, 0], 'radius': 1.0,
            'bsdf': {'type': 'roughplastic', 'diffuse_reflectance': {'type': 'rgb', 'value': [0.9, 0.25, 0.15]}, 'alpha': 0.12},
        },
        'box': {
            'type': 'cube',
            'to_world': T.translate([2.2, 0.6, -0.5]).rotate([0, 1, 0], box_rot).scale([0.6, 0.6, 0.6]),
            'bsdf': {'type': 'roughconductor', 'material': 'Au', 'alpha': 0.15},
        },
        'light': {
            'type': 'rectangle',
            'to_world': T.translate([0, 4, 3]).rotate([1, 0, 0], 60).scale(1.5),
            'emitter': {'type': 'area', 'radiance': {'type': 'rgb', 'value': [12, 11, 10]}},
        },
        'env': {'type': 'constant', 'radiance': {'type': 'rgb', 'value': [0.08, 0.09, 0.12]}},
    })


if __name__ == '__main__':
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else N
    t0 = time.time()
    for i in range(start, end):
        path = os.path.join(OUT, f'f{i:04d}.png')
        if os.path.exists(path):
            continue
        img = mi.render(scene(i / N))
        mi.util.write_bitmap(path, img)
        print(f'frame {i+1}/{N} elapsed {round(time.time()-t0)}s', flush=True)
    print('RENDER_DONE', flush=True)
