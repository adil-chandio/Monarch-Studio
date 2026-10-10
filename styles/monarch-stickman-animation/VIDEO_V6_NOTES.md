# v6 — REAL CHARACTER PASS

`stickman_money_37s_v6.mp4` · 1080×1920 · 30 fps · **37.00 s** · 10.79 MB
sha256[:16] `85bdb4d35358dbed` · −12.1 LUFS · true peak −0.54 dBFS · stereo 48 kHz · decode-clean

Everything v5 got right is untouched: the clean layout grid, the chapter accents,
the one-swipe transition, 37.00 s exact, the same Urdu VO timing.
What changed is the **character** and the **mix**.

---

## 1. The character is now a shaded solid, not a flat fill

`toon()` renders the figure into its own tile, lights it as one body, then
composites. Four stacked cues, all masked by an **eroded** alpha so the crisp ink
contour is never touched — shading lives strictly *inside* the outline.

| cue | how | what it buys |
|---|---|---|
| **bevel** | alpha minus itself offset by `0.020·s`, blurred | lit edge upper-left, dark edge lower-right |
| **form** | broad diagonal ramp, 11.5 % | every limb gets a lit side and a shaded side |
| **AO** | soft pools at neck, armpits, hips, elbows, knees | limbs read as separate volumes, not a decal |
| **spec** | one soft highlight on the skull | the head becomes a ball |

The **face is drawn after shading**, so eyes and mouth stay pure crisp ink.

## 2. Real hands with fingers

The mitten is gone. The palm and four fingers are **one scalloped polygon**, so
the outline pass strokes the notches *between* the fingers. (Building each finger
as its own overlapping circle welds them shut — the grow pass is wider than the
gap.) The thumb is a second piece, because a thumb genuinely does separate.
Crease lines in `(96,90,84)` sit on top.

Four shapes, chosen per pose: `relax` · `point` (index extended) · `open`
(fingers splayed) · `fist`. Hands grew `0.033 → 0.040` of body height so the
articulation survives at 500 px figures.

## 3. Feet and legs

The shoe now **rolls about the ankle**, `roll = clamp(shin_angle · 0.62, ±26°)`.
Standing → flat. Walking → heel strike on the plant, toe off on the push.
The ground shadow is a blurred radial sprite that **shrinks and fades as the
figure leaves the floor**, so weight reads.

## 4. Motion physics — `phys()` in `clean.py`

A pure function of `t`, so sharding stays bit-identical.

* forearms and shins are read **70 ms in the past** → follow-through / drag
* the head blends now with 35 ms ago → lead-and-lag
* **hair inertia**: spike *tips* swing with the head's angular velocity, roots stay planted
* the torso **breathes** at ~0.33 Hz
* the walk has a real vertical bob (`_bob`), rising over the passing leg and
  dropping onto the plant

## 5. Audio — voice forward, SFX silkier

**Voiceover is now clearly in front: +10.0 dB over the bed before ducking**,
and the sidechain pulls the bed down a further ~6–9 dB while the voice is on.

| | v5 | v6 |
|---|---|---|
| VO chain | flat | HPF 85 · −2.2 dB @230 · **+3.2 dB @2.8 k** presence · 3.6:1 comp · ×2.15 |
| bed level | 0.52 | **0.40** |
| ducking | thr .035 / 7:1 | **thr .014 / 18:1 / rel 360** |

Smoothness work:
* every transient attack lengthened (`pop` 4→8 ms, `tap` 3→9 ms, `thud` 5→10 ms)
* bus lowpass pulled **9.2 k → 8.2 k**
* a **silk plate reverb** on the cue bus only (12 prime-spaced taps, 13–452 ms,
  band 220 Hz–5.2 kHz, 34 % wet, tails alternating L/R). Music bed stays dry so
  it never mushes. This is what turns correct SFX into ASMR — nothing stops dead.
* clicky cues pulled down (keys −3 dB, checks −3.4, taps −3), smooth cues pushed
  up (chimes +4 dB and longer tails)

248 events, ledger in `ASMR_EVENT_LEDGER.csv`.

## 6. Verified

| check | result |
|---|---|
| duration | 37.00 s exact (1110 frames @ 30) |
| frame size | 1080×1920, yuv420p, High@4.0 |
| decode | clean, zero errors |
| loudness | −12.1 LUFS, LRA 2.0 |
| true peak | −0.54 dBFS, clip-free |
| VO vs bed | +10.0 dB during speech, before ducking |
| frame 0 | mean 227, bright — no black thumbnail |
| render | 0.254 s/frame, 2 shards, bit-identical (`render(i)` is pure) |

## 7. Rebuild

```bash
python3 src/clean.py 0   555  build/c0.mp4
python3 src/clean.py 555 1110 build/c1.mp4
python3 src/make_asmr.py
# concat -c copy, then the mux chain above
```
Flat (pre-shading) renderer kept at `src/toon_flat_backup.py`.
