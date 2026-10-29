# Quality ladder — 480p se aage kaise jayein

Trigger: `AGENTGO quality` · WF-07 · VIPER-1 `upscale` stage · last verified 2026-10-27

Yeh doc sirf ek sawal ka jawab hai: **"480p kam nahi hai?"** — haan, kam hai. Neeche har rung ka
asli number hai, aur kis rung par kya *nahi* milta.

## 1. Sach (numbers)

| Rung | Output (9:16) | Detail | Audio | Cost | Kahan chalta hai |
|---|---|---|---|---|---|
| Free route (Wan 1.3B) | **480×832** | native model output, soft faces | ❌ silent | **$0** | Colab T4, ~10–25 min/clip |
| + Lanczos ×2 | 960×1664 | sirf edges crisper — **naya detail zero** | ❌ | **$0** | CPU bhi chalta hai |
| + Real-ESRGAN ×2 | 960×1664 | texture saaf, chehre thode behtar — **asli 1080p nahi** | ❌ | **$0** | Colab T4, ~2–4× slow |
| H3 API 768P | 768×1365 | asli render, motion+lighting sahi | ✅ stereo | **$0.08/s** | hosted API |
| H3 API 2K | 1440×2560 | asli high-res, delivery-grade | ✅ stereo | **$0.13/s** | hosted API |

Yani: **free route se 1080p "ban sakta hai" sirf size me** — 960×1664 upar se scale karke 1080×1920.
Wo technically 1080p file hai, magar 1080p *detail* nahi. Isi liye verify/plan dono yeh line print karte hain.

## 2. 480p kab bilkul theek hai

- Reels/Shorts drafts, client review, animatic, timing check
- Background plates (jinpar typography + grade chadti hai, WF-05)
- Face close-up jahan aap khud lipsync (LatentSync) chadha rahe ho — 480p face + 2× upscale phone par theek dikhta hai
- Instagram khud 1080×1920 par compress karta hai; 480p → 960p ka farq thumbnail me dikhta hai,
  full-screen me halka — magar **paid 2K se compare mat karo**, wo jeet jayega

## 3. 480p kab bilkul theek NAHI hai

- Client delivery jahan "1080p master" likha ho
- Text/screens/faces par close-up jahan pores/edges count hote hain
- Native dialogue + lip-sync chahiye (free route silent hai — lipsync alag pass hai)
- TV/landscape se watch karne wala content (9:16 480p bada screen par tootta hai)

## 4. Command flow

```bash
# 1. free clips render (480x832)
python3 tools/videogen.py render <project>.json            # -> queue/free_jobs-*.json

# 2. upscale plan (project.json ka delivery block)
#    "delivery": {"upscale": "realesrgan", "factor": 2, "target_height": 1664}
python3 tools/videogen.py upscale <project>.json                     # T4 notebook
python3 tools/videogen.py upscale <project>.json --engine lanczos    # CPU-only route

# 3. Colab me notebook Run all -> shots/<id>-2x.mp4 wapas Drive me

# 4. verify height bhi check karta hai (target_height se neeche = exit 3)
python3 tools/videogen.py verify <project>.json
python3 tools/videogen.py assemble <project>.json
```

`upscale` ek hi notebook banata hai: `upscale/UPSCALE_<project>_<engine>_x<factor>.ipynb` —
Drive path, per-shot upscale, audio passthrough, aur `upscale_receipt.json` (size + md5).

## 5. Paid shortcut (agar quality hi maqsad ho)

H3 768P: 5 s hero = **$0.40** | 10 s = **$0.80** — audio + lipsync usi pass me.
2K: 5 s = **$0.65** | 10 s = **$1.30**. Sirf 1–2 hero shots paid karo, plates free rakho:
3-shot reel ≈ **$0.40–0.65** total. Yahi budget discipline `plan` + `budget_usd` gate enforce karta hai.

## 6. Rules (verify in code)

1. `plan` free route par target_height vs actual height ka warning deta hai — "scale, not detail".
2. `verify` height < target×0.95 ho to **exit 3** (file deliver nahi).
3. `assemble` target tak scale karta hai magar console par likhta hai: "sharpening, not new detail".
4. Kisi bhi scaled file ko 1080p/4K native ke tor par present karna **banned**.
5. 2K ka wada sirf H3 API route par.
