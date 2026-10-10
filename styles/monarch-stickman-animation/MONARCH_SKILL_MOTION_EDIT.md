# SKILL: PREMIUM 2D MOTION EDIT ENGINE (v3.0)
## For: Monarch — YouTube Automation Agent
## Status: ADDITIVE ONLY. Do not remove, replace, or modify any existing skill or pipeline.

---

# 0. STYLE ROUTER — READ THIS FIRST

Monarch now has TWO stickman styles. They are **siblings**, not replacements.

**STYLE A — IMAGE COMPILE (existing, DO NOT TOUCH)**
Generate still images -> compile -> apply zoom in/out, transitions, captions -> export full video.
Keep every file, prompt and step of this exactly as it is. Nothing in this document changes it.

**STYLE B — FRAME RENDERER (new, this document)**
Every frame is drawn in code (Python + PIL) at 1080x1920, then encoded. No still images, no generative art, zero drift between frames.

```
if brief needs: character animation / walk cycles / hand gestures /
                consistent character across scenes / frame-exact VO sync
    -> STYLE B
if brief needs: photoreal or illustrated scenes / many locations / fast / cheap
    -> STYLE A
else -> STYLE A   (cheaper; escalate to B only when the brief demands it)
```

Everything below is Style B.

---

# 1. THE MISTAKE LEDGER — WHAT WENT WRONG, WHY, AND HOW IT WAS FIXED

This is the heart of the skill. Each entry is: **symptom -> root cause -> fix -> proof.**

### M1 — Too much on screen
- **Symptom:** client rejected the densest build outright. *"clean rakho, zyada cheezen NAHI bharo"*
- **Cause:** treating "more elements" as "more value". Every scene had 2-3 competing graphic clusters.
- **Fix:** removed ~40 % of elements. One cluster per scene, max 3 colours, one transition type.
- **Proof:** next build approved immediately with no notes.

### M2 — The character looked like a chalk stick figure
- **Cause:** flat single-weight strokes with no fill, no volume, no shading.
- **Fix:** two-pass silhouette (grow the whole figure in outline colour, then fill), then a shading stack.
- **Note:** per-part outlines produce **joint seams**. Only a whole-figure silhouette works.

### M3 — Shading destroyed the ink contour
- **Symptom:** the crisp near-black outline turned grey; eyes and mouth went grey too.
- **Cause:** shading layers were masked with the **raw alpha**, which includes the outline band.
- **Fix:** clip every shading layer to an **eroded** mask — `alpha.blur(ow*1.15).point(v>248) x alpha` — and draw the **face AFTER** shading, on the final canvas.

### M4 — Hands became a mitten
- **Symptom:** fingers welded into one blob.
- **Cause:** fingers built as overlapping circles. At `OW ~= 7 px` the outline grow pass is **wider than the inter-finger gap**, so the dilation fuses them.
- **Fix:** palm + 4 fingers = **ONE scalloped polygon** with notches cut between fingers; thumb is a separate capsule.
- **Sizing is a narrow window:** `0.033*s` -> fingers thinner than the outline, invisible. `0.047*s` -> boxing gloves that clip the thighs. **`0.040*s` is correct.**

### M5 — THE REVERSED FOOT (client spotted it before any metric)
- **Symptom:** *"uska paon ulta hai."* One foot read as on backwards.
- **Cause:**
  ```python
  heel = fx - abs(T)*0.40     # T is SIGNED (negative for the left foot)
  toe  = fx + T*1.03
  ```
  `abs()` forced the heel onto the **same side as the toe** on the left foot. That foot had no heel behind the ankle.
- **Fix:** `heel = fx - T*0.44` — always opposite the toe. Full 8-point profile: heel-back -> heel-top -> instep -> toe-top -> toe-front -> toe-ground -> heel-ground.
- **LAW:** *never mix a signed direction variable with `abs()` in the same shape. Audit every `abs()` sitting next to a sign multiplier.*

### M6 — It moved like a puppet
- **Symptom:** every action was a sideways flap. *"putle ki tarah hai, real insan ki tarah hona chahiye."*
- **Root cause:** the rig rotated every joint **in the picture plane only**. A human arm swinging forward moves in **depth**. A flat rig physically cannot express that. **No amount of easing fixes this.**
- **Fix:** a real 3D skeleton with perspective projection. See Section 3.

### M7 — Even with 3D, the walk still did not read
- **Cause:** the character was **front-on**. A sagittal swing in a front view means the legs scissor in depth and simply overlap on screen.
- **Fix:** a global **`yaw`** that rotates the whole body about its vertical axis before projection. Depth swing then reads as real horizontal travel. This was the single biggest realism win.

### M8 — The eyes went lazy
- **Cause:** when yaw was added, eye offset was set to `sin(yaw)*1.05` — far too much.
- **Fix:** `sin(yaw)*0.34`. A 3/4 hint, not a stare.

### M9 — Shoulder and knee had visible steps
- **Cause:** limb capsule radius != the shape it attaches to.
- **Fix:** a **deltoid cap disc** at each shoulder, a **patella disc** at each knee. Same trick, both joints.

### M10 — A sleeve cuff was painted on the chest
- **Cause:** the cuff helper was 2D and knew nothing about depth, so the cuff for an arm **behind** the torso drew on top of the torso.
- **Fix:** draw the cuff inside its own arm group, perpendicular to **its own** forearm, so depth sorting handles it.

### M11 — Seated and bent poses floated off the ground
- **Cause:** eyeballed vertical offsets; then an analytic `foot_drop()` that could not account for perspective.
- **Fix:** the renderer projects **both** ankles, finds the lower sole, and shifts the whole figure so it touches the ground line. `foot_drop()` now returns `0.0` and that is a regression test.

### M12 — CAPTIONS WERE UNDER THE PLATFORM UI (the most damaging defect in the project)
- **Symptom:** none. It looked perfect in the editor.
- **Found by:** measuring the distance of every baseline from the frame edge.
- **Cause:** caption baseline at `y=1718` on a 1920 frame = **202 px from the bottom**. Reels/TikTok/Shorts UI covers roughly the bottom **320-420 px** and the top **~130 px**.
- **Every caption in the film was being covered on a real phone.**
- **Fix:** re-flow the entire grid into `y in [180, 1500]`, scale the character x0.84, re-anchor every prop that was positioned off the old ground line.
- **Proof:** 202 px -> **468 px** from the bottom edge.

### M13 — Every accent colour failed contrast
- **Found by:** computing WCAG contrast on the real palette constants.
- **Measured:** coral 3.40 / blue 3.92 / violet 4.48 / amber 2.78 / green 3.40 / gold **2.17** / **white on the gold CTA pill 2.39:1**.
- **Cause:** colours chosen by eye on a bright monitor. Big headline words survive on size; small caption keywords and white-on-accent CTA text do not.
- **Fix:** darken all six by 18-26 % for use on light backgrounds; keep a bright `ACC_HI` set for fills on dark panels.
- **Proof:** 4.72 - 7.07:1, all PASS. White on gold **2.39 -> 5.18**.

### M14 — The transitions were a strobe
- **Measured:** mean frame luma at each cut: `223->127`, `223->138`, `214->139`, `222->92`, `221->145`. **49 frames with a >8 luma jump.**
- **Cause:** a full-bleed saturated colour panel sweeping the frame. 222 -> 92 and back, **five times in 37 seconds**, on a bright cream film.
- **Fix:** tint, do not flood. See Section 5.2.
- **Proof:** swing **-131 -> -13**, luma jumps **49 -> 0**, darkest frame **104 -> 200**.

### M15 — The picture led the sound at every cut
- **Measured:** the motion-energy peak landed **1-2 frames before** the cut frame, every time (-33 to -67 ms).
- **Fix:** `TLAG = 0.050 s` added to the cut time so the swipe sits late and locks to the impact.

### M16 — A tenth of two scenes was frozen
- **Measured:** `p10` frame-diff of **0.06** in two scenes, and a **0.53 s dead zone** at t=5.93 — inside the first-7-second retention window.
- **Cause:** props froze the instant they finished revealing. Nothing in the frame was moving between beats.
- **Fix:** `fl()` micro-float on every revealed prop group.
- **Proof:** `p10` **0.06 -> 0.22-0.47**.

### M17 — THE SUB-PIXEL CAMERA TRAP
- **Symptom:** after adding float, consecutive frames were still **byte-identical**.
- **Cause:**
  ```python
  zw, zh = int(W*z), int(H*z)   # z changes every frame; int() does not
  ```
  The zoom was quantised to whole pixels, so the crop stalled for several frames at a time.
- **Fix:** replace resize+crop with a float `Image.AFFINE` resample carrying the zoom **and** a two-term float drift.
- **Proof:** global minimum frame-diff **0.01 (frozen) -> 0.082**.
- **LAW:** *any animated value that passes through `int()` before reaching pixels will quantise and stall.*

### M18 — Reveals snapped instead of settling
- **Measured:** `p95(jerk)` of 3.1-4.1 in four scenes, vs 0.9 in the two that felt good.
- **Cause:** `e_back` overshoot of 1.5-1.9 over a 0.40 s window with no settle tail, and siblings staggered so far apart they read as four separate pops.
- **Fix:** overshoot **1.5 -> 1.12**, stagger **.45 -> .30**, ramp **.55 -> .72**, rise easing `e_out(3.2) -> e_out(2.2)`.
- **Proof:** worst-scene jerk **4.13 -> 1.62**.

### M19 — THE MIX WAS SECRETLY MONO
- **Measured:** L/R correlation **0.9941** (anything >0.97 is mono), side/mid energy **0.054**.
- **Cause:** a full stereo ASMR bed existed — panned cues, a stereo plate, detuned pads — and then a **mono voiceover at +10 dB was summed on top and swamped all of it.** The designed width never reached the listener.
- **Fix:** mid/side process the bed, Side x3.30, keep the voice centred.
- **Proof:** correlation **0.9941 -> 0.7547**, side/mid **0.054 -> 0.374**.

### M20 — The spectrum was mud
- **Measured:** 120-500 Hz held **66.75 %** of all energy; 1-4 kHz only **5.76 %**; 8-16 kHz **0.60 %**.
- **Cause:** an 8.2 kHz bus lowpass added to kill harshness **also removed every bit of sparkle**, plus insufficient low-mid control on the voice.
- **Fix:** bus lowpass -> 14.5 kHz, air shelf added back, deeper VO low-mid cut, presence and air shelves.
- **Proof:** 120-500 Hz **66.8 -> 57.7 %**, 4-8 kHz **8.3 -> 10.7 %**.

### M21 — The mix kept dropping out
- **Measured:** short-term minimum **-32.4 LUFS**, loudness range **20.9 LU**, **12 holes** more than 9 LU below the mean, largest onset gap **2.19 s**. One hole was *inside the CTA*.
- **Cause:** the bed was ducked at **18:1** between phrases and nothing filled the space.
- **Fix:** sidechain **18:1 -> 5:1**, bed level up, and **12 pad swells placed on the measured hole list**.
- **Proof:** holes **12 -> 4**, minimum **-32.4 -> -27.3 LUFS**, range **20.9 -> 15.2 LU**.

### M22 — THE MEASUREMENT THAT WAS ITSELF WRONG
- **Symptom:** VO/music balance measured as **1.27 dB**, which nearly triggered a massive over-correction.
- **Cause:** the measurement compared speech-window RMS against gap-window RMS **on the summed mix**. The "gaps" contained the transition impacts — so it was comparing the voice to a drum hit.
- **Fix:** render the VO chain and the bed to **separate stems** and compare those. True value: **+10.0 dB**.
- **LAW:** *any A-vs-B audio measurement must use isolated stems, never a sum.*

### M23 — Silent patch failures
- `str.replace` with a wrong parameter name did nothing, silently (`_hair`'s `ang` vs `a`).
- `s.index()` on a box-drawing comment character failed invisibly.
- Rewriting `_hand_parts` left a stale `arc(...,0,0,0)` call that raised `ZeroDivisionError` **at runtime, not at patch time**.
- A bulk regex replacement deleted the `SCENES` and `CAPS` tables along with the block it was targeting.
- **Fix:** see Section 2.

---

# 2. THE WORKING LOOP — "PIXELS ARE EVIDENCE"

```
patch -> assert the new token exists -> RE-RENDER -> LOOK AT THE IMAGE -> only then continue
```

- After **every** `str.replace`, assert a token from the new text is present.
- Never trust a bulk regex that spans to "the next `def`" — it will eat tables and constants that happen to sit in between. Bound it explicitly.
- Build a **6x2 contact sheet** of frames spanning all scenes for scene checks, and an **8-pose strip** for character checks. One image, one look, every problem visible at once.
- Draw the platform-UI danger zones onto the contact sheet as red rectangles so safe-area violations are impossible to miss.

---

# 3. CHARACTER SYSTEM — THE 3D RIG

Body space: **x = screen right, y = DOWN, z = TOWARD THE CAMERA.** Origin at the hip centre.

Every limb segment is solved from two angles — **abduction** (frontal plane, left/right) and **swing** (sagittal plane, forward out of the screen):
```python
def _dirv(abd, swing):
    a, w = radians(abd), radians(swing)
    return (cos(w)*sin(a), cos(w)*cos(a), sin(w))
```

Perspective projection — a long lens so depth reads but nothing distorts:
```python
F = 4.2 * s                       # focal length in body-height units
k = F / (F - z)
screen = (ox + x*k, oy + y*k)
# limb RADII are multiplied by k too - this is what sells it
```

**Joint limits — a puppet has none:**
```python
forearm_swing = arm_swing   + max(0.0, elbow_flex)   # elbow flexes FORWARD only
shin_swing    = thigh_swing - max(0.0, knee_flex)    # knee flexes BACKWARD only
```

**Depth sorting + aerial perspective:**
Group the figure — left arm, right arm, left leg, right leg, torso, head.
- *Within* a group: two-pass silhouette -> no seams at elbow or knee.
- *Between* groups: composite in **z order** -> an arm in front of the chest gets its own contour; an arm behind is correctly occluded. No extra image layers needed.
```python
def depth(colour, z, s):
    k = 1.0 + 0.26*(z/s)          # behind -> darker, in front -> lifted
    return tuple(clamp(int(v*k), 0, 255) for v in colour)
```

**Global yaw (the 3/4 view):**
```
idle 14 / walk 27 / think 20 / sit_type 18 / shake 23 / point +-16 / dance +-10 / present 4  (degrees)
eye shift = sin(yaw) * 0.34
```

**Pose channels:** `yaw, lean, twist, pelvis, tilt, sway, sh_up, head, head_t, al/ar, az_l/az_r, el/er, ef_l/ef_r, ll/lr, lz_l/lz_r, kl/kr, hl/hr, _bob, _br, _hv`

**Pose-angle convention is a trap.** Plain world angles only: 0 = down, **+ = screen +x**, left and right written out. A `+-1` side multiplier makes antisymmetric poses (walk cycles) **inexpressible**. Never feed one rig's pose dict to a different rig.

### Poses on real biomechanics

**idle — CONTRAPPOSTO.** A standing human is never square:
```
weight on one leg -> that hip rides UP (tilt)
pelvis shifts over the support leg (sway)
shoulders counter-tilt against the hip line (twist)
spine makes a shallow S; the unloaded knee stays soft
weight drifts to the other leg on a ~6.8 s cycle
arms rest with ~13 deg elbow flexion - arms are NEVER straight
```

**walk — a true two-beat gait:**
```
legs swing +-27 deg in the SAGITTAL plane (not sideways)
pelvis rotates WITH the leading leg      pelvis = +7.5*sin(phase)
shoulders counter-rotate against it      twist  = -7.5*sin(phase)
arms swing opposite their OWN leg
knee: near 0 through stance, ~59 deg peak in swing
    knee(q) = 7 + 52 * max(0, sin(q + 2.0))**1.6
    _bob    = 0.020*abs(cos(phase)) - 0.008
```

**think** — hand to chin, other arm folded across supporting that elbow.
**shake** — the arm reaches OUT OF FRAME toward the other person. Only expressible in depth.
**type / sit_type** — forearms come forward out of the screen.
**dance** — hips lead, shoulders follow a beat late (`twist` uses `sin(ph - 0.6)`).
**shrug** — shoulders raised via `sh_up`, elbows pinned to the ribs, palms up.

### Secondary motion
```python
def phys(fn, t, **kw):
    """MUST be a pure function of t, or parallel shards will not match at the seam."""
    p, pl, pm = fn(t), fn(t-0.070), fn(t-0.035)
    out = dict(p)
    for k in ('el','er','kl','kr'):  out[k] = pl[k]      # forearms/shins lag 70 ms
    out['head'] = 0.55*p['head'] + 0.45*pm['head']
    out['_hv']  = (pm['head']+pm['lean']) - (p['head']+p['lean'])   # hair inertia
    out['_br']  = sin(t*2.05)                            # breathing ~0.33 Hz
    return out
```
`_br` -> torso width x`1 + 0.020*_br`. `_hv` -> hair tip swing clamped +-0.42*rx, roots fixed.

### Craft details that read as expensive
| fix | why |
|---|---|
| hand `(41,36,31)`, creases `(132,122,112)` at `0.58*ow` | near-black hands collapse to blobs at a ~20 px delivery scale |
| deltoid cap disc / patella disc | removes the step where a limb meets its parent |
| tapered neck capsule | the head was bolted onto the collar |
| shirt hem; knee crease above 14 deg flex; 2 inner-elbow wrinkles above 35 deg flex | flat silhouettes read as paper |
| foot roll `clamp(shin_sagittal*0.62, +-26 deg)` about the ankle | feet that stay flat look nailed down |
| **subsurface warmth** — 7 stacked warm ellipses at 6 % alpha on the lower skull | one specular on flat white reads as plastic |
| second **hard contact-core** shadow under the soles | a soft blob alone leaves the figure floating |

### Rendering rules
- **Outline growth:** stroke the closed perimeter at `2*ow` with `joint='curve'`, then fill. Per-shape dilation is dead code.
- **Capsules:** one `atan2` angle, sweep each end cap by pi. Never mix bases per cap point.
- **Eroded shading mask:** `alpha.blur(ow*1.15).point(v>248) x alpha`. **Face drawn after shading.**
- `ImageChops.offset` **wraps around** — only safe when the figure never touches the tile edge and every layer is re-multiplied by the mask.

---

# 4. FORENSIC METHOD — MEASURE, NEVER EYEBALL

**Never evaluate a render by watching it. Decode the delivered file and measure it.** Run this every time.

### Video telemetry
```python
# ffmpeg -i out.mp4 -vf scale=216:384 -f rawvideo -pix_fmt gray /tmp/g.raw
a    = memmap(...).reshape(-1, 384, 216)
luma = per-frame mean
d    = per-frame mean abs(frame - prev)  # motion energy
jerk = abs(diff(d))                      # pops / stutter
```
| metric | catches | target |
|---|---|---|
| `p10(d)` per scene | frozen frames | **> 0.20** |
| `min(d)` globally | truly dead frames | **> 0.05** |
| runs of `d < 0.40` | retention-killing dead zones | none > ~0.5 s |
| `p95(jerk)` per scene | elements snapping | **< 2.0** |
| count abs(delta luma) > 8 | strobing | **0** |
| `min(luma)` | dark flashes | within ~25 of mean |
| peak of `d` near each cut | picture leading sound | **0 frame offset** |

### Audio telemetry
```python
M, S = (L+R)/2, (L-R)/2
corr  = corrcoef(L, R)
width = rms(S)/rms(M)
ST    = -0.691 + 10*log10(mean(M[w]**2))    # 400 ms window, 100 ms hop
band_share = abs(rfft)**2 per band / total
```
| metric | catches | target |
|---|---|---|
| L/R correlation | a "stereo" mix that is mono | **0.55 - 0.80** |
| side/mid | no width | **> 0.25** |
| 120-500 Hz | mud | **< 58 %** |
| 1-4 kHz | starved presence | **> 7 %** |
| 4-8 kHz | no crispness | **> 10 %** |
| short-term minimum | dropouts between phrases | within **9 LU** of mean |
| loudness range | inconsistent energy | **< 16 LU** |
| onset density / largest gap | sparse ASMR texture | **> 2/s** / **< 1.5 s** |

### Design telemetry
- WCAG contrast on every colour pair: **>= 4.5:1**.
- Distance of every text baseline from each frame edge vs the platform safe area.

---

# 5. PLATFORM & EDITING LAWS

### 5.1 SAFE AREA — check this before anything else
**All content lives in `y in [180, 1500]` of a 1080x1920 frame.**
```
0    - 180   DEAD (platform chrome)
142  - 210   progress hairline + "01 / 06  CHAPTER"
300  - 520   headline (max 2 lines)
560  - 1060  graphic cluster (exactly ONE)
1060 - 1298  stage, ground line GY = 1298
1340 - 1408  payoff  (PAY_Y = 1374)
1430 - 1476  caption (CAP_Y = 1452)
1500 - 1920  DEAD (platform chrome)
```
When the grid compresses, **scale the character too** and re-anchor every prop tied to the old ground line.

### 5.2 TRANSITIONS — tint, never flood
```python
tint = 0.18*accent + 0.82*paper     # panel body, luma stays ~220
glow = 0.40*accent + 0.60*paper     # feather
# sweeping edge, bottom to top:
#   H*0.044 .. H       -> tint
#   H*0.026 .. 0.044   -> glow
#   H*0.007 .. 0.026   -> full accent  (thin leading band)
#   H*0.000 .. 0.007   -> INK hairline (crisp edge)
```
- Window **centred on the cut**: `c - TDUR/2 -> c + TDUR/2`, so full cover lands on the beat and the VO start.
- Freeze the outgoing scene while `p < 0.5`.
- `TDUR = 0.46`, `TLAG = 0.050`.
- **ONE transition type for the whole film.**

### 5.3 NOTHING ON SCREEN IS EVER PERFECTLY STILL
```python
def fl(t, i=0, a=5.0, w=1.0):
    return sin(t*(0.78*w) + i*1.37)*a + sin(t*(1.23*w) + i*0.61)*a*0.42
```
Apply to every revealed prop group with a per-element phase offset `i`.

### 5.4 SUB-PIXEL CAMERA
```python
iz = 1.0/z
ox = (W - W*iz)*0.5 + drift_x      # float drift, two incommensurate sines
oy = (H - H*iz)*0.5 + drift_y
frame = frame.transform((W,H), Image.AFFINE, (iz,0,ox, 0,iz,oy), Image.BICUBIC)
```
- Per-scene push amplitude, not one identical move: `(.026,.034,.020,.038,.028,.042)`
- Alternate direction by scene parity.
- Arrival settle: `exp(-lt*6.4) * sin(lt*16.5) * 0.0052`
- **No shake. Ever.** It is the cheapest-looking tool in motion graphics.

### 5.5 TYPOGRAPHY
**Extrude toward the light:**
```python
def _ext_col(col):
    if sum(col) < 220: return (201,193,177)   # warm paper emboss under INK
    return tuple(int(c*0.50) for c in col)    # darkened face under an accent

ex = int(sz/15) if sz >= 68 else 0            # captions get none
for k in range(ex, 0, -1):
    draw.text((cx + k*0.54, y + dy + k*0.64), word, font=f, fill=ext_colour)
draw.text((cx, y + dy), word, font=f, fill=face_colour)
```
*A dark extrusion under near-black ink is invisible - that is why ink gets a LIGHT emboss.*

**Kinetic emphasis:** the highlighted word lands **8.5 % oversized** and settles to 100 % across its reveal, extrusion and all.
```python
k = 1.0 + 0.085*(1 - e_out(word_progress, 2.0))
```

**Reveal easing:** overshoot `e_back(s=1.12)`, stagger `.30`, ramp `.72`, rise `e_out(2.2)`.

### 5.6 CTA
The most important element must read as a **lit object**: a soft white band sweeps diagonally across the pill on a 1.6 s cycle — 11 feathered strokes, each <= 18 % alpha, slanted ~13 deg off vertical.

### 5.7 PARTICLES
26 pieces / 3 shapes (rect, ribbon, disc) / per-piece 3D tumble with foreshortening `height x (0.34 + 0.66*abs(cos(t*rate + i)))` / speed streaks on the fast ones / accent + ink only, never a rainbow.

### 5.8 PALETTE
```python
PAPER (248,244,233)  INK (26,24,22)  SOFT (132,125,114)
ACC = [(178,44,32),(28,82,190),(86,54,194),(166,74,14),(14,112,80),(146,100,12)]
ACC_HI = [tuple(min(255,int(c*1.34+22)) for c in a) for a in ACC]   # for dark fills
```
Max 3 colours on screen. **Character colours CONSTANT; only the world is themed per chapter.**

---

# 6. AUDIO ENGINE

### Structure
- **Dual bus:** music dry, cues through the plate. Never put the chord bed in a reverb.
- **`silk()` plate** on the cue bus only: 12 prime-spaced taps `0.0131 ... 0.4523 s`, gains `.50 -> .030`, alternating 62/38 pan, band 220 Hz - 5.2 kHz, **34 % wet**.
- **Attacks >= 8 ms** on every percussive cue (pop 3->9 ms, tap 4->8, thud 5->10). Clicky attacks are what make SFX fatiguing.
- Soft knee `tanh(x*1.05)*0.74`. Bus band 28 Hz - 14.5 kHz.
- One chord per chapter; sub pulse every 2nd beat; noise room floor ~= -42 dB.
- Per-cut stack of 6: riser `c-0.84`, whoosh-in `c-0.16` (pan -0.55), thud + sub at `c`, chime `c+0.03`, whoosh-out `c+0.20` (pan +0.55).
- Keep an **event ledger CSV** (`t, tag, gain, pan`) — the only way to debug a 248-event bed.

### Width
```python
M_ = (mix[0]+mix[1])*0.5
S_ = (mix[0]-mix[1])*0.5
S_ = bandpass(S_, 150, 16000) * 3.30
mix = [M_ + S_, M_ - S_]
```
Keep the **voice centred**; make the **bed wide**.

### Hole filling
Place a pad swell on **every measured hole**: sine stack at 146.8 / 220 / 293.7 / 440 / 587.3 Hz with a 1.004 detune layer, `sin(pi*t/T)^1.6` envelope, 2.6 s, bandpass 70-2600 Hz, right channel rolled 331 samples for width.

### Final mux (audio-only onto existing video — use `-c:v copy`)
```
[iN]atempo=X,aresample=48000,aformat=channel_layouts=stereo,adelay=D:all=1
6x amix=inputs=6:normalize=0,
   highpass=f=90,
   equalizer=f=250:t=q:w=1.0:g=-4.2,
   equalizer=f=430:t=q:w=1.4:g=-1.6,
   equalizer=f=3100:t=q:w=1.3:g=3.6,
   treble=g=2.8:f=7400,
   acompressor=threshold=0.045:ratio=3.6:attack=10:release=170:makeup=1.5,
   volume=1.92                                         -> [vo]
[vo]asplit=2[vod][vsc]
[bed]volume=0.60[bedr]
[bedr][vsc]sidechaincompress=threshold=0.024:ratio=5:attack=6:release=260:makeup=1.0[bd]
[vod][bd]amix=inputs=2:weights=1 1:normalize=0,treble=g=3.4:f=9000
loudnorm=I=-11:TP=-1.0:LRA=9, alimiter=limit=0.97
video: libx264 -preset slow -crf 23 -maxrate 2800k -bufsize 5600k -pix_fmt yuv420p
       -profile:v high -level 4.0 | aac 192k 48000 | +faststart | -t <EXACT>
```

### Audio gotchas
- **Python-loop IIR over 1.7 M samples is far too slow.** Use FFT magnitude shaping per short grain.
- **ffmpeg `asplit` -> `anullsink` aborts** (`Assertion best_input >= 0 failed`). Duplicate the chain instead of discarding a split branch.
- Target for shorts: **-12 to -11 LUFS, TP <= -0.5 dBFS.**

---

# 7. TIMING CONTRACT

Lock this before a single frame is drawn; treat it as immutable.
```
TEMPO = 1.45   LEAD = 0.30   SPB = 0.535714 s (112 BPM)
RAW   = [7.13, 10.15, 9.31, 6.40, 9.02, 8.33]

S  start    end     dur    voAt     f0   f1    nf
1  0.000   5.567   5.567   0.300     0   166  167
2  5.567  12.867   7.300   5.617   167   385  219
3 12.867  19.588   6.721  12.917   386   587  202
4 19.588  24.302   4.714  19.638   588   728  141
5 24.302  30.823   6.521  24.352   729   924  196
6 30.823  37.000   6.177  30.873   925  1109  185
                                     sum nf = 1110
VO atempo/adelay: 1.446/300 . 1.351/5617 . 1.441/12917 . 1.525/19638 . 1.484/24352 . 1.487/30873
```
**THE RE-FIT LAW:** if the duration target changes, **re-fit `atempo` per scene**. Do not trim, do not cross-fade, do not stretch the whole mix. Every scene gets its own rate so the cuts stay on the beat.

---

# 8. BUILD & ENVIRONMENT

```bash
python3 src/clean.py   0  555 build/c0.mp4  &      # shard in parallel
python3 src/clean.py 555 1110 build/c1.mp4  &
wait
python3 src/make_asmr.py                           # -> build/asmr_bed.wav
ffmpeg -f concat -safe 0 -i build/clist.txt -c copy build/silent.mp4
ffmpeg ... (mux chain above)
```
- **Shards must encode to mp4 inline.** Raw-frame shards are infeasible (3.4 GB each).
- Shards must be **bit-identical at the seam** — every animation function must be a pure function of `t`.
- **Only re-encode what changed.** Audio-only fixes use `-c:v copy` (7 s) vs a full re-encode (58 s).
- Long renders go to a background process, never a time-capped shell call.
- **Do not pipe a long render through `tail -N`** — `tail` buffers until exit. Poll with `stat -c%s` or read the log after. (`tail -2` is invalid; use `tail -n 2`.)
- `ffprobe` is **not** shipped with `imageio_ffmpeg`. Use `ffmpeg -i file 2>&1 | grep -E "Duration|Stream"`.
- `/tmp`, pip packages and `build/` do **not** persist between sessions — re-install and re-create them, and regenerate `clist.txt`.
- `cat -n` truncates long files. Read with `sed -n 'A,Bp'`, ~170 lines per call.
- **An f-string containing a literal newline is a `SyntaxError`.** Write a heredoc script file instead of `python3 -c`.
- Render cost: **0.17-0.25 s/frame** at 1080x1920 on 2 cores.

---

# 9. REJECTED — DO NOT RE-PROPOSE
Hoodie as a closed trapezoid / outlined circle+pupil eyes / filled rectangle collar / mitten hands / mono SFX / five different transition types in one film / flat chalk-line stickman (client rejected) / high element density (client rejected).

---

# 10. QA GATE — NOTHING SHIPS UNTIL ALL OF THIS PASSES

**Container**
- [ ] duration exact to the frame / 1080x1920 / 30 fps / yuv420p / H.264 High@4.0 / `+faststart`
- [ ] `ffmpeg -v error -f null -` decodes with zero errors
- [ ] frame 0 is not black (it is the thumbnail — check mean luma and bright-pixel count)

**Design**
- [ ] all content inside `y in [180, 1500]`
- [ ] every accent >= 4.5:1 against its background
- [ ] every text-on-fill pair >= 4.5:1
- [ ] max 3 colours on screen / exactly one graphic cluster per scene
- [ ] character colours identical in every scene

**Motion**
- [ ] zero frames with abs(delta luma) > 8 / darkest frame within ~25 of the mean
- [ ] `p10` frame-diff > 0.20 in every scene / global min frame-diff > 0.05
- [ ] `p95(jerk)` < 2.0 in every scene
- [ ] transition energy peak lands ON the cut frame
- [ ] no text/character collision in any scene
- [ ] `foot_drop == 0.0` for every standing pose

**Audio**
- [ ] L/R correlation 0.55-0.80 / side/mid > 0.25
- [ ] 120-500 Hz < 58 % / 1-4 kHz > 7 % / 4-8 kHz > 10 %
- [ ] short-term minimum within 9 LU of the mean / loudness range < 16 LU
- [ ] integrated -12 to -11 LUFS / true peak <= -0.5 dBFS
- [ ] VO vs bed measured from **separate stems**, +9 to +11 dB during speech

---

# 11. DELIVERY ARTEFACTS
1. the mp4, with its **sha256 prefix recorded**
2. `VIDEO_Vn_NOTES.md` — what changed, with **before -> after numbers**
3. `FORENSIC_AUDIT.md` — the measured defect list for the next pass
4. character sheet PNG (front views / expressions / pose studies)
5. ASMR event ledger CSV
6. QA contact sheet (6x2 frames spanning all scenes, with safe-area boxes drawn on)
7. **restore points** for every file rewritten (`*_backup.py`)

---

# 12. THE TEN LAWS

1. **Measure, never eyeball.** Decode the delivered file and run the telemetry.
2. **Check the platform safe area before anything else.** `y in [180, 1500]`.
3. **Contrast every colour pair.** Big type lies to you; small type does not.
4. **Tint transitions, never flood them.** Luma must not crash.
5. **Depth, not the picture plane.** A flat rig is a puppet, forever.
6. **Clamp every joint.** Elbows forward only, knees backward only.
7. **Nothing on screen is ever perfectly still** — and no animated value may pass through `int()`.
8. **Width is the product** in ASMR. Voice centred, bed wide.
9. **The mix never breathes out.** Fill every measured loudness hole.
10. **Premium is subtraction.** When in doubt, delete it.

---

# 13. WHAT THE 42 s "POWERFUL MAN" SHORT ADDED (ledger 39–45)

Built `stickman_power_42s.mp4` (sha `3af2f5fda7a99b2d`, −11.7 LUFS, peak −1.49 dBFS,
ALL 18 GATES PASS) on the v9 engine with a new timeline, six new poses and a
re-voiced bed. Notes: `VIDEO_POWER_NOTES.md`. Seven things were learned.

**39 — Blend poses, never switch them.**
v9 changed poses with `p_point if lt > .9 else p_think`; the solver re-grounded
the feet so it never *failed*, but every switch was a 1-frame jump. `blend(fa,
fb, t, t0, d, s)` interpolates the whole joint dict with `e_back` overshoot and
then runs `phys()` on the result. Three times more pose changes than v9 at a
lower jerk p95 (1.77). Rule: any two poses that share a timeline must be blended.

**40 — The rig's `lean` is a body-space rotation.**
`_skeleton` applies `lean` as `_rz` *before* the yaw, so at yaw ≈ 0 it is a
sideways bend, not a forward one. A squat at yaw 40 with lean 24 read as a man
tilting over — the forward component is `sin(yaw)`. Use yaw ≥ 60 for any pose
whose meaning is a forward lean (squat, bow, push), or add a true pitch axis.

**41 — Measure the voices before you write a spectral gate.**
`tap()` is band-limited to `900 + 2300*bright` ≤ 3.2 kHz; no amount of 5.6 kHz
"shaker" taps can lift the 4–8 kHz share (it sat at 1.4 %). A dedicated `air()`
voice (noise, 4.2–9.2 kHz, raised-cosine edges) fixed it in one build. Second
half of the same lesson: a D2 (73 Hz) pad root put 46 % of the bed-only energy
under 120 Hz. Keep chord roots ≥ 110 Hz under a voice-led short.

**42 — A clamping limiter is a loudness wall.**
`alimiter … level=disabled` only clamps. With the ceiling at 0.70–0.74 the film
sat at −12.5 … −12.8 LUFS **whatever `loudnorm I=` was set to** — the crest
factor, not the target, decided the loudness. Drive the lookahead limiter
(`volume=1.25` ahead of it) to trade crest for level, then measure the *decoded
AAC* peak: overshoot above the PCM ceiling was 0.9–2.1 dB and erratic (one
setting decoded at 0.0 dBFS, the next at −1.4). Never trust the PCM number.

**43 — The pads are the stereo width.**
Lowering the pads 0.95 → 0.80 to buy 4–8 kHz margin pushed L/R correlation from
.75 to .815 — the detuned pad is what decorrelates the channels. Width and air
are coupled through the same element. Restore width with `extrastereo` (1.85 →
2.4) rather than by putting the pads back; it leaves the spectrum alone.

**44 — Captions that mirror full sentences overflow a 1080 px frame.**
Five captions ran 1028–1162 px at the v9 size 50; two were clipped at the edge
and no gate caught it — the probe is 180 px wide and nothing measured text
extents. `caption_fit()` measures the line and scales to a 936 px safe width.
And the camera moves the safe area: under z 1.07 / pan −12 the caption glyph
bottom reached Y 1523 (safe line 1500). Compute the worst-case output Y of every
text band over *all* frames before locking a camera; this build settled at
Z0 1.020, AMP ≤ .024, pans 7/9, caption y 1440 → worst 1495.

**45 — Fit the voice by cutting pauses, not by `atempo`.**
v9 stretched the TTS 1.35–1.53× and it is audible. Here internal pauses were
capped at 0.30 s and the edges trimmed (47.3 → 38.6 s), the voice stays at
pitch, and the picture is cut to the voice (`timeline_power.py` recomputes
scene starts from the fitted lengths). Cross-correlation on the delivered file
puts all six clips within +5 ms of plan — the 5 ms is the limiter's lookahead.

---

# 14. WHAT THE SHADE REMAKE ADDED (ledger 46–49)

Rebuilt the same 42 s film as `shade_power_42s.mp4` (sha `3a0de99bc85e1caa`, ALL 18
GATES PASS) with the user's own hooded black-suit figure — SHADE — on the toon 3D rig,
and a hybrid charcoal/paper look where a diagonal seam divides the frame. Notes:
`VIDEO_SHADE_NOTES.md`. Four things were learned.

**46 — A solid hero is a luma mass.**
The v9 swipe crossed a thin stickman and never moved the frame's luma; the same swipe
crossing a 7 %-of-frame black figure in under three frames produced Δluma 11.4 at three
cuts (frames 191, 580, 782). Rule: any wipe that crosses the hero in < 3 frames must
dissolve the outgoing layer first (dissolve over tp < .5, then wipe). Build 2 landed at
5.95 with nothing else changed.

**47 — Two-tone everything that crosses a dark/paper seam.**
The seam is a character, not a backdrop. Transition stripes, props, type and the
hero's rim all need a paper-side and a charcoal-side value (`PAPER_ON_DARK` 236,232,222
against DARK 38,36,41); a single-tone element vanishes on one side and the contrast
rule (≥ 4.5:1) fails silently on the other.

**48 — Props for a 1/5.2-head character need their own sizes.**
Stickman prop scales (`book`, `coin`, `pill`) were tuned to a 1/7-head figure; on SHADE
they read as toys. `book2` and friends are sized from the hero's hand span, measured on
the rendered sprite, not inherited.

**49 — Gate instruments measure the look, so a deliberate dark edge needs a
re-calibrated test, not a waiver.**
The black-sliver detector ("> 50 % of an edge line below 40/255") flagged the charcoal
wedge itself. A transform sliver is 0 and the charcoal never decodes under ~28, so the
test became "an edge line ≥ 95 % below 12/255" — the geometric guarantee (sampled
rectangle inside the source) is still asserted on every frame. Never waive a gate;
re-derive it from what the new look can and cannot produce.

---

# 15. WHAT THE 90 s "IZZAT" SHORT ADDED (ledger 50–56)

Built `shade_respect_90s.mp4` (2700 frames, sha `f3d0f1a21ec59b00`, ALL 18 GATES PASS)
— a nine-chapter mini-story with a cinematic layer (dolly push-ins, 0.5× parallax far
plane, depth of field, light shafts, dust, slow-mo) and a new voice (voice-01). Notes:
`VIDEO_RESPECT_NOTES.md`. Seven things were learned, two of them the hard way.

**50 — Wedge offset must be continuous across cuts.**
A 160 px jump of the seam under the transition band measured ≈ 15 luma on the probe —
twice the gate. The seam's offset is a timeline value like any other: ease it inside the
receiving scene (S1/S2 +260 → S3 eases to −160 → S4 to 0), never step it at the cut.

**51 — Far-plane silhouettes are the hero rig flattened to one tone and blurred by
distance.**
Drawing extras as separate art broke the DNA; rendering the SHADE rig once per 1/6 s
pose bucket, flattening to (96,92,100) and Gaussian-blurring by depth gave a crowd that
is unmistakably the same species — and cached, it costs nothing.

**52 — Never key a sprite cache on a continuously animated value.**
The silhouette cache was keyed on dolly size, head angle and fade alpha; every frame
produced new keys and the shard was OOM-killed at 1.9 GB. Quantise (size /16 px with a
resample, head /2°), apply alpha at paste time, and bound the cache (72 entries ≈ 80 MB;
max RSS fell to 396 MB).

**53 — Dolly = world scale about the floor centre; UI static.**
A camera push is a scale of the *world* (floor, hero, props, far plane at 0.5×), not of
the frame: chrome, captions and the progress line stay put, so the safe-area numbers
stay true. Props placed in world space go through `wx()`; `on_paper` is asserted in
screen space, after the dolly.

**54 — Two x264 encoders and two renderers do not fit in 2 GB.**
Parallel shards worked for the light v9 renderer (≈ 150 MB each); with the cinematic
layer each renderer holds ≈ 400 MB and each encoder ≈ 490 MB — the second shard's
encoder was OOM-killed. Render shards sequentially; never run the bed build while a
shard is live; and a resume script must count finished frames by *decoding*
(`-map 0:v:0 -f null -`), because ffmpeg 7 prints no `frame=` line under `-c copy`.

**55 — Pad the VO bus to the full duration before the sidechain pair.**
The VO bus ended with the last clip (84.94 s); `sidechaincompress` and the second
`amix` end with their shortest input, so the bed went silent for the 5 s tail — gate:
longest silence 4.56 s, L/R correlation .45. `apad=whole_dur=PADD` on the VO bus before
`asplit` fixed both numbers in one line.

**56 — A new voice is a new mix.**
voice-01's ≈ 8 kHz sibilants, pushed by the locked chain (+2.8 dB @ 7.4 k, +3.6 @ 3.1 k,
drive 1.25), flat-topped the limiter; flat-topped HF overshoots up to +5 dB in AAC
decode, so the PCM peak read .746 while the decoded file peaked at 0.0 dBFS (hundreds of
full-scale bursts, all on "s"). Lowering the ceiling alone cannot fix it: de-ess *before*
the bus (`deesser=i=0.7:m=0.75:f=0.4`), ceiling .71, and leave ≥ 2.5 dB under 0 dBFS.
Three corollaries from the same build: (a) `extrastereo m=2.4` drives bed-only passages
anti-phase (tail correlation −.71) — a 90 s cut with 25 % bed-only time needs ≈ 1.7;
(b) single-pass `loudnorm` is content-dependent, so any bed change re-opens the peak
gate — always re-measure the decoded file; (c) a bed-only tail dilutes the 4–8 kHz
share — give the tail its own air (hiss +2.4 dB, shimmer, ticks).

**57 — Caption widths are measured, never squeezed.**
Every CAPS entry is measured with `F(40, 600)` against `CAP_MAX_W` (936) at build time;
an entry that does not fit is *shortened* (fewer words, same meaning), never fitted by
lowering the size floor. Found when the IZZAT captions were ported to v2: the floor is a
legibility contract with the viewer, the width is a layout contract with the chrome.

**58 — Cut to the voice; never pad the voice to the cut.**
IZZAT v1 reached its 90 s brief with 22 s of air (chapter tails 1.3–2.6 s) and the user
heard it as "the pauses make the length". v2 keeps the identical nine fitted clips and lets
the picture follow the voice: chapter breath 0.55–0.70 s (lead 42 % / tail 58 % of the
breath, so the first word lands just after the cut), 0.60 s cold open, 1.85 s end card —
75.19 s, voice share 90 %. A short is as long as its sentences.

**59 — One transition kind per boundary, drawn from a library and a plan.**
Every boundary is a shot change (33 shots in 75 s, 0.9–5.0 s each, median 2.2 s) and every
boundary gets its own transition kind from a 15-kind library (cube h/v, zoom-through,
whip h/v, iris, slices, ink, wedge, card, spin, sweep, blur, doors, shatter). The plan is a
list (`respect2.PLAN`), asserted against the shot count and against "never the same kind
twice in a row"; the sound bed reads the same list (`make_asmr_respect2.tr_cue`) so each
kind has one matched cue. Durations .34–.70 s, both neighbours on the hybrid palette,
`fillcolor=DARK` on every warp — the per-frame Δluma < 8 and black-edge gates still apply
to all fifteen.

**60 — No continuous noise floor; the air comes from the cues.**
The v9/POWER/IZZAT-v1 beds carried a `room` + `hiss` layer (and a 0.6 s hat/shaker grid)
to keep the 4–8 kHz share above 10 % in bed-only passages. The user hears a constant floor
as "radio static". v2 removes both; the bed-only passages (≈8 s: the breaths, the open,
the end card) get their 4–8 kHz energy from the transition cues that sit exactly in them
(air, glass, shimmer, doppler) — measured 18 % in those passages before the mux. Also:
`place_st(pad1, st − 0.25)` with st = 0 was silently dropped (`t < 0 → return`) in every
earlier bed and the hiss hid the hole; clamp pad starts to 0.

**61 — When the edit density changes, re-derive the gate, do not re-read it.**
Two v1 gates passed for the wrong reason and one failed for the wrong reason once IZZAT v2
had 32 transitions in 75 s (28 % of all frames inside a transition):
(a) `jerk_p95 < 2` over *all* frames measured the transition onsets, not stutter — v2 measures
it on shot frames (windows ± 3 f excluded; .48) and caps every transition window separately:
`trans_jerk_max < 8` = no step in motion energy larger than the cut cap. That cap found real
flaws: the wedge wipe ran B→A→B (inverted mask, two hidden hard cuts), the iris spent half its
duration off-frame (r = 2300 for a 1226 px corner), the wedge swept ±Hb for a 0..Hb field,
the carousel chips popped in with no alpha, and smoothstep onsets in 10-frame whips. Fixes:
quintic ease `e_q` (zero acceleration at both ends), area-uniform iris (r ∝ √e), edges that
cross the frame over the whole duration, entrances that end after the transition (the S1
payoff sweep now *lands* on the beat instead of cutting on it).
(b) `all_120_500 < 58` passed in v1 (55.9) only because the hiss floor diluted the voice's
own low-mids; without the floor the same voice reads 60.9. The honest fix is on the source:
250 Hz −5.4 dB (was −4.2) and 160 Hz −1.5 dB on the VO bus → 56.1, plus a five-partial pad
(the v9 two-sine pad put 95 % of its energy in 120–500 Hz).
(c) `place_st` dropped any event at t < 0 — the first pad of every bed so far never played.

**62 — A wipe step is edge speed × content contrast; patch windows, never the film.**
The last two gate failures of IZZAT v2 were not in the transition maths but under it: a hard
14 px wedge edge crossing the frame at ≈170 px/frame over a row of dark silhouettes (and the
hero) is a one-frame luma step of 9.6 even with a soft tint band, because the step is the
contrast *under* the edge times the width swept per frame. Rule: over figure-dense incoming
shots the wipe edge is soft (≥ 100 px, here 110) and the duration long enough that no frame
sweeps more than ≈ 1/12 of the field (`TD['wedge']` .64) — measured 9.6 → 6.2 / 5.7. Workflow
rule from the same session: a transition tweak is a *window* job — `respect2.py A B out.mp4`
renders only frames A..B, `splice_windows.py` streams master → swap → one encoder, and the
verification probe is uint8 at 180×320 per window; a float32 full-film probe (≈ 520 MB) next
to two ffmpeg pipes hung the 2 GB sandbox for 25 minutes. Pre-check every new kind with a
luma trace before any shard render (ledger 61's cap applies per window: `trans_jerk_max < 8`).
