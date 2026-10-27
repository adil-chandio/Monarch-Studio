# Checkpoint 0009-20261027T162448Z

- Task: `EMS-20261027-WF06-H3-LAB`
- Status: `active`
- Title: WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan
- Style: `minimax-h3-video`
- Time: 2026-10-27T16:24:48Z
- Journal head: `764d811bea35342c0d12aece709b1c55e145f06c746ffe0de7a3dd2737486132`

## Completed since prior checkpoint

viper-1.4 mobile milestone: videogen mobile writes one phone-first Run-all notebook (clips+voice+foley+upscale, prompts baked in, per-stage toggles, DONE/ADHURA gate); which() falls back to the imageio-ffmpeg static binary and probe() parses 'ffmpeg -i' so mix/verify/assemble run in the sandbox; three real bugs found and fixed by an end-to-end sandbox run (asplit ducker for the single-consumption ffmpeg rule, loudnorm moved inside the graph, verify now rejects 0-byte files); docs/MOBILE.md + AGENTS mobile protocol pin that the owner never types commands; 142 tests OK, validate 25/0, Drive synced to 19 files.

## Exact next action

When the owner says 'reel banao <topic>': new project with real prompts, mobile notebook, upload to Drive, give the Colab link, then after DONE run mix --loudnorm + verify + assemble and report the master.

## Cross-platform rule

The same factual status must be applied to GitHub, Google Drive, Notion, Linear and Google Docs. Remote IDs/results are recorded in `SYNC.json`; no platform is silently skipped.
