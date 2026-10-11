# WF-03 — TUMHARI RESERVED SEAT — MONARCH NOIR IMAX TABAHI V2

This is the separately versioned V2 production package for task `EMS-20261011-003`. The accepted V1 package remains untouched in the sibling `tumhari-reserved-seat/` directory.

## Locked creative master
- 74.00 seconds, 34 beats, 1920×1080, 24 fps.
- Exact byte-identical selected `voice-00`; no time stretch.
- Timeline SHA-256: `75838e71c598c04bb322fabbe080d71641853aa9fc2cf2dc6341a73e42698c0b`.
- Voice SHA-256: `c411bfae2b12b194cf2107c556b2604e82f3e763c9e6fea94a6186ac650ca972`.

## V2 identity
- rain-soaked midnight railway platform / humanised Monarch / wet practical noir.
- measured platform dolly, lens-breath push/pull, foreground-column occlusion and precision shutter echoes.
- 72 BPM physical rail rhythm; D-minor pressure to post-decision amber Picardy lift; 3-depth rain ASMR.
- Five authored set pieces; three simultaneous motion scales; 12 transition families.
- Procedural source only: no stock picture, music, samples or loops.

## Reproduce
```bash
python3 src/render.py --sheet --sheet-output artifacts/LOOK_SHEET_WF03_V2.jpg
python3 src/render.py --output build/tumhari-seat-wf03-v2-mute.mp4
python3 src/audio.py --output build/tumhari-seat-wf03-v2-mix.wav --mux-video build/tumhari-seat-wf03-v2-mute.mp4 --final build/TUMHARI_RESERVED_SEAT_WF03_V2_NOIR_IMAX_TABAHI.mp4
python3 src/gate.py build/TUMHARI_RESERVED_SEAT_WF03_V2_NOIR_IMAX_TABAHI.mp4
```

## Evidence map
- `ENHANCEMENT_BIBLE.md` — creative/motion/audio doctrine and anti-noise rules.
- `DNA.json` — machine-readable V2 identity, locks and targets.
- `artifacts/VISUAL_ENHANCEMENT_LEDGER.csv` — 34-beat primary/depth/micro map.
- `artifacts/THREEX_DELTA.json` — measured V1→V2 delta ledger.
- `artifacts/BRAIN_GATE.txt` — 30/30 freshness review.
- `records/parent-v1/` — immutable V1 acceptance evidence copied for comparison.
- `records/EXPERIMENTS_FAILURES_FIXES.md` — decisions, failures and repairs.

Final master, delivery receipt and Drive URLs are intentionally absent until all final measured gates pass.
