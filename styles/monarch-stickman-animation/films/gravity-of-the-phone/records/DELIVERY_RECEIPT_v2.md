# DELIVERY RECEIPT — THE GRAVITY OF THE PHONE · WTF-30 #1 · **v2**

- Delivered: 2026-10-14 · task `EMS-20261014-002` · supersedes v1 (`DELIVERY_RECEIPT_v1.md`, Drive `118VOjnmzDmTrTuz8iCsGPwIwWUvJDbPJ`)
- File: `THE_GRAVITY_OF_THE_PHONE_WTF30_01_v2.mp4` · 60,699,977 bytes · 20.00 s · 600 frames · 1080×1920 @ 30 fps · h264 High yuv420p + aac lc 48 kHz stereo
- MD5 `dc13effd2c86277767b29dec7769bca4` · SHA-256 `e0bc302cf89c4a55a4275cbcd03e13a446e0b2281cada4edddf9ea96bbf603f1`
- Drive file `1vzNjW3FeXOMoJ4HDGqM-km5BCKw8IUfp` (md5 verified equal on upload) · folder https://drive.google.com/drive/folders/1ITMYpBexdmGaALpaf6BlTXNuGNfAFTiQ
- Drive side files: `LOOK_SHEET_v2.jpg` `1ym5SUyr4ZlYrEUPB1dr--gNIG3n59fvP` · `gate_receipt_v2.json` `1PV2rrkhL3Was925qHqWiQ-a-vYA2HeEu`
- Measured: -14.1 LUFS · TP -1.2 dBTP · LRA 6.6 · loop seam 3.23/255 · silence holes −119.8 / −116.3 dBFS · sound-design-stem floor −49.7 dBFS
- Cuts detected: [2.0, 2.03, 3.8, 4.6, 14.6, 17.97] (all planned) · WTF uncut 10.0 s from 4.9 s onset · shots [2.0, 1.8, 0.8, 10.0, 3.35, 2.05]
- Law: gravity · meaning line "Phone ulta. Zindagi seedhi." · moral "Warna tum ulte." · on-screen words 7 (4 + 3) · beats 44 (max gap 1.45 s) · interrupts 10 · SFX voices 96 · score 122.4 BPM E minor → E major
- Gates: **12/12 measured PASS** · **28/28 brain freshness PASS**

## What changed from v1 (why a v2 exists)

1. **Score.** `src/music.py` — a procedural, event-locked 122.4 BPM score (music-box motif → drop groove → breakdown → tape-stop silence → E-major relief → punchline pings) summed on its own bus under the sound design (`MUSIC_GAIN 0.85`), sidechain-pumped by the kick, dotted-eighth ping-pong delay.
2. **Sound design.** 96 voices / 170 cues (v1: 78 / 150): grid-locked heartbeat, hook buzz on the loop seam, bells on the dings, accelerating paper-snap fill, land stutter gates, text snap-out click.
3. **Moral.** S6 now carries "Warna tum ulte." (VO `audio/vo_moral_b.mp3`, 18.00–19.50): the last word lands **upside-down** and the whole line snaps out on the returning buzz — a 3-word payoff that keeps G-W7 at exactly 7 words.
4. **Picture.** Beat-pulse on the glow, flow specks toward the phone, sweat drops pulled sideways, land squash-and-stretch, vignette + floor-grid release over 0.2 s after the drop, falling lines on the restore, 1-frame tint on impact (alpha 30), moral spin-in.
5. **Hygiene.** CRC32-deterministic `hash01` (parallel halves now agree at the seam), SFX-stem noise-floor measurement, cut_s6 moved 18.20 → 17.95 to give the moral VO room.

## Measured gate lines

- PASS — G-W1 container 1080x1920 @ 30 fps H.264 + AAC: 1080x1920 30.0 fps h264 (High) (avc1 / 0x31637661) / aac (LC) (mp4a / 0x6134706D) 48000 Hz
- PASS — G-W13 duration 20.0–30.0 s: 20.00 s
- PASS — frame count = 600: 600 frames
- PASS — G-W2 frame 1 in motion (0→3 change > 0.15/255) + visual question by 0.8 s (0→24 change > 0.4/255): 0→3 1.11, 0→24 0.69
- PASS — max still ≤ 0.4 s (no 12-frame window without change): none
- PASS — G-W6 one uncut WTF set-piece ≥ 3 s, no cut inside it, no other shot > 4 s: WTF shot 10.0 s, detected cuts at [2.0, 2.03, 3.8, 4.6, 14.6, 17.97], unplanned [], inside-WTF [], other shots [2.0, 1.7999999999999998, 0.7999999999999998, 3.3499999999999996, 2.0500000000000007]
- PASS — G-W10 loop seam: last vs first frame mean abs diff ≤ 6/255: 3.23/255
- PASS — G-W5 silence hole 0.3–0.6 s before the WTF onset (< −60 dBFS RMS): 4.50–4.90 s = 0.40 s at -115.2 dBFS; second hole -114.8 dBFS
- PASS — hook: sound within the first 0.1 s (frame 1 is alive): first sound at 0.000 s
- PASS — G-W11 loudness −14 ± 1 LUFS, TP ≤ −1 dBTP: -14.1 LUFS, TP -1.2 dBTP, LRA 6.6 LU
- PASS — no synthetic noise floor (quietest 0.5 s of the sound-design stem ≤ −45 dBFS; score is a separate composed bus): stem quietest block -49.7 dBFS at 14.5 s; master quietest -19.4 dBFS at 10.0 s
- PASS — 4:5 safe centre: every subject inside y 285–1635 on key frames, ink share ≥ 0.72: 0.5s ink 0.78 phone=1036; 3.0s ink 0.91 phone=1258,hero_feet=1465,hero_head=982; 8.5s ink 0.93 phone=1241,hero_pivot=865; 11.4s ink 0.92 phone=1235,hero_pivot=1038; 16.67s ink 0.93 phone=1311,hero_feet=1311,hero_head=689,text_line1=440,text_line2=580; 19.1s ink 0.82 phone=1036,text_moral_a=668,text_moral_b=812; 19.5s ink 0.82 phone=1036
