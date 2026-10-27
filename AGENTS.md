# Mandatory instructions for every Arena agent

Before doing any work in this repository:

1. Run `python3 tools/continuity.py resume`.
2. Treat `workflows/current/ACTIVE_TASK.json` and the latest checkpoint as authoritative.
3. Log the visible user message verbatim with `continuity.py log --kind user`.
4. Never restart a completed operation or discard a newer active task because an older chat summary appears.
5. Record every material action/result/error and every long-running process ID.
6. Checkpoint before/after long operations, after material results, on errors, before ending the turn, and at least every 55 minutes while active.
7. Keep permanent accepted knowledge inside the named style under `styles/`; keep only running work in `workflows/current/payload/`.
8. Do not mark remote sync complete without updating the target's `SYNC.json` entry with its real ID/result.
9. Do not commit credentials, hidden system instructions, private connector tokens or raw sensitive identity media.
10. Run `python3 tools/studio.py validate` before a milestone commit.

If a response/process stops, query the recorded process and execute the exact next action in `RESUME.md`; do not begin again from zero.

## Finish delivery; do not stop at a progress promise

- When a runnable production step remains, continue through process completion, QA, presentation and verified upload in the same turn. Do not end merely after starting a render or saying “continuing.” A real external blocker or an explicit user pause is different.
- Query the recorded process before launching anything. Use a blocking process wait, not duplicate renders or repeated short polling.
- A checkpoint or `status=done` is not the media itself. Confirm that every required artifact actually exists; ignored runtime folders, dependencies and ignored final masters can disappear on a workspace refresh.
- Before cloud delivery, protect only the critical pending-upload bytes in a bounded recovery spool that survives snapshots. Respect the workspace patch budget and per-file limits. Keep disposable caches ignored. After Drive IDs and checksums verify, return heavy media to the repository's external-storage/ignore convention; do not permanently add large masters to Git.
- Never say “presented” before `present_file` succeeds, or “uploaded/complete” before the upload returns a real ID and the remote size/checksum match. Presentation, local encode success, cloud delivery and source recovery are separate gates.
- For media tasks, persist a delivery receipt with the actual master/source IDs, hashes and URLs. If a delivered task receives only another “continue,” return/recover its verified deliverable rather than regenerating its images, voice or edit.
- Platform/service interruptions cannot be guaranteed away. The reliable promise is durable artifacts, exact resumption and truthful completion state—not unattended connector work between turns.

## WF-06 / H3GO routing (MiniMax-H3 video)

When the user asks for MiniMax-H3, H3 video, or `H3GO <topic or shot list>`, load
`styles/minimax-h3-video/README.md` and `knowledge/01_COLAB_RUNBOOK.md` before answering or running anything.

- **Colab is a controller, not a GPU.** H3-Base needs ~100-128 GB resident; the default route is the hosted API
  (`POST /v2/video_generation`) from a CPU Colab runtime with `MINIMAX_API_KEY` in Colab Secrets.
- **Price before spending.** `python3 styles/minimax-h3-video/src/h3_client.py estimate <shotlist>` first; the
  notebook's `DRY_RUN`/`CONFIRM_SPEND` gate stays locked unless the user explicitly approves the estimate.
- **Pick the tool with the planner, not from memory.** `python3 styles/minimax-h3-video/src/route_planner.py
  plan --need <talking_hero|broll_plate|reel_loop|film_scene|lipsync_only|animate_still> [--free] [--duration N]`
  reads `data/tool_registry.json` and returns model + hardware + cost + steps + licensing. Free T4 = Wan 1.3B/LTX +
  LatentSync 1.5; 24 GB = Wan 2.2 5B / HunyuanVideo 1.5 / LatentSync 1.6; rented = Wan A14B / LTX-2.5 / H3 local;
  API = H3 2K. A talking Monarch face does **not** require H3: silent clip + own VO + LatentSync is the free chain.
- **2K only via API.** Local/pruned-weight runs are 768P; never promise 2K from a local deployment.
- **Free route = different model.** A free Colab T4 cannot run H3; use `colab/MONARCH_T4_FREE_BRIDGE.ipynb`
  (Wan 2.1 T2V 1.3B, 480p, silent, $0) for drafts/plates and keep H3 (paid) for dialogue/2K hero shots.
  Never present a free-route Wan clip as an H3 output. Tunnel/server cells stay off unless the user accepts the
  Colab ToS risk and rents GPU hosting instead.
- **Monarch identity comes from the locked reference pack** (`characters/monarch`), passed as Ref2VA
  `reference_image` items — the same 3-4 images for every shot in a scene, never prompt wording alone.
- H3 supplies talking shots and plates; WF-01's procedural rig, WF-03's line-art hero DNA and WF-05's
  editing/typography authority are not replaced. Hand off to WF-05 with video + separated audio + receipts.

## VIPER-1 (our video engine) — use it for any generated video

`tools/videogen.py` is the studio's own generator. For any request that means "generate video", work through it
instead of hand-rolling API calls:

1. `python3 tools/videogen.py doctor` — confirm this machine's reality (ffmpeg, key, registry).
2. `new` (or reuse the payload project) → edit prompts, references and `budget_usd`.
3. `plan` — read the engine-per-shot table and the retry-buffered estimate before anything else.
4. `render` (dry run) → only then `render --yes`. Paid shots need `MINIMAX_API_KEY`; free shots are emitted as
   queue files for the Colab notebook and are **not** done until the mp4 comes back.
5. `verify` (exit 3 = not delivered) → `assemble` → receipts → continuity checkpoint.

Rules: no delivery claim without `verify` passing; `budget_usd` is a hard gate; free route is the default when no
key is present; engine knowledge stays in `styles/minimax-h3-video/`, finish stays in WF-05.

## Mobile owner protocol (standing)

The owner works from a **phone**, through this agent. Never hand him CLI work.

- Run every command here (`plan`, `render` queue, `audio`, `upscale`, `mix`, `verify`, `assemble`, `quota`).
  This sandbox has a static ffmpeg (imageio-ffmpeg) and `probe()` falls back to `ffmpeg -i` when ffprobe
  is missing, so the whole finish line runs here.
- **Never put a `!`-magic inside a `if`/`try` block** in a generated notebook: Colab runs it as
  `/bin/bash: line 1: !pip: command not found`. Use `subprocess.run([sys.executable, "-m", "pip", ...])`.
  Order matters too: `DELIVERY`/paths must be defined after `BASE`, and templates must avoid `"""`/`\n`
  escapes (they close the template string). `tests/test_videogen.py` now runs the notebook's finish cell
  against real ffmpeg, so these three mistakes cannot come back silently.
- **Finish stage ke do qatil, ab tests me pinned:** concat demuxer `file <path>` ko **space par tod deta hai**
  (Drive folder `Wf-07 • Monarch Ai Agent`) → `list.txt` me sirf bare `segNN.mp4` naam + `cwd=<segments>`.
  Aur `loudnorm` **silent audio par `NaN`** deta hai (`Qavg: nan`, `frames left in the queue`) → pehle
  `volumedetect`; `mean_volume <= -70 dB` ya audio nahi → loudnorm skip + receipt me `"loudnorm": null`.
  Master `_segments/` me stage hota hai, phir `delivery/` me copy; receipt sirf copy ke baad.
- **This sandbox cannot reach Google hosts.** Never plan on downloading a clip or master here. The notebook's
  `RUN_FINISH` stage builds `delivery/<project>_MASTER.mp4` inside Colab and writes
  `colab_master_receipt.json`; read that receipt with the Drive connector and run
  `mobile_ops.py adopt <job> --receipt <json>` → `deliver --master-id <drive id>`. Only the small receipt
  crosses the boundary, never the video.
- **Drive is optional in the notebook.** `drive.mount()` may fail with `credential propagation was unsuccessful`;
  the config cell falls back to `/content/m_out/<project>` and cell 7 always builds `<project>_outputs.zip`
  (+ `files.download()`). If the owner sends that ZIP in chat, run
  `python3 tools/mobile_ops.py ingest <job> --zip <path>` (it unpacks into the project, refuses escapes, and
  re-checks) then `finish` — do not ask him to re-run for a Drive problem.
- **Drive name must end `.ipynb`** (`<project>_phone_run_all.ipynb`, mimeType `application/x-ipynb+json`) or
  Colab answers "This file type is unsupported" — rename with `update_file` before sending any link.
- **Measured on the owner's free T4 (2026-10-27):** 33 frames @ 480×832, 30 steps = **49 s** render after a
  ~3 min first-time download; host RAM 8.1–9.1 GB free with the 4-bit encoder. Quote these numbers, not guesses.
- `basicsr` / Real-ESRGAN fails to build on Colab ("Getting requirements to build wheel"): install with
  `--no-build-isolation` and patch the `torchvision.transforms.functional_tensor` import. The notebook does
  both and still falls back to ffmpeg lanczos, so an upscale problem never kills the run.
- **Free Colab = 12.7 GB host RAM.** Wan's UMT5 encoder must stay 4-bit NF4 (`load_in_4bit`, `nf4`,
  `device_map={"": 0}`), DiT fp16, VAE tiled+sliced, `HF_HUB_DISABLE_XET=1`, glibc `malloc_trim`, and the
  pipeline `del`-ed after clips. A "session crashed after using all available RAM" is never a user error —
  cut frames first (`--max-frames 33`), never ask him to retry the same config.
- Default to `mobile --one-cell` for the owner: one cell, one ▶. If a screenshot shows every cell as `[ ]`,
  nothing ran — never debug the code, just make the trigger smaller (one cell) and ask for the last cell.
- Give him **one notebook link** (`python3 tools/videogen.py mobile <project>` → upload → Colab link) with
  prompts baked in. He taps `Runtime ▸ T4 GPU ▸ Run all`; the last cell prints `DONE ✅`.
- One action per message. No multi-step terminal instructions, no JSON editing, no file renaming.
- **Drive every mobile project through `tools/mobile_ops.py` (MOBILEOPS-1), never ad-hoc.** One job file per
  project under `studio/mobile/jobs/`; the state machine (`intake → planned → handed_off → partial/clip_ready →
  mixed → verified → assembled → delivered`, plus `blocked`) decides who does what next:
  `doctor` → `start` → `plan` → `handoff --colab <link>` → (owner taps) → `check` → `finish` → `deliver`.
  Read `mobile_ops.py next <job>` before acting; a `REFUSED:` line means a gate said no — fix it, do not jump.
- Owner-facing text comes from `mobile_ops.py card <job>`: one link, one tap, zero commands (a test enforces
  that no `python3`/`pip`/`ffmpeg`/flag/`.json` ever reaches him).
- After he says `DONE`: `check` first (real bytes, not promises), then `finish` = `mix --loudnorm` → `verify` →
  `assemble`, then `deliver` with the real Drive id + md5.
- SOP: `docs/MOBILE_WORKFLOW.md` (gates, failure matrix, turn-end checklist, definition of done).

## WF-07 / AGENTGO routing (delivery home)

Everything the studio *generates* lands in the user's Drive folder **`Wf-07 • Monarch Ai Agent`**
(`1IBgfHFdigeDzaYkJuNoelhLiWLqRZ6d1`, inside `MONARCH STUDIO`) — ids and conventions in
`styles/monarch-ai-agent/data/drive.json`.

- Projects → `05 · Projects/<project-id>/` (project.json, plan.json, receipts.json, shots/)
- Masters → `06 · Masters & Receipts/`; never a master without its md5 in the receipts
- Engine + manual → `02 · Engine (VIPER-1)`; notebooks → `03 · Colab Notebooks`; knowledge exports → `04 · Knowledge`
- Git stays the source of truth for code and knowledge; Drive is delivery + sharing.
- Answer the free/paid question the same way every time: the tool and the free route cost $0.
- **Zero-spend is the default and enforced in code** (`viper-1.3`): paid steps are rewritten to the free chain
  unless someone deliberately exports `MONARCH_ALLOW_PAID=1`. Never present a paid route as the plan.
- Free compute: Colab free T4, **Kaggle ~30 GPU h/week**, Lightning free credits, laptop CPU. Log every GPU
  session with `python3 tools/videogen.py quota --use <provider> <hours>`; see `docs/FREE_ONLY_PLAYBOOK.md`.

## WF-05 / MOTIONGO routing

When the user requests WF-05, WF5, Premium Motion Editing or MOTIONGO, load `styles/premium-motion-editing/FRESH_CHAT.md` and `data/approved-profile.json` before production. Default: V5 clean integrated typography plus accepted V6 non-caption motion improvements; **no V6 bottom caption pills or active-word lower strip**. Historical case renderers are not the new-project default. Use the registered style, current acceptance policy and source-backed lessons rather than recreating the workflow from memory.
