#!/usr/bin/env python3
"""THE GRAVITY OF THE PHONE — sound design.  One cue per visual event, all synthesised in numpy
from the same timeline (scene.TL / scene.PROPS) the picture is rendered from.

  python3 audio.py --out ../audio/mix.wav [--vo ../audio/vo_meaning.mp3]
Writes the raw mix (float WAV, 48 kHz stereo) + a JSON ledger of every cue placed.
Loudness normalisation and the mux live in build.py.
"""
import argparse, json, math, pathlib, subprocess, sys
import numpy as np
from scipy import signal

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scene as S                      # noqa: E402
from scene import TL, DUR, PROPS, clamp, lerp, smooth, seg, ease_in, ease_out   # noqa: E402

SR = 48000
N = int(DUR * SR)
rng = np.random.default_rng(20261014)
LEDGER = []


# ── primitives ───────────────────────────────────────────────────────────────
def tt(dur):
    return np.arange(int(dur * SR)) / SR


def sine(f, dur, phase=0.0):
    return np.sin(2 * np.pi * f * tt(dur) + phase)


def sweep(f0, f1, dur, curve=1.0):
    t = tt(dur)
    u = (t / max(dur, 1e-6)) ** curve
    f = f0 * (f1 / f0) ** u
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph)


def noise(dur):
    return rng.standard_normal(int(dur * SR))


def bp(x, lo, hi, order=4):
    lo = max(20.0, lo); hi = min(hi, SR / 2 - 100)
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, fc, order=4):
    sos = signal.butter(order, min(fc, SR / 2 - 100), btype="low", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def hp(x, fc, order=2):
    sos = signal.butter(order, max(fc, 20), btype="high", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def env_exp(dur, tau, attack=0.002):
    t = tt(dur)
    e = np.exp(-t / tau)
    a = np.minimum(1.0, t / max(attack, 1e-5))
    return e * a


def env_adsr(dur, a=0.01, d=0.05, s=0.7, r=0.1):
    n = int(dur * SR)
    e = np.ones(n) * s
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nd:
        e[na:na + nd] = np.linspace(1, s, nd)[:max(0, min(nd, n - na))]
    if nr and nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def fade(x, fin=0.005, fout=0.01):
    x = x.copy()
    ni, no = int(fin * SR), int(fout * SR)
    if ni and len(x) > ni:
        x[:ni] *= np.linspace(0, 1, ni)
    if no and len(x) > no:
        x[-no:] *= np.linspace(1, 0, no)
    return x


class Mix:
    def __init__(self):
        self.L = np.zeros(N)
        self.R = np.zeros(N)

    def add(self, sig, t, gain=1.0, pan=0.0, name="", loop=False):
        """Place `sig` at time t (s).  pan -1..1.  loop=True also places it DUR seconds later
        (hook sounds defined at negative loop-time)."""
        sig = np.asarray(sig, float) * gain
        gl, gr = math.sqrt(0.5 * (1 - pan)), math.sqrt(0.5 * (1 + pan))
        placed = False
        for t0 in ((t, t + DUR) if loop else (t,)):
            i0 = int(round(t0 * SR))
            s0 = 0
            if i0 < 0:
                s0 = -i0
                i0 = 0
            if s0 >= len(sig) or i0 >= N:
                continue
            seg_ = sig[s0:s0 + (N - i0)]
            self.L[i0:i0 + len(seg_)] += seg_ * gl
            self.R[i0:i0 + len(seg_)] += seg_ * gr
            placed = True
        if name and placed:
            LEDGER.append(dict(t=round(float(t), 3), cue=name, gain=round(float(gain), 3), dur=round(len(sig) / SR, 3)))
        return placed


# ── voices (each a small instrument) ─────────────────────────────────────────
def v_buzz_burst(dur=0.38):
    t = tt(dur)
    tone = 0.6 * np.sin(2 * np.pi * 182 * t) + 0.3 * np.sin(2 * np.pi * 364 * t) + 0.12 * np.sin(2 * np.pi * 546 * t)
    am = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 25 * t) + 0.2)
    rattle = bp(noise(dur), 1800, 5200) * 0.35
    x = (tone * (0.6 + 0.4 * am) + rattle * am) * env_adsr(dur, 0.01, 0.02, 0.85, 0.05)
    return lp(x, 6000)


def padto(x, n):
    """Zero-pad or trim x to n samples."""
    if len(x) >= n:
        return x[:n]
    return np.pad(x, (0, n - len(x)))


def v_click(gain_hi=1.0, dur=0.012, lo=1500, hi=5000):
    return bp(noise(dur), lo, hi) * env_exp(dur, dur / 3) * gain_hi


def v_wood_knock(dur=0.16, f=190):
    t = tt(dur)
    body = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.035) + 0.5 * np.sin(2 * np.pi * f * 2.3 * t) * np.exp(-t / 0.018)
    return body + padto(v_click(0.7, 0.008, 800, 3000), len(t))


def v_thud(dur=0.35, f=58):
    t = tt(dur)
    return (np.sin(2 * np.pi * (f + 40 * np.exp(-t / 0.03)) * t) * np.exp(-t / 0.09)
            + 0.4 * lp(noise(dur), 300) * np.exp(-t / 0.05))


def v_ceramic(dur=0.28):
    t = tt(dur)
    x = (np.sin(2 * np.pi * 2630 * t) * np.exp(-t / 0.08) + 0.6 * np.sin(2 * np.pi * 3920 * t) * np.exp(-t / 0.05)
         + 0.4 * np.sin(2 * np.pi * 5210 * t) * np.exp(-t / 0.03))
    return x + padto(v_click(0.8, 0.006, 2000, 8000), len(t))


def v_metal_ring(dur=0.9):
    t = tt(dur)
    x = (np.sin(2 * np.pi * 1130 * t) * np.exp(-t / 0.30) + 0.7 * np.sin(2 * np.pi * 1655 * t) * np.exp(-t / 0.22)
         + 0.5 * np.sin(2 * np.pi * 2910 * t) * np.exp(-t / 0.12) + 0.3 * np.sin(2 * np.pi * 4420 * t) * np.exp(-t / 0.07))
    return x * 0.6


def v_book_slap(dur=0.14):
    t = tt(dur)
    return bp(noise(dur), 180, 2600) * np.exp(-t / 0.022) + 0.6 * np.sin(2 * np.pi * 120 * t) * np.exp(-t / 0.03)


def v_pot_clack(dur=0.22):
    t = tt(dur)
    return (np.sin(2 * np.pi * 910 * t) * np.exp(-t / 0.05) + 0.5 * np.sin(2 * np.pi * 1480 * t) * np.exp(-t / 0.03)
            + padto(v_click(1.0, 0.008, 700, 2500), len(t)))


def v_page_flutter(dur=0.45, n=6):
    x = np.zeros(int(dur * SR))
    for i in range(n):
        d = 0.03 + 0.04 * rng.random()
        s = bp(noise(d), 1800, 7000) * env_exp(d, d / 2.5)
        i0 = int(rng.random() * (len(x) - len(s)))
        x[i0:i0 + len(s)] += s * (0.6 + 0.6 * rng.random())
    return x


def v_scrape(dur, lo, hi, env):
    """Material scrape whose loudness follows `env` (array sampled at SR)."""
    x = bp(noise(dur), lo, hi)
    e = np.interp(np.arange(len(x)) / SR, np.linspace(0, dur, len(env)), env)
    return x * e


def v_whoosh(dur, f0=300, f1=2400, rise=True):
    t = tt(dur)
    u = t / dur
    x = noise(dur)
    # time-varying band: cheap approximation with 5 crossfaded bands
    out = np.zeros_like(x)
    bands = np.geomspace(f0, f1, 6)
    for i in range(5):
        c = (i + 0.5) / 5
        w = np.exp(-((u - c) / 0.22) ** 2)
        out += bp(x, bands[i], bands[i + 1]) * w
    env = (u ** 1.6) * (1 - u) ** 0.4 if rise else ((1 - u) ** 1.6) * u ** 0.3
    return out * env * 3.0


def v_creak(dur, f0=95, f1=120, wob=6.0, gain_env=None):
    t = tt(dur)
    f = f0 + (f1 - f0) * (t / dur) + 4 * np.sin(2 * np.pi * wob * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(ph * k) / k for k in range(1, 9))        # sawtooth-ish
    x *= 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * (wob * 2.3) * t))   # stick-slip grit
    e = env_adsr(dur, 0.04, 0.1, 0.8, 0.12) if gain_env is None else gain_env
    return lp(x * e, 1800)


def v_squeak(dur=0.1, f0=1900, f1=1350):
    return (sweep(f0, f1, dur) + 0.4 * sweep(f0 * 2, f1 * 2, dur)) * env_adsr(dur, 0.01, 0.03, 0.7, 0.04)


def v_ding(dur=0.6):
    t = tt(dur)
    return (np.sin(2 * np.pi * 1318.5 * t) * np.exp(-t / 0.18) + 0.7 * np.sin(2 * np.pi * 1760 * t) * np.exp(-t / 0.14)
            + 0.3 * np.sin(2 * np.pi * 2637 * t) * np.exp(-t / 0.08)) * 0.5


def v_glass_note(dur, f=523.25, att=0.6):
    t = tt(dur)
    x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.26 * t + 0.3) + 0.25 * np.sin(2 * np.pi * f * 2.0 * t)
    x *= 1 + 0.08 * np.sin(2 * np.pi * 5.2 * t)
    return x * env_adsr(dur, att, 0.2, 0.75, 0.5) * 0.3


def v_bell(dur=0.9):
    t = tt(dur)
    return (np.sin(2 * np.pi * 1318 * t) * np.exp(-t / 0.16) + 0.6 * np.sin(2 * np.pi * 1975 * t) * np.exp(-t / 0.11)
            + 0.35 * np.sin(2 * np.pi * 3290 * t) * np.exp(-t / 0.05)) * 0.5


def v_power_down(dur=0.15):
    t = tt(dur)
    return sweep(420, 60, dur, 1.4) * np.exp(-t / 0.06) * (1 + 0.3 * np.sin(2 * np.pi * 40 * t))


def v_breath(dur=0.4):
    return bp(noise(dur), 300, 1400) * env_adsr(dur, 0.15, 0.1, 0.8, 0.12)


def v_footstep(dur=0.11):
    t = tt(dur)
    return lp(noise(dur), 900) * np.exp(-t / 0.03) + 0.7 * np.sin(2 * np.pi * 85 * t) * np.exp(-t / 0.04)


def v_boing(dur=1.1, f=330):
    t = tt(dur)
    fm = f * (1 + 0.06 * np.sin(2 * np.pi * 6.5 * t) * np.exp(-t / 0.5))
    ph = 2 * np.pi * np.cumsum(fm) / SR
    return (np.sin(ph) + 0.4 * np.sin(2 * ph)) * np.exp(-t / 0.35) * 0.5


def v_heartbeat(dur, rate0=1.3, rate1=1.9, f=46):
    x = np.zeros(int(dur * SR))
    t = 0.0
    while t < dur - 0.3:
        u = t / dur
        rate = lerp(rate0, rate1, u)
        for off, g in ((0.0, 1.0), (0.17, 0.6)):
            i0 = int((t + off) * SR)
            d = 0.16
            s = np.sin(2 * np.pi * (f + 18 * np.exp(-tt(d) / 0.02)) * tt(d)) * np.exp(-tt(d) / 0.05) * g
            x[i0:i0 + len(s)] += s[:len(x) - i0]
        t += 1.0 / rate
    return x


def v_drone(dur):
    t = tt(dur)
    x = bp(noise(dur), 70, 420) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.31 * t)) * 1.6
    x += 0.5 * np.sin(2 * np.pi * 58 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.21 * t + 1))
    return x


def v_flutter(dur, rate=8.0):
    t = tt(dur)
    am = 0.55 + 0.45 * np.sin(2 * np.pi * (rate + 1.5 * np.sin(2 * np.pi * 0.4 * t)) * t)
    return lp(noise(dur), 1400) * am


# ── speed envelopes from the picture ─────────────────────────────────────────
def v_plip(f0=2300, f1=1500, dur=0.035):
    """A tiny wet 'plip' (a drop leaving skin): short descending sine with a soft click."""
    return fade(sweep(f0, f1, dur) * env_exp(dur, 0.012) + hp(noise(dur), 4000) * env_exp(dur, 0.003) * 0.3, 0.001, 0.006)


def v_sizzle(dur=0.07):
    """A drop hits the hot screen: 'tss' — band-limited noise with a fast decay and a faint rising hiss tail."""
    return fade(bp(noise(dur), 3500, 11000) * env_exp(dur, 0.018) + bp(noise(dur), 6000, 12000) * env_adsr(dur, 0.01, 0.02, 0.4, 0.03) * 0.3, 0.001, 0.01)


def v_sparkle(f=5200, dur=0.05):
    """A glass grain of the field's light — a 50 ms sine ping with a 2nd partial."""
    return fade((sine(f, dur) + 0.4 * sine(f * 2.01, dur)) * env_exp(dur, 0.012), 0.001, 0.01)


def v_ink_tick(dur=0.012, f=3200):
    """A letter lands: a dry little ink tick (band-passed click)."""
    return fade(bp(noise(dur), f * 0.7, f * 1.6) * env_exp(dur, 0.003), 0.0005, 0.004)


def v_roll_whoosh(dur=0.30):
    """The whole room rolls past the lens: wide noise sweep up-and-down with a Doppler dip."""
    t_ = tt(dur)
    u = t_ / dur
    fc = 250 * (14 ** (1 - np.abs(u - 0.45) / 0.55))
    x = np.zeros_like(t_)
    nz = noise(dur)
    # crude sweep: blockwise band-pass
    blk = 480
    for i in range(0, len(t_), blk):
        f = float(fc[min(len(fc) - 1, i)])
        x[i:i + blk] = bp(nz[i:i + blk] if i + blk <= len(nz) else np.pad(nz[i:], (0, i + blk - len(nz))), f * 0.6, f * 1.7)[:len(x[i:i + blk])]
    return fade(x * np.exp(-((u - 0.45) / 0.3) ** 2), 0.005, 0.01)


def prop_speed_env(name, t0, t1, step=0.01):
    ts = np.arange(t0, t1, step)
    sp = np.array([math.hypot(*S.prop_vel(name, t)) for t in ts]) * S.FPS   # px / s
    return ts, sp


# ── the cue sheet ────────────────────────────────────────────────────────────
MUSIC_GAIN = 0.85


def build(vo_path=None, vo_moral_path=None):
    M = Mix()

    # HOOK (defined at loop time tau, placed twice: tau and tau+20)
    for k in range(4):
        tau = TL["buzz_start"] + 0.6 * k
        if tau < TL["flip_up"]:
            M.add(v_buzz_burst(0.38), tau, 0.34, pan=0.05, name="buzz_am", loop=True)
    # pencil roll ticks: one per facet (7 px) — accelerating like the picture
    last = None
    for tau in np.arange(TL["pencil_start"], TL["pencil_end"], 0.004):
        x = S.pencil_x(tau)
        f = int(x // 7)
        if last is not None and f != last:
            spd = (S.pencil_x(tau) - S.pencil_x(tau - 0.004)) / 0.004
            M.add(v_click(1.0, 0.014, 900, 3200), tau, 0.05 + 0.0012 * spd, pan=-0.25, name="pencil_roll_tick", loop=True)
        last = f
    M.add(v_wood_knock(0.14, 520), TL["pencil_end"], 0.22, pan=-0.1, name="pencil_tak", loop=True)
    # the phone flips itself: click, lift, land flat + glow swell
    M.add(v_click(1.0, 0.02, 600, 2500), TL["flip_up"], 0.35, name="flip_clack")
    M.add(v_whoosh(TL["flip_dur"], 400, 1800, rise=True) * 0.6, TL["flip_up"], 0.22, name="flip_lift_whoosh")
    M.add(v_wood_knock(0.18, 240), TL["flip_up"] + TL["flip_dur"], 0.5, name="flip_land")
    M.add(v_glass_note(TL["glow_off"] - TL["glow_on"] + 0.3, 220, 0.5) * 0.35, TL["glow_on"], 0.16, name="glow_swell")
    M.add(v_thud(0.3, 52), TL["cut_s2"], 0.35, name="cut_thump")
    # S2 walk-in
    for ts in (2.08, 2.56, 3.03, 3.50):
        M.add(v_footstep(), ts, 0.42, pan=-0.3 + 0.2 * (ts - 2), name="footstep_paper")
    # the wall clock ticks from loop-time -1.8 s (S6) through the hook until it rips off the wall
    for i in range(40):
        ts = -1.8 + 0.5 * i
        if ts < PROPS["clock"]["t0"]:
            M.add(v_click(1.0, 0.009, 2500 if i % 2 else 1800, 6500), ts, 0.07, pan=-0.35, name="clock_tick", loop=(ts < 0))
    M.add(v_creak(0.5, 140, 110, 9), TL["pend_lean"], 0.08, pan=-0.35, name="pendulum_lean_creak")
    M.add(v_page_flutter(0.35, 3), TL["page_lift"], 0.18, pan=0.25, name="page_lift_flutter")
    M.add(v_breath(0.45), 4.0, 0.14, name="hero_breath")
    # ---- silence hole 4.5–4.9 is enforced by the mute mask below ----
    # FIELD ONSET
    M.add(v_whoosh(0.8, 150, 2600, rise=True), TL["field_on"] - 0.05, 0.45, name="pull_riser")
    M.add(v_thud(0.6, 44), TL["field_on"], 0.5, name="sub_drop")
    M.add(v_ding(0.9) * 0.6 + padto(sweep(880, 1320, 0.25), int(0.9 * SR)) * np.exp(-tt(0.9) / 0.12) * 0.4,
          TL["field_on"], 0.4, name="onset_ping")
    M.add(v_heartbeat(TL["glow_off"] - TL["field_on"], S.BPM / 120.0, S.BPM / 120.0), TL["field_on"], 0.5, name="sub_pulse_rise")
    dr = v_drone(TL["glow_off"] - TL["field_full"]) * env_adsr(TL["glow_off"] - TL["field_full"], 1.2, 0.5, 1.0, 0.03)
    # dropout under the look-at-lens
    t_ = np.arange(len(dr)) / SR + TL["field_full"]
    duck = np.where((t_ >= TL["look_lens"]) & (t_ < TL["look_end"]), 0.18, 1.0)
    duck = lp(duck, 12, 2)
    M.add(dr * duck, TL["field_full"], 0.16, name="pull_drone")
    for d in (TL["ding1"], TL["ding2"], TL["ding3"]):
        M.add(v_ding(), d, 0.42, pan=0.3, name="notification_ding")
    # per-prop scrapes / whooshes / impacts, driven by measured sprite speed
    MAT = dict(cup=("ceramic", 1500, 4200), chair=("wood", 250, 1300), fbook0=("paper", 900, 4000), fbook1=("paper", 900, 4000),
               fbook2=("paper", 900, 4000), plant=("pot", 700, 2600))
    for name in ("cup", "chair", "fbook0", "fbook1", "fbook2", "plant"):
        P = PROPS[name]
        ts, sp = prop_speed_env(name, P["t0"], P["t0"] + P["dur"] + 0.05)
        env = np.clip(sp / 600.0, 0, 1.2)
        mat, lo, hi = MAT[name]
        M.add(v_scrape(ts[-1] - ts[0], lo, hi, env), ts[0], {"ceramic": 0.22, "wood": 0.4, "paper": 0.16, "pot": 0.28}[mat],
              pan=(P["home"][0] - 540) / 900, name=f"slide_scrape_{mat}")
        tl = P["t0"] + P["dur"]
        imp = dict(ceramic=v_ceramic, wood=lambda: v_wood_knock(0.2, 160), paper=v_book_slap, pot=v_pot_clack)[mat]()
        M.add(imp, tl, {"ceramic": 0.35, "wood": 0.6, "paper": 0.35, "pot": 0.45}[mat], pan=(P["pile"][0] - 540) / 900,
              name=f"arrive_{mat}")
    for name in ("page0", "page1", "page2"):
        P = PROPS[name]
        M.add(v_page_flutter(P["dur"] + 0.1, 7), P["t0"], 0.3, pan=0.25, name="page_flutter")
    for name in ("sbook0", "sbook1", "sbook2", "hbook"):
        P = PROPS[name]
        M.add(v_whoosh(P["dur"], 250, 1800), P["t0"], 0.5, pan=0.1, name="book_whoosh")
        M.add(v_book_slap(), P["t0"] + P["dur"], 0.5, pan=0.2, name="book_slap")
    M.add(v_creak(0.9, 110, 82, 5.5), 5.1, 0.16, pan=0.2, name="lamp_metal_groan")
    M.add(v_metal_ring(0.5) * 0.5, 5.9, 0.2, pan=0.2, name="lamp_metal_ring")
    # clock rips off the wall and lands on the desk leg
    P = PROPS["clock"]
    M.add(v_click(1.0, 0.03, 400, 1800) * 1.5 + padto(v_wood_knock(0.1, 900), int(0.03 * SR)), P["t0"], 0.5, pan=-0.3, name="nail_pop")
    M.add(v_whoosh(P["dur"], 200, 1500), P["t0"], 0.45, pan=-0.1, name="clock_whoosh")
    M.add(v_metal_ring(1.0) + padto(v_wood_knock(0.2, 170), int(1.0 * SR)), P["t0"] + P["dur"], 0.55, pan=0.1, name="clock_clang")
    # rug drag
    ts = np.arange(5.4, 6.45, 0.01)
    env = np.array([ease_in(seg(t, 5.4, 6.4), 1.8) * (1 - seg(t, 6.3, 6.45)) for t in ts])
    M.add(v_scrape(ts[-1] - ts[0], 120, 900, env), ts[0], 0.25, pan=-0.1, name="rug_drag")
    # HERO: brace slide, lunge, grab, flag
    ts = np.arange(TL["field_on"], TL["brace_end"], 0.01)
    env = np.array([ease_in(seg(t, TL["field_on"], TL["brace_end"]), 2.0) for t in ts])
    M.add(v_scrape(ts[-1] - ts[0], 500, 3000, env), ts[0], 0.22, pan=-0.3, name="shoe_slide_squeal")
    M.add(v_squeak(0.14, 1500, 1900), 5.32, 0.09, pan=-0.3, name="slip_squeak")
    M.add(v_breath(0.3) * 2, TL["lunge"], 0.2, pan=-0.3, name="lunge_breath")
    M.add(v_whoosh(0.4, 200, 1200), TL["lunge"], 0.3, pan=-0.4, name="lunge_whoosh")
    M.add(v_book_slap(0.12) * 0.8 + padto(v_wood_knock(0.12, 300), int(0.12 * SR)), TL["grab"], 0.45, pan=-0.5, name="hands_grab")
    M.add(v_creak(TL["flag_full"] - TL["grab"] + 0.3, 80, 118, 5.0), TL["grab"], 0.3, pan=-0.5, name="wood_creak_frame")
    for tc, g in ((8.0, 0.16), (8.65, 0.13), (10.5, 0.18), (10.85, 0.22)):
        M.add(v_creak(0.45, 100, 92, 7.0), tc, g, pan=-0.5, name="wood_creak_strain")
    fl = v_flutter(TL["letgo"] - 6.6, 8.0)
    t_ = np.arange(len(fl)) / SR + 6.6
    fl *= np.array([smooth(seg(t, 6.6, 7.6)) for t in t_]) * np.where((t_ >= TL["look_lens"]) & (t_ < TL["look_end"]), 0.25, 1.0)
    M.add(fl, 6.6, 0.14, pan=-0.2, name="cloth_flag_flutter")
    # v3 — sweat: each strain drop leaves his head with a 'plip' and hits the hot screen with a 'tss' 0.5 s later
    for t0, j in S.sweat_drops(TL["letgo"]):
        h = S.hash01(j, 61)
        M.add(v_plip(2100 + 600 * h, 1300 + 300 * h), t0, 0.11 + 0.05 * h, pan=-0.45, name="sweat_plip")
        M.add(v_sizzle(0.06 + 0.03 * h), t0 + 0.5, 0.10 + 0.05 * h, pan=0.3, name="sweat_sizzle")
    # v3 — the field's light grains: sparse glass pings while the flow streams to the phone (never on the grid)
    ts_ = TL["field_full"]
    jj = 0
    while ts_ < TL["letgo"]:
        h = S.hash01(jj, 62)
        if not (TL["look_lens"] <= ts_ < TL["look_end"]):
            M.add(v_sparkle(4200 + 2600 * h, 0.04 + 0.03 * h), ts_, 0.035 + 0.025 * h, pan=-0.6 + 1.2 * S.hash01(jj, 63), name="field_sparkle")
        ts_ += 0.21 + 0.27 * h
        jj += 1
    for ts_ in (TL["slip1"], TL["slip2"]):
        M.add(v_squeak(0.1), ts_, 0.16, pan=-0.5, name="hand_slip_squeak")
        M.add(v_click(1.0, 0.02, 300, 1500), ts_ + 0.07, 0.3, pan=-0.5, name="hand_slip_regrip")
    M.add(v_ding(0.5) * 0.3 + padto(v_glass_note(0.5, 1046, 0.02), int(0.5 * SR)) * 0.6, TL["look_lens"], 0.16, name="look_at_lens_sparkle")
    # LET GO → flight → landing on the desk → the slap → flip face-down
    M.add(v_whoosh(TL["land"] - TL["letgo"] + 0.05, 250, 3000, rise=True), TL["letgo"], 0.75, pan=0.1, name="letgo_whoosh")
    M.add(v_click(1.0, 0.025, 300, 1600) * 1.4, TL["letgo"], 0.5, pan=-0.5, name="release_snap")
    M.add(v_thud(0.5, 62) * 1.3 + padto(v_wood_knock(0.2, 150), int(0.5 * SR)), TL["land"], 0.55, pan=0.3, name="desk_slam")
    for i in range(7):   # the pile rattles
        M.add(v_click(1.0, 0.01, 800 + 300 * i, 4000 + 400 * i), TL["land"] + 0.02 + 0.025 * i + 0.01 * rng.random(), 0.12, pan=0.3,
              name="pile_rattle")
    M.add(v_ceramic(0.2) * 0.5, TL["land"] + 0.05, 0.25, pan=0.5, name="cup_rattle")
    M.add(bp(noise(0.03), 300, 3000) * env_exp(0.03, 0.008) * 2 + padto(v_thud(0.12, 200), int(0.03 * SR)) * 0.5,
          TL["slap"], 0.6, pan=0.3, name="hand_slap_phone")
    M.add(v_click(1.0, 0.02, 600, 2500), TL["flip_down"], 0.35, pan=0.3, name="flip_clack")
    M.add(v_wood_knock(0.18, 240) * 1.1, TL["flip_down"] + TL["flip_dur"], 0.6, pan=0.3, name="flip_land_facedown")
    M.add(v_power_down(0.15), TL["glow_off"], 0.5, name="power_down_sweep")
    # ---- silence 12.0–12.3 enforced by the mute mask ----
    # THE DROP: every prop lands with its own material, staggered exactly like the picture
    land = dict(chair=("wood", 0.6), clock=("metal", 0.5), plant=("pot", 0.45), fbook0=("paper", 0.4), fbook1=("paper", 0.4),
                fbook2=("paper", 0.5), page0=("paper", 0.25), page1=("paper", 0.25), page2=("paper", 0.25), cup=("ceramic", 0.35),
                sbook0=("paper", 0.3), sbook1=("paper", 0.35), sbook2=("paper", 0.35), hbook=("paper", 0.3))
    for name, (mat, g) in land.items():
        P = PROPS[name]
        tl = TL["drop"] + 0.02 * (P["z"] % 4) + P["fall"]
        imp = dict(wood=lambda: v_wood_knock(0.22, 150) + padto(v_thud(0.2, 70), int(0.22 * SR)),
                   metal=lambda: v_metal_ring(1.1) + padto(v_wood_knock(0.18, 170), int(1.1 * SR)),
                   pot=lambda: v_pot_clack(0.25) + padto(lp(noise(0.3), 1200) * env_exp(0.3, 0.08), int(0.25 * SR)) * 0.5,
                   paper=v_book_slap, ceramic=v_ceramic)[mat]()
        M.add(imp, tl, g, pan=(P["down"][0] - 540) / 900, name=f"drop_{mat}")
        if P["bounce"] >= 6:
            M.add(imp * 0.4, tl + P["fall"] * 0.5 * 0.9, g * 0.5, pan=(P["down"][0] - 540) / 900, name=f"drop_bounce_{mat}")
    M.add(v_thud(0.6, 48) * 1.2, TL["drop"] + 0.28, 0.5, name="drop_sub_thud")
    M.add(lp(noise(0.9), 500) * env_adsr(0.9, 0.05, 0.3, 0.5, 0.4), TL["drop"] + 0.3, 0.09, name="dust_hiss")
    M.add(v_boing(1.2, 300), TL["drop"], 0.14, pan=0.1, name="lamp_boing")
    M.add(v_page_flutter(0.8, 10), TL["drop"] + 0.05, 0.22, pan=0.2, name="pages_settle")
    M.add(v_creak(0.4, 90, 80, 6) * 0.5, TL["stand"], 0.08, pan=0.3, name="hero_stand_rustle")
    # after-shock: the room settles (sub rumble tail + debris ticks)
    M.add(np.sin(2 * np.pi * 44 * tt(1.6)) * env_adsr(1.6, 0.1, 0.3, 0.5, 1.0), TL["drop"] + 0.4, 0.12, name="settle_rumble")
    for ts_, g in ((12.92, 0.12), (13.28, 0.09), (13.71, 0.07), (14.05, 0.05)):
        M.add(v_click(1.0, 0.012, 900, 3500), ts_, g, pan=-0.2 + 0.4 * rng.random(), name="debris_tick")
    for ts_ in (13.62, 14.22):
        M.add(lp(v_click(1.0, 0.012, 1200, 4000), 2500), ts_, 0.07, pan=-0.1, name="clock_tick_fallen")
    # MEANING
    M.add(lp(noise(0.5), 800) * env_adsr(0.5, 0.2, 0.1, 0.6, 0.2), TL["cut_s5"], 0.05, name="cut_air")
    M.add(v_glass_note(TL["cut_s6"] - 14.8 - 0.2, 523.25, 0.9), 14.8, 0.15, name="glass_note_held")
    M.add(v_thud(0.3, 70), TL["line1"], 0.35, name="word_slam")
    M.add(v_thud(0.3, 70), TL["line2"], 0.3, name="word_slam")
    M.add(v_thud(0.4, 60) * 1.3 + padto(v_ding(0.4) * 0.8, int(0.4 * SR)), TL["hot"], 0.4, name="hot_word_slam")
    M.add(v_thud(0.3, 50), TL["cut_s6"], 0.3, name="cut_thump")
    M.add(v_click(1.0, 0.03, 500, 2600), TL["moral_out"], 0.22, name="text_snap_out")
    # v3 — kinetic type: one dry ink tick per letter on the cascade grid (render.LETTER_STAGGER)
    for t0, text, off in ((TL["line1"], "Phone ulta.", 0), (TL["line2"], "Zindagi", 0), (TL["line2"], "seedhi.", 8)):
        for i, ch in enumerate(text):
            if ch == " ":
                continue
            M.add(v_ink_tick(0.012, 2600 + 900 * S.hash01(i, 64, off)), t0 + (i + off) * 0.018, 0.05, pan=-0.3 + 0.6 * (i + off) / 16, name="type_ink_tick")
    # v3 — the world rolls on 'ulte.': whoosh + a low whomp; the buzz snaps it back with a dry click
    M.add(v_roll_whoosh(TL["roll_dur"] + 0.06), TL["roll_start"] - 0.02, 0.55, name="world_roll_whoosh")
    M.add(v_thud(0.4, 44) * 1.2, TL["roll_start"], 0.45, name="world_roll_whomp")
    M.add(v_click(1.0, 0.03, 400, 2200) * 1.3 + padto(v_thud(0.12, 90), int(0.03 * SR)) * 0.6, TL["moral_out"], 0.4, name="snap_back_click")
    # VO — speech begins exactly at line1 (the file has 0.48 s of leading silence)
    if vo_path and pathlib.Path(vo_path).exists():
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        p = subprocess.run([ff, "-v", "error", "-i", str(vo_path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True)
        vo = np.frombuffer(p.stdout, dtype=np.float32).astype(float)
        env = np.abs(vo)
        i_on = int(np.argmax(env > env.max() * 0.06))
        vo = hp(vo, 80)
        vo = vo / (np.abs(vo).max() + 1e-9)
        M.add(vo, TL["line1"] - i_on / SR, 1.0, name="vo_meaning_line")
        LEDGER.append(dict(t=TL["line1"], cue="vo_word_1_phone", gain=0.9, dur=0))
    # VO punchline — 'Warna' lands on moral1 (18.00); 'tum' ≈ 18.64; 'ulte' ≈ 18.98
    if vo_moral_path and pathlib.Path(vo_moral_path).exists():
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        p = subprocess.run([ff, "-v", "error", "-i", str(vo_moral_path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True)
        vm = np.frombuffer(p.stdout, dtype=np.float32).astype(float)
        env = np.abs(vm)
        i_on = int(np.argmax(env > env.max() * 0.06))
        vm = hp(vm, 80)
        vm = vm / (np.abs(vm).max() + 1e-9)
        M.add(vm, TL["moral1"] - i_on / SR, 1.0, name="vo_moral_line")
    # MUSIC — the procedural score (music.py), event-locked to the timeline
    M.sfx = (M.L.copy(), M.R.copy())          # sound-design stem (the noise-floor gate measures this)
    import music
    Lm, Rm = music.render()
    M.L += Lm * MUSIC_GAIN
    M.R += Rm * MUSIC_GAIN
    for t_, name_, g_ in music.EVENTS:
        LEDGER.append(dict(t=t_, cue=name_, gain=round(g_ * MUSIC_GAIN, 3), dur=0))
    # silence holes (the gate requires them; they also make the sub drop hit harder)
    mask = np.ones(N)
    for a, b in ((4.5, TL["field_on"] - 0.02), (TL["glow_off"] + 0.15, TL["drop"] - 0.02)):
        ia, ib = int(a * SR), int(b * SR)
        r = int(0.012 * SR)
        mask[ia:ib] = 0.0
        mask[ia - r:ia] = np.linspace(1, 0, r)
        mask[ib:ib + r] = np.linspace(0, 1, r)
    M.L *= mask; M.R *= mask
    if hasattr(M, "sfx"):
        M.sfx = (M.sfx[0] * mask, M.sfx[1] * mask)
    return M


def write_wav(path, L, R):
    import wave, struct
    x = np.stack([L, R], 1)
    peak = np.abs(x).max()
    if peak > 0.98:
        x = x / peak * 0.98
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return peak


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../audio/mix.wav")
    ap.add_argument("--vo", default="../audio/vo_meaning.mp3")
    ap.add_argument("--vo-moral", default="../audio/vo_moral_b.mp3")
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    M = build(a.vo, a.vo_moral)
    peak = write_wav(out, M.L, M.R)
    if hasattr(M, "sfx"):
        write_wav(out.parent / "mix_sfx.wav", M.sfx[0], M.sfx[1])
    led = sorted(LEDGER, key=lambda e: e["t"])
    (out.parent / "cue_ledger.json").write_text(json.dumps(led, indent=1))
    voices = sorted({e["cue"] for e in led})
    print(f"wrote {out} peak={peak:.3f} cues={len(led)} voices={len(voices)}")
    print(", ".join(voices))


if __name__ == "__main__":
    main()
