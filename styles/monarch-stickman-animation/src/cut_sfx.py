import subprocess, json, os
FF = open('/home/user/build/ff_path.txt').read().strip()
SRC = '/home/user/build/sfx_src'
OUT = '/home/user/build/sfx_lib2'
VIDS = {1: 'VID_20261011_031631_368.mp4', 2: 'VID_20261011_031646_165.mp4', 3: 'VID_20261011_031700_458.mp4', 4: 'VID_20261011_031727_691.mp4'}
# video 1 = labelled by promo title (names only; not verified by ear)
V1 = {'crack_flash': (0.43, 0.90), 'digital_click': (2.14, 2.40), 'synth_sparkle': (7.00, 7.29), 'lighter_ignite': (8.77, 9.28),
      'riser_click': (11.48, 12.46), 'gleam': (16.22, 17.45), 'conjure_charge': (18.34, 19.54), 'modern_shutter': (21.23, 21.58)}
# unlabelled windows, named by source video and index (labels assigned later by feature analysis)
V2 = {'v2_a': (0.08, 0.77), 'v2_b': (1.17, 1.57), 'v2_c': (2.59, 3.10), 'v2_d': (3.44, 3.98), 'v2_e': (4.71, 5.06), 'v2_f': (11.21, 12.11)}
V3 = {'v3_a': (0.13, 1.02), 'v3_b': (1.65, 2.06), 'v3_c': (2.35, 5.39), 'v3_d': (5.70, 8.84), 'v3_e': (9.11, 9.22), 'v3_f': (10.98, 11.88)}
V4 = {'v4_a': (0.06, 4.37), 'v4_b': (4.76, 5.16), 'v4_c': (5.46, 5.57), 'v4_d': (6.11, 6.72), 'v4_e': (8.40, 9.63), 'v4_f': (10.54, 11.43)}
jobs = [(1, V1), (2, V2), (3, V3), (4, V4)]
for vid, segs in jobs:
    for name, (a, b) in segs.items():
        pad = 0.02
        out = f'{OUT}/{name}.wav'
        subprocess.run([FF, '-y', '-v', 'error', '-ss', f'{max(0,a-pad):.3f}', '-t', f'{b-a+2*pad:.3f}', '-i', f'{SRC}/{VIDS[vid]}',
                        '-vn', '-ac', '2', '-ar', '48000', '-c:a', 'pcm_s16le', out], check=True)
print(sorted(os.listdir(OUT)))
