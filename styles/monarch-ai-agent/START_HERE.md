# START HERE · Wf-07 • Monarch Ai Agent

Yeh folder studio ka saara **AI-generated video** kaam rakhta hai. Generate karne wala engine hamara apna hai:
**VIPER-1** (`tools/videogen.py`), aur uske peeche ka knowledge **WF-06** (`styles/minimax-h3-video/`) me hai.

## 1. Free hai ya nahi?

| Cheez | Free? | Note |
|---|---|---|
| VIPER-1 tool | ✅ free | repo me, koi subscription nahi |
| Free route: Colab T4 + Wan 2.1 1.3B + LatentSync + ffmpeg | ✅ **$0** | 480p silent base, 10–25 min/clip |
| MiniMax-H3 API (2K, native stereo, dialogue one pass) | ❌ paid | $0.08/s @768P · $0.13/s @2K |
| Drive (yeh folder) | ✅ free 15 GB | masters bhaari hote hain — purane runs archive karo |

**Matlab:** tool free, draft/plates free, sirf hero shots ka paisa — aur woh bhi sirf jab aap khud
`render --yes` chalao, estimate dekhne ke baad. API key na ho to har shot free chain par chalta hai.

## 2. Folder map

| Folder | Kya |
|---|---|
| `01 · START HERE` | yeh guide |
| `02 · Engine (VIPER-1)` | `videogen.py` + `VIDEOGEN.md` manual |
| `03 · Colab Notebooks` | free T4 notebook + H3 API notebook |
| `04 · Knowledge` | model facts, prompting, free routes, toolbox, tool registry |
| `05 · Projects` | per project: `project.json`, `plan.json`, `receipts.json`, `shots/` |
| `06 · Masters & Receipts` | final masters + md5 receipts |

## 3. Ek click flow (free)

1. Colab → `03 · Colab Notebooks/MONARCH_T4_FREE_BRIDGE.ipynb` upload karo
2. Runtime → **T4 GPU** → cells 1–7 Run
3. Clips Drive me `05 · Projects/<project>/shots/` me aa jayenge
4. Lipsync: `lipsync/<shot>.sh` (LatentSync 1.5 + T4 fp16 patch) — apni awaaz ke saath

## 4. Command flow (repo)

```bash
python3 tools/videogen.py doctor
python3 tools/videogen.py new --id <project-id> --title "<title>" --aspect 9:16
python3 tools/videogen.py plan   <project>/project.json
python3 tools/videogen.py render <project>/project.json          # dry run — $0
python3 tools/videogen.py render <project>/project.json --yes    # paid only
python3 tools/videogen.py verify <project>/project.json          # exit 3 = deliver nahi hua
python3 tools/videogen.py assemble <project>/project.json
```

## 5. Rules

1. Estimate pehle, paisa baad me (`budget_usd` hard gate, 1.5× retries).
2. `verify` pass hone se pehle koi delivery claim nahi.
3. Free = draft/animatic; paid = hero 2K.
4. 2K sirf API route se.
5. Har master ke saath md5 receipt.
6. Finish (typography/music/conform) WF-05 me.

_Full detail: repo `styles/monarch-ai-agent/README.md` + `docs/VIDEOGEN.md`._
