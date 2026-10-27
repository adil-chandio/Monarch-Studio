# Audio · free voice + foley + music (aur asli quality ka raasta)

Trigger: `AGENTGO audio` · WF-07 · VIPER-1 `audio` + `mix` · researched 2026-10-27

Sawaal tha: **"audio bhi chahiye aur quality bhi — sab free me."** Neeche woh stack hai jo aaj
free T4 / CPU par chalta hai, kya licence ke saath, aur kahan free khatam ho jata hai.

## 1. Verdict pehle

| Chahiye | Free T4 / CPU par? | Kaise |
|---|---|---|
| **Voice (VO / narration)** | ✅ haan | **Kokoro-82M** (Apache-2.0, CPU, 54 voices) ya **Chatterbox** (MIT, 5–10 s clone, ~5 GB GPU) |
| **Foley / SFX (video ke saath sync)** | ✅ haan | **MMAudio** (~6 GB, video→audio) ya **ThinkSound** 533M/724M/1.3B (Apache code) |
| **Music bed** | ✅ haan | **MusicGen-small** (~4 GB) — weights CC-BY-NC |
| **Lip-sync (voice ↔ face)** | ✅ haan | **LatentSync 1.5** (8 GB, pehle se wired) |
| **Ek hi pass me synced dialogue + video (Veo-3 jaisa)** | ❌ **nahi** | **Ovi** (Apache-2.0, 11B) ko 24 GB (fp8) / 32 GB (bf16) chahiye; **Kandinsky 6.0 Video Lite** (MIT) ~21.7 GiB |

Yani free me audio **milta hai — stems ke roop me** (voice + foley + bed + lipsync), jo asal me pro
workflow bhi hai. "Ek prompt → video + awaaz" wala Veo-style output free T4 par nahi aata; uska
sasta raasta niche §5 hai.

## 2. Jo repos actually kaam ke hain (verified numbers)

| Model | Kaam | Size | VRAM | Licence | Note |
|---|---|---|---|---|---|
| [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) | text→voice | 82M | **0 (CPU)** | **Apache-2.0** (commercial OK) | 54 preset voices, cloning nahi, ~1.5–5× real time |
| [Chatterbox](https://github.com/resemble-ai/chatterbox) | text→voice + clone | ~0.5B | ~5 GB | **MIT** | 10 s reference se cloning; Monarch ki apni awaaz |
| [MMAudio](https://github.com/hkchengrex/MMAudio) | video→audio | 157M–1.03B | **~6 GB (fp16)** | code MIT / **weights CC-BY-NC 4.0** | 44.1 kHz, ~1.2 s per 8 s clip, T4 par tested |
| [ThinkSound](https://github.com/FunAudioLLM/ThinkSound) | video→audio (CoT) | 533M/724M/1.3B | ~8 GB | Apache-2.0 code (commercial ke liye author se poochho) | V2A benchmarks me MMAudio se aage |
| [FoleyCrafter](https://github.com/open-mmlab/FoleyCrafter) | video+text→audio | 1.2B | ~8 GB | Apache-2.0 | purana magar stable |
| [MusicGen](https://github.com/facebookresearch/audiocraft) | text→music | 300M–1.5B | ~4 GB | code MIT / **weights CC-BY-NC** | small model T4 par 30 s bed |
| [Ovi](https://github.com/character-ai/Ovi) | video **+** audio ek saath | 11B (5B+5B+1B) | **32 GB** (24 GB fp8) | **Apache-2.0** | 720×720/960×960, 24 fps, 16 kHz audio, synced speech + SFX + music |
| [Kandinsky 6.0 Video Lite](https://github.com/kandinskylab/kandinsky-6.0) | video + 44 kHz audio | audio 0.6B | ~21.7 GiB | **MIT** | commercial-friendly alternative to Ovi |
| [LatentSync](https://github.com/bytedance/LatentSync) | lipsync | 1.5 | 8 GB | Apache-2.0 code / OpenRAIL++ weights | T4 fp16 patch chahiye (pehle se wired) |

**Licence line jo main har baar repeat karunga:** MMAudio aur MusicGen ke **weights non-commercial**
hain. Personal/portfolio reel = theek. Paid client kaam = `thinksound` (foley) chuno, music ke liye
licensed track ya paid library, warna licence violation hai. Code MIT/Apache hona weights ko
commercial nahi banata.

## 3. Free audio pipeline (jo ab engine me hai)

```bash
python3 tools/videogen.py audio <project>.json     # Colab notebook: voice + foley + bed
# Colab: T4 GPU -> Run all -> audio/vo/*.wav, audio/foley/*.wav, audio/bed.wav in Drive
python3 tools/videogen.py mix   <project>.json     # ffmpeg: dialogue + foley + ducked bed
python3 tools/videogen.py verify <project>.json    # stems hain to audio stream bhi check hota hai
python3 tools/videogen.py assemble <project>.json
```

`mix` ka graph (har shot): `vo + foley → amix`, `bed → volume -6 dB`, phir
`sidechaincompress(threshold 0.03, ratio 8)` se bed dialogue ke neeche duck hota hai, uske baad
`amix(dia, bed_duck) → aac 192k`. `--loudnorm` se `-16 LUFS / TP -1.5` (social platforms ka target).

Project file me:

```json
"audio": {
  "vo_engine": "kokoro",        // kokoro | chatterbox | own | off
  "foley_engine": "mmaudio",    // mmaudio | thinksound | off
  "bed_engine": "musicgen",     // musicgen | off
  "bed_prompt": "dark cinematic pulse, low strings",
  "bed_gain_db": -6,
  "mix": true
},
"shots": [{ "id": "s01-hook", "vo_text": "Main Monarch hoon…",
            "foley_prompt": "cloth rustle, distant room tone" }]
```

## 4. Quality + audio ek saath — free me kya realistic hai

1. **Video:** Wan 2.1 1.3B 480×832 (free, reliable) → **Real-ESRGAN ×2 → 960×1664** (free). ~₹0.
2. **Voice:** Kokoro (free, no clone) — ya Chatterbox clone (~5 GB GPU, MIT) aapki awaaz ke saath.
3. **Foley:** MMAudio small_44k (T4) — clip ke saath sync ho kar ambience/SFX.
4. **Music:** MusicGen-small bed, `mix` me ducked.
5. **Lipsync:** LatentSync 1.5 hero shot par, aapki VO file se.
6. **Verify:** height + audio stream dono check, warna exit 3.

Ye poora chain **$0** hai aur 960×1664 + mixed audio deta hai — reels ke liye enough, 2K nahi.

## 5. "Ek hi pass me synced audio" chahiye to (sasta paid raasta, per-hour)

| Route | Kya milta hai | Cost |
|---|---|---|
| **Ovi fp8 on rented 4090 (24 GB)** | 720×720/960×960 + synced voice/SFX | ~$0.30–0.45 / hour → 8–12 clips per hour ≈ **$0.04/clip** |
| **Ovi bf16 on A100 40 GB** | same, faster | ~$1.2–1.6 / hour |
| **MiniMax-H3 API 768P** | 768×1365 + stereo + lipsync | **$0.08/s** → 5 s = $0.40 |
| **H3 2K** | 1440×2560 + stereo | **$0.13/s** → 5 s = $0.65 |

Agar ek reel me 1 hero shot chahiye: free plates (960p) + ek Ovi/ H3 hero ≈ **$0.40–0.65 total**.
Free Colab par Ovi **mat** chalao — 11B + Colab free ka ~12 GB system RAM = OOM ya 30+ min/4 s clip.

## 6. Do-not list

- Free T4 par Ovi ya Kandinsky 6 chalane ki koshish (24 GB floor) — Colab Pro L4/A100 ya rented 4090.
- MMAudio/MusicGen weights ko paid client delivery me use karna.
- "Free me Veo-3 level synced dialogue" — nahi hai; stems + LatentSync hi free raasta hai.
- MusicGen bed ko full song samajhna — 30 s chunks, structural control kam.
- Chatterbox clone ke liye kisi aur ki awaaz bina permission use karna.
