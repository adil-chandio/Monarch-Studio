import time
import mitsuba as mi
mi.set_variant('scalar_rgb')
from mitsuba import ScalarTransform4f as T


def scene(angle, W=640, H=360, spp=32):
    return mi.load_dict({
        'type': 'scene',
        'integrator': {'type': 'path', 'max_depth': 6},
        'sensor': {
            'type': 'perspective', 'fov': 38,
            'to_world': T.look_at(origin=[0, 1.6, 6.5], target=[0, 0.9, 0], up=[0, 1, 0]),
            'film': {'type': 'hdrfilm', 'width': W, 'height': H, 'rfilter': {'type': 'gaussian'}},
            'sampler': {'type': 'independent', 'sample_count': spp},
        },
        'floor': {
            'type': 'rectangle',
            'to_world': T.rotate([1, 0, 0], -90).scale(20),
            'bsdf': {'type': 'roughplastic', 'diffuse_reflectance': {'type': 'rgb', 'value': [0.05, 0.05, 0.07]}, 'alpha': 0.08},
        },
        'ball': {
            'type': 'sphere', 'center': [0, 1.0, 0], 'radius': 1.0,
            'bsdf': {'type': 'roughplastic', 'diffuse_reflectance': {'type': 'rgb', 'value': [0.9, 0.25, 0.15]}, 'alpha': 0.12},
        },
        'box': {
            'type': 'cube',
            'to_world': T.translate([2.2, 0.6, -0.5]).rotate([0, 1, 0], angle).scale([0.6, 0.6, 0.6]),
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
    t = time.time()
    img = mi.render(scene(0.4))
    print('render seconds', round(time.time() - t, 1), flush=True)
    mi.util.write_bitmap('probe.png', img)
