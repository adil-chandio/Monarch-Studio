# WF-07 · Monarch AI Agent — knowledge map

Yeh workflow koi naya model nahi sikhata; yeh **studio ka operating layer** hai: kahan se kya generate hota hai,
kahan save hota hai, aur kis cheez ka paisa lagta hai.

| # | Where | What it answers |
|---|---|---|
| 1 | [`../README.md`](../README.md) | free vs paid ek nazar me, folder map, commands, rules |
| 2 | [`../data/drive.json`](../data/drive.json) | Drive authority: root + 6 subfolder IDs |
| 3 | [`../../docs/VIDEOGEN.md`](../../docs/VIDEOGEN.md) | VIPER-1 manual: project schema, engines, gates, exit codes |
| 4 | [`../../tools/videogen.py`](../../tools/videogen.py) | the engine itself (doctor/new/plan/render/verify/assemble/status) |
| 5 | [`../../styles/minimax-h3-video/knowledge/00_MODEL_FACTS.md`](../../styles/minimax-h3-video/knowledge/00_MODEL_FACTS.md) | H3 facts, VRAM, API fields, pricing |
| 6 | [`../../styles/minimax-h3-video/knowledge/01_COLAB_RUNBOOK.md`](../../styles/minimax-h3-video/knowledge/01_COLAB_RUNBOOK.md) | Colab control-room route |
| 7 | [`../../styles/minimax-h3-video/knowledge/02_PROMPTING.md`](../../styles/minimax-h3-video/knowledge/02_PROMPTING.md) | prompt grammar + Monarch templates |
| 8 | [`../../styles/minimax-h3-video/knowledge/05_FREE_ROUTES.md`](../../styles/minimax-h3-video/knowledge/05_FREE_ROUTES.md) | is H3 free? trial routes, tunnel risks |
| 9 | [`../../styles/minimax-h3-video/knowledge/06_NEXT_LEVEL_TOOLBOX.md`](../../styles/minimax-h3-video/knowledge/06_NEXT_LEVEL_TOOLBOX.md) | model menu by GPU tier + free talking-face chain |
| 10 | [`../../studio/videogen/examples/monarch-reel-01.project.json`](../../studio/videogen/examples/monarch-reel-01.project.json) | ready example project |
| 11 | [`AUDIO.md`](AUDIO.md) | free audio stack: Kokoro/Chatterbox, MMAudio/ThinkSound, MusicGen, Ovi, licences |
| 12 | [`QUALITY.md`](QUALITY.md) | quality ladder: 480p kyun, upscale kya karta hai, 1080p kab, paid kab |

## Standing decisions

1. **Free is the default.** No `MINIMAX_API_KEY` → every shot resolves to the free T4/lipsync chain at $0.
2. **Money needs two keys:** an estimate you have read, and `render --yes`. `budget_usd` is a hard gate (1.5× retries).
3. **Only `verify` may call a shot done.** Exit 3 = not delivered, no matter what the render log said.
4. **Drive is the delivery home, Git is the truth.** Project files, receipts and masters to Drive;
   knowledge and code stay in the repository.
5. **Free route renders 480p silent** — fine for drafts, reels-as-animatics and plates. `upscale` (realesrgan or
   lanczos x2) takes it to 960×1664; that is sharper, **not** true 1080p detail. Real 1080p/2K and native stereo
   dialogue need the paid H3 route (or WF-05 finishing on top of free plates).
6. **Never sell a free-tier render as an H3 output,** and never promise 2K from a local run.
7. **Audio is free stems, not magic:** voice + foley + bed + LatentSync costs $0; native synced
   dialogue in one pass needs Ovi (24 GB) or the paid H3 API.
8. **Licence before delivery:** MMAudio and MusicGen weights are CC-BY-NC — personal/portfolio yes,
   paid client work needs ThinkSound + licensed music.
