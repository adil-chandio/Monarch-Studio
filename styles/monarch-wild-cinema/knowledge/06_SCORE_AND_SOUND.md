# 06 · Score and sound

## The score is synthesised, and that is a feature

`score.py` builds the entire soundtrack from oscillators, filters and
envelopes: a stereo drone, an air floor, a tension dyad, and **12 cue voices**
(`impact`, `impact_soft`, `sub_drop`, `riser`, `riser_short`, `whoosh`,
`doppler_whip`, `whoosh_edge`, `hard_hit`, `pad_swell`, `bell`, `tick`).

Consequences, all of them good:

- **No licensing exposure.** No music library, no claim risk, no Content ID.
- **Cues are addressable.** The transition table names a cue per transition
  kind, and `run_film.py` reads the *same table* the picture uses, so a cue can
  never drift away from its cut.
- **The episode is reproducible from text.** The score is a function of the
  plan, not a file someone must find.

## Four laws, each learned the hard way

### 1 · Width is created at the source

A widener multiplying a mono signal gives exactly zero. In the noir project the
bed's energy sat in a drone panned to centre, so the side channel was
*identically zero* and `side × 3.10` was still zero — measured **L/R
correlation 0.9817**, a mono file with a stereo processing chain bolted to it.

Every bed here is therefore generated as a **true stereo pair**: independent
detune and independent random phase per channel
(`bed_drone(n, width=1.0)`), and cues that need width get an explicit
inter-channel delay (`_stereo(x, spread=…)`).

### 2 · Budget the spectrum before the loudness

Three stacked bass instruments do not sound cinematic, they sound like a
rumble. The noir v1 measured **34 % of all energy below 120 Hz** and only
**7.9 % in 4–8 kHz**. Each stem here owns a band: the drone lives at 40–130 Hz,
air at 200 Hz–8 kHz, tension at 1.1–1.8 kHz, cues declare their own range.

Gate G13 measures the 4–8 kHz share **with the voice removed** — because once
narration covers most of the runtime, a whole-file spectral target is measuring
the narrator's sibilance, not the bed (stickman ledger #35).

### 3 · The limiter protects the PCM, not the codec

A pre-encode peak of −1.52 dBFS decoded from AAC at **+0.85 dBFS** — a 2.4 dB
overshoot. The mix chain therefore sets `alimiter=limit=0.63:level=disabled`
(≈ −4 dBFS) and lets the codec overshoot into the headroom. `score.measure()`
reports the peak **after decoding the delivered file** (`max_volume` on the
decoded stream), never before encoding it.

### 4 · An unbounded `apad` will pad forever

`loudnorm` + `alimiter` latency made an output ~0.37 s short. A bare `apad`
padded infinitely and thrashed the box until `kswapd` took over. Any padding
uses `apad=whole_dur=…,atrim=…`. This engine does not use `apad` at all — the
voice track is built by concatenation, which is exact.

## The two-pass mix

A single ffmpeg graph combining `sidechaincompress` + `amix` + `loudnorm`
fails: the filter graph cannot carry it, and renaming labels does not help.
The working structure is two passes:

```
pass 1:  bed → volume → sidechaincompress(by voice) → amix → alimiter(-4 dBFS)
pass 2:  loudnorm I=-16 TP=-1.5 LRA=9
```

Duck ratio is **5:1**, not 18:1. The stickman mix used 18:1 and produced 12
holes more than 9 LU below the mean, one of them inside the call to action.
A duck that breathes out between sentences leaves an audible hole; 5:1 with the
bed level raised keeps the floor continuous.

## Measurement scope, stated honestly

`score.measure()` reports integrated LUFS, LRA, true peak, decoded peak and mean
volume. `score.stereo_report()` reports L/R correlation and side/mid ratio.
`score.band_energy()` reports per-band shares, split by voice presence when the
voice spans are known.

**What is not claimed:** no independent human listening pass. Every delivery
state records exactly what was measured and nothing more. An approval field
filled from intention is worse than an empty one.

## Targets

| metric | target | gate |
|---|---|---|
| integrated loudness | −16.5 ± 1.0 LUFS | G08 |
| true peak | ≤ −1.0 dBTP | G09 |
| decoded sample peak | ≤ −1.0 dBFS | G07 |
| L/R correlation | 0.55 – 0.85 | G10 |
| side/mid energy | > 0.25 | G11 |
| 4–8 kHz, voice absent | > 10 % | G13 |
| 120–500 Hz, whole file | < 58 % | G14 |

---

## 6.x · The mix bus, in order (rebuilt 2026-10-16 after five measured failures)

```
beds ─► cues ─► shape_spectrum ─► soft_clip ─► pre-master peak        (run_film.build_score)
                                       │
                                       ▼
                gain ─► linked limiter (safety only) ─► BALANCER ─► common-gain guard
                                       (score.solve_mix, iterated against measurements)
```

Five laws, each from a failure that reached a master:

1. **No ffmpeg loudness stage on the bus.** `alimiter` and `loudnorm` reduce gain **per channel**;
   a mix balanced to +0.580 arrived at the master at +0.320 (and at +0.055 once `alimiter` was in
   the chain). Gain is solved in numpy, so the image that goes in is the image that comes out.
2. **The balancer is the last stereo operation.** The correlation sum is gain-weighted, so any
   level change after it moves the correlation.
3. **The peak guard is a COMMON gain, not a limiter.** Both channels scale together, so trimming
   for G07/G09 cannot disturb G10/G11.
4. **Crest factor is content, not mastering.** A 24.5 dB crest cannot reach −16 LUFS under a
   −1 dBFS ceiling; over-driving a peak limiter made a dense mix *quieter* (−23.6 LUFS in,
   −27.5 out). Fixed at the source: cue balance, `soft_clip`, and sustained mid energy.
5. **Never let the 16-bit write decide loudness.** Solve on float; the first "successful" mix
   measured −16.06 LUFS **because it clipped**.

**Where energy actually has to live** (measured on the shipped 31 s bed): 20–120 Hz 10.3 % ·
120–500 Hz 25.5 % · 500–2 kHz 25.9 % · 2–4 kHz 3.6 % · **4–8 kHz 25.2 %** · 8–16 kHz 9.0 %.
A hit-and-drone score lands nowhere near that — the 4–8 kHz share came from a band-limited
shimmer (exact FFT mask 4.4–7.2 kHz) and the sustained mid energy from a 440 Hz pad.

**Band-limiting:** a 2-pole filter leaks enough above its corner to put **34.2 %** of the mix in
8–16 kHz while the target band measured 17.8 %. Use `fft_band` (raised-cosine mask) whenever a
band *share* is gated.
