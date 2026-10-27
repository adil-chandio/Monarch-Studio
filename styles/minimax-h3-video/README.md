# WF-06 · MiniMax-H3 Generative Video

**Trigger:** `H3GO <topic or shot list>` · **Code:** WF-06 · **Slug:** `wf06` · **State:** PILOT_READY (no delivery yet)

Yeh style MiniMax-H3 ko Monarch ke production loop me lagata hai: **AI video + native audio** generate karke
WF-05 ke editing pipeline ko shots deta hai, aur WF-04 ke locked Monarch face ko on-screen perform karwata hai.

## 1. Sawal ka seedha jawab — Colab par kaise chalayein

**Model ko Colab ke GPU par na chalao. Colab ko control room banao.**

| | Route | Colab par | Output |
|---|---|---|---|
| **A (default)** | Hosted API — notebook/CLI jobs bhejta hai | ✅ free T4/CPU par bhi | 768P + **2K**, native audio, Ref2VA |
| B | Local pruned INT8 (ComfyUI) | ⚠️ Pro A100 80GB, ~42 GB download, 15–40 min/clip | 768P only |
| C | Local BF16 (SGLang/diffusers) | ❌ ~100–128 GB resident → 4×H100 class | 768P only |

Wajah numbers me hai: H3-Omni-Transformer 33B + Qwen3-VL-32B encoder + visual/audio VAEs =
**~100–128 GB BF16 resident**. Free Colab 16 GB, Pro 40 GB. 2K **sirf** API route se milta hai
(H3-Regenerate-2K closed-source hai).

Steps (poori detail `knowledge/01_COLAB_RUNBOOK.md`):

1. <https://platform.minimax.io> → API key → balance top-up.
2. Colab → upload `colab/MONARCH_H3_COLAB.ipynb` → Runtime **CPU**.
3. 🔑 Secrets → `MINIMAX_API_KEY` (notebook access ON).
4. Cells top-to-bottom: environment → key → templates → helpers → shot list → **cost gate** → run → receipts → ffmpeg.
5. Shot list approve hone par hi `DRY_RUN=False` + `CONFIRM_SPEND=True`.

Terminal/CI route (same logic, git-friendly shot lists):

```bash
export MINIMAX_API_KEY=...
python3 styles/minimax-h3-video/src/h3_client.py estimate data/shotlist.example.json
python3 styles/minimax-h3-video/src/h3_client.py run data/shotlist.example.json --out h3_runs          # dry run
python3 styles/minimax-h3-video/src/h3_client.py run data/shotlist.example.json --yes                  # spends money
```

## 2. Next level — WF-04 Monarch face se aage

```text
IDENTITY (WF-04: REAL face v5 + body v2)  →  PERFORMANCE (H3 Ref2VA: dialogue + lipsync + camera + audio)
                                          →  FILM (WF-05: typography, transitions, score, 24→30 fps conform)
                                          →  DELIVERY (Drive + receipts + records/)
```

| Level | Deliverable | Cost est. |
|---|---|---|
| L1 | 5 s identity + voice test (Ref2VA, 768P) | $0.40 |
| L2 | 3 shots × 5 s scene test (cuts + one dialogue beat) | ~$2 |
| L3 | 45–60 s Monarch reel (6–8 shots, 2K, WF-05 edit) | $8–12 |
| L4 | Locked ref pack + shot skeleton + gates → repeatable series | per episode |

Poora plan + reference pack + QC gates: `knowledge/04_WF04_MONARCH_FACE_INTEGRATION.md`.

## 3. Kya badalta hai, kya nahi

**Nahi badalta:** WF-01 stickman ka procedural rig authority; WF-03 noir ka hand-built plate + line-hero DNA;
WF-05 ka edit/typography/audio-design ownership. H3 in tino ko **replace nahi** karta.

**Badalta hai:** hero ke talking shots (asli dialogue + voice timbre), cinematic B-roll bina stock ke,
aur ek hi prompt skeleton se 16:9 + 9:16 dono versions.

## 4. Cost (list price, USD per output second)

| Model / resolution | Rate |
|---|---|
| `MiniMax-H3` 768P | $0.08 |
| `MiniMax-H3` 2K | $0.13 |
| `MiniMax-H3-Highspeed` 768P | $0.06 |
| `MiniMax-H3-Lite` 480P/768P | $0.04 |
| `MiniMax-H3-Max` 480P / 768P | $0.05 / $0.08 |
| 768P → 2K regeneration | $0.05 |
| Reference audio | free · first 5 images free · $0.04 per extra image · reference video billed per second |

10 s @2K = $1.30 · 15 s @2K = $1.95 · 60 s film (6×10 s @2K) ≈ $7.80 + retries (budget 1.5×).

## 5. Hard rules

1. **Spend gate:** koi batch `estimate` ke baghair submit nahi hota; `CONFIRM_SPEND`/`--yes` explicit.
2. **Receipts:** har shot ka `task_id`, `usage.output_seconds`, `content.url`, md5 — `receipts.json` me.
3. **Same reference pack** har shot me (front · 3/4 · profile · 2 expressions + 1 voice ref).
4. **2K ka wada sirf API route par.** Local run 768P hai.
5. **Language:** H3 ke stable 11 languages me Urdu/Hindi nahi — dialogue se pehle ek 4–5 s test.
6. **Licence:** H3 Community License local deployment US/EU/UK/South Korea me authorisation ke baghair nahi.
7. **Moderation:** blocked prompt (422 / code 1026) par retry na karo — prompt badlo aur log karo.
8. Heavy media Git me na dalo: refs Drive par, `assets/refs/` sirf placeholders + md5.

## 6. Files

| Path | Kya |
|---|---|
| `knowledge/INDEX.md` | knowledge map |
| `knowledge/00_MODEL_FACTS.md` | verified specs, architecture, VRAM, API fields, limits, pricing, licence |
| `knowledge/01_COLAB_RUNBOOK.md` | Colab step-by-step + Route B ka sach |
| `knowledge/02_PROMPTING.md` | H3 prompt grammar + Monarch templates (t2va / i2va / fl2va / ref2va) |
| `knowledge/03_ROUTES_AND_COST.md` | route decision table, cost model, batch strategy |
| `knowledge/04_WF04_MONARCH_FACE_INTEGRATION.md` | face → performance → film pipeline, levels, QC gates |
| `colab/MONARCH_H3_COLAB.ipynb` | runnable Colab notebook (API route, cost gate, receipts, assemble) |
| `src/h3_client.py` | stdlib CLI: `estimate` / `run` / `query` |
| `data/shotlist.example.json` | 3-shot example (Monarch Ref2VA + noir plate + reel insert) |
| `records/PROVENANCE.json` | source URLs + access date + what was verified |
| `tests/test_wf06_h3.py` | payload validation, cost math, receipts flow, CLI dry-run (offline) |

## 7. Status / open items

- ✅ Knowledge, notebook, CLI, tests, example shot list landed 2026-10-27.
- ⏳ No live generation yet (no API key in this sandbox; nothing was spent).
- ⏳ L1 identity test needs: reference pack crops in `assets/refs/` + one voice reference.
- ⏳ Drive folder / Notion page / Linear issue / Google Doc hub IDs not yet created (registry row lists them as `null`).
