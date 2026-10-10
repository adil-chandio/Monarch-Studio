# stickman_money_37s_v4.mp4 — what changed

**37.00 s · 1080x1920 · 30 fps · 13.39 MB · sha256[:16] `08358ed55094118d`**
Built by `src/stick3.py` + `src/fx.py` + `src/character.py`.
Audio stream copied bit-for-bit from v2 (same timeline, so sync is unchanged, −11.2 LUFS).

## 1. One character, not seven
v2 called `stick()` with a different seed in every scene — 31, 33, 37, 39, 43, 47, 53.
Different hand-wobble each time, so it was literally **a different person per scene**.
v4 runs one `hero()` on `HERO_SEED=101` in all six scenes: same cap, same hoodie,
same face rig, 10 expressions, deterministic blink, motion ghosts.
Side cast is deliberately subordinate — the client is `s=338` and 25 % dimmer, never
gets a marker, never outsizes the hero.

## 2. Theme colouring — the film is now a colour journey
Each scene owns a colour chapter, and the **background wash, particles, HUD,
progress rail, bloom halation and the grade's shadow/highlight split-tone all
follow it**. The themes cross-fade through the cut, so the colour changes *with*
the wipe rather than snapping.

| Scene | Chapter | Key | Feel |
|---|---|---|---|
| 1 | PROBLEM | RED | cold, airless |
| 2 | SKILL | CYAN | electric, clean |
| 3 | GRIND | VIOLET | deep, nocturnal |
| 4 | CREATE | PINK | hot, playful |
| 5 | SELL | MINT | fresh, money-green |
| 6 | PAYOFF | GOLD | warm, maximal |

## 3. New motion graphics
- **Kinetic captions** — 17 Roman-Urdu lines, word-by-word pop on a dark pill,
  one word per line burned in the theme colour. Replaces v2's static bottom text.
- **Progress rail** — six chapter segments, each in its own theme colour, with a
  glowing travelling head. The viewer can see how much is left (retention device).
- **Step chips** — ringed `1/4 … 4/4` counter, top right, with a sweeping arc fill.
- **Corner HUD brackets** — animated, theme-coloured.
- **Ambient particle field** — 54 bokeh/dust elements, beat-reactive.
- **Counters and progress rings** — brain `0-100 %`, calendar `0-60 HOURS`, `3/3` samples.
- **Confetti, radial bursts, triple shock-rings, light sweeps.**

## 4. Transitions: 5 -> 9
v4 ships **zoom-punch · glitch-slice · paint-strokes · radial clock wipe · ink-iris**
(the library also has eraser, zip, whip, barn-doors). Every wipe now draws a bright
leading edge in the *incoming* scene's theme colour.

## 5. Camera and grade
- Per-scene camera intent instead of one global push — scenes alternate
  push-in / pull-out with a lateral drift, eased with smoothstep.
- **Cut window bug fixed.** v2 gated the cut effects on `−0.20 ≤ dd ≤ 0.34` while
  the falloff `1−|dd|/0.26` is already zero past `0.26` — about 12 frames of the
  film ran dead code. v4 gates on `−0.24 ≤ dd ≤ 0.26`, matching the falloff.
- Constant subtle chromatic aberration plus a beat-locked extra push.
- New grade: theme shadow/highlight split-tone, coloured edge glow, filmic
  S-curve roll-off, **halation** (warm bleed around the brightest marks).

## 6. Frame-0 defect fixed
v2's first frame measured `mean 31.61, max 156, zero pixels > 200` — at `lt=0`
scene 1 drew nothing. It is the feed thumbnail.
v4 frame 0: **`mean 56.2, max 251, 57,523 pixels > 200`** — title at 48 % entry
scale, ground line live, hero already on stage.

## 7. Build integrity
- `render(i)` is a pure function of `i`; proven by rendering frame 300 twice to
  the same sha256. The film was rendered as **two parallel shards** (0-555,
  555-1110) and concatenated; the boundary delta (3.05) sits inside the normal
  neighbour range (2.98-4.58), i.e. no seam.
- `stick2.py` / `stickbase.py` / `timeline.py` / `make_audio4.py` are **byte-identical**
  to the manifest. v4 is additive. The 46-check harness for the v2 build still passes.

## 8. Still a placeholder
`@YOURHANDLE` in the bottom bar — give me your real handle and I will re-render
(only the HUD changes, ~6 min).
