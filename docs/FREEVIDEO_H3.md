# FreeVideo (MiniMax H3, local) — hamare liye kya hai

Source: https://github.com/FlashML-org/FreeVideo (checked 2026-10-29)
Model: MiniMax H3 ka 8-step distilled version (`OpenVDN/vdn-minimax-h3`, VDN-H3).

## Ek line ka faisla

**Yeh asli upgrade hai** — wohi model jo WF-04 me tha (MiniMax H3), free, bina API key.
Magar ise chalane ke liye **NVIDIA GPU chahiye jo T4 se naya ho**, aur phone par mumkin nahi.

## Kya chahiye (official docs se)

| Cheez | Requirement |
|---|---|
| OS | x86_64 Linux (ya Windows / macOS launcher) |
| GPU driver | **580 ya naya** |
| VRAM | 8 GB se shuru, 16 GB aaram se |
| RAM | 16 GB minimum, 32 GB behtar |
| Compute path | **int8** = Ampere / GeForce Ada / Blackwell · **FP8** = SM89 (Ada), SM90 (Hopper), SM120 (Blackwell) |

**Colab ka free T4 = SM75 (Turing)** — na int8, na FP8. Is liye T4 par FreeVideo ka fast path
nahi chalta; isi liye hum abhi Wan 2.2 TI2V-5B (diffusers) par hain, jo T4 par chalta hai.

## Free GPU jo kaam karega

- **Lightning AI Studio, free tier**: L4 (24 GB, Ada = SM89) ya A10G (24 GB, Ampere = int8).
  ~22 GPU-hours/month, **card nahi**, sirf phone verification. Persistent disk (models dobara
  download nahi hote).
- Kaggle/Colab ke free GPUs (T4, P100) is kaam ke nahi — wahi SM75/SM60 masla.

## Agent ke liye interface (important)

FreeVideo me ComfyUI ke baghair bhi generation hai — yani script se chalti hai:

```bash
git clone https://github.com/FlashML-org/FreeVideo.git && cd FreeVideo
./setup.sh                                            # runtime + models + checks
./freevideo plan --vram-gib 24 --ram-gib 64 --width 768 --height 1344 --seconds 5
./freevideo generate --prompt-file prompt.txt --out scene.mp4
```

Har output ke sath `<out>.request.json` aata hai (measured hardware, plan, timings) — receipt ki
tarah kaam aata hai.

## Hamari film ke liye plan (jab Ampere+ GPU mile)

1. 12 scenes ki jagah **6 clips × ~6 s** (MiniMax H3 lambay shots behtar karta hai), ya wohi 12 × 3 s.
2. Stickman i2v: keyframes already ready (`studio/films/stick-i2v/keyframes/`), H3 first-frame
   conditioning leta hai.
3. Voice: same `voice/v01..v10.wav`; assembly: `tools/clip_film.py` (bilkul wohi).

## Kya nahi karna

- T4/Colab par FreeVideo try karke waqt zaya karna.
- Owner ko CLI chalwane ke liye kehna — script agent chalata hai.

## Kaam kaise hoga (owner ke 2 tap + 1 paste)

1. **Lightning AI** → free account (phone verify, card nahi) → **New Studio → L4 GPU**.
2. Studio ka **Terminal** kholo aur ek line paste:

```bash
curl -fsSL https://raw.githubusercontent.com/adil-chandio/Monarch-Studio/arena/3d8cfad7-monarch-studio/scripts/freevideo_start.sh | bash
```

3. Bas. Woh script khud: GPU/driver/disk check → FreeVideo install + models → 12 stickman
   keyframes download → har scene ko animate (image → video) → receipts. ~45-70 min.

Agent ka kaam: clips aane ke baad `tools/freevideo_fetch.py` se uthana (agar `GITHUB_TOKEN`
diya ho to script khud branches `fv-stick-h3-<scene>` par bhej deta hai), `tools/clip_film.py`
se captions + voice + sound ke sath 1080x1920 master, Drive par public upload.

### Files
- `tools/freevideo_run.py` — renderer (preflight + resume + receipts + optional branch publish)
- `tools/freevideo_fetch.py` — branches se clips wapas
- `scripts/freevideo_start.sh` — ek-line bootstrap (owner ke liye)
- `cloud/freevideo_jobs/stick-h3.json` — 12 scenes, 768x1344, 3s each = 36s

### Bonus
MiniMax H3 **audio bhi generate karta hai** (`i2va` task) — yani ambience/SFX free milta hai;
hamari voice (`voice/v01..v10.wav`) uske oopar mix hoti hai.

## Lightning AI band (PK) — naya raasta: Modal

Lightning ne Pakistan me service nahi khuli ("hasn't expanded to your area"), is liye:

| Platform | Free GPU | Card? | PK? | Verdict |
|---|---|---|---|---|
| Lightning AI | L4/A10G | nahi | **band** | out |
| **Modal** | **L4 / A10G (24 GB)** | **nahi** ($30/month credits) | haan | **yehi** |
| Beam | A10G (10 h) | nahi | haan | backup |
| Colab | T4 (SM75) | nahi | haan | Wan 2.2 chalta hai, H3/FastVideo nahi |

Modal par $30/month ≈ **37 GPU-hours L4** — poore 12 scenes ke liye kaafi.

Files:
- `tools/modal_monarch.py` — Modal app (`render_scene`, `files` web endpoint, `smoke`, `film`).
- `notebooks/modal_cell_smoke.py` — Modal **Notebook** ke liye ek cell (browser, koi CLI nahi).
