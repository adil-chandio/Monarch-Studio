# KAANTA · Organic Motion v7

Native **1080×1920 · 30fps · 30.5s**. Delivered for user review, not assumed artistically approved.

[Watch V7](https://drive.google.com/file/d/1zRKxqy7yS_k1USCyTuGCBSOCOCNbPVjz/view) · [Delivery folder](https://drive.google.com/drive/folders/1YPpOkcm_hh843HI4V69cQL5rQrFL5tMI) · [Preserved V6](https://drive.google.com/file/d/1c-o5LKg11MAZOLNOLQHIXqwBn3ozUGEx/view)

This is a focused organic-motion/detail iteration of V6, not a newly rewritten film or another shot-design rebuild.

## Actual changes
- Three independent high-resolution hero membranes (48 × 32 sphere segments).
- Deterministic absolute-time travelling folds and leading lobes; no accumulated state or random per-frame jitter.
- Softer membrane opacity/roughness for readable layered cell interiors.
- Same voice WAVs, narration, safety qualifiers, captions, nine-shot edit, credited score and clean-frame constraints retained.

This is stylized educational animation, not a biological simulation or clinical advice.
Inherited release receipts live under data/baseline-v6; they are NOT V7 delivery evidence.
V7 passed 7/7 production source tests, 13/13 retained actor/director checks, rendered determinism/focus and V7-specific organic A/B tests, and 32/32 actual-master gates. All 915 native output frames decode. Encoded 10-scene/16-action sampling sheets were inspected; this is not an independent ear/clinical review or artistic perfection guarantee.

`data/ORGANIC_QA.json` measures 1617 vertices per hero membrane, bounded travelling deformation, exact geometry returns, same-time picture differences and unchanged caption canvases. `data/V7_QA_PROVENANCE.json` binds current reports to the frozen native picture signature. The inherited director check compares V6 camera design against V5; it is not a claim that V7 adds nine new shots.

## Rebuild on Linux

Node20+, Python3.11+, and `tar`. Create a disposable Python environment and install the pinned requirements, then install Node dependencies:

```bash
python3 -m venv /path/to/disposable-venv
/path/to/disposable-venv/bin/pip install -r requirements.txt
npm ci
MONARCH_PYTHON=/path/to/disposable-venv/bin/python bash src/run-v7.sh
```

The portable runner verifies source/director, rendered determinism/focus and organic A/B proofs, then renders all 915 frames, assembles audio and runs actual-master gates. Native rendering is substantial on a software GPU. Never duplicate a live render or change its frozen picture inputs; matching completed chunks resume automatically. `build/` and `node_modules/` are disposable and not bundled. No reference frames/audio or optical-flow interpolation are used. The inherited GLB is not falsely represented as a new complete Blender/Cycles project.

## Music credit — retain when publishing
Original score: Monarch Studio. Instrument samples: FluidR3 GM via MIDI.js Soundfonts (Benjamin Gleitzman), CC BY3.0 US. https://github.com/gleitz/midi-js-soundfonts — https://creativecommons.org/licenses/by/3.0/us/ . Samples arranged and processed for this film.
