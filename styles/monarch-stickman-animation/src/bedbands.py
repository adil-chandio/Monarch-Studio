import sys, wave, numpy as np
sys.path.insert(0, '/home/user/src'); import timeline_power as TL
w = wave.open('/home/user/build/asmr_bed_power.wav'); n = w.getnframes()
x = np.frombuffer(w.readframes(n), dtype='<i2').reshape(-1, 2).astype(np.float64) / 32768.0
m = x.mean(1)
mask = np.zeros(len(m), dtype=bool)
for i, o in enumerate(TL.VO_AT):
    with wave.open(f'/home/user/assets/p{i + 1}_fit.wav') as vw: dur = vw.getnframes() / vw.getframerate()
    mask[int(o * 48000):min(len(m), int((o + dur) * 48000))] = True
def bands(sig):
    nfft = 1 << 15; acc = np.zeros(nfft // 2 + 1); win = np.hanning(nfft)
    for off in range(0, len(sig) - nfft, nfft): acc += np.abs(np.fft.rfft(sig[off:off + nfft] * win)) ** 2
    fr = np.fft.rfftfreq(nfft, 1 / 48000); tot = acc.sum()
    return {f'{a}-{b}': round(100 * acc[(fr >= a) & (fr < b)].sum() / tot, 1) for a, b in ((20,120),(120,500),(500,2000),(2000,4000),(4000,8000),(8000,16000))}
print('bed-only windows', (~mask).sum()/48000, 's', bands(m[~mask]))
print('whole bed       ', bands(m))
