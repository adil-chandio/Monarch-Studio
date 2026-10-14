# WF-04 · MONARCH FACE · CHAOS VIDEO 2 — DELIVERY GATES REPORT

- **Master:** `MONARCH_CHAOS_VIDEO_2_MASTER.mp4` (`49,467,617` bytes · MD5 `51e662222a409c2bf8ae7c57ac8c4d9c`)
- **Format:** `1080×1920` (9:16) · `30.00 fps` · `1336 frames` (`44.53 s`)
- **Audio:** 48 kHz stereo AAC · `-14.87 LUFS` · true peak `-1.50 dBFS` · corr `0.8155`
- **Result:** **21/21 GATES PASSED**

| Gate | Check | Status | Measured |
|---|---|---|---|
| `G01` | Master MP4 exists and is non-empty | PASS | `49,467,617 B` |
| `G02` | Exact Full-HD 9:16 vertical resolution (1080x1920) | PASS | `1080x1920` |
| `G03` | Exact frame rate (30.00 fps) | PASS | `30.00 fps` |
| `G04` | Reference length: 1336 frames / 44.53s | PASS | `1336 frames (44.53s)` |
| `G05` | 48 kHz stereo mastered audio stream | PASS | `48000 Hz, 2 ch` |
| `G06` | Loudness in cinematic short range (-16.5 to -11.0 LUFS) | PASS | `-14.87 LUFS` |
| `G07` | True-peak ceiling safety (<= -1.0 dBFS) | PASS | `-1.50 dBFS` |
| `G08` | Stereo spatial width active (L/R decorrelation present) | PASS | `corr=0.8155` |
| `G09` | Act A cold open is dark and pulsing (reference dark intro) | PASS | `mean=25.0, max=31.4` |
| `G10` | Act B throne awakening brightens and the neural-sync HUD act is present | PASS | `B=52.0 vs A=25.0` |
| `G11` | Act C chaos projection montage has real shot variety (15-frame cuts) | PASS | `std=18.0` |
| `G12` | Act D triad close-up/profile/pointing shots are readable (not blown out) | PASS | `mean=60.2` |
| `G13` | Act E chaos burst fires >= 20 frame-locked transitions in 6.6 s | PASS | `66 transitions` |
| `G14` | Act F sovereign stance moves less than the Act E chaos burst (locked wide shots) | PASS | `motion F=5.56 vs E=15.26 per frame` |
| `G15` | Act G finale montage accelerates (15->4 frame cuts) with strobes | PASS | `71 transitions, peak=228.9` |
| `G16` | Face stays readable through the finale build (no permanent white-out) | PASS | `median-band luma=96.7` |
| `G17` | Reference-matched gold impact flash lands at 40.25-40.6 s (luma spike > 150) | PASS | `peak=228.9 at frames 1195-1250` |
| `G18` | Crowned MONARCH STUDIO emblem holds: warm gold dominant over blue in act H | PASS | `R=25.2 vs B=15.4` |
| `G19` | All 10 canonical hero plates present in styles/monarch-face-chaos/plates | PASS | `10/10 plates` |
| `G20` | Look sheet, contact sheet and plan JSON present | PASS | `sheets + plan verified` |
| `G21` | Deterministic MD5 checksum recorded | PASS | `51e662222a409c2bf8ae7c57ac8c4d9c` |
