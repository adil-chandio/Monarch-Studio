# 03 · Routes, cost aur production design

## 1. Route decision — ek table

| | **Route A · Hosted API** | **Route B · Local pruned (ComfyUI/GGUF)** | **Route C · Local official (SGLang/diffusers BF16)** |
|---|---|---|---|
| Where | Colab / laptop / this sandbox | 1× 12–24 GB local GPU (slow) ya 1× A100 80GB | 4× H100/H200 class |
| Max res | **2K** (768P → regenerate) | 768P | 768P |
| Native audio | ✅ | ✅ | ✅ |
| Ref2VA (face/voice) | ✅ API roles | ✅ if workflow supports | ✅ |
| Prompt preprocessing | H3-Context-IR API | prompt khud likho | prompt khud likho |
| 5 s clip ka waqt | 30 s – 4 min | 36 s (5090 NVFP4) … 10 min (offload) | ~13–20 s |
| Cost | $0.08–0.13 / s | hardware + bijli | ~$8–12 / hr (4×H100 rent) |
| Setup effort | **10 minute** | 2–6 ghante | 1 din |
| Failure mode | moderation block, rate limit | OOM, slow, session dead | OOM, NCCL, version hell |

**Default: Route A.** Route B sirf tab jab output volume itna ho ke per-second pricing mehnga lage, ya internet/
privacy ki wajah se data bahar na ja sake. Route C individual studio ke liye economically bekaar hai.

## 2. Cost model (per-second billing, list price)

```
cost = output_seconds × rate[resolution]  +  additional_reference_images × 0.04
       + reference_video_seconds × rate[resolution]
```

| Deliverable | Shots | Dur/shots | Res | Est. cost |
|---|---|---|---|---|
| Ek hero talking clip test | 1 | 5 s | 768P | $0.40 |
| Ek hero talking clip test | 1 | 5 s | 2K | $0.65 |
| 30 s reel | 4 | 5–8 s | 2K | ~$3.20 + retries |
| 60 s film | 6 | 10 s | 2K | ~$7.80 + retries |
| 60 s film, 768P draft → 2K final | 6 | 10 s | 768P→2K | 6×0.80 + 6×0.50 = $7.80 |

Retry budget: **1.5× multiplier** rakho (har shot ke 1.5 attempts average). 60 s film ka realistic budget ~$12.
10 s @2K ≈ $1.30 — client ke liye quote karte waqt retries + editing time shamil karo.

Model choice by stage:

- **Explore / storyboard:** `MiniMax-H3-Lite` 480P ($0.04/s) — composition aur timing check karo.
- **Draft:** `MiniMax-H3` 768P ($0.08/s) ya `Highspeed` ($0.06/s).
- **Final:** `MiniMax-H3` 2K ($0.13/s), ya 768P + regeneration ($0.08 + $0.05 = $0.13/s — barabar, magar
  regeneration me context reuse hota hai to detail behtar aati hai).

## 3. Batch strategy (paisa bachane ka asli tareeqa)

1. **Ek shot ko 3 variants me na maaro.** Pehle 480P `Lite` par composition lock karo, phir final.
2. **Prompt pehle likho, generate baad me.** `DRY_RUN` gate + `estimate_cost()` se pehle number dekho.
3. **Fail fast:** blocked prompt (422/1026) par retry na karo — prompt badlo.
4. **Reuse the reference set:** images free hain pehli 5 tak; same 3–4 images har shot me use karo.
5. **Chain with FL2VA:** shot N ka last frame shot N+1 ka first frame → continuity + fewer retries.
6. **Drift check:** 2K par jaane se pehle 768P draft par identity verify karo (2K sirf paisa double karta hai).

## 4. Production pipeline (Monarch ke andar)

```text
WF-04 character (locked face/body authority)
        │  reference stills: front · 3/4 · profile · expression  (≤9, first 5 free)
        ▼
H3 Ref2VA / FL2VA  ── shots 4–15 s, 24 fps, native 32 kHz stereo
        │  receipts.json (task_id, usage, url, md5)
        ▼
QA gates: identity · audio · format · content-safety · cost
        ▼
WF-05 Premium Motion Editing (typography, transitions, score, conform to 30 fps, captions)
        ▼
Master + Drive delivery + records/
```

## 5. What H3 changes for Monarch (aur kya nahi badalta)

**Badalta hai:**

- Talking-hero shots: asli dialogue + lipsync + voice timbre → pehle jo WF-04 me static face + VO tha, ab
  on-camera performance ban sakta hai.
- B-roll: cinematic plates bina stock footage ke, native sound ke saath.
- 9:16 reels: ek hi prompt se 16:9 + 9:16 versions (alag ratio, same prompt skeleton).

**Nahi badalta:**

- **Stickman animation (WF-01)** procedural renderer hi rahega — H3 se stick figure ki consistent line art
  nahi milti, aur woh style rig-based hai.
- **Noir film (WF-03)** ka hand-built plate + line-hero DNA. H3 ko sirf environment plates ya transitions ke
  liye use karo, hero ke liye nahi (warna DNA toot jata hai).
- **Typography, timing, music design, delivery gates** — woh WF-05/studio ka kaam hai.

## 6. Legal / platform notes

- H3 Community License: local deployment US / EU / UK / South Korea me authorisation ke baghair nahi — client
  delivery me yeh note karo. API use platform terms ke tehat hai.
- Moderated inputs: text, images, video aur enhanced prompt sab filter hote hain. Corporate client ke liye
  pehle test prompt bhejo, baad me shoot na karo.
- Content rights: reference images/audio sirf apne ya licensed. Monarch face user ka apna hai (authority
  `characters/monarch`), third-party faces ke liye written permission record karo.
