# FORENSIC AUDIT — `stickman_money_37s_v7.mp4`

Measured, not guessed. Every number below came from decoding the actual
delivered file and analysing it.

Method: 1110 frames decoded to greyscale for motion/luma telemetry · full-res
frame re-render for pixel inspection · 36 s of PCM pulled for loudness,
stereo, spectral and transient analysis · WCAG contrast computed on the real
palette constants.

**Verdict: the file is technically clean but it is leaving a lot on the table,
and it has three defects that will visibly hurt it on platform.**

---

# TIER 1 — SHIPPING DEFECTS (these cost views right now)

### 1.1 ❌ The caption band is underneath the platform UI
```
caption baseline y = 1718  ->  202 px from the bottom
Reels / TikTok / Shorts UI eats roughly the bottom 320-420 px
(username, caption text, music ticker, like/comment/share rail)
```
**Every caption in the film is partially or fully covered on a real phone.**
The payoff line at y=1600 (320 px from bottom) is borderline too.
Top chrome at y=52 sits under the status bar / "For You" row.

**Fix:** move the content safe area to `y ∈ [180, 1500]`. Captions to
y≈1430, payoff to y≈1330, chrome to y≈150. Re-flow the whole grid upward.

---

### 1.2 ❌ Every accent colour fails contrast on the cream paper
```
accent          contrast    verdict
coral  226,85,70    3.40:1   FAIL
blue   46,118,232   3.92:1   FAIL
violet 118,86,232   4.48:1   FAIL (borderline)
amber  226,118,48   2.78:1   FAIL
green  22,150,110   3.40:1   FAIL
gold   214,158,44   2.17:1   FAIL — barely visible
white on gold CTA pill       2.39:1   FAIL
```
Large headline words survive on size alone. The **highlighted keyword in every
50 px caption does not**, and the "FOLLOW FOR PART 2" CTA — the single most
important element in the video — is the worst offender on the sheet.

**Fix:** darken every accent by 18–26 % for use on paper (keep the bright
version for fills on dark panels). Target ≥ 4.5:1. Gold must go to roughly
`(150,104,16)`. CTA pill text gets an ink colour, or the pill goes ink with
gold text.

---

### 1.3 ❌ The transitions are a dark strobe, not a smooth swipe
```
cut      before   AT CUT   after    swing
f167     223.2 ->  126.9 -> 229.5   -96
f386     222.8 ->  138.3 -> 230.3   -85
f588     214.3 ->  138.6 -> 228.7   -76
f729     222.4 ->   91.7 -> 227.1  -131   <- emerald
f925     220.9 ->  144.8 -> 228.7   -76
49 frames in the film carry a >8 luma jump
```
A 222 → 92 drop and back, **five times in 37 seconds**, on an otherwise bright
cream film. That is the opposite of "smooth"; it reads as a flashbang and it is
a photosensitivity concern.

**Fix:** stop full-bleed flooding. Options, best first —
(a) make the panel a **light tint** of the accent (85 % toward paper) with only
the thin leading bar in ink — swing drops to about −25;
(b) replace the flood with a **masked shape wipe** (a circle or diagonal band)
so only 40–55 % of the frame is ever covered;
(c) keep the colour but **cross-dissolve the luma** over 4 frames either side.

---

# TIER 2 — ENGAGEMENT LEAKS (why retention drops)

### 2.1 ⚠ A 0.53 s dead zone right after the first cut
```
frames 178-194  (t = 5.93 – 6.47 s)   frame-diff < 0.40
```
This lands in the **first 7 seconds** — the exact window that decides whether
the viewer stays. The S2 headline finishes at t≈6.12 and the first checklist
row does not arrive until t≈6.67. Nothing happens in between.

### 2.2 ⚠ 10 % of frames are effectively frozen
```
scene   p10 frame-diff
S1      0.32
S2      0.06   <- frozen
S3      0.14
S4      0.15
S5      0.06   <- frozen
S6      1.27   (this is what "always alive" looks like)
```
S2 and S5 have a tenth of their frames with essentially zero change. S6 proves
the fix: a continuously moving hero plus drifting confetti never drops below
1.27.

**Fix:** give every scene a continuous low-amplitude motion layer — the
character already breathes, so add a slow parallax drift on the graphic
cluster (±6 px over 3 s), a 0.6 % breathing scale on cards, and a slowly
travelling specular sheen on the accent shapes.

### 2.3 ⚠ Element reveals pop instead of settling
```
scene   jerk p95 (2nd derivative of motion energy)
S1 1.03   S2 3.10   S3 4.13   S4 3.11   S5 2.97   S6 0.91
```
S2–S5 are 3–4× jerkier than S1/S6. Cause: `e_back` overshoot over a very short
0.40–0.48 s window with no settle tail, so elements snap into place.

**Fix:** lengthen reveals to 0.55–0.62 s, reduce overshoot from 1.9 to 1.35,
and add a 2-frame settle. Stagger siblings by 0.09 s instead of 0.32 s so the
group reads as one gesture, not four separate pops.

### 2.4 ⚠ The cut's visual peak lands 1–2 frames before the audio impact
```
cut f167 peak at f165  (-0.067 s)
cut f386 peak at f385  (-0.033 s)
cut f588 peak at f586  (-0.067 s)
cut f729 peak at f728  (-0.033 s)
cut f925 peak at f923  (-0.067 s)
```
Small but systematic — picture leads sound by 33–67 ms at every cut.

**Fix:** shift the transition window +2 frames, or move the impact cue to
`cut − 0.05 s`.

---

# TIER 3 — AUDIO (the biggest single opportunity)

### 3.1 ❌ The mix is effectively MONO
```
L/R correlation    0.9941     (anything > 0.97 is mono)
side / mid energy  0.0544
```
A stereo ASMR bed was built — panned cues, a stereo plate, detuned pads — and
then a **mono voiceover at +10 dB was summed on top of it and swamped the lot**.
The width that was designed is not reaching the listener. For ASMR, width *is*
the product.

**Fix:**
- mid/side process the BED: push Side +6 dB before the sum
- give the VO a narrow stereo image of its own (6–11 ms Haas on a −9 dB copy,
  or a short stereo plate send at 8 % wet) so the voice has air without smearing
- hard-pan more cue pairs (the 30 day-ticks should sweep a full −0.8 → +0.8)
- target correlation 0.55–0.75

### 3.2 ❌ The spectrum is muddy and dull
```
  20-  60 Hz   0.04 %
  60- 120 Hz   6.16 %
 120- 250 Hz  34.67 %   <- 
 250- 500 Hz  32.08 %   <-  66.8 % of ALL energy in one octave and a half
 500-1000 Hz  12.35 %
1000-2000 Hz   3.49 %
2000-4000 Hz   2.27 %   <- presence band is starved
4000-8000 Hz   8.34 %
8000-  16k Hz  0.60 %   <- no air at all
```
Two-thirds of the energy sits in the boxy 120–500 Hz region, the 1–4 kHz
intelligibility band holds 5.8 %, and there is essentially nothing above 8 kHz.
This is why it can feel thick rather than crisp.

**Fix:**
- broad −4 dB shelf across 180–380 Hz on the VO (currently only −2.2 dB at 230)
- raise the bus lowpass from 8.2 kHz to 13–14 kHz; the low ceiling was added to
  kill harshness but it also removed every bit of sparkle
- +2 dB gentle high shelf from 7 kHz on the cue bus only
- add a quiet 10–14 kHz "air" layer to chimes and shimmer

### 3.3 ⚠ The mix drops out — twelve loudness holes
```
short-term loudness: mean -16.8  min -32.4 LUFS  range 20.9 LU
holes >9 LU below mean at t = 0.1, 6.2, 13.7, 15.2, 17.0, 20.2, 20.3,
                               21.7, 21.8, 25.8, 28.8, 33.8 s
largest gap between audible onsets: 2.19 s at t = 17.66 s
onset density: 1.2 per second
```
Between VO phrases the bed is ducked hard (18:1) and nothing fills the space,
so the film repeatedly falls almost silent — including at 33.8 s, inside the
CTA. A hooked short should never breathe out.

**Fix:** raise the ducked floor (ratio 18 → 8, makeup on release), add a
sustained pad swell timed into each hole, and raise ambient texture density to
~2.5 gentle events/s.

---

# TIER 4 — CHARACTER AND MOTION GRAPHICS CRAFT

From 1.35× pixel inspection of the rendered frames:

| # | finding | fix |
|---|---|---|
| 4.1 | **Hands collapse to black blobs at delivery scale.** Fingers were built correctly but at a 500 px figure the hand is ~20 px and the creases vanish. | lighten HAND to `(38,34,30)`, widen creases to `0.55·ow` in `(120,112,104)`, deepen the notches 30 % |
| 4.2 | **Visible step at the knee** where the thigh capsule (r=0.032) meets the shin capsule (r=0.0256) | add a patella disc at the knee, same trick as the deltoid cap that fixed the shoulder |
| 4.3 | **Shoes have no detail** — a white blob with a grey smudge | add a midsole stripe, a toe cap arc and two lace ticks |
| 4.4 | **Trousers and shirt are flat silhouettes** — no hem, no crease, no pocket | add a hem line, one knee crease that deepens with knee flex, a chest pocket |
| 4.5 | **Arms are perfect tubes** — no elbow definition, no sleeve wrinkle | taper the forearm more, add two short wrinkle ticks at the inner elbow that appear above 35° flex |
| 4.6 | **S3: the desk legs draw OVER the character's legs** and the laptop lid overlaps the torso — depth order is wrong for props | give props a z value and sort them into the same depth list as the limbs |
| 4.7 | **Confetti reads as dirt specks** — 14 flat diamonds | 26 pieces, 3 shapes (rect, ribbon, disc), per-piece 3D tumble with a scale flip, motion blur streak on the fast ones |
| 4.8 | **No contact darkening** under the shoes — the soft shadow floats | add a small hard-core shadow at 35 % directly under each sole |
| 4.9 | **Props never move once revealed** (cards, phone, grid) | continuous micro-float, ±4 px, phase-offset per element |
| 4.10 | **Text has no depth** despite "3D text" being requested | extrude headlines 6–10 px toward the light with a darkened accent face, plus a 1 px inner highlight on the top edge |
| 4.11 | **The camera push is linear and identical every scene** | ease the push with a slow-in/slow-out, vary amplitude per scene, add a 0.3 % settle bounce on cut arrival |
| 4.12 | **No subsurface warmth on the face** — the head is flat white with one specular | add a faint warm gradient on the lower half of the skull |

---

# WHAT "NEXT LEVEL" ACTUALLY LOOKS LIKE — RANKED PLAN

| rank | change | effort | impact |
|---|---|---|---|
| 1 | Safe-area re-flow (1.1) | S | huge — captions currently unreadable on platform |
| 2 | Accent darkening for contrast (1.2) | S | huge — CTA legibility |
| 3 | De-strobe the transitions (1.3) | M | huge — perceived smoothness |
| 4 | Stereo width + spectral rebalance (3.1, 3.2) | M | huge — this is the ASMR promise |
| 5 | Kill the dead zone + frozen frames (2.1, 2.2) | M | high — first-7-second retention |
| 6 | Reveal easing and stagger (2.3) | S | high — perceived polish |
| 7 | Fill the loudness holes (3.3) | M | high |
| 8 | 3D extruded text (4.10) | M | high — explicitly requested, currently absent |
| 9 | Hands / knee / shoe / cloth detail (4.1–4.5) | L | medium-high |
| 10 | Prop depth sorting + micro-float (4.6, 4.9) | M | medium |
| 11 | Confetti rebuild (4.7) | S | medium |
| 12 | Camera easing + contact shadow (4.8, 4.11) | S | medium |

Tiers 1–3 are roughly one build. Tier 4 is a second.
