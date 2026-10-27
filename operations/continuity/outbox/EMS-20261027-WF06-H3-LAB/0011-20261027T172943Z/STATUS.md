# Checkpoint 0011-20261027T172943Z

- Task: `EMS-20261027-WF06-H3-LAB`
- Status: `active`
- Title: WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan
- Style: `minimax-h3-video`
- Time: 2026-10-27T17:29:43Z
- Journal head: `f137fc2bd5f75f1194495908116ce59e1183f3a6ab1cc7ac7bfaa74bcd03777f`

## Completed since prior checkpoint

Trust-test handoff: the owner is running the first real Colab pass on a one-shot notebook (clip + x2 upscale, voice/foley off) to prove Drive mount + T4 work on his phone account before a full 3-shot reel. Job mob-test-01 sits in handed_off; resolve_project now resolves bare ids and payload dirs. Awaiting his DONE, after which: check -> finish (mix/verify/assemble) -> deliver.

## Exact next action

When owner says DONE: python3 tools/mobile_ops.py check mob-test-01, then finish + deliver; if blocked, read the blocker and hand him exactly one re-run instruction.

## Cross-platform rule

The same factual status must be applied to GitHub, Google Drive, Notion, Linear and Google Docs. Remote IDs/results are recorded in `SYNC.json`; no platform is silently skipped.
