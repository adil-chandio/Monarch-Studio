# Monarch Face · Cyber-Sovereign Chaos (`WF-04`)

> **2026-10-17 user review:** The delivered v2 was **rejected**: its 2.5D image-plate face moves like jelly. The prior 21/21 checks measured format/edit continuity, **not** this subjective failure. v2 Drive links stay live as *historical* deliveries, not an approved cinematic 3D master. An actual 3D remake is in [true3d/](true3d/README.md) **look development only**; its current mesh/wardrobe fails visual QA and no v3 master has been delivered. Do not call the photo-textured prototype the requested finished 3D film.

- **Style ID:** `monarch-face-chaos`
- **Workflow contract:** `WF-04`
- **Trigger:** `CHAOSGO <reference_or_topic>`
- **Normalized state:** **ACTIVE (`R1`)**
- **Default format:** `1080×1920` (9:16 Full HD), `30.00 fps`, `48 kHz` Stereo AAC (`-14.0 LUFS ± 1.0 LU`)

## Style Definition

`monarch-face-chaos` combines forensic frame-accurate edit reconstruction with locked **CUSTOM_HERO (`MONARCH`)** real facial identity (`CUSTOM_HERO_REAL_SHEET_v5.png`, `CUSTOM_HERO_REAL_BODY_SHEET_v2.png`, and `v9` side-profile anchor) inside a dark cyber-cathedral / monolithic monolith aesthetic.

Every frame is driven by a deterministic Python compositing & procedural VFX engine (`src/build_chaos_video1.py`) paired with a 48 kHz spatial audio engine (`src/audio_engine.py`) and verified by a 21-gate automated test suite (`src/gate_chaos_video1.py`).

## Release #1 · `MONARCH CHAOS VIDEO 1 · SOVEREIGN OVERLOAD`

- **Task ID:** `EMS-20261013-001`
- **Master Video Drive ID (`Chaos video 1`):** `1CWt3Yr0mLDLV4rFcmvtCbdGv-hXTtO8W`
- **Master Video Drive ID (`Wf-04` Root):** `1gKsQyxepHVS5jrOt0abxHsZH-CMGi-_1`
- **Side-by-Side Sync Compare Drive ID:** `1v-lBJ9k-HGiX6YjNJNpYg6xNhZFW4Owr`
- **Source Package Drive ID:** `1KBK6A7fD9041lDMOb9Rfas4BCqlXU_Xe`
- **Look Sheet Drive ID:** `1ZzbaawT8Qzl98fK_3M6GuI82etAdEA6u`
- **Contact Sheet Drive ID:** `1a7DddEqnpUpFZUbg8Z6S5lUMX7iuSKS1`
- **Gate Report Drive ID:** `1aum2KJd3UyI6rtktQoefw5traauu2unW`
- **MD5:** `26d6f611effb4074993b163951521448`
- **SHA-256:** `c2f343bd6a791009996d544f0ac03152357baef3950e63a8e5c064037d7524bf`
- **Specs:** `1080×1920`, `30.00 fps`, `636 frames` (`21.20 s`), `-13.90 LUFS`, `-1.50 dBFS` True Peak, `21/21` gates passed.

## Last delivered (historical; user-rejected visual approach) · `MONARCH CHAOS VIDEO 1 v2 · SOVEREIGN OVERLOAD`

- **Task ID:** `EMS-20261013-002` · **21/21 objective gates PASS**.
- **Latest master:** [MONARCH_CHAOS_VIDEO_1_MASTER_v2.mp4](https://drive.google.com/file/d/10nBp4Nsr3FlqxTOCKoU2cu5N44PYz-7M/view?usp=drivesdk) (`Chaos video 1` folder; Drive ID `10nBp4Nsr3FlqxTOCKoU2cu5N44PYz-7M`; root copy `1sBFi9jFjCp8a7OpRpbA8gb7EZm0CTA_I`).
- **Master provenance:** `23,291,460` bytes · MD5 `f5d09353fab1ae7d52fb0a906f4f5598` · SHA-256 `8811eee1147102e028952716a7d743a345de2fbaab9eac3759483c27ea07c3f4` · `1080×1920`, `30.00 fps`, `636 frames / 21.20 s`, `48 kHz stereo`, `-13.97 LUFS`, `-1.50 dBFS` peak.
- **Creative upgrade:** 10 character plates consistently use the locked REAL face v5 + body v2 (slim charcoal blazer, open-collar black shirt, slim black trousers). Frame-by-frame 2.5D facial/head, torso, shoulder and hand motion, including pointing action 🫵; behind-subject neon projections; 24K-gold crown 👑 positioned above the `MONARCH STUDIO` finale title. The final hero-to-logo edit uses a brief gold flash rather than ghosting the face.
- **Inspection/provenance:** [Side-by-side compare](https://drive.google.com/file/d/1uwQ14-kOpA6Lm6tYisPEztUseLZM48uz/view?usp=drivesdk) · [12-shot look sheet](https://drive.google.com/file/d/13H0WquPh_SOzlYNkrYTjlS4DjeRUINtu/view?usp=drivesdk) · [42-frame contact sheet](https://drive.google.com/file/d/1KCa_LV-R1kmkv7k2fBx0RkIUeUIYU5H2/view?usp=drivesdk) · [21/21 gate report](https://drive.google.com/file/d/16BZjoWexLNJOpOCqm2jZBcL-IkkvV8pO/view?usp=drivesdk) · [source package](https://drive.google.com/file/d/1Devm-wKU3QZ5DTXgL5pHV2Udqxl6S59f/view?usp=drivesdk). Checksums and prior releases are in `records/DELIVERY_RECEIPT.json`.
- **Cross-platform hubs:** [Notion](https://app.notion.com/p/WF-04-Monarch-Face-3f8807e1e91681efb335eafb037ca211) · [Notion registry row](https://app.notion.com/p/WF-04-Monarch-Face-3f8807e1e91681368ceee607f8aaf092) · [Linear MON-65](https://linear.app/monarchmation/issue/MON-65/00-resume-key-chaosgo-wf-04-monarch-face-state-and-links) · [Google Doc HUB](https://docs.google.com/document/d/1Vx2t3z5Kx_gUMd2nkPjdqa3kc-BGDe8sj2Cua4pvxEY/edit).
- **Prior link safety:** Both previously issued v2 revisions remain live as `_v2_pre_motion_boost` and `_v2_pre_flash_fix` files; all earlier Drive URLs still resolve. The unsuffixed `_v2` video is the final clean-shutter cut. Historical v1 remains untouched.

## Implementation Map

| Path | Purpose |
|---|---|
| `src/build_chaos_video1.py` | Frame-exact 636-frame (`1080×1920`) compositor & procedural VFX renderer |
| `src/audio_engine.py` | 48 kHz stereo spatial audio & sub-bass transient synthesizer |
| `src/gate_chaos_video1.py` | 21-gate objective verification CLI |
| `plates/` | 10 lossless 9:16 hero plates (`Front`, `3/4`, `v9 Side Profile`, `Sovereign Crown`) |
| `records/DELIVERY_GATES.md` | 21/21 objective gate report |
| `records/DELIVERY_RECEIPT.json` | Complete Drive ID and hash provenance receipt |
| `records/MONARCH_CHAOS_VIDEO_1_LOOK_SHEET.jpg` | 12-panel key state look sheet |
| `records/MONARCH_CHAOS_VIDEO_1_CONTACT_SHEET.jpg` | 42-panel full timeline contact sheet |
