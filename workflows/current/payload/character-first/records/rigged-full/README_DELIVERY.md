# MONARCH — full main-reference 2.5D recreation V1

## Watch the FULL video

https://drive.google.com/file/d/14v1Zi_aGVrCJF1PK5_3t5dmBGjqCYmZP/view

This is the full **1,332-frame / 44.4-second picture edit**, not the earlier
6-second example, 21-second chair film, rejected live-action composite, or a
3.6-second outro alone. The original audio tail is retained, so the container
is slightly longer than the picture track, just like the supplied reference.

- 720 × 1280, 30 fps, H.264 MP4 + original AAC 44.1 kHz stereo.
- New complete owner-character imagery, reference-matched costume variant,
  original industrial room/prop imagery, bounded skeletal image rigging,
  rigid face core and prop layers, arm-echo effects, camera/light treatment,
  controlled smirk shot and crown above MONARCH STUDIO ending.
- The correct main reference is `1sYYhXs9fbHeHcQGOmH5IR7CvUSVr9Tmx`.
- Original encoded AAC payload AND decoded PCM hashes match unchanged.
  No replacement score, added outro sting, resampling or normalization.
- No reference actor video was composited. The chair/cables example informed
  the technique, not the scenes, wardrobe, timing or music of this movie.

## Honest method / review status

The user approved proceeding with the explicitly offered **limited 2.5D** route.
The picture uses photographic skeletal skinning, not reconstructed 3D geometry
or natural AI-generated human acting. Motion is bounded; camera/poses/coverage
approximate the reference's major phases rather than duplicating its complete
3D human/weapon choreography. The on-video opening label discloses the method.

The complete V1 is ready for user review. Likeness/motion quality has NOT been
marked user-approved or “100% exact.” Encoded samples and ungraded rig views were
inspected; technical checks do not substitute for artistic approval. Contains
rapid cuts and light accents.

## Reproduction

The source ZIP contains the six new generated scene assets, renderer, audio
conform tool, original reference audio copy, brand video component, reference
metrics and reports. It does not include the source actor's reference video,
private raw identity recordings, other-chat scene images or credentials.
The full delivered MP4 is linked above and delivered separately, not duplicated
inside the source ZIP.

Python 3.11; install `requirements.txt`. DejaVu system fonts are required.
From the extracted source package:

```bash
python src/rigged_main_film.py \
  --root . --work render-cache \
  --metrics records/REFERENCE_FRAME_METRICS.csv \
  --outro components/MONARCH_CROWN_OUTRO_3p6s.mp4 \
  --output output/PICTURE_ONLY_2_5D.mp4

python src/conform_reference_audio.py \
  --picture output/PICTURE_ONLY_2_5D.mp4 \
  --audio-source components/MAIN_REFERENCE_ORIGINAL_AUDIO.m4a \
  --audit records/MAIN_REFERENCE_AUDIT.json \
  --output output/MONARCH_REFERENCE_2_5D_FULL_V1.mp4
```

Completed matching shot chunks are reused. A changed renderer/asset/settings
fingerprint must use a fresh work directory rather than mixing stale frames.
Do not run this again merely because local media vanished: restore the exact
completed movie by its verified Drive ID/hash in `DELIVERY.json` first.

## Provenance

Owner identity: the already-saved reference-based master from the user's
personal face videos. Scene imagery: newly generated for this main-reference
recreation. Rig mathematics: adapted conceptually from the user-supplied
whole-character workflow; outlines, joint locations, standing/prop layers,
coverage, matte corrections and picture rendering are specific to these new
assets. Typography: DejaVu system fonts, binaries not redistributed.
Music: unchanged user-supplied main-reference soundtrack; no independent
licensing clearance for later public/commercial use is asserted.
