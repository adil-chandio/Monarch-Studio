# Monarch Stickman Animation (WF-01 Paper Cinema) · video brain

Style `monarch-stickman-animation` · workflow WF-01. Created 2026-10-13 03:17 PKT.

## Problems and fixes (append-only)

Use `tools/brain.py` to add entries. Do not edit old entries.
## P-001 · 2026-10-13 · status: fixed

- **Symptom:** Paper layers looked washed out, world and key light too bright
- **Cause:** World strength 0.9 plus area energy 900 at size 6
- **Fix:** World 0.3 colour (0.22,0.21,0.2). Key area size 2.5, energy 380, raking angle
- **Verified by:** Lookdev r2_wf01 and r3_wf01_t6: layers readable

## P-002 · 2026-10-13 · status: open

- **Symptom:** Still looks flat and grey, paper reads as boards
- **Cause:** No edge highlight, no shadow pass between layers, no paper texture
- **Fix:** Not fixed. Next: paper-layer shadows and edge highlights (NEXT_LEVEL)
- **Verified by:** Not yet

## P-003 · 2026-10-13 · status: open

- **Symptom:** Stick figure reads cheap next to the premium target
- **Cause:** Primitive shapes (sphere head, cube torso, cylinder limbs)
- **Fix:** Not fixed. Design a paper cut-out figure with a proper silhouette
- **Verified by:** Not yet

## P-004 · 2026-10-13 · status: open

- **Symptom:** Title text placement off-frame at some times
- **Cause:** Title sits at z 2.6 and 2.05 with camera framing that changes per shot
- **Fix:** Partly fixed. Check at each shot time before accepting
- **Verified by:** Lookdev r3_wf01_t6 shows both lines

