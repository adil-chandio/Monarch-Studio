# 🧠 MASTER PROMPT — "How To Make Money Online" Viral Video System
### Forensic, zero-gap reproduction spec (10s cinematic reel + 37s stickman explainer)
> Har cheez: pipeline, math, coordinates, timings, synth parameters, ffmpeg commands, bugs & fixes.
> Is file ka **Part 1** copy-paste karne layak master prompt hai. **Part 2–9** uska forensic appendix hai.

---

# PART 1 — THE MASTER PROMPT (copy-paste this)

```
ROLE
You are a senior motion-design engineer + sound designer. You have NO video-generation model and NO
stock footage. You must build broadcast-quality vertical social video 100% procedurally in Python
(PIL + NumPy + SciPy), stream raw frames into ffmpeg, and synthesize ALL audio from scratch (no
copyrighted music, no sample libraries).

GOAL
Produce a vertical 1080x1920 social video on "How to make money online" in TWO formats:
  A) 10 s cinematic motion-graphics reel, 60 fps  (premium neon/3D look)
  B) 37 s stickman / chalkboard doodle explainer, 30 fps (hand-drawn cartoon look)
Both must have: Urdu voiceover, fully synthesized music + SFX, beat-synced editing, and must be
Instagram-Reels / TikTok / YouTube-Shorts ready (H.264 High, yuv420p, +faststart, ~-11 LUFS).

NON-NEGOTIABLE TECHNICAL RULES
1.  Canvas 1080x1920. 10s reel = 60 fps (600 frames). 37s explainer = 30 fps (1110 frames).
2.  Never hold all frames in RAM. Open ffmpeg with
    `-f rawvideo -pix_fmt rgb24 -s 1080x1920 -r FPS -i -` and write each frame's bytes to stdin.
3.  Persist all source code OUTSIDE any folder named build/, dist/, out/, node_modules/, __pycache__
    (those are excluded from workspace snapshots). Use src/. Final .mp4 goes in the project root.
4.  pip packages do NOT persist between sessions: re-run `pip install imageio-ffmpeg` and get the
    binary via `imageio_ffmpeg.get_ffmpeg_exe()`.
5.  Fonts: download once into fonts/ from Google Fonts raw GitHub:
      Montserrat[wght].ttf (variable) – cinematic reel
      PermanentMarker-Regular.ttf, PatrickHand-Regular.ttf, Caveat[wght].ttf – doodle version
    No Urdu/Arabic font is installed, so ALL on-screen text is English / Roman-Urdu; the Urdu lives
    only in the voiceover.
6.  Every timing is derived from the REAL measured voiceover lengths — never guessed.
7.  Target per-frame render cost <= 0.6 s; cache every static asset (text images, coins, cards,
    board texture) in dicts keyed by their parameters.

STAGE 1 — SCRIPT & VOICE
- Write the script in Urdu, split into one clip PER SCENE (not one long file) so each scene's length
  can be derived from its own audio.
- Generate each clip with the same TTS voice. Trim leading/trailing silence with ffmpeg
  `silenceremove` (start_threshold=-45dB) applied forwards and reversed.
- Measure each trimmed clip. Choose a global speed-up (atempo ~1.45 for energetic reel pacing).
- scene_duration[i] = vo_len[i]/tempo + tail[i]  (tail 0.30 s, 0.45 s on the last, +0.30 s lead-in
  on the first). Tune tails so the grand total lands on an exact round number (37.000 s).
- Store the timeline in a shared module (timeline.py) imported by BOTH the renderer and the audio
  builder, so picture and sound can never drift.
- If the VO is regenerated later and lengths change, DO NOT re-time the video: give each clip its own
  atempo = new_len / target_len so it still fits its original slot exactly.

STAGE 2 — LOOK A: CINEMATIC REEL (10 s, 60 fps)
Background: low-res (300x533) NumPy gradient + 3 moving Gaussian glows (blue 24,92,240 / magenta
196,40,152 / amber 255,152,30), bicubic-upscaled to 1080x1920; synthwave perspective grid (horizon at
0.70H, lines advancing with 1/z spacing, vanishing point centred); 70-90 blurred bokeh particles.
Type: Montserrat ExtraBold/Black with per-character letter-spacing, vertical 3-stop gradient fill,
two-pass Gaussian glow halo, drop shadow, dark stroke, and TRUE 3D extrusion (N offset copies of the
glyph mask, each darkened toward the back) plus an animated specular "sweep" band across the glyphs.
Motion: slam-in with out_back overshoot + motion blur that resolves, exit with in_cubic + blur.
Depth: every element has a parallax `depth` factor multiplied by the virtual camera offset.
VFX: per-cut glitch (random horizontal slice displacement + green channel roll), RGB split, horizontal
5-tap motion smear, warm light-leak flash, anamorphic lens streaks on impacts, bloom, filmic grade.
Camera: continuous push-in per scene + handheld sine-noise drift + rotation + 126 BPM beat bump.
Structure (seconds): 0.00 hook, 2.85 step 1, 4.95 step 2, 7.05 money counter, 8.55 CTA, 10.00 end.
Make the INCOMING scene's first elements appear within ~0.1 s of the cut, and the OUTGOING scene exit
only in the last 0.3 s, so no frame is ever empty.

STAGE 3 — LOOK B: STICKMAN / CHALKBOARD (37 s, 30 fps)
Board: procedural chalkboard texture (noise -> blur -> upscale + 900 dust specks + 14 soft smudges),
animated accent colour-wash per scene, parallax doodle layer (46 faint doodles scrolling), faint
graph-paper grid scrolling at a different speed, vignette + grain + 2-frame "paper jitter".
Hand-drawn feel ("boil"): every polyline vertex is displaced by a deterministic hash noise that only
changes every 2 frames (= 15 fps boil) -> jpt(p, seed, tq, amp). Line caps are drawn as circles.
Draw-on reveal: polyline truncation by arc-length fraction p (0..1) -> looks like it is being drawn.
Rigged stick figure: forward kinematics from a hip anchor; proportions relative to total height s:
  head radius .115s, torso .36s, upper arm .19s, forearm .18s, thigh .22s, shin .22s, foot .055s.
  Pose dict = {lean, head, al, el, ar, er, ll, kl, lr, kr} in degrees (0 = straight down).
  Pose library: idle, sad, type, cheer, point(up/right), think, walk (sine cycle), shake, dance.
  Faces: neutral / happy / sad via mouth arc.
3D marker text: same extrusion+glow+sweep technique but with Permanent Marker, dark outline, and a
squash-and-stretch pop (out_back) on entry.
VFX library: speed lines, shockwave rings, comic star burst with word, chalk dust puffs, sparkle
crosses, flames, crown, floating motion-graphics badges, highlighter swipes, hand-drawn circle-marks,
animated underlines, coin rain, fireworks, stickman motion trails (same pose drawn at t-Δ, dimmed).
Transitions (one distinct type per cut, 0.34 s each, placed AFTER the cut): ink-blob iris (angular
wobble), 7-column paint-stroke wipe, noisy eraser wipe, vertical zip, diagonal whip — each composited
as Image.composite(new_scene, frozen_old_scene, mask) + flash + RGB split + smear + shake.
HUD: progress bar with chapter dots, "STEP x/4" badge, @handle watermark.

STAGE 4 — POST CHAIN (identical philosophy for both looks, run per frame, in this order)
  1 horizontal 5-tap motion smear (only near cuts)
  2 zoom -> rotate -> crop (camera: push-in + handheld + shake)
  3 RGB split (roll R +s px, B -s px)
  4 glitch slices (doodle version: only inside ±0.07 s of a cut)
  5 bloom: downscale /4, threshold ~168-172, two Gaussian blurs (15 and 32), upscale, add * 0.5
  6 filmic grade: teal lift in shadows, warm gain in highlights, soft S-curve (30% smoothstep blend)
  7 vignette multiply, light-leak flash add, paper jitter roll, film grain add
Everything in float32 NumPy, clipped to uint8 at the end.

STAGE 5 — AUDIO (100% synthesized, NumPy + SciPy butterworth filters + FFT convolution reverb)
Reverb = exponentially-decaying filtered noise impulse response, convolved with fftconvolve.
Instruments: kick (pitch-swept sine + click), 808 sub with glide, shaker/hat (HP noise), clap (4 taps),
snare, woodblock, marimba (additive with fast partial decay), pizzicato (detuned saws + LP envelope),
whistle (vibrato sine), pads (additive + LP + reverb).
Cartoon SFX: pencil scratch (band-passed noise with 38-63 Hz flutter), pop (fast exponential pitch
drop), ding (3-partial bell), boing (FM-ish vibrato glide), swish (24-chunk sweeping band-pass),
cinematic impact (80->33 Hz boom + sub + crack + rumble, big reverb), riser (exponential pitch + noise
+ accelerating tremolo), reverse cymbal, coin clink, cash register, firework.
Arrangement rules:
  - Doodle version: 112 BPM, C-major-ish chord per scene, marimba triad arpeggio, pizzicato, whistle
    melody [0,4,7,12,11,7,4,2], kick on 1&3, clap on 3, shaker 8ths, woodblock fill every 4th bar.
  - Cinematic version: 126 BPM trap bed (kick, clap+snare, swung 16th hats with stereo pan, 808
    glides, minor-key pluck arpeggio, pads).
  - EVERY visual event gets a sound: scene start = riser + reverse cymbal + swish + impact + 808 +
    pencil + pop; each tick/pop/X-mark/coin/star/handshake/burst has its own cue at its exact time.
Master: sidechain "pump" envelope from the kick grid, high-pass 32 Hz, mid/side widening of the side
channel above 2.5-3 kHz, tanh tape saturation, peak normalise to 0.93.

STAGE 6 — VOICE MIX & MUX (ffmpeg filtergraph)
VO chain: atempo (per clip) -> adelay to its slot -> amix -> highpass 95 -> EQ (-2.5 dB @250,
+4 dB @4 k) -> acompressor (thr -20 dB, ratio 5, atk 5, rel 110, makeup 5) -> alimiter -> apad/atrim.
Final mix: [music] + [vo] with `sidechaincompress` (threshold 0.030, ratio 8, attack 6, release 260,
makeup 1.8) keyed by the VO so music ducks under speech, then amix weights 1 : 1.4, loudnorm
I=-11 TP=-1.0 LRA=10, alimiter 0.97, atrim to exact duration.
Encode: libx264 High, preset slow, crf 23-27, maxrate 2.8-8 M, -pix_fmt yuv420p, -g 60,
AAC 160-192 k, -movflags +faststart. Keep the file under ~15 MB so in-app previews load.

STAGE 7 — QA (must all pass before delivering)
- Duration is EXACTLY the target (ffprobe), audio and video both.
- No empty/near-empty frame anywhere (sample frames at every cut ±0.1 s and mid-scene).
- No text touching the 1080-px edges; nothing colliding with the watermark or progress bar.
- Transition masks computed at half-res must use FRACTIONAL geometry, or be scaled x2 when drawn
  on the full-res canvas (classic off-by-2 bug).
- PIL guards: rounded_rectangle needs x1 >= x0 (clamp animated widths to >= 4 px); gradient arrays
  must broadcast as (h,1,1) not (h,1); a text mask regenerated without stroke must keep the SAME pad.
- Loudness -11 to -12 LUFS, true peak <= -1 dBTP.
DELIVER the .mp4 in the project root, keep sources in src/, and summarise what was built.
```

---

# PART 2 — ENVIRONMENT & FILE MAP (exact)

| Thing | Value |
|---|---|
| Python | 3.13, libs: Pillow 12.3, NumPy 2.3.5, SciPy 1.17.1 |
| ffmpeg | `pip install imageio-ffmpeg` → `imageio_ffmpeg.get_ffmpeg_exe()` (v7.0.2 static build) |
| CPU/RAM | 2 cores / 1 GB → frames MUST be streamed, never buffered |
| Fonts dir | `/home/user/fonts/` |
| Sources | `/home/user/src/` → `timeline.py`, `stickbase.py`, `stick2.py`, `make_audio4.py` |
| Scratch | `/home/user/build/` (NOT snapshot-persisted — only intermediates here) |
| Deliverables | `/home/user/*.mp4` |

Font download commands (one time):
```bash
curl -sL -o fonts/Montserrat-VF.ttf     "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"
curl -sL -o fonts/PermanentMarker.ttf   "https://github.com/google/fonts/raw/main/apache/permanentmarker/PermanentMarker-Regular.ttf"
curl -sL -o fonts/PatrickHand.ttf       "https://github.com/google/fonts/raw/main/ofl/patrickhand/PatrickHand-Regular.ttf"
curl -sL -o fonts/Caveat-VF.ttf         "https://github.com/google/fonts/raw/main/ofl/caveat/Caveat%5Bwght%5D.ttf"
```
Montserrat is a variable font → `ImageFont.truetype(...).set_variation_by_name('ExtraBold'|'Black'|'Bold'|'SemiBold')`.

---

# PART 3 — TIMELINE MATH (the spine of the whole edit)

```python
TEMPO = 1.45                                   # global VO speed-up
RAW   = [7.13, 10.15, 9.31, 6.40, 9.02, 8.33]  # measured, silence-trimmed VO seconds
VO    = [r / TEMPO for r in RAW]               # = [4.92, 7.00, 6.42, 4.41, 6.22, 5.75]
LEAD  = 0.30                                   # silence before the first word
TAIL  = [0.35, 0.30, 0.30, 0.30, 0.30, 0.45]   # breathing room after each scene's speech
```
Result (exact, total **37.000 s**):

| Scene | Start | End | Length | VO starts at |
|---|---|---|---|---|
| S1 hook | 0.00 | 5.57 | 5.57 | 0.30 |
| S2 step 1 | 5.57 | 12.87 | 7.30 | 5.62 |
| S3 step 2 | 12.87 | 19.59 | 6.72 | 12.92 |
| S4 step 3 | 19.59 | 24.30 | 4.71 | 19.64 |
| S5 step 4 | 24.30 | 30.82 | 6.52 | 24.35 |
| S6 CTA | 30.82 | 37.00 | 6.18 | 30.87 |

Re-recorded VO lengths were `[7.11, 9.46, 9.25, 6.73, 9.23, 8.54]` → per-clip atempo
`= new/target` = `[1.446, 1.351, 1.441, 1.525, 1.484, 1.487]` so the picture never had to change.

---

# PART 4 — DOODLE VISUAL SYSTEM (forensic)

### 4.1 Palette (RGB)
`CHALK (238,242,250)` · `GOLD (255,201,60)` · `CYAN (70,224,255)` · `MINT (124,255,178)` ·
`RED (255,107,107)` · `PINK (255,140,200)` · board base `(16,20,28)` · ground lines `(120,132,155)`
Scene accents: `[RED, CYAN, MINT, PINK, GOLD, GOLD]`.

### 4.2 Hand-drawn "boil"
```python
def hsh(a,b=0): v = sin(a*12.9898 + b*78.233)*43758.5453; return v - floor(v)   # deterministic noise
def jpt(p, seed, tq, amp=2.6):          # tq = frame_index // 2  → 15 fps boil
    return (p[0] + (hsh(seed*1.7 + tq*3.1)-.5)*2*amp,
            p[1] + (hsh(seed*3.3 + tq*5.7 + 9.1)-.5)*2*amp)
```
Each primitive receives a unique `seed` so its wobble is independent but repeatable.

### 4.3 Draw-on reveal
`_cut(pts, p)` walks the polyline accumulating segment lengths and cuts at `p * total_length`,
interpolating the final partial segment → strokes appear to be *drawn*, not faded.

### 4.4 Primitives
`poly` (jitter + cut + round caps) · `circ` (34-segment polygon) · `arc` · `box` · `squiggle`
(9-point zigzag, h=11) · `arrow` (quadratic Bézier, 16 samples + 2 head strokes) · `star` (10-point) ·
`tick` · `cross` (two strokes drawn sequentially) · `coin` (ellipse squashed by |cos(spin)| + `$`) ·
`laptop` (screen box + trapezoid base + callback for screen content) · `play_btn` · `speech` bubble
(7-point outline with tail) · `_bullet` (tick + Patrick Hand label at x+190).

### 4.5 Stick figure rig (FK)
```
hip   = (x, y - .42s)
neck  = hip + rot(lean)·(0, -.36s)
head  = neck + rot(lean+head)·(0, -(.115s + .035s))
shoulder = neck + (0, .03s)
limb(root, a1, a2, l1, l2):  joint = root + l1·(sin a1, cos a1);  end = joint + l2·(sin(a1+a2), cos(a1+a2))
arms: l1=.19s l2=.18s      legs: l1=.22s l2=.22s      feet: .055s horizontal stub
eyes: r=.014s at ±.38·head_r;  mouth: arc (happy/sad) or line (neutral)
```
Pose table (degrees, 0 = straight down, sign = direction):

| Pose | lean | head | al/el | ar/er | ll/kl | lr/kr |
|---|---|---|---|---|---|---|
| idle | ±2·sin | ±3·sin | 18+b / 10 | -18-b / -10 | 10/2 | -10/2 |
| sad | 8 | 16 | 14/20 | -14/-20 | 8/4 | -8/4 |
| type | 12 | 6 | 68+osc / 42 | 66-osc / 44 | 96/-92 | 88/-86 |
| cheer | -3 | -6 | 168+a / 12 | -168-a / -12 | 20/6 | -20/6 |
| point-up | -2 | -4 | 150+j / 6 | -16/-12 | 11/3 | -11/3 |
| walk | 4 | 2 | 26·sin φ / 18 | -26·sin φ / -18 | 30·sin φ / max(0,26 sin(φ+1)) | mirrored |
| shake | 5 | 4 | 18/12 | -74-j / -14 | 11/3 | -11/3 |
| dance | 10·sin φ | 8·sin φ | 120+40 sin φ / 30 | -120-40 sin(φ+2) / -30 | 18+14 sin φ / 8 | mirrored |

`osc = 7·sin(13t)`, `j = 8·sin(9t)`, `φ = 7t … 7.5t`. Motion trails = same pose at `t − k·0.055` drawn
with 35 % brightness and 3 px thinner lines.

### 4.6 Background stack (bottom → top)
1. `BOARD`: 360x640 noise(σ=7) + Gaussian 1.6 → bicubic 1080x1920 → 900 dust specks → 14 blurred
   white-7-alpha smudges.
2. `wash(t, scene)`: 180x320 float field, three Gaussian glows (accent at a Lissajous position, cyan
   counter-glow, broad centre lift) → bicubic upscale.
3. `GRID`: 135-px graph paper at alpha 9, scrolls `(t*26) % 135`.
4. `DOODLES`: 1080x2520 layer of 46 faint doodles (circle/star/$/triangle/squiggle, alpha 34),
   scrolls `(t*34) % 600` → parallax against the grid.
5. Scene content layer (transparent RGBA) → blurred copy at 42 % as chalk glow → sharp copy on top.

### 4.7 3D marker text (class `T3`)
```
mask           = glyph mask (Permanent Marker)
mask_outline   = same glyph with stroke_width=6
glow           = colour, alpha = blur(mask_outline, 26) * 1.8 * 120/255
extrusion      = for i in depth..1: colour = side*(0.45+0.55*(1-i/depth)), offset (0.45i, 0.95i)
outline        = (10,13,19) filled mask_outline
face           = flat colour filled mask
sweep(phase)   = exp(-((x + 0.3y - 1.6·phase)²)/(2·0.14²)) · mask · 215  → additive white band
```
Entry animation `w3(...)`: scale `0.4 + 0.6·out_back(p, 2.4)`, horizontal squash `1+sq`, vertical
`1/(1+sq)`, alpha `clamp(3p)`, optional rotation, optional sweep phase.

### 4.8 VFX library (exact parameters)
| Effect | Parameters |
|---|---|
| speed_lines | 30 rays, inner radius 420-560, length 260-680, width 3-10, alpha 150·p, blur 1.6 |
| shockwave | r = maxr·out_expo(p), alpha 220·(1-p)^1.5, double ring at 0.72r |
| comic_burst | 18-point star, k = out_back(min(1,2.2p)) · fade after 0.7, fill alpha 46 + stroked outline + word |
| dust | 12 particles, r = spread·out_expo(p)·(0.4+rand), radius 9(1-p), rises 40p |
| sparkle | 4-ray cross, size s·sin(πp), 5 px + 3 px diagonals |
| badge | pill (radius 26, fill alpha 46, outline 235) + Patrick Hand text, pops with out_back, floats −60p, fades after 0.6 |
| flame | 7-point doodle flame, width modulated `1+0.12 sin(9t)` |
| crown | 7-point polyline above head radius 46 |
| highlighter | rounded bar, alpha 60, width grows with out_expo |
| circle_mark | ellipse polyline with `1+0.04 sin(a/24)` wobble, red, 7 px |
| coin rain | 22 coins, speed 0.5-1.3, radius 26-46, spin `4t+i`, `$` glyph when face is wide |
| fireworks | 9 stars on a −π/2 ± fan, r = 480·out_expo, size shrinks 40 % |

### 4.9 Transitions (0.34 s, placed in `[cut, cut+0.34]`)
Composite = `Image.composite(new_scene_at_t, old_scene_frozen_at_end, mask)`.
Masks are built at 540x960 then blurred 5 px and upscaled:

| # | Type | Mask math |
|---|---|---|
| 1 | Ink-blob iris | `r < p^1.25 · 700 · (1 + .16 sin5θ + .08 sin(9θ+1.3))` around (0.5W, 0.62H); visible ring drawn at `p^1.25·1400` on the full-res canvas |
| 2 | Paint wipe | 7 columns, each `y < H·clamp((p − .05c)/.72)·1.3 + 40 sin(2.1c)` |
| 3 | Eraser | `x < (1.3p − .15)W + 26 sin(.06y) + 18 sin(.013y+2)` + a 12 px chalk edge line |
| 4 | Vertical zip | `|y − H/2| < p^0.85 · 0.75H` |
| 5 | Diagonal whip | `0.6x + 0.4y < 1.15p(0.6W + 0.4H)` |

Each cut also triggers: flash `0.34k²`, RGB split `9k`, smear `14k`(pre)/`7k`(post), shake
`26k·sin(88Δ)`, `18k·cos(70Δ)`, rotation `1.4k·sin(52Δ)`, with `k = 1 − |Δ|/0.26`.

### 4.10 Camera & post (per frame)
```
zoom  = 1.025 + 0.05·(lt/scene_len)^1.05 + 0.01·exp(-6·beat_phase)     # 112 BPM bump
shake = 7 sin(2.0t) + 4 sin(5.1t+1) , 6 sin(1.6t+.5) + 3 sin(4.3t+2)   # handheld
rot   = 0.3 sin(1.1t)
bloom: /4 downscale, threshold 168, blur 15 & 32, upscale, add ×0.5
grade: shadows += (-3,1,11)·(1-lum) ; highlights += (13,5,-7)·lum ; S-curve 30 % smoothstep
vignette: clip(1.06 − 0.45·r^2.0)   grain: N(0,1)·4.5 (half-res, nearest-doubled)
paper jitter: ±2 px roll driven by the 2-frame hash
```

---

# PART 5 — SCENE-BY-SCENE STORYBOARD (doodle version, exact)

**S1 0.00-5.57 — HOOK**
walk-in from x=−160 → W/2−80 over 0.85 s (walk cycle + dust), then `pose_sad`; ground line y=1530;
3D title "JEEB KHALI?" at (540,330) rot −2.5° from t=0.5 + red squiggle underline at y=420;
speed lines 0.5-0.95 s; rain cloud (3 circles at y≈760) from 1.1 s with 5 falling drops; empty-pocket
arcs on the hips at 1.2/1.3 s; speech bubble (540+268, 900) + 3D "Rs 0" at 1.75 s + sparkle;
three cyan "?" at 1.9/2.15/2.4 s bobbing `16 sin(2t)`; 2.9 s shockwave + 3D "PURA PLAN" (540,1690) +
"4 STEPS ME" (1800) + "FREE" badge; flames at x=150 / x=930 from 3.6 s.

**S2 5.57-12.87 — STEP 1 · SKILL SEEKHO**
Number "1" (Patrick Hand 150, gold) in a hand-drawn circle at (150,290); 3D title at (650,290);
checklist at x=150, y=520/625/730/835 (DESIGN, VIDEO EDIT, CODING, AI TOOLS) at 1.5/1.9/2.3/2.7 s,
each with tick + sparkle + "+1" badge at x=560; brain = pulsing circle (830,620) r=92+5 sin(4t) with
5 inner arcs filling 1.4→4.2 s and a live `%` readout; 6 knowledge sparkles spiralling in;
desk top y=1330 (legs to 1520), stool, seated figure at x=315 (`pose_type`), laptop at (630,1330)
with a pulsing play button; `</>`, `*`, `~` particles rising; pink arrow brain→head at 3.3 s;
highlighter + "YouTube = FREE university" at 4.3 s.

**S3 12.87-19.59 — STEP 2 · ROZ 2 GHANTE**
Clock centre (320,640) r=158, 12 tick marks staggered 0.022 s apart, hour hand sweeps `720°·p`
(1.1→3.3 s), minute hand ×12 with a 3-step motion trail, "2h DAILY" 3D at (320,862);
mini desk at y=870 with a 330-px typing figure at x=726 + laptop at 912 + 3 sweat drops;
calendar 5×6 at origin (265,990), cell 112 px, cross marks appear every 0.1 s from 1.6 s with a dust
puff on the active cell; counter "`{hrs} HOURS`" 0→60 at (540,1740) with a squash wobble;
at 4.5 s shockwave + "CONSISTENCY = POWER" badge.

**S4 19.59-24.30 — STEP 3 · SAMPLE BANAO**
Three frames at x=230/540/850, y=700(+36 odd) bobbing `8 sin(1.6t+i)`, popping at 0.3/0.75/1.2 s with
squash `1+0.25(1−1.6p)`; contents: poster (circle + mountain line), reel (play button), website (bar +
3 lines); labels POSTER / REEL / WEBSITE at y+196; dust puff under each; painter figure (470 px,
`pose_point` up, 1 trail) + gold brush stroke; 2.5 s "DEGREE nahi," + red circle-mark, 3.0 s 3D
"KAAM bolta hai!" + speed lines.

**S5 24.30-30.82 — STEP 4 · SERVICE BECHO**
Phone body (540±220, 800±310) + speaker line; three chat bubbles sliding in from ±240 px with
out_back at 1.3/2.0/2.7 s ("Hi! Reels edit karta hu" / "Rate kya hai?" / "Deal! Invoice bhejo");
3D "10 DM / DAY" at (540,1190) + speed lines at 3.0 s; platform boxes FIVERR/UPWORK/INSTA at
x=230/540/850, y=1300-1400, popping 3.4/3.65/3.9 s; ground y=1790; handshake pair (400 px) at
±180 px from 4.2 s, gold hand link at 4.6 s, "DEAL!" comic burst + shockwave, 5 coins falling
1430→1690 with sparkles.

**S6 30.82-37.00 — CTA**
22-coin money rain with per-coin speed/spin + random sparkles; dancing figure (470 px, 2 trails)
bouncing `30·|sin(5.2t)|` with a dust puff at each landing; crown at 2.2 s; 3D "AAJ HI SHURU" (420) +
"KARO!" (548) with sweeps, gold squiggle at 628, speed lines + 760-px shockwave at 0.3-1.1 s;
recap row SKILL/TIME/SAMPLES/SELL at y=790 with ticks + sparkles (1.2-2.1 s); pulsing
"FOLLOW = PART 2" box (170→910, 960-1105) at 2.6 s; "SAVE karo, bhool jaoge!" + two flames at 3.3 s;
9 fireworks from 2.9 s; "LET'S GO!" comic burst at 4.6 s.

---

# PART 6 — AUDIO FORENSICS

### 6.1 Synthesis primitives (all NumPy)
| Sound | Recipe |
|---|---|
| kick | f = 46 + 95·e^(−32t), sine, env e^(−8t), tanh(×1.6) |
| 808 | f glides `f + (slide−f)·e^(−9t)`, +16 % 2nd harmonic, env `min(1,55t)·e^(−1.6t)`, tanh |
| shaker | HP 7 kHz noise · e^(−45t), 70 ms |
| clap | 4 band-passed (1.2-5.2 kHz) noise taps at 0/10/21/30 ms, e^(−26t) |
| snare | 190+278 Hz tone · e^(−26t) + BP 1.4-7.8 kHz noise · e^(−19t) |
| marimba | sine + 4th partial·e^(−18t) + 9.2nd·e^(−30t), env e^(−6.5t) |
| pizzicato | two saws detuned ±0.4 %, LP 1.8 kHz, e^(−11t) |
| whistle | sine with 5.5 Hz / 1.2 % vibrato, soft attack + release |
| pencil | BP 1.8-9 kHz noise × flutter `0.55+0.45 sin(2π(38+25τ)t)` × sin(πτ)^0.8 |
| pop | f = f₀·(1+2.4 e^(−55t)), e^(−26t) |
| ding | partials 1 / 2.01 / 3.01 with decays 5 / 8 / 12 |
| boing | f = 420 e^(−4t)+90 with vibrato `1+0.5 sin(22πt)e^(−3t)` |
| swish | 18-chunk band-pass sweep 380 Hz → 9.9 kHz, sin(πτ)^1.2 window |
| impact | (78 e^(−3.4t)+33) Hz boom + 36 Hz sub + HP 2.6 k crack + LP 160 rumble, big reverb, tanh |
| riser | f = 170·14^(τ^1.3) + noise τ³, tremolo 5→25 Hz |
| reverse cymbal | HP 5 kHz noise × τ³ + long reverb |
| coin / register / firework | bell partials / bell+noise ka-ching / HP crack + tail |
| reverb | IR = noise·e^(−decay·τ), LP-damped, 12 ms pre-delay, `fftconvolve` |

### 6.2 Doodle arrangement
112 BPM (`SPB = 0.5357 s`). Chord per scene (semitones from A440 index): C, G, Am-ish, F, G, C.
Kick on beats 1 & 3 (0.78) and 0.5 elsewhere, clap on beat 3, shaker 8ths panned 0.38/0.62,
808 on beat 1, pizzicato on off-beats, marimba triad as a 16th arpeggio panned 0.35→0.65,
woodblock fill on beat 4 of every 4th bar, whistle melody `[0,4,7,12,11,7,4,2]` 4 notes per scene.

### 6.3 SFX cue sheet (relative to each scene start)
```
every cut:  riser −0.85 | rev-cymbal −0.80 | swish −0.30 | IMPACT 0.00 | 808 0.00 | swish 0.02 |
            pencil 0.06 | pop 0.10
S1: pops 1.10/1.50 · ding 1.75 · pops 1.95/2.20/2.45 · impact+ding 2.90 · swish 3.60
S2: 16 typing clicks from 0.70 · pop+ding at 1.50/1.90/2.30/2.70 · pencil 1.10 · 7 coin clinks
    1.60+0.40k · pencil 4.35 · ding 4.60
S3: tick-tock ×10 from 1.00 (0.45 s) · 30 pencil scratches 1.62+0.10k (+pop every 5th) ·
    12 typing clicks 2.30 · impact+ding 4.50
S4: pencil/pop/ding triplets at 0.35, 0.80, 1.25 · swish 2.95 · impact 3.05
S5: pop+ding 1.30/2.00/2.70 · pops 3.45/3.70/3.95 · swish 2.95 · boing 4.25 · impact 4.62 ·
    register 4.70 · 5 coin clinks 4.90+0.16k
S6: swish 0.05 · impact+808 0.30 · 12 coin clinks 0.30+0.36k · 9 boings 0.55+0.58k ·
    pop+ding 1.20/1.50/1.80/2.10 · pencil 2.60 · ding 2.70 · 7 fireworks 2.95+0.12k ·
    rev-cymbal 4.30 · impact 4.60
```

### 6.4 Master chain
Sidechain pump envelope `1 − 0.3·e^(−7τ)(1−τ^0.4)` every beat → multiply (80 % wet) → HP 32 Hz →
mid/side with `side += HP(side, 3 kHz)·0.45` → `tanh(1.1x)/tanh(1.1)` → peak 0.93.

---

# PART 7 — EXACT FFMPEG COMMANDS

**Trim VO silence**
```bash
ffmpeg -y -i assets/sN.mp3 -af "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,\
areverse,silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,areverse" build/vsN.wav
```

**Build the 37 s VO bed (per-clip tempo + slot delay)**
```bash
ffmpeg -y -i build/vs1.wav ... -i build/vs6.wav -filter_complex "\
[0:a]atempo=1.446,adelay=300|300[a0]; [1:a]atempo=1.351,adelay=5617|5617[a1]; \
[2:a]atempo=1.441,adelay=12917|12917[a2]; [3:a]atempo=1.525,adelay=19638|19638[a3]; \
[4:a]atempo=1.484,adelay=24352|24352[a4]; [5:a]atempo=1.487,adelay=30873|30873[a5]; \
[a0][a1][a2][a3][a4][a5]amix=inputs=6:duration=longest:normalize=0,highpass=f=95,\
equalizer=f=250:t=q:w=1:g=-2.5,equalizer=f=4000:t=q:w=1.2:g=4,\
acompressor=threshold=-20dB:ratio=5:attack=5:release=110:makeup=5,alimiter=limit=0.95,\
apad,atrim=0:37,aresample=48000[a]" -map "[a]" build/vo37.wav
```

**Final mux (ducking + loudness + encode)**
```bash
ffmpeg -y -i build/stick2_silent.mp4 -i build/music4.wav -i build/vo37.wav -filter_complex "\
[2:a]apad,atrim=0:37,asetpts=N/SR/TB[vof];[vof]asplit=2[vo][sc];[1:a]volume=0.9[mus];\
[mus][sc]sidechaincompress=threshold=0.030:ratio=8:attack=6:release=260:makeup=1.8[duck];\
[duck][vo]amix=inputs=2:duration=longest:dropout_transition=0:weights=1 1.4,\
loudnorm=I=-11:TP=-1.0:LRA=10,alimiter=limit=0.97,apad,atrim=0:37,aresample=48000[a]" \
-map 0:v -map "[a]" -c:v libx264 -profile:v high -preset slow -crf 23 -maxrate 7M -bufsize 12M \
-pix_fmt yuv420p -g 60 -c:a aac -b:a 192k -movflags +faststart out.mp4
```
**Size pass** (keep previews loading): re-encode with `-crf 27 -maxrate 2800k -bufsize 5600k -b:a 160k`
→ 37 s went 27 MB → **14 MB** with no visible loss on a doodle look.

---

# PART 8 — BUGS HIT & THEIR FIXES (so you never repeat them)

| # | Symptom | Root cause | Fix |
|---|---|---|---|
| 1 | `ValueError: could not broadcast (269,3) into (269,969,3)` | gradient built with `ys[:,None]` | use `ys[:, None, None]` so it broadcasts over (h,w,3) |
| 2 | `images do not match` on `paste` | stroke mask used `pad = 90 + stroke`, the re-made inner mask used a different pad | fix the pad to a constant (96) for both passes |
| 3 | `x1 must be >= x0` crash at frame ~300 | animated widths hit 0 (`underline`, bar chart) | clamp to `max(4, …)` |
| 4 | Transition frames almost empty | mask radius computed in HALF-res pixels but the matching ring drawn in FULL-res | use fractional geometry, or halve/double consistently (700 ↔ 1400) |
| 5 | Wipe revealed a blank incoming scene | incoming scene was rendered at `lt≈0` where nothing exists yet | place the wipe AFTER the cut, freeze the outgoing scene at its last frame, and make every scene's first elements appear within 0.05-0.1 s |
| 6 | Washed-out, hazy first look | background glows too bright, glow halos too strong | base to (13,11,30)→(2,2,7), glow amps 0.42/0.26/0.20, vignette 1.10−0.78r^1.9 |
| 7 | Text clipped at the frame edges | font sizes too large for 1080 px | MONEY 300→268, SERVICE BECHO 112→96, START KARO 150→132 |
| 8 | 13 MB / 27 MB files refused to preview in-app | bitrate too high | second encode pass to ≤ 15 MB, `+faststart` |
| 9 | Sources vanished between sessions | the folder was literally named `build/`, which snapshots exclude | keep code in `src/`, only intermediates in `build/` |
| 10 | `ModuleNotFoundError: imageio_ffmpeg` after a session | pip installs don't persist | re-install at the start of every session |
| 11 | Collisions (head over text, labels over frames) | layout done by feel | fix a y-grid per scene and verify by rendering sample frames before the full run |

---

# PART 9 — DELIVERABLES & KNOBS

| File | Spec |
|---|---|
| `stickman_money_37s_v2.mp4` | 37.00 s · 1080×1920 · 30 fps · 14 MB · doodle + full VFX (**flagship**) |
| `stickman_money_37s.mp4` | 37.00 s · stickman v1 (no 3D text / transitions) |
| `money_online_reel_v2.mp4` | 10.00 s · 60 fps · cinematic 3D reel |
| `money_online_reel.mp4` | 10.00 s · 30 fps · first cinematic pass |

**One-line knobs**
- Handle: `'@YOURHANDLE'` in `hud()` (stick2.py) / `render()` (render2.py).
- Whiteboard look: `BOARD` base → `(248,248,244)`, `CHALK` → `(32,34,40)`, drop the chalk-glow blend
  to ~0.12, invert the vignette strength.
- Language: every on-screen string lives in the scene functions; the Urdu is only in the TTS calls.
- Length: edit `RAW`/`TAIL` in `timeline.py`; the renderer and the audio builder follow automatically.
- Aspect: change `W,H` to 1080×1080 or 1920×1080 and re-check the y-grid constants per scene.

**Render budget (2-core box):** doodle 1110 frames ≈ 0.45-0.6 s/frame ≈ 9-11 min;
cinematic 600 frames @60 fps ≈ 0.7 s/frame ≈ 7 min; audio build ≈ 4 s; mux + 2-pass encode ≈ 2 min.
