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
