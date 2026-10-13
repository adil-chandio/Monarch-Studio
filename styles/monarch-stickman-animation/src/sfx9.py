"""sfx9.py — AMEER KA KUTTA v9: designed sound effects, synthesised (numpy + scipy), 48 kHz mono float32.

Why: the licensed SFX pack lives on Drive and cannot be fetched from this sandbox (Google hosts are
blocked). mux_kutta2 prefers the pack when a sample exists in SFX_LIB and falls back to these designs,
so the same cue names keep working:  crack_flash, riser_click, digital_click, modern_shutter, gleam,
conjure_charge, lighter_ignite, synth_sparkle.  New v9 cues: braam, impact, coin, confetti, thunder,
rain (long bed), sub_drop, stamp_ring, whoosh_air.

Design rules: transients may be broadband (an impact is a crack), but nothing here is a constant hiss.
Every clip starts and ends at zero (short fades) so nothing clicks at the splice.
"""
import numpy as np
from scipy.signal import butter, lfilter

SR = 48000


def tt(d):
    return np.arange(int(round(d * SR))) / SR


def env_ad(t, a, tau):
    return np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-np.maximum(0.0, t - a) / tau)


def fade(x, ms_in=2.0, ms_out=12.0):
    n_in, n_out = int(SR * ms_in / 1000), int(SR * ms_out / 1000)
    x = x.astype(np.float32).copy()
    if n_in > 0 and len(x) > n_in:
        x[:n_in] *= np.linspace(0, 1, n_in, dtype=np.float32)
    if n_out > 0 and len(x) > n_out:
        x[-n_out:] *= np.linspace(1, 0, n_out, dtype=np.float32)
    return x


def noise(d, seed=0):
    return np.random.default_rng(seed).standard_normal(int(round(d * SR))).astype(np.float32)


def bp(x, lo, hi, order=2):
    b, a = butter(order, [lo / (SR / 2), min(hi, SR / 2 - 100) / (SR / 2)], btype='band')
    return lfilter(b, a, x).astype(np.float32)


def lp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), btype='low')
    return lfilter(b, a, x).astype(np.float32)


def hp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), btype='high')
    return lfilter(b, a, x).astype(np.float32)


def sine(f, d, amp=1.0, tau=0.3, a=0.003, ph=0.0):
    t = tt(d)
    return (amp * np.sin(2 * np.pi * f * t + ph) * env_ad(t, a, tau)).astype(np.float32)


def sweep(f0, f1, d, amp=1.0, tau=None, a=0.002):
    t = tt(d)
    f = f0 * (f1 / f0) ** (t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    e = env_ad(t, a, tau if tau else d)
    return (amp * np.sin(ph) * e).astype(np.float32)


def norm(x, peak=0.9):
    m = float(np.max(np.abs(x))) if len(x) else 0.0
    return (x / m * peak).astype(np.float32) if m > 1e-9 else x.astype(np.float32)


# ───────────────────────────── hits
def impact(amp=1.0, seed=1):
    """cinema hit: sub thump + crack + body + short metallic ring."""
    d = 1.1
    t = tt(d)
    sub = sweep(95, 34, d, 1.0, tau=0.28)
    crack = bp(noise(d, seed), 900, 7000) * env_ad(t, 0.001, 0.025) * 1.6
    body = bp(noise(d, seed + 1), 120, 2400) * env_ad(t, 0.004, 0.16) * 0.9
    ring = sum(sine(f, d, g, tau=0.55, a=0.004) for f, g in ((412, .12), (1123, .08), (1874, .05)))
    return fade(norm(sub + crack + body + ring, 0.9 * amp))


def crack_flash(amp=1.0):
    d = 1.0
    t = tt(d)
    crack = bp(noise(d, 7), 1500, 9000) * env_ad(t, 0.001, 0.035) * 1.8
    flash = sweep(2400, 600, 0.5, 0.35, tau=0.12)
    out = impact(1.0, seed=3)
    out[:len(crack)] += crack
    out[:len(flash)] += flash
    return fade(norm(out, 0.9 * amp))


def braam(amp=1.0):
    """trailer braam: detuned low saw stack, slow swell, 2.4 s."""
    d = 2.4
    t = tt(d)
    out = np.zeros_like(t, dtype=np.float32)
    for f0, g, det in ((55.0, 1.0, 0.0), (55.0, .8, .006), (82.5, .55, -.004), (110.0, .35, .003)):
        f = f0 * (1 + det)
        for k in range(1, 12):
            out += (g / k) * np.sin(2 * np.pi * f * k * t + k * .7).astype(np.float32)
    e = np.minimum(1.0, t / 0.35) * np.exp(-np.maximum(0, t - 0.9) / 0.6)
    out = lp(out * e, 900)
    out += sweep(60, 40, d, 0.6, tau=0.9)
    return fade(norm(out, 0.8 * amp), 20, 120)


def sub_drop(amp=1.0):
    d = 1.6
    out = sweep(72, 26, d, 1.0, tau=0.7, a=0.01)
    out += bp(noise(d, 11), 80, 400) * env_ad(tt(d), 0.004, 0.05) * 0.5
    return fade(norm(out, 0.85 * amp), 4, 200)


def thunder(amp=1.0, seed=21):
    """crack, then a rolling low rumble (lowpassed noise, gusting envelope). 2.6 s."""
    d = 2.6
    t = tt(d)
    crack = bp(noise(d, seed), 300, 3500) * env_ad(t, 0.002, 0.07) * 1.2
    rum = lp(noise(d, seed + 1), 160, 3)
    g = (np.exp(-np.maximum(0, t - 0.08) / 1.1) * np.minimum(1, t / 0.05)
         * (1 + .45 * np.sin(2 * np.pi * 2.3 * t) * np.exp(-t / 1.5)))
    rum = rum * g * 2.4
    sub = sweep(60, 30, 1.4, 0.5, tau=0.5)
    out = crack + rum
    out[:len(sub)] += sub
    return fade(norm(out, 0.85 * amp), 2, 300)


def stamp_ring(amp=1.0):
    """gong-like end punctuation: inharmonic partials, 2.6 s."""
    d = 2.6
    out = sum(sine(f, d, g, tau=tau, a=0.004) for f, g, tau in
              ((182, 1.0, 1.4), (291, .7, 1.1), (473, .5, .9), (712, .35, .7), (1180, .2, .5), (1931, .1, .35)))
    out += bp(noise(d, 5), 200, 2500) * env_ad(tt(d), 0.002, 0.04) * 0.6
    return fade(norm(out, 0.8 * amp), 2, 300)


# ───────────────────────────── sweeps
def riser_click(amp=1.0, d=1.0, seed=31):
    """rising band of air + a rising tone, snaps shut with a click at the end."""
    t = tt(d)
    n = noise(d, seed)
    bands = [bp(n, lo, hi) for lo, hi in ((250, 700), (600, 1600), (1400, 3600), (3000, 8000))]
    out = np.zeros_like(t, dtype=np.float32)
    for i, b in enumerate(bands):
        c = (i + .5) / len(bands)
        w = np.exp(-((t / d - c) / 0.22) ** 2)
        out += b * w
    out *= (t / d) ** 1.6 * 1.5
    out += sweep(180, 1500, d, 0.25, tau=d * 2, a=0.05) * (t / d)
    click = bp(noise(0.03, seed + 1), 1500, 7000) * env_ad(tt(0.03), 0.0005, 0.006) * 1.2
    out = np.concatenate([out, np.zeros(int(0.06 * SR), np.float32)])
    o = len(t) - len(click) // 2
    out[o:o + len(click)] += click[:len(out) - o]
    return fade(norm(out, 0.8 * amp), 10, 20)


def whoosh_air(d=0.6, amp=1.0, seed=41):
    """noise whoosh (band 300-4000 Hz, sin^2 envelope) — layered under the tonal sweep whoosh."""
    t = tt(d + .08)
    n = bp(noise(d + .08, seed), 300, 4000)
    e = np.sin(np.pi * np.clip(t / (d + .08), 0, 1)) ** 2
    return fade(norm(n * e, 0.7 * amp), 10, 30)


# ───────────────────────────── small tonal
def digital_click(amp=1.0):
    out = np.concatenate([sine(2400, 0.02, 1.0, tau=0.006, a=0.0005), np.zeros(int(0.03 * SR), np.float32),
                          sine(3200, 0.025, 0.8, tau=0.007, a=0.0005)])
    return fade(norm(out, 0.6 * amp))


def modern_shutter(amp=1.0, seed=51):
    c1 = bp(noise(0.012, seed), 1500, 6500) * env_ad(tt(0.012), 0.0005, 0.003)
    c2 = bp(noise(0.016, seed + 1), 1000, 5000) * env_ad(tt(0.016), 0.0005, 0.004)
    out = np.concatenate([c1, np.zeros(int(0.07 * SR), np.float32), c2, np.zeros(int(0.05 * SR), np.float32)])
    return fade(norm(out, 0.6 * amp))


def gleam(amp=1.0):
    d = 1.4
    out = np.zeros(int(d * SR), np.float32)
    for i, f in enumerate((1318.5, 1760.0, 2217.5, 2637.0, 3520.0)):
        s = sine(f, d - i * .05, .5 / (1 + i * .25), tau=0.55, a=0.03 + .01 * i)
        o = int(i * .05 * SR)
        out[o:o + len(s)] += s
    t = tt(d)
    out *= 1 + .18 * np.sin(2 * np.pi * 6.5 * t)
    return fade(norm(out, 0.55 * amp), 5, 80)


def conjure_charge(amp=1.0):
    d = 1.1
    t = tt(d)
    out = np.zeros_like(t, dtype=np.float32)
    for k, g in ((1, 1.0), (2, .5), (3, .33), (4, .25), (5, .2)):
        f = 110.0 * k * (1 + .9 * (t / d) ** 2)
        ph = 2 * np.pi * np.cumsum(f) / SR
        out += g * np.sin(ph).astype(np.float32)
    out *= (t / d) ** 1.4 * (1 + .35 * np.sin(2 * np.pi * 9 * t))
    out = lp(out, 3500)
    bell = sine(880, 0.9, .6, tau=0.35, a=0.004)
    out = np.concatenate([out, np.zeros(int(0.9 * SR), np.float32)])
    o = len(t) - len(bell) // 4
    out[o:o + len(bell)] += bell
    return fade(norm(out, 0.65 * amp), 10, 100)


def lighter_ignite(amp=1.0, seed=61):
    d = 0.55
    t = tt(d)
    crackle = np.zeros_like(t, dtype=np.float32)
    rnd = np.random.default_rng(seed)
    for k in range(5):
        o = int(rnd.uniform(0, 0.09) * SR)
        c = bp(noise(0.02, seed + k), 2000, 9000) * env_ad(tt(0.02), 0.0005, 0.004)
        crackle[o:o + len(c)] += c * (1 - k * .12)
    fsst = hp(noise(d, seed + 9), 3000) * env_ad(t, 0.03, 0.09) * 0.7
    tone = sweep(900, 1800, 0.25, 0.25, tau=0.12)
    out = crackle + fsst
    o = int(0.06 * SR)
    out[o:o + len(tone)] += tone[:len(out) - o]
    return fade(norm(out, 0.6 * amp))


def synth_sparkle(amp=1.0, n=9, d=0.5, seed=71, flo=2000, fhi=6500):
    rnd = np.random.default_rng(seed)
    out = np.zeros(int((d + .4) * SR), np.float32)
    for k in range(n):
        f = rnd.uniform(flo, fhi)
        o = int(rnd.uniform(0, d) * SR)
        s = sine(f, 0.35, rnd.uniform(.3, .6), tau=0.09, a=0.002)
        out[o:o + len(s)] += s
    return fade(norm(out, 0.5 * amp), 2, 60)


def coin(amp=1.0, seed=81):
    d = 0.5
    out = sine(3136, d, 1.0, tau=0.12, a=0.001) + sine(4699, d, .6, tau=0.08, a=0.001) + sine(6272, d, .3, tau=0.05, a=0.001)
    out += bp(noise(d, seed), 3000, 9000) * env_ad(tt(d), 0.0005, 0.004) * 0.8
    return fade(norm(out, 0.45 * amp))


def confetti(amp=1.0, seed=91):
    pop = bp(noise(0.08, seed), 700, 4000) * env_ad(tt(0.08), 0.001, 0.02) * 1.5
    sp = synth_sparkle(1.0, n=18, d=0.7, seed=seed + 1, flo=2500, fhi=8000)
    out = np.zeros(max(len(pop), len(sp)) + 10, np.float32)
    out[:len(pop)] += pop
    out[:len(sp)] += sp * .8
    return fade(norm(out, 0.6 * amp))


def rain(d=8.0, amp=1.0, seed=101):
    """diegetic rain bed: droplet ticks (bandpassed noise 2-9 kHz) under a slow gust envelope. quiet."""
    t = tt(d)
    n = bp(noise(d, seed), 1800, 9000)
    gust = 0.7 + 0.3 * np.sin(2 * np.pi * 0.17 * t + 1.0) * np.sin(2 * np.pi * 0.07 * t)
    e = np.minimum(1.0, t / 0.6) * np.minimum(1.0, (d - t) / 0.8)
    drops = np.zeros_like(t, dtype=np.float32)
    rnd = np.random.default_rng(seed + 1)
    for _ in range(int(d * 26)):
        o = int(rnd.uniform(0, d - 0.03) * SR)
        c = bp(noise(0.012, int(rnd.integers(1, 10 ** 6))), 2500, 8000) * env_ad(tt(0.012), 0.0004, 0.0025)
        drops[o:o + len(c)] += c * rnd.uniform(.4, 1.0)
    out = (n * 0.55 + drops * 1.2) * gust * e
    return fade(norm(out, 0.22 * amp), 200, 400)


SYNTH = {
    'crack_flash': crack_flash, 'riser_click': riser_click, 'digital_click': digital_click,
    'modern_shutter': modern_shutter, 'gleam': gleam, 'conjure_charge': conjure_charge,
    'lighter_ignite': lighter_ignite, 'synth_sparkle': synth_sparkle,
    'braam': braam, 'impact': impact, 'coin': coin, 'confetti': confetti, 'thunder': thunder,
    'sub_drop': sub_drop, 'stamp_ring': stamp_ring,
}


def synth(name, amp=1.0, **kw):
    return SYNTH[name](amp, **kw) if name in SYNTH else None


if __name__ == '__main__':
    import sys, wave
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/sfx9_demo.wav'
    parts = []
    for name in SYNTH:
        parts.append(SYNTH[name](1.0)); parts.append(np.zeros(int(0.4 * SR), np.float32))
    parts.append(rain(3.0)); parts.append(whoosh_air(0.7))
    x = np.concatenate(parts)
    w = wave.open(out, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    print('wrote', out, round(len(x) / SR, 1), 's')
