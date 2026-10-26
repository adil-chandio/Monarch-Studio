# WF-04 · MONARCH FACE · CHAOS VIDEO 2 — DELIVERY GATES REPORT

- **Master:** `MONARCH_CHAOS_VIDEO_3_MOTION_MASTER.mp4` (`36,492,634` bytes · MD5 `14abf0a5206a5f100972792f8c2bf0f7`)
- **Format:** `1080×1920` (9:16) · `30.00 fps` · `1333 frames` (`44.43 s`)
- **Audio:** 48 kHz stereo AAC · `-16.15 LUFS` · true peak `-1.50 dBFS` · corr `0.9414`
- **Result:** **22/23 GATES PASSED**

| Gate | Check | Status | Measured |
|---|---|---|---|
| `G01` | Master MP4 exists and is non-empty | PASS | `36,492,634 B` |
| `G02` | Exact Full-HD 9:16 vertical resolution (1080x1920) | PASS | `1080x1920` |
| `G03` | Exact frame rate (30.00 fps) | PASS | `30.00 fps` |
| `G04` | Reference length: 1336 frames (±4 concat joins) / 44.53s | PASS | `1333 frames (44.43s)` |
| `G05` | 48 kHz stereo mastered audio stream | PASS | `48000 Hz, 2 ch` |
| `G06` | Loudness in cinematic short range (-16.5 to -11.0 LUFS) | PASS | `-16.15 LUFS` |
| `G07` | True-peak ceiling safety (<= -1.0 dBFS) | PASS | `-1.50 dBFS` |
| `G08` | Stereo spatial width active (L/R decorrelation present) | PASS | `corr=0.9414` |
| `G09` | Act A cold open is dark and pulsing (reference dark intro) | PASS | `mean=26.5, max=33.3` |
| `G10` | Act B throne awakening brightens and the neural-sync HUD act is present | PASS | `B=57.3 vs A=26.5` |
| `G11` | Act C chaos projection montage has real shot variety (15-frame cuts) | PASS | `std=26.1` |
| `G12` | Act D triad close-up/profile/pointing shots are readable (not blown out) | PASS | `mean=68.7` |
| `G13` | Act E chaos burst fires >= 20 frame-locked transitions in 6.6 s | PASS | `27 transitions` |
| `G14` | Act F sovereign stance moves less than the Act E chaos burst (locked wide shots) | PASS | `motion F=1.97 vs E=10.69 per frame` |
| `G15` | Act G finale montage accelerates (15->4 frame cuts) with strobes | PASS | `117 transitions, peak=126.3 (base 60.1)` |
| `G16` | Face stays readable through the finale build (no permanent white-out) | PASS | `median-band luma=48.6` |
| `G17` | Reference-matched gold impact flash lands at 40.25-40.6 s (>= 2.2x the act base) | FAIL | `peak=132.4 vs base 79.1` |
| `G18` | Crowned MONARCH STUDIO emblem holds: warm gold dominant over blue in act H | PASS | `R=24.1 vs B=17.2` |
| `G19` | All 10 canonical hero plates present in styles/monarch-face-chaos/plates | PASS | `10/10 plates` |
| `G20` | Look sheet, contact sheet and plan JSON present | PASS | `sheets + plan verified` |
| `G21` | Deterministic MD5 checksum recorded | PASS | `14abf0a5206a5f100972792f8c2bf0f7` |
| `G22` | REAL MOVEMENT: walk act advances the body (>= 0.8 subject-band diff/frame) | PASS | `0.95 per frame` |
| `G23` | REAL MOVEMENT: pointing hop snaps in 8 frames (>= 3.8 subject-band diff/frame) | PASS | `4.30 per frame` |
