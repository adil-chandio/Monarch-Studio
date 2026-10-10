"""Forensic pass/fail gate for the SHADE remake of the 42 s POWERFUL MAN short.
Identical to gate_power.py except the black-sliver detector: the hybrid look
has a deliberate charcoal wedge (38,36,41) on the top/left edges, so a sliver
is now "an edge line that is >= 95 % below 12/255" (a real transform sliver is
0; the charcoal never decodes under ~28 even with grain + x264).
Same instrument as gate_full.py (measures the DELIVERED file, never the
intermediates); adds the loudness pair (integrated LUFS, short-term floor)
from VIDEO_V9_NOTES so the vertical scorecard matches the earlier shorts.
    python3 src/gate_power.py [path.mp4]
"""
import json, math, re, subprocess, sys, wave
import numpy as np
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/user/shade_respect_90s.mp4'
sys.path.insert(0, '/home/user/src')
import timeline_respect as TL

W, H, FPS = 1080, 1920, 30
SW, SH = 180, 320                      # downscaled probe
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
blk_frames = []                        # frames with a (near) black sliver on any edge
while True:
    b = p.stdout.read(fs)
    if len(b) < fs:
        break
    f = np.frombuffer(b, dtype=np.uint8).reshape(SH, SW).astype(np.float32)
    if prev is not None:
        ddiff.append(float(np.mean(np.abs(f - prev))))
    lum.append(float(f.mean()))
    if any((edge < 12).mean() >= 0.95 for edge in (f[0], f[-1], f[:, 0], f[:, -1])):
        blk_frames.append(nf)
    prev = f
    nf += 1
p.stdout.close(); p.wait()

d = np.array(ddiff)
lu = np.array(lum)
res['frames'] = nf
res['identical_frames'] = int(np.sum(d == 0.0))
res['max_dluma'] = round(float(np.max(np.abs(np.diff(lu)))), 3)
res['frames_dluma_gt8'] = int(np.sum(np.abs(np.diff(lu)) > 8))
jerk = np.abs(np.diff(np.diff(d)))
res['jerk_p95'] = round(float(np.percentile(jerk, 95)), 3)
res['black_edge_frames'] = len(blk_frames)

starts = TL.SCENE_START + [TL.DUR_TOTAL]
worst = (1e9, -1)
for i in range(len(starts) - 1):
    a = int(starts[i] * FPS) + 8          # skip the swipe (TDUR .46 -> 7 frames each side)
    b = int(starts[i + 1] * FPS) - 8
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
                '-f', 'wav', '/home/user/build/_gate_respect.wav'], check=True)
w = wave.open('/home/user/build/_gate_respect.wav')
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

# VO mask from the fitted clips at their timeline offsets
mask = np.zeros(len(m), dtype=bool)
for i, o in enumerate(TL.VO_AT):
    with wave.open(f'/home/user/assets/r{i + 1}_fit.wav') as vw:
        dur = vw.getnframes() / vw.getframerate()
    mask[int(o * 48000):min(len(m), int((o + dur) * 48000))] = True
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

# EBU R128 on the delivered file: integrated, true peak, short-term minimum
eb = subprocess.run([FF, '-nostats', '-i', SRC, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                    capture_output=True, text=True).stderr
res['lufs_integrated'] = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', eb)[-1])
res['true_peak_dBTP'] = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', eb)[-1])
st = [float(v) for v in re.findall(r' S:\s+(-?[\d.]+)', eb)]
st = [v for v in st if v > -70]
res['short_term_min_LUFS'] = round(min(st[6:-1]) if len(st) > 8 else min(st), 1)  # skip the 3 s warm-up

print(json.dumps(res, indent=1))

GATES = [
    ('frames', lambda v: v == int(round(TL.DUR_TOTAL * FPS)), f'== {int(round(TL.DUR_TOTAL * FPS))}'),
    ('identical_frames', lambda v: v == 0, '== 0'),
    ('max_dluma', lambda v: v < 8, '< 8'),
    ('frames_dluma_gt8', lambda v: v == 0, '== 0'),
    ('black_edge_frames', lambda v: v == 0, '== 0 (no slivers)'),
    ('min_scene_p10', lambda v: v > 0.12, '> 0.12'),
    ('jerk_p95', lambda v: v < 2.0, '< 2.0'),
    ('lr_corr', lambda v: 0.55 <= v <= 0.80, '0.55-0.80'),
    ('side_mid', lambda v: v > 0.25, '> 0.25'),
    ('all_120_500_pct', lambda v: v < 58, '< 58 %'),
    ('bed_4000_8000_pct', lambda v: v > 10, '> 10 % (sound-design air)'),
    ('vo_4000_8000_pct', lambda v: v > 5, '> 5 % (speech presence)'),
    ('bed_20_120_pct', lambda v: v < 48, '< 48 % (no boom)'),
    ('decoded_peak_dBFS', lambda v: v <= -1.0, '<= -1.0 dBFS'),
    ('lufs_integrated', lambda v: -12.5 <= v <= -10.5, '-12.5 .. -10.5 LUFS'),
    ('short_term_min_LUFS', lambda v: v > -30, '> -30 LUFS (never breathes out)'),
    ('av_delta', lambda v: v <= 0.1, '<= 0.1 s'),
    ('longest_silence_s', lambda v: v < 1.2, '< 1.2 s'),
]
bad = 0
for k, fn, txt in GATES:
    ok = fn(res[k])
    bad += not ok
    print(f'{"PASS" if ok else "FAIL"}  {k:22s} {res[k]!s:10s} ({txt})')
print(('ALL GATES PASS' if not bad else f'{bad} FAILURES'))
sys.exit(1 if bad else 0)
