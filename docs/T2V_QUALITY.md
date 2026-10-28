# T2V quality lab — kya cheez kitni achi hai (measured, 2026-10)

Sab numbers asli runs se hain (GitHub Actions, `ubuntu-latest`, 4 vCPU, 16 GB RAM, koi GPU nahi).
Har clip 1080x1920 delivery look me finish hoti hai; yahan "raw" = model ka apna output.

| backend | model | settings | waqt | result |
|---|---|---|---|---|
| animatediff | `Lykon/dreamshaper-8` + motion-adapter v1-5-2 | 384x672, 16 f, 10 steps | **32 min** | motion asli hai, magar look 2023 wala: plastic skin, soft detail |
| animatediff | `guoyww/animatediff-motion-adapter-v1-5-2` | 432x768, 24 f, 12 steps | >60 min (timeout) | CPU par practically na-qabil |
| ltx | `Lightricks/LTX-Video` (2B) | 480x832, 97 f, 20 steps | **35 min** | dark mush — is settings par unusable |
| wan | `Wan-AI/Wan2.1-T2V-1.3B-Diffusers` | 480x832, 33 f, 15 steps | **4 h+ (CPU)** | 2025 ka model, magar CPU par waqt khatam |
| wan (GPU) | wahi model, T4 fp16, 28 steps | 480x832, 49 f | ~6-10 min/scene (est.) | **yehi asli raasta hai** — `notebooks/Wan_T2V_Colab.ipynb` |

## Sabak

1. **GPU ke bagair 2026-level realism nahi milta.** CPU par 2025 ke models chal jate hain
   magar 4+ ghante per clip — 12 scenes = 2 din. Yeh hardware ki deewar hai, code ki galti nahi.
2. **"Slides + camera move" kabhi mat karo.** Owner ne do baar reject kiya. Har frame model se aaye.
3. **minterpolate mat lagao.** 8 fps clip ko 24 fps banane se chehra smear hota hai; native fps
   rakho aur 16/24 fps par hi deliver karo.
4. **LTX 2B CPU par dark mush deta hai** — is config me dobara mat try karna.
5. **AnimateDiff sirf fallback hai** (jab kuch bhi na chale), final quality ke liye nahi.

## Publish/failure ka tareeqa (jo finally chala)

- Clip ban kar `t2v_out/<job>_<scene>/` me aata hai.
- Publish step **fresh repo** banata hai `/tmp/pub` me, `git init` + commit + `git push --force`
  token-URL par, 3 retries + `http.postBuffer` 500 MB.
- Har clip ke saath `receipt.json` (bytes, md5, ffmpeg probe) jata hai; agent `cloud_t2v_fetch.py`
  se md5 verify karke fetch karta hai.
- Failure par poora `gen.log` + `publish.log` + mem/disk `t2verr-<job>-<scene>` branch par.
- **Trap:** `ffmpeg -i` akela exit code 1 deta hai. `set -euo pipefail` ke saath yeh step fail
  kar deta hai aur publish skip ho jata hai — is liye `|| true` lazmi hai.
