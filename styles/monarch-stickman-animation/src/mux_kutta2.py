"""mux_kutta2.py — audio + mux for "AMEER KA KUTTA" v2 (kutta2.py picture, 20.1 s, 9:16).

Replaces the v1 bed (no pad-hiss, no filtered-noise whooshes, no radio-type buffer).
Everything is procedural numpy/ffmpeg, all TONAL:
  * BG music  : 96 BPM, A minor. Pad (Am-F-C-G, detuned L/R), bass pluck, soft kick,
                tonal 9 kHz ticks, a hooked lead melody (dotted-eighth echo), and a 16th-note
                shimmer arp that only lives in the RAJA chapter. Each chapter has its own layer mix,
                crossfaded over 0.4 s, so the BG changes with the picture instead of looping one bed.
  * SFX       : premium ASMR-style tonal foley from kutta2.cue_list(): leash jingle, footsteps,
                door creak / thunk, dog hop, engine (harmonic series), AC click + whir, coin ping,
                bell chime, tonal sweep whooshes (one per transition, length = transition TD).
  * VO        : the four fitted ur-PK clips (voice-03) at kutta2.VO_AT, EQ'd by ffmpeg
                (highpass 90, mud cut 300 Hz, presence 5 kHz, light compression). Continuous: each
                clip starts where the previous one ends (see kutta2.LEAD/TAIL).
  * Mix       : music ducks under the voice (envelope sidechain, numpy). Loudness: ffmpeg loudnorm
                I=-12, TP=-1.5. No noise generator is used anywhere in this file.

Run:
  python3 src/mux_kutta2.py            -> build/kutta/v2/mix_kutta2.wav, vo_bus.wav, bed_only.wav
  python3 src/mux_kutta2.py mux        -> build/kutta/kutta_v2.mp4 (needs shard0.mp4 + shard1.mp4)
"""
import os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kutta2 as K

SR = 48000
OUT = '/home/user/build/kutta'
VO_DIR = f'{OUT}/vo'
WORK = f'{OUT}/v2'
N = int(round((K.DUR_TOTAL + 0.5) * SR))
BPM = 96
BEAT = 60.0 / BPM
BAR = 4 * BEAT
TOTAL_S = N / SR


def _ff():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def mtof(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def tt(d):
    return np.arange(int(round(d * SR))) / SR


class Bus:
    def __init__(self):
        self.L = np.zeros(N, np.float32)
        self.R = np.zeros(N, np.float32)

    def add(self, sig, t0, pan=0.0, gain=1.0):
        i0 = int(round(t0 * SR))
        if i0 < 0:
            sig = sig[-i0:]
            i0 = 0
        n = min(len(sig), N - i0)
        if n <= 0:
            return
        ang = (pan + 1.0) * np.pi / 4.0
        self.L[i0:i0 + n] += gain * np.cos(ang) * sig[:n]
        self.R[i0:i0 + n] += gain * np.sin(ang) * sig[:n]


# ───────────────────────────── voices (all tonal)
def tone(f, d, amp=1.0, tau=0.3, a=0.004, harm=(1.0,)):
    t = tt(d)
    s = sum(h * np.sin(2 * np.pi * f * (k + 1) * t) for k, h in enumerate(harm))
    e = np.exp(-t / tau) * np.minimum(1.0, t / a)
    return (amp * s * e).astype(np.float32)


def sweep(f0, f1, d, amp=1.0, shape='exp'):
    t = tt(d)
    f = f0 * (f1 / f0) ** (t / d) if shape == 'exp' else f0 + (f1 - f0) * t / d
    return (amp * np.sin(2 * np.pi * np.cumsum(f) / SR)).astype(np.float32)


def kick(amp=0.5, d=0.32):
    t = tt(d)
    f = 44 + 96 * np.exp(-t / 0.022)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (amp * np.sin(ph) * np.exp(-t / 0.10) * np.minimum(1, t / 0.002)).astype(np.float32)


def pad_chord(freqs, d, amp):
    """soft pad: 3 harmonics per voice, L/R detuned ±0.18 % for width; slow attack, long release."""
    t = tt(d)
    env = np.minimum(1, t / 0.45) * np.minimum(1, (d - t) / 0.7)
    L = np.zeros_like(t); R = np.zeros_like(t)
    for f in freqs:
        for k in (1, 2, 3):
            w = 1.0 / k
            L += w * np.sin(2 * np.pi * f * (1 - .0055) * k * t + .6 * k)
            R += w * np.sin(2 * np.pi * f * (1 + .0055) * k * t + 1.9 * k)
    s = amp / max(1, len(freqs)) * env
    return (L * s).astype(np.float32), (R * s).astype(np.float32)


def bell(f, d, amp, tau):
    return tone(f, d, amp, tau, harm=(1.0, 2.0, 2.76, 5.40))


# ───────────────────────────── musical layers
CHORDS = [  # (pad voicing midi, bass root midi, arp tones midi)
    ([57, 60, 64], 45, [69, 72, 76, 81]),   # Am
    ([53, 57, 60], 41, [65, 69, 72, 77]),   # F
    ([55, 60, 64], 36, [67, 72, 76, 79]),   # C (over G)
    ([55, 59, 62], 43, [67, 71, 74, 79]),   # G
]
# hooked lead, one bar = 4 beats: (beat, midi, length in beats)
LEAD = [
    [(0, 76, 1), (1, 81, .5), (1.5, 84, .5), (2, 83, 1), (3, 81, 1)],   # Am
    [(0, 77, 1), (1, 81, .5), (1.5, 84, .5), (2, 81, 1), (3, 79, 1)],   # F
    [(0, 79, 1), (1, 76, .5), (1.5, 79, .5), (2, 84, 1), (3, 83, 1)],   # C
    [(0, 74, 1), (1, 79, .5), (1.5, 83, .5), (2, 81, 1), (3, 76, 1)],   # G
]

# per-chapter layer gains: pad, bass, kick, tick, lead, arp
LAYER_NAMES = ['pad', 'bass', 'kick', 'tick', 'lead', 'arp']
CH_GAINS = [
    [0.75, 0.00, 0.00, 0.35, 0.55, 0.00],   # ch1 HOOK: airy pad, lead enters soft
    [0.65, 0.65, 0.55, 0.55, 0.90, 0.00],   # ch2 LUXURY: groove up
    [0.80, 0.80, 0.85, 0.65, 0.85, 0.85],   # ch3 RAJA: full, shimmer arp
    [0.55, 0.45, 0.00, 0.25, 0.45, 0.00],   # ch4 GAREEB: thin, pulled back
]


def build_layers():
    layers = {k: Bus() for k in LAYER_NAMES}
    n_bars = int(TOTAL_S / BAR) + 2
    for bar in range(n_bars):
        c = bar % 4
        t_bar = bar * BAR
        voicing, root, arp = CHORDS[c]
        Lp, Rp = pad_chord([mtof(m) for m in voicing], BAR + .6, 0.22)
        i0 = int(round(t_bar * SR)); n = min(len(Lp), N - i0)
        if n <= 0:
            continue
        layers['pad'].L[i0:i0 + n] += Lp[:n]      # true stereo: detuned L and R copies
        layers['pad'].R[i0:i0 + n] += Rp[:n]
        # bass: root on 0, octave on 1.5, root on 2, fifth on 3
        for bp, m, dur in ((0, root, .9), (1.5, root + 12, .4), (2, root, .9), (3, root + 7, .4)):
            layers['bass'].add(tone(mtof(m), dur * BEAT, 0.42, tau=0.16, harm=(1, .12)), t_bar + bp * BEAT)
        for bp in (0, 2):
            layers['kick'].add(kick(0.55), t_bar + bp * BEAT)
        # tonal ticks on every 8th note, accent on the off-beats
        for e in range(8):
            acc = 0.12 if e % 2 else 0.07
            layers['tick'].add(tone(9000.0, .03, acc, tau=.007, harm=(1.0,)), t_bar + e * BEAT / 2, pan=(0.6 if e % 2 else -0.6))
        for bp in range(4):   # tonal air: 11 kHz sparkle on every beat (sine, no noise)
            layers['tick'].add(tone(11000.0, .07, .085, tau=.022, harm=(1.0,)), t_bar + bp * BEAT, pan=(-0.8 if bp % 2 else 0.8))
        for bp, m, ln in LEAD[c]:
            layers['lead'].add(tone(mtof(m), ln * BEAT * .95, 0.20, tau=ln * BEAT * .55, harm=(1, .28, .09)),
                               t_bar + bp * BEAT, pan=0.12)
        # 16th-note shimmer arp (RAJA chapter only via gain curve)
        for s16 in range(16):
            m = arp[s16 % len(arp)]
            layers['arp'].add(tone(mtof(m), BEAT / 4 * .9, 0.07, tau=.09, harm=(1.0,)),
                              t_bar + s16 * BEAT / 4, pan=(-0.9 if s16 % 2 else 0.9))
    # dotted-eighth echo on the lead for width (no reverb noise)
    ld = layers['lead']
    dl = int(round(BEAT * 1.5 * SR))
    eL = np.zeros(N, np.float32); eR = np.zeros(N, np.float32)
    eL[dl:] = ld.R[:N - dl] * .32
    eR[dl:] = ld.L[:N - dl] * .32
    ld.L += eL; ld.R += eR
    return layers


def gain_curve(ch_vals, key):
    """piecewise-linear gain over time, crossfade 0.4 s centred on each chapter boundary."""
    t = np.arange(N) / SR
    starts = K.SCENE_START
    xs, ys = [0.0], [ch_vals[0][key]]
    for i in range(1, len(starts)):
        b = starts[i]
        xs += [b - .2, b + .2]
        ys += [ch_vals[i - 1][key], ch_vals[i][key]]
    xs.append(TOTAL_S + 1)
    ys.append(ch_vals[-1][key])
    return np.interp(t, xs, ys).astype(np.float32)


# ───────────────────────────── SFX (tonal foley)
def sfx_jingle(amp=1.0):
    out = np.zeros(int(.5 * SR), np.float32)
    for dt, f in ((0.00, 3520), (0.04, 4186), (0.09, 5274), (0.13, 6272), (0.18, 7040)):
        b = tone(f, .35, .05 * amp, tau=.07, harm=(1,))
        i = int(dt * SR); out[i:i + len(b)] += b[:len(out) - i]
    return out


def sfx_step(amp=1.0):
    d = .16
    t = tt(d)
    thump = np.sin(2 * np.pi * np.cumsum(70 + 40 * np.exp(-t / .02)) / SR) * np.exp(-t / .05)
    click = tone(1800.0, .02, .10, tau=.004)
    s = np.zeros(int(d * SR), np.float32)
    s += (.26 * amp * thump).astype(np.float32)
    s[:len(click)] += click
    return s


def sfx_door_open(amp=1.0):
    d = .55
    t = tt(d)
    f = 170 + 60 * t / d + 6 * np.sin(2 * np.pi * 5.5 * t)
    creak = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t / .12) * np.sin(np.pi * t / d)
    latch = tone(2500.0, .03, .10, tau=.006)
    s = (.07 * amp * creak).astype(np.float32)
    s[:len(latch)] += latch
    return s


def sfx_door_close(amp=1.0):
    thunk = tone(70.0, .34, .42 * amp, tau=.075, harm=(1, .25, .08))
    click = tone(1200.0, .02, .10 * amp, tau=.004)
    s = np.zeros(len(thunk), np.float32)
    s += thunk
    s[:len(click)] += click
    return s


def sfx_hop(amp=1.0):
    d = .14
    up = sweep(300, 520, d, .14 * amp, shape='lin') * np.exp(-tt(d) / .07)
    land = sfx_step(.9 * amp)
    out = np.zeros(int(.4 * SR), np.float32)
    out[:len(up)] += up.astype(np.float32)
    i = int(.20 * SR)
    out[i:i + len(land)] += land[:len(out) - i]
    return out


def sfx_engine(amp=1.0):
    d = 1.25
    t = tt(d)
    s = sum(w * np.sin(2 * np.pi * 42.0 * (k + 1) * t) for k, w in enumerate((1.0, .55, .28, .12)))
    env = np.minimum(1, t / .7) * np.minimum(1, (d - t) / .25)
    am = .85 + .15 * np.sin(2 * np.pi * 8.0 * t)
    return (.13 * amp * s * env * am).astype(np.float32)


def sfx_ac(amp=1.0):
    d = .55
    t = tt(d)
    click = tone(3500.0, .01, .18 * amp, tau=.003)
    whir = np.sin(2 * np.pi * np.cumsum(900 + 320 * t / d) / SR) * np.sin(np.pi * t / d) ** 2
    s = (.035 * amp * whir).astype(np.float32)
    s[:len(click)] += click
    return s


def sfx_ping(amp=1.0):
    return (tone(2093, .9, .16 * amp, tau=.22) + tone(3136, .9, .07 * amp, tau=.14)
            + tone(4186, .9, .03 * amp, tau=.10)).astype(np.float32)


def sfx_chime(amp=1.0):
    return bell(mtof(69), 2.2, .16 * amp, .9)


def sfx_whoosh(d, amp=1.0):
    """tonal sweep only: rising sine pair (7 Hz detune) with a sin^2 swell. No noise."""
    t = tt(d)
    f = 280 * (2000 / 280) ** (t / d)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + np.sin(2 * np.pi * np.cumsum(f + 7) / SR)
    s = s * .5 * np.sin(np.pi * t / d) ** 2
    return (.12 * amp * s).astype(np.float32)


SFX_FN = {'jingle': sfx_jingle, 'step': sfx_step, 'door_open': sfx_door_open, 'door_close': sfx_door_close,
          'hop': sfx_hop, 'engine_on': sfx_engine, 'ac_click': sfx_ac, 'ping': sfx_ping, 'chime': sfx_chime}
SFX_PAN = {'jingle': 0.0, 'step': 0.0, 'door_open': -0.45, 'door_close': -0.45, 'hop': 0.35,
           'engine_on': -0.1, 'ac_click': 0.3, 'ping': 0.2, 'chime': 0.0}


def build_sfx():
    bus = Bus()
    step_flip = 0
    for t, name, amp in K.CUES:
        if name == 'whoosh':
            b = int(amp)
            d = K.tdur(K.PLAN[b])
            bus.add(sfx_whoosh(d + .08, .9), t, pan=(-.2 if b % 2 else .2), gain=1.0)
        elif name == 'step':
            step_flip ^= 1
            bus.add(SFX_FN['step'](amp), t, pan=(-.18 if step_flip else .18), gain=1.0)
        else:
            bus.add(SFX_FN[name](amp), t, pan=SFX_PAN.get(name, 0.0), gain=1.0)
    return bus


# ───────────────────────────── voice
def eq_vo():
    """ffmpeg EQ + compression per clip -> mono 48 kHz. Returns list of (start_s, np.array)."""
    FF = _ff()
    os.makedirs(WORK, exist_ok=True)
    clips = []
    for i in range(4):
        src = f'{VO_DIR}/fit_k{i + 1}.wav'
        dst = f'{WORK}/eq_k{i + 1}.wav'
        chain = ('highpass=f=90,equalizer=f=250:t=q:w=1:g=-5,equalizer=f=180:t=q:w=1:g=-1.5,equalizer=f=5000:t=q:w=1.2:g=8.5,equalizer=f=7500:t=q:w=1.4:g=5,'
                 'acompressor=threshold=0.063:ratio=3:attack=8:release=180:makeup=1.2')
        subprocess.run([FF, '-y', '-v', 'error', '-i', src, '-af', chain, '-ac', '1', '-ar', str(SR),
                        '-c:a', 'pcm_s16le', dst], check=True)
        w = wave.open(dst)
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        clips.append((K.VO_AT[i], a))
    return clips


def write_wav(path, L, R=None):
    if R is None:
        st = np.stack([L, L], axis=1)
    else:
        st = np.stack([L, R], axis=1)
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    w = wave.open(path, 'wb')
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(np.ascontiguousarray(pcm).tobytes())
    w.close()


def loudnorm(src, dst, I=-11.0, TP=-2.0):
    FF = _ff()
    # extrastereo 3.0 widens only the side (mid, and so mono sum, unchanged): mix L/R corr ~0.95 -> ~0.75
    subprocess.run([FF, '-y', '-v', 'error', '-i', src, '-af',
                    f'extrastereo=m=3.0,alimiter=limit=0.75:attack=4:release=70,loudnorm=I={I}:TP={TP}:LRA=7', '-ar', str(SR), '-c:a', 'pcm_s16le', dst], check=True)


def build():
    os.makedirs(WORK, exist_ok=True)
    layers = build_layers()
    ch_vals = CH_GAINS
    music_L = np.zeros(N, np.float32); music_R = np.zeros(N, np.float32)
    hz = int(round(.014 * SR))      # Haas offset: right channel of the wide layers arrives 14 ms late
    for name in LAYER_NAMES:
        g = gain_curve(ch_vals, LAYER_NAMES.index(name))
        Lb, Rb = layers[name].L, layers[name].R
        if name in ('pad', 'arp', 'tick'):
            Rb = np.concatenate([np.zeros(hz, np.float32), Rb[:-hz]])
        music_L += Lb * g
        music_R += Rb * g
    sfx = build_sfx()
    # voice bus (mono, centred)
    vo = np.zeros(N, np.float32)
    for start, a in eq_vo():
        i0 = int(round(start * SR))
        n = min(len(a), N - i0)
        vo[i0:i0 + n] += a[:n]
    # sidechain: music ducks under the voice (10 ms attack, 260 ms release)
    hop = int(.01 * SR)
    env_raw = np.sqrt(np.convolve(vo ** 2, np.ones(int(.03 * SR)) / int(.03 * SR), 'same'))
    env = env_raw.copy()
    rel = np.exp(-1.0 / (.26 * 100))
    atk = np.exp(-1.0 / (.01 * 100))
    cur = 0.0
    for i in range(0, N, hop):
        seg = env_raw[i:i + hop]
        tgt = float(seg.max()) if len(seg) else 0.0
        cur = max(tgt, cur * (atk if tgt > cur else rel))
        env[i:i + hop] = cur
    duck = 1.0 - 0.55 * np.clip(env / (np.percentile(env[env > 1e-4], 90) + 1e-9), 0, 1)
    duck = duck.astype(np.float32)
    bedL = (music_L * duck + sfx.L).astype(np.float32)
    bedR = (music_R * duck + sfx.R).astype(np.float32)
    # balance: voice sits ~6 dB above the bed while it speaks (measured on the voice-active samples)
    act = np.abs(vo) > 1e-3
    bed_m = np.sqrt(((bedL ** 2 + bedR ** 2) / 2)[act].mean() + 1e-12)
    vo_r = np.sqrt((vo[act] ** 2).mean() + 1e-12)
    g_vo = 1.8 * bed_m / vo_r
    vo = vo * np.float32(g_vo)
    peak = max(np.max(np.abs(bedL)), np.max(np.abs(bedR)), np.max(np.abs(vo)), 1e-9)
    s = 0.80 / peak
    bedL *= s; bedR *= s; vo *= s
    print('vo gain', round(float(g_vo), 3), 'bed_rms_act', round(float(bed_m), 4), 'vo_rms_act', round(float(vo_r), 4))
    mixL = bedL + vo
    mixR = bedR + vo
    write_wav(f'{WORK}/bed_only.wav', bedL, bedR)
    write_wav(f'{WORK}/vo_bus.wav', vo)
    write_wav(f'{WORK}/mix_raw.wav', mixL, mixR)
    loudnorm(f'{WORK}/mix_raw.wav', f'{WORK}/mix_kutta2.wav')
    print('wrote', f'{WORK}/mix_kutta2.wav', 'dur', round(N / SR, 3), 'vo_peak_pre', round(float(np.max(np.abs(vo))), 3))


def mux():
    FF = _ff()
    lst = f'{WORK}/shards.txt'
    with open(lst, 'w') as f:
        f.write(f"file '{OUT}/v2/shard0.mp4'\nfile '{OUT}/v2/shard1.mp4'\n")
    subprocess.run([FF, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy',
                    f'{OUT}/v2/kutta2_mute.mp4'], check=True)
    subprocess.run([FF, '-y', '-v', 'error', '-i', f'{OUT}/v2/kutta2_mute.mp4', '-i', f'{WORK}/mix_kutta2.wav',
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
                    '-ac', '2', '-shortest', '-movflags', '+faststart', f'{OUT}/kutta_v2.mp4'], check=True)
    print('wrote', f'{OUT}/kutta_v2.mp4')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'mux':
        mux()
    else:
        build()
