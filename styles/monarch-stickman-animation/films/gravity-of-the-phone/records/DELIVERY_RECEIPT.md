# DELIVERY RECEIPT — THE GRAVITY OF THE PHONE · WTF-30 #1 · **v4**

- Delivered: 2026-10-14 · task `EMS-20261014-002` · supersedes v3 (`DELIVERY_RECEIPT_v3.md`, Drive `1LsfTOubsY6kHeWJatrSj4z71Qxbcpfh1`), v2 (`_v2`) and v1 (`_v1`)
- File: `THE_GRAVITY_OF_THE_PHONE_WTF30_01_v4.mp4` · 61,998,081 bytes · 20.00 s · 600 frames · 1080×1920 @ 30 fps · h264 High yuv420p + aac lc 48 kHz stereo
- MD5 `b2735dbf9ff18dc2e8f3fbf2be341c22` · SHA-256 `8da959fff87a994025b173f66dcafd889e9f749304a727cbd9b89060d8743482`
- Drive file `1Zi87F-qYb-tGENwdPdMGeP4jVAbeggGl` (md5 verified equal on upload) · folder https://drive.google.com/drive/folders/1ITMYpBexdmGaALpaf6BlTXNuGNfAFTiQ
- Drive side files: `LOOK_SHEET_v4.jpg` `1qe20v4NuD7Rcm5J_dOVxwDPu8snEVXzU` · `gate_receipt_v4.json` `1kY9Kn1TeqrtgNBTyZ9RonrA4ORN190ej`
- Measured: -14.1 LUFS · TP -1.3 dBTP · LRA 6.5 · loop seam 3.40/255 · silence holes digital silence · sound-design-stem floor −49.1 dBFS
- Cuts detected: [2.0, 2.03, 3.8, 4.6, 14.6, 17.97, 19.13, 19.17, 19.2, 19.23, 19.27, 19.3, 19.33, 19.37, 19.4, 19.7] (planned cuts + the designed whip-roll frames 574–582) · WTF uncut 10.0 s from 4.9 s onset
- Law: gravity · meaning line "Phone ulta. Zindagi seedhi." · moral "Warna tum ulte." + the world rolls 180° · on-screen words 7 (digits on the lock screen / clock are not words) · beats 55 (max gap 1.45 s) · interrupts 16 · sound voices 117 / cues 245
- Gates: **12/12 measured PASS** · **28/28 brain freshness PASS**

## What changed from v3 (why a v4 exists)

The user asked for two things: the phone must be an **iPhone**, and the film must carry details that people cannot help discussing — "comment kiye baghair na reh saken". v4 keeps v3's score, sound design, type and the 180° world roll, and adds **the comment engine**: seven planted details, each visible on a normal watch or a pause (no subliminal frames, no hidden tricks), each physically motivated by the film's one broken law.

| plant | what happens | why people comment | when |
|---|---|---|---|
| `iphone_941` | the phone is an iPhone and its lock screen reads 9:41 (Apple's keynote time); the wall clock reads 9:41 too | brand-fan recognition / 'did you notice' flex | 1.45–2.0 s |
| `time_flies` | while the field is on, the wall clock's hands spin through 5 hours (9:41 → 2:41) and the lock screen races with them; both stop dead at the drop | relatable ('that's me every night') + spot-it | 4.9–12.33 s |
| `photo_cameo` | a framed photo: Monarch-in-the-photo is pulled across the glass and plastered to the edge nearest the phone; the friend turns to watch; after the drop he slides down the glass | background character + debate ('why only one of them?') | 5.0–12.9 s |
| `photo_points` | on 'tum' the friend in the photo points straight at the lens, then the world rolls | direct address / eye-contact reflex | 18.64–19.7 s |
| `moth` | a moth circles the lamp, leaves it for the brighter screen, orbits the phone like a satellite while the field is on (tighter and faster), tumbles when the field dies and staggers back to the lamp | 'we are the moth' metaphor + tiny-moving-thing eye magnet | 0.0–14.0 s |
| `steam_away` | the coffee steam bends AWAY from the phone while everything else falls toward it (hot air is buoyant: it moves opposite to gravity) | physics debate with a defensible answer | 5.0–12.5 s |
| `spiral_light` | the lock-screen wallpaper is a slowly turning amber spiral; in the ECU its bands sweep his face | hypnotic motion on the brightest object | 1.55–11.78 s |

- **The iPhone** (`render.phone_tile` / `phone_image`): an upright 2-D tile (lock screen or titanium back) projected onto the desk plane with an exact affine (top end turned 22°, elevation sin E = 0.50); visible thickness edge with the USB-C slot and speaker holes; side buttons on the long edge. Lock screen: Dynamic Island, lock glyph, the time in Montserrat 300, amber spiral wallpaper (`_spiral_wallpaper`, 0.22 rev/s, 4× faster with the field), notification pills that rise on each ding. Back: brushed natural titanium, triple-camera plateau with flash + LiDAR, the bitten-apple mark engraved.
- **Time flies** (`scene.clock_minutes`): 9:41 until the field; then 5 h pass by the drop (ease-in 1.9) on the wall clock (live hands + motion smear, `draw_clock_hands`) and on the lock screen; both stop dead at 12.30 with a spring. Sound: 60 five-minute ratchet ticks accelerating with the hands, a wooden tock + spring at the stop.
- **The photo** (`scene.photo_state`, `render.photo_tile`): at world (690, 1000), left of the shelf; Monarch-in-the-photo slides to the glass edge nearest the phone (hits at 5.60 with a bounce, a thump + glass tink), the friend's eyes and brow follow him; after the drop he slides down the glass (squeak); on 'tum' (18.64, S6 only) the friend's arm rises and points at the lens with a foreshortened glove. The frame itself tilts 6° toward the phone with the field.
- **The moth** (`scene.moth_state`): orbits the lamp (1.5× cartoon scale), migrates to the brighter screen at 1.55, orbits the phone tighter and faster with the field, tumbles at the drop, staggers back to the lamp. Sound: a papery 24 Hz flutter in natural bursts whose level follows the shot.
- **Steam away** (`scene.steam_dir`): three wisps from the cup; their direction blends from straight-up to *away from the phone* with the field (buoyancy opposes gravity) — a physics argument with a defensible answer.
- **Spiral light in the ECU**: the rim light's amplitude is modulated by the same log-spiral so slow amber bands sweep his hood and the wall.
- Mastering: limiter ceiling moved to TP − 0.5 dB so the AAC-encoded true peak sits at −1.3 dBTP (v3 sat at −1.1; the first v4 pass measured −1.0, legal but with no margin).

## Measured gate lines

- PASS — G-W1 container 1080x1920 @ 30 fps H.264 + AAC: 1080x1920 30.0 fps h264 (High) (avc1 / 0x31637661) / aac (LC) (mp4a / 0x6134706D) 48000 Hz
- PASS — G-W13 duration 20.0–30.0 s: 20.00 s
- PASS — frame count = 600: 600 frames
- PASS — G-W2 frame 1 in motion (0→3 change > 0.15/255) + visual question by 0.8 s (0→24 change > 0.4/255): 0→3 1.03, 0→24 0.89
- PASS — max still ≤ 0.4 s (no 12-frame window without change): none
- PASS — G-W6 one uncut WTF set-piece ≥ 3 s, no cut inside it, no other shot > 4 s: WTF shot 10.0 s, detected cuts at [2.0, 2.03, 3.8, 4.6, 14.6, 17.97, 19.13, 19.17, 19.2, 19.23, 19.27, 19.3, 19.33, 19.37, 19.4, 19.7], unplanned [], inside-WTF [], designed roll frames [574, 575, 576, 577, 578, 579, 580, 581, 582], other shots [2.0, 1.8, 0.8, 3.35, 1.75, 0.3]
- PASS — G-W10 loop seam: last vs first frame mean abs diff ≤ 6/255: 3.40/255
- PASS — G-W5 silence hole 0.3–0.6 s before the WTF onset (< −60 dBFS RMS): 4.50–4.90 s = 0.40 s at -115.3 dBFS; second hole -119.4 dBFS
- PASS — hook: sound within the first 0.1 s (frame 1 is alive): first sound at 0.000 s
- PASS — G-W11 loudness −14 ± 1 LUFS, TP ≤ −1 dBTP: -14.1 LUFS, TP -1.3 dBTP, LRA 6.5 LU
- PASS — no synthetic noise floor (quietest 0.5 s of the sound-design stem ≤ −45 dBFS; score is a separate composed bus): stem quietest block -49.1 dBFS at 14.5 s; master quietest -18.2 dBFS at 13.0 s
- PASS — 4:5 safe centre: every subject inside y 285–1635 on key frames, ink share ≥ 0.72: 0.5s ink 0.77 phone=1036; 3.0s ink 0.92 phone=1259,hero_feet=1467,hero_head=982; 8.5s ink 0.93 phone=1241,hero_pivot=865; 11.4s ink 0.92 phone=1235,hero_pivot=1038; 16.67s ink 0.93 phone=1313,hero_feet=1313,hero_head=691,text_line1=440,text_line2=580; 19.1s ink 0.81 phone=1036,text_moral_a=668,text_moral_b=812; 19.6s ink 0.81 phone=881,text_moral_a=1262,text_moral_b=1113
