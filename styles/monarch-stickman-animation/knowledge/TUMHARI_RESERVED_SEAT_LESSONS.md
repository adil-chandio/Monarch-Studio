# Promoted learning — TUMHARI RESERVED SEAT · WF-01

**Task:** `EMS-20261011-002` · accepted 2026-10-11  
**Permanent production:** `../films/tumhari-reserved-seat/`

## What was proven

1. **WF-01 works as a premium 16:9 short without becoming a generic explainer.** The paper/ink/charcoal world, single yellow SHADE accent, hand-built Monarch poses, print-registration texture, and tactile transitions retain the workflow identity at 1920×1080.
2. **A 34-beat voice-led timeline can sustain 74 seconds.** Beat lengths maxed at 4.70 seconds, with visual progression and local motion inside every beat rather than arbitrary high-frequency cutting.
3. **A selected VO should remain exact.** The approved `voice-00` was not stretched; picture and sound were authored around its native cadence.
4. **Foreground animation and environment refresh need not share a rate.** Caching environment plates at 6 Hz while rendering character, type, transition, and camera layers at 30 fps materially reduced cost without violating the measured motion floor.
5. **Procedural stereo can stay narration-first.** 352 synchronized events, asymmetric filtered room taps, and a restrained bed produced valid stereo depth while the voice remained centred and intelligible.
6. **Objective acceptance protects craft.** The final master passed 21/21 delivery gates and the concept passed 18/18 freshness gates before promotion.

## Failures that became permanent safeguards

- Fractional-power whoosh envelopes must clamp the sine base to non-negative before exponentiation, or NumPy can emit NaNs.
- Edge-entering transition strips must clamp coordinates before rectangle drawing; alternating strips can otherwise generate `x0 > x1` at a frame boundary.
- FFmpeg `loudnorm` may leave an oversampled output rate. Append `aresample=48000` and also force encoder `-ar 48000`; never infer sample rate from the source mix.
- Smoke-test frames immediately before, at, and after every transition boundary before a full render.
- Do not weaken gates to accept a render. Correct the implementation, rerun the unchanged gate, and record the failure and fix.

## Reuse rule

Reuse these engineering safeguards, not this film’s visual answers. A future WF-01 concept must pass novelty/freshness checks and must not recycle this film’s invisible-queue, reserved-seat, ticket, or yellow-seat climax devices without explicit creative justification.

## Evidence

- DNA and lock: `../films/tumhari-reserved-seat/DNA.json`, `MASTER_TIMELINE.json`
- Source: `../films/tumhari-reserved-seat/src/`
- Measurements: `../films/tumhari-reserved-seat/artifacts/`
- Failure/fix record: `../films/tumhari-reserved-seat/records/EXPERIMENTS_FAILURES_FIXES.md`
- Delivery receipt: `../films/tumhari-reserved-seat/records/DELIVERY_RECEIPT.md`
