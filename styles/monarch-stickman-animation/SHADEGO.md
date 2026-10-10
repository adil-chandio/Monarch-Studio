# SHADEGO — one-word autopilot trigger for WF-01 · Monarch Stickman Animation
MONARCH STUDIO · workflow WF-01 · legacy resume key "best video reel editing" · owner: Ali · created 2026-10-09 (turn 15b).
Identical copies: Google Doc "SHADEGO" 1EdP_cvptM1GG8dDg_6ld_yjnkc1Ko9-kHtXy3BYXc2A (authority) · Drive WF-01 folder 1Qum7OkUZpRMSt3SMJ6q3WumUUwzezTw- → SHADEGO.md · Notion page "SHADEGO" 3f4807e1-e916-81f2-b9f0-d2d75b384983 (child of the WF-01 project page) · Linear issue MON-56 "SHADEGO" https://linear.app/monarchmation/issue/MON-56 (f550f107-2949-4f72-b9d3-1c08a5813060) · local /home/user/SHADEGO.md.

## 0. What the word means
A message that contains the token SHADEGO (any case) followed by a topic is a complete order. It means: resume WF-01 from the four platforms, restore the toolchain, run the EDITOR BRAIN ritual on FULL AUTOPILOT, build the video to the measured 20-gate bar, upload to Drive with md5, write every record, and reply in Roman Urdu with a proof block. The user chose full autopilot on 2026-10-09: the agent decides format, duration, concept, script, plates, sound and transitions itself and states the reasons. There are exactly two allowed questions: (a) the topic, only if the message has none; (b) the voice audition click, which the speech tool requires. Preferences written in the trigger message override the defaults below.

Message grammar: `SHADEGO <topic>` optionally followed by `| short|film | <n> s | voice: <note> | <special ask> | language: <lang>`.
Examples: `SHADEGO discipline` · `SHADEGO how to stay calm when insulted | film | 150 s` · `SHADEGO fear of failure | short | 60 s | language: Urdu`.

## 1. Resolution rule
Only WF-01. The phrase "Monarch Stickman Animation" also appears in WF-02 (the LEGACY "Powerful Personality" explainer, key "TABAHI ACTIVATE", Linear a813926c-b2ef-4956-91dd-09e91f08b7d9, Notion 3f2807e1-e916-81b2-a334-d34ea75cc5ea). WF-02 files and facts are never used for WF-01. Resolve by WF code + id, never by name.
Registry (any platform): Notion hub 3f4807e1-e916-813a-9000-e7e94ac0ac53 (Workflows DB 8e8f1c1c-30c9-4b15-badd-cff77d64a80b, row WF-01 3f4807e1-e916-8140-aee5-e1f13ab5b6d7) · Linear project 0a01b89d-3c9d-4193-8416-76b32d76cfca + MON-55 · Drive folder MONARCH STUDIO 1-wAt4bgYVn7q15uq22ZnRY8z5iIQaI-l · Google Doc 1ONXXVp-yYG2P9ldUPBOSAhr8oWkS79qgzdu6eGHTm8Q.

## 2. Step A — RESUME (read in this order; load each connector with list_connector_tools first, every turn)
1. Linear project WF-01 4d053022-acab-4836-8f13-5ccb7e043c17 body §0 → MON-34 (f8bd0a44-3d9b-4e20-8387-363aca59eaa9, https://linear.app/monarchmation/issue/MON-34) newest STATE comments (they carry the newest Drive ids).
2. Notion WF-01 page 3f3807e1-e916-819e-aa60-fc633bf61478 → Doc 00 3f3807e1-e916-8152-9bff-c8caf4f08bb2 top callouts (Docs 00–12 = production record; Doc 11 = EDITOR BRAIN, Doc 12 = reference study; Docs DB 3f2807e1-e916-8001-a73c-e29f5cbba8f6).
3. Drive WF-01 folder 1Qum7OkUZpRMSt3SMJ6q3WumUUwzezTw-: RESUME_STATE.md (newest block on top; at writing 1VwjEJtgOU_FcdD5nYJU0RbMSNm1xEfl3) + MONARCH_STICKMAN_ANIMATION_SESSION_LOG.md (at writing 1pstBLsRF__bKDOD4QbjCCGoWsp48HLgH; read §0, §18–§21) + DRIVE_MANIFEST rows in the log.
4. Google Doc HUB 1g2WLpd-S9LmBur4nbz9mHc4AkOCCl54ZUpHNAzHuW5g → "Current state".
Confirm before building: last delivered video (IZZAT v2, 75.19 s, 19/19 gates, Drive 1fu_g2HTNZVRqE3XBKdUKZoj6O8tIdkpu), brain registry = 6 videos, skill ledger 1–68, open items (MON-44 listen pass, MON-48 next video), which record ids are newest. If a newer RESUME_STATE block exists than this document describes, the newer block wins.

## 3. Step B — RESTORE the toolchain (a new chat's sandbox is empty)
- `pip install numpy pillow scipy imageio-ffmpeg reportlab pymupdf` (yt-dlp optional). ffmpeg only through `imageio_ffmpeg.get_ffmpeg_exe()`. `mkdir -p build`.
- Download with google_drive download_file (return_download_url=true → curl; if that is unavailable: make_public → curl → make_private):
  archive v3 13xhEW-e3l1gS8oiCVum_41TQcsbg3bgb (src/, assets/, character sheets, gate scripts, SCRIPT_*.md, notes) → unzip at /home/user;
  brain v2 zip 1aqCFhUAavp3EOXmSNzL68cALoT1SgJX9 (brain/, MONARCH_EDITOR_BRAIN.md, references) → unzip at /home/user;
  IZZAT v2 package 16dY7R5PpdwbOZnA4nMeFJPT1QJjoQB2M only if the respect2 sources are missing from archive v3.
- Verify: `python3 brain/concept.py status` runs and shows 6 videos; `src/gate_respect2.py`, `src/timeline_respect2.py`, `src/respect2.py`, `src/vo_fit.py`, `src/make_asmr_respect2.py`, `src/mux_respect2.sh`, `shade_respect_v2_contact.png`, `CHARACTER_SPEC.md`, `MONARCH_SKILL_MOTION_EDIT.md` (ledger 1–68) exist.
- Machine: 2 vCPU, 2 GB RAM, ~128 MB persisted snapshot (build/ never persists). Render in sequential shards with start_process; big outputs go to Drive in the same turn and are deleted locally after the md5 check.

## 4. Step C — ACTIVATE (before any build)
- Status Parked → Active on: Notion Workflows row 3f4807e1-e916-8140-aee5-e1f13ab5b6d7 (Status) · Linear registry MON-55 (comment) · Google Doc registry 1ONXXVp… WF-01 row (replace "PARKED" text) · WF-01 Linear project §0 first line · Notion Doc 00 new top callout "ACTIVE — SHADEGO <topic> <date>" · MON-34 STATE comment "SHADEGO start: <topic>".
- First reply to the user (Roman Urdu, ≤8 lines): state confirmed, chosen format + duration + concept headline with the one-line reason, ETA. Then continue without waiting for an answer.

## 5. Step D — DECIDE (full autopilot; the brain decides, the agent documents why)
- Format + duration: run `python3 brain/concept.py propose --topic "<topic>" --dur <d> --n 3 --format short` and `--format film`. Short = 1080×1920, 40–90 s, −11.6 LUFS, something new on screen every 2–3 s. Film = 1920×1080, 120–300 s, −16.5 ±1 LUFS, holds 7–14 s, ≥3 callbacks, 2 quotable lines, no CTA. Rule: a single punchy claim or lesson → short 45–75 s; an arc with a before/after, a story or a character journey → film 120–180 s. State the reason in one line. A format or duration written in the trigger message overrides this.
- Concept: pick the proposal with the highest composite of novelty (vs the registered videos: hook/device window 3, grammar/camera/sonic/type/ending window 2, transitions overlap ≤.40 with ≥3 new kinds, SFX ≥50 % new), hook strength, and feasibility in the Python renderer (respect2 family). Never reuse the last video's hook device, opening shot, ending, or transition set. Keep the other two proposals in the notes as "not chosen, why".
- Script: written by the agent for the chosen duration (short ≈2.4 words/s with breathing room; film = sparse lines, long holds, 2 quotable lines). Language = the language of the last delivered script (SCRIPT_*.md in the archive) unless the trigger says otherwise. Natural pauses only — no long inter-chapter gaps. Every spoken line maps to a visual beat; every 2–3 s something new (short).
- Hero: SHADE — hooded black suit, 3D rig, hybrid paper/ink look; identity LOCKED (approved 2026-10-09), no approval round. New per-video poses, plates and metaphors are required (CHARACTER_SPEC.md; rim/fill on black cloth; no mitten hands; closer shots are inserts, never a scaled scene layer). The contact sheet is delivered with the final, not before.
- Voice: the only click. add_voice (masculine, narration, language of the script) with a 40-word line from the new script; the user picks one of the two. Then generate all VO lines (≤10 clips per turn, ≤1500 chars each; chunk long scripts), fit with src/vo_fit.py, de-ess + LIM .71 / XS 1.7 for a new voice. Voice ids never carry across chats.
- Sound: varied premium SFX (never the same SFX twice in a row, ≥50 % new vs registry), ASMR bed per src/make_asmr_respect2.py, no continuous radio/static texture, pad the VO bus before the sidechain so the mix never breathes, voice centred / bed wide.
- Transitions: every one different, 3D/cinematic, luma-traced, ending on the beat, tint-not-flood, soft edge ≥100 px + TD .64 over figure-dense B shots, quintic easing, iris r ∝ √e, horizontal pushes only (vertical failed Δluma).
- Picture: nothing perfectly still; parallax, push, depth, light rays, particles, slow-mo where the concept calls for them; low density; safe area y 180–1500 (short); captions ≤936 px wide; contrast ≥4.5:1; premium = subtraction; extruded type, chrome, v9 grammar.

## 6. Step E — BUILD (measured, sequential, resumable)
1. New `src/timeline_<slug>.py` + `src/<slug>.py` from the respect2 pattern; `python3 brain/concept.py cadence --module <module>`; render shards with start_process and get_process_output wait_for (never edit a running script; never `pkill -f` a pattern that matches the tool shell).
2. VO + SFX + bed → mux (src/mux_respect2.sh pattern) → loudness to the format target.
3. Gates: `src/gate_<slug>.py` = the 19 checks of src/gate_respect2.py (bands 'all' is authoritative) + `python3 brain/concept.py gate` (#20). All 20 PASS with numbers. A failure is fixed and re-run; thresholds are never relaxed; a failing build is never delivered.
4. Also produced: 12-frame contact sheet PNG, VIDEO_<SLUG>_NOTES.md (concept, why, rejected proposals, numbers), package zip (sources + notes + gate report).
5. `python3 brain/concept.py commit` only after all gates pass (it writes brain/registry.json; the file is never hand-edited); `python3 brain/concept.py export`.

## 7. Step F — DELIVER + RECORD (same turn as the final render)
- Drive WF-01 folder 1Qum7OkUZpRMSt3SMJ6q3WumUUwzezTw- → new sub-folder "stickman <TOPIC> <dur>s": master mp4, contact sheet, notes, gate report, package zip, new brain zip (monarch_editor_brain_v3.zip, then v4 …, containing brain/ + doctrine). md5 of every upload compared with the local file; a mismatch is re-uploaded.
- Local, then uploaded to the same folder: RESUME_STATE.md (new top block: what, ids, md5, gates, open items), session log (new §: narrative + lessons), DRIVE_MANIFEST rows, MONARCH_SKILL_MOTION_EDIT.md ledger 69+ for every new lesson. The new file ids go into the MON-34 STATE comment.
- Linear: MON-48 → Done (or a new issue "VIDEO n · <topic>" in project 4d053022… with attachments: master, package, Notion doc); MON-34 STATE comment (ids, md5, gate summary, next open items); project §0 current-state lines; MON-55 comment only if status or open items changed.
- Notion: Doc 00 top callout (status, latest video, Drive ids); new Doc 13+ "VIDEO n · <topic>" page in the Docs DB (concept, numbers, ids); Workflows row Open items.
- Google Doc HUB 1g2WLpd… "Current state" updated with ids + md5.
- Final reply (Roman Urdu, concise): master + package ids; PROOF BLOCK = duration, format, integrated LUFS / true peak, the 20-gate table (check → value → threshold → PASS), novelty scores vs the registry, md5 of every file, every record id; then open items. A reply without the proof block is not a delivery.

## 8. Hard rules (any violation = not done)
Measured not eyeballed, numbers in the reply · same identity (v9 grammar, extruded type, SHADE 3D-rig hero, hybrid look, ASMR bed, chrome), next-level execution · every video different from all previous (gate #20) · no repeated transitions or SFX, no mono SFX, no static radio bed, no long inter-chapter pauses · tint-not-flood, contrast ≥4.5:1, safe area, nothing perfectly still, low density, premium = subtraction · deliverables on Drive with md5 in the same turn · records on all four platforms + local · Roman Urdu replies with ids · WF code + id, never the bare name · no questions except the topic (if missing) and the voice click.

## 9. Known traps (15 turns of lessons; read before building)
- Connectors: list_connector_tools <service> before its tools, every turn. Notion rejects imperative/agent-directed text — write factual sentences. Linear: description ≤255 chars (body goes in content), project names ≤~80 chars, no project URLs (issue URLs only), create_project returns content null → verify with get_project. Notion get_block_children page_size ≤14.
- Sandbox: restores after pauses → pip packages and processes are gone; `mkdir -p build` each time; x264 is not reproducible → compare the md5 of the uploaded file, not of a re-encode.
- Memory: quantise animated values for sprite caches; sequential shards; splice via streaming decode → swap → encode; grey stacks uint8 ≤180×320; `int()` on animated values stalls; zoom <1 → black slivers.
- Audio: `apad=whole_dur,atrim`; `asplit` when the VO is used twice; bed `place_st(t<0)` → clamp; sidechain after padding; hiss fix pad2 + VO LM250 −5.4 / LM160 −1.5; captions ≤ CAP_MAX_W 936.
- Rig/hybrid: `_dirv` swing >90° flips; black cloth needs rim/fill; Pillow alpha_composite rejects negative dest; light headline y≈520 right / y≈975 left lands on paper; dissolve the outgoing over the band; the old SFX repetition came from the 0.6 s grid → vary; closer shots are inserts.
- Transitions: luma-trace every new kind; tr_wedge mask inversion lesson; transitions END on the beat.
- PDF (only if regenerated): src/makepdf.py needs build/pdfimg JPEG twins and the root `_probe _zoom _t _cta _tr.png` plates — never delete them.
- TTS: ≤10 clips per turn; voice ids never persist across chats. Snapshot cap ~128 MB drops the newest/largest files: upload first, delete after the md5 check.

## 10. For the user (Ali)
New chat → the four apps ON (Notion, Linear, Google Drive, Google Docs) → type `SHADEGO <topic>`. If the agent asks what SHADEGO is, the answer is: "search SHADEGO in Notion, Linear and Drive and follow it". One click for the voice; everything else arrives finished with the proof block. A different style is never started with SHADEGO — it gets its own WF code, name and trigger (see the add-a-workflow checklist, Notion 3f4807e1-e916-81c2-b5b5-ef1cb8412710).
