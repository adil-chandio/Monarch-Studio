"""Forensic pass/fail gate for the full 16:9 episode."""
import json, math, subprocess, sys, wave
import numpy as np
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/user/stickman_wide_episode_full.mp4'
sys.path.insert(0, '/home/user/src')
import wide_full as WF

W, H, FPS = 1920, 1080, 30
SW, SH = 320, 180                      # downscaled probe
res = {}

# ── video: decode greyscale thumbnails ──────────────────────────────────
p = subprocess.Popen(
    [FF, '-v', 'error', '-i', SRC, '-vf', f'scale={SW}:{SH}',
     '-pix_fmt', 'gray', '-f', 'rawvideo', '-'],
    stdout=subprocess.PIPE, bufsize=10 ** 8)
fs = SW * SH
prev = None
lum, ddiff = [], []
nf = 0
while True:
    b = p.stdout.read(fs)
    if len(b) < fs:
        break
    f = np.frombuffer(b, dtype=np.uint8).reshape(SH, SW).astype(np.float32)
    if prev is not None:
        ddiff.append(float(np.mean(np.abs(f - prev))))
    lum.append(float(f.mean()))
    prev = f
    nf += 1
p.stdout.close(); p.wait()

d = np.array(ddiff)
lu = np.array(lum)
res['frames'] = nf
res['identical_frames'] = int(np.sum(d == 0.0))
res['max_dluma'] = float(np.max(np.abs(np.diff(lu))))
vel = d
jerk = np.abs(np.diff(np.diff(vel)))
res['jerk_p95'] = float(np.percentile(jerk, 95))

# per-scene p10 frame diff (motion presence inside every scene)
starts = WF.SCENE_START + [WF.DUR_TOTAL]
worst = (1e9, -1)
for i in range(len(starts) - 1):
    a = int(starts[i] * FPS) + 2
    b = int(starts[i + 1] * FPS) - 2
    if b - a < 6:
        continue
    seg = d[a:min(b, len(d))]
    if len(seg) == 0:
        continue
    v = float(np.percentile(seg, 10))
    if v < worst[0]:
        worst = (v, i + 1)
res['min_scene_p10'] = round(worst[0], 4)
res['min_scene_p10_scene'] = worst[1]

# ── audio: decode the delivered AAC back to PCM ─────────────────────────
subprocess.run([FF, '-y', '-v', 'error', '-i', SRC, '-ac', '2', '-ar', '48000',
                '-f', 'wav', '/home/user/build/_gate.wav'], check=True)
w = wave.open('/home/user/build/_gate.wav')
n = w.getnframes()
x = np.frombuffer(w.readframes(n), dtype='<i2').reshape(-1, 2).astype(np.float64) / 32768.0
L, R = x[:, 0], x[:, 1]
res['audio_dur'] = round(n / 48000.0, 3)
res['video_dur'] = round(nf / FPS, 3)
res['av_delta'] = round(abs(res['audio_dur'] - res['video_dur']), 3)
res['decoded_peak_dBFS'] = round(20 * math.log10(max(np.max(np.abs(x)), 1e-9)), 2)
res['lr_corr'] = round(float(np.corrcoef(L, R)[0, 1]), 4)
m = (L + R) / 2; s = (L - R) / 2
res['side_mid'] = round(float(np.sqrt((s ** 2).mean()) / np.sqrt((m ** 2).mean())), 3)

# Spectral balance, measured separately over narration and sound-design
# windows. A single whole-file number is meaningless here: voice covers
# 93.5 % of the runtime, so a whole-file 4-8 kHz share grades the VO's
# sibilance, not the bed's air.
VO_CLIPS = ['w1', 'w2', 'w3', 'w4', 'w5', 'w6'] + [f'b{i}' for i in range(1, 11)]
VO_OFFS = [0.350, 7.250, 13.350, 19.550, 25.050, 37.750, 53.450, 74.110,
           96.700, 117.470, 135.730, 155.190, 178.490, 195.890, 215.920,
           237.940]
mask = np.zeros(len(m), dtype=bool)
for c, o in zip(VO_CLIPS, VO_OFFS):
    raw = subprocess.run([FF, '-v', 'error', '-i', f'/home/user/assets/{c}.mp3',
                          '-f', 's16le', '-ac', '1', '-ar', '48000', '-'],
                         capture_output=True).stdout
    dur = len(raw) / 2 / 48000
    mask[int(o * 48000):int((o + dur) * 48000)] = True
res['vo_coverage_pct'] = round(100 * float(mask.mean()), 1)


def bands(sig, pfx):
    nfft = 1 << 15
    acc = np.zeros(nfft // 2 + 1)
    win = np.hanning(nfft)
    for off in range(0, len(sig) - nfft, nfft):
        acc += np.abs(np.fft.rfft(sig[off:off + nfft] * win)) ** 2
    fr = np.fft.rfftfreq(nfft, 1 / 48000)
    tot = max(acc.sum(), 1e-30)
    for a, b in ((20, 120), (120, 500), (4000, 8000)):
        res[f'{pfx}_{a}_{b}_pct'] = round(100 * acc[(fr >= a) & (fr < b)].sum() / tot, 1)


bands(m[mask], 'vo')
bands(m[~mask], 'bed')
bands(m, 'all')

# short-term loudness floor: no dead air longer than 1.2 s
blk = 48000 // 2
rms = np.sqrt(np.convolve(m ** 2, np.ones(blk) / blk, 'valid'))
quiet = rms < 10 ** (-60 / 20)
run = best = 0
for q in quiet:
    run = run + 1 if q else 0
    best = max(best, run)
res['longest_silence_s'] = round(best / 48000.0, 2)

print(json.dumps(res, indent=1))

GATES = [
    ('identical_frames', lambda v: v == 0, '== 0'),
    ('max_dluma', lambda v: v < 8, '< 8'),
    ('min_scene_p10', lambda v: v > 0.12, '> 0.12'),
    ('jerk_p95', lambda v: v < 2.0, '< 2.0'),
    ('lr_corr', lambda v: 0.55 <= v <= 0.80, '0.55-0.80'),
    ('side_mid', lambda v: v > 0.25, '> 0.25'),
    ('all_120_500_pct', lambda v: v < 58, '< 58 %'),
    ('bed_4000_8000_pct', lambda v: v > 10, '> 10 % (sound-design air)'),
    ('vo_4000_8000_pct', lambda v: v > 5, '> 5 % (speech presence)'),
    ('bed_20_120_pct', lambda v: v < 48, '< 48 % (no boom)'),
    ('decoded_peak_dBFS', lambda v: v <= -1.0, '<= -1.0 dBFS'),
    ('av_delta', lambda v: v <= 0.1, '<= 0.1 s'),
    ('longest_silence_s', lambda v: v < 1.2, '< 1.2 s'),
]
bad = 0
for k, fn, txt in GATES:
    ok = fn(res[k])
    bad += not ok
    print(f'{"PASS" if ok else "FAIL"}  {k:22s} {res[k]!s:10s} ({txt})')
print(('ALL GATES PASS' if not bad else f'{bad} FAILURES'))
