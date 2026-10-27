# Checkpoint 0018-20261027T191746Z

- Task: `EMS-20261027-WF06-H3-LAB`
- Status: `active`
- Title: WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan
- Style: `minimax-h3-video`
- Time: 2026-10-27T19:17:46Z
- Journal head: `80e9fb85d6a4448222c80bbd558f6efeb65bd46098b1b63fea23d730b92870ad`

## Completed since prior checkpoint

Milestone: the phone-only pipeline is PROVEN end to end on the owner's free Colab T4 — 4-bit UMT5 fix worked (host RAM 8.1-9.1 GB free), one clip rendered in 49 s (33 frames, 30 steps), upscale fell back to ffmpeg lanczos because basicsr would not build, ZIP landed in Drive 05 · Projects/m-test-01/. viper-1.8 hardens that install (--no-build-isolation + functional_tensor patch) and replaces guessed timings with measured ones. Only remaining gap: the sandbox cannot reach Google hosts, so mix/verify/assemble need the 0.2 MB ZIP attached in chat.

## Exact next action

Owner attaches m-test-01_outputs.zip; then mobile_ops ingest mob-test-01 --zip <path> -> check -> finish -> deliver with the Drive id.

## Cross-platform rule

The same factual status must be applied to GitHub, Google Drive, Notion, Linear and Google Docs. Remote IDs/results are recorded in `SYNC.json`; no platform is silently skipped.
