# Monarch Noir Film (WF-03 Midnight Platform Noir) · video brain

Style `monarch-noir-film` · workflow WF-03. Created 2026-10-13 03:17 PKT.

## Problems and fixes (append-only)

Use `tools/brain.py` to add entries. Do not edit old entries.
## P-001 · 2026-10-13 · status: fixed

- **Symptom:** Volumetric haze too noisy, lookdev grainy
- **Cause:** Density 0.022 at 24 spp
- **Fix:** Density 0.004 to 0.007 at 32 spp
- **Verified by:** Lookdev wf03_v2 vs wf03_vol

## P-002 · 2026-10-13 · status: fixed

- **Symptom:** Lamp barely lights the bench and ticket
- **Cause:** Point lamp 900 W at 6 m
- **Fix:** 4200 W point lamp, radius 0.9. Spot light on ticket is the next step
- **Verified by:** Lookdev r2_wf03 shows the ticket

## P-003 · 2026-10-13 · status: fixed

- **Symptom:** Ticket floats 1.3 m above the bench
- **Cause:** Ticket rise animation was left on in the lookdev time
- **Fix:** Ticket lies flat on the bench at z 0.73. Stamp moves with it
- **Verified by:** Lookdev r2_wf03

## P-004 · 2026-10-13 · status: open

- **Symptom:** Frame feels empty; ticket is small and the dolly is not in place
- **Cause:** Camera distances from the first layout, no slow dolly yet
- **Fix:** Not fixed. Next: slow dolly and tighter ticket framing (NEXT_LEVEL)
- **Verified by:** Not yet

## P-005 · 2026-10-13 · status: open

- **Symptom:** Film numbering drift: two claims for Film number 3 with different formats
- **Cause:** Registry drift recorded in studio/registry.json (4:00 AM v2 and AB KARO ABHI v1)
- **Fix:** Not reconciled. Reconcile before the next numbered film
- **Verified by:** Not yet

