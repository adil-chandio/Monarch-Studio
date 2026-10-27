# WF-07 · Monarch AI Agent

**Trigger:** `AGENTGO <job or topic>` · **Code:** WF-07 · **State:** ACTIVE (user-created Drive home, 2026-10-27)

Yeh woh jagah hai jahan studio ka **saara AI-generated kaam** rehta hai: project files, clips, masters, receipts.
Generate karne wala engine studio ka apna hai — [`tools/videogen.py`](../../tools/videogen.py) (VIPER-1).

> **Drive home:** [Wf-07 • Monarch Ai Agent](https://drive.google.com/drive/folders/1IBgfHFdigeDzaYkJuNoelhLiWLqRZ6d1)
> (id `1IBgfHFdigeDzaYkJuNoelhLiWLqRZ6d1`, inside `MONARCH STUDIO`) — IDs: [`data/drive.json`](data/drive.json)

## 0. FREE-ONLY MODE (default)

`viper-1.3` **kharch nahi kar sakta** jab tak koi jaan-boojh kar `MONARCH_ALLOW_PAID=1` na likhe:

- `plan` header: `FREE-ONLY ($0 guaranteed)`; `route: paid` likha ho to bhi har paid step free chain me rewrite
- `render --yes` → `FREE-ONLY MODE: no paid step will be submitted` (H3 client call hi nahi hota)
- free GPU ka hisaab: `python3 tools/videogen.py quota` (Kaggle 30 h/week counter, weekly auto-reset)

Free compute ka poora structure + weekly rhythm + quota-khatam plan:
[`docs/FREE_ONLY_PLAYBOOK.md`](../../docs/FREE_ONLY_PLAYBOOK.md) · menu: [`studio/free_compute.json`](../../studio/free_compute.json)

## 1. "Yeh sab free hai?" — seedha jawab

| Cheez | Free? | Detail |
|---|---|---|
| **VIPER-1 tool** (`tools/videogen.py`, docs) | ✅ **free** | studio ka apna code, repo me, koi subscription nahi |
| **Free route** — Colab T4 · Wan 2.1 1.3B · LatentSync lipsync · local ffmpeg | ✅ **$0** | 480×832, silent base (voice aap ki), 10–25 min/clip |
| **Free upscale** — Real-ESRGAN ×2 (T4) ya Lanczos ×2 (CPU) | ✅ **$0** | 480×832 → **960×1664**, sharper magar naya detail nahi |
| **Free audio** — Kokoro/Chatterbox voice + MMAudio/ThinkSound foley + MusicGen bed | ✅ **$0** | MMAudio & MusicGen weights **non-commercial**; Kokoro/Chatterbox commercial OK |
| **Free compute** — Colab free T4 + **Kaggle 30 h/week** + Lightning credits + laptop CPU | ✅ **$0** | koi card nahi; Colab quota dynamic, Kaggle counter visible |
| **Drive storage** | ✅ free 15 GB | 1080p masters bhaari hote hain; purane runs archive karo |
| **MiniMax-H3 API** (2K, native stereo, ek pass me dialogue+lipsync) | ❌ **paid — LOCKED by default** | $0.08/s @768P · $0.13/s @2K; sirf `MONARCH_ALLOW_PAID=1` ke baad |
| **H3 local weights** | ✅ weights free | magar 4×H100 class GPU — Colab par nahi |

Toh: **tool free hai, free route $0 hai, sirf hero shots (2K + native audio) ka paisa lagta hai.**
Aur paisa bhi tab lagta hai jab aap khud `render --yes` chalao — estimate dekhne ke baad. Isi liye default route
`auto` hai: API key na ho to har shot free chain par chala jata hai.

## 2. Folder map (Drive)

| Drive folder | Kya rakha jata hai |
|---|---|
| `01 · START HERE` | yeh guide + engine manual (Google Doc copy) |
| `02 · Engine (VIPER-1)` | `videogen.py` + `VIDEOGEN.md` |
| `03 · Colab Notebooks` | free T4 notebook + H3 API notebook |
| `04 · Knowledge` | model facts, prompting, free routes, toolbox, tool registry |
| `05 · Projects` | per project: `project.json`, `plan.json`, `receipts.json`, `shots/` |
| `06 · Masters & Receipts` | final masters (md5 receipts ke saath) |

Git source of truth hai; Drive delivery + sharing ki jagah hai. Dono ke ids `data/drive.json` me.

### Abhi Drive me kya rakha hai (17 files, 6 folders)

| Folder | Files |
|---|---|
| `01 · START HERE` | START HERE guide (Google Doc) |
| `02 · Engine (VIPER-1)` | `videogen.py` (v1.3), `VIDEOGEN` manual (Doc) |
| `03 · Colab Notebooks` | `MONARCH_T4_FREE_BRIDGE.ipynb` (free), `MONARCH_H3_COLAB.ipynb` (paid) |
| `04 · Knowledge` | 00 facts · 01 runbook · 02 prompting · 05 free routes · 06 toolbox · **QUALITY ladder** · **AUDIO research** · **FREE-ONLY PLAYBOOK** (Docs) + `tool_registry.json` · `free_compute.json` |
| `05 · Projects` | `monarch-reel-01.project.json`, `free_jobs.example.json` |
| `06 · Masters & Receipts` | (khaali — pehla master yahan aayega) |

Har file ka Drive id: [`data/drive.json`](data/drive.json) → `uploaded`.

## 2b. "480p kam nahi?" — short answer

480×832 free route ka asli output hai. `upscale` stage usko **960×1664** kar deta hai ($0):
Real-ESRGAN T4 par texture saaf karta hai, Lanczos sirf edges — **dono me naya detail nahi aata**.
Asli 1080p/2K + native dialogue chahiye to H3 API (paid). Poora ladder: [`knowledge/QUALITY.md`](knowledge/QUALITY.md).

```bash
python3 tools/videogen.py upscale <project>.json                  # T4 notebook (realesrgan x2)
python3 tools/videogen.py upscale <project>.json --engine lanczos # CPU-only, ffmpeg
# project.json: "delivery": {"upscale": "realesrgan", "factor": 2, "target_height": 1664}
```

`verify` height bhi enforce karta hai: target se neeche = **exit 3**.

## 2c. Audio — free me kaise

| Layer | Free engine | Licence | Hardware |
|---|---|---|---|
| Voice | **Kokoro-82M** / **Chatterbox** (clone) | Apache-2.0 / MIT | CPU / ~5 GB GPU |
| Foley + ambience | **MMAudio** / **ThinkSound** | MIT+CC-BY-NC / Apache | ~6–8 GB GPU |
| Music bed | **MusicGen-small** | MIT + CC-BY-NC | ~4 GB GPU |
| Lip-sync | **LatentSync 1.5** | Apache + OpenRAIL++ | 8 GB GPU |

```bash
python3 tools/videogen.py audio <project>.json   # Colab notebook: vo + foley + bed
python3 tools/videogen.py mix   <project>.json   # vo+foley amix, bed ducked (sidechaincompress)
python3 tools/videogen.py mix   <project>.json --loudnorm   # -16 LUFS for social
```

Ek hi pass me synced dialogue (Veo-3 jaisa) free T4 par **nahi** aata — uske liye **Ovi** (24 GB fp8)
ya paid H3. Poora research + licences: [`knowledge/AUDIO.md`](knowledge/AUDIO.md).

## 3. Ek project ka poora cycle

```bash
python3 tools/videogen.py doctor
python3 tools/videogen.py new --id monarch-reel-01 --title "Monarch reel 01" --aspect 9:16
# prompts + references + voice_ref bharo, budget_usd set karo
python3 tools/videogen.py plan    workflows/current/payload/monarch-reel-01/project.json
python3 tools/videogen.py render  workflows/current/payload/monarch-reel-01/project.json        # dry
python3 tools/videogen.py render  workflows/current/payload/monarch-reel-01/project.json --yes  # paid only
python3 tools/videogen.py verify  workflows/current/payload/monarch-reel-01/project.json        # exit 3 = no
python3 tools/videogen.py assemble workflows/current/payload/monarch-reel-01/project.json
```

Free shots ke liye `render` ek `queue/free_jobs-*.json` deta hai → usse Colab notebook me chalao → mp4 wapas
`shots/` me (same id). Hero shot ke liye `lipsync/<id>.sh` banta hai (video + aap ki awaaz → talking clip).

## 4. Rules (baked in, not advice)

1. **Estimate pehle, paisa baad me.** `plan` 1.5× retry buffer ke saath total deta hai; `budget_usd` hard gate hai.
2. **`verify` hi delivery hai.** File + md5 + ffprobe (duration/fps/audio) pass ho, tab hi master banta hai.
3. **Free = draft, paid = hero.** 480p silent clip ko final 1080p master ke tor par present na karo.
4. **2K ka wada sirf API route par.** Local/free se 2K mumkin nahi.
5. **Har clip ka receipt** (`task_id`, billed seconds, md5) project folder me — Drive me bhi.
6. **Identity `characters/monarch` se** — reference pack same rahe, prompt badle.
7. **Finish WF-05 me** — typography, transitions, score, 24→30 fps conform.

## 5. Kahan kya likha hai

| Path | Kya |
|---|---|
| [`data/drive.json`](data/drive.json) | Drive root + subfolder ids + convention |
| [`knowledge/INDEX.md`](knowledge/INDEX.md) | knowledge map + standing decisions |
| [`../../docs/VIDEOGEN.md`](../../docs/VIDEOGEN.md) | VIPER-1 manual (schema, engines, exit codes) |
| [`../../styles/minimax-h3-video/`](../../styles/minimax-h3-video/) | engine knowledge (WF-06): facts, Colab, prompts, free routes, toolbox |
| [`../../studio/videogen/examples/monarch-reel-01.project.json`](../../studio/videogen/examples/monarch-reel-01.project.json) | ready example project |

## 6. Open items

- ⏳ Pehla asli project: Monarch reference crops + ek voice line chahiye.
- ⏳ Drive me project folders tab banenge jab pehla `plan/verify` chale (naming: `<project-id>/`).
- ⏳ Google Docs HUB / Notion / Linear ids is workflow ke liye abhi nahi bane (registry me `null`).
