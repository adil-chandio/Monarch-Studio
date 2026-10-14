# Storage and materialization

## Why compact mode exists

Arena workspace snapshots are best-effort capped near 128 MB. Keeping a 60+ MB worktree, a 60+ MB Git object database, duplicate recovery archives and populated vendor clones can exceed that boundary and silently omit files on the next turn.

The permanent source is not deleted. Git and Drive keep it; compact mode only marks heavy tracked assets as sparse-omitted in this local worktree.

## 2026-10-14 investigation — why sessions kept "stopping"

The user asked twice why the process stops again and again. Measured cause, in order of impact:

1. **A fresh turn starts at `main`.** `git reflog` in the recovered workspace shows only
   `clone` + `checkout main → arena/<session-branch>`. Work committed in earlier turns
   lived on *other* arena branches (`arena/a188bd4a…`, `arena/ab4ba9f7…`,
   `arena/d53677cc…`) and on Drive. A checkout at `main` shows none of it, so the
   session looked restarted even though nothing was lost.
2. **The workspace was over the snapshot cap before any render.**
   `python3 tools/repo_budget.py` measured **199.8 MB**: 108 MB worktree + 91.7 MB `.git`
   against a ~128 MB best-effort cap. Over-cap snapshots drop the newest files silently —
   exactly the failure recorded in `operations/incidents/INC-20261011-001`. Symptoms:
   `workflows/current/payload/chaos02/*.py` and other fresh work missing next turn.
3. **Drive assets were staged inside the workspace.** The connector downloads into
   `./google_drive/`; pulling the 26 MB reference video + 25 MB side-face video + 47 MB
   phone clip added ~100 MB to the snapshot on top of an already-over-cap tree.
4. **The render environment is not part of the snapshot.** `numpy`, `Pillow`, `scipy`,
   `cv2` and the ffmpeg binary live outside the workspace and vanish each turn; earlier
   sessions spent the first 20-30 minutes re-discovering them, which reads as a stall.

Fixes now in the repository:

- `tools/session_recover.sh` — list arena branches by commit date, print the recorded next
  action, `--merge <ref>` to fast-forward instead of restarting. (Anti-stop rule 11.)
- `tools/repo_budget.py` + `make budget` — measure workspace/`.git`/staging against the cap
  and fail loudly with the exact remediation commands. (Rule 12.)
- `tools/bootstrap_env.sh` + `make env` — idempotent dependency install/verify, stamps
  `.runtime/env-bootstrap.stamp`. (Rule 14.)
- `.gitignore` now excludes `google_drive/`, `_probe/`, `renders/` and rendered media
  (`*.mp4|*.mov|*.mkv|*.wav|*.flac`), including the previously-missed uppercase
  `*_MASTER.mp4` pattern that the WF-04 renderer writes.
- `payload/plates/` (a byte-identical 20 MB duplicate of `styles/monarch-face-chaos/plates/`)
  was deleted; both engine copies resolve the plates directory through `_plates_dir()`.

## Commands

```bash
python3 tools/materialize.py status
python3 tools/materialize.py compact   # control plane + source/gates/indexes
python3 tools/materialize.py full      # required before a full render/package rebuild
```

Both mode changes require a clean worktree. `studio.py` preserves hash records for tracked sparse-omitted files and reports deferred verification as a warning.

## Compact set

Compact mode retains:

- active task, journal, transcript, checkpoints and outbox;
- documentation, schemas, CI, tests and all control tools;
- both style root contracts/notes plus renderer source, brain, gates, event/data records and knowledge indexes;
- WF-01 fonts required by compatibility hydration;
- Monarch authority metadata, tooling, board/Bible and previews;
- studio registry/editor brain and all root governance files.

It omits the largest reconstructable render inputs from the local worktree, notably WF-01 generated audio assets and WF-03 plate/VO directories. They remain Git blobs and are also represented in Drive recovery bundles. WF-04 plates and engine are **kept** because WF-04 is the active workflow.

## Vendor repositories

Vendor projects remain pinned as gitlinks. Initialize only when needed:

```bash
git submodule update --init vendor/effectcraft
git submodule update --init vendor/awesome-opus5-5-videos
```

Remove populated vendor working trees after use if snapshot capacity is tight; the pins remain.

## Full recovery

1. Clone the GitHub repository when available, or clone the Drive Git bundle.
2. Apply checkpoint delta bundles in the documented order when using Drive recovery.
3. Run `python3 tools/materialize.py full`.
4. Run `git submodule update --init` only for vendor work being used.
5. Run `python3 tools/studio.py validate` and the test suite.
6. Run `python3 tools/continuity.py resume` and continue the exact next action.

## Materializing Drive assets without blowing the cap

The Google Drive connector is the only channel into the sandbox (the shell cannot reach
`drive.google.com`; verified `curl` TLS reset). It writes downloads to `./google_drive/`
inside the workspace, so:

```bash
# 1. ask the connector for the file (agent tool) ...
# 2. move it out of the snapshot immediately:
mkdir -p /tmp/monarch-stage && mv google_drive/* /tmp/monarch-stage/
# 3. keep only small derived artifacts in the repo (analysis JSON, sheets),
#    with the Drive ID + MD5 recorded next to them.
```

WF-04 reference audio for the renderer is derived, not stored raw:

```bash
python3 - <<'PY'   # once per turn, from the staged reference video
import imageio_ffmpeg, subprocess
exe = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([exe,"-y","-i","/tmp/monarch-stage/ref.mp4","-vn","-ac","2","-ar","44100",
                "-c:a","pcm_s16le",".runtime/ref_video/ref_audio.wav"], check=True)
PY
```
