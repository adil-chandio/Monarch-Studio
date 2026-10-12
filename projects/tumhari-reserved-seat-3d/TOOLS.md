# Tools: tumhari-reserved-seat-3d

Every tool used in this project, what it was used for, how it was run, and what it produced. Versions are as installed in the sandbox. Re-check after any reset.

## Rendering and 3-D

| Tool | Version | Used for | How it was run | Output or status |
|---|---|---|---|---|
| Blender (bpy, headless Cycles CPU) | `bpy==4.3.0`, Python 3.11 | Three 9:16 scene builders (WF-01, WF-02, WF-03) | `LD_LIBRARY_PATH=/tmp/stublib /tmp/venvs/blender/bin/python tools/render/blender-vertical/wf_scenes.py --wf NN --lookdev T --res 270x480 --samples 32 --out X.png` | Lookdev stills only. Not accepted. |
| Stub X11/GL libraries | built with `gcc -shared` | Let `import bpy` load without apt | `tools/bootstrap/setup_3d.sh` | Verified `BPY_OK` |
| Mitsuba 3 | 3.9.1 | Demo 3-D render (640×360, 12 fps, 6 s) | `tools/render/zackd3d-demo/render_demo.py`, then `encode_demo.py` | Demo proof (`zackd3d_demo_360p_12fps.mp4`, in the payload snapshot) |
| Remotion (offline) | 4.0.484 | Explainer test render, verified 4 s | `tools/render/remotion-offline/` (font shim, config) | Verified earlier |
| React Bits (Vite) | pin `2139cb3` | Animated components preview on port 5173 | `tools/render/react-bits-preview/vite.preview.config.mjs` | Preview only |

## Audio and voice

| Tool | Used for | Notes |
|---|---|---|
| Platform voice-00 (`add_voice` audition) | Demo narration `vo_part1..3.wav` | Platform voice. Not the user's voice. |
| Platform voice-02 (ur-PK) | Accent-correct narration `vo_ur_part1..3.wav` | Urdu-script speech copy for accent. |
| numpy (procedural) | Sound design: `make_sound_wf01_wf03.py`, `make_sound_wf02.py` | Scripts lost in a reset. Final MP4s survive on Drive. |
| `generate_speech` | Narration synthesis | Requires a registered voice. |

## Video encode and post

| Tool | Used for | Settings that worked |
|---|---|---|
| ffmpeg (`imageio-ffmpeg` v7.0.2 binary, `/tmp/venvs/render/.../ffmpeg-linux-x86_64-v7.0.2`) | Muxing, encoding, mux narration into MP4 | Not on PATH. Write intermediate files; `<(...)` produced no output. |
| `enhance_wf01.py` (numpy, threaded) | WF-01 v4 enhancement pass | CRF 21, grain 2.4 (20.9 MB). CRF 17 with grain 3.2 gave 103 MB. |

## Storage and sharing

| Tool | Used for | Notes |
|---|---|---|
| Google Drive connector | Finals, payload snapshot, WAV, MP4 | Call `list_connector_tools` first in each turn, or uploads fail as "unavailable". Folder: `1LTkHpkEUFSui8Lqyy8I0j5-1AceSziWX`. |
| GitHub (`git`, `gh`) | Repo, pins, PRs, archive records | `gh` is logged in. `uploads.github.com` is blocked, so release assets cannot be uploaded. |
| `tools/archive/record_artifact.sh` | Records a Drive link, size and SHA-256 in `ARTIFACTS.md` | Use after each upload. |
| `tools/vendor/materialize.sh` | Restore or release vendor repos at their pins | `status`, `one <name>`, `all`, `release all`. |
| `tools/bootstrap/setup_3d.sh` | Rebuilds the venvs and stub libraries in a new clone | Idempotent. |

## Continuity and repo checks

| Tool | Used for | Notes |
|---|---|---|
| `tools/studio.py validate` | Repo structure and manifest checks | Fails when new files are missing from `.studio-manifest.json`. Run `tools/studio.py manifest --write` after adding files. |
| `tools/continuity.py` (`resume`, `status`, `checkpoint`, `log`) | Active task, journal, checkpoints | Slot `EMS-20261012-001`. Use `checkpoint` at milestones. |
| `present_file` | Opens a deliverable in the user's viewer | Used for the lookdev sheet and earlier finals. |

## Dead ends (do not retry)

- Blender `apt-get` for X11 libraries: `deb.debian.org` blocked. Use stubs.
- Chromium `--dump-dom`: hangs silently. Use DevTools or CDP.
- GitHub Release asset upload: `uploads.github.com` blocked.
- HuggingFace model or voice assets: blocked. Do not bypass.
- `@remotion/google-fonts`: fetches at runtime, blocked. Use the offline shim.
- Playwright Chromium CDN: blocked, so browser-use cannot run browser tasks here.
- EffectCraft and cc-switch Rust builds: crates.io and static.rust-lang.org blocked.
