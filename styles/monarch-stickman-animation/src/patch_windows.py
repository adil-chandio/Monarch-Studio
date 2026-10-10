"""
patch_windows.py — re-render only the transition windows whose kind changed, measure them, splice them into
the mute master with a frame-accurate filter concat (one crf-16 generation; the mux re-encodes anyway).
usage: python3 src/patch_windows.py kind1,kind2,...   (kinds from respect2.PLAN)
"""
import os, subprocess, sys
import numpy as np, imageio_ffmpeg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import respect2 as Q
FF = imageio_ffmpeg.get_ffmpeg_exe()
B = '/home/user/build'
FPS = 30
kinds = set(sys.argv[1].split(','))
extra = [tuple(int(v) for v in r.split(':')) for r in sys.argv[2].split(',')] if len(sys.argv) > 2 else []
NF = int(round(Q.TL.DUR_TOTAL * FPS)) if hasattr(Q, 'TL') else 2256

# windows (frames) around every boundary of a changed kind, ±2/3 frames of context, merged
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
print('windows:', [(a, z, k, b) for a, z, k, b in merged], 'frames', sum(z - a for a, z, _, _ in merged), flush=True)

# render
outs = []
for n, (a, z, k, b) in enumerate(merged):
    o = f'{B}/r2_w{n:02d}.mp4'
    subprocess.run([sys.executable, f'{os.path.dirname(os.path.abspath(__file__))}/respect2.py', str(a), str(z), o],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    outs.append(o)
    print(f'rendered {o} [{a},{z}) {k} @ {b}', flush=True)


def gray(path, sw=180, sh=320):
    p = subprocess.run([FF, '-v', 'error', '-i', path, '-vf', f'scale={sw}:{sh}', '-pix_fmt', 'gray', '-f', 'rawvideo', '-'],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.uint8).reshape(-1, sh, sw).astype(np.float32)


# measure each window with 3 frames of the untouched master on both sides
master = f'{B}/respect2_mute.mp4'
mg = gray(master)
assert len(mg) == NF, len(mg)
worst = {}
for (a, z, k, b), o in zip(merged, outs):
    wg = gray(o)
    assert len(wg) == z - a, (len(wg), z - a)
    seq = np.concatenate([mg[max(0, a - 3):a], wg, mg[z:z + 3]])
    lu = seq.mean((1, 2)); dl = np.abs(np.diff(lu))
    d = np.array([np.abs(seq[i + 1] - seq[i]).mean() for i in range(len(seq) - 1)])
    jerk = np.abs(np.diff(np.diff(d)))
    print(f'{k:16s} @{b:6.2f}  max_dluma {dl.max():5.2f}  trans_jerk_max {jerk.max():5.2f}  dmax {d.max():5.1f}', flush=True)
    worst[k + '@' + str(b)] = (round(float(dl.max()), 2), round(float(jerk.max()), 2))

# splice — streaming: decode the master once, swap in the window frames, one encoder (no multi-branch buffering)
out = f'{B}/respect2_mute_patched.mp4'
dec = subprocess.Popen([FF, '-v', 'error', '-i', master, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, bufsize=10 ** 7)
enc = subprocess.Popen([FF, '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '30', '-i', '-',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
FS = 1080 * 1920 * 3
wi = 0
i = 0
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
dec.stdout.close(); dec.wait()
enc.stdin.close(); enc.wait()
assert i == NF and wi == len(merged), ('frames', i, 'windows used', wi)
pg = gray(out)
assert len(pg) == NF, ('patched frame count', len(pg))
for f in (0, 300, 1500, NF - 1):
    assert np.abs(pg[f] - mg[f]).mean() < 1.5, ('splice drift', f, float(np.abs(pg[f] - mg[f]).mean()))
os.replace(master, f'{B}/respect2_mute_prev.mp4')
os.replace(out, master)
print('PATCHED ->', master, worst, flush=True)
