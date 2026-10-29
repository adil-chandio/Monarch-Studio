# Checkpoint 0006-20261027T143143Z

- Task: `EMS-20261027-WF06-H3-LAB`
- Status: `active`
- Title: WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan
- Style: `minimax-h3-video`
- Time: 2026-10-27T14:31:43Z
- Journal head: `3759b475adae22f1ad696effb640f494ccf44f0dcae62298bd936ab2efd145f6`

## Completed since prior checkpoint

viper-1.1 quality stage delivered: FREE_FRAMES table aligned with the queue (480x832 9:16, 480x608 4:5), delivery block (upscale/factor/target_height), plan DELIVERY line + 'scale, not detail' warnings, new upscale command writing a self-contained Colab notebook (Real-ESRGAN x2 on T4 or ffmpeg Lanczos x2 on CPU) with audio passthrough + upscale_receipt.json, verify enforces target_height (exit 3), assemble prints the sharpening note, 10 new QualityTests (104 tests OK, 2 skipped), validate 25/1/0, manifest ~995 files, Drive WF-07 synced to 14 files.

## Exact next action

First real project: user provides Monarch reference crops + one voice line; run plan -> render (free queue) -> upscale -> verify -> assemble, then promote to 05 · Projects/<id>/ and 06 · Masters & Receipts/.

## Cross-platform rule

The same factual status must be applied to GitHub, Google Drive, Notion, Linear and Google Docs. Remote IDs/results are recorded in `SYNC.json`; no platform is silently skipped.
