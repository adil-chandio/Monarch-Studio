# Checkpoint 0007-20261027T150212Z

- Task: `EMS-20261027-WF06-H3-LAB`
- Status: `active`
- Title: WF-06 MiniMax-H3 generative video: Colab route + Monarch face plan
- Style: `minimax-h3-video`
- Time: 2026-10-27T15:02:12Z
- Journal head: `7a6fe77c2a394d6d1669b9fccd19d9a9839f7977048a5cf5083738da96b1bb6c`

## Completed since prior checkpoint

viper-1.2 delivers the free audio + quality answer: new audio command writes audio/AUDIO_<project>.ipynb (Kokoro or Chatterbox voice, MMAudio/ThinkSound foley, MusicGen bed, receipt), new mix command builds per-shot ffmpeg graphs (vo+foley amix, sidechain-ducked bed, optional loudnorm -16 LUFS, video copied), shot_media prefers -mix stems, verify fails when stems exist but the file has no audio stream, plan prints non-commercial licence warnings, knowledge/AUDIO.md documents the researched stack (with licence reality) and the Ovi/Kandinsky 24GB wall, tool_registry.json extended with 7 audio models in the existing schema, docs/VIDEOGEN.md + WF-07 README + INDEX updated, 120 tests OK, validate 25/1/0, manifest 1000 files, Drive synced to 15 files.

## Exact next action

First real reel: user supplies Monarch reference crops + a voice line (or lets Kokoro speak it); run plan -> render (free queue) -> audio (Colab) -> upscale (Colab) -> mix -> verify -> assemble, then promote to 05 · Projects/<id>/ and 06 · Masters & Receipts/.

## Cross-platform rule

The same factual status must be applied to GitHub, Google Drive, Notion, Linear and Google Docs. Remote IDs/results are recorded in `SYNC.json`; no platform is silently skipped.
