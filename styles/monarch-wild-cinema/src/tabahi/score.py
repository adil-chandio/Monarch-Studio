"""TABAHI SCORE — procedural, stereo, measured. No third-party music.

Four laws are encoded here because each one was learned the hard way and each
one is cheap to obey and expensive to ignore:

  1. WIDTH IS CREATED AT THE SOURCE. A widener multiplying a mono drone gives
     exactly zero. Every bed stem is generated as a true stereo pair with
     independent detune and independent phase noise per channel.
  2. BUDGET THE SPECTRUM BEFORE THE LOUDNESS. Three stacked bass instruments
     do not sound cinematic; they sound like a rumble. Every stem is assigned
     a band, and the final mix is measured per band with and without voice.
  3. THE LIMITER PROTECTS THE PCM, NOT THE CODEC. AAC overshoots by ~2.4 dB.
     Limit to -4 dBFS and re-measure the peak AFTER decoding the delivered file.
  4. AN UNBOUNDED `apad` WILL PAD FOREVER. Always `apad=whole_dur=…,atrim=…`.
"""
from __future__ import annotations

import math
import subprocess

import numpy as np

from . import core as C

SR = C.SR


# ─────────────────────────────────────────────────────────────────────────────
# PRIMITIVES
# ─────────────────────────────────────────────────────────────────────────────

def _env_ad(n: int, attack: float, decay: float, curve: float = 3.0) -> np.ndarray:
    a = max(int(attack * SR), 1)
    d = max(n - a, 1)
    e = np.concatenate([
        np.linspace(0, 1, a, dtype=np.float32),
        (1.0 - np.linspace(0, 1, d, dtype=np.float32)) ** curve,
    ])
    return e[:n]


def _stereo(x: np.ndarray, spread: float = 0.0) -> np.ndarray:
    """spread > 0 delays/attenuates the right channel for width."""
    if spread <= 0:
        return np.stack([x, x], axis=1).astype(np.float32)
    d = int(spread * SR)
    r = np.concatenate([np.zeros(d, np.float32), x[:len(x) - d]]) * 0.94
    return np.stack([x, r], axis=1).astype(np.float32)


def add(dst: np.ndarray, src: np.ndarray, at: float, gain: float = 1.0):
    """Mix src into dst at time `at`, clipped to the buffer."""
    i0 = int(at * SR)
    if i0 >= len(dst) or i0 < 0:
        return
    n = min(len(src), len(dst) - i0)
    dst[i0:i0 + n] += src[:n] * gain
    return


# ─────────────────────────────────────────────────────────────────────────────
# CUES  (name -> generator; the transition table references these by name)
# ─────────────────────────────────────────────────────────────────────────────

def soft_clip(x: np.ndarray, drive: float = 1.0) -> np.ndarray:
    """Memoryless saturation — the crest-factor tool that cannot pump.

    MEASURED NEED: the proof score arrived with a 24.5 dB peak-to-RMS crest
    (impacts peaking at +1.6 dBFS over a bed 9.4 dB quieter). No gain structure
    reaches -16 LUFS with a -1 dBFS ceiling from a 24 dB crest without either
    clipping the 16-bit write or pumping; a limiter that tracks the envelope
    only made it quieter (-23.6 LUFS in, -27.5 LUFS out). tanh raises the RMS
    by squaring off the peaks and is per-sample, so it cannot modulate the
    stereo image or the level over time.
    """
    if drive <= 1.0:
        return x
    return (np.tanh(x * drive) / np.tanh(drive)).astype(np.float32)


def fft_band(x: np.ndarray, lo: float, hi: float, tilt_db: float = 0.0) -> np.ndarray:
    """Band-limit with an exact FFT mask (raised-cosine edges).

    MEASURED NEED: the 2-pole bandpass used while building the shimmer left so
    much energy above its 7.8 kHz corner that the 8-16 kHz band measured 34.2 %
    of the mix while 4-8 kHz — the band the gate actually asks for, G13 — sat
    at 17.8 %. A brickwall-ish mask places the energy where the gate measures.
    """
    n = len(x)
    mono = x if x.ndim == 1 else x.mean(axis=1)
    spec = np.fft.rfft(mono)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    edge = max(200.0, lo * 0.25)
    lo_m = np.clip((f - (lo - edge)) / edge, 0.0, 1.0)
    hi_m = np.clip(((hi + edge) - f) / edge, 0.0, 1.0)
    mask = 0.5 - 0.5 * np.cos(np.pi * lo_m)
    mask *= 0.5 - 0.5 * np.cos(np.pi * hi_m)
    if tilt_db:
        with np.errstate(divide="ignore"):
            mask = mask * (10.0 ** (tilt_db * np.log2(np.maximum(f, 20.0) / max(lo, 20.0)) / 20.0))
    mask = mask.astype(np.float32)
    out = np.fft.irfft(spec * mask, n)[:n].astype(np.float32)
    return out if x.ndim == 1 else np.stack([out, out], axis=1)


def limit_linked(x: np.ndarray, ceiling: float = 0.72, attack_ms: float = 4.0,
                 release_ms: float = 240.0, block: int = 128) -> np.ndarray:
    """A LINKED limiter: one gain curve for both channels.

    MEASURED CORRECTION: ffmpeg's `alimiter` applies its gain reduction per
    channel. A stereo cue whose two channels differ in peak (every delayed
    stereo cue here) therefore gets compressed by different amounts per side,
    which rewrites the inter-channel phase relationship. A mix balanced to
    L/R correlation +0.580 arrived at the master measuring +0.055.

    Deriving the gain from max(|L|,|R|) and applying it to both channels is
    what a real bus limiter does, and it cannot move the correlation at all —
    a per-sample gain applied equally to both channels preserves it exactly.
    The envelope is computed on 128-sample blocks so the attack/release loop
    runs on ~12 k points instead of 1.6 M.
    """
    env = np.maximum(np.abs(x[:, 0]), np.abs(x[:, 1])).astype(np.float32)
    n = len(env)
    nb = n // block
    if nb < 4:
        return x
    blocks = env[: nb * block].reshape(nb, block).max(axis=1)
    a = float(np.exp(-1.0 / max(attack_ms / 1000.0 * SR / block, 1.0)))
    r = float(np.exp(-1.0 / max(release_ms / 1000.0 * SR / block, 1.0)))
    gain = np.ones(nb, np.float32)
    g = 1.0
    for i in range(nb):
        e = float(blocks[i])
        want = 1.0 if e <= ceiling else ceiling / max(e, 1e-9)
        coeff = a if want < g else r
        g = coeff * g + (1.0 - coeff) * want
        gain[i] = g
    full = np.interp(np.arange(n, dtype=np.float32),
                     (np.arange(nb, dtype=np.float32) + 0.5) * block, gain).astype(np.float32)
    return (x * full[:, None]).astype(np.float32)


def stereo_balance(x: np.ndarray, target_corr: float = 0.58) -> np.ndarray:
    """Rebuild the mix around a target L/R correlation, keeping the width.

    G10 wants correlation 0.55-0.85 and G11 wants side/mid > 0.25. Those two are
    the same number seen from two sides — side/mid = (1-corr)/(1+corr) — so the
    window that satisfies both is corr in [0.55, 0.60], side/mid in [0.25, 0.29].

    Each stereo stem was built correlated on purpose, but inter-channel delays
    in the cues and any block that used two different frequencies push the sum
    toward zero or below it, which is a mono-cancelling mix. Rather than chase
    every source, this normalises the MID/SIDE ratio at the end:

        k = sqrt( Em*(1-t) / (Es*(1+t)) )      with L = m + k*s, R = m - k*s

    which lands the correlation on the target by construction.
    """
    m = (x[:, 0] + x[:, 1]) * 0.5
    sd = (x[:, 0] - x[:, 1]) * 0.5
    if float((sd ** 2).mean()) < 1e-12:
        return x

    def corr_at(k: float) -> float:
        left = m + k * sd
        right = m - k * sd
        den = float(np.sqrt((left ** 2).sum() * (right ** 2).sum()))
        return float((left * right).sum() / den) if den > 0 else 1.0

    # The closed form (Em(1-t))/(Es(1+t)) is only exact when mid and side are
    # uncorrelated, which they are not once the channels differ in level —
    # measured 0.342 against a 0.58 target. Solve it numerically instead.
    if corr_at(1.0) >= target_corr:
        return x
    lo, hi = 0.0, 6.0
    for _ in range(26):
        mid = (lo + hi) * 0.5
        if corr_at(mid) > target_corr:
            lo = mid
        else:
            hi = mid
    k = (lo + hi) * 0.5
    return np.stack([m + k * sd, m - k * sd], axis=1).astype(np.float32)


def shape_spectrum(x: np.ndarray, sr: int = SR, high_shelf_db: float = 0.0,
                   shelf_hz: float = 1500.0, low_cut_hz: float = 32.0,
                   low_cut_db: float = -18.0) -> np.ndarray:
    """Shelf and low-cut on the whole bed, done in the frequency domain.

    This is an offline render, so a non-causal FFT shelf is legitimate and
    exact — and it is the only reliable way to hit a per-band energy target
    instead of guessing at filter coefficients. Measured need: the first mix
    put 72 % of its energy below 120 Hz and 1.2 % in 4-8 kHz.
    """
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(len(x), 1.0 / sr)
    ramp = 1.0 / (1.0 + np.exp(-(f - shelf_hz) / (shelf_hz * 0.35)))
    gain = 10.0 ** ((high_shelf_db / 20.0) * ramp)
    lc = 1.0 / (1.0 + np.exp(np.clip((f - low_cut_hz) / (low_cut_hz * 0.5 + 1e-6), -60, 60)))
    gain = gain * (10.0 ** ((low_cut_db / 20.0) * lc))
    return np.fft.irfft(X * gain[:, None], n=len(x), axis=0).astype(np.float32)


def cue_impact(strength: float = 1.0, dur: float = 0.9) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = np.exp(-t * 8.0).astype(np.float32)
    f = 74.0 * np.exp(-t * 6.0) + 33.0
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env
    click = np.exp(-t * 240.0).astype(np.float32) * np.random.default_rng(2).standard_normal(n).astype(np.float32) * 0.25
    x = (body + click) * 0.9 * strength
    return _stereo(x, spread=0.006)


def cue_impact_soft(strength: float = 1.0) -> np.ndarray:
    n = int(0.55 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = np.exp(-t * 11.0).astype(np.float32)
    x = np.sin(2 * np.pi * 58.0 * t) * env * 0.6 * strength
    return _stereo(x, spread=0.008)


def cue_sub_drop(dur: float = 1.5, strength: float = 1.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = np.linspace(88.0, 32.0, n, dtype=np.float32)
    env = (1.0 - t / dur) ** 1.6
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env * 0.85 * strength
    return _stereo(x, spread=0.004)


def cue_riser(dur: float = 1.2, strength: float = 1.0, hi: float = 2600.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    rng = np.random.default_rng(9)
    noise = rng.standard_normal(n).astype(np.float32)
    # sweeping band-pass by ring modulation of a filtered noise is expensive;
    # a pitch-swept saw + noise gives the same "rising" percept for 1/50 cost
    f = np.linspace(180.0, hi, n, dtype=np.float32)
    saw = 2.0 * ((np.cumsum(f) / SR) % 1.0) - 1.0
    env = (t / dur) ** 2.2
    x = (saw.astype(np.float32) * 0.35 + noise * 0.16) * env * strength
    return _stereo(x, spread=0.010)


def cue_riser_short(strength: float = 1.0) -> np.ndarray:
    return cue_riser(0.5, strength, 3400.0)


def cue_whoosh(dur: float = 0.42, strength: float = 1.0, tilt: float = 1.0) -> np.ndarray:
    """Filtered-noise pass. Tilt 1 = left->right, -1 = right->left."""
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    rng = np.random.default_rng(4)
    x = rng.standard_normal(n).astype(np.float32)
    k = max(int(SR * 0.004), 8)
    kern = np.hanning(k).astype(np.float32)
    kern /= kern.sum()
    x = np.convolve(x, kern, mode="same")
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6
    x = x * env * strength
    pan = np.clip(0.5 + 0.45 * tilt * (2 * t / dur - 1), 0, 1)
    l = x * np.sqrt(1 - pan)
    r = x * np.sqrt(pan)
    return np.stack([l, r], axis=1).astype(np.float32)


def cue_doppler_whip(strength: float = 1.0) -> np.ndarray:
    n = int(0.34 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = np.linspace(1400.0, 180.0, n, dtype=np.float32)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    env = np.sin(np.pi * np.clip(t / 0.34, 0, 1)) ** 1.2
    x = (x * env * 0.5 * strength).astype(np.float32)
    return _stereo(x, spread=0.012)


def cue_whoosh_edge(strength: float = 1.0) -> np.ndarray:
    return cue_whoosh(0.30, strength * 0.8, 1.0)


def cue_hard_hit(strength: float = 1.0) -> np.ndarray:
    n = int(0.30 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = np.exp(-t * 26.0).astype(np.float32)
    x = (np.sin(2 * np.pi * 96.0 * t) * env + np.exp(-t * 120.0) * 0.2) * strength
    return _stereo(x.astype(np.float32), spread=0.002)


def cue_pad_swell(dur: float = 2.4, strength: float = 1.0, root: float = 110.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    rng = np.random.default_rng(13)
    x = np.zeros(n, np.float32)
    for m, a in ((1.0, 0.5), (1.5, 0.22), (2.0, 0.16), (3.0, 0.09)):
        ph = rng.random() * 6.283
        x += a * np.sin(2 * np.pi * root * m * t + ph)
    x = (x * env * 0.4 * strength).astype(np.float32)
    return _stereo(x, spread=0.016)


def cue_bell(dur: float = 1.1, strength: float = 1.0, freq: float = 880.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = np.exp(-t * 3.6).astype(np.float32)
    x = np.zeros(n, np.float32)
    for m, a, d in ((1.0, 1.0, 0), (2.01, 0.42, 2.4), (3.02, 0.2, 4.1), (5.4, 0.08, 6.2)):
        x += a * np.sin(2 * np.pi * freq * m * t) * np.exp(-t * (3.6 + d))
    return _stereo((x * env * 0.32 * strength).astype(np.float32), spread=0.004)


def cue_tick(strength: float = 1.0) -> np.ndarray:
    n = int(0.09 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = np.exp(-t * 70.0).astype(np.float32)
    x = (np.random.default_rng(21).standard_normal(n).astype(np.float32) * env + 0.4 * env) * 0.5 * strength
    return _stereo(x.astype(np.float32), spread=0.003)


CUES = {
    "impact": cue_impact, "impact_soft": cue_impact_soft, "sub_drop": cue_sub_drop,
    "riser": cue_riser, "riser_short": cue_riser_short, "whoosh": cue_whoosh,
    "doppler_whip": cue_doppler_whip, "whoosh_edge": cue_whoosh_edge,
    "hard_hit": cue_hard_hit, "pad_swell": cue_pad_swell, "bell": cue_bell, "tick": cue_tick,
}


# ─────────────────────────────────────────────────────────────────────────────
# BEDS  (stereo at the source; each bed owns a band)
# ─────────────────────────────────────────────────────────────────────────────

def bed_drone(n: int, root: float = 65.41, seed: int = 31,
              width: float = 1.0, level: float = 0.20) -> np.ndarray:
    """Stereo by DETUNE, not by two unrelated signals.

    MEASURED CORRECTION: generating fully independent phases per channel
    produced L/R correlation -0.245 — a mix that cancels its own bass when a
    phone folds it to mono, and a G10 failure. Width is still created at the
    source (independent detune + a short inter-channel delay), but the partial
    SET and the phases are shared, so the channels stay positively correlated.
    The root also moved up an octave: at 43.65 Hz the whole mix measured 72 %
    of its energy below 120 Hz, which is a rumble, not a score.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(n, dtype=np.float32) / SR
    phases = rng.random(8) * 6.283
    # the fundamental is deliberately NOT the loudest partial: a drone whose
    # energy sits in one sub-bin owns the whole mix's spectrum
    partials = ((1.0, 0.55), (1.5, 0.85), (2.0, 0.62), (3.0, 0.45), (4.0, 0.34), (6.0, 0.22))
    out = np.zeros((n, 2), np.float32)
    for ch in (0, 1):
        d = 1.0 + (1 if ch else -1) * 0.0022 * width
        swell = 0.55 + 0.45 * np.sin(2 * np.pi * (0.021 + 0.003 * ch) * t + phases[0])
        for i, (m, a) in enumerate(partials):
            out[:, ch] += a * np.sin(2 * np.pi * root * m * d * t + phases[i % 8])
        out[:, ch] *= swell
    delay = int(0.0035 * SR * width)
    if delay:
        right = np.concatenate([np.zeros(delay, np.float32), out[:n - delay, 1]])
        out[:, 1] = right * 0.96 + out[:, 1] * 0.04
    return (out * level / 2.6).astype(np.float32)


def bed_air(n: int, seed: int = 41, level: float = 0.05) -> np.ndarray:
    """PRESENCE, not rumble.

    MEASURED CORRECTION: smoothing white noise with a hanning kernel is a
    LOW-pass, so the previous "air" stem added energy below 120 Hz and the mix
    measured 1.2 % of its energy in 4-8 kHz. Air is the residual after removing
    the smoothed part, which is a genuine high-pass, plus a slow amplitude
    drift so it breathes instead of hissing like tape.
    """
    rng = np.random.default_rng(seed)
    base = rng.standard_normal(n).astype(np.float32)
    k = int(SR * 0.003)                          # ~3 ms kernel => residual is >~300 Hz
    kern = np.hanning(max(k, 8)).astype(np.float32)
    kern /= kern.sum()
    resid = base - np.convolve(base, kern, mode="same")
    resid = fft_band(resid, 4500.0, 11000.0)
    resid = resid / (np.abs(resid).max() + 1e-6)
    out = np.zeros((n, 2), np.float32)
    t = np.arange(n, dtype=np.float32) / SR
    # SAME source in both channels (independent noise per channel measured as
    # L/R correlation -0.30 — a mix that cancels itself in mono). Width comes
    # from amplitude drift and a 1.5 ms offset, not from unrelated signals.
    for ch in (0, 1):
        slow = 0.5 + 0.5 * np.sin(2 * np.pi * (0.013 + 0.004 * ch) * t + ch)
        out[:, ch] = resid * slow
    d = int(0.0015 * SR)
    out[d:, 1] = out[:n - d, 1] * 0.98 + out[d:, 1] * 0.02
    return (out * level).astype(np.float32)


def _bandpass(x: np.ndarray, lo: float, hi: float, sr: int = SR) -> np.ndarray:
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / sr)
    c, w = (lo + hi) / 2.0, max((hi - lo) / 2.0, 1.0)
    g = np.exp(-0.5 * ((f - c) / w) ** 2)
    return np.fft.irfft(X * g, n=len(x)).astype(np.float32)


def bed_shimmer(n: int, seed: int = 67, level: float = 0.05, per_second: float = 1.6) -> np.ndarray:
    """Sparse high-frequency ticks: the 4-8 kHz content the mix was missing.

    Gate G13 asks for > 10 % of the bed's energy in 4-8 kHz. A drum, a drone and
    filtered noise cannot deliver that; small bright transients can, and they
    also give the mix a pulse the visuals can cut against.
    """
    rng = np.random.default_rng(seed)
    out = np.zeros((n, 2), np.float32)
    x = rng.standard_normal(n).astype(np.float32)
    k = int(SR * 0.0018)
    kern = np.hanning(max(k, 4)).astype(np.float32)
    kern /= kern.sum()
    x = x - np.convolve(x, kern, mode="same")      # remove everything slow
    count = max(int(n / SR * per_second), 1)
    env = np.zeros(n, np.float32)
    for i in range(count):
        at = int(rng.random() * (n - 1))
        # 30-90 ms decays instead of 14 ms: the same band energy with a far
        # lower crest factor (a "shhh" not a "tick"), because the true-peak
        # ceiling was preventing the loudness target from being reached
        ln = min(int(SR * (0.030 + 0.06 * rng.random())), n - at)
        t = np.arange(ln, dtype=np.float32) / SR
        env[at:at + ln] += (np.exp(-t * 22.0) * (0.5 + 0.5 * rng.random())).astype(np.float32)
    sig = x * env
    # MEASURED CORRECTION: this stem had no band-pass at all — `x` was white
    # noise above ~550 Hz, and white noise has more octaves above 8 kHz than
    # inside 4-8 kHz, so the mix measured 34.2 % in 8-16 kHz against 17.8 % in
    # the band G13 actually asks for. An exact FFT mask centres the energy.
    sig = fft_band(sig, 4400.0, 7200.0)
    sig = sig / (np.abs(sig).max() + 1e-9) * 0.9
    # kept coherent across channels on purpose: the ticks must not wreck the
    # L/R correlation that G10 measures
    out[:, 0] = sig
    out[:, 1] = sig
    return (out * level).astype(np.float32)


def bed_pad(n: int, level: float = 0.06, seed: int = 71, root: float = 440.0) -> np.ndarray:
    """Sustained mid-range pad — the crest factor fix, and a real spectral hole.

    MEASURED NEED: the score's 2000-4000 Hz band held 2.4 % of the energy and
    the mix had no sustained content between the sub drone and the 4.4-7.2 kHz
    shimmer. Loudness is carried by sustained energy, so a hit-and-drone score
    reaches -16 LUFS only by clipping or by pumping a limiter (measured: a
    15.9 dB crest needs <= 14.2 dB for the gate). A pad with a ~4 dB crest
    raises the RMS far more than it raises the peak, which is the only
    legitimate way to close that gap.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(n, dtype=np.float32) / SR
    out = np.zeros((n, 2), np.float32)
    ratios = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 4.5, 5.5)
    for i, r in enumerate(ratios):
        f = root * r
        if f > 3400.0:
            continue
        amp = 0.55 / (1.0 + 0.6 * i)
        # slow beating between the two channels only through DETUNE, never
        # through unrelated phases: unrelated phases are what made the drone
        # measure -0.245 correlation
        for ch in (0, 1):
            d = 1.0 + (0.0016 * ch * (1 if i % 2 == 0 else -1))
            lfo = 0.82 + 0.18 * np.sin(2 * np.pi * (0.07 + 0.017 * i) * t + ch * 1.7)
            out[:, ch] += (amp * lfo * np.sin(2 * np.pi * f * d * t + rng.random() * 0.0)).astype(np.float32)
    # MEASURED: a 220 Hz root put 56.0 % of the whole mix into 120-500 Hz
    # (G14 allows 58 %), because every partial landed in that one band. A
    # 440 Hz root with the mask starting at 380 Hz keeps the sustain out of
    # the bass band and fills 500-4000 Hz instead, where the score was empty.
    out = fft_band(out, 380.0, 3600.0)
    pk = float(np.abs(out).max()) + 1e-9
    return (out * (level / pk)).astype(np.float32)


def bed_tension(n: int, level: float = 0.075, seed: int = 53) -> np.ndarray:
    """A high sustained dyad — the 'something is wrong' layer. Sparse by design."""
    rng = np.random.default_rng(seed)
    t = np.arange(n, dtype=np.float32) / SR
    out = np.zeros((n, 2), np.float32)
    # MEASURED CORRECTION: two channels 6 Hz apart beat against each other and
    # average to zero correlation over a long window. Detune, do not fork.
    base_f, ph = 1174.66, rng.random() * 6.283
    for ch in (0, 1):
        f0 = base_f * (1.0 + (1 if ch else -1) * 0.0024)
        amp = 0.5 + 0.5 * np.sin(2 * np.pi * 0.007 * t + ph)
        out[:, ch] = (np.sin(2 * np.pi * f0 * t + ph)
                      + 0.3 * np.sin(2 * np.pi * f0 * 1.5 * t + ph)) * amp
    return (out * level / 1.3).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# MIX  (two-pass, because loudnorm may not share one graph with sidechain+amix)
# ─────────────────────────────────────────────────────────────────────────────

def build_voice_track(vo_files: list, out_dir, gaps: float = 0.42) -> tuple:
    """Concatenate VO chunks with frame-aligned silence; return (path, spans)."""
    import pathlib
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sil = out_dir / "sil.wav"
    C.run([C.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
           "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{gaps}", str(sil)], "silence", quiet=True)
    parts, spans, t = [], [], 0.0
    for i, f in enumerate(vo_files):
        dst = out_dir / f"vo_{i+1:02d}.wav"
        C.run([C.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(f),
               "-ar", "48000", "-ac", "2", str(dst)], f"vo {i+1}", quiet=True)
        dur = float(subprocess.run(
            [C.ffmpeg(), "-i", str(dst), "-f", "null", "-"],
            capture_output=True, text=True).stderr.split("time=")[-1].split(" ")[0].split(":")[-1]) if False else None
        if dur is None:
            import wave
            with wave.open(str(dst)) as w:
                dur = w.getnframes() / w.getframerate()
        spans.append((t, t + dur))
        parts += [dst, sil]
        t += dur + gaps
    parts = parts[:-1]
    lst = out_dir / "vo_concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts))
    voice = out_dir / "voice.wav"
    C.run([C.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-f", "concat",
           "-safe", "0", "-i", str(lst), str(voice)], "voice concat", quiet=True)
    return voice, spans


def wav_read(path) -> np.ndarray:
    import wave
    with wave.open(str(path)) as f:
        n, ch = f.getnframes(), f.getnchannels()
        a = np.frombuffer(f.readframes(n), dtype="<i2").astype(np.float32) / 32768.0
    return a.reshape(-1, ch) if ch > 1 else a.reshape(-1, 1)


def solve_mix(raw_path, out_path, target_i: float = -16.0, target_corr: float = 0.575,
              ceiling: float = 0.72, peak_guard: float = 0.68, tol: float = 0.20,
              iters: int = 8) -> tuple:
    """Solve loudness and stereo correlation on the finished bus, in numpy.

    Four measured failures decide the shape of this function:

    * NO ffmpeg LOUDNESS STAGE. `loudnorm` rides a limiter whose gain
      reduction is derived per channel: a mix balanced to +0.580 came off it
      at +0.320, and later +0.055. The gain is solved here instead, so the
      stereo image that goes in is the image that comes out.
    * BALANCER LAST. The correlation sum is gain-weighted, so anything that
      changes the level after the balance moves the correlation. Order is
      gain -> limit -> balance -> peak guard.
    * A LINKED LIMITER IS A SAFETY NET, NOT A TOOL. Over-driving it makes a
      dense mix QUIETER (measured 24.2 dB crest: -23.6 LUFS in, -27.5 out),
      so if the peak forces limiting the solve stops and reports the shortfall
      instead of pumping. Wide crest is a content problem — fixed upstream by
      cue balance and `soft_clip` — not a mastering problem.
    * THE GUARD IS A COMMON GAIN, not a limiter: both channels scale together,
      so trimming for G07/G09 cannot disturb G10/G11.
    """
    import pathlib as _pl
    out_path = _pl.Path(out_path)
    buf = wav_read(raw_path)
    probe = out_path.with_name(out_path.stem + "_probe.wav")
    gain, best, work = 1.0, None, buf
    for _ in range(iters):
        work = buf * gain
        limited = float(np.abs(work).max()) > ceiling
        if limited:
            work = limit_linked(work, ceiling=ceiling)
        # The balancer is LEVEL-NEUTRAL: narrowing the side to reach the
        # correlation target also removes side energy, and on this score that
        # cost 1.15 dB (content -16.52 LUFS -> -17.67 after balancing), which
        # left the loudness solve one limiter trigger short of the gate. The
        # RMS is restored with a COMMON gain, which is correlation-exact.
        pre_rms = float(np.sqrt((work ** 2).mean()))
        work = stereo_balance(work, target_corr)
        post_rms = float(np.sqrt((work ** 2).mean()))
        if pre_rms > 1e-9 and post_rms > 1e-9:
            work = (work * (pre_rms / post_rms)).astype(np.float32)
        pk = float(np.abs(work).max())
        if pk > peak_guard:
            work = (work * (peak_guard / pk)).astype(np.float32)
        C.wav_write(probe, work)
        i = _lufs(probe)
        if i is None:
            break
        err = float(target_i) - i
        if best is None or abs(err) < best[0]:
            best = (abs(err), work.copy(), i, limited)
        if abs(err) <= tol or limited:
            break
        gain *= 10.0 ** (err / 20.0)
    C.wav_write(out_path, best[1] if best else work)
    probe.unlink(missing_ok=True)
    return (best[2] if best else None), (best[3] if best else False)


def _lufs(path):
    st = _ffmpeg_stderr(["-hide_banner", "-nostats", "-i", str(path),
                         "-af", "loudnorm=print_format=json", "-f", "null", "-"])
    import json
    try:
        return float(json.loads(st[st.rfind("{"):st.rfind("}") + 1])["input_i"])
    except Exception:
        return None


def mix(voice, score_path, out_path, duck_ratio: int = 5, bed_gain: float = 0.42,
        target_i: float = -16.0, has_voice: bool = True, ceiling: float = 0.72,
        target_corr: float = 0.575, peak_guard: float = 0.68) -> dict:
    """Mix and normalise.

    Three laws are enforced here, each one from a measured failure:

    * NO SELF-SIDECHAIN. When an episode has no narration, voice and score are
      the same file; feeding it to the sidechain made the bed duck itself and
      the master measured -18.26 LUFS against a -16.5 target.
    * NO SIDECHAIN ON THE MIX BUS and NO ffmpeg LOUDNESS STAGE. A single
      dynamic loudnorm pass missed the target by 1.8 LU, and its limiter is
      per-channel: it rewrote the correlation of an already-balanced mix. The
      gain is now solved iteratively in numpy and the limiter is linked, so the
      stage cannot alter the stereo image it was given.
    """
    import numpy as _np  # noqa: F401  (kept for the path below)
    import json
    import pathlib
    out_path = pathlib.Path(out_path)
    raw = out_path.with_name(out_path.stem + "_raw.wav")

    if has_voice:
        graph = (f"[1:a]volume={bed_gain}[bedx];"
                 f"[bedx][0:a]sidechaincompress=threshold=0.030:ratio={duck_ratio}"
                 ":attack=14:release=380[duck];"
                 "[0:a][duck]amix=inputs=2:duration=first:normalize=0,"
                 "aresample=48000[a]")
        C.run([C.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
               "-i", str(voice), "-i", str(score_path), "-filter_complex", graph,
               "-map", "[a]", "-c:a", "pcm_s16le", str(raw)], "mix pass 1 (duck)")
    else:
        # music-led: the score IS the bus, so hand it straight to the solver
        raw = pathlib.Path(score_path)
        C.say("  mix pass 1 (music-led: score straight to the solver)")

    # gain -> linked limit -> balance, solved against measurements (G08-G11)
    got, limited = solve_mix(raw, out_path, target_i=float(target_i),
                             target_corr=float(target_corr), ceiling=float(ceiling),
                             peak_guard=float(peak_guard))
    note = " (peak-limited: crest too wide for the target)" if limited else ""
    C.say(f"  mix: measured {got:.2f} LUFS (target {target_i}){note}")
    return measure(out_path)


# ─────────────────────────────────────────────────────────────────────────────
# MEASURE  (what was actually measured, never what was intended)
# ─────────────────────────────────────────────────────────────────────────────

def _ffmpeg_stderr(args: list[str]) -> str:
    return subprocess.run([C.ffmpeg()] + args, capture_output=True, text=True).stderr


def measure(path, spans: list | None = None) -> dict:
    import json
    st = _ffmpeg_stderr(["-hide_banner", "-nostats", "-i", str(path),
                         "-af", "loudnorm=print_format=json", "-f", "null", "-"])
    j = st[st.rfind("{"):st.rfind("}") + 1]
    try:
        d = json.loads(j)
    except Exception:
        d = {}
    out = {"i_lufs": d.get("input_i"), "lra": d.get("input_lra"), "lra_low": d.get("input_lra_low"),
           "lra_high": d.get("input_lra_high"), "true_peak": d.get("input_tp"),
           "target_offset": d.get("target_offset")}

    # decoded-domain peak: the codec overshoots the PCM limiter (law #3)
    pk = _ffmpeg_stderr(["-hide_banner", "-nostats", "-i", str(path),
                         "-af", "volumedetect", "-f", "null", "-"])
    for line in pk.splitlines():
        if "max_volume" in line:
            out["decoded_peak_dbfs"] = float(line.split("max_volume:")[1].split("dB")[0].strip())
        if "mean_volume" in line:
            out["mean_volume_dbfs"] = float(line.split("mean_volume:")[1].split("dB")[0].strip())
    return out


def stereo_report(path) -> dict:
    """L/R correlation and side/mid energy — is the mix actually stereo?"""
    import tempfile
    import wave
    import pathlib
    tmp = pathlib.Path(tempfile.mkdtemp()) / "m.wav"
    C.run([C.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(path),
           "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(tmp)], "decode for stereo", quiet=True)
    with wave.open(str(tmp)) as w:
        raw = w.readframes(w.getnframes())
    a = np.frombuffer(raw, dtype="<i2").astype(np.float32).reshape(-1, 2) / 32768.0
    l, r = a[:, 0], a[:, 1]
    denom = (np.sqrt((l ** 2).sum()) * np.sqrt((r ** 2).sum()) + 1e-9)
    corr = float((l * r).sum() / denom)
    mid, side = (l + r) / 2, (l - r) / 2
    sm = float((side ** 2).sum() / ((mid ** 2).sum() + 1e-9))
    return {"lr_correlation": corr, "side_mid": sm,
            "verdict": "stereo" if corr < 0.97 else "effectively mono"}


def band_energy(path, spans: list | None = None) -> dict:
    """Per-band share of energy, optionally split by voice presence.

    A whole-file spectral target grades the wrong thing once narration covers
    most of the runtime (ledger #35). With spans, the report separates
    VO-absent (the bed) from VO-present (the voice).
    """
    import pathlib
    import tempfile
    import wave
    tmp = pathlib.Path(tempfile.mkdtemp()) / "b.wav"
    C.run([C.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(path),
           "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(tmp)], "decode for bands", quiet=True)
    with wave.open(str(tmp)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    bands = [(20, 120), (120, 500), (500, 2000), (2000, 4000), (4000, 8000), (8000, 16000)]

    def share(x, label):
        if len(x) < 4096:
            return None
        f = np.fft.rfft(x * np.hanning(len(x)))
        p = (np.abs(f) ** 2)
        fr = np.fft.rfftfreq(len(x), 1 / SR)
        tot = p.sum() + 1e-12
        return {f"{lo}-{hi}": float(p[(fr >= lo) & (fr < hi)].sum() / tot * 100) for lo, hi in bands}

    rep = {"whole": share(a, "all")}
    if spans:
        mask = np.zeros(len(a), bool)
        for s0, s1 in spans:
            mask[int(s0 * SR):int(s1 * SR)] = True
        rep["vo_present"] = share(a[mask], "vo")
        rep["vo_absent"] = share(a[~mask], "bed")
        rep["vo_coverage_pct"] = float(mask.mean() * 100)
    return rep
