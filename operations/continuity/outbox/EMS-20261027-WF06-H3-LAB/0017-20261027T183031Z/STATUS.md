# Checkpoint 0017-20261027T183031Z

- Task: `EMS-20261027-WF06-H3-LAB`
- Status: `active`
- Title: WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan
- Style: `minimax-h3-video`
- Time: 2026-10-27T18:30:31Z
- Journal head: `194fa35a586c6ebef2f560f2e2c835040000b14e506326556c830b0e021af304`

## Completed since prior checkpoint

viper-1.7 memory-safe phone notebook: the owner's crash was Colab host RAM (12.7 GB) during the 22.7 GB fp32 UMT5 load. Fix ported from the proven rivas-vega/wan2.1-t4-colab recipe: 4-bit NF4 text encoder on GPU, fp16 DiT, fp32 tiled+sliced VAE, HF_HUB_DISABLE_XET, glibc mallopt/malloc_trim, UniPC flow_shift 3.0 at 480p, pipeline deleted before upscale, Real-ESRGAN -> ffmpeg lanczos fallback. Test shot cut to 33 frames (~2 s, ~6 min render); mobile --max-frames added. 181 tests OK, validate 25/0, tag colab-test-04.

## Exact next action

Owner opens colab-test-04 link, one play button, waits 10-20 min; then sends DONE screenshot or the ZIP; agent runs mobile_ops ingest/check -> finish.

## Cross-platform rule

The same factual status must be applied to GitHub, Google Drive, Notion, Linear and Google Docs. Remote IDs/results are recorded in `SYNC.json`; no platform is silently skipped.
