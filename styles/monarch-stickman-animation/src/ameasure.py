"""Quick audio-only metrics on an AAC test mux (same maths as gate_power.py)."""
import math, re, subprocess, sys, wave
import numpy as np, imageio_ffmpeg
sys.path.insert(0, '/home/user/src')
import timeline_power as TL
FF = imageio_ffmpeg.get_ffmpeg_exe()
SRC = sys.argv[1]
subprocess.run([FF, '-y', '-v', 'error', '-i', SRC, '-ac', '2', '-ar', '48000', '-f', 'wav', '/home/user/build/_am.wav'], check=True)
w = wave.open('/home/user/build/_am.wav'); n = w.getnframes()
x = np.frombuffer(w.readframes(n), dtype='<i2').reshape(-1, 2).astype(np.float64) / 32768.0
L, R = x[:, 0], x[:, 1]; m = (L + R) / 2; s = (L - R) / 2
r = {}
r['peak_dBFS'] = round(20 * math.log10(np.abs(x).max()), 2)
r['lr_corr'] = round(float(np.corrcoef(L, R)[0, 1]), 4)
r['side_mid'] = round(float(np.sqrt((s ** 2).mean()) / np.sqrt((m ** 2).mean())), 3)
mask = np.zeros(len(m), dtype=bool)
for i, o in enumerate(TL.VO_AT):
    with wave.open(f'/home/user/assets/p{i + 1}_fit.wav') as vw:
        dur = vw.getnframes() / vw.getframerate()
    mask[int(o * 48000):min(len(m), int((o + dur) * 48000))] = True
def bands(sig, pfx):
    nfft = 1 << 15; acc = np.zeros(nfft // 2 + 1); win = np.hanning(nfft)
    for off in range(0, len(sig) - nfft, nfft):
        acc += np.abs(np.fft.rfft(sig[off:off + nfft] * win)) ** 2
    fr = np.fft.rfftfreq(nfft, 1 / 48000); tot = acc.sum()
    for a, b in ((20, 120), (120, 500), (4000, 8000)):
        r[f'{pfx}_{a}_{b}'] = round(100 * acc[(fr >= a) & (fr < b)].sum() / tot, 1)
bands(m[mask], 'vo'); bands(m[~mask], 'bed'); bands(m, 'all')
eb = subprocess.run([FF, '-nostats', '-i', SRC, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
r['LUFS'] = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', eb)[-1])
r['TP'] = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', eb)[-1])
st = [float(v) for v in re.findall(r' S:\s+(-?[\d.]+)', eb)]; st = [v for v in st if v > -70]
r['ST_min'] = min(st[6:-1])
r['LRA'] = float(re.findall(r'LRA:\s+(-?[\d.]+) LU', eb)[-1])
print(' '.join(f'{k}={v}' for k, v in r.items()))
