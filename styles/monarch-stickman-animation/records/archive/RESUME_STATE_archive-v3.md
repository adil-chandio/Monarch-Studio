# RESUME STATE — restored from Google Drive `video edit workflow.zip`
_2026-10-08 · restored into `/home/user` (the paths every doc and script expect)_

## What was restored
| source | result |
|---|---|
| Drive `video edit workflow.zip` · 161,649,174 B · 99 files | downloaded byte-exact, `unzip -t` clean, extracted to `/home/user` |
| Drive `workspace-01a11973-….zip` · 327 MB | **different project** ("Powerful Personality" / TABAHI, JS renderer). Left untouched in `drive_dl/workspace_prev.zip` — not mixed into this workspace |

Both Drive files were made link-readable for a few seconds to get past the connector's 100 MiB cap, then set back to private (owner-only). Nothing on Drive was modified or moved.

## Integrity — measured, not assumed
| check | result |
|---|---|
| `stickman_money_37s_v7.mp4` sha256[:16] | `e7d8966ad6c0083c` ✅ matches VIDEO_V7_NOTES |
| `stickman_money_37s_v8.mp4` | `ff1fb7e612b48b61` ✅ matches VIDEO_V8_NOTES |
| `stickman_money_37s_v9.mp4` | `30a5f761d3f14ad6` ✅ matches VIDEO_V9_NOTES |
| `src/timeline.py` `stickbase.py` `stick2.py` `make_audio4.py` | ✅ all four sha256 match `BUILD_MANIFEST.json` |
| `python3 verify.py` | **37/37 PASS** (env, fonts, source, timeline oracle, drawing language, delivered file) |
| `python3 -m py_compile src/*.py` | all 23 modules compile |
| `src/wide_full.py 0 3 …` smoke render | frame 0 renders correctly (ACT 1 bar, "TWO HOURS IN", hunter) |

## Where the previous chat stopped
The last shipped work is the **16:9 long-form episode "The Slowest Predator"** (34 scenes, 5 acts, 263.5 s) — `VIDEO_EPISODE_NOTES.md` reports ALL GATES PASS on `stickman_wide_episode_full.mp4` (69,730,507 B, sha `48d5857e227b86e8`), plus ledger entries 32–38 in `MONARCH_SKILL_LONGFORM_16x9.md §9`.

## What the zip did NOT contain (gap found → being regenerated)
| missing deliverable | why it matters | action |
|---|---|---|
| `stickman_wide_episode_full.mp4` (1080p master) | only the 720p in-app preview was in the zip; the master is the upload file | **re-rendering now** via `build_all.sh` — exact recipe from VIDEO_EPISODE_NOTES §8 (2 shards → bed → concat → `src/mux_full.sh` → `src/gate_full.py`) |
| `stickman_wide_hook_53s.mp4` (53 s hook) | standalone hook deliverable from VIDEO_WIDE_NOTES | re-rendering after the episode (`src/mux_hook.sh` added — chain verbatim from VIDEO_WIDE_NOTES §6) |
| `build/` intermediates | never snapshot-persisted by design | recreated |

Render log: `build/build_all.log`. The pipeline is a pure function of `t`, so frames should be identical; the container sha may differ because the ffmpeg build here is v7.0.2 — the gate measures the delivered file either way.

## Known open items carried over from the docs
- `MONARCH_STICKMAN_MOTION_ENGINE_COMPLETE.pdf` was generated before the long-form work — it does not yet include `MONARCH_SKILL_LONGFORM_16x9.md`, `VIDEO_WIDE_NOTES.md`, `VIDEO_EPISODE_NOTES.md`, `SCRIPT_HOOK_PERSISTENCE.md`, `FULL_AUDIO_LEDGER.csv`, `WIDE_AUDIO_LEDGER.csv` (`src/makepdf.py` section list).
- MASTER_PROMPT_V4 §28 gaps (10 s reel source lost, TTS engine for `s1..s6` unrecorded, etc.) — unchanged.
- Env rules that still apply: `build/` and pip packages are not persisted; `pip install numpy pillow scipy imageio-ffmpeg reportlab` on a fresh box; never run an audio build while both shards are live (ledger 36).

---

## Update — same day, later

### Regeneration finished (`build_all.sh`, log `build/build_all.log`)
| deliverable | result |
|---|---|
| `stickman_wide_episode_full.mp4` | 69,729,447 B · sha `53a10e08f4c50b5e` · `src/gate_full.py` **ALL GATES PASS** (identical 0, Δluma 6.74, p10 .136, jerk 1.09, corr .761, side .368, peak −1.67, A/V 0.055, silence 0.28) |
| `stickman_wide_hook_53s.mp4` | 14,116,573 B · sha `5f030fcb7687eb68` · mux rc 0 |

The container shas differ from the notes (`48d5857e…`) because the ffmpeg build here is v7.0.2; the frames are a pure function of `t` and the gate measures the delivered file.

### New deliverable — 42 s "POWERFUL MAN" short
`stickman_power_42s.mp4` · 1260 frames · 15,882,763 B · sha `4c5a5c79c4408386` (rebuilt; first build `3af2f5fda7a99b2d`) · −11.7 LUFS · peak −1.49 dBFS · **ALL 18 GATES PASS** (`src/gate_power.py`).
Everything about it is in `VIDEO_POWER_NOTES.md`; ledger 39–45 appended to `MONARCH_SKILL_MOTION_EDIT.md §13`; `BUILD_MANIFEST_POWER.json`; `ASMR_POWER_LEDGER.csv`; `contact_power_42s.png`; one-shot rebuild `build_power.sh`.
Sources: `SCRIPT_POWER.md`, `src/timeline_power.py`, `src/vo_fit.py`, `src/power.py`, `src/make_asmr_power.py`, `src/mux_power.sh`, `src/gate_power.py`, `src/ameasure.py`, `src/sheet_power.py`, `assets/p1–p6.mp3` (raw TTS, voice `voice-00`), `assets/p1–p6_fit.wav` (what the mix uses).

Open: one human listen of the fitted VO (pause cap 0.30 s is measured, not auditioned). The MONARCH PDF still predates the long-form and power docs (`src/makepdf.py` section list).

### Permanent copies (Drive) — folder `stickman POWERFUL MAN 42s` (My Drive root)
| file | Drive id | check |
|---|---|---|
| `stickman_power_42s.mp4` (15,885,994 B) | `1uq_xNhjQTcwvAUiHR5fXCnsBrlcJLyCI` | md5 `1b61a2223d196af3c53f7af3269dd959` matches local |
| `power_short_package.zip` (sources, docs, raw + fitted VO, fonts) | `1AyvsSfSwGruAY5Ub0_vUPwi8Gm8Fa2pk` | 6,276,088 B |
Temporary mirror (72 h from 2026-10-08 16:57 UTC): https://litter.catbox.moe/wvlqbh.mp4 — catbox.moe permanent uploads are refused from this sandbox (HTTP 412 "Invalid uploader").

---

## Addendum — 2026-10-08 ≈ 17:40 UTC (documentation push)

**Resume key agreed with the user: "best video reel editing"** — when the user writes this name and asks to continue, resume from the state below. Full protocol: `MONARCH_STICKMAN_ANIMATION_SESSION_LOG.md` §0 (same file also in the Drive folder) and the Linear project body.

| record | where |
|---|---|
| Master session log | `/home/user/MONARCH_STICKMAN_ANIMATION_SESSION_LOG.md` (Drive copy: id `1le21NHN7NI6Y9NqsqZ5JMmB50SdAmPp9` in folder `1YSvMC-paJWQHVJEBpBZ0Mybp-WxshcPO`; this RESUME_STATE.md snapshot: Drive id `1poh0usjxECQ62ExP5i7pVy9RO7aVK8vG`) |
| Notion project | **Monarch Stickman Animation** `3f3807e1-e916-819e-aa60-fc633bf61478` → https://app.notion.com/p/Monarch-Stickman-Animation-3f3807e1e916819eaa60fc633bf61478 · Docs 00–08 ids: 00 `3f3807e1-e916-8152-9bff-c8caf4f08bb2` · 01 `…812c-8db0-d476c68c6c58` · 02 `…8174-b146-d1b53d9fbbf5` · 03 `…8145-b413-c1d30d68fcd4` · 04 `…81eb-9ccd-fdb74c4e94f0` · 05 `…8155-a8a5-fba6f57e61e5` · 06 `…8199-bb44-e92fd1fe3ac2` · 07 `…814d-9d5e-f96c5f6d5ee7` · 08 `…81c8-b655-c84ecea5ebd0` (prefix `3f3807e1-e916-`) |
| Linear project | **Monarch Stickman Animation** `4d053022-acab-4836-8f13-5ccb7e043c17` (team MON) · issues MON-34 (resume key) · MON-35 (prompt log) · MON-36…MON-42 (phases 1–5, rules, inventory; Done) · MON-43 A episode+hook regen (In Progress) · MON-44 B VO listen · MON-45 C PDF · MON-46 D trim · MON-47 E archive zip · MON-48 F next short |
| Episode + hook regen | `episode-hook-render-7cc910e1` started 17:27:45 UTC; at 17:38 shards at 2000/3953 + 2200/3952 (alive); ETA shards ≈ 17:49, mux ≈ 17:58, gate ≈ 18:01, hook ≈ 18:08 UTC. If `/home/user/stickman_wide_episode_full.mp4` + `stickman_wide_hook_53s.mp4` exist and are NOT yet on Drive → upload them first thing (same turn), record ids/md5 here, close MON-43, set Notion Doc 06 to Done. |

Open items unchanged: a (episode+hook upload) · b (VO listen) · c (PDF) · d (workspace trim ≈ 57 MB old shorts) · e (archive zip) · f (next video).

---

## Addendum — 2026-10-08 ≈ 18:15 UTC — NEW HERO "SHADE" (user's personal main character)

User attached a reference portrait (`uploads/436649626_1789475045520701.jpg`: hooded black suit, void face,
glowing slanted wedge eyes + crescent smirk, diagonal black/white split background) and asked to make it the
main character in 3D and rebuild the editing "next level". Decisions (ask_user): **remake the 42 s POWERFUL MAN
short with the same script + same VO · HYBRID look (paper/ink engine + diagonal split DNA) · character sheet
first, full video after approval.**

New files: `src/shade.py` (SHADE character on the toon.py 3D rig — own proportions SP swapped into toon.P during
the solve; garments: notch-lapel blazer, turtleneck, trousers, gloves, dress shoes, knit hood; glowing face with
bloom; lighting for black cloth: key rim / fill rim / form lift / AO / knit crackle / satin / gloss; EXPR table
with 15 expressions; poses p_pocket (reference stance, hand style 'pocket'), p_pocket_both, p_arms_cross),
`src/hybrid.py` (charcoal wedge over chrome + headline, diagonal drifts ±28/±22 px, accent seam with glow,
hot-word colours lightened until ≥ 4.8:1 on DARK — measured: 4.9/5.13/4.87/5.57/5.35/6.39),
`src/sheet_shade.py` → `shade_character_sheet.png` (turnaround, 8 poses, 8 expressions, Scene-1 frame),
`shade_scene1_preview.png` (1080×1920 Scene-1 mock in the hybrid look).
Status: WAITING FOR USER APPROVAL of the sheet. Next: `src/power2.py` = power.py scenes rebuilt with SHADE +
hybrid backdrop + enhanced beats (same timeline_power / VO / captions / mux_power.sh / gate_power.py), render,
gate, upload to Drive in the same turn.
Episode+hook regen (MON-43): attempt 3 died with a sandbox reset (confirmed 17:52 UTC) — still open.

---

## Addendum — 2026-10-08 ≈ 18:58 UTC — SHADE v2 DELIVERED

`shade_power_42s.mp4` (SHADE = user's personal main character on the 3D rig, hybrid paper/ink + diagonal split look,
same script / VO / cuts / mux as v1) — 1260 f · 42.000 s · 15,908,959 B · sha256[:16] `3a0de99bc85e1caa` ·
md5 `c9f8c2f4fedb36d80d16edbd60953c05` · **18/18 gates** (`build/gate_shade.log`; max_dluma 5.954).
Drive folder `1YSvMC-paJWQHVJEBpBZ0Mybp-WxshcPO`: mp4 `1rsJq7Y4wpQaKEsK7Zd7LNhiTqBYBUlJM` · sources
`shade_power_package.zip` `1dU8yV4zD5x9PQtEusk24Yb-vcJoDYD8C` · notes `VIDEO_SHADE_NOTES.md` `1JAwhlhBrLAr9Oy5J5w_AGeYiyH4HLBMn`.
Rebuild from a fresh sandbox: unzip the package over `/home/user`, `pip install numpy pillow scipy imageio-ffmpeg`,
restore `assets/p*_fit.wav` from `power_short_package.zip` (`1AyvsSfSwGruAY5Ub0_vUPwi8Gm8Fa2pk`), `mkdir -p build`,
`bash build_shade.sh`. Build 1 failed max_dluma on the swipe crossing SHADE → fixed by dissolve-under-wipe +
two-tone stripes (log §12). Open items a–f unchanged; next short = same recipe with a new script.
Records: Notion Doc 09 `3f3807e1-e916-8175-9d4f-fb33a2179ad8` · Linear MON-49 (Done) · Drive current log
`1xZG7dSfpaEZLjGkAUiyurnnWc9EDu-GY` · current RESUME_STATE `13koWDtxJBWt8CYhSfz090f0nWIkaG16a`.

## 2026-10-08 21:2x UTC — RESPECT short DELIVERED (turn 8)
- `shade_respect_90s.mp4` — 2700 f / 90.000 s / 33,808,670 B / sha256[:16] `f3d0f1a21ec59b00` / md5 `839b95bbf35d96bf4fa26eb811f680e1` — 18/18 gates (build 4).
- Topic "Log aapki izzat kyun nahi karte" (5 rules), SHADE hero, hybrid split, cinematic layer (dolly/parallax/DOF/shafts/dust/slow-mo), voice-01.
- Sources: `SCRIPT_RESPECT.md`, `src/respect.py`, `src/timeline_respect.py`, `src/make_asmr_respect.py`, `src/mux_respect.sh`, `src/gate_respect.py`, `build_respect.sh`, `VIDEO_RESPECT_NOTES.md` (BUILD_RESULT), `shade_respect_contact.png`, `shade_respect_package.zip`.
- Records: Linear MON-50; Notion Doc 10 `3f3807e1-e916-8190-b4a6-f9c708d50b25`; session log §13. Drive folder "stickman IZZAT 90s" (ids in log §13 FINAL block).
- Ledger now 1–56. Open items unchanged: a (MON-43 episode+hook regen), b (VO listen), c (PDF), e (archive zip).
- Drive "stickman IZZAT 90s" `1_MhRILyCB86LWHYqLDzBPvmneA6Y2uqo`: mp4 `1FtRyxIvEnBldm6_DGnGPWHcvNRPznzAQ` · zip `1zYeJ_rECNjBDFx1cuBwI2PtKZj9TaBzE` · notes `1VhY__mCYoDjwzEyX_M9vta-OeqjIEp_q` · sheet `1MLEJaTwYHrgf7HSFfLxkRyEog4sZY394` · log `1TJdyElMWt5aPV8KGbXuQ1cyKwpITCWVs` · script `1oGFQVhTTx8rI1KTbK7ticUyw8XvmcHJ9` · RESUME_STATE (this file, uploaded last).
- Workspace trim (snapshot cap): removed local scratch (_body_a/_probe/_ref_*/_shade_test*/_zoom) and the already-on-Drive `power_short_package.zip` (Drive `1AyvsSfSwGruAY5Ub0_vUPwi8Gm8Fa2pk`) + regenerable `contact_power_42s.png`; `drive_dl/` restore scratch removed.


## Turn 9 — 2026-10-08 21:23–22:00Z — MON-43 episode/hook regen · MON-45 PDF v4.0 · MON-47 archive v2

**MON-43 DONE** — `stickman_wide_episode_full.mp4` 69,729,482 B / 7905 f / 263.50 s / sha `e2bbc8edddcfcbf5` / md5 `8aec7360cbc1849b5f8cafe2c18e7e7b` → Drive `1MbClU5EuAeWEA-zaS8nNhxPIkBUZxtdW`; `stickman_wide_hook_53s.mp4` 14,115,662 B / 1590 f / 53.00 s / sha `f2ec3a02d69dee0a` / md5 `288134f14c09579577d67a4223071693` → Drive `1qbCkv36OknO0S-2TFXUSkTLIepjpTn8o` (both folder `1YSvMC-paJWQHVJEBpBZ0Mybp-WxshcPO`, md5 verified). gate_full ALL PASS (Δluma 6.765 · p10 .1349 · jerk 1.066 · corr .7607 · side .369 · peak −1.67 · A/V .055 · silence .22). Episode master moved to `build/` (not persisted) after upload — cap rule.

**MON-45** — `src/makepdf.py` → v4.0 (cover meta rows for episode/POWER/SHADE/IZZAT; new Parts VIII LONG-FORM 16:9, IX THE SHADE-ERA SHORTS, X SOURCE CODE II (28 files), XI VISUAL REFERENCE II (plates 10–13), XII DATA APPENDIX II (POWER + IZZAT ledgers, POWER manifest, session log, this file); header v4.0; `build/pdfimg/*.jpg` downscaled twins ≤1800 px). `_probe.png` / `_zoom.png` restored from the original Drive zip (make_public → curl drive.usercontent.google.com … confirm=t&uuid → make_private). Ledger 46–56 appended to `MONARCH_SKILL_MOTION_EDIT.md` §14/§15 and to Notion Doc 07.

**MON-48** recipe rewritten (A POWER / B SHADE-cinematic).

(PDF + archive ids are appended below once uploaded.)

**MON-45 DONE** — `MONARCH_STICKMAN_MOTION_ENGINE_COMPLETE.pdf` v4.0 · 403 pages · 5,286,439 B · md5 `3c7da60fc00dae9efd7677facfdfd82e` → Drive `1c_CSbdenDdPl1WEwpXCAR0gnUGq2HXK9` (folder `1YSvMC-paJWQHVJEBpBZ0Mybp-WxshcPO`, md5 verified). Regenerate any time with `python3 src/makepdf.py` (needs `build/pdfimg/*.jpg` twins — recreate with PIL ≤1800 px q82 if `build/` is gone, otherwise the full-size PNGs are embedded and the file grows).

**MON-47 DONE** — `video_edit_workflow_v2.zip` · 163 files · 83,667,238 B · md5 `2782af79b6cfc9390990070b7ec98962` → Drive `10wfkO0Hkc9yfJcEO754sg_rEaiY0a0Js` (folder `1YSvMC-paJWQHVJEBpBZ0Mybp-WxshcPO`, md5 verified). Contents: everything persisted (src/, build scripts, docs, ledgers, plates, assets, PDF v4.0, log, this file, `DRIVE_MANIFEST.md`) + `stickman_wide_hook_53s.mp4` + `stickman_money_37s_v9.mp4` + 720p preview; excluded masters (episode 70 MB, IZZAT 34 MB, SHADE v2 16 MB, POWER v1 16 MB) are listed in `DRIVE_MANIFEST.md` with ids + md5. Original `video edit workflow.zip` `1labbEjdk4GO6zgth4Ce_JhP4WDpjZOEM` untouched (made public for 20 s to curl it, then private again). Local zip + local hook copy removed after the md5 check (cap); workspace ≈ 120 MB.

### OPEN after turn 9
- **MON-44** — human listen pass of the fitted VO (POWER / SHADE v2 share the same voice-00 track; IZZAT voice-01) — only the user can do it; files: Drive `1uq_xNhjQTcwvAUiHR5fXCnsBrlcJLyCI` / `1rsJq7Y4wpQaKEsK7Zd7LNhiTqBYBUlJM` / `1FtRyxIvEnBldm6_DGnGPWHcvNRPznzAQ`.
- **MON-48** — next short: follow recipe B (SHADE-cinematic) in the issue description.
- Ledger candidate 57 (caption widths ≤ CAP_MAX_W at the floor size) — written into recipe B step 1; add to the skill doc with the next build.


## Turn 10 — 2026-10-09 11:3x–13:4x Z — IZZAT v2 (flow · density · SFX · transitions)

**DONE — `shade_respect_v2.mp4`** 75.19 s / 2256 f · 28,432,377 B · md5 `8d91be52ab969e0b23f21bf6bab0df85` → Drive `1fu_g2HTNZVRqE3XBKdUKZoj6O8tIdkpu` (folder "stickman IZZAT 90s" `1_MhRILyCB86LWHYqLDzBPvmneA6Y2uqo`, md5 verified). Gate `src/gate_respect2.py` 19/19 (details: `VIDEO_RESPECT_NOTES.md` BUILD_RESULT_V2, log §15).
- Timeline `src/timeline_respect2.py` (VO_AT 0.600 · 7.538 · 15.814 · 20.558 · 29.488 · 37.496 · 45.424 · 53.564 · 61.872; adelay ms = ×1000) · shots/transitions `src/respect2.py` (33 shots, `PLAN` 32 kinds, `TD`, `e_q`) · bed `src/make_asmr_respect2.py` → `ASMR_RESPECT2_LEDGER.csv` · mux `src/mux_respect2.sh` (LM250 −5.4, LM160 −1.5, rest = v1 chain) · gate `src/gate_respect2.py` (jerk on shot frames + `trans_jerk_max < 8`).
- Rebuild from zero: `bash build_respect2.sh` (shards 0+1, ≈21 min sequential) → `bash finish_respect2.sh` (bed → mux → gate). `build_respect2_b.sh` was the card-fix second half of this turn's build (shard 1 + filter concat); `src/patch_windows.py KINDS [a:z]` re-renders only the transition windows of the given kinds and `src/splice_windows.py KINDS [a:z]` splices them (streaming) — use these for transition tweaks instead of a full re-render.
- Local tree: v2 mp4 + `shade_respect_v2_contact.png` kept; v1 `shade_respect_90s.mp4` moved to `build/` (Drive `1FtRyxIvEnBldm6_DGnGPWHcvNRPznzAQ`, md5 `839b95bbf35d96bf4fa26eb811f680e1`). Workspace ≈119 MB.
- Ledger 57–61 in `MONARCH_SKILL_MOTION_EDIT.md` §15 (61 = gate recalibration + hidden mud + `place_st` t<0).
- Sandbox lesson: never hold a float32 full-film probe array (520 MB) in RAM next to an ffmpeg pair — the box hung 25 min; uint8 + per-window.


**Turn-10 ids:** Drive mp4 `1fu_g2HTNZVRqE3XBKdUKZoj6O8tIdkpu` · contact `1SG--FCZ1r71jKvo0PgA7W2aI4tEVaBar` · notes `14INr04m-LbotIa6gfliNU8TAHiLhsUBx` · RESUME_STATE `1wUVVqtovI8i98eatPpz4AxMdkz3QxO4j` · Linear **MON-52** `11c0f33d-341b-4ae0-94d2-af4de32b2722` (Done) + MON-44 comment `b9ce407c` · Notion Doc 10 / 07 / 08 appended 13:38–13:39 Z.

### OPEN after turn 10
- **MON-44** — user listen pass (now also `shade_respect_v2.mp4`).
- **MON-48** — next short: recipe B + the v2 additions (cut to the voice, 15-kind transition library + plan, no noise floor, `trans_jerk_max`).
- Optional polish candidates (not flaws, all gates pass): the two-hero overlap inside the wedge wipes (same hero x in A and B) could use an offset hero in the incoming shot; PDF v4.1 to add the v2 section + ledger 57–61.
