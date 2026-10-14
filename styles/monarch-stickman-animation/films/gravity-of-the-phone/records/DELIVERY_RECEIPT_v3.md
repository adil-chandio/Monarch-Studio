# DELIVERY RECEIPT — THE GRAVITY OF THE PHONE · WTF-30 #1 · **v3**

- Delivered: 2026-10-14 · task `EMS-20261014-002` · supersedes v2 (`DELIVERY_RECEIPT_v2.md`, Drive `1vzNjW3FeXOMoJ4HDGqM-km5BCKw8IUfp`) and v1 (`DELIVERY_RECEIPT_v1.md`)
- File: `THE_GRAVITY_OF_THE_PHONE_WTF30_01_v3.mp4` · 61,573,207 bytes · 20.00 s · 600 frames · 1080×1920 @ 30 fps · h264 High yuv420p + aac lc 48 kHz stereo
- MD5 `f54c3b295011bb3310ce60f7d710e98b` · SHA-256 `8beef5da5cae88b4a82c6cc6d07b5a95a6d2e1dee56f632530c961495db8c5bd`
- Drive file `1LsfTOubsY6kHeWJatrSj4z71Qxbcpfh1` (md5 verified equal on upload) · folder https://drive.google.com/drive/folders/1ITMYpBexdmGaALpaf6BlTXNuGNfAFTiQ
- Drive side files: `LOOK_SHEET_v3.jpg` `1b-Usf3fQV4yjX7lYD0ucCw5CcFqxAwt_` · `gate_receipt_v3.json` `1fkMxnPAlM0VoM7ka2lciSdRU_yCEEX_O`
- Measured: -14.1 LUFS · TP -1.1 dBTP · LRA 6.7 · loop seam 3.13/255 · silence holes digital silence · sound-design-stem floor −50.4 dBFS
- Cuts detected: [2.0, 2.03, 3.8, 4.6, 14.6, 17.97, 19.7] planned + designed whip-roll frames 574–582 · WTF uncut 10.0 s from 4.9 s onset · shots [2.0, 1.8, 0.8, 10.0, 3.35, 1.75, 0.30]
- Law: gravity · meaning line "Phone ulta. Zindagi seedhi." · moral "Warna tum ulte." + the world rolls 180° · on-screen words 7 · beats 50 (max gap 1.45 s) · interrupts 13 · SFX+music voices 111 · 7 transition kinds
- Gates: **12/12 measured PASS** · **28/28 brain freshness PASS**

## What changed from v2 (why a v3 exists)

1. **Score (`src/music.py`).** A formant-synthesised **vocal-chop hook** ('oh · ah-oh · uh · eh-oh', `vox()`) rides the groove from beat 12 and climbs with the arp; odd 16ths jump an octave from bar 3; a reversed 'oh' under the lens look; a riser into the let-go; a reverse swell into the hot word; a whomp + whoosh on the world roll; a cartoon **'uh-oh'** in the upside-down hold; a vinyl brake into the loop; plucks side-chained; tanh glue on the bus.
2. **Sound design.** 111 voices / 239 cues (v2: 96 / 170): sweat **plip + sizzle** per drop, field sparkle grains, flip lift whoosh, one dry **ink tick per letter** of the meaning line, world-roll whoosh + whomp, snap-back click.
3. **Picture.** Kick-synced **camera pump** (1.4 % zoom) + **chroma split ≤ 3 px**; **god-rays** from the phone while the field is on; **anamorphic streak** (flash at wake, pulses on kicks); **afterimages** on lunge / slips / fall; ECU **amber rim light**; **kinetic letter cascade** on the meaning line; and the payoff — **the whole world whip-rolls 180°** on 'ulte.' (punch-zoom, 12-sample motion blur), holds upside-down so the upside-down word is the only upright thing, and the buzz snaps it back at 19.70.
4. **Gate.** Designed camera moves (`ROLL_WINDOWS`) are reported, not counted, by the cut detector — never inside the WTF; the 4:5 anchors are mirrored by the roll on the upside-down key frame (588).

## Measured gate lines

- PASS — G-W1 container 1080x1920 @ 30 fps H.264 + AAC: 1080x1920 30.0 fps h264 (High) (avc1 / 0x31637661) / aac (LC) (mp4a / 0x6134706D) 48000 Hz
- PASS — G-W13 duration 20.0–30.0 s: 20.00 s
- PASS — frame count = 600: 600 frames
- PASS — G-W2 frame 1 in motion (0→3 change > 0.15/255) + visual question by 0.8 s (0→24 change > 0.4/255): 0→3 1.11, 0→24 0.69
- PASS — max still ≤ 0.4 s (no 12-frame window without change): none
- PASS — G-W6 one uncut WTF set-piece ≥ 3 s, no cut inside it, no other shot > 4 s: WTF shot 10.0 s, detected cuts at [2.0, 2.03, 3.8, 4.6, 14.6, 17.97, 19.13, 19.17, 19.2, 19.23, 19.27, 19.3, 19.33, 19.37, 19.4, 19.7], unplanned [], inside-WTF [], designed roll frames [574, 575, 576, 577, 578, 579, 580, 581, 582], other shots [2.0, 1.8, 0.8, 3.35, 1.75, 0.3]
- PASS — G-W10 loop seam: last vs first frame mean abs diff ≤ 6/255: 3.13/255
- PASS — G-W5 silence hole 0.3–0.6 s before the WTF onset (< −60 dBFS RMS): 4.50–4.90 s = 0.40 s at -125.9 dBFS; second hole -108.6 dBFS
- PASS — hook: sound within the first 0.1 s (frame 1 is alive): first sound at 0.000 s
- PASS — G-W11 loudness −14 ± 1 LUFS, TP ≤ −1 dBTP: -14.1 LUFS, TP -1.1 dBTP, LRA 6.7 LU
- PASS — no synthetic noise floor (quietest 0.5 s of the sound-design stem ≤ −45 dBFS; score is a separate composed bus): stem quietest block -50.4 dBFS at 14.0 s; master quietest -18.3 dBFS at 13.0 s
- PASS — 4:5 safe centre: every subject inside y 285–1635 on key frames, ink share ≥ 0.72: 0.5s ink 0.78 phone=1036; 3.0s ink 0.92 phone=1259,hero_feet=1467,hero_head=982; 8.5s ink 0.93 phone=1241,hero_pivot=865; 11.4s ink 0.92 phone=1235,hero_pivot=1038; 16.67s ink 0.93 phone=1313,hero_feet=1313,hero_head=691,text_line1=440,text_line2=580; 19.1s ink 0.82 phone=1036,text_moral_a=668,text_moral_b=812; 19.6s ink 0.82 phone=881,text_moral_a=1262,text_moral_b=1113
