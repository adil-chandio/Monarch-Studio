# WF-04 · Chaos Video 1 — true-3D rebuild (LOOK DEVELOPMENT ONLY)

**2026-10-17 review: NOT A MASTER. Visual QA blocked.** The user rejected v2's moving/jelly-looking face and its image-plate construction, and asked for an actual realistically animated 3D Monarch model matching the reference. Preserve v2 as history; never treat its 21/21 *technical* gates as a creative sign-off.

## What this source does

- `fit_face.py` samples **one** locked REAL face v5 hero portrait once, fits measured X/Y landmarks and MediaPipe's canonical Z geometry to a **468-vertex/898-triangle OBJ**, and stores a *surface* albedo. The photographed portrait is **not** a video frame/card/plate; the head vertices and texture are static thereafter. Its UV/photo-texture use is a normal 3D material but **has not been explicitly approved** by the user (who said “images se nahi”). Do not assume approval of a photo-textured approach.
- `build_assets.py` sculpts independent 3D skull, hair shell/strands, neck, blazer, open-collar shirt, sleeves, hands, chair cables and surfaces. These are early geometry sketches, **not** a production-quality rig/wardrobe. The hands are **not finger-rigged** yet.
- `render_proof.py` CPU path-traces the actual meshes under physical 3D camera/light transforms (Mitsuba). Head and torso animate as independent rigid objects; **no per-frame image warps, flow fields, remapping, face morph noise, or pre-rendered hero plates**. It refuses filenames containing `MASTER`/`FINAL` and marks frames `3D MESH / RIG TEST - NOT FINAL`.
- `review_gate.py` fails closed unless both model integrity and explicit user visual approval **for the specific mesh hash** are present. It cannot create that approval.

## QA result and blocker

Several front and three-quarter renders were inspected. Face geometry is genuinely three-dimensional and stable, but the **hair silhouette, skin fidelity, neck, tailoring, hands and overall cinematic realism fail** the requested standard. A prior 21/21 gate accepted the rejected v2, so numerical/edit checks must *not* certify v3. There is **no delivered v3 MP4**, no approved 3D character, no crown/title finale from this pipeline, and no replacement link. Never upload this proof as a final master.

To reach an exact photoreal likeness rather than a guess from a design sheet, the preferred next input is a textured, rigged head/body scan (`.glb`/`.fbx`/`.obj` plus textures) **or** evenly lit, unfiltered face + full-body 360° capture covering front, both 45° views, both profiles and back, neutral expression and the locked charcoal-blazer/black-shirt wardrobe. Existing v5/v2 sheets and the side-face/Snapchat videos are design references, **not** a professional 3D scan. The user has not selected a scan/texture option; do not pretend one was supplied.

## Historical reference beats (not yet rendered in 3D)

| Time in supplied 720×1280, 30 fps, 632-frame reference | Beat |
|---|---|
| ~0–4.8 s | Dark cyber hall, scarlet portal, cables, extreme wide-to-near-silhouette, black flashes |
| ~5–9.5 s | Seated wired figure, red pulsing portal, selective body reveal |
| ~9.5–11.5 s | Three-quarter/profile insert and neural visor, tightly controlled closeup |
| ~11.5–14.5 s | Cyan awakening → amber/orange burn, dramatic silhouette |
| ~14.5–17.4 s | Emblem title beat; v3 must put 👑 **directly above MONARCH STUDIO**, never on top of the face |
| ~17.5–21.1 s | Source's social/Instagram coda; do not silently substitute or add a new call-to-action |

## Reproduction for engineering review only

Run in an isolated Python 3.11 virtualenv, outside Git history; example versions tested: `numpy==1.26.4`, `mediapipe==0.10.21`, `opencv-python-headless==4.11.0.86`, `Pillow==11.3.0`, `mitsuba==3.9.1`, `imageio-ffmpeg==0.6.0`. The MediaPipe wheel may pull a GUI `opencv-contrib-python` whose `libGL.so.1` is unavailable on a headless host: uninstall the GUI wheel and reinstall headless OpenCV if importing `cv2` fails. `bpy` was tested but requires absent X/GL libraries here; no Blender asset/scene is claimed.

```bash
# Keep locked face sheet and reference videos private; obtain from their Drive authority.
python styles/monarch-face-chaos/true3d/fit_face.py \
  --sheet .runtime/references/CUSTOM_HERO_REAL_SHEET_v5.png --output .runtime/model
python styles/monarch-face-chaos/true3d/build_assets.py --output .runtime/model
python styles/monarch-face-chaos/true3d/render_proof.py \
  --model .runtime/model --output .runtime/analysis/true3d_proof.png --still 0.5
python styles/monarch-face-chaos/true3d/review_gate.py --model-dir .runtime/model
# The last command MUST exit nonzero until real visual review is received.
```

`.runtime/`, `.venv/`, face sheets, reference/turnaround videos, generated OBJ/UV albedo, and preview frames contain sensitive identity media: they are **ignored and not committed**. Their absence after workspace restore is expected. Stored Drive authority IDs: face v5 `1YTschdKJjpmsl4jIgC15y8yjek0zf1-M`; body v2 `177bFsA2oy--XSZOqbRycGieIbYJuX8S-`; Chaos 1 reference `1-S-wGrKYtRDL5iQf8iQBLJhKHRB71RlY` (MD5 `4eb7850feddcf400e1034ffa1d3834ce`). The 46 KB generic face topology is Apache-2.0, copied from google-ai-edge/mediapipe (Git blob `0e666d1c4e75949d1639c2bcf347a38da4834164`); its license is in `MEDIAPIPE_LICENSE.txt`. No raw reference frame is in Git.
