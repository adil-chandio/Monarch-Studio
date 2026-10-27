# Checkpoint 0012-20261027T173336Z

- Task: `EMS-20261027-WF06-H3-LAB`
- Status: `active`
- Title: WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan
- Style: `minimax-h3-video`
- Time: 2026-10-27T17:33:36Z
- Journal head: `2f21a7f143038de0acc3b1162f5f1328cbcd64350103d3276ff2285317e9f6ed`

## Completed since prior checkpoint

Colab handoff bug found and fixed: Drive notebooks must be named *.ipynb or Drive/Colab refuses them ('This file type is unsupported'). Renamed TEST_01_phone_run_all.ipynb (id 1Fc1fprDJwqcp9c1rYSx6z7sLD1bfNMaf, link unchanged) and MOBILE_monarch-reel-01.ipynb; naming rule documented in AGENTS.md + MOBILE_WORKFLOW 5b and pinned in drive.json. Job mob-test-01 still handed_off, awaiting the owner's Run all + DONE.

## Exact next action

Owner re-opens the same Colab link and taps Runtime > T4 GPU > Run all; on DONE run mobile_ops check mob-test-01 then finish.

## Cross-platform rule

The same factual status must be applied to GitHub, Google Drive, Notion, Linear and Google Docs. Remote IDs/results are recorded in `SYNC.json`; no platform is silently skipped.
