# MONARCH — FULL V3 motion / framing refinement

## Full video

https://drive.google.com/file/d/1jCE5Xtdkenf9Cg_OfsEHh35mAeqxlpZ5/view

Preserved V2:
https://drive.google.com/file/d/1Bl8zQE7Lmbv_i-IfjF7xcPu7olo-aT7y/view

1,332 frames / 44.4 seconds of picture, 720×1280, 30 fps. Original reference AAC
payload and decoded PCM remain unchanged, including the slightly longer audio
tail. Same user-approved limited photographic **2.5D** method—not natural AI
performance, reconstructed 3D, or exact reference choreography.

## What advanced in V3

Only shots **3, 5, 6, 7** change: **132 frames** in total.

- Neutral reveal: 60px camera-framing correction retains the full hair/head
  silhouette. Scale, face art, expression and cut timing remain unchanged.
- Arm section: a controlled outward/upward palm lift replaces some of the
  static-feeling hand hold. Glove regions follow the forearms rigidly; no
  finger stretching or added face morph.
- Arm echoes: staggered build/fade replaces constant pulsing, giving the
  reveal a clearer progression rather than simply adding flashes.
- The already-created clean room plate is reused only around arm disocclusions;
  no new character image or scene redesign was generated.

**All other 1,200 decoded RGB frames are identical to V2**, including every one
of the 159 V2 repair frames. The V2 prop-background and portrait-light fixes are
therefore retained unchanged. V2's original MP4 is preserved.

## Checks and limits

All 98 gesture frames were checked for rig constraints. Bone scales remain
unit, hands remain connected, inverse Jacobians stay positive, and the face /
foot bone matrices are unchanged from the base. Conservative headroom stays
above 23px through the corrected reveal. Encoded changed frames were inspected.

These are scope/geometry/file checks—not user approval of likeness or proof of
natural human performance. Source expressions remain image-based and motion
remains bounded under the approved method. Contains rapid cuts/light accents.

## Source / exact recovery

The package includes all 37 finished picture chunks, canonical source audio,
source/reports and the reused background plate. No raw identity recordings or
source-actor reference video is included. The main MP4 is delivered separately.

After extracting, reassemble without new rendering:

```bash
pip install imageio-ffmpeg==0.6.0
python src/reassemble_rendered_edit.py --root . --output RECOVERED_FULL_V3.mp4
```

Direct download of the verified completed movie is the preferred recovery path.
For image-level revisions, the unchanged six original scene assets are in the
V1 source pack; V2 repairs/source are preserved separately. Do not regenerate
the character or restart the whole film merely because local media vanished.

Music is the user-supplied reference soundtrack; independent licensing for
later public/commercial use is not asserted.
