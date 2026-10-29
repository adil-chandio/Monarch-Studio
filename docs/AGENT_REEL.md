# AGENT REEL — video jo main khud banata hoon (owner ke bina)

**Rule:** video banane ke liye owner se koi click, link, Colab ya upload nahi maangna. Agar sandbox me ban sakti
hai to **yahin banao**. Sirf woh cheez owner ke paas le jao jo yahan *technical taur par* nahi ban sakti.

## Kyun yeh rasta

Sandbox me **GPU nahi hai, HuggingFace/Google tak network nahi hai** — is liye Wan/MMAudio jaisa diffusion model
yahan nahi chalega. Lekin:

- Monarch ke paas pehle se **asli art plates** hain (`styles/monarch-noir-film/plates/`, 10 plates, 1376×768).
- 2 CPU cores par ffmpeg se **1080×1920, 17 second ki reel ~50–70 second me** ban jati hai.

Yani "video" ke liye GPU ki zarurat sirf naye AI footage ke liye hai — camera moves, grading, captions, sound
design aur editing ke liye nahi. Woh sab yahan hota hai.

## Istemal

```bash
python3 tools/reel_render.py studio/videogen/examples/reel-local-01/reel.json \
        --out studio/videogen/examples/reel-local-01/delivery/reel-local-01_MASTER.mp4
```

`make reel` bhi yahi karta hai. Output ke saath `<name>_receipt.json` banti hai (md5, bytes, w×h, duration,
per-shot log, render seconds) — receipt sirf us file ki hoti hai jo wahan maujood hai.

## Spec (reel.json)

| field | matlab |
|---|---|
| `size` | `[1080, 1920]` vertical (ya `[1080,1080]` square) |
| `fps` | 24 default |
| `plate_height` | plate band ki height (720 = 16:9 art vertical frame me) |
| `grain` | film grain (7 halka, 12 zyada) |
| `crf` | 22 delivery / 18 master quality |
| `shots[]` | `image`, `seconds`, `move` (`push` `pull` `pan_left` `pan_right` `still`), `caption` |
| `audio` | `drone`, `rain`, `pulse`, `impacts`, `riser`, `voice` (wav path) |

Har shot me: peeche usi plate ka blurred bed, aage **zoompan camera move** (yahi asli motion hai — freeze frame
nahi), grain, vignette, grade; phir caption PIL se PNG bana kar fade ke saath overlay hoti hai (kyunki har ffmpeg
build me `drawtext` nahi hota). Shots `xfade` dissolve se judte hain. Audio: drone + barish + pulse + cut par
impact + riser, sab ffmpeg lavfi se, aakhir me `loudnorm I=-16`.

## Quality levers (jab owner "zyada acha" kahe)

1. **Motion**: `push` 12% zoom par rukta hai — 0.12 ko badhao (max ~0.18, warna blur).
2. **Depth**: plate ke aage ek foreground element (smoke PNG, `noise` + `blend`) daal kar parallax banaya ja sakta hai.
3. **Sound**: `voice` me wav do (Kokoro/recorded) — baaki bed khud adjust ho jata hai.
4. **Length**: 6 shots × 3.2 s = ~17 s; Reels ke liye 15–20 s theek hai.

## Honest limits

- Yeh **AI-generated footage nahi** hai — yeh aap ke asli art par cinematic motion/sound design hai. Jab naya
  AI shot chahiye (Wan), tab free GPU ka raasta Colab hai; woh **ek hi tap** hai aur sirf tab jab aap khud naya
  footage maangein. Baaki har cheez (edit, mix, master, receipt) main yahan karta hoon.
- 2 cores par ek reel ~1 minute; 60-second film ~4–6 minute. Session time se pehle plan karo.
