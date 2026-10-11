# Promoted learning — TUMHARI RESERVED SEAT · WF-03

**Task:** `EMS-20261011-002` · accepted 2026-10-11  
**Permanent production:** `../films/tumhari-reserved-seat/`  
**Film number:** intentionally unassigned; the historical Film-#3 conflict remains unresolved.

## What was proven

1. **WF-03 can expand into a 16:9 cinematic short without repeating THE SHADOW or THE WINDOW.** The new authored world is a midnight station platform built around rain, rails, departure-board time, ticket geometry, sodium/cyan separation, and a humanised Monarch performance.
2. **Darkness can be controlled and measured rather than guessed.** The accepted picture measured mean luma 26.22, dark share 0.823, p99 highlight 203.83, no empty samples, and no perfectly still sampled pairs.
3. **A restrained noir cadence can still retain attention.** Thirty-four voice-led beats maxed at 4.70 seconds; motivated camera drift, atmospheric motion, prop state, gaze, and light changes keep holds alive.
4. **The soundtrack can preserve a distinct workflow identity around shared narration.** A 72 BPM station-score architecture, rail/rain textures, asymmetric room reflections, and 121 synchronized sound events kept `voice-00` exact and central.
5. **Six-Hz environment caching is compatible with full-rate cinema motion.** Environmental plates can update less frequently while character, type, camera, and transition layers remain at 24 fps.
6. **Objective acceptance protects both mood and delivery.** The final passed 21/21 delivery gates; the concept and implementation passed 18/18 freshness gates.

## Failures that became permanent safeguards

- The implemented `ticket_hole_bloom` transition must be named in DNA as well as code. A missing ledger entry is a provenance/freshness failure even when the visual exists.
- Fractional-power envelopes must clamp their base before exponentiation to prevent NaNs.
- Transition-strip coordinates must be clamped before raster rectangle drawing; test all boundaries before full render.
- After `loudnorm`, explicitly resample and encode at 48 kHz; do not rely on implicit filter-chain output rates.
- Preserve separate implementations and event ledgers when two workflows share a script and voice. Shared narrative does not license shared visual or sonic treatment.
- Never assign a future film number until the pre-existing Film-#3 contradiction is resolved.

## Reuse rule

Reuse engineering safeguards and measured thresholds, not this film’s creative answers. Future WF-03 work should avoid repeating the rain-platform, reserved-seat, ticket-hole, departure-board, and yellow-seat resolution unless deliberately transformed and cleared by freshness review.

## Evidence

- DNA and lock: `../films/tumhari-reserved-seat/DNA.json`, `MASTER_TIMELINE.json`
- Source: `../films/tumhari-reserved-seat/src/`
- Measurements: `../films/tumhari-reserved-seat/artifacts/`
- Failure/fix record: `../films/tumhari-reserved-seat/records/EXPERIMENTS_FAILURES_FIXES.md`
- Delivery receipt: `../films/tumhari-reserved-seat/records/DELIVERY_RECEIPT.md`
