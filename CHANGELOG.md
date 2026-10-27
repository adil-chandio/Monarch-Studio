# Changelog

## 0.3.1 — 2026-10-27

- `viper-1.7`: the phone notebook now runs inside free Colab's 12.7 GB host RAM — UMT5 text encoder in
  4-bit NF4, fp16 DiT, tiled/sliced VAE, `HF_HUB_DISABLE_XET`, glibc `malloc_trim`, UniPC `flow_shift=3.0`,
  and the pipeline is released before upscale. Fixes the real crash the owner hit ("session crashed after
  using all available RAM").
- `mobile --max-frames N` caps frames per shot (33 ≈ 2 s, 49 ≈ 3 s) so a free-T4 render fits a phone session.
- Real-ESRGAN upscale now falls back to ffmpeg lanczos if `basicsr`/`realesrgan` cannot install.

## 0.3.0 — 2026-10-27

- Added `tools/mobile_ops.py` (`mobileops-1.0`): durable per-project job state machine for phone-only
  operation (`intake → planned → handed_off → partial/clip_ready → mixed → verified → assembled → delivered`,
  plus `blocked`), with evidence gates, owner-facing cards and resume across turns.
- Added `docs/MOBILE_WORKFLOW.md`: the phone SOP (contract, gates, failure matrix, turn-end checklist,
  definition of done) and pinned it in `AGENTS.md`, WF-07 `workflow.json` and the registry tool table.
- `viper-1.4`: `mobile` notebook command, static-ffmpeg fallback + `ffmpeg -i` probe, fixed mix filtergraph,
  `verify` now rejects 0-byte files.

## 0.2.0 — 2026-10-11

- Separated permanent named editing styles from the single running workflow slot.
- Added atomic active-task state, hash-chained journal, visible-chat transcript and exact resume capsule.
- Added immutable checkpoints, long-process ledger, 55-minute watcher and GitHub hourly audit.
- Added five-platform GitHub/Drive/Notion/Linear/Docs outbox with independent sync status.
- Added permanent per-style knowledge indexes and completion/promotion protocol.
- Corrected WF-03 current Drive inventory and delivery IDs from a fresh 35-item audit.

## 0.1.0 — 2026-10-11

- Assembled WF-01 and WF-03 from connected Notion, Linear, Google Drive and Google Docs authorities.
- Added locked Monarch REAL/STICK character authority, Bible v2 and Master Board v2.
- Preserved complete fully sourced implementations for IZZAT v2, THE SHADOW and THE WINDOW.
- Recorded 4:00 AM and AB KARO ABHI evidence without overstating missing source/gates.
- Added normalized registries, provenance/reconciliation documentation, repository validation and generated legacy-path runtime.
- Added pinned EffectCraft and awesome-opus5-5-videos vendor boundaries.
