# CHAOS · NEXT FILM — v3 TRUE-3D BUILD

**Yeh document measured artifacts se banaya gaya hai** — `v3/report.py` `SHOTLIST_3D.json`, `DELIVERY_PREVIEW.json`, `QC_REPORT_GRADED.json` aur `AUDIO_MASTER_RECEIPT.json` padh kar khud likhta hai. Jo number file mein nahi, woh yahan nahi.

---

## 1. Kya bana

| Cheez | Halat | File |
|---|---|---|
| Shotlist | **113 shots · 1332 frames · 44.4 s** | `v3/SHOTLIST_3D.json` |
| 3D scene (set + character + lights + cameras) | generated in code | `v3/chaos_scene.py` |
| Score | procedural, 48 kHz, cut-grid driven | `v3/score.py` |
| End card | our own, replaces reference creator's outro | `v3/endcard.py` |
| Delivered preview | **26.19 MB · 1080×1920 · 30 fps · 44.4 s** | `v3/out/CHAOS_NEXT_FILM_v3_graded.mp4` |
| Checksums | md5 `92b99cc709c0557aa360c82bda61015b` · sha256 `1c54bf9f3a0aec385a184deb…` | `v3/out/DELIVERY_PREVIEW.json` |
| QC | **10/10 measured gates** | `v3/out/QC_REPORT_GRADED.json` |

## 2. Rhythm — reference se **naapa hua**, copy nahi

| | Reference (`VID_20261013_050529_146.mp4`) | Hamari film |
|---|---|---|
| Duration | 44.40 s | 44.4 s |
| Frames @30 | 1,332 | 1332 |
| Hard cuts | 171 | 170 (+ act boundaries) |
| Act structure | 6 acts | 6 acts, same boundaries |
| Resolution | 720×1280 | 1080×1920 |

Cut *timing* reference ke measured cut instances se aata hai (frames 0–1331 par exact), lekin **koi pixel, frame, audio ya asset reference se nahi liya gaya** — har frame hamare 3D scene se render hua hai.

## 3. Acts (measured boundaries)

| Act | Naam | Frames | Shots | Feel |
|---|---|---|---|---|
| A1 | hall_reveal | 0–289 | 1 | two long wides, no cutting, only drift |
| A2 | doorway_figure | 289–489 | 2 | figure in doorway, scarlet practical, long hold |
| A3 | masked_closeups | 489–876 | 68 | masked hero, crescent visor, rapid cutting begins |
| A4 | doorway_hold | 876–987 | 2 | 3.7 s breathe: wide doorway, red floor light |
| A5 | climax | 987–1275 | 39 | fastest cutting, blade reveal, red strobes, overhead |
| A6 | end_card | 1275–1332 | 1 | OUR OWN outro card (reference's IG card is replaced, never reused) |

## 4. QC — jo file se decode kar ke naapa gaya

| Gate | Nateeja |
|---|---|
| T1_spec | ✅ |
| T1b_faststart | ✅ |
| T2_frames | ✅ |
| T3_rhythm | ✅ |
| T4_arc | ✅ |
| T5_contrast | ✅ |
| T6_scarlet | ✅ |
| T7_loudness | ✅ |
| T8_true_peak | ✅ |
| T9_motion | ✅ |

| Measure | Value |
|---|---|
| Decoded frames | 1332 |
| Mean luma | 19.3 / 255 |
| p10 / p90 luma | 5.4 / 40.8 |
| Scarlet bias (R − mean(G,B)) | +15.7 |
| Cuts detected (p97 diff) | 13 |
| Longest static run | 3 frame pairs |
| Loudness | -14.73 LUFS |
| True peak | -1.76 dBFS |
| Rhythm alignment (mean frame diff on planned cuts vs elsewhere) | 59.6× |
| Act luma (6 acts) | [8.2, 18.9, 22.8, 19.2, 28.9, 4.1] |
| Reference act luma | [9.4, 19.0, 27.0, 20.0, 29.0, 8.0] |


Audio master chain: highpass 32 Hz → compressor 2.6:1 → gain 9.98 dB → true-peak limiter -4.0 dB. Result: **-14.7 LUFS / -1.68 dBTP / LRA 12.7** (target hit).

Luma-arc grade (act gains): `{'A1': 0.43, 'A2': 0.65, 'A3': 1.383, 'A4': 0.963, 'A5': 1.78, 'A6': 1.25}` — measured before `[21.8, 29.2, 19.5, 20.8, 16.3, 3.6]`, reference target `[9.4, 19.0, 27.0, 20.0, 29.0, 8.0]`.

**QC ka matlab samajh lein:** yeh *technical* gates hain (spec, rhythm, exposure arc, loudness, motion). Ye creative approval nahi hai — woh aap ka faisla hai.

## 5. Honest limits (jo abhi kam hain)

1. **Character detail:** yeh preview 288×512 par render hui hai (2 vCPU, GPU nahi). 1080×1920 par scale hoti hai liye picture soft hai. Full-res render ka time neeche table mein hai.
2. **Face/expressions:** abhi hero **masked visor** design hai — 22-blendshape face rig is build mein nahi hai. Khula chehra chahiye to woh agla gate hai.
3. **Deep detail close-ups:** is art pass mein tight inserts environmental rakhe gaye hain (portal ring, chains, blade) — character ke extreme close-ups tabhi jayenge jab mesh/garment detail barhe.

## 6. Full-res render ka rasta (measured)

| Resolution | Samples | s/frame (measured on this box) | Poori film |
|---|---|---|---|
| 288×512 | 8 | 4.1 | ~90 min |
| 324×576 | 8 | 5.2 | ~2.0 h |
| 405×720 | 12 | 10.4 | ~3.9 h |
| 1080×1920 | 16 | 59.1 | ~21.9 h |

GPU ka rasta (aap ke Colab/Kaggle notebook se) isi animatic ko *driving video* bana kar **Wan2.2-Animate-14B** par bhej sakta hai — motion bilkul yehi, skin/detail photoreal, aur GPU hours sab se kam. Notebook: Drive `Chaos video 2` → `CHAOS_GPU_COLAB.ipynb`.

## 7. Dobara chalane ke commands

```bash
cd workflows/current/payload/WF04-CHAOS04
python3 v3/build_shotlist.py
LD_LIBRARY_PATH=/home/user/.runtime/xstub python3 v3/chaos_scene.py \
    --frames 0:1331 --res 288x512 --samples 8 --out v3/render/animatic
python3 v3/endcard.py
python3 v3/score.py
python3 v3/assemble.py && python3 v3/verify.py && python3 v3/report.py
```

