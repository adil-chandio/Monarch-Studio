#!/usr/bin/env python3
"""THE GRAVITY OF THE PHONE v2 — procedural score (numpy).  122.4 BPM, E minor climb → E major relief.

The score is event-locked to scene.TL: beat 10 = field onset (4.90 s), beat 35 = hot word (17.157 s),
beat 38 = 'tum' (18.63 s).  Every element is an original synthesised instrument: additive plucks (music box /
pizzicato), sub + saw bass through a block-swept low-pass, soft paper kick, noise hats/shaker/paper-snap,
detuned-saw pad, inharmonic bells, a dotted-eighth ping-pong delay, side-chain pumping, stutter gates on the
slips and a tape-stop when the phone's power dies.  render() returns (L, R) float arrays of scene.DUR seconds.
"""
import math
import numpy as np
from scipy.signal import butter, lfilter, lfilter_zi

from scene import TL, DUR, BPM, BEAT

SR = 48000
N = int(DUR * SR)
EVENTS = []          # (t, name, gain) — merged into the cue ledger by audio.py


def B(n):
    """Time of beat n on the grid (beat 0 = 0.0 s)."""
    return n * BEAT


def n2f(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def env_ad(dur, a=0.004, tau=0.3, hold=0.0):
    t = tt(dur)
    e = np.exp(-np.maximum(0, t - a - hold) / tau)
    e[t < a] = t[t < a] / a
    return e


def fade(x, fin=0.002, fout=0.01):
    x = np.array(x, float)
    ni, no = int(fin * SR), int(fout * SR)
    if ni and len(x) > ni:
        x[:ni] *= np.linspace(0, 1, ni)
    if no and len(x) > no:
        x[-no:] *= np.linspace(1, 0, no)
    return x


def lp(x, fc, order=2):
    b, a = butter(order, min(fc, SR / 2 - 100) / (SR / 2))
    return lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = butter(order, max(fc, 10) / (SR / 2), btype="high")
    return lfilter(b, a, x)


def bp(x, lo, hi, order=2):
    b, a = butter(order, [lo / (SR / 2), min(hi, SR / 2 - 100) / (SR / 2)], btype="band")
    return lfilter(b, a, x)


def sweep_lp(x, fc_curve, block=240):
    """Time-varying 2-pole low-pass; fc_curve = array of cutoff Hz per sample."""
    y = np.empty_like(x)
    zi = None
    for i in range(0, len(x), block):
        fc = float(np.clip(fc_curve[min(i, len(fc_curve) - 1)], 40, SR / 2 - 200))
        b, a = butter(2, fc / (SR / 2))
        if zi is None:
            zi = lfilter_zi(b, a) * x[0]
        y[i:i + block], zi = lfilter(b, a, x[i:i + block], zi=zi)
    return y


# ── instruments ──────────────────────────────────────────────────────────────
def pluck(f, dur=1.2, bright=0.6, decay=0.45, body=1.0):
    """Additive plucked string / music-box tone: harmonics decay faster the higher they are."""
    t = tt(dur)
    out = np.zeros_like(t)
    K = 14
    for k in range(1, K + 1):
        fk = f * k * (1 + 0.0004 * k * k)       # slight stiffness inharmonicity
        if fk > SR * 0.45:
            break
        amp = (1.0 / k ** (1.25 + (1 - bright) * 1.3))
        dk = decay / (1 + 0.55 * (k - 1))
        out += amp * np.sin(2 * np.pi * fk * t + 0.3 * k) * np.exp(-t / dk)
    pick = (np.random.default_rng(int(f * 7)).standard_normal(len(t)) * np.exp(-t / 0.0025)) * 0.25
    out = out + hp(pick, 2500)
    out *= env_ad(dur, 0.0015, 10.0)
    return fade(out * 0.5 * body, 0.001, 0.02)


def bell(f, dur=1.6, gain=1.0):
    t = tt(dur)
    parts = ((1.0, 1.0, 1.0), (2.76, 0.45, 0.55), (5.40, 0.22, 0.32), (8.93, 0.10, 0.2))
    out = np.zeros_like(t)
    for r, a, d in parts:
        if f * r < SR * 0.45:
            out += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (dur * d * 0.5))
    return fade(out * 0.35 * gain, 0.001, 0.05)


def sub(f, dur, level=1.0, a=0.004, r=0.08):
    t = tt(dur)
    e = env_ad(dur, a, 10.0)
    n_r = int(r * SR)
    if n_r and len(e) > n_r:
        e[-n_r:] *= np.linspace(1, 0, n_r)
    x = np.sin(2 * np.pi * f * t) + 0.12 * np.sin(2 * np.pi * 2 * f * t)
    return x * e * level


def saw(f, dur):
    t = tt(dur)
    return 2 * ((t * f) % 1.0) - 1


def bass_saw(f, dur, fc0, fc1, level=1.0):
    x = saw(f, dur) * 0.6 + saw(f * 1.004, dur) * 0.4
    fc = np.geomspace(fc0, fc1, len(x))
    x = sweep_lp(x, fc)
    e = env_ad(dur, 0.004, 10.0)
    n_r = int(0.03 * SR)
    e[-n_r:] *= np.linspace(1, 0, n_r)
    return np.tanh(1.6 * x) * e * level * 0.5


def kick(dur=0.32, f0=140, f1=42, level=1.0, click=0.5):
    t = tt(dur)
    ph = 2 * np.pi * (f1 * t + (f0 - f1) * 0.045 * (1 - np.exp(-t / 0.045)))
    x = np.sin(ph) * np.exp(-t / 0.11)
    x += click * hp(np.random.default_rng(3).standard_normal(len(t)) * np.exp(-t / 0.004), 1800) * 0.4
    return fade(np.tanh(1.8 * x) * level, 0.0005, 0.02)


def hat(dur=0.045, level=1.0, open_=False):
    rng = np.random.default_rng(11 if not open_ else 12)
    d = 0.16 if open_ else dur
    t = tt(d)
    x = hp(rng.standard_normal(len(t)), 7600, 4) * np.exp(-t / (d * 0.33))
    return fade(x * 0.55 * level, 0.0005, 0.005)


def shaker(level=1.0):
    rng = np.random.default_rng(13)
    t = tt(0.09)
    x = bp(rng.standard_normal(len(t)), 2600, 7000) * np.sin(np.pi * np.clip(t / 0.09, 0, 1)) ** 0.6
    return fade(x * 0.5 * level)


def paper_snap(level=1.0):
    """A clap made of three paper flicks — the world's snare."""
    rng = np.random.default_rng(17)
    t = tt(0.16)
    x = np.zeros_like(t)
    for d, g in ((0.0, 1.0), (0.011, 0.8), (0.024, 0.65)):
        i = int(d * SR)
        n = len(t) - i
        x[i:] += g * bp(rng.standard_normal(n), 1200, 4200) * np.exp(-np.arange(n) / SR / 0.028)
    return fade(x * 0.6 * level, 0.0005, 0.02)


def pad(midis, dur, fc0=400, fc1=1800, level=1.0, attack=0.25, release=0.4):
    x = np.zeros(int(dur * SR))
    for m in midis:
        f = n2f(m)
        for det in (-7, 0, 6):
            x += saw(f * 2 ** (det / 1200), dur) / (3 * len(midis))
    fc = np.geomspace(fc0, fc1, len(x))
    x = sweep_lp(x, fc)
    e = np.ones_like(x)
    na, nr = int(attack * SR), int(release * SR)
    e[:na] = np.linspace(0, 1, na) ** 1.5
    e[-nr:] *= np.linspace(1, 0, nr) ** 1.2
    return x * e * level * 0.9


def noise_swell(dur, level=1.0, lo=300, hi=6000):
    rng = np.random.default_rng(23)
    t = tt(dur)
    fc = np.geomspace(lo, hi, len(t))
    x = sweep_lp(rng.standard_normal(len(t)), fc) * (t / dur) ** 2.2
    return fade(x * 0.5 * level, 0.01, 0.01)


def slide(f0, f1, dur=0.22, level=1.0):
    """A soft descending 'wah' (sine with a bit of 3rd harmonic), for the upside-down word."""
    t = tt(dur)
    f = f0 * (f1 / f0) ** (t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = (np.sin(ph) + 0.18 * np.sin(3 * ph)) * env_ad(dur, 0.01, 0.12)
    return fade(x * 0.5 * level, 0.005, 0.03)


# ── bus helpers ──────────────────────────────────────────────────────────────
class Bus:
    def __init__(self):
        self.L = np.zeros(N)
        self.R = np.zeros(N)

    def add(self, sig, t, gain=1.0, pan=0.0):
        i0 = int(round(t * SR))
        if i0 >= N:
            return
        s0 = 0
        if i0 < 0:
            s0, i0 = -i0, 0
        seg_ = np.asarray(sig, float)[s0:s0 + (N - i0)] * gain
        gl, gr = math.sqrt(0.5 * (1 - pan)), math.sqrt(0.5 * (1 + pan))
        self.L[i0:i0 + len(seg_)] += seg_ * gl
        self.R[i0:i0 + len(seg_)] += seg_ * gr


def pingpong(L, R, time_s, fb=0.38, mix=0.5, damp=3200):
    d = int(time_s * SR)
    outL, outR = L.copy(), R.copy()
    bufL, bufR = L.copy(), R.copy()
    for k in range(1, 7):
        g = fb ** k * mix
        if g < 0.01:
            break
        bufL, bufR = lp(bufR, damp), lp(bufL, damp)      # swap channels each repeat
        sh = d * k
        if sh >= N:
            break
        outL[sh:] += bufL[:N - sh] * g
        outR[sh:] += bufR[:N - sh] * g
    return outL, outR


def room(L, R):
    taps = ((0.011, 0.22, 1), (0.017, 0.17, -1), (0.023, 0.13, 1), (0.031, 0.10, -1), (0.047, 0.07, 1))
    outL, outR = L.copy(), R.copy()
    for d, g, side in taps:
        s = int(d * SR)
        src_l, src_r = (L, R) if side > 0 else (R, L)
        outL[s:] += src_l[:N - s] * g
        outR[s:] += src_r[:N - s] * g
    return lp(outL, 9000), lp(outR, 9000)


def sidechain_env(kick_times, depth=0.55, rel=0.26):
    e = np.ones(N)
    t = np.arange(N) / SR
    for tk in kick_times:
        i0 = int(tk * SR)
        i1 = min(N, int((tk + rel * 3) * SR))
        if i0 >= N:
            continue
        seg_t = t[i0:i1] - tk
        e[i0:i1] = np.minimum(e[i0:i1], 1 - depth * np.exp(-seg_t / rel) * (1 - np.exp(-seg_t / 0.004)))
    return e


def tape_stop(L, R, t0, t1):
    """Everything after t0 slows to a stop by t1 (pitch and speed fall together), silence after."""
    i0, i1 = int(t0 * SR), int(t1 * SR)
    n = i1 - i0
    u = np.arange(n) / n
    speed = (1 - u) ** 1.6
    pos = i0 + np.cumsum(speed)
    outL, outR = L.copy(), R.copy()
    idx = np.arange(N)
    outL[i0:i1] = np.interp(pos, idx, L) * (1 - u) ** 0.5
    outR[i0:i1] = np.interp(pos, idx, R) * (1 - u) ** 0.5
    outL[i1:] = 0.0
    outR[i1:] = 0.0
    return outL, outR


def gate(L, R, t, dur=0.045):
    i0, i1 = int(t * SR), int((t + dur) * SR)
    r = int(0.002 * SR)
    m = np.ones(N)
    m[i0:i1] = 0.0
    m[i0 - r:i0] = np.linspace(1, 0, r)
    m[i1:i1 + r] = np.linspace(0, 1, r)
    return L * m, R * m


def ev(t, name, gain):
    EVENTS.append((round(float(t), 3), name, round(float(gain), 3)))


# ── the score ────────────────────────────────────────────────────────────────
E1, E2, E3, E4, E5, E6 = 28, 40, 52, 64, 76, 88
MOTIF_MIN = [E5, E5 - 5, E5 - 9, E5 - 5]        # E5 B4 G4 B4  (music box, minor)
MOTIF_MAJ = [E5, E5 - 5, E5 - 8, E5 - 5]        # E5 B4 G#4 B4 (same box, major)
ARP = [0, 3, 7, 10, 12, 10, 7, 3, 0, 3, 7, 12, 15, 12, 7, 3]   # minor-7 arpeggio, 16ths, one bar


def render():
    plk = Bus()        # plucks / bells (get ping-pong)
    drum = Bus()       # kick / hats / snaps (dry)
    bass = Bus()       # sub + saw bass (side-chained)
    padb = Bus()       # pads (side-chained, roomed)
    kicks_full, kicks_half = [], []

    # ── I. intro pulse (beats 0–9.2): the box motif + half-time heartbeat pulse ────────────
    for n in range(0, 19):                     # 8th notes 0 → 4.5 s
        t = B(n / 2)
        if t >= 4.47:
            break
        m = MOTIF_MIN[n % 4]
        g = 0.26 + 0.05 * (n % 2 == 0)
        if t >= 3.9:                           # the last half-beat before the hole climbs
            m += [2, 3, 5, 7][min(3, n - 16)] if n >= 16 else 0
        plk.add(pluck(n2f(m), 1.4, 0.55, 0.5), t, g, pan=-0.15 + 0.3 * (n % 2))
    ev(0.0, "music_box_motif_intro", 0.3)
    for n in range(0, 10, 2):                  # heartbeat pulse every 2 beats
        t = B(n)
        drum.add(kick(0.3, 110, 40, 0.22, click=0.1), t, 1.0)
        kicks_half.append(t)
    ev(0.0, "music_pulse_halftime", 0.22)
    # bed enters with the hook cut: sub 8ths + pad Em opening
    for n in range(8, 18):                     # 8ths from beat 4 (1.96 s)
        t = B(n / 2)
        if t > 4.45:
            break
        bass.add(sub(n2f(E1), BEAT * 0.45, 0.42), t)
    padb.add(pad([E2, E2 + 7, E3 + 3, E4 - 5], 4.5 - 1.96, 260, 2200, 0.55, 0.5, 0.15), 1.96)
    ev(1.96, "music_pad_em_open", 0.55)
    plk.add(noise_swell(0.58, 0.5, 400, 7000), 3.9, 0.6)
    ev(3.9, "music_reverse_swell", 0.5)
    for i, m in enumerate((E5 + 2, E5 + 3, E5 + 5, E5 + 7)):   # 16ths climbing into the hole
        plk.add(pluck(n2f(m), 0.5, 0.7, 0.25), 4.02 + i * 0.11, 0.3, pan=-0.3 + 0.2 * i)

    # ── II. the drop (beat 10 = field onset) → groove to beat 22, fill, letgo ──────────────
    t_on = TL["field_on"]
    drum.add(kick(0.5, 170, 38, 0.95, 0.7), t_on, 1.0)
    bass.add(bass_saw(n2f(E1), 0.7, 3200, 120, 0.9), t_on)
    bass.add(sub(n2f(E1), 0.7, 0.8, 0.003, 0.2), t_on)
    drum.add(hp(noise_swell(0.5, 1.0, 8000, 2000)[::-1], 2500), t_on, 0.35)
    ev(t_on, "music_drop_boom", 0.95)
    groove_end = B(22)                          # 10.78 s: the fill starts
    for n in range(10, 23):                     # beats 10..22
        t = B(n)
        bar_pos = (n - 10) % 4
        tr = [0, 0, 2, 3, 5, 7, 7][min(6, (n - 10) // 2)]       # the hypnotic climb: +0 +0 +2 +3 +5 +7
        breakdown = TL["look_lens"] <= t < TL["look_end"]
        if n < 22:
            if not breakdown:
                drum.add(kick(0.3, 140, 42, 0.62, 0.45), t, 1.0)
                kicks_full.append(t)
                if bar_pos in (1, 3):
                    drum.add(paper_snap(0.55), t, 1.0, pan=0.1)
            else:
                kicks_full.append(t)            # keep the pump even when the kick is silent
            # sub 8ths, saw 8ths pattern, arp 16ths, hats 16ths, shaker off-8ths
            for h in range(2):
                th = t + h * BEAT / 2
                if th >= groove_end:
                    break
                bass.add(sub(n2f(E1 + (tr if tr < 5 else tr - 12)), BEAT * 0.46, 0.5), th)
                sm = [E1, E1, E1, E1 + 3, E1, E1, E1 + 10, E1 + 7][(bar_pos * 2 + h) % 8]
                if not breakdown:
                    fc_t = 380 + 1500 * ((t - t_on) / (groove_end - t_on)) ** 1.4
                    bass.add(bass_saw(n2f(sm + (tr if tr < 5 else tr - 12)), BEAT * 0.48, fc_t * 1.3, fc_t * 0.7, 0.42), th)
                shk = shaker(0.5 if h == 1 else 0.28)
                drum.add(shk, th + BEAT / 4, 1.0, pan=0.35)
            for q in range(4):
                tq = t + q * BEAT / 4
                if tq >= groove_end:
                    break
                note = E4 + ARP[(bar_pos * 4 + q) % 16] + tr
                brt = 0.35 + 0.55 * ((tq - t_on) / (groove_end - t_on))
                plk.add(pluck(n2f(note), 0.7, brt, 0.22, 0.9 if not breakdown else 0.55), tq,
                        0.22 + 0.06 * (q == 0), pan=-0.35 + 0.7 * ((q + bar_pos) % 2))
                drum.add(hat(0.04, 0.42 if q % 2 else 0.25), tq, 1.0, pan=-0.25)
            if bar_pos == 3:
                drum.add(hat(0.0, 0.3, open_=True), t + BEAT / 2, 1.0, pan=-0.2)
    ev(B(10), "music_groove_em_climb", 0.6)
    ev(TL["look_lens"], "music_breakdown_pulse_only", 0.5)
    # bells on the three dings (in key: B5 · D6 · E6)
    for td, m in ((TL["ding1"], E5 + 7), (TL["ding2"], E5 + 10), (TL["ding3"], E6)):
        plk.add(bell(n2f(m), 1.8, 1.0), td, 0.5, pan=0.3)
        ev(td, "music_bell_in_key", 0.5)
    # fill into the let-go: paper snaps accelerating 10.78 → 11.0
    tf = groove_end
    k = 0
    while tf < TL["letgo"] - 0.01:
        drum.add(paper_snap(0.3 + 0.03 * k), tf, 1.0, pan=-0.2 + 0.05 * k)
        tf += 0.055 - 0.0025 * k
        k += 1
    ev(groove_end, "music_snap_fill", 0.45)

    # ── III. fall & restore: reverse swell → land hit → chord → tape stop (12.0) ───────────
    plk.add(noise_swell(TL["land"] - TL["letgo"], 0.6, 300, 5000), TL["letgo"], 0.6)
    drum.add(kick(0.45, 160, 40, 0.9, 0.6), TL["land"], 1.0)
    bass.add(sub(n2f(E1), 0.9, 0.85, 0.003, 0.3), TL["land"])
    padb.add(pad([E2, E2 + 7, E3 + 3, E4], TL["glow_off"] + 0.3 - TL["land"], 1400, 500, 0.42, 0.01, 0.05), TL["land"])
    for i, m in enumerate((E4, E4 + 3, E4 + 7, E4 + 12)):
        plk.add(pluck(n2f(m), 0.9, 0.5, 0.35), TL["land"] + 0.02 * i, 0.3, pan=-0.3 + 0.2 * i)
    ev(TL["land"], "music_land_hit_em", 0.9)
    ev(TL["glow_off"], "music_tape_stop", 1.0)

    # ── busses → effects → stereo ───────────────────────────────────────────────
    scF = sidechain_env(kicks_full, 0.55, 0.26)
    scH = sidechain_env(kicks_half, 0.35, 0.3)
    sc = np.minimum(scF, scH)
    pL, pR = pingpong(plk.L, plk.R, BEAT * 0.75, 0.38, 0.55)
    padL, padR = room(padb.L * sc, padb.R * sc)
    L = pL * 1.0 + drum.L + bass.L * sc + padL
    R = pR * 1.0 + drum.R + bass.R * sc + padR
    # slips: stutter gates (the music loses its grip with his hands)
    for ts in (TL["slip1"], TL["slip2"]):
        L, R = gate(L, R, ts, 0.05)
        L, R = gate(L, R, ts + 0.09, 0.03)
    ev(TL["slip1"], "music_stutter_gate", 1.0)
    # the phone's power dies: tape-stop, then nothing until the relief chord
    L, R = tape_stop(L, R, TL["glow_off"], TL["glow_off"] + 0.17)
    # sections IV + V live on fresh busses (the tape-stop wiped the main ones)
    t_rel = TL["stand"]
    pl2 = Bus(); dr2 = Bus(); ba2 = Bus(); pd2 = Bus()
    kicks_rel = _render_after(pl2, dr2, ba2, pd2, t_rel)
    sc2 = sidechain_env(kicks_rel, 0.35, 0.3)
    pL2, pR2 = pingpong(pl2.L, pl2.R, BEAT * 0.75, 0.38, 0.55)
    pdL2, pdR2 = room(pd2.L * sc2, pd2.R * sc2)
    relL = pL2 + dr2.L + ba2.L * sc2 + pdL2
    relR = pR2 + dr2.R + ba2.R * sc2 + pdR2
    L = L + relL
    R = R + relR
    # gentle bus tone + safety
    L, R = hp(L, 28), hp(R, 28)
    peak = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    g = 0.62 / peak
    return L * g, R * g


def _render_after(plk, drum, bass, padb, t_rel):
    """Sections IV (relief, E major) + V (punchline) on fresh busses; returns the half-time kick times."""
    kicks = []
    padb.add(pad([E2, E2 + 7, E3, E3 + 4], TL["cut_s6"] - t_rel + 0.4, 500, 1800, 0.42, 0.6, 0.6), t_rel)
    for i, m in enumerate((E3, E3 + 4, E3 + 7, E4, E4 + 4)):
        plk.add(pluck(n2f(m), 2.2, 0.5, 0.8), t_rel + i * BEAT / 2, 0.34, pan=-0.3 + 0.15 * i)
    n = 28
    while B(n) < TL["cut_s6"] - 0.05:
        t = B(n)
        if n % 2 == 0:
            drum.add(kick(0.3, 110, 40, 0.3, 0.12), t, 1.0)
            kicks.append(t)
            bass.add(sub(n2f(E1), BEAT * 1.6, 0.4, 0.01, 0.3), t)
        for h in range(2):
            th = t + h * BEAT / 2
            if th >= TL["cut_s6"] - 0.05:
                break
            m = MOTIF_MAJ[(n * 2 + h) % 4]
            plk.add(pluck(n2f(m), 1.4, 0.55, 0.5), th, 0.24 + 0.1 * ((th - t_rel) / 5), pan=-0.15 + 0.3 * h)
        n += 1
    for tw, ms in ((TL["line1"], (E2, E3)), (TL["line2"], (E2 + 7, E3 + 7))):
        for m in ms:
            bass.add(sub(n2f(m), 0.6, 0.35, 0.004, 0.2), tw)
        drum.add(paper_snap(0.4), tw, 1.0)
    bass.add(sub(n2f(E1), 1.4, 0.95, 0.003, 0.5), TL["hot"])
    drum.add(kick(0.5, 150, 38, 0.8, 0.5), TL["hot"], 1.0)
    plk.add(bell(n2f(E6), 2.0, 1.0), TL["hot"], 0.55, pan=0.1)
    for i, m in enumerate((E4, E4 + 4, E4 + 7, E5)):
        plk.add(pluck(n2f(m), 1.6, 0.6, 0.6), TL["hot"] + 0.015 * i, 0.3, pan=-0.3 + 0.2 * i)
    padb.add(pad([E2, E2 + 7, E3, E3 + 4, E4], TL["cut_s6"] - TL["hot"] + 0.3, 900, 2600, 0.38, 0.02, 0.5), TL["hot"])
    plk.add(pluck(n2f(E5), 1.2, 0.6, 0.5), TL["moral1"], 0.36, pan=-0.1)
    plk.add(pluck(n2f(E5 - 5), 1.2, 0.6, 0.5), TL["moral2"], 0.34, pan=0.1)
    for i, m in enumerate((E5 - 5, E5 - 9, E5 - 12)):
        plk.add(pluck(n2f(m), 0.6, 0.6, 0.3), TL["moral3"] + 0.07 * i, 0.3, pan=0.2 - 0.2 * i)
    plk.add(slide(880, 330, 0.3, 0.9), TL["moral3"] + 0.04, 0.42)
    ev(t_rel, "music_relief_e_major", 0.5)
    ev(B(28), "music_box_motif_major", 0.3)
    ev(TL["hot"], "music_hot_word_boom", 0.95)
    ev(TL["moral1"], "music_word_ping", 0.36)
    ev(TL["moral3"], "music_upside_down_slide", 0.42)
    return kicks


if __name__ == "__main__":
    import time, wave
    t0 = time.time()
    L, R = render()
    x = np.stack([L, R], 1)
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open("../audio/music_only.wav", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    rms = 20 * math.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
    print(f"music rendered in {time.time() - t0:.1f}s  peak {np.abs(x).max():.3f}  rms {rms:.1f} dBFS  events {len(EVENTS)}")
