# VIDEO — `stickman_wide_hook_53s.mp4`
## 16:9 long-form opening hook · "The Slowest Predator" · ancient-survival niche

**File** `/home/user/stickman_wide_hook_53s.mp4`
**1920 × 1080 · 30 fps · 53.000 s · 1590 frames · 14,113,533 B · sha `283de8becbb95f97`**
H.264 High@4.0 yuv420p, CRF 24 / maxrate 1900k · AAC 192 k 48 kHz · faststart

This is the **opening 50 seconds** of an 8–15 minute episode, built to prove the
engine retargets from 9:16 to 16:9. The body of the episode runs on the
existing Style A image-compile pipeline, which is untouched.

---

## 1. Additive — nothing was modified

| file | status |
|---|---|
| `src/wide.py` | **NEW** — landscape scene renderer |
| `src/wide_audio.py` | **NEW** — landscape sound design |
| `assets/w1…w6.mp3` | **NEW** — English VO |
| `SCRIPT_HOOK_PERSISTENCE.md` | **NEW** — script + sources |
| `MONARCH_SKILL_LONGFORM_16x9.md` | **NEW** — the skill doc |
| `src/clean.py`, `src/toon.py`, `src/make_asmr.py` | **unchanged** |
| `stickman_money_37s_v9.mp4`, `assets/s1…s6.mp3` | **unchanged** |

`wide.py` imports `toon.py` read-only. The four character colours that `toon()`
does not expose as arguments are rebound at import time inside `wide.py`'s own
process; `clean.py` never imports `wide.py`, so the vertical build cannot be
affected.

---

## 2. Script — 8 beats, 9 verifiable facts in 50 s

| S | in | out | VO | line |
|---|---|---|---|---|
| 1 | 0.000 | 6.900 | w1 @0.350 | "You have been running for two hours. The antelope ahead of you stopped being faster forty minutes ago." |
| 2 | 6.900 | 13.000 | w2 @7.250 | "No bow. No spear. Nothing in your hands but a stick, and a gourd of water." |
| 3 | 13.000 | 19.200 | w3 @13.350 | "It is forty-two degrees out here. Push too hard, and you go down before it does." |
| 4 | 19.200 | 24.700 | w4 @19.550 | "So how did the slowest predator on the savanna become the one that never loses?" |
| 5 | 24.700 | 31.000 | w5 @25.050 | "Your skin carries up to four million sweat glands. Ten times a chimpanzee's…" |
| 6 | 31.000 | 37.300 | *(w5 cont.)* | "…The kudu has almost none. It cools by panting, and it cannot pant while it gallops." |
| 7 | 37.300 | 45.400 | w6 @37.750 | "Every time it sprints, it heats up. Every time you jog, you cool down…" |
| 8 | 45.400 | 53.000 | *(w6 cont.)* | "…below thirty-nine degrees while the oryx hit forty-four. He didn't outrun it. He out-cooled it." |

Measured VO: `6.11 · 5.30 · 5.46 · 4.83 · 11.86 · 14.92 s`.
**No `atempo` anywhere.** The picture was cut to the voice, not the reverse.
Two lines deliberately span two visual beats — the cut lands mid-sentence,
which is free retention.

Sources for every claim: `SCRIPT_HOOK_PERSISTENCE.md`.

---

## 3. Grid (locked)

```
title-safe  x  96 – 1824    y  54 – 1026
chrome      y  64 –  118
headline    y 170 –  300
stage       y 330 –  824    GY = 824   <- one horizon, held all 8 beats
statchip    CHIP_Y = 888
caption     CAP_Y  = 952    (128 px clear of the frame bottom)
```
The lower band was lifted 46 px from the first build: YouTube's transport bar
and gradient cover roughly the bottom 100 px of a 1080-tall player on hover,
and v1's caption at y 998 sat under it.

## 4. Palette — all WCAG ≥ 4.5:1 on paper AND on the ground band

```
PAPER (243,236,221)   PAPER_D (231,221,201)   INK (28,24,22)   SOFT (104,95,82)
ACC = [(166,62,24) (104,70,38) (171,38,30) (44,58,112)
       (16,104,96) (122,84,10) (26,96,58)  (166,62,24)]
```
| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| vs PAPER | 5.37 | 7.16 | 5.90 | 9.17 | 5.63 | 5.76 | 6.43 | 5.37 |
| vs ground | 4.69 | 6.25 | 5.15 | 8.01 | 4.91 | 5.03 | 5.61 | 4.69 |

`SOFT` was darkened from (128,118,102) → (104,95,82): the original was 3.80:1
and the chapter tag / axis labels are small text.

## 5. Character

v9 3D rig, unchanged. Hunter recolour: `shirt (196,150,108)`, `pants
(150,110,70)`, `hair (44,36,30)`, plus `T.SHOE (132,96,58)` / `T.SOLE
(88,62,36)` / `T.SHIRT_D (172,128,90)` / `T.PANTS_D (124,90,56)` rebound at
import.

**`p_run`** — new, built on the v9 pose contract:
`yaw 60 · lean 16 · rate 9.4 · az ±46 · elbow 66+20 · knee 14+78·max(0,sin(q+1.9))^1.5 · _bob 0.040|cos φ|−0.012`
**`p_jog`** — `yaw 54 · rate 6.6 · lean 8`, knee and arm swing scaled back.

> Yaw is the whole trick. At the v9 walk's 27° the sagittal stride is
> foreshortened to nothing in a wide frame and the figure hops on the spot.
> Tested 44 / 62 / 78 — 60° is correct, 78° collapses the shoulders.

**`antelope()`** — one filled silhouette on ungulate proportions. `s` = withers
height; top of the back lands at `gy - s`; belly at 0.66 s. Wedge barrel,
fore-aft leg swing, carpus bends back / hock bends forward, horns raked back,
transverse gallop with suspension lift.

## 6. Audio

Bed (`src/wide_audio.py`, 98 logged events, 84 BPM, D-minor/Dorian):
true-stereo drone (independent detuning + phases per channel), frame drum on
1 and 3, sand shaker on eighths, 0.09 Hz wind swells, bone-flute answers,
plus a cue layer locked to every on-screen reveal — including the S6 gait
pulse, which fires the kudu at 2.4 Hz and the human at half that.

```
VO : highpass 90, eq 250 Q1.0 −4.2, eq 430 Q1.4 −1.6, eq 3100 Q1.3 +3.6,
     treble +2.8 @7400, acompressor .045/3.6/10/170/mk1.5, volume 1.92
bed: volume 0.98
duck: sidechaincompress thr .022 ratio 6 attack 6 release 280
mix: amix weights "1 1" normalize=0, treble +3.4 @9000, extrastereo m=1.85,
     loudnorm I=-11:TP=-1.6:LRA=9, alimiter limit=0.63:level=disabled,
     apad=whole_dur=53.4, atrim=0:53.0, asetpts=N/SR/TB
vid: libx264 preset slow crf 24 maxrate 1900k bufsize 3800k high@4.0 g 60
aud: aac 192k 48000 · +faststart · -t 53.0
```

## 7. Forensic scorecard — v1 → delivered

| metric | v1 | **delivered** | target |
|---|---|---|---|
| identical frames | 0 | **0** | 0 |
| max abs ΔLuma | 5.12 | **5.05** | < 8 |
| frames ΔLuma > 8 | 0 | **0** | 0 |
| per-scene p10 frame-diff (min) | 0.135 | **0.14** | > 0.12 |
| jerk p95 | 1.42 | **1.42** | < 2.0 |
| accent contrast (worst) | 4.69 | **4.69** | ≥ 4.5 |
| caption clearance | 82 px ✗ | **128 px** | > 100 px |
| L/R correlation | 0.9817 ✗ | **0.6771** | 0.55 – 0.80 |
| side / mid | 0.096 ✗ | **0.439** | > 0.25 |
| energy 20–120 Hz | 34.2 % ✗ | **11.7 %** | < 20 % |
| energy 120–500 Hz | 39.5 % | **53.2 %** | < 58 % |
| energy 4–8 kHz | 7.9 % ✗ | **10.3 %** | > 10 % |
| decoded peak | +0.39 dBFS ✗ | **−2.13 dBFS** | ≤ −1.0 |
| audio vs video duration | −0.371 s ✗ | **−0.072 s** | within 0.1 s |

Seven gates failed on the first build. All pass now.

## 8. Rebuild

```bash
pip install imageio-ffmpeg
mkdir -p build
printf "file '/home/user/build/wc0.mp4'\nfile '/home/user/build/wc1.mp4'\n" > build/wclist.txt
python3 src/wide.py   0  795 build/wc0.mp4   &
python3 src/wide.py 795 1590 build/wc1.mp4   &   wait
python3 src/wide_audio.py
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
$FF -y -f concat -safe 0 -i build/wclist.txt -c copy build/wide_mute.mp4
# + the mux in §6
```
~5 min per shard on one core, ~2 min for the bed, ~90 s for the mux.
`build/` is not snapshot-persisted — recreate it before launching shards.
