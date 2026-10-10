# CUSTOM HERO — user's own face as a studio character (MONARCH STUDIO shared asset)
_created 2026-10-10 (turn 23) · **REAL face sheet v5 ACCEPTED (turn 28) · STICK sheets v3 delivered (turn 30) · MASTER BOARD v1 + CHARACTER BIBLE v1 (turn 31) · TURN 33: MOVED to the user's Drive folder "Monarch Face / MONARCH CHARACTERS" `1iPXavru1AXiSG5wRHuLKc5VNXhaVcXZK` (Realistic `1NpOJTSOY3zjkBR8LoktHDUFUSB8oW5jN` · Stickman `11uHSeU6wc81n9W_lRVvRU9arLQZTp3r8` · Shared & Reference `1dkk9Z3Js_wfSg2aIsTpmxlB9uNyD2OiJ` · Archive · old versions `1D-hvAls1B5QgoRs1fo54OpxdIR2JGwKt`) — file ids unchanged; NEW DIRECTION (user, turn 32): stickman = STICKMAN FACE, not his human face → stick-face hero v1 PREVIEW `1yMkEjUpi2ZDSM_KFx4HNfAYi_1UcVhX9` → TURNS 34–35: STICK FACE SHEET v4 `1b2Wj1lUGtZpOI-26UuxneCi6fm7G3zKc` + STICK BODY SHEET v4 `1zoHaynrUsosrjwU45I7WZHfFUj2lt7uc` + BIBLE v2 `1j-zZhDepXYw28nhsYzpgOs6nmAKPJORf` + BOARD v2 `1HkAE5dtx8mJqlpY6mPPIXjDAepYANrkQ` delivered — current set REAL face v5 · REAL body v2 · STICK face v4 · STICK body v4 — **LOCKED by default in turn 36** (12th identical message; lock default announced in turn 35; "change: ___" reopens) and registered in the studio registry / root RESUME / Notion hub / WF-03** · owner: the user (his face)_

## What it is
A character design of the user himself, built from two reference videos he uploaded to Drive:
- `VID_20261010_145131.mp4` `1TelE6KTVEglV-Nj3cp_1LiiYAFkphkQ9` (23 s, raw turnaround: front / L profile / back / R profile / front) — true structure.
- `Snapchat-1811422650.mp4` `1czlTX5v0W4KeXIVKrLNqMLPyeYc13BHC` (39 s, beauty-filtered turnaround) — the LOOK he wants (clean skin, groomed, "boss masculine").
- `Side face` `1ZtYyXj7buyP52reUgtg3kgAfmF8pwR4N` (12 s, dedicated right + left profile, turn 24) — the PROFILE authority: long straight nose (no bump) with a slightly dropped tip, thin lips set back, clearly receding soft chin, natural beard along/under the jaw and down the neck, big layered hair volume at the crown/back to the collar, long side locks IN FRONT of the ear (ear hidden).
All three files were made link-readable for ~5 s to curl them, then set private again. Frames live in `studio/characters/hero_refs/` (ref_* raw, ref2_* filtered).

Brief (user, turn 22–23): face must stay the same person; attractive · boss · masculine · fun · hooked · attention-grabbing · eye-catching · engaging; two sheets — 3-D ANIMATION and REALISTIC — with best expressions and a cute/hooked gaze.

## Deliverables (md5 verified) — LOCATION NOTE turn 33: the folder "MONARCH STUDIO / CHARACTERS · Custom Hero" `1E-GX7wD…` named below was emptied and trashed on 2026-10-10; every file now lives under "Monarch Face / MONARCH CHARACTERS" (see the turn-33 section at the end). Drive ids did not change.
| file | Drive id | md5 |
|---|---|---|
| `CUSTOM_HERO_REAL_SHEET_v2.png` 2464×2042 | `1GYG37g_b_-jNgFpQRdrTWlx4LOQLVr44` | 5e73803e3ab08babaa29cd96bec7f8f8 |
| `CUSTOM_HERO_ANIM_SHEET_v2.png` 2464×2042 | `1z6D-QxfYy0nlSQ4k1dRtqmqR7qx7WCM-` | 444d3376fa3e6865bf711933e0d5786b |
| `CUSTOM_HERO_parts_v2.zip` (hero portraits, turnarounds v2+v3, expression sets, `compose_sheet.py`, ref boards) | `1SVnwhQKgLi1YR1F8cAiUo0tpKtNcOk3A` | 0a83dca28c3e3ba280de1ee9833160ee |

Sheet anatomy: HERO SHOT (boss gaze) · TURNAROUND front / 3-4 / profile · EXPRESSIONS 01 warm smile · 02 confident smirk · 03 laugh · 04 surprise · 05 intense · 06 wink · identity + wardrobe + light notes.
Wardrobe chosen for the "boss" brief: fitted black shirt (top button open) + charcoal blazer, no tie. Light: soft key upper-left, teal + amber rims, charcoal backdrop.

## How it was made (repeatable)
1. Frames: `ffmpeg -vf fps=5` → sharpest frame per segment (Laplacian variance) → Haar face box → 7:9 crops (`hero_refs/`).
2. `generate_image` with the ref crops: hero portrait per style (v2 prompts: boss/masculine, same face) → turnaround (3 panels, profile facing right; ANIM needed v3 with the REAL turnaround as a layout reference to stop overlapping figures) → six-expression study per style.
3. `python3 studio/characters/compose_sheet.py REAL|ANIM v2` → sheet PNG + JPG (labels, bands, notes; assets at native 1:1 scale — never upscale).
History: v1 attempts (turn 22) were full-sheet single generations offered as options; the user picked none twice → switched to parts + own composition, no option picker.


## v3 (turn 24) — profile fix
User: "side face hamare reference video se match nahi ho raha" → he uploaded a dedicated side-face video. Fix: profile generated separately per style with the ref3 crops as the primary identity input (REAL v5 → v6 edit: receding chin + locks in front of the ear; ANIM v5/v6 kept a heroic jaw → v7 recreated from the REAL v6 profile as a silhouette reference in the CG style), then `compose_turnaround.py` swaps the right third of the turnaround with the new profile (head scaled to ~415 px panel width, hair top at ~50 px, background padded from the image's own edges — no upscaling). Sheets recomposed → v3.
| file | Drive id | md5 |
|---|---|---|
| `CUSTOM_HERO_REAL_SHEET_v3.png` | `1Qn9j53mLV1MvKq3wUzox_hDyojIOt9oc` | 6f44ae7af96dc27de1b5d343736c6c52 |
| `CUSTOM_HERO_ANIM_SHEET_v3.png` | `1dUXfryB_s9CA6M7xlkCTmyf76VcwWnbL` | 80535001ff27ca6c927fa0e883561055 |
| `CUSTOM_HERO_parts_v3.zip` (profiles v6/v7, turnarounds REAL v3 / ANIM v4, compose_turnaround.py, compose_sheet.py, ref3 crops) | `1xIlCh9u1-e089KGG0u-TGQBdbAfsFeiz` | 82498279d69db8ca81dc468724ea7651 |
v2 sheets stay on Drive as history. Residual (honest): the REAL profile's lower face reads slightly fuller than the real slim profile; fixable with one more edit pass if the user wants.

## v4 (turn 25) — profile pass 2 (slim lower face)
The user re-sent the side-face link → second pass on the residual: lower face slimmed (narrow cheek/jaw, slim neck, sparser cheek beard) via an edit of the v6/v7 profiles with the side-face frames (REAL v8, ANIM v8). `compose_turnaround.py` now fades the panel bottom instead of mirroring/replicating rows (mirrored lapel artefact seen in a test). Comparison board `CUSTOM_HERO_profile_compare_v4.jpg` (real frame | REAL v6 → v8 | ANIM v7 → v8).
| file | Drive id | md5 |
|---|---|---|
| `CUSTOM_HERO_REAL_SHEET_v4.png` | `1o12IfxP4lKPutESl7GAUvn81oI3Cqd_H` | f5628b0c29f82bb564b2660ed2ec1913 |
| `CUSTOM_HERO_ANIM_SHEET_v4.png` | `17Mbq-VaRdt5Twajhc1JbY6nugSqwUH13` | 037cec456d9e26796418124918a06bdd |
| `CUSTOM_HERO_parts_v4.zip` (profiles v8, turnarounds REAL v4 / ANIM v5, scripts, compare board) | `1dC1Dwec_D9caUKHwoE4_TT-Rr6ILt6AH` | bb22f2a84ec369a4a3aab85ac3770316 |
| `CUSTOM_HERO_profile_compare_v4.jpg` | `1NPM83k9_Kbw6A2kT088rOI0zxgy1TcrO` | c2fbdbbd7d1a4645537a38aedcd33a82 |
Current sheets = v4 (v2/v3 kept as history).

## v5 (turn 26) — profile rebuilt from scratch
The user sent the side-face link a third/fourth time without feedback (skipped the clarifying questions) → treated as "still not me": the profile was regenerated FROM SCRATCH per style using only right-facing profile refs (ref3_profR_a/b, mirrored ref3_profL_a, ref_profile_R, ref2_f_profR) + one front image for wardrobe/light, with an "exact likeness, nothing idealised" brief (young slim face, long straight nose, light beard under chin/jaw, long layered hair to the collar, ear visible with hair behind — as the video actually shows). REAL v9 / ANIM v9 → turnarounds REAL v5 / ANIM v6 → sheets v5. Correction to the earlier read: the ear is VISIBLE in the side-face video (hair behind it, a sideburn lock in front), not hidden.
| file | Drive id | md5 |
|---|---|---|
| `CUSTOM_HERO_REAL_SHEET_v5.png` | `1YTschdKJjpmsl4jIgC15y8yjek0zf1-M` | 020566659864a22ac68e65e3d96c0bd9 |
| `CUSTOM_HERO_ANIM_SHEET_v5.png` | `1k5xXFT68uTRyoSlSzmj67kaob30n4YEv` | eaf8f1dd090bb4eed8dc78ecf8727931 |
| `CUSTOM_HERO_parts_v5.zip` (profiles v9, turnarounds REAL v5 / ANIM v6, compare board, scripts) | `1qFBT8CpP3BOMmd9dJ9ui30e32ZvjwZ39` | 40aeb9b6eb5660feb31410a2e7a066a9 |
| `CUSTOM_HERO_profile_compare_v5.jpg` (2 real frames | REAL v9 | ANIM v9) | `1bpF8CQ4I49AEPab1k2w7CF7971_yD9B_` | 9ef2aee711b00be705b9846016504831 |
Current sheets = v5 (v2–v4 kept as history).

## Turn 28 — STICKMAN style + FULL-BODY sheets
User: "realistic face sheet is ready; now the animation sheet in STICKMAN style with my face, and full-body sheets for both." The animation style switched from Pixar-CG to the studio's own stick-figure DNA (NOIRGO MAX hero v2 body: oversized head, thin stick limbs, white 5-finger hands, white sneakers) with HIS face/skin/hair/beard on the stick head and the boss wardrobe (charcoal blazer, black shirt, white sneakers). Pipeline: stick hero bust (refs: CHARSHEET_HERO_v2 for the body style + REAL/ANIM hero portraits + profile ref) → stick bust turnaround (REAL turnaround as layout ref) → stick expressions ×6 → stick full-body turnaround ×4 views → stick poses ×6; REAL full-body turnaround ×4 + poses ×6 (refs: REAL hero + turnaround). Composition: `compose_sheet.py STICK` (face sheet) + new `compose_body_sheet.py` (turnaround + poses + proportions/wardrobe/palette notes).
| file | Drive id | md5 |
|---|---|---|
| `CUSTOM_HERO_STICK_SHEET_v1.png` (stickman face sheet: hero + turnaround + 6 expressions) | `1amd4MbXXnRMujV9X2Aq5Fq-hFsybpoFT` | 2fe2345e1964859ee1025fdb39f7506c |
| `CUSTOM_HERO_STICK_BODY_SHEET_v1.png` (full body: 4-view turnaround + 6 poses) | `1Qq0xWnLEETv4mrv5c2X6kdqgqwg5FS0D` | 6d9422013e6b42c32123648d1e082230 |
| `CUSTOM_HERO_REAL_BODY_SHEET_v1.png` (full body: 4-view turnaround + 6 poses) | `1sBmrG4h3Tnsmofvvrwf5djzKWRldXMm2` | 80aadf1835f780749d6d310871a6ab7f |
| `CUSTOM_HERO_parts_v6_stick_body.zip` (all 7 generated parts + both compose scripts) | `1gvkDWcH7L-M1JMvlgwKcAftvwiKaVSaD` | a466aafc47f222ff5375f405383469e2 |
Current set: REAL face v5 · STICK face v1 · REAL body v1 · STICK body v1 (the Pixar-CG ANIM sheets v2–v5 stay on Drive as history; the stickman is the animation style going forward).

## Turn 29 — v2 sheets ("next level" strips)
User repeated the stickman + full-body request after seeing v1 → upgraded instead of regenerating: new strips STICK head angles ×6, STICK hands ×6, STICK walk cycle (6 phases, side), STICK run cycle (5 phases, 3/4), REAL walk cycle ×6, REAL wardrobe variants ×4 (signature blazer · bomber · hoodie · overcoat), REAL hands ×6. New generic composer `compose_sheet_v2.py` (JSON spec: optional hero column + labelled strips, grid pills for 2-row studies).
| file | Drive id | md5 |
|---|---|---|
| `CUSTOM_HERO_STICK_SHEET_v2.png` 2464×3740 (hero · turnaround · expressions · head angles · hands) | `1VdlEZTzVf2pHoSwc7IjhllkCvjBKo5Yt` | 39b6c4033c0a5dcfaad78b43066ee7a7 |
| `CUSTOM_HERO_STICK_BODY_SHEET_v2.png` 1520×3848 (turnaround · poses · walk · run) | `1XR8kzOfm2JR0yOBGKA2YV-Du02Sq57yx` | b91ff16615d622332851deb8b5bffc7f |
| `CUSTOM_HERO_REAL_BODY_SHEET_v2.png` 1520×4716 (turnaround · poses · walk · wardrobe · hands) | `177bFsA2oy--XSZOqbRycGieIbYJuX8S-` | 9c579848370cd95d95261a1f56b17f87 |
| `CUSTOM_HERO_parts_v7_strips.zip` (7 new strips + compose_sheet_v2.py + specs) | `1fNLBTQ07WhKHoFZOUoShMh_ER5vuSQi-` | 4a14a657c0ebae3267483f094bb97ae0 |
Current set: REAL face v5 · STICK face v2 · REAL body v2 · STICK body v2 (v1 bodies / STICK face v1 kept as history).

## Turn 30 — STICK sheets v3 (animation-ready upgrade, no regeneration of approved parts)
The user re-sent the stickman + full-body brief (13th identical message) → instead of blind regeneration, a full-res QA pass (zero flaws found in v2) and an UPGRADE with the parts an animation character actually needs for a full-VO film: 6 more expressions (RAGE · MIND BLOWN · FEAR · SALUTE · EXHAUSTED · HEARTBROKEN), 12 lip-sync visemes (M-B-P · A-I · E · O · U-W · F-V · L · TH · S-Z · CH-SH-J · talk-smile · shout), eyes & blink chart (right · left · up · down · half blink · closed — screen-direction labels), 6 action poses (jump · landing · defeated · triumph · sit+phone · sprint start), a 6-phase jump cycle (side), and a MEASURED proportion + palette panel (`measure_proportions.py`: hair top = first Canny edge row in the head band, chin = Haar box bottom, shoulders = knee of the silhouette-extent curve, crotch = first row where the near-black trousers split into two dark runs, floor = last sneaker row; palette = median colours from fixed anatomical regions, lit albedo for the whites). Result on the front view: height 686 px = **4.06 heads** · head 169×148 px (w:h 0.88) · shoulders 121 px = 0.72 heads · hands hang to 2.64 heads · crotch 2.39 heads · legs 282 px = 1.67 heads · sneakers 37 px; side view hair top / floor within 2 / 1 px of the front. Palette: skin #A97051 · hair #151919 · blazer #2F3336 · shirt #191917 · trousers #050705 · glove #C2C6C4 · sneaker #B7C2BF · backdrop #0E1213 · rim teal #35605E · rim amber #8A5F3A.
New composer `compose_sheet_v3.py` (single 1376-wide column, HERO ROW = hero bust + stacked likeness column REAL v5 ↔ STICK, auto-wrapped notes, auto-fit subtitles). Reused panels come from the PNG masters (parts v6/v7 zips re-downloaded, md5 verified, re-privatised) — nothing re-generated, nothing upscaled. Generation lessons: wide strips need a wide strip as the FIRST reference (a portrait reference produced 896×1200 grids with overlapping figures); eye-direction cells must be labelled by what is actually rendered (cell 1 came out looking screen-right).
| file | Drive id | md5 |
|---|---|---|
| `CUSTOM_HERO_STICK_SHEET_v3.png` 1520×8748 (hero + likeness · turnaround · expressions 01–12 · visemes 01–12 · eyes & blink · head angles · hands) | `1Z434Pxr0aqsVHsrBF0AnMPTPxGREhyi3` | 4a44f07a7f984b039e82e9600fd80084 |
| `CUSTOM_HERO_STICK_BODY_SHEET_v3.png` 1520×6612 (measured proportions + palette · turnaround · acting poses · action poses · walk · run · jump) | `1xMSjERNvqBoZSlx81vRYB7PWCF50ygnb` | 637231047c7eedab827df9a68fdd6862 |
| `CUSTOM_HERO_parts_v8_stick_v3.zip` (7 new strips/panels + measurement JSON + debug overlay + compose_sheet_v3.py + measure_proportions.py + specs) | `19Tb1b4mKbt5w0VkPbbEOgMgskugi79yo` | cf38e1babcfd423a482a3526998b4439 |
Local JPG copies: `studio/characters/CUSTOM_HERO_STICK_SHEET_v3.jpg` (55c0be1d…) · `CUSTOM_HERO_STICK_BODY_SHEET_v3.jpg` (8e86f0b6…). **Current set: REAL face v5 · REAL body v2 · STICK face v3 · STICK body v3** (STICK v1/v2 sheets stay on Drive as history; REAL untouched this turn).

## Turn 31 — MASTER BOARD v1 + CHARACTER BIBLE v1 (consolidation, nothing regenerated)
The identical brief arrived a 14th time ("realistic is best … now the animation one in stickman style with this face … full-body sheets for both"). Both sets already exist, so this turn makes them impossible to miss: one board that shows the two styles side by side, and one PDF that holds every sheet at 1:1 in phone-readable pages.
- `compose_master_board.py` + `board_v1.json` → **CUSTOM_HERO_MASTER_BOARD_v1** 1080×1920 (studio reel frame): column 1 REALISTIC (hero portrait v2 master · expressions 01–06 · 4-view full-body turnaround · poses 01–06) | column 2 ANIMATION · STICKMAN (same four rows from the STICK masters). Every panel is a 1:1 DOWN-scale of an approved PNG master from parts v2 / v6 (re-downloaded, md5 = state file, re-privatised); captions under the panels (no pills over faces); the rejected REAL turnaround v2 was NOT used.
- `make_bible_pdf.py` + `bible_v1.json` → **CUSTOM_HERO_CHARACTER_BIBLE_v1.pdf** 15 pages @150 dpi: p1 cover = master board · p2 index (contents with real page numbers, identity lock, wardrobe, measured proportions, palette swatches, Drive ids) · p3 REAL face v5 (2464-wide page, 1:1) · p4–6 REAL body v2 · p7–11 STICK face v3 · p12–15 STICK body v3. Sheets are cut ONLY inside detected gap rows (rows whose max horizontal step < 8 on a blurred grey = page background only, run ≥ 24 px) with a balanced packer (smallest page count whose cuts fit 2068 px) — no panel or label is split (verified on the page thumbnails).
| file | Drive id | md5 |
|---|---|---|
| `CUSTOM_HERO_MASTER_BOARD_v1.png` 1080×1920 | `1gNXdw63dMkbrc7vsiBAxbso1QuMYfcL9` | 411a48df6ed519504df57769206aafaf |
| `CUSTOM_HERO_CHARACTER_BIBLE_v1.pdf` 15 pages, 5,006,689 B | `12lyIRh2aoDzgvGxgtloCBCDiQMMa1cDh` | 9ace5cf8d2f01f0c1046da42e700b289 |
| `CUSTOM_HERO_parts_v9_board_bible.zip` (both scripts + both specs + page thumbnails; masters stay in parts v2 / v6) | `1udV7GE_2pgFZuob2GIvcmouBJ6uESPG1` | 19c40ec293eb4a0372493fa9e1e222b3 |
Local copies: `studio/characters/CUSTOM_HERO_MASTER_BOARD_v1.jpg` (1d1a3aeb…) · `studio/characters/CUSTOM_HERO_CHARACTER_BIBLE_v1.pdf` (9ace5cf8…). Current set unchanged: REAL face v5 (accepted) · REAL body v2 · STICK face v3 · STICK body v3 — the board and the bible are VIEWS of these, not new versions.

## Turn 33 (2026-10-10 16:04–16:20 UTC) — MOVED to "Monarch Face / MONARCH CHARACTERS" + stick-face direction
**User instruction:** "dono character ban gaye; ab sab kuch is Monarch Face folder mein — stickman ya realistic, character ka sab kuch — aur isi tarah Notion, Linear, Drive, Google Doc har jagah." Earlier the same day (turn 32): "stickman wale mein same human face na lagao, stickman face use karo."

**Drive (new home, user-created root folder "Monarch Face" `1EpH_0IcH34cJmf-s9DbaOQNBy3DXqPHw`)** — a parallel session had already created `MONARCH CHARACTERS` `1iPXavru1AXiSG5wRHuLKc5VNXhaVcXZK` (14:51–14:58 UTC) with Realistic / Stickman / Shared & Reference, moved 30 files, and created the HUB doc, Notion page, Linear project + MON-58/59. This turn completed it:
| folder | id | contents after turn 33 |
|---|---|---|
| Realistic | `1NpOJTSOY3zjkBR8LoktHDUFUSB8oW5jN` | REAL face v5 `1YTschdKJjpmsl4jIgC15y8yjek0zf1-M` (ACCEPTED) · REAL body v2 `177bFsA2oy--XSZOqbRycGieIbYJuX8S-` · Side face `1ZtYyXj7buyP52reUgtg3kgAfmF8pwR4N` · Snapchat `1czlTX5v0W4KeXIVKrLNqMLPyeYc13BHC` · **monarch voice.aac `1tOhhtG0-IJwswGwqDVJ6nDm7EeVUUDgi` (md5 13a1a9ed11787d692a836769448ca36b — user's voice sample, purpose not given yet)** |
| Stickman | `11uHSeU6wc81n9W_lRVvRU9arLQZTp3r8` | STICK face v3 `1Z434Pxr0aqsVHsrBF0AnMPTPxGREhyi3` · STICK body v3 `1xMSjERNvqBoZSlx81vRYB7PWCF50ygnb` · parts v8 `19Tb1b4mKbt5w0VkPbbEOgMgskugi79yo` · **stick-face hero v1 PREVIEW `1yMkEjUpi2ZDSM_KFx4HNfAYi_1UcVhX9` (md5 ae1e79ced1dd8810f12b4d6e3d0b7cb2)** · WF03_CHARSHEET_HERO_v2_stick3d.jpg `1OGLoFtS78QDNnNjw_cMyZ5DzGL0NgDnj` (md5 3851e12bad53f67c8efe59e8602eeab5) · WF-01 character_sheet_1–4 `1cZbP9gkLgLON7HVtJYhdkvisV-kk8A0v` `1jL7SSuCqwJHisX52hCVFCDCwOslmMwPw` `1GIa8gFbwg05Yy-IVa_Ls9IUAl44kkukM` `15VxS0iiTReW7Xqrm6R7Sm54TbY1bIeU1` · shade_character_sheet `1Elifxy3ZSxMuwe2myBImOoykG5sO7HgH` |
| Shared & Reference | `1dkk9Z3Js_wfSg2aIsTpmxlB9uNyD2OiJ` | this file `17fGVpLddAUe3XRYsmgAmxzfsBHAbtsfc` · BIBLE v1 `12lyIRh2aoDzgvGxgtloCBCDiQMMa1cDh` · BOARD v1 `1gNXdw63dMkbrc7vsiBAxbso1QuMYfcL9` · parts v9 `1udV7GE_2pgFZuob2GIvcmouBJ6uESPG1` · parts v7 `1fNLBTQ07WhKHoFZOUoShMh_ER5vuSQi-` · parts v2 `1SVnwhQKgLi1YR1F8cAiUo0tpKtNcOk3A` · profile_compare_v5 `1bpF8CQ4I49AEPab1k2w7CF7971_yD9B_` · sideface_check_v5 `10IV3H7qH6Yp-1uFHVg1TMlULa4UbfV_e` |
| Archive · old versions (NEW) | `1D-hvAls1B5QgoRs1fo54OpxdIR2JGwKt` | REAL v2 `1GYG37g_…` v3 `1Qn9j53m…` v4 `1o12IfxP…` v5_superseded_1202 `15okzY6o…` · REAL body v1 `1sBmrG4h…` · STICK v1 `1amd4MbX…` v2 `1VdlEZTz…` · STICK body v1 `1Qq0xWnL…` v2 `1XR8kzOf…` · parts v6 `1gvkDWcH…` · ANIM v2 `1z6D-Qxf…` v3 `1dUXfryB…` v4 `17Mbq-Va…` v5 `1k5xXFT6…` v5_superseded_1202 `13noXbwC…` · parts v3 `1xIlCh9u…` v4 `1dC1Dwec…` v5 `1qFBT8Cp…` v5_superseded_1202 `17w0RtyV…` · profile_compare_v4 `1NPM83k9…` (20 files; 3 duplicate pairs resolved by renaming the OLDER copy — nothing deleted) |
Old folder `1E-GX7wDCGBDqiUPtPwRPG_z9ucnVskBt` emptied → trashed. Shortcut in MONARCH STUDIO root: `1CXqpDM3Amj7q0dGhpFXCmvgcYrXHt6aX`. Raw turnaround video `1TelE6KTVEglV-Nj3cp_1LiiYAFkphkQ9` was trashed by the user (left in trash, not restored). "monarch overall workflow.zip" `1oTbPwpDttmfCwW3HHJsFay0B_EdQV3zM` (98.9 MB, user's workspace export) sits in Monarch Face root — not a character file.

**Mirrors:** Google Doc `MONARCH CHARACTERS — HUB` `1AsFnHq43aYYWORu1MAdrjsnDyPf-ftOg5HrY0Uj40BI` (rewritten; local copy `studio/characters/MONARCH_CHARACTERS_HUB.md`) · Notion page `3f5807e1-e916-816c-9624-f7bdc5dba4b2` under the studio hub (to-dos closed, folder bullets rewritten, CURRENT STATE callout + cross-links + open items) · Linear project `MONARCH CHARACTERS` `eb308dbc-c28d-46e5-ad5e-71ddb601a3b7` (MON-58 `850e3729…` Done · MON-59 `ff1ad1f7…` Done · **MON-60 `8b76458c-f063-445d-83e7-8ba86afc1404` stick-face rebuild v4 — In Progress** · MON-61 `550e5b32…` Done) · MON-55 comment `87db0b2c…` repointed.

**Stick-face direction (turn 32→33):** hero bust generated with refs = studio stick face (CHARSHEET_HERO_v2 head crop, padded 3:4) + REAL hero v5 crop; prompt = studio stickman face (bone-white smooth egg head, simple lidded eyes with brown irises, nub nose, thin sculpted mouth, NOT a realistic face) + his cues (big swept-back layered black hair to the collar, thick straight brows, longer straight nose, light jaw beard + moustache as matte dark clay, black shirt + charcoal blazer, white 5-finger glove on lapel). Local master `studio/characters/stickface/STICKFACE_hero_v1.png` (896×1200, md5 4f9c083a3fc545bf9e4004c3c7e5d3d8); refs in `studio/characters/stickface/refs/` (style_face_34, layout_grid3x2, layout_row3, layout_body4, REAL_hero_v5_crop). First attempt was lost because it was written under `build/` (not persisted) — **rule: generated parts go under `studio/characters/stickface/`**.
On approval → v4 plan (MON-60): round 2 parallel (bust turnaround · expr 01–06 · 07–12 · visemes 01–06 · 07–12 · eyes · head angles · 4-view body turnaround; refs = layout guide + hero bust) → round 3 (poses · action · walk · run · jump; refs = body turnaround + hero bust) → hands strip reused from parts v7 → `measure_proportions.py` → `compose_sheet_v3.py` → STICK face v4 + STICK body v4 → bible v2 + board v2 → upload + records. Open design question for the user: head tone bone-white (studio DNA, used in the preview) vs warm skin.

## Turn 34 — STICK FACE SHEET v4 delivered (face only; body v4 next turn)
User re-sent the identical message a 9th time → stick-face v1 treated as approved (stated default). `CUSTOM_HERO_STICK_SHEET_v4.png` 1520×8844 md5 5c18bd13e79fb7274a63a236487ef0d9 → Drive Stickman `1b2Wj1lUGtZpOI-26UuxneCi6fm7G3zKc` · parts v10 (hero + 10 strips + refs + spec + composer) `15XBFk4qevr1J9JiBfgJolzAXkejIuZzc` md5 6412ba080d089f7982eea5905507f99d. Strips: SF_turnaround · SF_expr01_06_v2 · SF_expr07_12 · SF_visemes01_06 · SF_visemes07_12 · SF_eyes (cell 2 = side glance, lids low — labelled as rendered) · SF_headangles · SF_hands · SF_body_turnaround (for the body sheet). Pending for body sheet v4: poses · action · walk · run · jump (image cap 10/turn) → measure_proportions → compose → bible v2 + board v2 → Drive pushes of this file / manifest / log.

## Turn 35 — STICK BODY SHEET v4 + CHARACTER BIBLE v2 + MASTER BOARD v2 (stick-face set COMPLETE)
Five body strips generated (poses · action · walk 6 · run 5 · jump 6; refs = v4 body turnaround + stick-face hero), `measure_proportions.py` patched (glove detection keeps only the first bright run — sneakers no longer merge into the glove blob) → front view 623 px = **3.18 heads** · head 196×176 · shoulders 0.71 heads · hands hang to 2.29 heads · crotch 2.09 heads · legs 1.09 heads · sneaker 37 px · side view within 1 px. Palette: head #958C7E (lit bone-white) · hair #2B2B2A · blazer #2B2B2A · shirt #171817 · trousers #0C0F0E · glove #D7D1CD · sneaker #CCC8C4 · backdrop #111717 · rim teal #3E827E · rim amber #9E6E46.
| file | Drive id | md5 |
|---|---|---|
| `CUSTOM_HERO_STICK_BODY_SHEET_v4.png` 1520×6644 (Stickman) | `1zoHaynrUsosrjwU45I7WZHfFUj2lt7uc` | c791940a822b52a7dbd00523db1ae0f7 |
| `CUSTOM_HERO_MASTER_BOARD_v2.png` 1080×1920 (Shared & Reference) | `1HkAE5dtx8mJqlpY6mPPIXjDAepYANrkQ` | 8977b5ee07e381894cffa4470b017759 |
| `CUSTOM_HERO_CHARACTER_BIBLE_v2.pdf` 16 pages (Shared & Reference) | `1j-zZhDepXYw28nhsYzpgOs6nmAKPJORf` | 24a5d5c3d1a1aa234d4420a34bf6b4ad |
| `CUSTOM_HERO_parts_v11_stickface_body.zip` (6 body strips + proportions panel/debug/JSON + specs body v4 / board v2 / bible v2 + 4 scripts + bible thumbs) | `1tzhP9PjUbRWWB3vXwgAuMIR_Cs7usVdr` | fc9efb6af3de085cd3ac4eb3f4fbb691 |
Bible v2 pages: 1 board v2 · 2 index · 3 REAL face v5 · 4–6 REAL body v2 · 7–12 STICK face v4 · 13–16 STICK body v4 (cuts only at gap rows, verified on thumbnails). Board v2 = REAL masters (parts v2/v6, re-downloaded + re-privatised) vs the v4 stick-face masters. **Current set: REAL face v5 (accepted) · REAL body v2 · STICK face v4 · STICK body v4** — v3 human-face stick sheets stay on Drive as history. Local JPG copies: `CUSTOM_HERO_STICK_SHEET_v4.jpg`, `CUSTOM_HERO_STICK_BODY_SHEET_v4.jpg`, `CUSTOM_HERO_MASTER_BOARD_v2.jpg`, `CUSTOM_HERO_CHARACTER_BIBLE_v2.pdf`; generated parts in `studio/characters/stickface/`.

## Turn 36 — LOCK (default) + registration everywhere
The identical message arrived a 12th time with no change note → per the default announced in turn 35 the set is treated as **LOCKED**: REAL face v5 (accepted) · REAL body v2 · STICK face v4 · STICK body v4 · bible v2 · board v2. Registration (records only, nothing regenerated): `MONARCH_STUDIO_REGISTRY.md` CHARACTERS section (Drive in place `1cGIALJxKtsn7iYVVQe33xLCIvyaIdzj8`) · root `RESUME_STATE.md` CHARACTERS block (Drive in place `109z7qydvLVNlHZmuO7neDwdRhhAETGEq`) · WF-03 `RESUME_STATE.md` custom-hero block (local; Drive `1V_C3PSoUKbSnVQIXThJIknlbEQkKH1j3`) · Notion studio hub callout + MONARCH CHARACTERS page callout · Linear MON-55 comment `87db0b2c…` + MON-57 comment + project MONARCH CHARACTERS · Google Doc registry `1ONXXVp…` + HUB doc change log. Reverting is one message: "change: ___".
How the locked character is used next: `NOIRGO <topic>` → film #3 may cast the CUSTOM HERO stick-face design (face sheet v4 + body sheet v4 are the design authority; the film renderer stays procedural `stick3d.py`, so the hero's hair / brows / beard / blazer / gloves / sneakers / 3.18-head proportions are ported into the rig as a `custom_hero` preset before the first shot).

## Open
- [user] What is `monarch voice.aac` for (VO reference / voice-clone target)?
- Next trigger: `NOIRGO <topic>` (film #3 with the custom hero) or `change: ___` (reopens the lock).
