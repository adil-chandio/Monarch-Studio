"""Forensic pass/fail gate for AMEER KA KUTTA v2 (kutta2.py picture + mux_kutta2.py audio).

Same instrument as gate_kutta.py (v1) on the DELIVERED file, with the v2 timeline from kutta2.
v2 additions: VO continuity (longest silence inside the voice track), and bed tonality
(spectral flatness of the music+SFX bed, 1-8 kHz; a noise bed would be near 1.0).
    python3 src/gate_kutta2.py [path.mp4]
"""
import json, math, re, subprocess, sys, wave
import numpy as np
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/user/build/kutta/kutta_v2.mp4'
sys.path.insert(0, '/home/user/src')
import kutta2 as TL

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
# v2 recalibration (ledger 61): 32 transitions in 75 s put ~28 % of all frames inside a transition, so the
# whole-film p95 of the motion jerk measures the transition onsets, not the stutter the gate was built for.
# jerk_p95 is now measured on SHOT frames (transition windows +-3 f excluded) with the original 2.0; every
# transition window gets its own cap instead: no step in motion energy larger than the cut cap (8 levels).
import kutta2 as _K
class Q2:
    BOUNDS = [s['t0'] for s in _K.SHOTS[1:]]
    PLAN = _K.PLAN
    TD = {k: _K.tdur(k) for k in _K.PLAN}
shot_mask = np.ones(len(jerk), dtype=bool)
trans_jerk = []
for b_, k_ in zip(Q2.BOUNDS, Q2.PLAN):
    td_ = Q2.TD[k_]
    a_ = max(0, int((b_ - td_ / 2) * FPS) - 3); z_ = min(len(jerk), int((b_ + td_ / 2) * FPS) + 3)
    shot_mask[a_:z_] = False
    trans_jerk.append((round(float(jerk[max(0, a_ - 1):z_].max()), 3), k_, round(b_, 2)))
res['jerk_p95'] = round(float(np.percentile(jerk[shot_mask], 95)), 3)
res['jerk_p95_all_frames'] = round(float(np.percentile(jerk, 95)), 3)
res['trans_jerk_max'] = max(trans_jerk)[0]
res['trans_jerk_max_at'] = f'{max(trans_jerk)[1]}@{max(trans_jerk)[2]}'
res['trans_frames_pct'] = round(100 * float((~shot_mask).mean()), 1)
res['black_edge_frames'] = len(blk_frames)

starts = TL.SCENE_START + [TL.DUR_TOTAL]
worst = (1e9, -1)
for i in range(len(starts) - 1):
    a = int(starts[i] * FPS) + 10         # skip the transition (v2 TD <= .60 at scene starts -> 9 frames each side)
    b = int(starts[i + 1] * FPS) - 10
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
                '-f', 'wav', '/home/user/build/kutta/_gate_kutta.wav'], check=True)
w = wave.open('/home/user/build/kutta/_gate_kutta.wav')
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
vw = wave.open('/home/user/build/kutta/v2/vo_bus.wav')
vo = np.frombuffer(vw.readframes(vw.getnframes()), dtype='<i2').astype(np.float64)[0::2] / 32768.0
vo_hop = 480
vo_rms = np.sqrt(np.array([np.mean(vo[i:i + vo_hop] ** 2) for i in range(0, len(vo) - vo_hop, vo_hop)]) + 1e-12)
vo_db = 20 * np.log10(vo_rms)
voiced = vo_db > -40.0
idx = np.where(voiced)[0]
first, last = idx[0], idx[-1]
gap_run = best_gap = 0
for v in voiced[first:last + 1]:
    gap_run = 0 if v else gap_run + 1
    best_gap = max(best_gap, gap_run)
res['vo_longest_gap_s'] = round(best_gap * vo_hop / 48000.0, 3)
res['vo_first_s'] = round(first * vo_hop / 48000.0, 2)
res['vo_last_s'] = round(last * vo_hop / 48000.0, 2)
mask = np.zeros(len(m), dtype=bool)
mask[:] = np.abs(vo[:len(m)]) > 1e-3
res['vo_coverage_pct'] = round(100 * float(mask.mean()), 1)
# bed tonality: spectral flatness of the music+SFX bed in 1-8 kHz (noise -> ~1, tones -> ~0)
bw = wave.open('/home/user/build/kutta/v2/bed_only.wav')
bed = np.frombuffer(bw.readframes(bw.getnframes()), dtype='<i2').reshape(-1, 2).astype(np.float64).mean(axis=1) / 32768.0
nfft = 4096
win = np.hanning(nfft)
fl = []
fr_ = np.fft.rfftfreq(nfft, 1 / 48000)
band = (fr_ >= 1000) & (fr_ < 8000)
for off in range(0, len(bed) - nfft, nfft // 2):
    seg = bed[off:off + nfft]
    if np.mean(seg ** 2) < 1e-7:
        continue
    P = np.abs(np.fft.rfft(seg * win)) ** 2 + 1e-12
    Pb = P[band]
    fl.append(np.exp(np.mean(np.log(Pb))) / np.mean(Pb))
res['bed_flatness_1k_8k'] = round(float(np.median(fl)), 3)


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
    ('jerk_p95', lambda v: v < 2.0, '< 2.0 (shot frames)'),
    ('trans_jerk_max', lambda v: v < 8.0, '< 8.0 (no step inside a transition larger than the cut cap)'),
    ('lr_corr', lambda v: 0.50 <= v <= 0.80, '0.50-0.80'),
    ('side_mid', lambda v: v > 0.25, '> 0.25'),
    ('all_120_500_pct', lambda v: v < 58, '< 58 %'),
    ('bed_4000_8000_pct', lambda v: v > 1.5, '> 1.5 % (tonal air only; v1 needed 10 %, met by hiss the user rejected)'),
    ('vo_4000_8000_pct', lambda v: v > 5, '> 5 % (speech presence)'),
    ('bed_20_120_pct', lambda v: v < 48, '< 48 % (no boom)'),
    ('decoded_peak_dBFS', lambda v: v <= -1.0, '<= -1.0 dBFS'),
    ('lufs_integrated', lambda v: -12.5 <= v <= -10.5, '-12.5 .. -10.5 LUFS'),
    ('short_term_min_LUFS', lambda v: v > -30, '> -30 LUFS (never breathes out)'),
    ('av_delta', lambda v: v <= 0.1, '<= 0.1 s'),
    ('longest_silence_s', lambda v: v < 1.2, '< 1.2 s'),
    ('vo_longest_gap_s', lambda v: v <= 0.35, '<= 0.35 s (voice flows: clip edges + natural breath only)'),
    ('bed_flatness_1k_8k', lambda v: v < 0.20, '< 0.20 (tonal bed, no hiss)'),
]
bad = 0
for k, fn, txt in GATES:
    ok = fn(res[k])
    bad += not ok
    print(f'{"PASS" if ok else "FAIL"}  {k:22s} {res[k]!s:10s} ({txt})')
print(('ALL GATES PASS' if not bad else f'{bad} FAILURES'))
sys.exit(1 if bad else 0)
