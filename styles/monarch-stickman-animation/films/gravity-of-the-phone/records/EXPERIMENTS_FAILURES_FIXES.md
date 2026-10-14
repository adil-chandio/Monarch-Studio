# THE GRAVITY OF THE PHONE — experiments, failures, fixes (post-mortem)

Task `EMS-20261014-002` · 2026-10-14 · first WTF-30 delivery. Everything below was measured, not guessed. Each lesson is phrased so the next build can apply it without re-discovering it.

## Rig and renderer

1. **`shade.head_only(..., ang=…)` takes RADIANS.** Passing degrees rotated the SHADE bust 90–170°. Use small values (≈ −0.06) for a head tilt.
2. **Toon arm convention:** `ar ≈ 150` points the arm UP; reaching DOWN to a desk needs `ar ≈ 0` plus lean and a deep squat; the hand cannot go lower than ≈ 52 px above the feet. Fix used: anchor the landing feet LEFT of the phone (`LAND_FEET_X = 806`) so the slap is reachable instead of faking it.
3. **Side-view pencil:** scrolling facet bands produced zig-zag aliasing; a slanted stick with static facet bands reads cleaner at 1080 px.
4. **PIL `ImageDraw` fills must be 4-tuples** when drawing on RGBA layers: `SOFT + (alpha,)`.
5. **Hot-word line centring:** drawing "Zindagi" alone, left-anchored in the slot reserved for "seedhi.", left the line off-centre for 0.5 s. Fix: drop the whole line in with the VO word and let the hot word change colour/scale on its own beat (`render.py`, meaning block). Re-rendered the second half only (pure-time renderer).
6. **Render economics:** 0.5–0.6 s per 1080×1920 frame; two halves in parallel ≈ 3 min per 300 frames. Always render halves to separate files and concat with `-c copy`; a late fix then costs one half, not the film.
7. **Pattern:** a 6×5 contact sheet from the *encoded master* (`select=not(mod(n,20))`) caught the text-centring issue that per-frame checks of the planned beats had missed. Always read the master, not only the frames you planned.

## Audio and mastering

8. **ffmpeg `loudnorm` with `linear=true` silently falls back to DYNAMIC mode** when the input crest factor (TP − I) exceeds the headroom the target allows (mix was 21.5 dB vs 13 dB). Result: LRA collapsed 10.2 → 5.4 and the integrated target was missed (−14.6). Dynamic loudnorm is now banned for this format.
   **Fix:** lower hot transients at source (slams 0.4–0.6, beds raised) and master with `build.master_linear()` — linear gain to −14 LUFS then a numpy look-ahead true-peak limiter (ceiling −1.3 dBTP, up to 5 passes), then AAC overshoot check. Measured −14.2 LUFS / TP −1.1 / LRA 7.4.
9. **`np.pad` with negative widths crashes**; when summing signals of different lengths always `padto(x, n)`.
10. **An inverted mute-mask range (start > end) silently does nothing.** The second silence hole was missing until the power-down cue was shortened to 0.15 s so the hole window became positive. Gate now asserts both holes.
11. **Clock-tick loops** and after-shock cues (small settles 0.3–0.8 s after the drop) made the restored room feel physical; the drop alone sounded like a cut.

## Gates

12. **4:5 safe-band "ink ratio" alone fails on desk shots** (legs/baseboard reach the frame bottom, ratio 0.78). The gate now checks *subject anchors* (phone, hero feet/head/pivot, text lines from `render.camera()` + `hero_screen_scale()`) are inside y 285–1635 on the key frames, plus ink share ≥ 0.72. Proof image: `artifacts/crop_4x5_proof.jpg`.
13. **Brain gate schema:** `concept.py gate` casts `shots`, `pattern_interrupts`, `wtf_moments` with `int()`. Keep the descriptive lists under `*_list` keys; the gate keys stay integers. Beat density is now a real list (`beats_list`, 38 beats, max gap 1.45 s), not a claimed number.
14. **Loop seam measured on the encoded master** (frame 599 vs frame 0 mean abs diff 3.1/255) — not on the renderer's output; AAC/x264 can move it.

## What to carry into the doctrine

- Crest-factor rule: if (TP − I) of the mix > 13 dB, loudnorm will go dynamic; fix the mix, then master linear + limiter.
- Subject-anchor crop proof instead of ink-ratio.
- Contact sheet from the master as a mandatory review step before gates.
- Pure-time scene solver + parallel halves + half re-render is the fastest honest iteration loop for 20–30 s films.
