# GPU jugaad — kaise chalana hai (2 minute)

## Rasta 1 · Colab (free T4 ya Pro A100)
1. Drive → `Chaos video 2` → `CHAOS_GPU_COLAB.ipynb` par right click → **Open with → Google Colaboratory**
2. `Runtime → Change runtime type → GPU`
3. `Runtime → Run all`
4. Notebook khud: GPU check → install → smoke test clip → (agar `CHAOS_JOBS.json` ho to) batch → clips wapas Drive ke `chaos_gpu_clips/` mein.

## Rasta 2 · Kaggle (free GPU quota, T4 x2 / P100)
1. kaggle.com → Create → Notebook → File → Import notebook → `CHAOS_GPU_COLAB.ipynb`
2. Settings → Accelerator = **GPU T4 x2**
3. Run all → Output tab se clips download.

## VRAM ke hisaab se kya milega (honest)
| GPU | Model | Result |
|---|---|---|
| T4 free 16 GB | LTX-Video 2B distilled | preview (480–768px, 2–4 s) — smoke test |
| L4 / 4090 24 GB | Wan2.2 TI2V-5B | 720p cinematic clips, asli kaam |
| A100 40 GB / Pro | Wan2.2-Animate-14B + TI2V-5B | character performance (expression replication) |

## Agent (main) ka hissa
- `CHAOS_JOBS.json` likhna (shot-by-shot prompts + seed + duration) — approval ke baad
- clips aa jayein to: timing/transitions/grade/HUD/end card/audio/QC/delivery
- 3D CPU base render (bpy) bhi main yahin kar sakta hoon — us render ko **driving video** bana kar Wan-Animate ko dena = exact motion + AI skin (sab se kam GPU hours)

---

## Drive copies (verified 2026-10-26)

Teeno files Drive folder **`Chaos video 2`** (`1uGPfl4pwPoL-D0VIag3hIejmbR__ochC`) mein upload ho chuki hain:

| File | Drive ID | Size |
|---|---|---|
| `CHAOS_GPU_COLAB.ipynb` | `1SKscDqK4j9Qx8TwzcKKbYxm2dm5l2vg-` | 14,926 B |
| `CHAOS_JOBS.example.json` | `1yOPHdCbvJ8KbDx2IP6k4S-oRfvGMrKmO` | 1,300 B |
| `README_GPU.md` (yeh file) | `1F5Qry8jO0QSdzaHStKM_Lfeuwa5Dvx9F` | 1,368 B |

**Honest note:** notebook ka live GPU run agent test nahi kar saka (sandbox mein GPU nahi). Sirf structure/syntax verified hai. Pehli baar chalane par agar koi cell fail ho, us cell ka error text bhej dein — main fix kar dunga.
