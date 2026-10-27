# Changelog

## 0.3.3 — 2026-10-28

- `viper-2.2`: the delivery stopped looking like a still image. Three causes, all fixed:
  - **fps**: Wan renders natively at 16 fps; the finish pass forced 24 by duplicating frames. The master now
    keeps each clip's probed frame rate (`fps=None`), so motion is real frames, not copies.
  - **length/motion**: the phone notebook now defaults to `--max-frames 77` (4.8 s per shot at 16 fps) and the
    new `m-reel-01` example uses motion-first prompts (rain, smoke, wind) instead of a static slow push-in.
  - **audio**: a new `bed` foley engine builds a deterministic ambience bed with ffmpeg only (`anoisesrc` +
    prompt-driven filtering: rain / city / room tone). No download, no model, works on every run; MMAudio stays
    available but is wrapped so a failure can never kill the run.
- Second example project `studio/videogen/examples/m-reel-01/`: 3 shots x 77 frames, 3 Kokoro voice lines,
  ambience bed, 960x1664 delivered. Locally proven end to end: 14.53 s master, 16 fps, 48 kHz aac,
  loudnorm applied.

## 0.3.2 — 2026-10-28

- `viper-2.1`: the master now actually finishes inside Colab. Two real failures the owner's run exposed:
  - the concat demuxer splits `file <path>` on spaces, so Drive's `Wf-07 • Monarch Ai Agent / 05 · Projects`
    always died with "Impossible to open '/content/drive/MyDrive/Wf-07'". `list.txt` now holds bare
    segment names and ffmpeg runs with `cwd` = the segments folder.
  - `loudnorm` returns NaN on digital silence (`Qavg: nan`, "frames left in the queue") and kills the AAC
    encoder mid-write — that is why a 25 KB truncated master with no receipt appeared. The finish pass now
    measures `volumedetect` first and skips loudnorm honestly (`receipt.loudnorm = null`) when there is no
    voice/foley, and resamples to 48 kHz when it does run.
  - the master is staged inside `_segments/`, sanity-checked, then copied to `delivery/`; the receipt is only
    written after the copy, so a receipt always means a real file.
- Re-running a project whose clips already sit on Drive now skips the Wan download/load entirely (and skips
  voice/foley when their text is empty): a retry after a broken finish costs ~1 minute, not 20.

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
