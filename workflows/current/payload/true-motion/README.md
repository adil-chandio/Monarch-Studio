# Monarch — no-jelly motion revision

## Status and scope

The user rejected the old recycled-still/mesh-warp film. **It is not an accepted
realistic 3D result.** This task contains two explicitly different approaches:

1. **Original 3D motion experiment**: a new industrial vault, charcoal garment,
   43-bone standing rig, length-preserving limb IK, planted-foot step, cuff/hand
   action, head turn, and a separately modelled gold crown above MONARCH STUDIO.
   The identity surface uses the user's previously measured capture-derived
   face mesh, not the old full-frame photographic plates. The procedural avatar
   **did not pass photoreal visual review**; do not market it as a finished film.
2. **44.4-second live-action VFX alternative draft**: genuinely moving face/body
   pixels from the user's supplied performance, a newly generated vault
   environment, a simple black shirt color grade, original synthesized sound,
   and a held 3D-rendered crown end card. This does **not** generate new full-body
   acting, a tailored suit, or the reference's action choreography.

Neither technical tests nor successful encoding certify artistic quality,
identity accuracy, seamless matting, or user acceptance.

## Source files

- `src/build_vault.py`: new 3D set, wardrobe, rig, action, and brand scene.
- `src/identity_head.py`: identity-only adapter from the user's prior private
  3D source package; no prior environment or still-video plates imported.
- `src/motion_math.py`: pure length-preserving IK and world-space foot targets.
- `src/render_vault.py`: native-frame CPU rendering, atomic PNG completion,
  scene/settings fingerprints; no optical flow or image-space body deformation.
- `src/composite_live.py`: original-performance matting/edit. Completed shots
  are reused only for matching processing/shot/background fingerprints. The
  decoder refuses to silently fill a short source with frozen frames.
- `src/finish_live.py`: original sound design, normalization, concat/mux, full
  decode/frame-count checks, and a candid delivery report.
- `tests/test_motion.py`: 10 motion/claim/resumability regression tests.

## Private inputs and runtime

See `records/BRIEF.json` for the user-provided Drive references. Raw identity
videos, head texture/mesh, generated imagery, `.blend`, frames, packages and
exports are intentionally **not in Git**. No credentials are required or stored
in these files. No raw personal video is included in a distributable source ZIP.

Local staging during this task:

```
.cache/monarch-true-motion/
  raw/front.mp4
  raw/side.mp4
  prior-source/work/character/{face_mesh.json,face_albedo.png}
  vault-empty.png
  brand-final.png
  new-scene-v3/THE_VAULT.blend
  live-shots/
```

The original generated look/concept image is visual direction only; it is NOT
passed off as a moving character in the live-action draft.

Use Python 3.11 and `pip install -r requirements.txt`. Blender and the OpenCV
wheel need Linux X/GL runtime libraries even for this CPU/headless workflow.
On a normal Debian-family workstation these include `libxrender1 libxxf86vm1
libxfixes3 libxi6 libxkbcommon0 libsm6 libice6 libgl1`. In the restricted task
sandbox they were resolved in an excluded local cache; pinned provenance and
hashes are in `records/NATIVE_DEPENDENCIES.json`. Those binaries are not shipped.
The cache is ephemeral; a fresh session must restore inputs/dependencies, not
assume that ignored files persisted.

## Reproduce

From the repository root, after restoring private inputs:

```bash
ROOT=workflows/current/payload/true-motion
python3 "$ROOT/src/build_vault.py" \
  --identity-root .cache/monarch-true-motion/prior-source \
  --output .cache/monarch-true-motion/new-scene-v3/THE_VAULT.blend

# Render only matching missing frames; change the output directory if the scene changes.
python3 "$ROOT/src/render_vault.py" \
  --blend .cache/monarch-true-motion/new-scene-v3/THE_VAULT.blend \
  --output .cache/monarch-true-motion/brand-native \
  --select c24 --width 720 --samples 32
cp .cache/monarch-true-motion/brand-native/c0024.png \
   .cache/monarch-true-motion/brand-final.png

python3 "$ROOT/src/composite_live.py" \
  --root .cache/monarch-true-motion \
  --out .cache/monarch-true-motion/live-shots
python3 "$ROOT/src/finish_live.py" \
  --shots .cache/monarch-true-motion/live-shots \
  --out deliverables/monarch-vault

python3 -m unittest discover -s "$ROOT/tests" -v
```

Use the recorded process ID before re-running an interrupted job. Do not start
parallel duplicate encoders. The live-action alternative is a draft, not a
silent replacement for the requested new photoreal 3D character film.

## Provenance and rights

- Actor performance/identity: the user's consented supplied front/profile videos.
- Original vault concept/background: generated anew for this task.
- 3D room/outfit/rig/animation/crown/typography arrangement: created in this task.
- Identity-only face surface adapter: recovered from the user's private
  `MONARCH_CHAOS_3D_SOURCE.zip`; derived from MediaPipe Apache-2.0 topology.
- DejaVu font: see its upstream license; the private Blender scene packs it.
- Original score: deterministic oscillators/noise in `finish_live.py`; no copied
  reference audio, source speech, or voice imitation.
- Engine/native library binaries are environment dependencies, not vendored art.
