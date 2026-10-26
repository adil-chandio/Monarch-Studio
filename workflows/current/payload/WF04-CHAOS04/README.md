# WF-04 · MONARCH CHAOS 04 — delivered

**Master:** `MONARCH_CHAOS_VIDEO_4_MOTION_MASTER.mp4` · Drive `1pvWrjJ1Gk1_I_KQNayNW6Mir1MnCtgi4`
44,741,521 B · MD5 `bf4a8925e3cb399bfcaaeaef1a4dfad5` (local == Drive read-back) · 44.40 s · 1332 frames
1080×1920 · 30 fps · H.264 High yuv420p bt709 · AAC 48 kHz stereo 256 kb/s · **−16.0 LUFS** · TP −5.11 dBFS · **23/23 gates**

## Pipeline (all measured from the decoded source)
1. `analyze_reference.py` → 47 source shots, cut grid, palette, 245 onsets, BPM.
2. `make_assets.py` → 5 light leaks, impact flash, gold crowned MONARCH STUDIO end card.
3. `render_chaos04.py` → 8-act plan (`work/ACT_PLAN.json`), per-act grade (contrast / gamma / split tone /
   vignette / bloom), animated leaks, neural-sync HUD act, beat-snapped cuts, 3 climax strobes, end card,
   BS.1770 loudness mastering to −16 LUFS with a true-peak guard, H.264 encode at 9 Mbps ceiling.
4. `verify_chaos04.py` → 23 gates measured on the actual master (frames decoded, audio analysed).
5. `write_report.py` → `output/DELIVERY_GATES_CHAOS04_v1.md`.

## Files
- `output/CHAOS04_MASTER.mp4` — delivered master (local, git-ignored; Drive is the store)
- `output/CHAOS04_LOOK.png` — look sheet, `output/GATE_REPORT_CHAOS04_v1.json` / `.md` — measured gates
- `output/DELIVERY_RECEIPT.json` — Drive IDs, MD5s, verification state
- `refs/` — CHAOS 03 master analysis used as the house standard (gates, look, contact sheet)

## Honest limits
- The raw footage carries a third-party **@VKTMDUBZ** watermark in every frame. Not removed, not covered.
  This master is a private style/proof cut, not a cleared publication asset.
- Source is HEVC 720×1280 upscaled to 1080×1920 — no invented detail.
- Nothing was generated: 100% of frames are from the supplied video.

## Repo note
`styles/` has no `monarch-face-chaos` (WF-04) style yet, so this run's method lives here in the task
payload. Promoting it to a permanent style is a separate step and has NOT been claimed.
