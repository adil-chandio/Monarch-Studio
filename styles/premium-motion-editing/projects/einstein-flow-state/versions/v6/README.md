# Flow State V6 — enhanced motion pass

## Scope authorized by the user

The user selected **“Video ko aur enhance karo”** after V5 was already
completed and delivered. V6 is a new revision of that edit, not a rerun
triggered by an ambiguous “continue.” The delivered V5 remains untouched:
https://drive.google.com/file/d/1UMSvHItighGlOuSsO_EaDkrfb_eKuBZC/view

## What changes in V6

| Element | V5 | V6 |
|---|---|---|
| Scene movement | Small single-plane camera transform | Independent near/far inverse-map 2.5D movement, gentle dolly/yaw and focus separation |
| Title entrance | Scale/rise | Perspective-yaw entrance, stronger extrusion and wider/larger type |
| Title relief | 8 extrusion steps | 13 extrusion steps; secondary-line violet accent |
| Transitions | One short directional blend | Three short treatments: depth push, diagonal whip, feathered directional cut |
| Subtitles | Plain dark 30px-base phrase text | 36px-base high-contrast rounded captions with active-word highlighting |
| Sound accents | Quiet pad and general cut/type taps | Stronger restrained cut accents, clock/chalk/running cues and a closing rise |
| Cleanup | Reviewed V5 cleanup | Also repairs a brief runner-title residue found during V6 frame review, without cutting the shoes |

The native reference animation still moves throughout all fourteen shots.
There are **no new still-image slides** and no new narration generation.

## What stays unchanged

- The same nine previously selected narrator files, verified by SHA-256.
- The same spoken script, natural **1.0×** voice pace and 63.1-second timeline.
- The same lavender editorial world and source-animation topic.
- No added Monarch branding, no visible Instagram handle/end card in reviewed
  output frames.
- Reference provenance and the V5 delivery remain recorded.

The caption phrases retain their narration timing. Active-word highlighting
uses proportional pacing **within** each phrase; it is not advertised as
ASR-certified word alignment.

## Honest production boundaries

V6 uses **2.5D image-space compositing** of actual moving supplied footage. It
does not claim to reconstruct photographed people, vehicles or props as new
3D geometry. The 1080 × 1920 export upscales the native 720 × 1282 reference;
new type is rendered at 1080 resolution. Cleanup of flattened text/tag areas
can soften the original paper texture.

The source attribution is **@RIT2RAJ_DAS** (retained here/off-frame at the
user's request to remove visible social tags). Original supplied reference
Drive ID: `1qOhYxKD6H_pJn8dkr7EMO2Ro4QyJeVW2`, MD5
`34f35d446136c574243cb918c7b96f5f`. The historical anecdote and creativity
rhetoric are translated as the reference's story, not independently
verified history/science. “Ek mashhoor kahani” remains in the opening.

## Reproduce / resume

Keep this directory together. `media/reference.mp4` and the exact `audio/`
clips are the input authorities. Fonts and their OFL licenses are included.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 .venv/bin/python run_pipeline.py
```

The resumable stages are cleanup → audio/timing → render → technical QA.
`PIPELINE_STATE.json` records the current stage. An already-verified source
clip is reused; no image/voice generation or new voice approval is needed.
`motion_v6.py` implements near/far camera mapping and transitions.

The pending master is `delivery/Flow_State_UrduEnglish_V6.mp4`. Only essential
pending-upload source clips and the master are protected in the bounded
spool; disposable reviews/audio caches are ignored. Video bitrate is bounded
so the protected files stay within the workspace patch budget. Once cloud
IDs and checksums are verified, large media return to ignored/external
storage. See the eventual `DELIVERY.json` for actual verified links.

## Delivery gates

`verify.py` fully decodes final video/audio and checks frame count, H.264
High/yuv420p, AAC stereo 48 kHz, faststart, peak level, non-static source clips,
original voice hashes, sampled social-icon candidates, and that the V6 master
is not a renamed V5 file. Review sheets sample the **encoded MP4**. These are
technical and sampled visual checks, not a claimed independent human
listening test or a promise of aesthetic perfection.

No stage may mark the task complete merely because encoding finished.
Presentation, encoded-frame review, verified Drive master and verified source
recovery are separate requirements. Connector uploads require the active
agent; platform interruptions are handled through resumption, not falsely
promised impossible.


## Verified delivery

Master: https://drive.google.com/file/d/1yJ2m5A0SJK3vhX8jRA8Fqvw7nAASC6lF/view

Recovery: https://drive.google.com/file/d/1BRFaecqh9-Xa9aEdwM60Glrh-qMRcWzd/view

Both independently verified by remote file size/MD5. V5 remains unchanged.
