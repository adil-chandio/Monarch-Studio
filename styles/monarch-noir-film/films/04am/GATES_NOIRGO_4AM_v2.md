# GATES — NOIRGO film #3 "4:00 AM — Jo Jaagta Hai" v2 (measured on delivered file)

File: /home/user/NOIRGO_4AM_v2.mp4  ·  md5 ed233b75aa67f4255aa5c792e213467f

Scope: these are INDEPENDENT measured checks (ffmpeg / numpy). The 27-gate WF-03 suite (gate_window.py) was NOT run:
its helpers (gate_shadow.py) and film data (events_window.json, mix_stats.json, DNA) are not present for film #3 in the sandbox.

| Gate | Result | Measured | Target |
|---|---|---|---|
| G01 container | PASS | 1920x1080 h264 / aac 48000 Hz stereo | 1920x1080 h264 / aac |
| G02 duration 60 s | PASS | 60.00 s | 60.00 s ± 0.1 |
| G03 size under Drive 100 MiB limit | PASS | 15.76 MB | < 104.9 MB |
| G04 integrated loudness | PASS | -16.7 LUFS | -18 to -14 LUFS |
| G05 true peak | PASS | -3.6 dBTP | <= -1.0 dBTP |
| G06 loudness range | PASS | 13.7 LU | <= 16 LU |
| G07 black runs = intentional text cards only (0.0–0.2 s fade-in; 44 s hold; 47–60 s text cards) | PASS | blackdetect: 0.00–0.21 s, 44.00–44.46 s, 47.17–59.96 s (text on black, S06/S08 by design) | informational — design intent |
| G08 mean luma in noir band 12–40 | PASS | 21.6/255 | 12–40 |
| G09 dark-pixel share >= 60 % | PASS | 84.7 % | >= 60 % |
| G10 no blown highlights (p99.9 < 250 on 95 % of frames) | PASS | 100.0 % frames | >= 95 % |
| G12 scene cuts vs timeline boundaries (8, 16, 24, 34, 44, 52, 57) | PASS | detected 8.0, 16.0, 24.0, 34.0, 44.0 s; 52 & 57 s are dark text-card cuts (low scene score) | the 5 bright cuts must be detected |

Result: 11/11 measured checks PASS.
