# Monarch — character-first design pack

## Current result

**The full-length 44.4-second limited 2.5D recreation is delivered; the current review version is V2 targeted polish.** It contains 1,332 picture frames with the exact original main-reference soundtrack. This is the user-approved image-based rigging route—not natural AI performance, reconstructed 3D, or exact source choreography. User likeness/motion approval is still pending.

Latest full-film receipt: `records/rigged-full/polish-v2/DELIVERY.json`.
V1 remains preserved at `records/rigged-full/DELIVERY.json`. V2 patches only five
shots (159 frames): a blade-background smear and over-bright portrait pulses.
The other 1,173 decoded RGB frames are identical to V1; music, cuts, camera/rig
trajectories and character art are locked. See `FRAME_INTEGRITY.json` in the V2
record folder for the full comparison result.

The V2 recovery/source package also retains every completed picture chunk and
was successfully reassembled without new rendering, reproducing the delivered
movie's SHA-256. Use the verified video/ZIP receipts if local media disappears.
The six source character/scene assets are still in `rigged-full/KEYFRAMES.json`.
Do not resend only the outro or rerender finished work merely on Continue.

- Four new matching character references: front master, right-facing profile,
  rear, and detailed face portrait.
- Four original cinematic shot-design stills: Threshold, Focus, Break, Resolve.
- Original crown-above-MONARCH-STUDIO end-frame graphic, 1080 × 1920.
- Three-page design bible, lossless PNG boards, native images and a design ZIP.

The character/shot stills are generated visual-development references, not a
face scan, rigged mesh, mocap performance, temporally verified human video, or
proof of exact biometric likeness. The separate outro is vector motion graphics;
its own original sting is NOT used in the main-reference-matched full movie.
The user subsequently approved proceeding with the explicitly limited full
2.5D recreation by replying Continue to that offer. This method approval is not
recorded as approval of the resulting likeness, motion quality or exactness.

## Canonical main reference and music — latest clarification

The MAIN reference is only
`1sYYhXs9fbHeHcQGOmH5IR7CvUSVr9Tmx` / `VID_20261013_050529_146.mp4`:
1,332 native frames at 30 fps, 720 × 1280, 44.4 seconds of picture. The separately
pasted red/blue chair-and-cables conversation is a workflow/technique example,
NOT a visual base, 21-second duration target, soundtrack or version selection
for this film. See `records/main-reference/REFERENCE_LOCK.md`.

The user now explicitly wants the reference's **same original music**. Its AAC
stream has been copied without re-encoding and verified twice: encoded packet
payload and decoded PCM hashes match. The source audio has a slightly longer
tail than the picture; preserve it. The separate crown outro supplies video only
under that continuous reference track—do not mix its own sting into this final.
This supersedes earlier proposals for an original score on the full film.

`src/conform_reference_audio.py` will accept only a complete, correctly timed
picture input, not an outro-only or the other chat's 632-frame edit. It rejects
the identical reference file and identical known rejected composite. It copies
the original soundtrack unchanged and verifies picture/audio payloads after
muxing. It does not generate human motion or certify visual accuracy. It has now been
run on the actually complete new 2.5D picture edit—not a placeholder—and its
encoded audio, decoded PCM and picture-bitstream checks passed.

Frame-by-frame metrics and transition *candidates* are saved under
`records/main-reference/`; candidates are not automatically confirmed cuts.
The earlier eight-beat proposal is archived in the current plan. The rendered
37-part coverage plan follows the reference's major phases/light-pulse timing;
it is not claimed as an exact source pose/camera/cut-for-cut reproduction.

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

If the local media directory is absent, download the `design_zip` ID from
`records/ASSETS.json` using the Drive connector. Restore the exact saved outputs
without installing image/render dependencies:

```bash
BASE=workflows/current/payload/character-first
python3 "$BASE/src/recover_design_assets.py" \
  --archive google_drive/MONARCH_CHARACTER_FIRST_DESIGN_PACK.zip \
  --ledger "$BASE/records/ASSETS.json" \
  --root /home/user/monarch-character-assets
```

The recovery command verifies the archive and every restored file, reuses
matching files, rejects path traversal, and refuses to overwrite a differing
existing image. It does not regenerate art, ask the user for the master again,
or claim to repair the Arena connection/pending-question banners.

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

`records/ANIMATION_PLAN.json` now contains the rendered 44.4-second V1 plan.
There are 1,332 complete picture frames, including 844 frames with the rigged
owner-character visible. Natural/reconstructed-3D character frames remain zero:
the method is bounded image-based skeletal skinning plus rigid prop layers.
`rigged-full/PICTURE_REPORT.json` and `AUDIO_CONFORM_REPORT.json` preserve the
actual render and mux receipts; `DELIVERY.json` identifies the uploaded movie.

`records/BRAND_OUTRO.json` holds the completed component's source/settings
fingerprints, full-decode checks and audio measurements. `VIDEO_COMPONENTS.json`
holds its verified Drive recovery ID. The outro is not inside the earlier
immutable still-design ZIP; recover it separately rather than re-rendering.

Renderer invocation (a matching completed output is reused, not duplicated):

```bash
BASE=workflows/current/payload/character-first
python3 "$BASE/src/render_brand_outro.py" \
  --work .cache/monarch-brand-outro/render \
  --output /home/user/monarch-video-components/MONARCH_CROWN_OUTRO_3p6s.mp4 \
  --report "$BASE/records/BRAND_OUTRO.json"
```

Use fresh work/output/report paths for a deliberately revised version.
The renderer refuses stale frame caches/unverified overwrites, skips completed
matching frames, and verifies 108 native 1080 × 1920 frames at 30 fps, 3.6-second
duration, 48 kHz stereo audio and an encoded true-peak ceiling. The graphic is a
crown/type reveal, restrained sheen/settle and fade; no human pixels are used.
Its sound is an original synthesized sting, not copied reference music or voice.

The full V1 uses `src/rigged_main_film.py`: connected 2D bones, analytic limb IK,
rigid facial cores/props, anchored boots, authored camera/effects and native
per-shot exports. Image-space skeletal skinning IS used and is disclosed.
No eye/mouth morph, arbitrary wave-body field, source-actor video, chair/cables
scene, or replacement score is used. A matte review corrected fingertip notches,
a prop/skin boundary fold, and a reflective-blade extraction error before final
rendering. Rendered sample frames were inspected after encoding.

If exact/natural 3D human/weapon choreography is requested later, that still
requires a different capable render pipeline; this V1 must not be relabelled as
one. The bounded motion and authored cuts are an approximation under the method
the user approved. Technical checks do not equal visual/likeness approval.

## Service-banner limitation

The supplied screenshot shows both a connection-interrupted banner and a
pending-question notice. The earlier clarification tool was recorded skipped,
while the UI still displayed a pending notice. Use the notice's Refresh control
and dismiss/answer the old question if it reappears. No new interactive choice
popup was opened during this design continuation. These are observations, not
a backend diagnosis or a claim that repository changes repair Arena's service.
