"""mux_kutta.py — audio + mux for "AMEER KA KUTTA" (kutta.py picture, 23.7 s, 9:16).

Procedural (numpy) bed, no sample library:
  * warm pad (A minor chord, slow LFO) under the whole film, decorrelated L/R for width
  * a bell on each chapter start (gold / teal / royal / coral pitch), a crown shimmer on the drop,
    a metallic coin ping on the BRANDED bowl, a low thud on GAREEB, soft sparkle ticks (air)
  * a filtered-noise whoosh on every transition (same boundaries and TD as the picture)
  * the bed ducks under the voice (envelope sidechain, numpy)
VO = the four measured Urdu clips (voice-03, ur-PK) at kutta.VO_AT, tone-shaped by ffmpeg EQ
(highpass 90, mud cut at 300 Hz, presence lift at 5 kHz).
Loudness: loudnorm I=-11 TP=-1.6 then alimiter (0.71), like the SHADE chain.

Run:  python3 src/mux_kutta.py        -> /home/user/build/kutta/mix_kutta.wav (audio only)
      python3 src/mux_kutta.py mux    -> /home/user/build/kutta/kutta_v1.mp4 (needs kutta_mute.mp4)
"""
import os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kutta as K
import respect2 as R2

SR = 48000
OUT_DIR = '/home/user/build/kutta'
VO_DIR = f'{OUT_DIR}/vo'
N = int(round((K.DUR_TOTAL + 0.5) * SR))


def _ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def read_wav(p):
    w = wave.open(p)
    sr, n = w.getframerate(), w.getnframes()
    a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    if sr != SR:
        x_old = np.linspace(0, 1, len(a))
        x_new = np.linspace(0, 1, int(len(a) * SR / sr))
        a = np.interp(x_new, x_old, a).astype(np.float32)
    return a


def write_wav(p, st):
    st = np.clip(st, -1, 1)
    pcm = (st * 32767).astype(np.int16)
    w = wave.open(p, 'wb')
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(np.ascontiguousarray(pcm).tobytes())
    w.close()


def read_stereo(p):
    w = wave.open(p)
    n = w.getnframes()
    x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32).reshape(-1, 2) / 32768.0
    return x


def eq_vo(src, dst):
    """voice tone: highpass 90, mud cut at 300 Hz, presence lift at 5 kHz (speech 4-8 kHz share)."""
    af = ('highpass=f=130,equalizer=f=220:t=q:w=1.4:g=-5,equalizer=f=380:t=q:w=1.2:g=-2,'
          'equalizer=f=5000:t=q:w=1.5:g=6,treble=g=3:f=8000')
    subprocess.run([_ffmpeg(), '-y', '-v', 'error', '-i', src, '-af', af, '-ar', str(SR), dst], check=True)


def t_axis():
    return np.arange(N, dtype=np.float32) / SR


def pad_layer(t, phase=0.0):
    chord = [110.0, 130.81, 164.81, 196.0, 246.94]          # A2 C3 E3 G3 B3
    out = np.zeros(N, np.float32)
    for i, f in enumerate(chord):
        vib = 1 + 0.0025 * np.sin(2 * np.pi * (0.2 + 0.05 * i) * t)
        out += (0.6 * np.sin(2 * np.pi * f * vib * t + phase + i) + 0.25 * np.sin(2 * np.pi * 2 * f * t)) * (0.7 / (i + 1.5))
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * t)
    fade = np.clip(t / 1.2, 0, 1) * np.clip((K.DUR_TOTAL + 0.3 - t) / 0.8, 0, 1)
    return out * lfo * fade * 0.030


def _add(out, i0, sig):
    n = min(len(sig), N - i0)
    if n > 0 and i0 >= 0:
        out[i0:i0 + n] += sig[:n]


def bell(out, t0, f, amp, dur=1.6):
    n = int(dur * SR)
    tt = np.arange(n, dtype=np.float32) / SR
    env = np.exp(-tt * 3.2) * np.clip(tt / .004, 0, 1)
    sig = (np.sin(2 * np.pi * f * tt) + .35 * np.sin(2 * np.pi * 2.76 * f * tt) + .15 * np.sin(2 * np.pi * 5.4 * f * tt))
    _add(out, int(t0 * SR), amp * env * sig)


def ping(out, t0, amp=0.10):
    n = int(0.7 * SR)
    tt = np.arange(n, dtype=np.float32) / SR
    env = np.exp(-tt * 9.0)
    _add(out, int(t0 * SR), amp * env * (np.sin(2 * np.pi * 3100 * tt) + .5 * np.sin(2 * np.pi * 4650 * tt)))


def thud(out, t0, amp=0.16):
    n = int(0.9 * SR)
    tt = np.arange(n, dtype=np.float32) / SR
    f = 96 * np.exp(-tt * 6.0) + 40
    ph = 2 * np.pi * np.cumsum(f) / SR
    _add(out, int(t0 * SR), amp * np.exp(-tt * 5.0) * np.sin(ph))


def whoosh(out, t0, dur, amp=0.09, seed=0):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = rng.normal(0, 1, n).astype(np.float32)
    k = 48
    lp = np.convolve(x, np.ones(k, np.float32) / k, mode='same')
    hp = x - lp
    tt = np.linspace(0, 1, n, dtype=np.float32)
    env = np.sin(np.pi * tt) ** 2 * (0.4 + 0.6 * tt)
    _add(out, int(t0 * SR), amp * hp * env)


def sparkle(out, t0, amp=0.018):
    n = int(0.35 * SR)
    tt = np.arange(n, dtype=np.float32) / SR
    env = np.exp(-tt * 22.0)
    _add(out, int(t0 * SR), amp * env * (np.sin(2 * np.pi * 6400 * tt) + .6 * np.sin(2 * np.pi * 8900 * tt)))


def air(out):
    """a very low high-passed hiss under the whole film (room air, 4-8 kHz body)."""
    rng = np.random.default_rng(99)
    x = rng.normal(0, 1, N).astype(np.float32)
    k = 6
    lp = np.convolve(x, np.ones(k, np.float32) / k, mode='same')
    out += 0.036 * (x - lp) * 2.0


def bed_mono():
    t = t_axis()
    out = pad_layer(t).astype(np.float32)
    air(out)
    for ch, f in enumerate([523.25, 659.25, 783.99, 293.66]):   # C5, E5, G5, D4 chapter bells
        bell(out, K.SCENE_START[ch] + .02, f, 0.10 if ch != 3 else 0.07)
    thud(out, K.SCENE_START[3] + .02, 0.10)            # GAREEB: a low thud on the first cut
    bell(out, 14.78 + .55, 1567.98, 0.08, dur=2.4)     # crown drop shimmer
    bell(out, 14.78 + .75, 2093.0, 0.05, dur=2.2)
    ping(out, 8.20, 0.10)                              # BRANDED coin ping on the bowl shot
    for tt_ in np.arange(0.9, K.DUR_TOTAL, 1.9):       # sparkle ticks (air)
        sparkle(out, float(tt_), 0.03)
    for b in range(K.N_SHOTS - 1):
        bt = K.SHOTS[b + 1]['t0']
        td = R2.TD[K.PLAN[b]]
        whoosh(out, bt - td / 2, td, amp=0.10, seed=b + 1)
    return out


def sidechain(bed_sig, vo_mono, depth=0.55):
    blk = 480
    nb = int(np.ceil(len(vo_mono) / blk))
    pad = np.zeros(nb * blk, np.float32)
    pad[:len(vo_mono)] = vo_mono
    rms = np.sqrt((pad.reshape(nb, blk) ** 2).mean(axis=1))
    env = np.zeros(nb, np.float32)
    a_att, a_rel = np.exp(-1 / 2.0), np.exp(-1 / 14.0)        # attack ~10 ms, release ~260 ms in blocks
    e = 0.0
    for i, r in enumerate(rms):
        a = a_att if r > e else a_rel
        e = a * e + (1 - a) * r
        env[i] = e
    g = 1 - depth * np.clip(env / 0.06, 0, 1)
    gfull = np.repeat(g, blk)
    gfull = gfull[:len(bed_sig)]
    if len(gfull) < len(bed_sig):
        gfull = np.concatenate([gfull, np.ones(len(bed_sig) - len(gfull), np.float32)])
    return bed_sig * gfull


def build():
    os.makedirs(OUT_DIR, exist_ok=True)
    # voice: place clips, then tone-shape them with ffmpeg
    vo_raw = np.zeros(N, np.float32)
    for i in range(4):
        clip = read_wav(f'{VO_DIR}/k{i + 1}.wav')
        s0 = int(round(K.VO_AT[i] * SR))
        n = min(len(clip), N - s0)
        vo_raw[s0:s0 + n] += clip[:n]
    write_wav(f'{OUT_DIR}/vo_bus.wav', np.stack([vo_raw, vo_raw], 1))
    eq_vo(f'{OUT_DIR}/vo_bus.wav', f'{OUT_DIR}/vo_eq.wav')
    vo_st = read_stereo(f'{OUT_DIR}/vo_eq.wav')
    vo_st = np.pad(vo_st, ((0, max(0, N - len(vo_st))), (0, 0)))[:N]
    vo_m = (vo_st[:, 0] + vo_st[:, 1]) / 2
    # bed: mono synth, then a decorrelated right channel (15 ms + gain) for width; sidechain both
    b = bed_mono()
    bl = sidechain(b, vo_m)
    br = sidechain(np.roll(b, 720) * 0.92, vo_m)
    bed_st = np.stack([bl, br], 1)
    write_wav(f'{OUT_DIR}/bed_kutta.wav', bed_st)
    mix = vo_st * 1.0 + bed_st * 0.85
    write_wav(f'{OUT_DIR}/mix_kutta.wav', mix)
    return f'{OUT_DIR}/mix_kutta.wav'


def mux(mix_path, mute, out):
    af = 'extrastereo=m=1.2,loudnorm=I=-11:TP=-1.6:LRA=9,alimiter=limit=0.71:level=disabled'
    cmd = [_ffmpeg(), '-y', '-v', 'error', '-i', mute, '-i', mix_path,
           '-filter_complex', f'[1:a]{af}[a]', '-map', '0:v', '-map', '[a]',
           '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-maxrate', '4000k', '-bufsize', '8000k',
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
           '-t', f'{K.DUR_TOTAL:.3f}', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)


if __name__ == '__main__':
    mp = build()
    print('mix ready', mp)
    if len(sys.argv) > 1 and sys.argv[1] == 'mux':
        mux(mp, f'{OUT_DIR}/kutta_mute.mp4', f'{OUT_DIR}/kutta_v1.mp4')
        print('muxed', f'{OUT_DIR}/kutta_v1.mp4')
