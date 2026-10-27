# CHAOS 04 — STRUCTURE v4 (measured, locked)

Source of truth for the build. Every number here was measured off the reference
before the freeze, not estimated. Frame numbers are 30 fps, 1-based.

## Format
| field | value |
|---|---|
| duration | 44.55 s container / **1332 frames** @ 30 fps (picture 44.40 s) |
| delivery | 1080 × 1920, H.264 high, crf 18–19, yuv420p, AAC 48 kHz, +faststart |
| aspect | 9:16 vertical, no letterbox, no watermark |
| reference spec | −13.9 LUFS integrated, true peak ≈ +0.1 dBFS, 17 soft cuts, 40 flashes |

## Acts
| act | time | frames | content |
|---|---|---|---|
| I | 0.00 – 13.27 | 1 – 398 | the room, empty, light and texture only |
| II | 13.27 – 39.50 | 399 – 1186 | Monarch, the doubles, the corridor, the montage |
| III | 39.50 – 44.55 | 1186 – 1332 | flash out, black, emblem, our endcard |

## Measured grid (drives cuts, strobes and the score)
Cuts (s): `16.25 17.25 18.00 18.62 19.38 20.50 | 24.38 25.50 26.25 27.62 28.88 | 32.88 34.12 34.88 35.75 36.50 | 39.50`

Flashes (s): 40 hits, ~0.50 s apart ⇒ **120 BPM half-beats**.

Silence: `40.34 – 40.93` and `42.10 – 44.55`.

## The 24 shots
| # | frames | name | set |
|---|---|---|---|
| 01 | 1–56 | Room, push in | room |
| 02 | 57–111 | Practical / floor | room |
| 03 | 112–167 | Doorway glow | room |
| 04 | 168–222 | Rack / steel macro | room |
| 05 | 223–279 | First silhouette | room |
| 06 | 280–336 | Hand to lapel | room |
| 07 | 337–398 | Back of the head | room |
| 08 | 399–488 | Halo hero | room |
| 09 | 489–518 | Eyes open | room |
| 10 | 519–540 | Six arms | room |
| 11 | 541–559 | Brood face | room |
| 12 | 560–581 | Doorway, floor pool | room |
| 13 | 582–615 | Neon doorway pull | room |
| 14 | 616–731 | Corridor walk | corridor |
| 15 | 732–765 | Spark whip | corridor |
| 16 | 766–788 | Halo blur | corridor |
| 17 | 789–829 | In frame | room |
| 18 | 830–866 | Tendril macro | room |
| 19 | 867–986 | Framed wide | room |
| 20a | 987–1024 | Amber close | room |
| 20b | 1025–1046 | Hand to lens | room |
| 20c | 1047–1073 | White void | void |
| 20d | 1074–1095 | Wide, small figure | room |
| 20e | 1096–1185 | Strobe close | room |
| 21 | 1186–1210 | Flash out | void |
| 22 | 1211–1228 | Silence, black | black |
| 23 | 1229–1263 | Emblem on | endcard |
| 24 | 1264–1332 | Our endcard | endcard |

## Copy / never-copy
**Copy the grammar:** 24-shot act structure, 120 BPM half-beat strobes, whip
pans, silhouette-first framing, slow push-ins, black silence before the
endcard, the 17-cut grid.

**Never use:** their footage, masks, brush logo, watermark (`@VKTMDubz`),
Instagram outro, their music, their LUT, any of their pixels.

**Ours instead:** Monarch (locked v5 face / v2 body) as real 3D, our charcoal
teal/amber chamber, our corridor, our white void, our emblem + wordmark, our
synthesised 120 BPM score (`chaos04/score.py`).

## Approval gates
1. **selftest** — scene builds, 8 frames render, no errors, timings logged.
2. **preview** — 360 × 640, every 2nd frame, 8 samples, full 1332 frames of
   timing, encoded with the real audio. This is the gate the user signs off.
3. **production** — 1080 × 1920, resumable batches, then encode + verify.
