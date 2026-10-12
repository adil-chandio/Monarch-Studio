# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261012-001`
- **Status:** `blocked`
- **Title:** Zack-D style 3-D video (WF-02 Drive source) · tumhari reserved seat script · cloned monarch voice
- **Next action:** Await user: (a) provide/confirm MuAPI key entry in the app UI for generation, (b) build EffectCraft on a machine with Rust, or (c) choose next render path.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.

## Video work: resume from the brain first

Every video style keeps its memory in `styles/<style-id>/brain/video-brain/`: mindset, toolchain, pipeline, next-level backlog, and append-only ledgers (sessions, problems, skills, strategies, videos). Before any video work, run:

```bash
python3 tools/brain.py list
python3 tools/brain.py resume <style-id>     # e.g. monarch-zackd-3d-power, monarch-stickman-animation, monarch-noir-film
python3 tools/brain.py check                 # every registered style has a complete brain
```

Log every working turn with `tools/brain.py session`, every failure with `problem` (and `resolve` when fixed), every reusable method with `skill`, every approach decision with `strategy`, and every video or lookdev with `video`. The ledgers are append-only: correct an old entry with a new entry, never by editing.

Project history (chat, process, tools, artifacts index) for the current 3-D work lives in [`projects/`](projects/README.md).
