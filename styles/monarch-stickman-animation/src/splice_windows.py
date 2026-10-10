"""
splice_windows.py — memory-light splice: stream the mute master through one encoder, swapping in the already
rendered window files build/r2_wNN.mp4 (same window list as patch_windows.py). No full-film arrays in RAM.
usage: python3 src/splice_windows.py kind1,kind2,... [a:z,a:z]
"""
import os, subprocess, sys
import numpy as np, imageio_ffmpeg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import respect2 as Q
FF = imageio_ffmpeg.get_ffmpeg_exe()
B = '/home/user/build'
FPS = 30
NF = 2256
kinds = set(sys.argv[1].split(','))
extra = [tuple(int(v) for v in r.split(':')) for r in sys.argv[2].split(',')] if len(sys.argv) > 2 else []
rng = []
for b, k in zip(Q.BOUNDS, Q.PLAN):
    if k in kinds:
        td = Q.TD[k]
        rng.append([max(0, int((b - td / 2) * FPS) - 2), min(NF, int((b + td / 2) * FPS) + 3), k, round(b, 2)])
for a, z in extra:
    rng.append([a, z, 'extra', 0])
rng.sort()
merged = []
for r in rng:
    if merged and r[0] <= merged[-1][1]:
        merged[-1][1] = max(merged[-1][1], r[1]); merged[-1][2] += '+' + r[2]
    else:
        merged.append(r)
outs = [f'{B}/r2_w{n:02d}.mp4' for n in range(len(merged))]
for o in outs:
    assert os.path.exists(o), o
print('windows', [(a, z, k) for a, z, k, _ in merged], flush=True)

master = f'{B}/respect2_mute.mp4'
out = f'{B}/respect2_mute_patched.mp4'
FS = 1080 * 1920 * 3
dec = subprocess.Popen([FF, '-v', 'error', '-i', master, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, bufsize=FS)
enc = subprocess.Popen([FF, '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '30', '-i', '-',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-threads', '2', out], stdin=subprocess.PIPE)
wi, i, wr = 0, 0, None
while True:
    buf = dec.stdout.read(FS)
    if len(buf) < FS:
        break
    if wi < len(merged) and merged[wi][0] <= i < merged[wi][1]:
        a, z, k, b = merged[wi]
        if i == a:
            wr = subprocess.run([FF, '-v', 'error', '-i', outs[wi], '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
            assert len(wr) == FS * (z - a), ('window frames', k, len(wr) // FS, z - a)
        enc.stdin.write(wr[(i - a) * FS:(i - a + 1) * FS])
        if i == z - 1:
            wi += 1; wr = None
    else:
        enc.stdin.write(buf)
    i += 1
    if i % 300 == 0:
        print('frame', i, flush=True)
dec.stdout.close(); dec.wait()
enc.stdin.close(); enc.wait()
assert i == NF and wi == len(merged), ('frames', i, 'windows used', wi)
# light verification: frame count + per-window motion check at 90x160 uint8 (whole film = 32 MB)
p = subprocess.run([FF, '-v', 'error', '-i', out, '-vf', 'scale=180:320', '-pix_fmt', 'gray', '-f', 'rawvideo', '-'], capture_output=True, check=True)
g = np.frombuffer(p.stdout, dtype=np.uint8).reshape(-1, 320, 180)
assert len(g) == NF, ('patched frame count', len(g))
lu = g.astype(np.float32).mean((1, 2)); dl = np.abs(np.diff(lu))
d = np.array([np.abs(g[j + 1].astype(np.int16) - g[j].astype(np.int16)).mean() for j in range(len(g) - 1)])
jerk = np.abs(np.diff(np.diff(d)))
worst = []
for b, k in zip(Q.BOUNDS, Q.PLAN):
    td = Q.TD[k]; a = max(0, int((b - td / 2) * FPS) - 3); z = min(len(jerk), int((b + td / 2) * FPS) + 3)
    worst.append((round(float(jerk[max(0, a - 1):z].max()), 2), round(float(dl[a:z + 1].max()), 2), k, round(b, 2)))
worst.sort(reverse=True)
print('max_dluma', dl.max().round(2), 'frames>8', int((dl > 8).sum()), 'worst transitions (jerk, dluma, kind, t):', worst[:6], flush=True)
os.replace(master, f'{B}/respect2_mute_prev.mp4')
os.replace(out, master)
print('PATCHED ->', master, flush=True)
