"""dog_husky.py — the golden dog for AMEER KA KUTTA v5, drawn from a CC0 3D rig.

Source: Husky.glb from Quaternius "Ultimate Animated Animal Pack" (CC0-1.0), mirrored at
github.com/trebeljahr/quaternius-showcase (public/glb/animals_pack/Husky.glb). husky/dogrig.py renders
it with Blender 4.3 Cycles (RGBA PNG per frame, recoloured gold) into SPRITE_DIR (kept out of git).

Same call shape as kutta.dog(d, x, gy, s, t, pose, flip):
    dog(d, x, gy, s, t, pose='stand'|'walk'|'eat'|'sit'|'lie', flip=False)
Poses map to real rig clips: stand/sit -> Idle loop, walk -> Walk loop, eat -> Eating loop,
lie -> the final frame of Death (the dog settles flat). The sprite is placed so its paws sit on
(x, gy); its height is REF_H * s. A tight ink outline is composited under the sprite.
The render faces left; 2D dogs face right, so flip=False mirrors the sprite.
"""
import os
import numpy as np
from PIL import Image, ImageFilter, ImageOps

SPRITE_DIR = os.environ.get('HUSKY_SPRITES', '/home/user/build/dog/out/v2')
FPS = 30
REF_H = 360.0          # 2D dog height (paw to head top) at s = 1, in kutta units (= px)
OUT_PX = 4.0           # outline width at s = 1
INK = (30, 24, 34)
# name -> (rendered clip, frame count, first rendered frame index)
CLIPS = {'stand': ('Idle', 80, 0), 'sit': ('Idle', 80, 0), 'walk': ('Walk', 25, 0),
         'eat': ('Eating', 64, 0), 'lie': ('Death', 1, 25)}
_ALPHA_T = 8

_geo = {}      # clip -> dict(L, T, ax, feet, base_h)
_frames = {}   # clip -> list of cropped RGBA frames
_cache = {}


def _path(clip, i):
    return os.path.join(SPRITE_DIR, f'{clip}_{i:03d}.png')


def _geometry():
    """Idle frame 0 defines the anchor: horizontal centre of the body and the paw row."""
    if 'stand' in _geo:
        return _geo['stand']
    im = Image.open(_path('Idle', 0)).convert('RGBA')
    a = im.getchannel('A').point(lambda v: 255 if v > 128 else 0)
    l, t, r, b = a.getbbox()
    feet = b - 1
    _geo['stand'] = dict(ax=(l + r) / 2.0, feet=float(feet), base_h=float(b - t))
    return _geo['stand']


def _clip_frames(pose):
    """Crops every frame of a clip to one union box, so all frames of a clip share the anchor."""
    if pose in _frames:
        return _frames[pose]
    clip, n, f0 = CLIPS[pose]
    ims = [Image.open(_path(clip, f0 + i)).convert('RGBA') for i in range(n)]
    L = T = 10 ** 9
    R = B = -1
    for im in ims:
        bb = im.getchannel('A').point(lambda v: 255 if v > _ALPHA_T else 0).getbbox()
        if bb:
            L, T, R, B = min(L, bb[0]), min(T, bb[1]), max(R, bb[2]), max(B, bb[3])
    _geo[('box', pose)] = (L, T)
    _frames[pose] = [im.crop((L, T, R, B)) for im in ims]
    return _frames[pose]


def _sprite(pose, idx, k, mirror):
    key = (pose, idx, round(k, 3), mirror)
    if key in _cache:
        return _cache[key]
    im = _clip_frames(pose)[idx]
    w, h = im.size
    nw, nh = max(1, round(w * k)), max(1, round(h * k))
    im = im.resize((nw, nh), Image.LANCZOS)
    # v9: richer gold (the raw render reads brown): warm the fur, keep the ink and the alpha
    _a = np.asarray(im).astype(np.float32)
    _a[..., 0] = np.minimum(255, _a[..., 0] * 1.10 + 6)
    _a[..., 1] = np.minimum(255, _a[..., 1] * 1.02)
    _a[..., 2] = _a[..., 2] * 0.80
    im = Image.fromarray(_a.astype(np.uint8), 'RGBA')
    if mirror:
        im = ImageOps.mirror(im)
    r = max(2, round(OUT_PX * k))
    dil = im.getchannel('A').filter(ImageFilter.MaxFilter(2 * r + 1))
    out = Image.new('RGBA', (nw, nh), INK + (0,))
    out.putalpha(dil)
    out.alpha_composite(im)
    if len(_cache) > 900:
        _cache.clear()
    _cache[key] = out
    return out


def dog(d, x, gy, s, t, pose='stand', flip=False, blink_at=3.4):
    pose = pose if pose in CLIPS else 'stand'
    g = _geometry()
    _, n, _f0 = CLIPS[pose]
    idx = int(t * FPS) % n if n > 1 else 0
    _clip_frames(pose)
    L, T = _geo[('box', pose)]
    k = REF_H * s / g['base_h']
    mirror = not flip                  # 2D dogs face right; the render faces left
    w, h = _clip_frames(pose)[idx].size
    sx = (g['ax'] - L) * k             # anchor column inside the scaled crop (unmirrored)
    sy = (g['feet'] - T) * k           # paw row inside the scaled crop
    if mirror:
        sx = round(w * k) - sx
    sp = _sprite(pose, idx, k, mirror)
    base = Image.Image()._new(d.im)
    ox, oy = int(round(x - sx)), int(round(gy - sy))
    if base.mode == 'RGBA':
        base.alpha_composite(sp, (ox, oy))
    else:
        base.paste(sp.convert('RGB'), (ox, oy), sp)
