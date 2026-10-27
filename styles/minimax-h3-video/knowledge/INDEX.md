# WF-06 · knowledge index

Permanent, source-backed knowledge for MiniMax-H3 inside Monarch Studio. Read in this order.

| # | File | Read when | Contents |
|---|---|---|---|
| 00 | [`00_MODEL_FACTS.md`](00_MODEL_FACTS.md) | before any plan or quote | what H3 is, the three modules, what is open vs API-only, architecture + weight sizes, measured VRAM/time table, framework list, API endpoints/fields/limits, pricing, licence, honest risks |
| 01 | [`01_COLAB_RUNBOOK.md`](01_COLAB_RUNBOOK.md) | when running it | route comparison, Colab steps, secrets, Drive, reference-image hosting, Route B reality check, delivery gates |
| 02 | [`02_PROMPTING.md`](02_PROMPTING.md) | before writing a prompt | T2VA/I2VA/FL2VA/Ref2VA shapes, shot/camera/dialogue grammar, Monarch locks, language limits (no stable Urdu/Hindi), ready templates, shot-list rules |
| 03 | [`03_ROUTES_AND_COST.md`](03_ROUTES_AND_COST.md) | before committing money or scope | route decision table, cost model + worked examples, batch strategy, production pipeline, what H3 changes and does not, legal notes |
| 04 | [`04_WF04_MONARCH_FACE_INTEGRATION.md`](04_WF04_MONARCH_FACE_INTEGRATION.md) | for Monarch-face work | reference pack spec, copy-paste Ref2VA shot skeleton, L1–L4 levels, QC gates, WF-05 handoff contract, when NOT to use H3 |

## Executable knowledge

| Path | Purpose |
|---|---|
| [`../colab/MONARCH_H3_COLAB.ipynb`](../colab/MONARCH_H3_COLAB.ipynb) | Colab control room: env → key → templates → helpers → shot list → cost gate → run → receipts → ffmpeg assemble |
| [`../src/h3_client.py`](../src/h3_client.py) | stdlib CLI (`estimate` / `run` / `query`), payload validation, cost math, receipts |
| [`../data/shotlist.example.json`](../data/shotlist.example.json) | 3-shot example: Monarch Ref2VA hero line, noir T2VA plate, Lite reel insert |
| [`../../tests/test_wf06_h3.py`](../../tests/test_wf06_h3.py) | offline tests: mutual-exclusion rule, ratio rules, duration/resolution guards, cost math, receipts flow, CLI dry run |
| [`../records/PROVENANCE.json`](../records/PROVENANCE.json) | sources, access date, what was verified, what is assumed |

## Standing decisions

1. **Route A (hosted API) is the default.** Local weights are a cost/privacy exception, never the production default.
2. **Colab is a controller, not a GPU.** CPU runtime is enough; GPU units on the API route are wasted money.
3. **2K only via API** (generation at 2K or 768P → regeneration). Local = 768P.
4. **Price before submit.** `estimate` + 1.5× retry buffer recorded in the project record.
5. **Identity via reference pack, not prompt wording.** Same 3–4 images every shot in a scene.
6. **Language risk is explicit.** Urdu/Hindi are not in H3's stable set; test one line first.
7. **WF-01/WF-03 engines are not replaced.** H3 supplies plates/talking shots only.
8. **No credentials in Git.** Key via `MINIMAX_API_KEY` (Colab Secrets or env).
