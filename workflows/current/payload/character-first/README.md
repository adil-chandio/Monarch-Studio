# Monarch — character-first design pack

## Current result

**Character-sheet and original shot-design stages are complete. Animation is not.**

- Four new matching character references: front master, right-facing profile,
  rear, and detailed face portrait.
- Four original cinematic shot-design stills: Threshold, Focus, Break, Resolve.
- Original crown-above-MONARCH-STUDIO end-frame graphic, 1080 × 1920.
- Three-page design bible, lossless PNG boards, native images and a design ZIP.

These are generated visual-development references. They are not a face scan,
rigged mesh, mocap performance, temporally verified video, or proof of exact
biometric likeness. The user delegated design judgement; that is not recorded
as explicit approval of likeness or a completed final film.

## User correction — binding direction

The user's personal video is **face reference only**. Do not composite that
recording into the movie. The earlier live-action draft and procedural mannequin
are rejected routes, not fallback deliverables. Do not resume `composite_live.py`
or call old photographic plates plus body warps a new animation.

The previous selected Option 1 was missing from a later workspace. The user
subsequently said “Tum dekh ke Aage BAHDO na.” The current master was newly made
from the restored original-video face crops under that delegated judgement;
it is **not** claimed to be the recovered Option 1. All final views now have
independent verified Drive recovery IDs, so a missing local file should be
restored, not regenerated.

## Durable recovery

`records/ASSETS.json` gives each finished asset's Drive ID, URL, size and hashes.
The folder is recorded there and in `records/BRIEF.json`. Restore a missing file
with the Drive connector, then verify its checksum before using it as a master.
Do not put raw identity video, face crops, generated personal images, tokens or
large media binaries into Git. Local media lives outside this Git checkout at
`/home/user/monarch-character-assets/`; Drive is the verified recovery copy.
Do not assume any local cache or excluded folder survives a later workspace.

## Rebuild the documents, not the character

Python 3.11; dependencies in `requirements.txt`. DejaVu fonts are expected under
`/usr/share/fonts/truetype/dejavu`. Font binaries are not vendored in this pack.

```bash
BASE=workflows/current/payload/character-first
python3 "$BASE/src/brand_end.py" \
  --output /home/user/monarch-character-assets/brand/MONARCH_CROWN_END.png
python3 "$BASE/src/assemble_design.py" \
  --root /home/user/monarch-character-assets \
  --output /home/user/monarch-character-assets/delivery
```

The document assembler only uniformly scales/places existing finished stills.
It neither reshapes the face/body nor creates motion. Native source images
retain their own dimensions; a 4000 × 2400 layout is not a claim that every
source image is native 4K. The review PDF uses high-quality JPEG page images;
lossless board PNGs and source-view PNGs are available separately.

## Motion/edit handoff

`records/ANIMATION_PLAN.json` contains the **proposed**, unrendered 44.4-second
edit and motion requirements. `rendered_frames` is deliberately zero.

A capable temporal video-generation or detailed rig/animation pipeline is still
required to produce new natural full-body acting. No such direct photoreal
image-to-video tool is available in this session. Do not represent pans, zooms,
independent-image morphs or a contact-sheet slideshow as satisfying that stage.
Validate the actor in native generated frames: face/hair/wardrobe continuity,
actual joints, plausible cloth, no sliding planted feet, stable hands, and no
frozen/duplicated source-frame padding. Technical checks do not equal visual
approval.

## Service-banner limitation

The supplied screenshot shows both a connection-interrupted banner and a
pending-question notice. The earlier clarification tool was recorded skipped,
while the UI still displayed a pending notice. Use the notice's Refresh control
and dismiss/answer the old question if it reappears. No new interactive choice
popup was opened during this design continuation. These are observations, not
a backend diagnosis or a claim that repository changes repair Arena's service.
