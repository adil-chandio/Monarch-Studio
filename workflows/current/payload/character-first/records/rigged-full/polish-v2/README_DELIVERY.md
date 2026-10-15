# MONARCH — FULL V2 targeted polish

## Watch the full video

https://drive.google.com/file/d/1Bl8zQE7Lmbv_i-IfjF7xcPu7olo-aT7y/view

V1 is preserved:
https://drive.google.com/file/d/14v1Zi_aGVrCJF1PK5_3t5dmBGjqCYmZP/view

This is still the user-approved **limited photographic 2.5D recreation**, not
natural AI performance, reconstructed 3D, or exact reference choreography.

## What changed

Only shots **20, 25, 30, 32 and 34** were patched (159 frames total):

- Blade shot: a matching empty background repairs the old reflective-prop
  inpainting footprint. The obvious diagonal smear on the door is removed.
  Visible surrounding background differs by only ~2.36/255 before compositing;
  no geometric camera warp was applied to the clean plate.
- Four close-up shots: a soft face-tracked exposure mask limits bright-pulse
  washout, preserving skin detail. No face reshaping, new expression, changed
  character image, changed rig trajectory or camera motion.

**All other 1,173 decoded RGB frames are identical to V1.** All 32 unaffected
encoded chunks were reused byte-for-byte. Total cut boundaries/order, 1,332-frame
picture duration (44.4s at 30fps), 720×1280 framing, and original AAC/decoded PCM
are unchanged. The reference's slightly longer audio tail remains intact.

Encoded patched frames were inspected. These tests establish scope/integrity,
not user approval of likeness or naturalism. V2 is ready for review.

## Recovery package

The V2 recovery/source ZIP contains:

- All 37 completed V2 **silent picture chunks**, with their saved hashes.
- The unchanged original reference audio copy and its audit.
- The new clean background plate and V2 patch/reassembly source.
- Frozen V1 renderer source and V1/V2 reports.

The complete MP4 is delivered separately at the link above. Raw personal/source
actor recordings are not included. To reassemble without generating any new
pictures, after extracting the package:

```bash
pip install imageio-ffmpeg==0.6.0
python src/reassemble_polished_v2.py --root . --output RECOVERED_FULL_V2.mp4
```

The direct verified movie download is the preferred recovery route. Container
metadata may differ after reassembly; the copied picture/audio payloads are
checked. Never overwrite the original V1 or reuse an unrelated soundtrack.

## Image-level editing

For image-level rerendering, the unchanged six scene assets and other dependencies
are in the V1 source pack:
https://drive.google.com/file/d/1wSU7SQM39RVfxMR66OxHhZVtO6ySeB7_/view

Use `polish_full_v2.py` with those assets, the frozen V1 report, canonical frame
metrics and original crown component. The 32 unchanged chunks in this recovery
pack are also valid byte-identical V1 base chunks; the five changed slots are
rendered by the patcher rather than taken as V1 source. Use a new work/output
path for intentional later revisions. Do not rerender merely because the user
says Continue.

Music remains the user-supplied main-reference soundtrack; no independent
licensing clearance for later public/commercial use is asserted.
