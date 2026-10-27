# CLOUD PIPELINE — cloud video, agent ke control me (owner ke taps ke bina)

**Rule (AGENTS.md me pinned):** cloud kaam ka trigger **agent** karta hai. Owner ko link, notebook, "Run all"
ya upload nahi dena. Owner sirf result dekhta hai.

## Masla kya tha

Sandbox se cloud tak seedha rasta band hai:

| host | sandbox se |
|---|---|
| `drive.google.com`, `googleapis`, `oauth2` | **000** |
| `huggingface.co`, `kaggle.com`, `colab.research.google.com` | **000** |
| `github.com`, `api.github.com`, `codeload`, `pypi`, `npm` | ✅ khula |

Is liye "aap Colab kholo aur Run all dabao" hi wahid rasta reh gaya tha — aur wohi owner ko tang karta tha.

## Rasta: GitHub Actions ko bridge banao

Runner ke paas **poora internet** hai (HF/Kaggle/Colab) aur 4 core CPU / 16 GB RAM. Sandbox sirf `github.com`
se baat karta hai — aur wahi kaafi hai:

```
agent (sandbox)                    GitHub Actions runner                  wapas
────────────────                   ─────────────────────                  ─────
cloud/jobs/<id>.json  ──push──▶    job pick + render (ffmpeg/torch)  ──▶   cloud-artifacts branch (git)
                                                                              │
git fetch origin cloud-artifacts ◀────────────────────────────────────────────┘
  → mp4 + cloud_receipt.json, md5 verify, project ke delivery/ me
```

Artifact download (`actions/download-artifact`) `objects.githubusercontent.com` se redirect hota hai jo yahan
band hai — is liye result **git branch** par publish hota hai. Git hi hamara transport hai.

## Commands (agent chalata hai, owner nahi)

```bash
# 1) job queue me daalo + push (push hi workflow trigger karta hai)
python3 tools/cloud_reel.py enqueue reel-local-01

# 2) cloud me banne ka intezaar + wapas laao (md5 verify hota hai)
python3 tools/cloud_reel.py fetch reel-local-01 --dest studio/videogen/examples/reel-local-01/delivery_cloud

# 3) status
python3 tools/cloud_reel.py status reel-local-01
```

AI clip (SD1.5 + AnimateDiff, runner ke CPU par — koi GPU account nahi):

```bash
# cloud/ai_jobs/<id>.json edit karo (prompt/frames/steps), phir commit+push
git push origin <branch>          # workflow cloud-ai-clip.yml khud chal jata hai
# result: cloud-ai-artifacts branch me <id>.mp4 + cloud_ai_receipt.json
```

## Proof (2026-10-28)

| kya | result |
|---|---|
| run | `Cloud reel (agent-triggered)` #40597344133 — **success**, ~3 min |
| master | `reel-local-01_MASTER.mp4`, 5 671 468 B, md5 `54120faf48b532de584f7e20c3cd9790` |
| wapas | `cloud_reel.py fetch` ne git se laaya, md5 **match** |
| owner ne kya kiya | **kuch nahi** |

## Limits (sach)

- **GPU yahan nahi hai.** GitHub ke free runners CPU hain. Is liye AI footage chhote model (SD1.5 + AnimateDiff) se
  banti hai — Wan 2.1 jaisi 480p quality ke liye free GPU (Colab/Kaggle) chahiye, aur us ke liye ek dafa account
  key chahiye hoti hai. Jab tak woh nahi hai, **cloud CPU + local renderer** hi rasta hai — aur woh bhi owner ke
  bina chalta hai.
- Runner par job 6 ghante tak chal sakta hai; CPU T2V 10–40 min leta hai (14 frames @ 384×640, 12 steps).
- Cloud ka ffmpeg/x264 version local se different hota hai, is liye same spec ka md5 **thoda** different aata
  hai — duration/resolution/fps match karte hain, byte-identical nahi. Receipt hamesha us file ka hota hai jo
  wapas aayi.
