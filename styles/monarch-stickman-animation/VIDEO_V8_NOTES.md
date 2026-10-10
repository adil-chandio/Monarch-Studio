# v8 — FORENSIC FIX PASS

`stickman_money_37s_v8.mp4` · 1080×1920 · 30 fps · **37.00 s** · 10.93 MB
sha256[:16] `ff1fb7e612b48b61` · −11.9 LUFS · TP −0.6 dBFS · decode-clean

Every item in `FORENSIC_AUDIT_V7.md` addressed. Measured before → after:

| # | defect | v7 | v8 |
|---|---|---|---|
| 1.1 | caption distance from bottom edge | **202 px** (under platform UI) | **468 px** (clear) |
| 1.2 | accent contrast on paper | all 6 FAIL (gold 2.17:1) | all 6 **PASS** (4.72–7.07:1) |
| 1.2 | white-on-gold CTA | **2.39:1** | **5.18:1** |
| 1.3 | luma swing at cuts | −76 … **−131** | −2 … **−13** |
| 1.3 | frames with >8 luma jump | **49** | **0** |
| 1.3 | darkest frame | 104.1 | **199.8** |
| 2.1 | dead zones ≥12 frames | one, 0.53 s at t=5.93 | **none** |
| 2.2 | byte-identical consecutive frames | present | **0** |
| 2.3 | reveal jerk p95 (worst scene) | **4.13** | **2.62** |
| 2.4 | picture-vs-sound offset at cuts | −33 … −67 ms | **aligned** (`TLAG`) |
| 3.1 | L/R correlation | **0.9941** (mono) | **0.8544** |
| 3.1 | side/mid energy | 0.054 | **0.280** |
| 3.2 | 120–500 Hz share | 66.75 % | **58.24 %** |
| 3.2 | 1–4 kHz presence | 5.76 % | **7.10 %** |
| 3.2 | 4–8 kHz | 8.34 % | **11.10 %** |
| 3.3 | loudness holes >9 LU | **12** | **4** |
| 3.3 | short-term minimum | **−32.4 LUFS** | −29.7 LUFS |
| 3.3 | loudness range | 20.9 LU | **17.6 LU** |

## What changed

**Safe area.** Grid moved to y 180–1500. `GY 1490→1298`, `PAY_Y 1600→1374`,
`CAP_Y 1718→1452`, chrome `52→142`, headlines +30, character scaled ×0.84.
S3 desk re-anchored to seated-elbow height, S4 card row up 78 px, S5 hero in
from the left edge.

**Palette.** All six accents darkened for ≥4.5:1 on cream. `ACC_HI` added for
use on dark fills.

**Transitions.** The panel body is now an 18 % tint of the accent; only a thin
leading band carries full colour behind an ink hairline. `TDUR 0.40→0.46`,
`TLAG 0.050` so the swipe no longer leads the impact.

**Type is extruded.** `line(..., ex=)` stamps side-wall steps down-right before
the face — darkened accent under colour, a warm paper emboss under ink. Auto
`ex = sz/15` above 68 px. Word stagger tightened `.45→.30`, ramp `.55→.72`.

**Camera.** `int(W*z)` quantised the push so consecutive frames were identical.
Replaced with a sub-pixel `Image.AFFINE` resample carrying the zoom *and* a slow
two-term float drift. Per-scene push amplitude, plus a decaying arrival settle.

**Character.** Patella disc (same fix as the deltoid cap), hand lightened to
`(41,36,31)` with wider lighter creases so fingers survive delivery scale,
sneaker midsole/toe-cap/lace detail, shirt hem, knee crease above 14° flex,
inner-elbow wrinkles above 35° flex, hard contact-shadow core under the soles.

**Confetti.** 26 pieces, 3 shapes, per-piece 3D tumble with foreshortening and
speed streaks.

**Audio.** M/S width ×3.30 on the bed · air shelf 6.5–17 kHz · bus lowpass
8.2 k → 14.5 kHz · nine pad swells placed into the measured loudness holes ·
VO EQ −4.2 dB @250 / −1.6 @430 / +3.6 @3.1 k / +2.8 shelf @7.4 k ·
sidechain 18:1 → 6:1, release 360 → 280 · bed 0.40 → 0.54, VO 2.15 → 1.92 ·
+3.4 dB shelf @9 kHz on the sum.

Restore points: `src/clean_v7_backup.py`, `src/make_asmr_v7_backup.py`,
`src/toon_flat_backup.py`.
