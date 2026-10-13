# 3D video pipeline and skills (Tumhari Reserved Seat, 9:16)

Status: **in progress, not accepted.** No WF-01/02/03 film has passed a frame-level review at premium quality. Lookdev stills are test quality. Do not describe any output as finished or premium until it has been checked frame by frame.

This runbook records what the studio has set up, what each tool is for, the Blender lessons from the lookdev passes, and the blockers. The repo pins are the source of truth for the vendored code. See `docs/VENDOR_INTEGRATION.md` for licence and adoption rules.

## 0. Start a new chat or a fresh clone (no Drive needed)

The workspace stays light. Everything the pipeline needs is either in Git or fetched from GitHub at a pinned commit.

```bash
git clone https://github.com/adil-chandio/Monarch-Studio.git && cd Monarch-Studio
git checkout arena/a188bd4a-monarch-studio          # the working branch
tools/bootstrap/setup_3d.sh                         # venvs + stub libs, verifies BPY_OK
tools/vendor/materialize.sh one react-bits          # any vendor repo, at its pin (or: all)
```

What is in Git: the pins for all 10 vendor repos, the text skill files (`docs/skills/vendored/`), the render scripts (`tools/render/`), the runbooks, and the continuity records.
What comes from GitHub on demand: the vendor source at its pin (`tools/vendor/materialize.sh`).
What is rebuilt locally: `/tmp` venvs and stub libraries (`tools/bootstrap/setup_3d.sh`).
What is not recoverable: the WF-02 v2 render and sound scripts, the `test10s` working set, and the first `wf_scenes.py` (see Section 8). Keep media output out of Git. Store final films on Drive.

Lookdev check after setup: `LD_LIBRARY_PATH=/tmp/stublib /tmp/venvs/blender/bin/python tools/render/blender-vertical/wf_scenes.py --wf 02 --lookdev 9.5 --res 270x480 --samples 32 --out /tmp/wf02.png`.

## 1. Locked concepts (approved by the user)

| Style | Metaphor | Editing and animation | Sound | Palette |
|---|---|---|---|---|
| WF-01 Paper Cinema | Paper train timetable with a reserved seat | Paper-page turns at each cut, three-plane parallax, paper-style motion | Paper percussion and paper SFX | Warm paper, red ink |
| WF-03 Midnight Platform Noir | Reserved ticket as a timer that runs out | Slow dolly, lens breath, rain ASMR, long holds, fewer cuts | Rain ASMR, procedural | Cold blue and amber |
| WF-02 Zack-D 3D Power | 20 min × 90 days = 30 hours, one cube per second, voxel 3D text | Hard cuts, whip angle changes, chrome and neon materials | Procedural | Chrome, gold, cyan neon |

All three are 9:16 vertical. Each style must have its own shot grammar. Do not share one look across styles.

Narration: script of record is `styles/monarch-stickman-animation/films/tumhari-reserved-seat/SCRIPT_AND_TOPIC.md` (74 s, Roman Urdunglish). Demo voice is voice-00. Accent-corrected ur-PK voice is voice-02. Voice cloning of the user's own voice is not done. It needs an allowed registry and a voice sample from the user.

## 2. Repo inventory (vendor/, pinned submodules)

| Path | Pin | Licence | Use in this pipeline |
|---|---|---|---|
| `vendor/effectcraft` | `f8b2552` | Apache-2.0 OR MIT | Optional effects or orchestration adapter. Rust build needs crates.io, which is blocked. |
| `vendor/awesome-opus5-5-videos` | `7562902` | (see upstream) | Research index only. Not an authority for prompts. |
| `vendor/open-generative-ai` | `6b704b0` | MIT | Next.js/Electron studio. Hosted generation needs the user's MuAPI key (`api.muapi.ai` is not allowed here). |
| `vendor/react-bits` | `2139cb3` | MIT + Commons Clause | Animated React components for web overlays. Do not sell or redistribute the components alone. |
| `vendor/OpenMontage` | `9327439` | AGPL-3.0 | Agentic video pipeline. Real providers need keys. Piper TTS voice models come from HuggingFace, which is blocked. AGPL network-use duties apply if modified code is served. |
| `vendor/browser-use` | `c75e847` | MIT | Browser agent. Needs Chromium, and the Playwright CDN is blocked here. |
| `vendor/cc-switch` | `28dc519` | MIT | Desktop assistant for switching AI coding-tool providers. Not video. Rust build blocked here. |
| `vendor/FreeCAD` | `23a5e34` | LGPL-2.1 | Parametric CAD. Not used in the video path. Pin moved from the old short pin `ec6852e` (see Section 7). |
| `vendor/Agent-Reach` | `94f06c1` | MIT | Agent read/search access. Uses logged-in channel cookies. Keep credentials out. Keep out of the render path. |
| `vendor/Scrapling` | `7a68493` | BSD-3-Clause | Scraping. Only within site terms and robots rules. Scraped footage needs a licence. |

Checkout: `git submodule update --init --depth 1 -- vendor/<name>`. Do not edit vendored code as Monarch source.

## 3. Tools in this repo

| Path | What it is | Status |
|---|---|---|
| `tools/render/blender-vertical/wf_scenes.py` | Three 9:16 Blender Cycles scene builders (`build_wf01/02/03`) and frame updaters (`update_wf0x`). CLI: `--wf 01|02|03 --out DIR --res 360x640 --samples 48 --frames 0-239`, or `--lookdev T --out PNG`. `NOVOL=1` hides the WF-03 haze cube. | Lookdev only. Not accepted. |
| `tools/render/zackd3d-demo/` | Mitsuba 3 CPU demo (`render_demo.py` 640×360 12 fps 6 s, `encode_demo.py`, `probe.py`). | Demo proof, not a film. |
| `tools/render/remotion-offline/` | Offline Remotion config and font shim. | Verified earlier with a 4 s Explainer render. |
| `tools/render/react-bits-preview/vite.preview.config.mjs` | Preview wrapper that reuses the vendored React Bits config. It allows the sandbox preview host and does not touch `vendor/react-bits`. | Moved from `workflows/current/payload/` in this pass. |
| `docs/runbooks/LOCAL_NO_API_RENDER.md` | Local render without API keys. Section 3 covers Blender bpy headless. | Verified (Cycles CPU). |

## 4. Blender headless setup (verified)

```bash
python3 -m venv /tmp/venvs/blender
/tmp/venvs/blender/bin/pip install "bpy==4.3.0" numpy
# X11/GL sonames are missing in this sandbox (apt is blocked). Build tiny stubs:
mkdir -p /tmp/stublib && cd /tmp/stublib
for lib in libXrender.so.1 libXxf86vm.so.1 libXfixes.so.3 libXi.so.6 libxkbcommon.so.0 libSM.so.6 libICE.so.6 libGL.so.1; do
  echo 'int stub_dummy(void){return 0;}' > s.c && gcc -shared -fPIC -Wl,-soname,$lib -o $lib s.c
done
LD_LIBRARY_PATH=/tmp/stublib /tmp/venvs/blender/bin/python -c "import os,sys; sys.setdlopenflags(os.RTLD_LAZY|os.RTLD_GLOBAL); import bpy; print(bpy.app.version_string)"
```

- The `_ARRAY_API` / numpy warnings from bpy are harmless. One run hit `numpy.core.multiarray failed to import` and a rerun worked. If it happens, rerun once before debugging.
- `/tmp` is wiped by resets. Recreate the venvs and stubs each time.
- Do not link an object into a collection twice. Blender raises "already in collection".

## 5. Blender scene lessons (from the lookdev passes)

These are measured lessons, not style decisions.

- **Reveal by visibility, not only scale.** Cube k only appears from t = k, so a lookdev at t = 3.5 shows only four cubes. This is correct behaviour but it is easy to mistake for a framing bug. Test WF-02 at t ≥ 9.5 to see the full tower.
- **Text reveal.** A text object with `scale = 0` is invisible. Start the reveal after the scene has built up, or lookdev it at a later time.
- **Portrait sensor.** In a 9:16 render with AUTO sensor fit, the 36 mm sensor width applies to the height. At 50 mm, a 19 m distance shows about 13.7 m of height. Set the camera distance from the tallest object, not from the floor.
- **Emission and AgX.** Emission above about 3 for text blows out to white blocks under the default AgX view transform, so the glyph shapes read as blobs. Keep neon emission around 1–3 and use a bloom-free base colour for the body.
- **World strength drives metal.** Chrome and gold cubes look black under a dark world. A mid-blue world at strength 1.1 made the whole frame grey and flat. The next step is a gradient or HDRI-like world with a bright top and a dark floor, not a flat colour.
- **Area light size and energy.** WF-01 washed out with energy 900 and size 6. A raking area light (size 2.5, energy 380) gave readable paper layers.
- **Volumetrics.** Haze density 0.022 was too noisy. 0.004–0.007 is usable at 32 spp. The volume has to fill the camera's view, so the haze cube should enclose the camera.
- **Lamp pool.** A point lamp at 900 W barely lit the bench. A 4200 W point lamp lit the ticket. A spot light aimed at the ticket is the likely next step.
- **Keep the ticket on the bench.** A ticket floating 1.3 m above the bench reads as a bug. Lying it flat at bench height (z ≈ 0.73) reads as a ticket.

Timing measured in this sandbox (2 vCPU):
- WF-02, 270×480, 32 spp: about 2.3 s per frame.
- WF-03 with volume, 270×480, 24 spp: about 10 s per frame.
- 360×640 at 48 spp is an estimate of about 6 s per frame for WF-02. It is not measured. Check per-frame timing before a 240-frame run.

## 6. Sound and video tooling

- Sound is procedural (numpy) by default. Sample libraries only if the user supplies a licensed library.
- Narration muxing: `ffmpeg` from `imageio-ffmpeg` (`/tmp/venvs/media/.../ffmpeg-linux-x86_64-v7.0.2`, not on PATH). Write intermediate files. Process substitution `<(...)` produced no output here.
- Final encode: CRF 21 with grain 2.4. CRF 17 with grain 3.2 gave a 103 MB file.
- Drive upload: `google_drive__upload_file` fails until `list_connector_tools` is called first in the turn.

## 7. Blockers in this sandbox

- HuggingFace and every mirror are blocked. Do not bypass the allowlist.
- `deb.debian.org` (apt) is blocked. X11/GL sonames are stubbed instead.
- `api.muapi.ai`, Kling, Luma and other provider APIs need the user's keys and their own allowlisted hosts.
- crates.io and static.rust-lang.org are blocked. EffectCraft and cc-switch cannot build here.
- Google Fonts is blocked. Use the offline font shim.
- `ec6852e` was the old FreeCAD pin in `VENDOR_INTEGRATION.md`, a short SHA that GitHub will not fetch directly. The pin is now `23a5e34` (upstream `main`). Update the doc's historical note if a full SHA for `ec6852e` is recovered.

## 8. Recovery after a sandbox reset

1. Check `git log -1` against `origin/arena/a188bd4a-monarch-studio`. Local can fall behind after a reset.
2. Back up first. Copy the tracked diff and untracked folders to `/tmp/restore_backup_N/`.
3. If tracked diffs equal origin, `git checkout -- .` and `git merge --ff-only origin/arena/a188bd4a-monarch-studio`. Move untracked copies that origin also has out of the way first. Never hard-reset.
4. Re-init vendor submodules: `git submodule update --init --depth 1 -- vendor/<name>`.
5. Recreate the Blender venv and stubs (Section 4).
6. Check `workflows/current/payload/` against the list below.

Media and scratch files are not committed (`workflows/current/payload/` holds the mp4, wav and png outputs, and it stays untracked). Scripts that matter are copied to `tools/render/`.

### Lost in the resets (not recoverable from this sandbox)

- `zackd3d_demo/render_v2_power.py` and `make_sound_wf02.py` (WF-02 v2 render and sound).
- `test10s/` (`enhance_wf01.py`, `make_sound_wf01_wf03.py`, the 10 s test MP4s).
- `test10s_final/` local MP4s. The Drive copies from the earlier uploads still exist (IDs in the session record).
- The original `wf_scenes.py`. The file in `tools/render/blender-vertical/` was rewritten from memory and carries the lookdev patches (WF-02 spacing 1.25, WF-03 flat ticket, WF-01 raking light, lamp 4200 W, haze 0.004).

## 9. Drive deliverables (uploaded earlier, not re-checked after reset)

- WF-01 v4 enhanced: `1puZyLWIX4YG43iX2G0u86hJT16_3_3ob`
- WF-02 v2 30HRS: `16pfe4ZwNfSE4Fgj0ktTZniRN1EcjmLJ9`
- WF-03 v3 sound pass (old picture): `1SmMEo2lhc5EXyFVPCDL_qybbds4j3D7X`

None of these has been accepted. WF-01 v4 is an enhancement pass on the V2 picture, not the approved concept rebuild.

## 10. Next steps

1. Rebuild WF-02 with a gradient world, neon emission in the 1–3 range, and a tower framed for 9:16.
2. Rebuild WF-01 with paper-layer shadows and edge highlights. Replace the stick figure with a designed paper cut-out.
3. WF-03: add a spot light on the ticket and a slow dolly.
4. Lookdev each style at its reveal time, check it frame by frame, and ask the user to approve before any 240-frame render.
5. Full-render time check: time one 360×640 frame at 48 spp before committing to 240 frames.
