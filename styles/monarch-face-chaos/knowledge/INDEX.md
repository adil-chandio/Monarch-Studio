# Knowledge Index · `monarch-face-chaos` (`WF-04`)

## Core Architecture

1. **Identity Lock (`characters/monarch/`)**:
   - Uses `CUSTOM_HERO_REAL_SHEET_v5.png` (`v1`–`v8` front and 3/4 views) and `v9` (`Side face` anchor) for 100% locked facial geometry, skin tone (`#C68B59`), spectacles (`#D4AF37`), and beard/mustache silhouette.
   - Pre-composited guide scenes are constructed with flood-fill background removal before plate generation to guarantee zero identity drift across extreme lighting changes.

2. **Depth-Aware Screen Projection Compositing (`src/build_chaos_video1.py`)**:
   - Background screen graphics (`X` cross, pulsing ring, vertical slit, wireframe globe, Monarch crown emblem, neural telemetry HUD) are rendered exclusively on the monolithic background screen behind the subject and behind hanging neural cables using luminance-aware silhouette mattes (`create_subject_matte`).
   - Subject rim lighting and edge spill dynamically wrap the screen color around the subject's hair, glasses, and shoulders.

3. **Spatial Audio Engineering (`src/audio_engine.py`)**:
   - Synthesizes a 48 kHz stereo master (`-13.90 LUFS`, `-1.50 dBFS` True Peak) combining the forensic reference timeline with 32–55 Hz sub-bass drops, metallic cable-whip transients, high-voltage neural arcs, and anamorphic flare risers.

## File Catalogue

- `README.md` — Human operating guide and release summary
- `style.json` — Permanent style metadata
- `workflow.json` — WF-04 workflow contract and delivery registry
- `src/build_chaos_video1.py` — 636-frame 1080×1920 master renderer
- `src/audio_engine.py` — 48 kHz stereo audio synthesizer
- `src/gate_chaos_video1.py` — 21-gate verifier
- `plates/*.png` — 10 lossless 9:16 hero plates
- `records/DELIVERY_GATES.md` — 21/21 gate report
- `records/GATE_REPORT.json` — Machine-readable gate output
- `records/DELIVERY_RECEIPT.json` — Drive IDs and MD5/SHA-256 provenance
- `records/MONARCH_CHAOS_VIDEO_1_LOOK_SHEET.jpg` — 12-panel hero look sheet
- `records/MONARCH_CHAOS_VIDEO_1_CONTACT_SHEET.jpg` — 42-panel contact sheet
