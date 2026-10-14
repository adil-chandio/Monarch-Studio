# 08 · Cleaning flattened references without damaging subjects

## Why localization is more than a new audio track

V4 retained old English typography, social tags and the Instagram end card, while the Urdu overlay was too small. Replacing audio alone did not meet the request. The repair localized the picture: it cleaned old glyphs/tags, rebuilt integrated type and excluded the social ending.

## The rejected approaches

Large Telea inpainting areas produced cloudy paper patches. A background-key/matte experiment removed pale hair, bulb highlights and thin details because their colors resembled the stage. Both were rejected rather than quietly called improvements. The rejected `matte.py` remains in the historical V5 source as evidence, not as the approved engine.

## The retained case method

Use shot-aware text regions, identify the intended ink, dilate enough to cover antialiasing, and apply Navier–Stokes inpainting. Review background texture after cleanup. This is restoration of flattened source pixels, not magical recovery of what was hidden by lettering; some texture softening remains a real limitation.

Detect the active Instagram icon position by template matching before masking its associated handle. The reference alternated between upper-right and lower-left. Erasing both locations in every shot damaged the hanging stone in the talent scene, where no lower-left tag was present. Observed true matches were approximately 0.85–0.997, versus about 0.10–0.21 for empty regions; the implementation used a case-specific threshold.

## Moving typography requires moving masks

The year, running-shoe heading and other text moved during entry. Settled-frame rectangles left partial letters. The watch/flow transition also arrived earlier than a sparse sample suggested. Inspect dense source frames and encode reviews around those boundaries.

The runner is the clearest caution: an early broad lower mask cut low-positioned shoes; a later ramp preserved shoes but missed the first rows of SPRINT. V6's targeted fix kept early shoes and cleaned the full lower title after the source runner rose, at approximately 25.70s. This is a **case coordinate/time**, not a universal rule for every runner.

Dark-purple sandbags could be mistaken for ink. Connected-component size/location protected the subject. Pale crutches, reflective metal, strings and hair need different caution. Do not convert a color heuristic into a claim that the machine understands an object.

## Transfer to a new project

The historical cleaner is fully preserved, but its coordinates are tied to this source. A new reference needs its own inspection and masks. Stage prepared, clean motion clips for the reusable compositor. Never run the Einstein masks on a new topic's frames merely because both videos are vertical and lavender.

Maintain source credit/rights in metadata and the archive when visible tags are removed at the user's request. Never imply ownership of the original supplied animation.
