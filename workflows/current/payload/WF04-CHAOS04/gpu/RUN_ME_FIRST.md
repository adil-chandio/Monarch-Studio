# GPU ka rasta — aap ke 3 click, phir mera kaam

## Ab (bas yeh karein)

1. Drive → `Chaos video 2` → **`CHAOS_GPU_COLAB.ipynb`** par right click →
   **Open with → Google Colaboratory**
2. `Runtime` → **Change runtime type** → Accelerator = **GPU** → Save
3. `Runtime` → **Run all** (pehla cell ~15 s mein chal jayega)
4. Jo **`PASTE-BACK REPORT`** print hoga — poora copy kar ke chat mein bhej dein.

Bas. Us report se mujhe pata chal jayega: kaunsa GPU mila, kitni VRAM, kaunsa model
chal sakta hai. Us ke baad main jobs/prompts likh dunga aur aap ko sirf **Run all**
dabana hoga.

## Ek baat jo saaf samajh lein (technical limit)

Main aap ke Colab machine ke andar **nahi** ghus sakta — mera internet sirf
github/pypi/Drive tak khula hai. Is liye:

- **GPU ka kaam** aap ke Colab par hoga (notebook sab kuch khud karta hai)
- **Mera kaam** hoga: shot plan, prompts, jobs file, phir clips Drive se uthana,
  edit, grade, audio, QC, delivery

Isi liye notebook ka design yeh hai: **resume + sha256 manifest + Drive upload** —
ek run fail ho jaye to dobara Run all, jahan se ruka tha wahan se aage barhega.

## Free T4 vs paid (seedhi baat, pehle hi)

| GPU | clip quality |
|---|---|
| Free **T4** 16 GB | 480–768p, 2–4 s clips — test/preview ke liye |
| **L4 / 4090** 24 GB | 720p cinematic — asli kaam |
| **A100** 40 GB | character performance (Wan-Animate-14B) — sab se qareeb |

Free T4 par "exactly same photoreal 1080p" nahi aayega. Agar woh chahiye to
24 GB+ chahiye (Colab Pro ya rented 4090 — approx $1–6 poori film).
Yeh number main pehle hi bata raha hoon, baad mein surprise na ho.
