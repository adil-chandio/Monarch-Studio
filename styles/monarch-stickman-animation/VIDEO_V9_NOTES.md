# v9 — FINAL POLISH

`stickman_money_37s_v9.mp4` · 1080×1920 · 30 fps · **37.00 s** · 11.29 MB
sha256[:16] `30a5f761d3f14ad6` · −11.7 LUFS · TP −0.4 dBFS · decode-clean

## Measured across all three builds

| metric | v7 | v8 | **v9** |
|---|---|---|---|
| reveal jerk p95, worst scene | 4.13 | 2.62 | **1.62** |
| p10 frame-diff S2 | 0.06 | 0.07 | **0.24** |
| p10 frame-diff S5 | 0.06 | 0.06 | **0.22** |
| p10 frame-diff S4 | 0.15 | 0.26 | **0.47** |
| global minimum frame-diff | 0.01 (frozen) | — | **0.082** |
| >8 luma jumps | 49 | 0 | **0** |
| darkest frame | 104.1 | 199.8 | **199.8** |
| L/R correlation | 0.9941 | 0.8544 | **0.7547** |
| side/mid energy | 0.054 | 0.280 | **0.374** |
| 120–500 Hz share | 66.75 % | 58.24 % | **57.67 %** |
| 4–8 kHz | 8.34 % | 11.10 % | **10.69 %** |
| short-term minimum | −32.4 | −29.7 | **−27.3 LUFS** |
| loudness range | 20.9 | 17.6 | **15.2 LU** |

Note on "dead zones": the v9 detector flags six runs under its 0.40 threshold,
but their minima are 0.082–0.282 against v7's 0.01. Nothing is frozen — those
are simply calm passages that are still moving every frame. The threshold is
now too strict to be meaningful.

## What v9 added

**Props breathe.** `fl(t, i, a, w)` — a two-term phase-offset micro-float
applied to the S2 checklist rows, the S3 calendar block, the S4 sample cards
and the S6 tick row. v8 froze every prop the instant it finished revealing;
a living frame never contains a perfectly still object. This is what moved the
p10 frame-diff from 0.06 to 0.22–0.47.

**Kinetic emphasis.** The highlighted word in every headline now lands 8.5 %
oversized and settles to 100 % across its reveal, extrusion and all. The eye
is pulled to the keyword instead of scanning the whole line.

**CTA specular sheen.** A soft white band sweeps diagonally across the
"FOLLOW FOR PART 2" pill on a 1.6 s cycle — 11 feathered strokes at ≤18 %
alpha. The single most important element in the film now reads as a lit object.

**Face subsurface warmth.** Seven stacked warm ellipses at 6 % alpha across the
lower skull. A head lit by one specular highlight on flat white reads as
plastic; real skin bleeds warm where the light wraps.

**Audio.** Twelve pad swells (was nine), gain 0.052 → 0.088, placed on the
re-measured hole list including t=0.15 and t=34.9. Sidechain relaxed again
6:1 → **5:1**, release 280 → 260, threshold 0.024. Bed 0.54 → **0.60**.
Result: loudness range down to 15.2 LU and the floor up 5.1 dB from v7.

## Lineage
v7 `e7d8966ad6c0083c` → v8 `ff1fb7e612b48b61` → **v9 `30a5f761d3f14ad6`**
Restore points: `src/clean_v7_backup.py`, `src/make_asmr_v7_backup.py`,
`src/toon_flat_backup.py`. Audit: `FORENSIC_AUDIT_V7.md`.
