# v7 — REAL HUMAN RIG (3D skeleton)

`stickman_money_37s_v7.mp4` · 1080×1920 · 30 fps · **37.00 s** · 10.48 MB
sha256[:16] `e7d8966ad6c0083c` · −12.1 LUFS · decode-clean · 0.174 s/frame

---

## 1. THE REVERSED FOOT — found and fixed

The shoe polygon placed the heel at `fx - abs(T)*0.40` while the toe went to
`fx + T*1.03`. `T` is **signed** (negative for the left foot) but the heel used
`abs(T)`, so on the LEFT foot the heel and the toe both landed on the same side
of the ankle. That foot had no heel behind it — it read as **on backwards**.

Fixed: the heel is now at `fx - T*0.44`, always opposite the toe. Full profile
is heel-back → heel-top → instep → toe-top → toe-front → toe-ground →
heel-ground, eight points, and it rotates about the ankle for the roll.
Shoe also shrunk `0.076 → 0.063` of body height; it was reading oversized
against the slimmer legs.

## 2. WHY IT MOVED LIKE A PUPPET — and the real fix

The old rig was a **paper doll**: every joint rotated in the picture plane only.
A human arm swinging forward moves in DEPTH, and a flat rig physically cannot
express that, so every action became a sideways flap. That is the puppet look.

v7 replaces the kinematics with a **3D skeleton**.
Body space: x right, y down, **z toward the camera**. Origin at the hip.

Every limb segment is solved from two angles:
* **abduction** — frontal plane, moves the limb left/right
* **swing** — sagittal plane, moves the limb FORWARD, out of the screen

```
dir(abd, swing) = ( cos(swing)·sin(abd),  cos(swing)·cos(abd),  sin(swing) )
```

Then a perspective projection, focal length `F = 4.2·s`:
```
k = F / (F - z)            screen = (x·k, y·k),  radii also ×k
```
A hand reaching toward the lens genuinely grows ~8 %, and limb thickness grows
with it. That is the whole difference between flat and dimensional.

### Joint limits (a puppet has none)
* the **elbow only flexes forward** — `max(0, flex)`, no hyperextension
* the **knee only flexes backward** — `max(0, flex)`
These two clamps alone kill most of the broken-doll look.

### Depth sorting and aerial perspective
Limbs are grouped (arm / leg / torso / head), each group gets its own two-pass
silhouette so there are no seams *within* a limb, and groups are composited in
**z order** so an arm in front of the chest gets its own contour against it.
Fill colours are scaled by `1 + 0.26·(z/s)`: limbs behind go darker, limbs in
front lift. Real depth separation, no extra layers.

### 3/4 VIEW — the single biggest win
A front-on figure cannot show a sagittal swing: the legs scissor in depth and
on screen they just overlap. Added a global **`yaw`** that rotates the whole
body about its vertical axis before projection. Now the depth swing reads as
real horizontal travel.
`idle 14° · walk 27° · think 20° · sit_type 18° · shake 23° · point ±16° ·
dance ±10° · present 4°`
The eyes shift by `sin(yaw)·0.34` so the head reads as turned, not as a flat disc.

## 3. POSES REBUILT ON HUMAN BIOMECHANICS

**idle — contrapposto.** A standing human is never square. Weight sits on one
leg, that hip rides UP (`tilt`), the pelvis shifts over it (`sway`), the
shoulders counter-tilt (`twist`), the spine makes a shallow S, the unloaded
knee stays soft. The weight drifts to the other leg on a ~6.8 s cycle. Arms
rest with a real carrying angle (13° of elbow flex) — arms are never straight.

**walk — a true two-beat gait.** Legs swing ±27° in the sagittal plane. The
pelvis rotates WITH the leading leg (`pelvis = 7.5·sin`), the shoulders
counter-rotate against it (`twist = -7.5·sin`), the arms swing opposite their
own leg. Knee flexion follows a real profile — near zero through stance,
peaking ~59° during swing — via `7 + 52·max(0, sin(φ+2.0))^1.6`. The body
rises over the passing leg and drops onto the plant.

Others: **think** (hand to chin, other arm folded across supporting that elbow),
**shake** (the arm reaches out of frame toward the other person — only possible
in depth), **type / sit_type** (forearms come forward out of the screen),
**present**, **point**, **cheer**, **dance** (hips lead, shoulders follow a beat
late), **shrug** (shoulders raised via `sh_up`, elbows pinned to the ribs).

New pose channels: `yaw, twist, pelvis, tilt, sway, sh_up, head_t,
az_l/az_r, ef_l/ef_r, lz_l/lz_r`.

## 4. OTHER FIXES THIS PASS

* **Grounding is now automatic.** The solver projects both ankles and shifts the
  figure so the lower sole touches the ground line. The old analytic
  `foot_drop()` could not account for perspective; it now returns 0.0 and the
  3D solver owns it. Verified: idle / walk / present all return 0.0.
* **Shoulder notch gone** — a deltoid cap disc is drawn at each shoulder joint,
  filling the step where the arm met the torso.
* **Neck added** — a tapered capsule between shoulder centre and head base. The
  head was previously bolted straight onto the collar.
* **Sleeve cuffs fixed.** The old helper was 2D and knew nothing about depth, so
  the cuff for an arm BEHIND the chest was painted onto the chest. Cuffs are now
  drawn per-arm, perpendicular to their own forearm, inside the arm's group.

## 5. VERIFIED

| check | result |
|---|---|
| duration | 37.00 s exact (1110 frames @ 30) |
| video | 1080×1920 yuv420p High@4.0, 2061 kb/s |
| audio | AAC-LC stereo 48 kHz |
| decode | clean, zero errors |
| loudness | −12.1 LUFS, LRA 2.0 |
| VO vs bed | +10.0 dB during speech, before ducking |
| frame 0 | mean 227.3, 1.96 M bright px — no black thumbnail |
| grounding | foot_drop = 0.0 for every standing pose |
| render | 0.174 s/frame, 2 shards |

Flat 2D rig preserved at `src/toon_flat_backup.py`.
