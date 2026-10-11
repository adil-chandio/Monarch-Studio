# Experiments, failures and fixes

## 2026-10-11 · Pre-render freshness gate

- **Test:** `studio/editor-brain/brain/concept.py gate DNA.json`
- **First result:** 17/18; failed transition-count gate because the DNA ledger named eight kinds while the renderer already contained a ninth physical transition—the expanding punched-ticket-hole bloom.
- **Cause:** implementation and ledger drift, not a missing visual.
- **Fix:** named `ticket_hole_bloom` explicitly in `DNA.json`; it is the expanding circular edge used by transition branch 4 and belongs to the ticket device.
- **Retest:** required before render; no target was weakened.
