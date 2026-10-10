# 🧠💀 MASTER PROMPT v2 — THE COMPLETE BUILD BIBLE
## "How To Make Money Online" — procedural viral video system (10 s cinematic reel + 37 s stickman explainer)
### Forensic edition · nothing omitted · every constant, formula, cue, command, bug and fix

> **How to use this file**
> • **§1** = the copy-paste MASTER PROMPT (self-contained; hand it to any agent/dev and the whole system rebuilds).
> • **§2–§20** = the microscope: architecture, full API reference, shot lists with literal parameters, audio math, QA protocol, bug museum, extension recipes.
> • Anything written as `code` is literal and must be reproduced exactly.

---
---

# §1 — THE MASTER PROMPT (copy-paste block)

```
════════════════════════════════════════════════════════════════════════════
ROLE
You are a senior motion-design engineer + technical sound designer + video editor.
You have NO video-generation model, NO stock footage, NO music library, NO sample packs.
Everything — every pixel and every sample — is generated procedurally in Python
(Pillow + NumPy + SciPy) and encoded by ffmpeg. Output must look and sound like it was cut
by a top-1% social media editor.

MISSION
Build a vertical 1080x1920 "How to make money online" package in two distinct looks:
  LOOK A  "Cinematic Reel"      10.000 s @ 60 fps  — neon/3D premium motion graphics
  LOOK B  "Stickman Explainer"  37.000 s @ 30 fps  — chalkboard doodle cartoon (flagship)
Both: Urdu voiceover, 100% synthesized music + SFX, beat-synced cutting, platform-ready encode.

════════ HARD RULES (violating any of these = failed build) ════════
R1  Canvas exactly 1080x1920. Durations exactly 10.000 s / 37.000 s (verify with ffprobe).
R2  Stream frames: popen ffmpeg with
      -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r FPS -i -   and write frame.tobytes() per frame.
    Never accumulate frames in a list (2-core / 1 GB box; 1110 frames x 6 MB = death).
R3  Source code lives in src/. NEVER in build/, dist/, out/, target/, __pycache__ (those names are
    excluded from workspace snapshots and WILL be deleted). Intermediates go to build/. Final .mp4
    in the project root.
R4  pip installs do not persist across sessions: start every session with
      pip install imageio-ffmpeg   and resolve the binary via imageio_ffmpeg.get_ffmpeg_exe().
R5  No Urdu/Arabic glyph coverage is installed → ALL on-screen text is English / Roman-Urdu.
    Urdu exists only as speech. Do not attempt Urdu text rendering.
R6  Every duration is DERIVED from measured audio, never guessed. One shared timeline module is
    imported by BOTH the renderer and the audio builder so picture/sound can never drift.
R7  Cache every static raster (text images, coins, cards, board texture, doodle layer, masks) in a
    dict keyed by its parameters; evict when the dict exceeds ~50-160 entries.
R8  Per-frame budget <= 0.6 s. If exceeded, move work to lower resolution (backgrounds at 1/6,
    bloom at 1/4, particle layers at 1/2) and upscale.
R9  No frame may ever be empty or near-empty — including the 0.34 s transition windows.
R10 Deliver <= ~15 MB per file (re-encode pass if needed) so in-app previews load, with +faststart.

════════ STAGE 1 · SCRIPT & VOICE ════════
1.1 Write the script in Urdu, SPLIT PER SCENE (6 clips for the 37 s version, 1 for the 10 s).
    Each clip is one scene's narration — this is what makes perfect sync possible.
1.2 Synthesize each clip with the SAME voice id.
1.3 Trim silence both ends:
    silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,areverse,<same>,areverse
1.4 Measure each trimmed clip (ffprobe). Pick a global tempo (1.45 = energetic reel pacing).
1.5 timeline:  vo_len[i] = raw[i]/TEMPO ;  scene_len[i] = vo_len[i] + tail[i] (+lead on the first)
    Tune tails (0.30 s, 0.45 s on the last, 0.30 s lead) until the total is an exact round number.
1.6 If the VO is ever re-generated and lengths shift, DO NOT re-time the picture:
    per-clip atempo = new_len / original_target_len. Slots stay identical.

════════ STAGE 2 · LOOK B — STICKMAN / CHALKBOARD (flagship) ════════
2.1 BOARD TEXTURE (built once): 360x640 noise sigma=7 -> GaussianBlur 1.6 -> bicubic to 1080x1920
    -> 900 dust specks (1-3 px, value 36-70) -> 14 soft white-alpha-7 smudges (r 70-240).
2.2 LIVING BACKGROUND, 5 layers bottom-up:
    (a) board texture
    (b) accent colour wash: 180x320 float field, 3 Gaussian glows — scene accent on a Lissajous
        path (amp .26), cyan counter-glow (.12), broad centre lift (.18) -> bicubic upscale
    (c) graph-paper grid, 135 px, alpha 9, scrolls (t*26)%135
    (d) parallax doodle layer: 1080x2520 with 46 faint doodles (circle/star/$/triangle/squiggle,
        alpha 34), scrolls (t*34)%600  -> different speed than (c) = depth
    (e) scene content layer (transparent RGBA), composited twice: blurred 13 px at 42 % (chalk glow)
        then sharp on top.
2.3 HAND-DRAWN "BOIL": every vertex is displaced by deterministic hash noise that only changes
    every 2 frames (15 fps boil):
      hsh(a,b) = frac(sin(a*12.9898 + b*78.233) * 43758.5453)
      jpt(p,seed,tq,amp) = p + (hsh(seed*1.7+tq*3.1)-.5)*2*amp , (hsh(seed*3.3+tq*5.7+9.1)-.5)*2*amp
    Every primitive gets a unique seed. Line ends are capped with filled circles.
2.4 DRAW-ON REVEAL: truncate any polyline by ARC LENGTH fraction p (interpolate the last partial
    segment) so strokes appear to be drawn by hand, never faded in.
2.5 RIGGED STICK FIGURE (forward kinematics, proportions relative to height s):
      hip=(x, y-.42s) ; neck=hip+rot(lean)(0,-.36s) ; head=neck+rot(lean+head)(0,-(.115s+.035s))
      shoulder=neck+(0,.03s) ; arms .19s+.18s ; legs .22s+.22s ; feet .055s stub
      pose = {lean, head, al, el, ar, er, ll, kl, lr, kr} degrees, 0 = straight down
      faces: eyes r=.014s at +-.38*head_r ; mouth = arc (happy/sad) or line (neutral)
    Pose library: idle, sad, type, cheer, point(up/right), think, walk, shake, dance (all time-driven
    with sine oscillators). Motion trails = the same pose at t-k*0.055 drawn dimmer and thinner.
2.6 3D MARKER TYPE: glyph mask + stroke-6 mask; glow = blur(outline,26)*1.8*120/255; extrusion =
    depth copies offset (0.45i, 0.95i) darkening toward the back; dark outline (10,13,19); flat face;
    animated specular sweep band exp(-((x+0.3y-1.6*phase)^2)/(2*0.14^2)) * mask * 215.
    Entry: scale 0.4+0.6*out_back(p,2.4), horizontal squash (1+sq) with vertical 1/(1+sq).
2.7 VFX LIBRARY (all hand-drawn style): speed lines, shockwave rings, comic star burst with word,
    chalk dust puffs, sparkle crosses, flames, crown, floating badges, highlighter swipes,
    hand-drawn circle-marks, animated underlines, coin rain, fireworks, stickman trails.
2.8 TRANSITIONS — one distinct type per cut, 0.34 s, placed AFTER the cut:
      composite = Image.composite(new_scene_at_t, old_scene_frozen_at_its_last_frame, mask)
      masks (computed at 540x960, blurred 5, upscaled): ink-blob iris with angular wobble /
      7-column paint wipe / noisy eraser wipe / vertical zip / diagonal whip.
    Plus per-cut: warm flash, RGB split, 5-tap horizontal smear, shake, rotation.
2.9 HUD: progress bar (chapter dots at each cut, gold fill, round head), "STEP x/4" badge,
    @handle watermark.

════════ STAGE 3 · LOOK A — CINEMATIC REEL ════════
Dark gradient + 3 moving Gaussian glows; synthwave perspective grid (horizon .70H, 1/z spacing);
bokeh particles; Montserrat ExtraBold/Black with per-character tracking, 3-stop vertical gradient
fill, two-pass glow, dark stroke, TRUE extrusion + specular sweep; glass-morphism cards with
shadow/inner highlight; neon vector icons (bulb/clock/rocket) with progress rings; rolling money
counter with motion blur; parallax depth per element; glitch + RGB split + smear + light-leak flash
transitions; anamorphic streaks; bloom; filmic grade; handheld camera + 126 BPM bump.
Beats: 0.00 hook / 2.85 step1 / 4.95 step2 / 7.05 counter / 8.55 CTA / 10.00.

════════ STAGE 4 · POST CHAIN (exact order, per frame, float32) ════════
  1 5-tap horizontal motion smear (near cuts only)
  2 camera: zoom -> rotate -> centre-crop (push-in + handheld sines + per-cut shake)
  3 RGB split: roll R +s px, B -s px
  4 glitch slices (doodle: only within +-0.07 s of a cut; 7 slices, dy 10-60 px, dx ~ N(0,38)*k)
  5 bloom: /4 downscale, threshold 168-172, blurs 15 & 32, upscale, add * 0.5
  6 grade: shadows += (-3,1,11)*(1-lum), highlights += (13,5,-7)*lum, S-curve 30 % smoothstep blend
  7 vignette multiply, flash add, paper jitter roll (+-2 px on the 2-frame hash), grain add
  8 clip to uint8

════════ STAGE 5 · AUDIO (synthesize everything) ════════
Reverb: IR = noise * exp(-decay*tau), low-passed, 12 ms pre-delay, applied with fftconvolve.
Instruments: kick (f=46+95e^-32t), 808 with glide, shaker/hat (HP noise), clap (4 taps), snare,
woodblock, marimba (additive), pizzicato (detuned saws + LP), whistle (vibrato sine), pads.
Cartoon SFX: pencil scratch (BP noise x 38-63 Hz flutter), pop (fast pitch drop), ding (3 partials),
boing (vibrato glide), swish (18-chunk BP sweep), cinematic impact (boom+sub+crack+rumble), riser
(exp pitch + accelerating tremolo), reverse cymbal, coin clink, cash register, firework.
Arrangement: doodle = 112 BPM major bed (kick 1&3, clap 3, shaker 8ths, marimba arpeggio, pizzicato,
whistle melody [0,4,7,12,11,7,4,2], woodblock fill every 4th bar); reel = 126 BPM trap bed.
EVERY visual event gets a cue. Each scene start = riser(-0.85) + reverse cymbal(-0.80) +
swish(-0.30) + IMPACT(0) + 808(0) + swish(+0.02) + pencil(+0.06) + pop(+0.10).
Master: kick-grid sidechain pump, HP 32 Hz, mid/side widening above 3 kHz, tanh saturation,
peak 0.93.

════════ STAGE 6 · MIX & ENCODE ════════
VO: per-clip atempo -> adelay to slot -> amix -> HP 95 -> EQ (-2.5 dB @250, +4 dB @4k) ->
acompressor(-20 dB, 5:1, 5/110, +5) -> alimiter -> apad/atrim.
Mix: sidechaincompress(threshold 0.030, ratio 8, attack 6, release 260, makeup 1.8) keyed by VO ->
amix weights 1 : 1.4 -> loudnorm I=-11 TP=-1.0 LRA=10 -> alimiter 0.97 -> atrim exact.
Encode: libx264 High, preset slow, crf 23 (master) then a size pass at crf 27 / maxrate 2800k,
-pix_fmt yuv420p, -g 60, AAC 160-192k, -movflags +faststart.

════════ STAGE 7 · QA GATE (all must pass) ════════
Q1 ffprobe duration == target, both streams.          Q2 sample frames at every cut +-0.1 s: never empty.
Q3 no element within 40 px of the frame edge.         Q4 nothing collides with HUD/watermark.
Q5 transition masks: fractional geometry only (or scale x2 when drawn full-res).
Q6 PIL guards: rounded_rectangle x1>=x0 (clamp widths >= 4 px); gradients broadcast as (h,1,1);
   a re-made mask must keep the SAME padding as the first one.
Q7 loudness -11..-12 LUFS, true peak <= -1 dBTP.      Q8 file <= ~15 MB, +faststart present.
Q9 sources in src/, deliverable in root, intermediates only in build/.
════════════════════════════════════════════════════════════════════════════
```

---
---

# §2 — DESIGN PHILOSOPHY (why every choice was made)

| Decision | Reason |
|---|---|
| Procedural frames, not a video model | Full control, exact timing, infinite re-renders, zero licensing risk |
| One VO clip **per scene** | Scene length = speech length → sync is structural, not manual |
| Shared `timeline.py` | Picture and sound read the same numbers; drift is impossible |
| Hash-noise "boil" at 15 fps | Real hand-drawn animation wobbles on 2s; smooth lines read as "computer-made" |
| Arc-length stroke truncation | Draw-ON (not fade-in) is the single biggest "hand-made" signal |
| Extrusion + sweep instead of fake 3D plugins | Gives depth and specular motion with pure 2D compositing |
| Transition AFTER the cut, old frame frozen | Guarantees the new scene's audio starts exactly on time while the wipe plays |
| Bloom + S-curve grade last | Unifies chalk, colour, and glow into one photographic image |
| Everything cached by key | 1110 frames x heavy text rasterisation would otherwise be 10x slower |
| Two encodes (master + size pass) | Master keeps quality for re-use; size pass guarantees the preview loads |

---

# §3 — ENVIRONMENT, PERSISTENCE, BOOTSTRAP

```
Python 3.13 · Pillow 12.3 · NumPy 2.3.5 · SciPy 1.17.1 · ffmpeg 7.0.2 (via imageio-ffmpeg)
CPU 2 cores · RAM 1 GB  → stream frames, keep caches small, work at reduced res where invisible
```
**Persistence law:** directories named `build`, `dist`, `out`, `target`, `node_modules`,
`__pycache__`, `.venv`, `.cache` … are **excluded from snapshots**. Code → `src/`. Deliverables → root.

**Bootstrap (run first in any new session):**
```bash
pip install imageio-ffmpeg
python3 -c "import imageio_ffmpeg,PIL,numpy,scipy;print(imageio_ffmpeg.get_ffmpeg_exe())"
mkdir -p src build assets fonts
curl -sL -o fonts/Montserrat-VF.ttf   "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"
curl -sL -o fonts/PermanentMarker.ttf "https://github.com/google/fonts/raw/main/apache/permanentmarker/PermanentMarker-Regular.ttf"
curl -sL -o fonts/PatrickHand.ttf     "https://github.com/google/fonts/raw/main/ofl/patrickhand/PatrickHand-Regular.ttf"
curl -sL -o fonts/Caveat-VF.ttf       "https://github.com/google/fonts/raw/main/ofl/caveat/Caveat%5Bwght%5D.ttf"
```
Montserrat is variable → `ImageFont.truetype(p,size).set_variation_by_name('Black'|'ExtraBold'|'Bold'|'SemiBold')`.
Permanent Marker has no numerals you want for step badges → **numbers are set in Patrick Hand**.

---

# §4 — THE SCRIPTS (verbatim)

### 4.1 Stickman version — 6 clips (Urdu, as fed to TTS)
```
S1  جیب خالی ہے؟ اور آن لائن کمانے کا طریقہ سمجھ نہیں آ رہا؟ یہ رہا پورا پلان، صرف چار قدموں میں۔
S2  پہلا قدم: ایک ہنر چنو۔ گرافک ڈیزائن، ویڈیو ایڈیٹنگ، کوڈنگ یا اے آئی ٹولز۔ یوٹیوب پر مفت کورس دیکھو اور روز نوٹس بناؤ۔
S3  دوسرا قدم: روزانہ صرف دو گھنٹے۔ تیس دن میں ساٹھ گھنٹے بن جاتے ہیں۔ یہی چیز تمہیں بگنر سے پروفیشنل بناتی ہے۔
S4  تیسرا قدم: تین سیمپل پروجیکٹ بناؤ۔ کلائنٹ تمہاری ڈگری نہیں، تمہارا کام دیکھتا ہے۔
S5  چوتھا قدم: سروس بیچو۔ فائیور، اپ ورک اور انسٹاگرام پر روز دس لوگوں کو میسج کرو۔ پہلا کلائنٹ مل گیا تو باقی آسان ہے۔
S6  بس اتنا ہی۔ ہنر، محنت، سیمپل، اور سیلنگ۔ آج ہی پہلا قدم اٹھاؤ۔ فالو کرو، پارٹ ٹو کل آ رہا ہے۔
```
### 4.2 Cinematic reel — single clip
```
آن لائن پیسہ کمانے کا سب سے تیز طریقہ! نمبر ایک، ایک ہنر سیکھو۔ نمبر دو، روزانہ دو گھنٹے دو۔
نمبر تین، اپنی سروس آن لائن بیچو۔ بس! آج ہی شروع کرو۔
```
### 4.3 On-screen copy (English / Roman-Urdu only)
S1 `JEEB KHALI?` · `Rs 0` · `PURA PLAN` · `4 STEPS ME` · `FREE`
S2 `1` `SKILL SEEKHO` · `DESIGN / VIDEO EDIT / CODING / AI TOOLS` · `+1` · `YouTube = FREE university`
S3 `2` `ROZ 2 GHANTE` · `2h DAILY` · `{0..60} HOURS` · `CONSISTENCY = POWER`
S4 `3` `SAMPLE BANAO` · `POSTER / REEL / WEBSITE` · `DEGREE nahi,` `KAAM bolta hai!`
S5 `4` `SERVICE BECHO` · `Hi! Reels edit karta hu` / `Rate kya hai?` / `Deal! Invoice bhejo` ·
   `FIVERR / UPWORK / INSTA` · `10 DM / DAY` · `DEAL!`
S6 `AAJ HI SHURU` `KARO!` · `SKILL / TIME / SAMPLES / SELL` · `FOLLOW = PART 2` ·
   `SAVE karo, bhool jaoge!` · `LET'S GO!`

---

# §5 — TIMELINE ENGINE (`src/timeline.py`)

```python
TEMPO = 1.45
RAW   = [7.13, 10.15, 9.31, 6.40, 9.02, 8.33]     # measured, silence-trimmed, seconds
VO    = [round(r/TEMPO, 3) for r in RAW]          # [4.917, 7.0, 6.421, 4.414, 6.221, 5.745]
LEAD  = 0.30
TAIL  = [0.35, 0.30, 0.30, 0.30, 0.30, 0.45]
DUR_TOTAL = 37.0
starts, t = [], 0.0
for i in range(6):
    starts.append(round(t,3)); t += (LEAD if i==0 else 0.0) + VO[i] + TAIL[i]
SCENE_START = starts
SCENE_END   = starts[1:] + [DUR_TOTAL]
VO_AT       = [round(SCENE_START[i] + (LEAD if i==0 else 0.05), 3) for i in range(6)]
```

| Scene | start | end | length | VO at | accent |
|---|---|---|---|---|---|
| S1 HOOK | 0.000 | 5.570 | 5.570 | 0.300 | RED |
| S2 SKILL | 5.570 | 12.870 | 7.300 | 5.617 | CYAN |
| S3 TIME | 12.870 | 19.590 | 6.720 | 12.917 | MINT |
| S4 SAMPLES | 19.590 | 24.300 | 4.710 | 19.638 | PINK |
| S5 SELL | 24.300 | 30.820 | 6.520 | 24.352 | GOLD |
| S6 CTA | 30.820 | 37.000 | 6.180 | 30.873 | GOLD |

**Re-sync law.** Re-recorded clips measured `[7.11, 9.46, 9.25, 6.73, 9.23, 8.54]` →
`atempo_i = new_i / VO_i` = `[1.446, 1.351, 1.441, 1.525, 1.484, 1.487]`. Picture untouched.

---

# §6 — RENDER ARCHITECTURE

### 6.1 Frame loop (pseudocode, `stick2.render(i)`)
```
t  = i / 30 ; tq = i // 2 ; si = last scene whose start <= t
bg = BOARD → + wash(t, si, next_si, mix) → + GRID(offset (t*26)%135) → + DOODLES(offset (t*34)%600)
if t ∈ [cut_k, cut_k + 0.34):                  # transition window
        old   = scene_layer(k,   lt = scene_len_k - 0.001)   # frozen last frame
        new   = scene_layer(k+1, lt = t - cut_k)             # real, animating
        layer = Image.composite(new, old, trans_mask(kind_k, p))   + edge decoration
else:   layer = scene_layer(si, lt = t - start_si)
layer += hud(t)
bg += blur(layer,13)*0.42        # chalk glow
bg += layer                      # sharp pass
frame = post(bg, camera(t))      # §11
return frame as uint8 RGB
```

### 6.2 Layer order (strict)
`board → wash → grid → doodles → [scene content: ground → props → figures → text → VFX] → HUD → glow → sharp → post`

### 6.3 Caching
| Cache | Key | Max |
|---|---|---|
| `_fc` fonts | (path, size, variation) | ∞ |
| `_tc` flat text rasters | (txt,size,col,font,rot,outline) | 160 |
| `T3._c` 3D text objects | user string key | 50 |
| `BOARD`, `GRID`, `DOODLES`, `VIGN`, `GRAIN` | module-level singletons | — |

### 6.4 Measured performance (2-core box)
| Stage | Cost |
|---|---|
| doodle frame (plain) | 0.42–0.48 s |
| doodle frame (inside a transition, 2 scenes) | 0.55–0.60 s |
| 1110 frames | ≈ 9–11 min |
| cinematic 60 fps frame | ≈ 0.70 s → 600 frames ≈ 7 min |
| audio build (37 s, all synthesis) | ≈ 4 s |
| mux + size pass | ≈ 2 min |

---

# §7 — COMPLETE API REFERENCE

### 7.1 `src/stickbase.py` — primitives (308 lines)
| Signature | Behaviour / math |
|---|---|
| `clamp(x,a=0,b=1)` | bound |
| `out_back(x,s=1.9)` | `1+(s+1)(x-1)³+s(x-1)²` — overshoot pop |
| `out_cubic(x)` | `1-(1-x)³` |
| `out_expo(x)` | `1-2^(-10x)` |
| `in_cubic(x)` | `x³` — exits |
| `ease(x)` | smoothstep `x²(3-2x)` |
| `hsh(a,b=0)` | `frac(sin(a*12.9898+b*78.233)*43758.5453)` deterministic noise |
| `jpt(p,seed,tq,amp=2.6)` | vertex boil displacement |
| `_cut(pts,p)` | arc-length truncation of a polyline |
| `poly(dr,pts,col,w=9,p=1,seed,tq,amp=2.6,closed=False,fill=None)` | jittered, drawable polyline + round caps |
| `circ(dr,c,rad,...,segs=34,start=-90)` | hand-drawn circle as a polygon |
| `arc(dr,c,rad,a0,a1,...,segs=22)` | hand-drawn arc |
| `box(dr,x0,y0,x1,y1,...)` | closed 4-point poly |
| `squiggle(dr,x0,y,x1,...,n=9,h=11)` | zigzag underline |
| `arrow(dr,a,b,...,curve=0.25)` | quadratic Bézier (16 samples) + 2 head strokes at p>0.85 |
| `ft(path,size,var)` | cached font loader |
| `text_img(txt,size,col,fontp,rot,shadow,var,outline)` | flat text raster + 9 px glow at 50 % |
| `put(cv,im,cx,cy,scale,alpha,reveal)` | centred composite with optional left→right reveal mask |
| `write(cv,txt,cx,cy,size,col,fontp,rot,p,scale,pop,...)` | convenience: `pop=True` → out_back scale-in, else reveal-wipe |
| `rot2(a,v)` | 2-D rotation |
| `stick(dr,x,y,s,pose,col,w=10,seed,tq,p,face)` | full FK figure, returns `{head,hand_l,hand_r,hip,neck,hr}` |
| `pose_*(t)` | 9 pose generators (table in §8.4) |
| `coin(dr,x,y,r,tq,seed,p,col,spin)` | ellipse squashed by `|cos(spin)|` + `$` when wide |
| `laptop(dr,x,y,w_,tq,seed,p,screen=cb)` | lid box + trapezoid base + screen callback |
| `play_btn`, `speech`, `star`, `tick`, `cross`, `_bullet` | props (see §8.5) |
| `make_board()` → `BOARD` | chalkboard texture |
| `VIGN` | `clip(1.06 - 0.45·r^2.0, 0, 1.1)` |
| `GRAIN` | `N(0,1)` at half res, nearest-doubled at use |

### 7.2 `src/stick2.py` — look, VFX, scenes (698 lines)
| Symbol | Spec |
|---|---|
| `ACCENT` | `[RED, CYAN, MINT, PINK, GOLD, GOLD]` |
| `class T3(txt,size,col,fontp,depth=16,dvec=(.45,.95),glow_a=120)` | 3D marker type; `.img`, `.size`, `._ma`, `.sweep(phase,width=.14,strength=215)` |
| `t3(key,*a,**k)` | cached T3 factory (max 50) |
| `w3(cv,obj,cx,cy,p,scale,rot,sq,sweep,alpha,pop)` | animated 3D text placement |
| `wash(t,si,si2,mix)` | animated accent background |
| `build_doodles()`/`DOODLES`, `build_grid()`/`GRID` | parallax layers |
| `speed_lines(cv,p,col,n=30,inner=420,cx,cy)` | radial comic lines, alpha 150p, blur 1.6 |
| `shockwave(cv,cx,cy,p,col,maxr=620,w=12)` | `r=maxr·out_expo(p)`, alpha `220(1-p)^1.5`, 2nd ring at .72r |
| `comic_burst(cv,cx,cy,p,txt,col,size=78,r=200)` | 18-point star + word, k=out_back(min(1,2.2p)), fades after .7 |
| `dust(cv,x,y,p,n=12,col,spread=120)` | puff, radius `9(1-p)`, rises `40p` |
| `sparkle(cv,x,y,p,col,s=26)` | 4-ray cross, size `s·sin(πp)` |
| `flame(d,x,y,s,t,col,p)` | 7-point flame, width `1+0.12 sin(9t)` |
| `crown(d,x,y,s,col,p)` | 7-point crown |
| `badge(cv,txt,x,y,p,col,size=40)` | pill (r26, fill α46, outline α235), pops, floats −60p, fades after .6 |
| `trail_stick(d,...,n=2,dt=.055)` | ghost trails then the real figure |
| `highlighter(d,x0,x1,y,p,col,h=46)` | marker swipe, alpha 60 |
| `circle_mark(d,cx,cy,rx,ry,p,col,w=8,tq)` | wobbling hand-drawn ellipse |
| `hud(cv,t,tq)` | progress bar + chapter dots + STEP badge + watermark |
| `scene1..scene6(cv,lt,tq)` | shot content (§9) |
| `trans_mask(kind,p)` | 5 wipe masks (§10) |
| `TKIND=[0,1,2,3,4]`, `TDUR=0.34` | transition assignment |
| `bloom(arr,amount=.5,thr=168)` / `grade(arr)` / `camera(t)` | post (§11) |
| `scene_layer(si,t,tq,lt=None)` | renders one scene to a transparent layer |
| `render(i)` / `main()` | frame assembly / ffmpeg pipe |

### 7.3 `src/make_audio4.py` — sound engine (303 lines)
`lp/hp/bp` (4th-order Butterworth via `sosfilt`) · `_ir`, `IR`, `IR_BIG`, `rev(x,mix,big)` ·
`add(x,at,pan,g)` (equal-power pan into the stereo bed) ·
instruments `kick, sub808, shaker, woodblock, clap, marimba, pizz, whistle` ·
SFX `pencil, pop, ding, boing, swish, impact, riser, rev_cym, coin_clink, register, firework,
typing(n,start,g), tick_tock(start,count,step,g)` ·
`BPM=112`, `SPB=0.5357`, `NOTE(n)=440·2^((n-9)/12)`,
`CHORDS=[(-12,[0,4,7]),(-7,[7,11,14]),(-10,[3,7,10]),(-5,[5,9,12]),(-7,[7,11,14]),(-12,[0,4,7])]`,
`MELODY=[0,4,7,12,11,7,4,2]`.

---

# §8 — VISUAL LANGUAGE SPEC

### 8.1 Palette
| Token | RGB | Use |
|---|---|---|
| CHALK | 238,242,250 | all primary strokes & body text |
| GOLD | 255,201,60 | money, step numbers, CTA, highlights |
| CYAN | 70,224,255 | skill/learning, questions, links |
| MINT | 124,255,178 | success, ticks, counters, follow box |
| RED | 255,107,107 | pain/problem, play buttons, circle-marks |
| PINK | 255,140,200 | brain/creativity, poster sample |
| board | 16,20,28 | background base |
| furniture | 150-170,162-182,185-205 | desks, frames, calendar chrome |
| ground | 120,132,155 | floor lines |

### 8.2 Type scale (doodle)
| Role | Font | Size | Notes |
|---|---|---|---|
| Scene title | Permanent Marker (3D, depth 14) | 88–92 | rot −1.5°, sweep |
| Hook / CTA | Permanent Marker (3D, depth 16–20) | 110–118 | rot −2.5°/+1.5° |
| Step number | Patrick Hand | 150 | gold, inside a 98 px circle |
| Big stat | Permanent Marker (3D, depth 10–14) | 62–84 | counters, "2h DAILY", "10 DM / DAY" |
| Body / bullets | Patrick Hand | 46–58 | checklists, labels |
| Chat / micro | Patrick Hand | 32–40 | bubbles, badges, watermark |

### 8.3 Layout grid (1080×1920)
```
y 96-108   progress bar          y 140-214  STEP badge (right)
y 290      scene title row       y 520-860  content column A (bullets / recap)
y 620-900  content column B (brain / clock / phone)
y 990-1700 main stage (calendar, frames, desk, figures)
y 1530-1790 ground line (per scene)      y 1828  watermark
safe margins: 60 px sides, never place a glyph within 40 px of an edge
```

### 8.4 Pose table (degrees)
| Pose | lean | head | al / el | ar / er | ll / kl | lr / kr |
|---|---|---|---|---|---|---|
| idle | 2·sin.7t | 3·sin.9t | 18+b / 10 | −18−b / −10 | 10 / 2 | −10 / 2 |
| sad | 8 | 16+2sin1.4t | 14 / 20 | −14 / −20 | 8 / 4 | −8 / 4 |
| type | 12 | 6+2sin2.6t | 68+osc / 42 | 66−osc / 44 | 96 / −92 | 88 / −86 |
| cheer | −3 | −6 | 168+a / 12 | −168−a / −12 | 20 / 6 | −20 / 6 |
| point(up,left arm) | −2 | −4 | 150+j / 6 | −16 / −12 | 11 / 3 | −11 / 3 |
| think | 4 | 10+sin t | 16 / 14 | −52 / −108 | 10 / 3 | −10 / 3 |
| walk | 4 | 2 | 26 sinφ / 18 | −26 sinφ / −18 | 30 sinφ / max(0,26 sin(φ+1)) | mirrored(φ+4) |
| shake | 5 | 4 | 18 / 12 | −74−j / −14 | 11 / 3 | −11 / 3 |
| dance | 10 sinφ | 8 sinφ | 120+40 sinφ / 30 | −120−40 sin(φ+2) / −30 | 18+14 sinφ / 8 | mirrored(φ+3) |

`b=4 sin2.2t` · `osc=7 sin13t` · `a=14 sin6.5t` · `j=5 sin5t` (point) / `8 sin9t` (shake) · `φ=7t…7.5t`

### 8.5 Prop geometry
`coin` ellipse `rx=|cos(spin)|·r`, stroke 7, `$` at 1.5r when `rx>0.45r` ·
`laptop` lid `w×0.62w` + base trapezoid 1.24w, screen callback at 0.8w×0.41w ·
`play_btn` box `2s×1.4s` + triangle ·
`speech` 7-point outline, tail 44 px below the baseline ·
`star` 10-point, inner 0.45 ·
`tick` 3-point check (−s,0)→(−.25s,.7s)→(s,−.8s) ·
`cross` two strokes drawn sequentially (`p*2`, `p*2−1`) ·
`_bullet` tick at x + Patrick Hand 58 at x+190.

### 8.6 Motion grammar
| Event | Curve | Duration |
|---|---|---|
| Title / number entry | `out_back(p,2.4–2.6)` + squash | 0.22–0.30 s |
| Prop draw-on | linear `p` over arc length | 0.26–0.50 s |
| Bullet reveal | tick `clamp(2p)` then text wipe `(p−.3)/.5` | 0.60 s |
| Card/frame pop | `out_back(2.2)` + squash `1+0.25(1−1.6p)` | 0.50 s |
| Slide-in | `out_expo` from ±240–540 px | 0.34–0.45 s |
| Exit | `in_cubic` + blur | 0.27–0.42 s |
| Idle float | `sin(1.6–2.4 t)` ±8–16 px | continuous |
| Beat bump | `+0.01·exp(−6·beat_phase)` zoom | every 0.536 s |

---

# §9 — SHOT LIST (literal, scene by scene)

### S1 · 0.00–5.57 · HOOK (accent RED)
| t (local) | Element | Exact parameters |
|---|---|---|
| 0.00 | ground line | `poly[(100,1530),(980,1530)] col(120,132,155) w7 p=lt/.22` |
| 0.00–0.85 | walk-in | `x = −160 + 700·out_cubic(lt/.85)`, `trail_stick(... 600 px, pose_walk, 2 trails)`, dust at `x−80` |
| 0.85→ | idle sad | `stick(460,1530,600,pose_sad(lt−.85), face='sad')` |
| 0.50 | 3D title | `T3('JEEB KHALI?',118,CHALK,depth16)` at (540,330) rot −2.5°, squash `.14(1−p)`, sweep from 1.1 s |
| 0.50–0.95 | speed lines | `strength=(1−(lt−.5)/.45)·0.8`, 26 rays, inner 520 |
| 0.95 | red squiggle | `squiggle(250,420,830,RED,9)` |
| 1.10 | rain cloud | 3 circles at (460±70/0/+72, 760±16) r 56/70/52, col (168,178,200) |
| 1.45→ | rain drops | 5 drops, `dp=((1.3t+0.27k)%1)`, length 30 px, CYAN |
| 1.20 / 1.30 | empty pockets | two arcs r26 at hip ±54, +30 y |
| 1.50 | speech bubble | `speech(808,900,310,190,tail(−.4,1))` |
| 1.75 | 3D "Rs 0" | 92 px RED depth 12 at (808,890) rot −4° |
| 1.90 | sparkle | at (960,820) RED s30 |
| 1.90/2.15/2.40 | three "?" | 112 px CYAN at (220,720)/(890,580)/(300,500), bob `16 sin(2t+i)`, rot −10/−1/+8 |
| 2.90 | shockwave + 3D "PURA PLAN" | ring maxr 520 w14; text 100 px GOLD depth 18 at (540,1690) rot 1.5° |
| 3.30 | "4 STEPS ME" | 62 px MINT Patrick Hand at (540,1800) |
| 3.50 | badge "FREE" | MINT 38 at (870,1660) |
| 3.60 / 3.75 | flames | GOLD at (150,1700) r44, RED at (930,1700) r44 (phase +1) |

### S2 · 5.57–12.87 · STEP 1 — SKILL SEEKHO (accent CYAN)
| t | Element | Parameters |
|---|---|---|
| 0.00 | number "1" | Patrick Hand 150 GOLD (150,296) rot −6°, pop `lt/.22` |
| 0.05 | circle | `circ((150,290),98,GOLD,8,p=(lt−.05)/.28, segs30, amp3.0)` |
| 0.07 | 3D title | `T3('SKILL SEEKHO',92,CHALK,depth14)` at (650,290) rot −1.5°, sweep 0.9→2.2 |
| 0.08–0.25 | desk + legs + ground + stool | desk `(220..860, 1330, h22)`, legs to y1520, stool `(240..390,1403..1520)` |
| 0.10 | seated figure | `stick(315, 1385+0.42·470, 470, pose_type(lt))` |
| 0.80 | laptop | `laptop(630,1330,240)` with pulsing play button `46+4 sin(7t)` |
| 1.00→ | code particles | `</>`, `*`, `~` rising 180 px, fade `1−sp` |
| 1.10 | brain outline | `circ((830,620), 92+5 sin(4t), PINK, 8, segs26)` |
| 1.40–4.20 | brain fill | 5 arcs `(830−42+21i, 610+26·(i%2))` r27, `p=(bp−0.17i)·3`; `%` readout at (830,762) |
| 1.60→ | knowledge sparks | 6 sparkles spiralling `r=230(1−sp)`, angle `−2.2+0.5k` |
| 1.5/1.9/2.3/2.7 | checklist | x150, y 520/625/730/835 + sparkle + "+1" badge at x560 |
| 3.30 | brain→head arrow | `arrow((760,760),(390,1120),PINK,7,curve .22)` |
| 4.30 | highlighter + line | bar (230→850, y1680, h54, CYAN α60) + "YouTube = FREE university" 58 px |

### S3 · 12.87–19.59 · STEP 2 — ROZ 2 GHANTE (accent MINT)
| t | Element | Parameters |
|---|---|---|
| 0.00/0.05/0.07 | number "2" (rot +5°), circle, 3D title `ROZ 2 GHANTE` 88 px | as S2 |
| 0.10 | clock face | `circ((320,640),158,CYAN,10,segs40)` |
| 0.32→ | 12 ticks | staggered `0.022·i`, from r128 to r148 |
| 1.10–3.30 | hands | hour `720°·p` at 0.55r GOLD w10; minute `12×` at 0.78r + 3 ghost trails at −0.22 rad, brightness 0.30/0.22/0.14 |
| 1.40 | "2h DAILY" | 3D GOLD 62 depth10 at (320,862) |
| 0.18–0.25 | mini desk | ground `(640..1010, 870)`, desk `(700..960, 720..734)` |
| 0.18 | typing figure | 330 px at x726, `pose_type(1.25·lt)` |
| 1.00 | small laptop | `(912,720,118)` |
| 2.20→ | sweat | 3 drops r8 cycling 1.2 s |
| 0.55 | calendar frame | `(227..933, 936..1632)` |
| 1.30→ | 30 cells | origin (265,990), cell 112, box 80×72 |
| 1.60+0.1k | X marks | MINT w7, each with a dust puff on the active cell |
| 1.90 | counter | `"{hrs} HOURS"` 3D MINT 84 at (540,1740), wobble `0.1 sin(14t)` until 60 |
| 4.50 | shockwave + badge | ring maxr 560 + "CONSISTENCY = POWER" |

### S4 · 19.59–24.30 · STEP 3 — SAMPLE BANAO (accent PINK)
| t | Element | Parameters |
|---|---|---|
| 0.00/0.05/0.07 | number "3" (rot −4°), circle, 3D title `SAMPLE BANAO` 88 px | as S2 |
| 0.00 | ground | y1560 |
| 0.06 | painter | 470 px `pose_point(up, left arm)` + 1 trail, gold brush 70 px from the hand |
| 0.30 / 0.75 / 1.20 | three frames | x 230/540/850, y 700(+36 odd) + `8 sin(1.6t+i)`, half-size 125×150, pop `out_back(2.2)` with squash `1+0.25(1−1.6p)` |
| +0.45 each | frame contents | ① circle r50 PINK + mountain polyline MINT ② play button s58 RED ③ CYAN bar + 3 lines |
| +0.50 each | sparkle + dust | sparkle at (x+110, y−150), dust at (x, y+160) |
| +0.60 each | labels | POSTER / REEL / WEBSITE, 46 px GOLD at y+196 |
| 2.50 | "DEGREE nahi," | 70 px Patrick Hand (540,1690) rot −1° |
| 2.80 | red circle-mark | `circle_mark(430,1690,180,54,RED,7)` |
| 3.00 | 3D "KAAM bolta hai!" | 82 px GOLD depth14 (540,1800) rot +1°, sweep 3.4→4.4 |
| 3.00–3.70 | speed lines | GOLD, 24 rays, inner 560, centred on the line |

### S5 · 24.30–30.82 · STEP 4 — SERVICE BECHO (accent GOLD)
| t | Element | Parameters |
|---|---|---|
| 0.00/0.05/0.07 | number "4" (rot +6°), circle, 3D title `SERVICE BECHO` 88 px | as S2 |
| 0.10 | phone body | `(320..760, 490..1110)` + speaker line at y520 |
| 1.30 / 2.00 / 2.70 | chat bubbles | y 630/780/930, slide from ±240 px with `out_back(1.8)`, box 360×104, text 32 px; 3rd gets a sparkle |
| 3.00 | 3D "10 DM / DAY" | 72 px MINT depth12 (540,1190) rot −1.5° + speed lines 3.0–3.6 |
| 3.40/3.65/3.90 | platform boxes | x 230/540/850, y1300-1400, width `±130·out_back(2.2)`, labels 46 px GOLD |
| 0.00 | ground | y1790 |
| 4.20 | handshake pair | two 400 px figures at ±180 px, `pose_shake`, second mirrored |
| 4.60 | hand link + burst | gold line between hands; `comic_burst('DEAL!',72,r180)` + shockwave maxr 480 at (540,1600) |
| 4.85+0.14k | 5 coins | from y1430 falling 260 px, r34, spin `5t+i`, each with a sparkle |

### S6 · 30.82–37.00 · CTA (accent GOLD)
| t | Element | Parameters |
|---|---|---|
| 0.00→ | money rain | 22 coins, speed `0.5+0.8·hsh`, y `((0.4·sp·t + hsh)%1.18)·2220 − 150`, r 26–46, spin `4t+i`, 40 % get sparkles |
| 0.00 | dancing figure | 470 px `pose_dance`, 2 trails (dt .05), bounce `30·|sin(5.2t)|`, dust on landing |
| 0.00 / 0.16 | 3D titles | `AAJ HI SHURU` 110 px CHALK depth18 (540,420) rot −2°; `KARO!` 112 px GOLD depth20 (540,548) rot +1.5° |
| 0.30–1.10 | speed lines + shockwave | 30 rays inner 540; ring maxr 760 w16 |
| 0.85 | gold squiggle | (300→780, y628) |
| 1.2/1.5/1.8/2.1 | recap row | SKILL/TIME/SAMPLES/SELL at x 180/420/660/900, y790 + ticks at y858 + sparkles |
| 2.20 | crown | r46 above the head, follows the bounce |
| 2.60 | follow box | `(170..910, 960..1105)` MINT + 3D `FOLLOW = PART 2` 62 px, pulse `1+0.03 sin(7t)` |
| 2.90+0.09k | 9 fireworks | fan `−π/2+(i−4)·0.3`, `r=480·out_expo`, star size `24(1−0.4cp)` |
| 3.30 | save line + flames | "SAVE karo, bhool jaoge!" 54 px + flames at x230 / x850 |
| 4.60 | final burst | `comic_burst("LET'S GO!",70,r210)` at (540,1450) |

---

# §10 — TRANSITION ENGINE (deep dive)

```python
TDUR = 0.34                       # seconds, placed in [cut, cut+TDUR)
TKIND = [0, 1, 2, 3, 4]           # one per cut: ink, paint, eraser, zip, whip
MW, MH = 540, 960                 # masks are built at half resolution
```
| Kind | Mask formula (half-res grid) | On-canvas decoration |
|---|---|---|
| 0 ink iris | `r < p^1.25 · 700 · (1 + .16 sin5θ + .08 sin(9θ+1.3))`, centre (0.5MW, 0.62MH) | accent ring at `p^1.25·1400`, width 10 |
| 1 paint | 7 columns, col c: `y < MH·clamp((p−.05c)/.72)·1.3 + 40 sin(2.1c)` | — |
| 2 eraser | `x < (1.3p−.15)·MW + 26 sin(.06y) + 18 sin(.013y+2)` | 12 px chalk edge line at `(1.3p−.15)·W` |
| 3 zip | `|y − MH/2| < p^0.85 · 0.75·MH` | — |
| 4 whip | `0.6x + 0.4y < 1.15p(0.6MW + 0.4MH)` | — |

All masks: `Image.fromarray(m*255,'L').filter(GaussianBlur(5)).resize((1080,1920))`.
Composite: `Image.composite(new, old_frozen, mask)`.

**Per-cut camera FX** (`Δ = t − cut`, active for `−0.14 ≤ Δ ≤ 0.24`, `k = clamp(1 − |Δ|/0.19)`):
```
flash = 0.34·k²      aberr = 9·k      smear = 14k (Δ<0) / 7k (Δ≥0)
shake += 26k·sin(88Δ), 18k·cos(70Δ)   rot += 1.4k·sin(52Δ)
glitch = 0.75k when |Δ| < 0.07  → 7 slices, height 10-60 px, dx ~ N(0,38)·glitch, G-channel roll 8·glitch
```

**Golden rule:** the incoming scene must have visible content by `p≈0.3` → every scene's number/title/
ground appear within 0.02–0.10 s of its start (that is why all openings were re-timed to `/.22–.30`).

---

# §11 — CAMERA & POST (exact order and math)

```python
zoom  = 1.025 + 0.05·(lt/scene_len)^1.05  + 0.01·exp(−6·beat_phase)      # beat = 112 BPM
shx   = 7 sin(2.0t) + 4 sin(5.1t + 1)        shy = 6 sin(1.6t + .5) + 3 sin(4.3t + 2)
rot   = 0.3 sin(1.1t)                         (+ per-cut terms from §10)

post(frame):
  1 smear   : mean of 5 copies rolled by (k−2)·smear on axis=1
  2 camera  : resize to (1080·zoom, 1920·zoom) → rotate(rot) → crop centred + (shx, shy), clamped
  3 aberr   : R = roll(R, +s, axis=1) ; B = roll(B, −s, axis=1)
  4 glitch  : random horizontal slice rolls + green-channel vertical roll
  5 bloom   : t = clip(down4 − 168, 0) · (255/87) ; blur 15 and 32 ; up4 ; frame += (0.6·b1+0.5·b2)·0.5
  6 grade   : lum = .299R+.587G+.114B ; frame += (1−lum)·(−3,1,11) + lum·(13,5,−7)
              x = clip(frame/255) ; x = 0.3·x²(3−2x) + 0.7·x ; frame = 255x
  7 vignette: frame *= clip(1.06 − 0.45 r^2.0)
    flash   : frame += (255,248,232)·flash
    jitter  : roll ±2 px from the 2-frame hash
    grain   : frame += N(0,1)·4.5
  8 clip → uint8
```

---

# §12 — AUDIO ENGINE (full math)

### 12.1 Core
```
SR 48000 · stereo float buffers L,R of 37·SR samples
add(x, at, pan, g): equal-power → L += x·cos(pan·π/2)·1.2·g ; R += x·sin(pan·π/2)·1.2·g
filters: 4th-order Butterworth via scipy.signal.butter(..., output='sos') + sosfilt
reverb IR: noise·exp(−decay·τ), low-passed (damp), 12 ms silent pre-delay, normalised ·0.5
          IR     = _ir(1.6 s, decay 5.0, damp 7 kHz)       → rooms/props
          IR_BIG = _ir(2.6 s, decay 3.2, damp 6 kHz)       → impacts/cymbals
```
### 12.2 Instrument recipes
| Sound | Math |
|---|---|
| kick | `f = 46 + 95·e^(−32t)` sine · `e^(−8t)`, `tanh(1.6x)`, 0.42 s |
| sub808 | `f = f₀ + (slide−f₀)e^(−9t)`, + 16 % 2nd harm, env `min(1,55t)·e^(−1.6t)`, tanh |
| shaker | HP 7 kHz noise · `e^(−45t)`, 70 ms |
| woodblock | `sin(2πft) + .5 sin(2π·2.4ft)` · `e^(−38t)` + 18 % reverb |
| clap | 4 BP(1.2–5.2 kHz) noise taps at 0/10/21/30 ms, `e^(−26t)`, 26 % reverb |
| marimba | `sin + .4·4th·e^(−18t) + .2·9.2nd·e^(−30t)`, env `e^(−6.5t)·min(1,900t)` |
| pizzicato | 2 saws ±0.4 % detune → LP 1.8 kHz → `e^(−11t)` |
| whistle | sine, 5.5 Hz / 1.2 % vibrato, soft attack `min(1,14t)`, release `min(1,9(d−t))` |
| pencil | BP 1.8–9 kHz noise × `(.55+.45 sin(2π(38+25τ)t))` × `sin(πτ)^0.8` |
| pop | `f = f₀(1 + 2.4 e^(−55t))`, `e^(−26t)` |
| ding | partials 1 / 2.01 / 3.01, decays 5 / 8 / 12, 35 % reverb |
| boing | `f = 420 e^(−4t) + 90`, vibrato `1 + .5 sin(22πt)e^(−3t)`, `e^(−6t)` |
| swish | 18 chunks, centre `380·26^τ` (280 Hz→9.9 kHz), BP ×0.6/×1.75, window `sin(πτ)^1.2` |
| impact | `(78 e^(−3.4t)+33) Hz` boom + 36 Hz sub + HP 2.6 kHz crack ×0.45 + LP 160 Hz rumble ×0.6, 35 % big reverb, tanh |
| riser | `f = 170·14^(τ^1.3)`, + BP 1.5–12 kHz noise τ³, tremolo 5→25 Hz |
| rev_cym | HP 5 kHz noise · τ³ + 40 % big reverb |
| coin_clink | partials 1 / 1.9 / 3.4, decays 9 / 13 / 18 |
| register | bell (1318+1760+2093 Hz, `e^(−6t)`) + BP 0.5–4 kHz `e^(−40t)` ka-ching |
| firework | HP 3.5 kHz crack `e^(−30t)` + HP 6 kHz tail `e^(−5t)`·0.35 + 40 % big reverb |

### 12.3 Bed generator (loop over `SPB = 0.5357 s`)
```
beat = i % 4
kick  (0.78 on beats 0,2 ; 0.50 otherwise)
clap  on beat 2
shaker ×2 per beat, pan 0.38 / 0.62
sub808 on beat 0 at chord root / 2
pizzicato on off-beats of even bars, pan 0.35
marimba triad as a 16th arpeggio, pan 0.35 → 0.65
woodblock on beat 3.75 of every 4th bar, pan 0.70
whistle: 4 notes per scene from MELODY starting at scene+0.8 s
```
### 12.4 Complete SFX cue sheet (offsets from each scene start)
```
EVERY CUT  : riser −0.85 | rev_cym −0.80 | swish −0.30 | impact 0.00 | sub808 0.00 |
             swish +0.02 | pencil +0.06 | pop +0.10
GLOBAL     : impact at 0.00 (film open), pencil at 0.50
S1 : pop 1.10, 1.50 · ding 1.75 · pop 1.95, 2.20, 2.45 · impact 2.90 · ding 2.95 · swish 3.60
S2 : typing ×16 from 0.70 · (pop + ding) at 1.50 / 1.90 / 2.30 / 2.70 · pencil 1.10 ·
     coin_clink ×7 at 1.60 + 0.40k · pencil 4.35 · ding 4.60
S3 : tick_tock ×10 from 1.00 step 0.45 · pencil ×30 at 1.62 + 0.10k (+ pop every 5th) ·
     typing ×12 from 2.30 · impact 4.50 · ding 4.55
S4 : (pencil, pop +0.40, ding +0.55) at 0.35 / 0.80 / 1.25 · swish 2.95 · impact 3.05
S5 : (pop, ding +0.12) at 1.30 / 2.00 / 2.70 · pop 3.45 / 3.70 / 3.95 · swish 2.95 ·
     boing 4.25 · impact 4.62 · register 4.70 · coin_clink ×5 at 4.90 + 0.16k
S6 : swish 0.05 · impact 0.30 · sub808 0.30 · coin_clink ×12 at 0.30 + 0.36k ·
     boing ×9 at 0.55 + 0.58k · (pop, ding) at 1.20 / 1.50 / 1.80 / 2.10 · pencil 2.60 ·
     ding 2.70 · firework ×7 at 2.95 + 0.12k · rev_cym 4.30 · impact 4.60
```
### 12.5 Master chain
```
pump[n] = min over beats of 1 − 0.3·e^(−7τ)(1−τ^0.4)   (τ = position in a 0.30 s window)
mix *= pump·0.8 + 0.2
mix = HP(mix, 32 Hz)
mid/side: side += HP(side, 3 kHz)·0.45    → wider highs, mono-safe lows
mix = tanh(1.1·mix)/tanh(1.1)             → tape-ish glue
mix /= peak ; mix *= 0.93 ; write 16-bit WAV
```

---

# §13 — VOICE PROCESSING & MUX (literal commands)

```bash
# 1. trim each clip
ffmpeg -y -i assets/sN.mp3 -af "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,\
areverse,silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,areverse" build/vsN.wav

# 2. build the 37 s VO bed (per-clip tempo + slot delay in ms)
ffmpeg -y -i build/vs1.wav -i build/vs2.wav -i build/vs3.wav -i build/vs4.wav -i build/vs5.wav -i build/vs6.wav \
-filter_complex "\
[0:a]atempo=1.446,adelay=300|300[a0];[1:a]atempo=1.351,adelay=5617|5617[a1];\
[2:a]atempo=1.441,adelay=12917|12917[a2];[3:a]atempo=1.525,adelay=19638|19638[a3];\
[4:a]atempo=1.484,adelay=24352|24352[a4];[5:a]atempo=1.487,adelay=30873|30873[a5];\
[a0][a1][a2][a3][a4][a5]amix=inputs=6:duration=longest:normalize=0,highpass=f=95,\
equalizer=f=250:t=q:w=1:g=-2.5,equalizer=f=4000:t=q:w=1.2:g=4,\
acompressor=threshold=-20dB:ratio=5:attack=5:release=110:makeup=5,alimiter=limit=0.95,\
apad,atrim=0:37,aresample=48000[a]" -map "[a]" build/vo37.wav

# 3. final mux with ducking + loudness
ffmpeg -y -i build/stick2_silent.mp4 -i build/music4.wav -i build/vo37.wav -filter_complex "\
[2:a]apad,atrim=0:37,asetpts=N/SR/TB[vof];[vof]asplit=2[vo][sc];[1:a]volume=0.9[mus];\
[mus][sc]sidechaincompress=threshold=0.030:ratio=8:attack=6:release=260:makeup=1.8[duck];\
[duck][vo]amix=inputs=2:duration=longest:dropout_transition=0:weights=1 1.4,\
loudnorm=I=-11:TP=-1.0:LRA=10,alimiter=limit=0.97,apad,atrim=0:37,aresample=48000[a]" \
-map 0:v -map "[a]" -c:v libx264 -profile:v high -preset slow -crf 23 -maxrate 7M -bufsize 12M \
-pix_fmt yuv420p -g 60 -c:a aac -b:a 192k -movflags +faststart master.mp4

# 4. size pass (14 MB, preview-friendly)
ffmpeg -y -i master.mp4 -c:v libx264 -profile:v high -level 4.0 -preset slow -crf 27 \
-maxrate 2800k -bufsize 5600k -pix_fmt yuv420p -g 60 -c:a aac -b:a 160k -movflags +faststart final.mp4
```
10 s reel variant: single VO clip, `atempo=1.40`, `adelay=320`, mix weights `1 : 1.35`,
`loudnorm I=-12` (reel) / `-11` (doodle).

---

# §14 — THE CINEMATIC REEL (Look A) — full spec

| Block | Spec |
|---|---|
| Canvas / rate | 1080×1920 @ **60 fps**, 600 frames, 10.000 s |
| Background | 300×533 NumPy field: vertical base (13,11,30)→(2,2,7) + glows blue (24,92,240)·0.42 r140, magenta (196,40,152)·0.26 r118, amber (255,152,30)·0.21 r95 on Lissajous paths → bicubic |
| Grid | horizon 0.70H, 22 depth lines with `y = hor + (H−hor)(1/z)·0.055`, 23 radial lines to the vanishing point, blur 2.2 |
| Particles | 90 bokeh, radius 2–11, alpha ≤125, blur 5, half-res |
| Type | Montserrat Black/ExtraBold; per-char tracking 2–12; 3-stop gradient; glow blur 30–46 at α165; dark stroke 4–6; extrusion depth 10–22 with `dvec (.42,.9)`; sweep band identical to §2.6 |
| Cards | 900×780 glass: shadow blur 34, fill α16, accent outline blur 26, 3 px border, top highlight line |
| Icons | bulb / clock / rocket drawn as neon vectors + blurred duplicate at α0.8, 300 px progress ring |
| Counter | `$0 → $1,250` via `out_expo` over 1.05 s, 184 px Black, depth 18, motion blur 3 px while rolling, flare at the peak |
| Beats | 0.00 hook · 2.85 step 1 · 4.95 step 2 · 7.05 money · 8.55 CTA |
| Transitions | flash 0.5k^2.2, smear 17k/8k, aberration 12k, glitch 0.75k inside ±0.07 s |
| Camera | zoom `1.02 + 0.055(lt/dur)^1.1`, handheld sines, rot `0.25 sin(1.3t)`, 126 BPM bump |
| Audio | 126 BPM trap: kick/clap/snare, swung 16th hats (±0.012 s), 808 glides, A-minor pluck arpeggio `[a2,e2,c2,g2,a2,e,g,c2]`, pads; risers + reverse cymbals + impacts at every cut; coin sparkles on the counter |
| Encode | crf 23 master → crf 24 / maxrate 6M size pass → 8.8 MB |

---

# §15 — QA PROTOCOL (run before every delivery)

```bash
# duration + streams
ffprobe -hide_banner final.mp4 2>&1 | grep -E "Duration|Stream"
# frame probes at every cut and mid-scene
for T in 0.5 2.9 5.6 5.75 9 12.9 13.1 16 19.6 19.8 22 24.3 24.5 28 30.8 31.1 34 36.5; do
  ffmpeg -y -ss $T -i final.mp4 -frames:v 1 -vf scale=405:-1 qa_$T.png; done
# loudness
ffmpeg -i final.mp4 -af loudnorm=print_format=summary -f null -   2>&1 | tail -12
```
Checklist: duration exact · no empty frame · no edge clipping · no HUD collision · ticks/pops land on
their sound · loudness −11…−12 LUFS, TP ≤ −1 · size ≤ 15 MB · `+faststart` · sources in `src/`.

---

# §16 — BUG MUSEUM (every failure encountered + the fix)

| # | Error / symptom | Cause | Fix |
|---|---|---|---|
| 1 | `ValueError: could not broadcast input array from shape (269,3) into shape (269,969,3)` | gradient built with `ys[:,None]` | `ys[:, None, None]` |
| 2 | `ValueError: images do not match` in `Image.paste` | stroke pass used `pad = 90 + stroke`, inner pass `pad = 90` | constant `pad = 96` for both |
| 3 | `ValueError: x1 must be greater than or equal to x0` at frame ~300 | animated widths reached 0 (`underline`, bars) | `max(4, …)` / `max(4.0, …)` |
| 4 | Transition ring far smaller than the revealed area | mask radius in half-res px, ring drawn in full-res px | fractional geometry; ink: mask 700 ↔ ring 1400 |
| 5 | Wipe revealed a blank scene | incoming scene rendered at `lt≈0` (nothing drawn yet) | wipe AFTER the cut + freeze the outgoing frame + speed up all scene openings to 0.02–0.10 s |
| 6 | First cinematic look washed out / hazy | background glows and text halos too strong | base (13,11,30)→(2,2,7), glow amps 0.42/0.26/0.20, halo ×1.7, vignette `1.10−0.78r^1.9` |
| 7 | Text clipped at frame edges | font sizes too large | MONEY 300→268, ONLINE 176→170, SERVICE BECHO 112→96, START KARO 150→132 |
| 8 | 13 MB / 27 MB files would not preview | bitrate too high for the in-app player | second encode pass to ≤15 MB + `+faststart` |
| 9 | All sources vanished next session | code lived in `build/` (snapshot-excluded) | move to `src/`; `build/` only for intermediates |
| 10 | `ModuleNotFoundError: No module named 'imageio_ffmpeg'` | pip installs are not snapshotted | reinstall at session start |
| 11 | `ModuleNotFoundError: No module named 'stick'` | module was in the wiped `build/` | rebuilt as `src/stickbase.py`, imports updated |
| 12 | Paint-wipe `could not broadcast (960,77) into (960,78)` | column widths from `int(c*cw)` were uneven | precompute `bounds = [round(i*MW/cols)]` and slice with them |
| 13 | Head overlapping labels / text over the brain | layout by feel | fixed y-grid per scene (§8.3) + frame probes before the full render |
| 14 | Urdu text rendered as boxes | no Arabic-script font installed | all on-screen copy in Roman-Urdu/English |
| 15 | VO 13.8 s vs a 10 s slot | script too long for the format | global `atempo 1.40–1.45` + per-scene clips |

---

# §17 — EXTENSION RECIPES

| Want | Do exactly this |
|---|---|
| **Your handle** | replace `'@YOURHANDLE'` in `hud()` (stick2) and `render()` (reel); keep ≤ 14 chars so it stays centred |
| **Whiteboard look** | `BOARD` base → `(248,248,244)`, dust alpha → 12, `CHALK` → `(32,34,40)`, chalk-glow blend `.42 → .12`, `VIGN` → `clip(1.02 − 0.25 r²)`, accents → darker (GOLD `(235,150,20)`, CYAN `(0,150,200)`) |
| **All-English copy** | strings live only inside `scene1..scene6`; swap and re-measure widths against the 40 px safe margin |
| **Longer / shorter** | edit `RAW` + `TAIL` in `timeline.py` → both renderer and audio follow; re-check each scene's internal cue times (they are scene-local, so they survive) |
| **1:1 or 16:9** | set `W,H`; multiply every y constant by `H/1920`; re-probe frames; HUD and ground lines need manual nudges |
| **New scene** | add VO clip → extend `RAW`/`TAIL` → write `scene7(cv,lt,tq)` → append to `SCENES` → add an entry to `TKIND` → add its cue block in the audio builder |
| **Different voice/lang** | regenerate clips, measure, apply the re-sync law (§5) — zero picture changes |
| **Captions burned in** | render a caption layer in `hud()` from a `[(start,end,text)]` table using Patrick Hand 46 with a dark rounded plate at y≈1640 |

---

# §18 — FILE MANIFEST

```
/home/user
├── MASTER_PROMPT.md            # v1 spec
├── MASTER_PROMPT_V2.md         # ← this build bible
├── stickman_money_37s_v2.mp4   # 37.000 s · 30 fps · 14 MB · FLAGSHIP
├── stickman_money_37s.mp4      # 37.000 s · doodle v1
├── money_online_reel_v2.mp4    # 10.000 s · 60 fps cinematic
├── money_online_reel.mp4       # 10.000 s · cinematic v1
├── src/
│   ├── timeline.py             #  20 lines · shared timing
│   ├── stickbase.py            # 308 lines · primitives, rig, props, board
│   ├── stick2.py               # 698 lines · 3D type, VFX, 6 scenes, transitions, post, main
│   └── make_audio4.py          # 303 lines · synthesis, arrangement, cues, master
├── fonts/  Montserrat-VF · PermanentMarker · PatrickHand · Caveat-VF
├── assets/ s1..s6.mp3          # raw Urdu VO clips
└── build/  (ephemeral: vsN.wav, vo37.wav, music4.wav, *_silent.mp4, qa frames)
```

# §19 — REPRODUCTION RUNBOOK (command order)

```bash
1  pip install imageio-ffmpeg                       # §3
2  download the 4 fonts                             # §3
3  generate 6 Urdu VO clips → assets/s1..s6.mp3     # §4.1
4  trim + measure → update RAW in src/timeline.py   # §5
5  python3 src/timeline.py                          # verify the table, total == 37.000
6  render sample frames (every cut ±0.1 s)          # §15 — fix layout BEFORE the full run
7  python3 src/stick2.py                            # ≈10 min → build/stick2_silent.mp4
8  python3 src/make_audio4.py                       # ≈4 s  → build/music4.wav
9  build build/vo37.wav                             # §13 step 2
10 mux → master.mp4                                 # §13 step 3
11 size pass → stickman_money_37s_v2.mp4            # §13 step 4
12 run the QA gate                                  # §15
```

# §20 — GLOSSARY
**boil** – deliberate frame-to-frame line wobble that reads as hand-drawn · **draw-on** – revealing a
stroke along its arc length · **sweep** – moving specular band across 3D type · **shockwave** – expanding
ring on an impact · **sidechain duck** – music level pulled down by the voice · **pump** – rhythmic gain
dip keyed to the kick · **LUFS/TP** – loudness and true-peak delivery targets · **faststart** – MP4 moov
atom at the front so players can stream instantly · **safe margin** – 40–60 px no-content border.

---
### ✅ This document + `src/` = the entire system, reproducible end-to-end, with no gaps.
