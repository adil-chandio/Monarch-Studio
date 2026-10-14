# Flow State — corrected Urdu-English motion edit (V5)

## What this is

A **reference-derived localization and motion re-edit**, not a newly modelled
3D film and not a sequence of newly generated still images. The supplied
reference's actual moving footage is retained in 14 separately timed shots.
It is recut to the already-selected narrator's original nine audio clips.
The reference's English overlays/social UI are cleaned; new Roman Urdu / easy
Urdu-English kinetic typography, depth extrusion, brief directional
transitions, camera movement and restrained sound accents are composited.

- Master target: **1080 × 1920, 30 fps, H.264 High, yuv420p, AAC stereo 48 kHz**.
- Natural-speed narration: **1.0×**, 63.1-second edit (quiet trimmed only).
- Native visual source: 720 × 1282; the 1080 master upscales that footage and
  renders the new typography at 1080. It does not invent native-1080 detail.
- Original closing Instagram card is excluded from the edit.
- No Monarch branding is added.
- 31 independently timed type states and 36 short Roman Urdu caption phrases.
- `Flow_State_Roman_Urdu.srt` is a separately editable subtitle export.

## Provenance and accuracy

Reference supplied by the user: Drive file
`1qOhYxKD6H_pJn8dkr7EMO2Ro4QyJeVW2`, MD5
`34f35d446136c574243cb918c7b96f5f`.
Its on-screen author handle is **@RIT2RAJ_DAS**. The user asked to remove visible
Instagram tags; provenance remains here and in the delivery description.
This edit is not claimed as ownership of the original animation.

The selected speech was recovered read-only from immutable repository commit
`5504074554dd8fb7fe2fbb5bdf60b95213cae7b4`, original path
`operations/history/EMS-20261014-001/payload/flow-v3/audio/line01.mp3` through
`line09.mp3`. No new voice registration/synthesis was performed for this
correction, and no complete operation was restarted merely because the
checkout was initially idle.

The Einstein/Mozart anecdote and the reference's claims about creativity are
translated as the supplied story, **not independently verified historical or
scientific facts**. The opening therefore says “Ek mashhoor kahani.”

Anton and Barlow Condensed fonts are OFL licensed. Their licenses accompany
this source package. Python dependencies are in `requirements.txt`.

## Why the previous versions were not silently reused as final

- V3 was an image-based slideshow rather than a matching motion edit.
- V4 retained the original English typography, Instagram handles and end card,
  with nearly microscopic Urdu subtitle text and globally sped-up narration.
- A first repair experiment using large Telea inpainting patches produced
  cloudy backgrounds; it was rejected.
- A color-keying experiment damaged pale objects; it was rejected.
- The retained method uses shot-aware Navier–Stokes glyph cleanup and actual
  icon-template detection. Only the **active** tag corner is masked. Painting
  both possible corners would damage the brain's hanging stone in one shot.

`matte.py` is an explicitly rejected experiment, not part of `run_pipeline.py`.

## One-command resumable execution

From the repository root, with the reference staged at
`workflows/current/payload/flow-repair/media/reference.mp4`:

```bash
python3 -m venv .venv
.venv/bin/pip install -r workflows/current/payload/flow-repair/requirements.txt
OPENBLAS_NUM_THREADS=1 .venv/bin/python -u \
  workflows/current/payload/flow-repair/run_pipeline.py
```

The stage chain is **cleanup → audio/timing → render → technical QA**.
`PIPELINE_STATE.json` records the exact current stage and resume command.
Completed cleanup clips have individual receipts and checksums, so a stopped
job can resume rather than re-create every asset. Use Arena's recorded process
ID before attempting a rerun. Do not start a second live render.

### Completion is fail-closed

Local encoding is **not** delivery. `DELIVERY_GATE.json` stays incomplete until:

1. the encoded output passes full video/audio decode, frame-count, codec,
   faststart, audio peak and moving-source checks;
2. the agent reviews frames sampled from the **encoded** MP4;
3. the actual MP4 is uploaded to Drive and its remote checksum/size match;
4. a recovery package is uploaded and its real ID is recorded.

Drive uploads require the interactive connector; no background program can
honestly claim those completed on its own. Unexpected platform/service
interruptions cannot be prevented by repository code, but exact resumption and
stage continuity no longer rely on another “continue” message.

## QA scope

`QA.json` reports measured checks, not aesthetic perfection. Full decode and
levels do not constitute an independent human listening test. Cleanup is a
restoration of a flattened source: pixels hidden by original lettering are
estimated rather than magically recovered. Review sheets sample 42 actual
encoded frames across all shots; automated icon searches supplement that
review. Source-motion measurements are made on moving clips before the new
text, not merely on animated captions over a still.

## Large artifacts

Video masters and the full source-media recovery ZIP belong on Drive, by real
ID and checksum. Local runtime media are ignored by Git. Source, fonts,
selected speech and state are small enough to retain with the task archive.
See `DELIVERY.json` for verified links once delivery is complete.


## Workspace reset correction

See `PERSISTENCE_FIX.md`. The default media directory is now `media/` beside the source scripts, and the pending master is `delivery/Flow_State_UrduEnglish_V5.mp4` beside them. These critical bytes are protected until their Drive copies verify. Do not trust a completed receipt when its media file is absent.
