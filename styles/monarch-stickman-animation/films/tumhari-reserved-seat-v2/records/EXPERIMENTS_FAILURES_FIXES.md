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

---

# V2 MONARCH CINEMA TABAHI — EXPERIMENTS / FAILURES / FIXES

## Immutable-fork decision
- **Risk:** A direct enhancement pass could silently overwrite the accepted V1 package and destroy the comparison baseline.
- **Decision:** Copied V1 into the separate permanent `tumhari-reserved-seat-v2/` package, retained byte-identical timeline/voice, moved copied acceptance evidence under `records/parent-v1/`, and recorded a canonical V1 tree hash.
- **Result:** V1 remains independently reproducible and gate-verifiable; V2 has no authority to claim acceptance until its own receipt exists.

## Look-sheet CLI mismatch
- **Failure:** First V2 preview command used the guessed flag `--look-sheet`; renderer correctly rejected it because the inherited CLI uses `--sheet`.
- **Fix:** Re-ran with `--sheet --sheet-output artifacts/LOOK_SHEET_WF01_V2.jpg`.
- **Prevention:** README now carries exact reproducible commands.

## Camera quality/performance experiment
- **Initial approach:** Resize → crop → rotate for every 1920×1080 frame.
- **Problem:** Two resampling passes softened edges and made full rendering unnecessarily expensive.
- **Fix:** Solved zoom, truck, pedestal and roll as one inverse affine transform and one bicubic resample.
- **Result:** Cleaner ink edges, deterministic movement and lower rendering cost without reducing motion design.

## Boundary smoke false-negative
- **Failure:** First 99-frame transition smoke run flagged 12 WF-01 cuts because intentional black/white impact frames were judged with full-film average-luma bounds.
- **Diagnosis:** Motion deltas, dimensions and non-empty content all passed; only the inappropriate per-boundary tonal rule failed.
- **Fix:** Boundary test now allows authored impact flashes (`5 < mean luma < 250`, non-empty) while the final master retains strict full-film paper-world luma/dark-share gates.
- **Result:** All 33 boundaries pass at −2 / cut / +2 frames; minimum pre-cut delta 0.2281 and minimum post-cut delta 12.5166.

## Audio build dependency recovery
- **Failure:** First V2 WAV build could not import `imageio_ffmpeg` after the prior ephemeral environment was restored.
- **Fix:** Reinstalled the runtime package; source continues to resolve its deterministic bundled FFmpeg binary.
- **Result:** 48 kHz stereo mix built with 1,073 synchronized events, including 294 moving-stereo objects; voice remains byte-identical and un-stretched.

## GitHub checkpoint push
- **Failure:** Local checkpoint commit succeeded, but push failed because `.git/config` still referenced a deleted temporary `/tmp/gh.../gh` credential helper.
- **Disposition:** Do not retry the stale helper. Re-authorize at final synchronization using the durable device-code method or an enabled GitHub connector; no credential is stored in source.

## Full-render memory ceiling and delivery-size optimization
- **Failure:** The first two-way full render exceeded the 2 GiB runner during two simultaneous multithreaded x264 encoders; part 0's pipe broke after ~60 frames. Part 1 completed correctly.
- **Recovery:** Preserved the complete 1,110-frame second half, constrained future encoders to one thread, and rendered only the failed first half solo. The orchestration tool now automatically performs failed-half-only recovery.
- **Verification:** Both halves independently reported 1,110 frames / 37.00 s; lossless concat decoded all 2,220 frames at 1920×1080 / 30 fps / 74.00 s.
- **Size finding:** Grain, paper fibre and moving parallax made the initial CRF-18 mute mezzanine 100,649,624 bytes, too close to the 100 MB durable-upload ceiling once AAC was added.
- **Fix:** Created a delivery encode at H.264 High CRF 19 (still visually transparent for this source) and standardized the reproducible renderer at CRF 19. The delivery mute is 84,539,307 bytes, preserving comfortable upload headroom.
