# 04 · WF-04 Monarch Face → H3 = "next level" pipeline

Yeh woh jawab hai: agar H3 isi tarah run karke AI videos generate karwate rahein, to agla level kya hai?
Jawab: **locked Monarch face ko H3 ka runtime character bana do** — static sheets se live, speaking,
sound-carrying footage tak. Neeche exact pipeline, reference prep, prompt skeleton aur level-wise plan.

## 1. Concept

WF-04 tumhe **identity** deta hai (locked REAL face v5 + body v2, stick face v4 + body v4). H3 us identity ko
**performance** deta hai: lipsync dialogue, expression, camera, light, ambience, music. Is ke baad WF-05 us
performance ko **film** banata hai (typography, transitions, score, pacing, delivery).

```text
IDENTITY (WF-04) ──► PERFORMANCE (H3 Ref2VA) ──► FILM (WF-05) ──► DELIVERY
```

## 2. Reference pack — ek dafa banao, hamesha use karo

H3 Ref2VA ko **≤9 images** (pehli 5 free) + **≤3 audio** (free) dete hain. Monarch ke liye locked pack:

| Slot | File | Kahan se | Kyun |
|---|---|---|---|
| `<Picture 1>` | `MONARCH_REAL_FRONT.png` (hero shot, boss gaze) | `MONARCH CHARACTERS/Realistic` (Drive `1NpOJTSOY3zjkBR8LoktHDUFUSB8oW5jN`) | primary identity |
| `<Picture 2>` | `MONARCH_REAL_34.png` (three-quarter) | turnaround panel crop | angle interpolation |
| `<Picture 3>` | `MONARCH_REAL_PROFILE.png` (right profile) | profile authority | side shots, nose/chin lock |
| `<Picture 4>` | `MONARCH_REAL_SMILE.png` (expression 01) | expression set | warm/approachable beat |
| `<Picture 5>` | `MONARCH_REAL_INTENSE.png` (expression 05) | expression set | "boss" beat |
| `<Audio 1>` | `monarch_voice_ref.mp3` (5–10 s clean speech) | selected studio voice (`voice-00` style) | timbre lock for dialogue |

Rules:

1. Images **crop karo, upscale na karo** — 256–5760 px side, JPG/PNG/WEBP, ≤30 MB each.
2. Profile aur front ek hi lighting me rakho (soft key upper-left, teal+amber rims) — warna H3 light ko average
   kar deta hai.
3. Audio ref 2–15 s, WAV/MP3, ≤15 MB, sirf us voice ka clean speech (music/echo nahi).
4. **Same pack har shot me.** Naya shot = naya prompt, naya reference set nahi.
5. Pack ko `styles/minimax-h3-video/assets/refs/` me rakho (Git me heavy media na dalo — Drive + md5 record).

## 3. Shot skeleton (copy-paste, sirf `detailed_description` badlo)

```text
subject_definitions:
<Subject 1> is the man in <Picture 1>–<Picture 5>: late-20s South Asian man, thick swept-back black hair with
volume at the crown, long side locks in front of the ears, light beard along the jaw, straight nose with a
slightly dropped tip, thin lips set back, wearing a fitted black shirt with the top button open and a charcoal
blazer. <Picture 1> front hero, <Picture 2> three-quarter, <Picture 3> right profile, <Picture 4> warm smile
reference, <Picture 5> intense gaze reference. <Audio 1> is the voice-timbre reference for <Subject 1>.

summary:
[single character, direct address] A <DURATION>-second <RATIO> shot of <Subject 1> in <ENVIRONMENT>, lit by a
soft key from upper-left with teal and amber rim lights, performing <ONE BEAT>.

retention_analysis:
<Subject 1>: fully_preserved - same face, hair volume, side locks, beard line, nose, wardrobe; expression and
head angle change per the beat.
<Audio 1>: reference - target speech follows the timbre and pacing of <Audio 1>.

detailed_description:
The target video is in realistic photographic style.
[Shot 1] <composition + distance + subject position + light> ... <action onset> ... <(S1) says: <d>[Urdu]
<line></d>> ... <reaction / beat landing> ... <camera: type + amplitude + speed> ...

overall_soundscape:
<room tone + fabric/breath/footstep detail>

non_diegetic_music:
<score or "none">
```

## 4. Levels — plan jo aaj se chal sakta hai

| Level | Deliverable | Shots | Cost est. | Kya prove hota hai |
|---|---|---|---|---|
| **L1 · Identity test** | 5 s, 9:16, ek line dialogue | 1 | $0.40–0.65 | face lock + voice timbre + lipsync reality |
| **L2 · Scene test** | 3 shots × 5 s, cuts, ek dialogue + ek reaction | 3 | ~$2 | shot-to-shot identity + audio continuity |
| **L3 · Monarch reel** | 45–60 s, 6–8 shots, H3-native audio + WF-05 typography | 6–8 | $8–12 | poora production loop |
| **L4 · Series system** | locked ref pack + prompt skeleton + gate report → har hafte episode | — | per episode | repeatable, quoted, on-brand |

Level 1 pehle chalao. Uske numbers ke baghair L3 ka budget guess hi rahega.

## 5. QC gates (H3 batch ke liye)

1. **Identity gate:** output frame vs `CUSTOM_HERO_MASTER_BOARD_v2.png` side-by-side. Chehre ka shape, hair
   volume, side locks, beard line, nose profile — 4/5 match minimum. Na ho to reference pack theek karo,
   prompt nahi.
2. **Performance gate:** lipsync line ke saath sync, jaw motion natural, blink kam az kam ek dafa.
3. **Audio gate:** dialogue intelligible, language tag sath match, music dialogue ko dabata nahi, stereo 32 kHz.
4. **Format gate:** `ffprobe` → 24 fps, requested ratio, duration ±0.2 s.
5. **Continuity gate:** same shot family me light direction aur wardrobe identical.
6. **Cost gate:** `usage.output_seconds` se actual cost nikalo, budget se compare, `records/` me likho.
7. **Safety gate:** moderation rejection ka reason note karo, blocked phrasing ko log me daalo (lessons file).

## 6. Handoff contract to WF-05 (editing)

H3 se milega: `shot-XX.mp4` (24 fps, H.264, stereo) + `receipts.json`. WF-05 ko dena:

- **video only trim** — H3 ka audio alag `shot-XX.wav` export karo (`ffmpeg -i shot.mp4 -vn -c:a pcm_s16le`),
  taake score aur VO ke saath mix ho sake.
- **24 → 30 fps conform** (`fps=30` filter, frame duplication) — speed change na karo.
- **9:16 ya 16:9 safe areas** — H3 ke frame me typography ke liye jagah prompt se hi reserve karo
  (e.g. "lower third of the frame stays empty dark space"), warna caption face par aa jayega.
- **look match** — H3 ka teal/amber rim WF-05 ke grade se match karna hai; LUT ek hi rakho.

## 7. Kab H3 use NA karo

- WF-01 stickman: procedural rig hi authority hai.
- WF-03 noir film #3+: hero ka line-art DNA H3 se reproduce nahi hota; sirf plates/atmosphere.
- Text-heavy explainer frames: H3 on-screen text (Arabic/Urdu typography) par bharosa na karo.
- Client ke liye 2K promise: **local route se 2K mumkin nahi** — API ya regeneration lazmi.
