#!/usr/bin/env python3
"""records_turn18.py — patch the local records after THE SHADOW v1 is on Drive. usage: records_turn18.py values.json"""
import json, sys, re, datetime, os
V = json.load(open(sys.argv[1]))
ROOT = '/home/user'
WF = f'{ROOT}/workflows/wf03_monarch_noir_film'
today = '2026-10-10'
G = V['gates']  # dict from gates_summary.json

def rw(path, fn):
    s = open(path, encoding='utf-8').read()
    s2 = fn(s)
    assert s2 != s, path
    open(path, 'w', encoding='utf-8').write(s2)
    print('patched', os.path.relpath(path, ROOT))

film_line = (f"**THE SHADOW v1** — `THE_SHADOW_v1.mp4` {G['duration']:.2f} s 1920×1080 24 fps, {V['size_mb']} MB, md5 `{V['md5']}`, Drive `{V['ids']['mp4']}` "
             f"(md5 verified) · gates {G['passed']}/{G['total']} PASS (`GATES_THE_SHADOW_v1.md` → Drive `{V['ids']['gates']}`) · {G['lufs']:.1f} LUFS, TP {G['tp']:.1f} dBTP, LRA {G['lra']:.1f} LU · "
             f"luma {G['luma']:.1f}/255, dark {G['dark']*100:.0f} %, chroma {G['chroma']:.1f} · 33 shots, {G['holds']} holds 8–14 s, {G['beats']} beats · 3 voice lines (voice-02) · brain gate #20 PASS 18/18, committed `{V['brain_key']}`.")

# 1 WF-03 HUB.md
def hub(s):
    s = s.replace("## Current state\n", f"## Current state\n- {today} (turn 18): **ACTIVE — film #1 delivered.** {film_line}\n  Sources: `src/film_shadow.py` (timeline + renderer, Drive `{V['ids']['film_py']}`), `src/audio_shadow.py` (score/SD/VO mix, Drive `{V['ids']['audio_py']}`), `src/gate_shadow.py` (film gates, Drive `{V['ids']['gate_py']}`), `SCRIPT_THE_SHADOW.md` (Drive `{V['ids']['script']}`), `DNA_THE_SHADOW.json` (Drive `{V['ids']['dna']}`).\n", 1)
    s = re.sub(r"## Open items\n- User look approval.*?\n", f"## Open items\n- Film #1 done. Next `NOIRGO <topic>` = film #2: brain proposes (`brain/concept.py propose --format film`), new world/device (lantern_corner + shadow_homothety are now blocked), voice audition click, same pipeline (film_shadow-style timeline → background render → audio_shadow-style mix → gate_shadow → Drive md5 → commit → records).\n- v1 notes for v2 of the engine: text reveal times should be exported into events.json by the renderer (turn 18 parsed them from source); renderer ≈0.6 s/frame at 1080p on 2 vCPU (≈38 min per 150 s) — fine in background; audio builder must stay chunked/float32 (OOM at 2 GB when the render runs in parallel).\n", s, count=1, flags=re.S)
    return s
rw(f'{WF}/HUB.md', hub)

# 2 WF-03 RESUME_STATE.md — newest block on top
def rs(s):
    block = f"""## {today} (turn 18) — FILM #1 DELIVERED · Status ACTIVE
- {film_line}
- Records: Notion row `3f4807e1-e916-810e-a035-fce9f7cc8f3f` Status → Active · Notion page callout `{V['ids'].get('notion_callout','')}` · MON-57 In Progress + STATE comment `{V['ids'].get('mon57_comment','')}` · Linear project §0 updated · Doc HUB section appended · registry MON-55 comment `{V['ids'].get('mon55_comment','')}` · brain v2.1 (format-aware gate; library +lantern_corner +shadow_homothety).
- Pipeline that produced it (repeat for film #2): `python3 src/film_shadow.py --events build/wf03_film/events.json --render build/wf03_film/picture.mp4 --metrics build/wf03_film/picture_metrics.json` (start_process, ≈38 min) → `generate_speech` ×3 (voice-02) → `python3 src/audio_shadow.py` (−16.5 LUFS mix) → `src/encode_shadow.sh` (segment encode CRF 21 medium, frame-exact splice of re-rendered shots, S03/S16 gamma trims, mux; the renderer master is ≈45 Mbit/s and must never be delivered) → `python3 src/gate_shadow.py` → Drive upload → `gate_shadow.py --drive-md5` → `brain/concept.py commit`.
- Voice: voice-02 (this chat only — a new chat must re-audition). Dependencies after a restore: `pip install numpy pillow scipy imageio-ffmpeg`, `mkdir -p build/wf03_film`.

"""
    return s.replace("## 2026-10-09 (turn 17)", block + "## 2026-10-09 (turn 17)", 1)
rw(f'{WF}/RESUME_STATE.md', rs)

# 3 CHECKLIST
def ck(s):
    return s + f"\n## Film #1 — THE SHADOW ({today}, turn 18)\n- [x] look approved → timeline locked (33 shots, 156.9 s) → voice-02 ×3 → render → mix → mux → gates {G['passed']}/{G['total']} → Drive `{V['ids']['mp4']}` md5 `{V['md5']}` → brain commit → records on all four platforms → Status ACTIVE.\n"
rw(f'{WF}/CHECKLIST.md', ck)

# 4 root RESUME_STATE pointer
def root_rs(s):
    return s.replace("Status Planned (look-dev v0 awaiting approval).", f"**Status ACTIVE — film #1 THE SHADOW v1 delivered {today} (turn 18): Drive `{V['ids']['mp4']}` md5 `{V['md5']}`, gates {G['passed']}/{G['total']}, {G['lufs']:.1f} LUFS; see `workflows/wf03_monarch_noir_film/RESUME_STATE.md`.**", 1)
rw(f'{ROOT}/RESUME_STATE.md', root_rs)

# 5 DRIVE_MANIFEST rows
def man(s):
    rows = "".join(f"| `{name}` (WF-03, turn 18) | `{fid}` | {md5} |\n" for name, fid, md5 in V['manifest_rows'])
    anchor = "| Google Doc `WF-03 · Monarch Noir Film — HUB` | `1sGGzPHXXars1-pJvB3ugnbnLuSuQ5EpE-obVidTj6rM` | (native doc) |\n"
    assert anchor in s
    return s.replace(anchor, anchor + rows, 1)
rw(f'{ROOT}/DRIVE_MANIFEST.md', man)

# 6 registry row
def reg(s):
    s = s.replace("| WF-03 | Monarch Noir Film | `NOIRGO <topic>` | PLANNED · look-dev v0 done (2026-10-09) |", f"| WF-03 | Monarch Noir Film | `NOIRGO <topic>` | ACTIVE · film #1 THE SHADOW v1 delivered ({today}) |", 1)
    s = s.replace("| workflows/wf03_monarch_noir_film/ | look-dev v0 done 2026-10-09 → awaiting look approval → film #1 THE SHADOW |", f"| workflows/wf03_monarch_noir_film/ | film #1 THE SHADOW v1 on Drive `{V['ids']['mp4']}` (gates {G['passed']}/{G['total']}) → next NOIRGO = film #2 |", 1)
    return s
rw(f'{ROOT}/MONARCH_STUDIO_REGISTRY.md', reg)

# 7 session log §23
def log(s):
    return s + f"""
## §23 — {today} (turn 18): WF-03 film #1 **THE SHADOW v1** produced, measured, delivered — WF-03 Status ACTIVE
- User approved the look + topic ("Aage BAHDO"). Voice audition → **voice-02** (masculine EN narration). Three lines generated (vo1 51.3 s, vo2 94.8 s, vo3 144.2 s).
- Picture: `workflows/wf03_monarch_noir_film/src/film_shadow.py` — 33-shot locked timeline 156.9 s (S01–S10, montage M1–M8 1.7→0.9 s, climax C1–C6 0.4 s, S12–S20), vector zoom/drift per shot, kneeling/sitting/carry poses, physically cast wall shadow (k ≤ 2.2 + body-thickness offset), carried lamp → floor shadow; rendered in background (start_process, 3766 frames, {V['render_min']} min, 0 frame errors) with per-shot metrics. {V.get('delivery_notes','')}
- Sound: `src/audio_shadow.py` — everything synthesized from events.json (room tone that never breathes out, 55 Hz sub + E1 in the dark, A-minor cello pad, 90 BPM piano motif, heartbeat + riser into the climax with a hard stop, footsteps panned from the animation, typewriter clicks, red-card stabs, lantern whump/huff/crackle, cut booms, wall thump + 0.4 s silence, lamp foley), VO centred and de-essed, bed ducked −5 dB, look-ahead limiter, normalised to −16.5 LUFS. Lesson: build chunked/float32 — the first version OOM-killed next to the render (2 GB box).
- Delivered: {film_line}
- Gates: `GATES_THE_SHADOW_v1.md` — measured on the delivered mp4: container, duration, luma/dark/chroma vs Day One, per-shot setup luma, render errors, cut detection on grey proxies (planned cuts found, 0 dissolve runs), max still run, stray black frames, holds, longest shot, montage/climax structure, beats density, 3 spoken lines, callbacks, quotables + pun, text contrast, LUFS/TP/LRA, quiet tail after the last line, dynamic arc, limiter share, brain gate, md5. {V.get('gate_notes','')}
- Brain v2.1: gate #20 made format-aware (beats instead of shots for films, cut-grammar kinds, same-format overlap, film interrupt/WTF targets); library + `lantern_corner`, `shadow_homothety`; registry entry `{V['brain_key']}` (format film, workflow WF-03). `MONARCH_EDITOR_BRAIN.md` §15.
- Records: Notion Workflows row Status Planned → **Active** (+ Open items), WF-03 page callout `{V['ids'].get('notion_callout','')}`; MON-57 → In Progress + STATE comment `{V['ids'].get('mon57_comment','')}`; Linear project `e173192b…` §0 rewritten; Doc HUB `1sGGzPHX…` film section appended; MON-55 registry comment `{V['ids'].get('mon55_comment','')}`; Drive uploads listed in DRIVE_MANIFEST (WF-03 rows, turn 18); local HUB/RESUME_STATE/CHECKLIST/registry updated.
- WF-01 untouched (PARKED; MON-44, MON-48 open). Next `NOIRGO <topic>` = film #2 with a fresh world/device (brain blocks lantern_corner + shadow_homothety).
"""
rw(f'{ROOT}/MONARCH_STICKMAN_ANIMATION_SESSION_LOG.md', log)
print('records patched')
