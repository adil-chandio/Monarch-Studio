# AMEER KA KUTTA — v9 handoff ("cinema" pass)

Status: v9 rendered, gated **21/21** and left at `/home/user/work/AMEER_KA_KUTTA_v9.mp4` (19.23 s, 1080x1920 30 fps,
34,255,847 B, md5 `98b7fe160fddcc2d0c58d4b1c3ba9a98`). Drive upload impossible from this sandbox — see P-023; v8
remains the last Drive upload (`1D44AE8qc4wFwuAFu1UPrKPyuC-T8oshr`). Neither v8 nor v9 is accepted by the user yet.
Gate: max_dluma 6.803, jerk_p95 1.136, trans_jerk_max 6.618, black_edge 0, decoded peak −1.8 dBFS, LUFS −12.1,
bed flatness 0.073 (full report: `/home/user/work/v9_gate.txt`, brain V-018).

## What v9 adds on top of v8 (same script, same 12 shots / 11 3D transitions)

Picture (`src/cinema9.py`, wired in `src/kutta2.py`):
- `render(i)` post chain: chapter grade (HOOK warm / LUXURY teal / RAJA purple-gold / GAREEB cold-desaturated, 0.6 s blends)
  → bloom (.38, streak .26, thresh 185) → handheld camera (chapter amplitude 1.0 / 1.25 / .85 / .6, roll .55° × punch)
  → chroma split + radial rush on punches → `respect3._grade` → vignette → flash → grain. Shake is clamped to the zoom
  margin so no black edges.
- Moments: slam title *AMEER KA KUTTA?* at 0.30 s (shockwave + dust), hot-word punches at the 8 caption keywords,
  speed streaks + light cones in the drive, money rain (notes + coins) in bowl/bed, god rays on the throne, crown drop at
  10.784 s (shockwave + confetti), rain + lightning (12.5 / 15.36 s) + breath fog in GAREEB, end stamp
  (crown, *AMEER KA KUTTA.* / *insaan ya janwar?*) at 15.68 s.
- Dog rides inside the car (head through the rear window, same glass mask as the driver). Husky sprites gold-tinted
  (`husky/dog_husky.py _sprite`).
- Transition plan: carousel, tunnel, **deck_short** (0.7 s), shatter, carousel, tunnel, deck, shatter, carousel,
  tunnel_long, flare. The walk shot is only 1.12 s, so a long tunnel + a 1.0 s deck overlapped (trans_jerk 17): the
  hook→luxury brightness drop is handled by `room_close` dimming its lights to .62 over the last .84 s instead.
- `cards3d.tunnel`: B's approach decelerates over the last 35 % (cubic Hermite) so back-to-back windows do not step.
- Per-shot exposure `EXPO` (bed .80, bowl .92, crouch .90, split .95) and a filmic toe lift (0 → 14) keep bright
  rooms under the dluma cap and night skies off the black-edge detector.

Sound (`src/sfx9.py`, `src/mux_kutta2.py`):
- Every cue is a designed synth (the Drive SFX pack is unreachable; `_lib()` falls back to `sfx9.synth(name)` and prints
  which names were synthesised). New cues: braam @0, impact on slam / crown / stamp, 7 + 4 coins, confetti, thunder ×2,
  diegetic rain bed from GAREEB (two decorrelated sheets at .42, gusting droplet bursts — flatness-safe), sub drop before
  line 4 with the music dipping to .16 and swelling back, stamp ring; `whoosh_air` layered under each tonal whoosh at .26.
- GAREEB music gains raised (pad .78, lead .60) so the rain sits under a tonal bed (ST-007 no-hiss rule).

Gate rules that shaped the work: max_dluma < 8 (every element fades in ≥ 3 frames, flash ramp 5/10, punch attack 0.10 s,
punches suppressed inside transitions), jerk_p95 < 2, trans_jerk_max < 8, bed flatness median < 0.2, LUFS −12.5..−10.5,
peak ≤ −1 dBFS.

## Rebuild in a fresh sandbox (≈ 45 min)

```
bash src/husky/bootstrap9.sh blender     # venvs in /tmp (render + bpy 4.3), GL stubs, /home/user/build -> /home/user/work/build9
bash src/husky/render_husky.sh           # 170 Husky sprites (Idle 0-79, Walk 0-24, Eating 0-63, Death 25), ~30 min
# VO: add_voice (ur-PK) + generate_speech k1..k4 -> /home/user/build/kutta/vo/, then python3 src/prep_vo_kutta.py
bash src/build9.sh                       # 2 shards -> mix -> KUTTA_OUT mux -> gate
```
`/home/user/work/build9/` persists (VO, sprites, shards, mixes); `/tmp` and anything named `build` do not.

## Timeline (voice-00 timing.json)

DUR 19.23 s, 577 frames. VO at 0.30 / 3.09 / 8.16 / 11.45; shots room_wide 0–1.54, room_close –3.09, walk –4.21,
door –5.02, drive –6.23, bowl –7.15, bed –8.16, throne –9.97, crown –11.45, pave –14.56, crouch –16.74, split –19.23.

## Open items

- P-021 / P-022 (sit pose = Idle clip; SFX designed, not verified by ear) still open.
- P-023: no Drive from this sandbox → upload v9 from a session with Drive access, then log the ID in VIDEO_LOG.
- Ideas not done: a real sit clip for the Husky; per-word caption kinetic typography; a dedicated 3D crown model.
