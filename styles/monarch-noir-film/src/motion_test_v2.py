#!/usr/bin/env python3
"""motion_test_v2.py — 8 s motion test of the 3-D human stick hero (1280×720, 24 fps):
0–3 s  face close-up: breathing, blinks, gaze shift, expression morph tired → resolve, slow push-in
3–5.5 s walk cycle (side), contact shadows, camera follows
5.5–8 s the hook: sitting on the bed with the phone, phone flicker lights the face, blink, head lift at the end."""
import os, sys, math, subprocess, time
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stick3d as S
import human as Hm
import world as Wd
import imageio_ffmpeg

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(Wd.WF, 'HERO_v2_motion_test.mp4')
W, H, FPS = 1280, 720, 24
DUR = 8.0
STUDIO = S.light_rig(key_dir=(-0.55, -0.6, 0.6), key_col=(1.0, 0.94, 0.86), key_int=1.05,
                     fill_dir=(0.7, -0.1, 0.7), fill_col=(0.55, 0.65, 0.9), fill_int=0.2,
                     rim_dir=(0.55, -0.35, -0.75), rim_col=(0.75, 0.85, 1.0), rim_int=0.6)


def studio(w, h):
    y = np.linspace(0, 1, h)[:, None, None]
    a = np.array((34, 35, 41), np.float32)[None, None, :] * (1 - y) + np.array((12, 12, 15), np.float32)[None, None, :] * y
    return np.repeat(a, w, axis=1)


def seg_face(t):
    can = Image.fromarray(studio(W * 2, H * 2).astype(np.uint8)).convert('RGBA')
    u = t / 3.0
    s = (2300 + 260 * Hm.ease(u)) * 2
    e = Hm.expr_mix('tired', 'resolve', Hm.ease(max(0.0, (u - 0.45) / 0.45)))
    pose = dict(Hm.p_stand(t), head_t=-14 + 20 * Hm.ease(max(0.0, (u - 0.5) / 0.4)), head=2 * math.sin(t * 0.8))
    look = (0.25 - 0.45 * Hm.ease(max(0.0, (u - 0.5) / 0.3)), 0.25 - 0.3 * Hm.ease(max(0.0, (u - 0.5) / 0.3)))
    S.render_window(can, (0, 0, W * 2, H * 2), s, pose, STUDIO, focus='hctr', focus_off=(0.0, 0.04), expr=e,
                    look=look, blink_v=Hm.blink(t, seed=5))
    return np.asarray(can.resize((W, H), Image.LANCZOS).convert('RGB'), np.float32)


def seg_walk(t):
    tt = t - 3.0
    can = Image.fromarray(studio(W * 2, H * 2).astype(np.uint8)).convert('RGBA')
    s = 600 * 2
    phase = tt * 1.45
    pose = dict(Hm.walk_pose(phase % 1.0), yaw=90)
    x = (W * 0.5 + 40 * math.sin(tt * 0.7)) * 2
    y = (H * 0.92) * 2
    _, J, _ = S.solve(x, y, s, pose)
    S.contact_shadows(can, J, s, alpha=0.5)
    S.render(can, x, y, s, pose, STUDIO, expr='neutral', blink_v=Hm.blink(t, seed=7), look=(0.0, 0.05))
    return np.asarray(can.resize((W, H), Image.LANCZOS).convert('RGB'), np.float32)


def seg_hook(t):
    tt = t - 5.5
    f = Wd.camera(Wd.plate('bedroom_night'), zoom=1.45 + 0.05 * tt / 2.5, cx=0.40, cy=0.62) * 0.55
    x, y, s = 930, 735, 700
    lift = Hm.ease(max(0.0, (tt - 1.6) / 0.8))
    pose = dict(Hm.p_sit(t, 0.75 - 0.3 * lift), yaw=-12, head=10 - 8 * lift, head_t=6 - 10 * lift, ll=-5, lr=5, kl=98, kr=94, lz_l=72, lz_r=70)
    pose = S.reach(pose, 'r', (935, 612 - 20 * lift), x, y, s, anchor='hip')
    pose = S.reach(pose, 'l', (1000, 735), x, y, s, anchor='hip')
    pose['hw_r'] = 85
    K3, J, fr = S.solve(x, y, s, pose, anchor='hip')
    phone_pos = K3['har'] + np.array([0.0, -0.03 * s, 0.07 * s])
    fl = Wd.flicker(t, 3)
    L = S.scene_lights(x, y, s, (300, 200), key_col=(0.35, 0.42, 0.6), key_int=0.35, key_z=0.2,
                       fill_col=(0.2, 0.25, 0.35), fill_int=0.1, rim_dir=(0.6, -0.4, -0.7), rim_col=(0.4, 0.5, 0.8), rim_int=0.35,
                       sky=(0.05, 0.06, 0.10), ground=(0.02, 0.02, 0.03),
                       points=[S.point_light(phone_pos, (0.55, 0.72, 1.0), 2.2 * (0.8 + 0.2 * fl), 0.22 * s)])
    layer = Wd.text_layer()
    e = Hm.expr_mix('tired', 'doubt', lift)
    S.person(layer, x, y, s, pose, L, hands=('relax', 'phone'), props=[dict(kind='phone', hand='r')], expr=e,
             look=(0.1 - 0.3 * lift, 0.7 - 0.6 * lift), anchor='hip', blink_v=Hm.blink(t, seed=11))
    f = Wd.glow(f, (J['har'][0], J['har'][1] - 20), 520, Wd.BLUE, power=0.55 * fl, falloff=2.2)
    f = Wd.composite(f, layer)
    f = Wd.grade(f, cold=0.55, sat=0.9)
    f = Wd.finish(f, np.random.default_rng(int(t * 24)), vignette=0.6, grain=1.4)
    im = Image.fromarray(np.asarray(f).clip(0, 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
    return np.asarray(im, np.float32)


def frame(t):
    if t < 3.0:
        return seg_face(t)
    if t < 5.5:
        return seg_walk(t)
    return seg_hook(t)


def main():
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(DUR * FPS)
    cmd = [ff, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    for i in range(n):
        t = i / FPS
        fr = frame(t)
        # dip between segments
        for b in (3.0, 5.5):
            d = abs(t - b)
            if d < 0.15:
                fr = fr * (d / 0.15)
        p.stdin.write(fr.clip(0, 255).astype(np.uint8).tobytes())
        if i % 24 == 0:
            print('frame %d/%d  %.1fs' % (i, n, time.time() - t0), flush=True)
    p.stdin.close()
    p.wait()
    print('saved', OUT, '%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
