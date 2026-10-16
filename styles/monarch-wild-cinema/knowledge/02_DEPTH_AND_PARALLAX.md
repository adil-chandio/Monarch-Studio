# 02 · Depth and parallax

## What this actually is (honest scope)

The engine builds a **2.5D image-space parallax** from a single plate. It is
*not* reconstructed 3-D geometry, and no delivery may claim that it is. What it
does is real and visible: a near plane, a mid plane and a far plane move at
different rates, so a dolly or an orbit reveals that the frame has depth.

The difference from a Ken Burns move is the whole point. A Ken Burns pan slides
a photograph behind a window. A parallax move **turns a picture into a place.**

## The depth field

`depth.field()` returns 0 (far) to 1 (near) per pixel, built from **focus
energy** by default:

```
focus = box-filtered |Laplacian(L)|
tone  = |L - median(L)|
sat   = HSV saturation
depth_raw = 0.62*focus + 0.24*tone + 0.14*sat
```

Three modes:

- `rect` — an explicit normalised rectangle. Deterministic, zero risk, no
  adaptation. Use it when the subject is known.
- `auto` — the heuristic alone.
- `hybrid` (default) — the heuristic **gated by** the rectangle: silhouette
  detail resolves inside the plateau, and the falloff is guaranteed safe
  outside it. A failed heuristic degrades to `rect` instead of producing a
  visible tear.

### Why darkness is the wrong prior — the measured correction

The first implementation used `1 - luminance` as the primary saliency term,
reasoning that a dark subject sits against a lit background. On the first
proof frame the depth map came back **inverted**: the environment was marked
near and the bear — the lit, sharp, dark-furred subject — was marked far.

This is not an edge case; it is the house style. The channel's cinematic grade
**lights the subject and drops the environment.** Any prior keyed to brightness
will invert on this style. Focus energy is the correct proxy: the subject is
sharp, the environment is shallow-DOF and soft. The plate's own design carries
the depth signal, and the depth field reads it.

Diagnostic that caught it: `depth.depth_preview(stage)` renders the field as a
TURBO heat image. **Render the depth map and look at it** before trusting a
parallax pass; the inversion is obvious in the heat image and invisible in the
motion.

## The environment canvas

A pull-back or a wide orbit needs pixels that do not exist outside the plate.
Naively requesting them gives `BORDER_REFLECT`, i.e. a **mirror smudge** at the
frame edge.

`depth.make_canvas()` instead embeds the sharp plate inside a blurred,
atmospheric extension of itself, tinted toward the far colour, with a feathered
mask. A zoom-out then reads as *receding into haze* rather than *hitting a
mirror*. Overscan is `1.22` — enough to cover the maximum displacement of the
declared camera envelope (≈ 116 px at the strongest zoom, against ≈ 211 px of
margin).

## The camera

`depth.camera_maps()` returns a remap pair for a given shot progress `p`. It
composes:

| parameter | default | note |
|---|---|---|
| `zoom` | (0.030, 0.075) | near-plane push across the shot |
| `orbit` | 26 px | lateral near-plane travel |
| `roll` | 0.42° | restrained; the WF-05 case used 0.65° |
| `drift` | −9 px | vertical settles |
| `breathe` | 1.6 px | **never perfectly still** |
| `yaw` | 2.0e-5 | coherent perspective shear |
| `ramp` | `linear` | see below |

### Eased ramps fail the motion test by design

An `e_io` ramp reaches zero velocity at both ends of a shot. On an action shot
nobody notices. On a typographic card **nothing else is moving**, so the frame
measures as frozen — this is ledger entry #33 in the stickman doctrine, and it
is why the default ramp here is linear-dominant
(`0.15*e_io(u) + 0.85*u`).

### Atmospheric separation

Rigid parallax on a soft, low-contrast generative plate can be almost
invisible — the eye needs a cue that distance *means* something. The far plane
is therefore mixed toward the plate's own computed far colour by up to
`haze_max = 0.22`, scaled per pixel by `(1 - depth)`.

This is why the proof's parallax reads on a frame that a pure geometric
diff would barely register: the geometry provides the movement, the haze
provides the *depth perception*.

## The Stage object

```python
st = depth.stage_from_file("assets/plates/01_hook_charge.jpg",
                           {"mode": "hybrid", "rect": (0.18, 0.16, 0.86, 0.98)})
frame = st.frame(p=0.35, cam={"zoom": (0.03, 0.09), "orbit": 34})
```

Build cost ≈ 2.5 s (depth field + canvas + far colour). Warp cost ≈ 96 ms at
1080p — the single most expensive stage in the pipeline, and still worth it.

## Failure modes to check, every time

1. **Inverted depth.** Render the heat preview. If the subject is not near, stop.
2. **Edge reveal.** Look at the four corners at the strongest transform, not at
   rest.
3. **Subject deformation.** A depth boundary through a face, a hand or an ear
   deforms it. Keep the plateau constant-depth across the whole subject
   cluster; feather only in empty margin.
4. **Camera-only proof.** If the source is a still and nothing else moves, the
   shot is a slideshow with a moving camera. Give the shot an event: a type
   reveal, an impact, a light change — or cut it.
