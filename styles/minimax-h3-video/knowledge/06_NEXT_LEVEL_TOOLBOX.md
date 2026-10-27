# 06 · Next-level toolbox — kya chalayein, kis GPU par, kitne me

_27 Oct 2026 · yeh file "mazedar next level" ka menu hai, magar har row ke saath uski qeemat aur shart likhi hai._
Machine-readable version (planner isi ko parhta hai): [`../data/tool_registry.json`](../data/tool_registry.json).
Route nikalne ka command: `python3 styles/minimax-h3-video/src/route_planner.py plan --need talking_hero --free`

## 1. Tiers — pehle apna GPU pehchano

| Tier | GPU | Kya mumkin | Kya nahi |
|---|---|---|---|
| **t4_free** | Colab free T4 16 GB (Turing sm_75) | Wan 2.1 1.3B 480p, LTX distilled (fp16), **LatentSync 1.5 lipsync**, LivePortrait, MuseTalk | bf16, FP8/NVFP4, H3 local, Wan 2.2 fp8, Hunyuan 1.5 fp8, LTX-2.5 |
| **colab_pro** | L4 24 GB / A100-40 | Wan 2.2 TI2V-5B 720p/24fps, HunyuanVideo 1.5 (fp8+offload, **best faces**), LatentSync 1.6 | LTX-2.5 full, H3 local |
| **rented** | RTX 4090/5090, A100-80, H100 | Wan 2.2 A14B, LTX-2.5 (audio), H3 local (768p), sab kuch bina compromise | 2K H3 (closed) |
| **api** | koi nahi | H3 2K + native stereo + Ref2VA identity | GPU control, unlimited free |

T4 ki technical wajah: Turing me `bfloat16`, FP8 aur NVFP4 **nahi** hote. Is liye 2026 ke naye models
(fp8/NVFP4 checkpoint) T4 par nahi chalte — chahe kitna hi offload karo.

## 2. Model menu (verified rows)

### Free tier (T4) — $0
| Model | Licence | Audio | Res / fps | VRAM | 5 s clip | Kaam |
|---|---|---|---|---|---|---|
| **Wan 2.1 T2V 1.3B** | Apache-2.0 | ❌ | 832×480 · 16 fps | ~8 GB | 8–25 min | drafts, B-roll plates |
| **LTX-Video distilled** | LTX open weights | ❌ | 512–704p | ~12 GB | 3–8 min | tez drafts (T4 par fp16 caveat) |
| **LatentSync 1.5** | Apache-2.0 + OpenRAIL++ | input audio | source clip | **8 GB** | minutes | **lipsync — asli hero step** |
| **MuseTalk** | repo licence | input audio | 256 px face | ~16 GB | near-realtime | LatentSync setup fight kare to fallback |
| **LivePortrait** | repo licence | ❌ | portrait crop | ~8 GB | seconds | still se halki motion |

### 24 GB class — $0 (sirf compute)
| Model | Licence | Audio | Res | VRAM | Kaam |
|---|---|---|---|---|---|
| **Wan 2.2 TI2V-5B** | Apache-2.0 | ❌ | 720p @ 24 fps | 8 GB (fp8/offload) – 24 GB fp16 | best free quality/size |
| **HunyuanVideo 1.5** | Tencent community | ❌ | 720p (1080 via SR) | 14 GB offload / 24 GB fp16 | **best free faces**, ~75 s distilled on 4090 |
| **LatentSync 1.6** | Apache-2.0 | input audio | 512 px face | 18 GB (16 GB with offload) | sharper lipsync |

### High end — rented GPU
| Model | Licence | Audio | Res | VRAM | Kaam |
|---|---|---|---|---|---|
| **Wan 2.2 A14B (MoE)** | Apache-2.0 | ❌ | 720p | 16 GB GGUF / 80 GB fp16 | best motion realism |
| **LTX-2.5** | LTX-2 Community (free < $10M ARR) | ✅ native | up to 4K 50 fps | ~32 GB fp8 / 16 GB NVFP4 (Blackwell) | free-tier native audio + 4K |
| **MiniMax-H3-Base** | H3 Community (territory exclusions) | ✅ | 768p | 80 GB pruned / 4×H100 | H3 quality bina per-second bill |

### Paid API
| Model | Audio | Res | Cost | Kaam |
|---|---|---|---|---|
| **MiniMax-H3** | ✅ 32 kHz stereo, 11 languages | 768P / **2K** | $0.08 / $0.13 per s | dialogue, lipsync native, client-grade hero |

## 3. Aap ke kaam ke liye asli "next level" — free talking Monarch

Yeh sabse important cheez hai is research me: **bolne wala Monarch face banane ke liye H3 lazmi nahi.**

```text
1) Silent clip      Wan 1.3B / LTX (T4, $0)          → face + camera + halki motion
2) Aap ki awaaz     own VO / TTS (Urdu bhi)          → audio track
3) Lipsync          LatentSync 1.5 (T4, $0)          → hont aap ki awaaz se match
4) Finish           WF-05 typography + music + grade → deliverable
```

Kyun kaam karta hai: LatentSync **source clip ka chehra** rakhta hai (identity lock already solved) aur sirf
mouth region ko audio se drive karta hai. H3 ka faida sirf yeh rehta hai ke woh **audio bhi khud banata hai,
2K deta hai, aur expression/camera ek hi pass me** karta hai. Is liye:

- **Draft / reel / test** → free chain
- **Client hero shot, 2K, native dialogue** → H3 paid ($0.40–0.65 per 5 s)

### Free lipsync chain ke exact steps (T4)
```bash
# 1. base clip (notebook se)     : MONARCH_T4_FREE_BRIDGE.ipynb → shot.mp4
# 2. voice                        : apni VO ya TTS → voice.wav (16-bit PCM)
# 3. LatentSync 1.5 (T4 patch zaroori)
git clone https://github.com/bytedance/LatentSync
cd LatentSync && bash setup_env.sh -h   # upstream instructions; checkpoints ~5 GB
#    T4 ki trap: code `capability[0] > 7` check karta hai, T4 = (7,5) → fp32 → OOM.
#    Patch: `>= 7` karo taake fp16 chale (~12 GB VRAM, 16 GB me fit).
python -m scripts.inference --inference_config configs/inference/sd15.yaml   # 1.5 checkpoint
#    video + audio input, output mp4 → Drive
```
LatentSync 1.6 (18 GB) sirf tab jab 24 GB card ho — mouth sharper, magar T4 par nahi.

## 4. Route decision tree (ek nazar me)

```text
Audio/dialogue chahiye?
├── Haan ──► paid H3 (native stereo + lipsync + 2K)  ya  free chain (silent + VO + LatentSync)
└── Nahi ──► 2K/final chahiye? ──► H3 API
            └── draft/plate ──► T4: Wan 1.3B · 24 GB: Wan 2.2 5B ya Hunyuan 1.5

Identity (Monarch face) chahiye?
├── Haan + silent ──► image-to-video (Wan 2.2 I2V / Hunyuan 1.5) + LatentSync
└── Haan + speaking ──► H3 Ref2VA (best) ya LatentSync par free chain
```

## 5. Kya **na** karein (wajah ke saath)

1. **T4 par fp8/NVFP4 model** — hardware support nahi hai, sirf waqt zaya.
2. **Wan 2.2 14B T4 par** — 16 GB me GGUF+offload 480p, magar 20–40 min/clip; free me sirf test ke liye.
3. **Free clip ko final 1080p master banana** — 480p se upscale = soft face, client reject.
4. **Colab free par 24/7 worker** — ToS violation; rented GPU lo.
5. **"Unlimited free H3 credits" wali site** — MiniMax aisa plan nahi deta; woh malware/credential theft hai.
6. **H3 local se 2K ka wada** — Regenerate-2K closed-source hai.

## 6. Total cost picture (jo mujhe poochna tha)

| Deliverable | Free route | Paid route |
|---|---|---|
| 30 s reel (6 × 5 s) | $0 + 4–6 ghante Colab | $2.40 (768P) / $3.90 (2K) |
| 60 s film (12 × 5 s) | $0 + 1–2 din | $4.80 / $7.80 |
| 5 s hero dialogue shot | $0 (silent + VO + LatentSync) | $0.40 / $0.65 |
| 2K native stereo clip | ❌ impossible | $0.65 |

Paid route ka **asli** faida paisa nahi, **waqt** hai: 4 ghante vs 4 minute. Is liye formula:
**explore free, deliver paid, sirf un shots par jo edit me bache.**

## 7. Sources

- H3 facts/pricing: `00_MODEL_FACTS.md`, repo README, platform docs (2026-10-27).
- Free/trial routes: `05_FREE_ROUTES.md`.
- Wan / Hunyuan / LTX / LatentSync numbers: `records/PROVENANCE.json` → `next-level-tools` entry
  (vendor model cards + 2026 comparison write-ups + LatentSync upstream README/community T4 patch report).
- Sab numbers **ranges** hain; community reports. Quote karne se pehle apne GPU par ek test clip chalao.
