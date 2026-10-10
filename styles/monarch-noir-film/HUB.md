# WF-03 · Monarch Noir Film — HUB (local template; copied into workflows/wf03_monarch_noir_film/ by studio/new_workflow.py)

## Identity
- Workflow code: WF-03 · Name: Monarch Noir Film · Resume key: "NOIRGO <topic>" · Status: ACTIVE (film #1 THE SHADOW v1 delivered 2026-10-10 · film #2 THE WINDOW v1 delivered 2026-10-10, NOIRGO MAX engine) · Created: 2026-10-09
- Style / engine: Dark cinematic animated short film, 1920x1080 24 fps, 120-180 s, own DNA per film, measured gates. Film #1 engine (noir.py): black world, bone-white line hero, amber light + one red villain colour, cast-shadow physics, text narration + 2-3 voice lines. Film #2 engine (NOIRGO MAX, current): real-life illustrated plates + crop camera (world.py, film_window.py), 3-D stick-human hero (stick3d.py), full English VO + SFX voices + score (audio_window.py), 27 gates (gate_window.py)
- Local root: workflows/wf03_monarch_noir_film/  (sources, build/, RESUME_STATE.md, HUB.md, CHECKLIST.md)

## The same workflow on the other platforms  (fill all four — the round-trip test fails until they are filled)
- Notion hub page: https://app.notion.com/p/WF-03-Monarch-Noir-Film-3f4807e1e9168135b919ee36b0e39165  (page id 3f4807e1-e916-8135-b919-ee36b0e39165, child of MONARCH STUDIO hub 3f4807e1-e916-813a-9000-e7e94ac0ac53) · Workflows DB row 3f4807e1-e916-810e-a035-fce9f7cc8f3f (authority)
- Linear project: WF-03 · Monarch Noir Film e173192b-b932-4801-ac4d-dcd7445237b8 (team MON 7d25e78c-c0f2-46b3-9c73-10bcf9c5a108) → resume issue: MON-57 bbb25ad6-7fcf-4901-bcee-9c3972d8a311 https://linear.app/monarchmation/issue/MON-57/00-resume-key-noirgo-wf-03-monarch-noir-film-state-links
- Google Drive folder (inside MONARCH STUDIO 1-wAt4bgYVn7q15uq22ZnRY8z5iIQaI-l): https://drive.google.com/drive/folders/11c194r1f_IMIo5yOmT-j80Iu-sZWP3KP  (id 11c194r1f_IMIo5yOmT-j80Iu-sZWP3KP)
- Google Doc HUB: https://docs.google.com/document/d/1sGGzPHXXars1-pJvB3ugnbnLuSuQ5EpE-obVidTj6rM  (id 1sGGzPHXXars1-pJvB3ugnbnLuSuQ5EpE-obVidTj6rM)
- Registry: Notion hub 3f4807e1-e916-813a-9000-e7e94ac0ac53 · Linear MON-55 · Drive MONARCH STUDIO · Google Doc 1ONXXVp-yYG2P9ldUPBOSAhr8oWkS79qgzdu6eGHTm8Q · local MONARCH_STUDIO_REGISTRY.md

## Resume order (key "NOIRGO <topic>")
1. Registry row (any platform) → confirm WF-03 by id.
2. Linear project body §0 → resume issue newest STATE comment.
3. Notion hub top callouts → Doc 00.
4. Drive RESUME_STATE.md (newest block on top) → session log.
5. Restore local sources from the workflow's Drive archive; rebuild deps; continue from "Open items".

## Current state
- **Status ACTIVE — 2 films delivered.** Film #1 THE SHADOW v1 (Drive `16qsEno9sN_p4fggfcTN05W9LUzYsz0u4`, 27/27). Film #2 **THE WINDOW v1** (NOIRGO MAX: real-life plates, 3-D stick-human hero v2, full English VO voice-03) delivered 2026-10-10 — Drive `1WaMfEroWgzuYHeSCpyU9CPY7gJ0a0iGy` md5 `cfe189f9c09e47e6728d2f2aba017f8d`, 155 s, 27/27 gates (`1K6k-6yS1hXOGy4D8v7mhI71w0xIDikCh`), brain `the_window_v1`. Next `NOIRGO <topic>` = film #3.
- Authority for the exact next step: `RESUME_STATE.md` in this folder (Drive `1V_C3PSoUKbSnVQIXThJIknlbEQkKH1j3`).

## Film #1 — THE SHADOW (brain pick: topic FEAR, ~150 s, 120–180 window)
- Why FEAR: universal, not on Day One's list (discipline, dopamine, motivation, roots, overthinking, ready, one last time, old book) nor ours (power, izzat); it is native to a dark world (light/shadow) and gives a physical, measurable spine device.
- Hero (brain pick for this film): the bone-white two-tone line figure — the villain is his own shadow, so the hero must be the lit one. SHADE stays WF-01. Design differs from Day One's chibi: ~7.5-head proportions on the 3-D skeleton, lit/dark halves, eyes-only face, scarf.
- Spine device: his cast shadow on the back wall = homothety about the lamp, k = (1 − z_lamp)/(z_hero − z_lamp), feet anchored on the wall/floor junction; readout `SHADOW n m` (1.8 m · k). Walking toward the wall shrinks it; at the wall k = 1 → exactly his size.
- Beats: 01 Every night, it was there (k 2.2, readout 8.0 m) · 02 The corner + red typewriter villain lines "stay. / not yet. / what if." · 03 Lights out (ember only) · 04 One step (back view) · 05 The walk (shaft + dust, 2.6 m) · 06 The wall — "When he touched the wall, the shadow was exactly his size." (1.9 m) · 07 End card "WALK TOWARD IT." · quiet.
- Quotable: "Fear is a shadow. Walk toward it — and it is exactly your size." · callbacks: lantern, readout, red lines (answered in white), the corner.
- Narration: on-screen serif text + 2–3 English voice lines (opening whisper, one mid line, "Walk toward it."). Voice audition = the only user click.
- Palette: BLACK 7·7·9 · WALL 14·14·15 · BONE 236·232·222 · SLATE 96·102·112 · AMBER 255·214·170 (warm-grey lamp light) · RED 214·38·32. Type: KaTeX Main (Computer Modern) narration, KaTeX Typewriter villain, Montserrat readout.

## Look-sheet v0 metrics (measure(): luma mean, chroma = mean(max−min), dark = share luma<30, p99, k)
| shot | luma | chroma | dark | p99 | k |
|---|---|---|---|---|---|
| 01 · Every night, it was the same | 28.5 | 7.6 | 0.731 | 188.6 | 2.2 |
| 02 · The corner (villain text) | 30.9 | 8.8 | 0.683 | 194.7 | 2.2 |
| 03 · Lights out (rock bottom) | 10.8 | 4.2 | 0.968 | 192.8 | 2.2 |
| 04 · One step (back view) | 31.1 | 8.2 | 0.705 | 191.6 | 2.2 |
| 05 · The walk (shaft + dust) | 31.7 | 9.0 | 0.637 | 176.3 | 1.46 |
| 06 · The wall (payoff) | 29.8 | 8.5 | 0.7 | 171.1 | 1.06 |
| 07 · End card | 1.9 | 1.7 | 0.994 | 5.0 | None |
Reference by the same measure on Day One keyframe sheets: luma 30–48, chroma 2–10, dark 0.39–0.51 (full-film video mean 18/255, 89 % dark incl. dips). Setup-frame targets for the film: luma 14–30, chroma ≤ 10, dark ≥ 0.6.

## Film #2 — THE WINDOW (NOIRGO MAX · brain pick: topic COMPARISON · 155 s · delivered 2026-10-10, turn 21)
- Device: the opposite facade = the villain's body (31 lit windows, measured rects); his own window blue → dark → amber; the phone dies → his reflection laid over the 31 windows; four red lines on the glass answered in white; DAY 1 / 9 / 23 / 40; dawn Picardy; two end cards (LIGHT YOUR OWN WINDOW · "You only ever see the lit room.").
- World: 10 illustrated real-life plates (facade, bedroom night/amber, runner/kitchen/desk windows, window inside, kitchenette, street dawn) · crop camera with `cam_lerp` moves · rain, dust, window gain/flicker · hero = `stick3d.py` 3-D stick-human (face, five-finger hands, blinks, gaze, IK).
- Sound: 10 VO clips (voice-03, 123.6 s), 30 SFX voices (0.87 new), felt-bell score D minor → D major at 121.3 s, 72 BPM; −16.5 LUFS, TP −3.5, LRA 6.2; bed arc hook −42 → climax −22 → tail −43 LUFS-S.
- Deliverables (Drive WF-03 folder): mp4 `1WaMfEroWgzuYHeSCpyU9CPY7gJ0a0iGy` · gates `1K6k-6yS1hXOGy4D8v7mhI71w0xIDikCh` · src v3 `16nQBnsv-fU5BmYcq7rKB8mjXIEyTPZyf` · data `1CCVbCmafbtsfZ-pZ7WKbz5WW571sIC7N` · plates zip `1TDuXbFMADWv3L_NBwkmjfDSObaITJb2_` + kitchenette `11wzRhUh0Nb5l-FmDacxaxBOl5B11wLex` · VO zip `11DTehQ6PZdJSt485q-jqyDo944DXN8DR` · char sheet v2 `14jZEeiw0-nQGejJMFsBrHkN-n6gR3a0A` · motion test `1IHM788_tWoLlOl_LwnbQexvuWRtTFz-R` · look sheet v2 `1DzH0K2Bq1Q4402AKffsfMwIMoLB4mVw2` · script `1nHI13fdLk79ZHUbkSNO3j-nezu3u2eSF`.
- Measured: luma 26.9/255 · dark 68.1 % · chroma 12.2 · 45 shots (38 hard cuts, 5 dips, 1 continuous take) · 14 holds 4–7 s · 162 beats (max gap 4.7 s) · brain gate 18/18.

## Open items
- [x] Hero v2 approved → GO (turn 21).
- [x] film_window.py (45 shots), look sheet v2, audio_window.py, gate_window.py 27/27, Drive md5, brain commit `the_window_v1` — delivered 2026-10-10 (turn 21).
- [ ] Film #3 on the next `NOIRGO <topic>` (brain picks a topic outside FEAR/COMPARISON and the Day One list).
- [ ] Custom-character option: stick3d MATS/HP are parametric — a user-supplied character = new palette + proportions + hair preset (document when first requested).

## Rules carried from MONARCH STUDIO
Measured not eyeballed · deliverables on Drive with md5 in the same turn · everything recorded (RESUME_STATE.md, log,
Notion, Linear, Google Doc HUB) · concise Roman Urdu replies with ids · never mix another workflow's files or facts
into this one · each new edit different from the last.
