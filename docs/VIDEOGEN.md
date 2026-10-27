# VIPER-1 · Monarch Studio's own AI video engine

`tools/videogen.py` — one project file, many engines. It is the studio's first-party tool, not another vendor script:
it decides **how** each shot gets made, prices it, renders what this machine can, queues what it cannot,
verifies the media, and assembles the master.

```text
tools/videogen.py doctor
tools/videogen.py new    --id monarch-reel-01 --title "Monarch reel 01" --aspect 9:16
tools/videogen.py plan   <project>/project.json
tools/videogen.py render <project>/project.json            # dry run, spends nothing
tools/videogen.py render <project>/project.json --yes      # submits paid shots
tools/videogen.py verify <project>/project.json
tools/videogen.py assemble <project>/project.json
tools/videogen.py status <project>/project.json
```

## 1. Why this exists

Every AI video vendor changes weekly, and each one has its own API, quota, VRAM floor and licence. The studio
should not re-learn that per project. VIPER-1 keeps **one job format** and swaps engines underneath:

| Engine id | What it is | Cost | Where it runs |
|---|---|---|---|
| `h3` | MiniMax-H3 hosted API (`POST /v2/video_generation`) | $0.08/s @768P · $0.13/s @2K | anywhere, needs `MINIMAX_API_KEY` |
| `wan` | Wan 2.1 T2V 1.3B on free Colab T4 | $0 | **queued** for `styles/minimax-h3-video/colab/MONARCH_T4_FREE_BRIDGE.ipynb` |
| `latentsync` | ByteDance LatentSync lipsync pass | $0 | GPU machine script (T4 needs the sm_75 fp16 patch) |

The model menu, licences and VRAM floors live in `styles/minimax-h3-video/data/tool_registry.json`; the
prose version is `styles/minimax-h3-video/knowledge/06_NEXT_LEVEL_TOOLBOX.md`. Add a row to the registry and a
planner branch in `route_planner.py` when a new engine earns its place — the project format does not change.

## 2. Project file

Created by `new`, edited by hand. Lives in the active payload (`workflows/current/payload/<project-id>/`).

```json
{
  "schema_version": 1,
  "project_id": "monarch-reel-01",
  "title": "Monarch reel 01",
  "character": "monarch",
  "aspect": "9:16",
  "fps": 24,
  "delivery_fps": 30,
  "route": "auto",
  "budget_usd": 5.0,
  "audio": { "music": "assets/music/bed.mp3", "dialogue": [] },
  "shots": [
    { "id": "s01-hook", "kind": "hero", "seconds": 5, "ratio": "9:16",
      "prompt": "…Ref2VA / T2VA prompt…", "references": ["assets/refs/MONARCH_REAL_FRONT.png"],
      "voice_ref": "assets/vo/line1.wav", "seed": 42 },
    { "id": "s02-plate", "kind": "plate", "seconds": 5, "prompt": "…", "seed": 7 },
    { "id": "s03-sync", "kind": "lipsync", "seconds": 5, "source": "s02-plate", "audio": "assets/vo/line2.wav" }
  ]
}
```

Rules the tool enforces before it touches money:

- `seconds` must be 4–15 (H3's own range; long shots are split into beats).
- `ratio` must be one of H3's ratios; defaults to the project aspect.
- shot ids are plain filenames (no `../`), unique, and become `<id>.mp4` in `shots/`.
- `route`: `auto` (paid hero if a key exists, free everywhere else) · `free` (never spend) · `paid` (all H3).
- `budget_usd` is a **hard** gate: the retry-buffered estimate must fit, or `render --yes` refuses.

## 3. What each command actually does

**`plan`** resolves each shot into ordered steps and writes `plan.json`:

```text
shot                  engine          steps                                 cost
s01-hook              free-chain      wan:queue -> latentsync:lipsync       0.00
s02-plate             free-chain      wan:queue                             0.00

ESTIMATE        $0.00
+ retry buffer  $0.00  (x1.5)
BUDGET          $5.00  -> OK
WARN            s01-hook: lipsync pass has no voice_ref/audio yet
```

**`render`** executes only what this machine can do:

- `h3` → submits with `h3_client.build_payload()`/`run_shot()`, writes `task_id`, billed seconds, md5 into `receipts.json`.
  Without `--yes` it prints the payload preview and submits nothing.
- `wan` → writes `queue/free_jobs-<project>.json` (portrait-aware 480×832 or 832×480, `frames = 4k+1`, seed, prompt).
  Open the free notebook, load that file as the queue, and save the mp4s back into `shots/` with the same ids.
- `latentsync` → writes an executable `lipsync/<shot>.sh` with the exact source, voice track and output paths
  (`<id>-talk.mp4`), plus the T4 fp16 patch note.

**`verify`** is the only thing that can call a shot done. It checks the file exists, hashes it, probes it when
`ffprobe` is present (duration ±0.6 s, fps within 1, audio present for paid hero shots) and records everything in
`receipts.json`. Missing media exits `3` so CI and the assistant cannot claim delivery by accident.

**`assemble`** concatenates the verified shots (talk version wins over the silent clip), conforms to
`delivery_fps`, optionally loops `audio.music` under the cut and fades it, writes `delivery/<id>_MASTER.mp4` and
adds a master receipt (md5, probe, fps). No `ffmpeg` → clean error, never a fake success.

**`status`** recomputes the plan (a stale `plan.json` cannot mislead) and prints per-shot state.

**`doctor`** checks python, ffmpeg/ffprobe, the tool registry, `MINIMAX_API_KEY`, the character authority and the
free notebook.

## 4. Exit codes

| Code | Meaning |
|---|---|
| 0 | ok / nothing spent / verified |
| 2 | user-fixable problem (invalid project, missing key, no ffmpeg, over budget) |
| 3 | media verification failed (missing shot, duration/fps/audio mismatch) |

## 5. Relationship to the rest of the studio

```text
characters/monarch        identity authority (reference pack)
        │
tools/videogen.py         plan → render/queue → verify → assemble      ← this tool
        │
WF-05 (styles/premium-motion-editing)   typography, transitions, score, 24→30 fps conform
        │
delivery + receipts + Drive + continuity checkpoint
```

- **WF-01 / WF-03 stay procedural.** They use VIPER-1 for plates and atmosphere, not for their hero line-art.
- **WF-06 owns the engine knowledge** (model facts, Colab runbook, prompting, routes, free toolbox).
- **WF-05 owns the finish.** VIPER-1 hands over shots + separated audio + receipts, never captions or grades.
- **Continuity:** the project lives in `workflows/current/payload/`; when it is accepted, promote to the style's
  `projects/` folder and checkpoint with `tools/continuity.py checkpoint --commit --push`.

## 6. Adding an engine (the checklist)

1. Add a row to `styles/minimax-h3-video/data/tool_registry.json` (licence, tier, VRAM, audio, speed, cost, confidence).
2. Add the planner branch in `styles/minimax-h3-video/src/route_planner.py`.
3. Add the engine to `tools/videogen.py`'s `plan_shot()` and, if it can run here, a `render_<engine>()`.
4. Add a test in `tests/test_videogen.py` that proves the dry run spends nothing and the paid path is gated.
5. Update this document's engine table and `knowledge/06_NEXT_LEVEL_TOOLBOX.md`.

Never let an engine report success without a file on disk: `verify` is the single source of truth.

## 7. Cost discipline (baked in)

| Guard | Where |
|---|---|
| dry run by default | `render` without `--yes` |
| retry buffer in the budget check | `plan` uses 1.5× |
| no silent overspend | `--allow-over-budget` must be explicit |
| receipts carry billed seconds and `task_id` | `render` → `receipts.json` |
| free engine is the default when no key exists | `route=auto` |
| a started render is not a delivered shot | `verify` exit codes |

## 8. Example

`studio/videogen/examples/monarch-reel-01.project.json` — a three-shot vertical reel (hero + plate + payoff) with
the real Monarch prompt skeleton, budget $5, route `auto`. Copy it into the payload folder, point the references at
your crops, then `plan → render → verify → assemble`.
