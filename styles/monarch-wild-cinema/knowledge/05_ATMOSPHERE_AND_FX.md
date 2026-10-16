# 05 · Atmosphere and effects

## Everything here is generated, nothing is a sticker

Every atmospheric element in this engine is a per-frame function of time,
position and a seed. There is no overlay asset library, no stock flare pack, no
downloaded texture. This is deliberate and it is load-bearing:

1. **Compliance.** The channel's largest policy exposure is reposted media.
   A production made entirely of generated plates, generated atmosphere,
   synthesised score and generated type has no third-party material in it at
   all. That is not a marketing claim; it is the risk model.
2. **Articulation.** A generated element can be parameterised by the shot
   (how strong, which direction, timed to which cue). A stock overlay can only
   be dropped on top.
3. **Reproducibility.** The same plan replays the same atmosphere. A PNG
   overlay sequence cannot be re-derived from a text file.

## The elements

| element | function | ceiling |
|---|---|---|
| `god_rays` | directional volumetric shafts from the key light | strength ≤ 0.34, angle declared per shot |
| `haze` | drifting two-octave fog; the depth cue | ≤ 0.22, tint toward the plate's far colour |
| `motes` | floating particles that **respect the depth field** | ≤ 140, radius 1–4 px |
| `streaks` | directional speed stylisation | only on a beat whose narration is about speed |
| `impact` | ring + hot-core burst, additive | 0.55 s life, decays |
| `flash` | bounded light hit | ≤ 0.55 mix, decay 5.5 |
| `shake` | damped two-frequency camera shake | ≤ 12 px, `exp(-7t)` decay |
| `chroma` | lateral chromatic aberration | ≤ 2.5 (≈ sub-pixel) |
| `letterbox` | optional bars | off by default |

## The two effects that most often go wrong

### 1 · Motes that ignore depth

A floating particle layer that does not know where the subject is looks like
dust on the lens. `motes()` samples the scene's depth field at each particle's
position and scales both radius and brightness by it, so a mote behind the bear
is smaller and dimmer than one drifting past the lens. The particle field then
**participates in the parallax** instead of sitting on top of it.

### 2 · Impacts that never decay

An impact that holds is a bug. Every element here has an explicit decay:
`impact` lives 0.55 s, `flash` decays as `exp(-5.5t)`, `shake` as `exp(-7t)`.
Sustained energy does not read as intensity; it reads as a rendering fault.

## Cost control (this is where the render budget goes)

Atmosphere is the second-largest cost after the grade. Three optimisations
carried the pipeline:

| element | naive | optimised | how |
|---|---|---|---|
| god rays | 109 ms | 38 ms | build the ray field at ¼ resolution, blur small, upscale |
| haze | 62 ms | 34 ms | `cv2.multiply` blend instead of a float32 mix |
| impact | 125 ms | 13 ms | build and blur inside a bounded ROI, not the frame |
| motes | 44 ms | 44 ms | unchanged (already cheap; 80 `circle` calls) |

The ROI trick generalises: **an effect that touches 3 % of the frame must be
computed on 3 % of the frame.** The impact was the clearest case — a 420 px
burst was paying for a 1920×1080 Gaussian blur.

## Anti-patterns

- A random effect on every frame ("effect roulette").
- Two atmospheres fighting for the same beat (rays **and** streaks **and** a
  flash on one cut).
- Atmosphere on a beat that has no light source in the frame.
- Streaks or shake on a slow, quiet, factual beat.
- Haze strong enough to raise the black floor toward the platform's
  compression noise (the bed of the picture must stay below ~0.06 luma on a
  `nocturne` plate).
