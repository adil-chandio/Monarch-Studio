# Experiments, failures and fixes

## 2026-10-11 · First full picture render

- **Failure:** deterministic render stopped at frame 121 during transition branch 3 with Pillow `ValueError: x1 must be greater than or equal to x0`.
- **Cause:** the alternating-strip transition deliberately staggered odd strips by 120 px; at the first transition frame this put the strip's left edge beyond the 1920 px right edge.
- **Fix:** clamp the strip edge with `min(W, …)` before drawing. The same boundary condition was proactively corrected in WF-03's related rail-strip transition before its first full render.
- **Data safety:** the incomplete file lived only in ignored `build/`; source, voice, timeline and checkpoint remained intact. Deterministic rendering restarts cleanly from frame zero.

## 2026-10-11 · First final mux gate

- **Result:** 20/21 gates passed. The single failure was audio sample rate: decoded AAC was 96 kHz instead of the required 48 kHz.
- **Cause:** FFmpeg `loudnorm` internally oversampled for true-peak measurement and the mux command did not explicitly resample its output.
- **Fix:** append `aresample=48000` to the mastering filter and force AAC `-ar 48000`; apply the correction to both style packages before WF-03 muxing.
- **Unchanged evidence:** 1920×1080, 30 fps, 74.00 s, −13.6 LUFS, −1.5 dBFS decoded peak, all picture/cadence/novelty gates passed.
