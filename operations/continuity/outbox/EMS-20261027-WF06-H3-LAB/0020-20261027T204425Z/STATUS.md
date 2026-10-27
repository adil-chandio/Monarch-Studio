# Checkpoint 0020-20261027T204425Z

- Task: `EMS-20261027-WF06-H3-LAB`
- Status: `active`
- Title: WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan
- Style: `minimax-h3-video`
- Time: 2026-10-27T20:44:25Z
- Journal head: `cbdc853e42c9d0d3860a167d4c311ebd5f4fac3e2ff5514716fe38520d97edad`

## Completed since prior checkpoint

viper-2.0: finish stage rewritten from a locally proven prototype (per-shot segments -> concat demuxer -> loudnorm), all pip installs use subprocess instead of !magic (a bang inside try/if becomes a bash error on Colab), DELIVERY moved after BASE, template escapes removed. New test executes the notebook's own finish cell against real ffmpeg and asserts a 960x1664 aac master with md5. 189 tests OK, validate 25/0, tag colab-test-07 pushed.

## Exact next action

Owner runs colab-test-07: clips skip, finish builds delivery/m-test-01_MASTER.mp4 + colab_master_receipt.json in ~2 min; then read the receipt with the Drive connector, adopt, deliver.

## Cross-platform rule

The same factual status must be applied to GitHub, Google Drive, Notion, Linear and Google Docs. Remote IDs/results are recorded in `SYNC.json`; no platform is silently skipped.
