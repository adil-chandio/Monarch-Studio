# Checkpoint 0008-20261027T160754Z

- Task: `EMS-20261027-WF06-H3-LAB`
- Status: `active`
- Title: WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan
- Style: `minimax-h3-video`
- Time: 2026-10-27T16:07:54Z
- Journal head: `fa16f992bb35c8c62787c3b04c644d795b2066a7b6a4faf4ee23bcfbc730c428`

## Completed since prior checkpoint

viper-1.3 makes the studio incapable of accidental spend: free_only() guard (default ON, MONARCH_ALLOW_PAID=1 to unlock), plan shows FREE-ONLY with blocked_paid count and rewrites paid steps, render prints FREE-ONLY MODE and skips the H3 client, doctor reports mode + card-free providers + Kaggle hours left, new quota command keeps a weekly ISO-week ledger (studio/free_quota.json) with per-provider limits parsed from studio/free_compute.json (Colab free T4, Kaggle ~30h/wk, Lightning 15 credits/mo, HF ZeroGPU 5min/day, laptop CPU; Modal excluded for card requirement). docs/FREE_ONLY_PLAYBOOK.md gives the full structure: who runs what, per-reel copy-paste flow, quota-exhaustion order, weekly rhythm, free ceiling, checklist. 10 new FreeOnlyTests; 130 tests OK, validate 25/1/0, manifest 1008 files, Drive synced to 17 files.

## Exact next action

Build the first real reel entirely free: user gives a voice line/topic (or Kokoro speaks it); run plan -> render (queue) -> Colab/Kaggle clips -> audio -> upscale -> mix -> verify -> assemble, logging GPU hours with quota --use, then promote to Drive 05/06.

## Cross-platform rule

The same factual status must be applied to GitHub, Google Drive, Notion, Linear and Google Docs. Remote IDs/results are recorded in `SYNC.json`; no platform is silently skipped.
