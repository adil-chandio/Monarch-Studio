# MOBILE MODE · phone se poora studio

Owner mobile par hai. Yeh doc batata hai **kaun kya karega** — taake aapko terminal, ffmpeg ya
file management ki zarurat kabhi na pade.

## 1. Kaam ka batwara (yaad rakhne wali ek table)

| Kaam | Kaun | Aap ko kya karna hai |
|---|---|---|
| project banana, prompts likhna, plan/pricing | **main (agent)** | bas topic/line bolo |
| Drive folder structure, receipts | **main** | kuch nahi |
| clips + voice + foley + upscale (GPU) | **Colab notebook** | **Run all** dabana |
| mix (voice+foley+music ducking) | **main** | kuch nahi |
| verify (height/audio/md5) + master assemble | **main** | kuch nahi |
| Drive me archive | **main** | link dekhna |

Aap ke paas sirf **ek notebook** hai. Usme 3 stage hain, sab ek hi **Run all** me.

## 2. Aap ka 3-tap flow

1. Chat me bolo: `reel banao <topic>` (ya `reel-01 shuru karo`)
2. Main notebook bana kar Drive me daal dunga + **Colab ka direct link** dunga
3. Phone par link kholo → **Runtime ▸ Change runtime type ▸ T4 GPU** → **Runtime ▸ Run all**
4. 20–40 min baad aakhri cell me `DONE ✅` aayega → chat me `DONE` likho
5. Main mix + verify + master bana kar Drive `06 · Masters & Receipts` me daal dunga

**Aap ko kabhi nahi karna:** pip install, ffmpeg, terminal, file rename, ZIP, md5.

## 3. Notebook ke andar kya hai (ek hi file)

| Cell | Kaam | Band kar sakte hain |
|---|---|---|
| 1 | Drive mount + project paths + jobs | nahi |
| 2 | Wan 2.1 1.3B load (fp16 + offload) | `RUN_CLIPS = False` |
| 3 | clips → `shots/<id>.mp4` | `RUN_CLIPS = False` |
| 4 | Kokoro voice → `audio/vo/<id>.wav` | `RUN_VOICE = False` |
| 5 | MMAudio foley → `audio/foley/<id>.wav` | `RUN_FOLEY = False` |
| 6 | Real-ESRGAN ×2 → `shots/<id>-2x.mp4` | `RUN_UPSCALE = False` |
| 7 | summary + `colab_receipt.json` + `DONE ✅` | nahi |

Toggles cell 1 ke top par hain. Pehli baar sirf clips chahiye? `RUN_VOICE/RUN_FOLEY/RUN_UPSCALE = False`
kar do — 10 min me pehla clip.

## 4. Main yahan se kya chala raha hoon (aap ke liye invisible)

```bash
python3 tools/videogen.py mobile <project>.json      # notebook + jobs (prompts baked in)
python3 tools/videogen.py plan   <project>.json      # $0.00 estimate
# ... aap Run all karte ho ...
python3 tools/videogen.py mix      <project>.json --loudnorm
python3 tools/videogen.py verify   <project>.json    # height + audio + md5
python3 tools/videogen.py assemble <project>.json
python3 tools/videogen.py quota --use kaggle <hours>
```

Is sandbox me ffmpeg **static binary** (imageio-ffmpeg) se aata hai, aur ffprobe na ho to
`ffmpeg -i` parse karke width/height/fps/duration nikale jate hain — matlab mix/verify/assemble
**yahan** ho jate hain, aap ke phone par kuch bhaari nahi chalta.

## 5. Agar mobile par kuch atak jaye

| Dikh raha hai | Matlab | Aap kya karo |
|---|---|---|
| `Runtime disconnected` | Colab ne session band kiya | dobara Run all (jo files bani hain skip ho jayengi) |
| `CUDA out of memory` | T4 16 GB bhar gaya | mujhe bolo — main frames/resolution kam kar ke notebook dobara dunga |
| `DONE` nahi aaya, `ADHURA ⚠️` | koi clip missing | mujhe bolo, main missing job chhota kar dunga |
| Drive me file nahi dikh rahi | path/galt folder | mujhe bolo — main `list_files` se check karunga |
| Kaggle use karna hai | Colab quota khatam | `File ▸ Upload notebook` → Kaggle me T4×2 → wahi Run all |

## 6. Mobile-friendly rules (mere liye)

1. Aap se **koi command** nahi maangunga — har CLI main chalata hoon.
2. Har notebook me **prompts baked-in** hote hain; aap ko JSON edit nahi karna.
3. Links seedhe **Colab** ke denge (`colab.research.google.com/drive/<file-id>`), Drive folder links nahi.
4. Ek notebook = ek Run all. Teen alag notebooks nahi bhejunga jab tak aap na kahen.
5. Har message ke aakhir me **ek hi agla step** likhunga (mobile par lambi list confusing hoti hai).

## 7. Ek reel ka waqt (T4, 3 shots)

| Stage | Waqt |
|---|---|
| clips ×3 | 25–40 min |
| voice (Kokoro, CPU) | < 1 min |
| foley ×3 (MMAudio small) | 5–10 min |
| upscale ×2 ×3 | 10–20 min |
| **total (Run all)** | **~45–70 min** |
| mix + verify + master (main) | 2–3 min |
