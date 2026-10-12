# TOOLCHAIN · Monarch Zack-D 3D Power (WF-02)

Current as of the last session. Re-verify after any sandbox reset.

## Environment (rebuild in a new clone or after reset)

```bash
tools/bootstrap/setup_3d.sh          # /tmp/venvs/render, /tmp/venvs/blender (bpy 4.3.0), /tmp/stublib; prints BPY_OK
```

- Blender: `bpy==4.3.0`, Python 3.11, Cycles CPU. Needs the stub `.so` files for X11/GL and `sys.setdlopenflags(os.RTLD_LAZY | os.RTLD_GLOBAL)` (already in the script). Run with `LD_LIBRARY_PATH=/tmp/stublib`.
- numpy, pillow, imageio-ffmpeg (ffmpeg v7.0.2 binary, not on PATH), scipy in `/tmp/venvs/render`.
- Scene code: `tools/render/blender-vertical/wf_scenes.py` (shared by WF-01, WF-02, WF-03 builders). It was rebuilt from memory after a reset, so verify it against the lookdev stills before trusting it.

## Commands that work

```bash
# lookdev still at a reveal time (270x480, 32 spp: about 3 s per frame)
LD_LIBRARY_PATH=/tmp/stublib /tmp/venvs/blender/bin/python tools/render/blender-vertical/wf_scenes.py --wf 02 --lookdev 9.5 --res 270x480 --samples 32 --out /tmp/wf02_9p5.png

# full render (240 frames at 24 fps). Timing NOT yet measured at 360x640 / 48 spp. Measure one frame first.
LD_LIBRARY_PATH=/tmp/stublib /tmp/venvs/blender/bin/python tools/render/blender-vertical/wf_scenes.py --wf 02 --out /tmp/wf02_frames --res 360x640 --samples 48 --frames 0-239
```

Scene facts from the code: cube k appears at t = k, with a bounce drop. Text reveal runs 6.5 to 8.5 s. Cut boundaries at 0, 2.5, 5.0, 7.5 s (four cameras). Tower spacing 1.25 m. Cyan emission 1.2 to 3.4 (not above 3 at the end of the reveal, keep it there). World colour (0.22, 0.27, 0.36) strength 1.1. Key area light 2600 W, rim point 1500 to 2500 W, fill point 2500 W.

## Encode and sound

- Encode: ffmpeg, libx264, CRF 21, 24 fps, 1080×1920 for the final (lookdev is 270×480). Check the CRF choice against file size (CRF 17 with heavy grain gave 103 MB).
- Sound: numpy procedural, written as WAV. Scripts from the first attempt are lost. Rebuild per PIPELINE step 9.
- Narration: the voice WAVs (voice-00 demo, voice-02 ur-PK) are NOT in the repo. They are in the payload snapshot on Drive (id `1W5CaGUNpeM8oGs2SO60KRhQ_y2Kc5Dkl`, see `projects/tumhari-reserved-seat-3d/ARTIFACTS.md`). Fetch on demand, and record new Drive IDs in VIDEO_LOG.

## Access and blockers

- HuggingFace and every mirror: blocked. Do not bypass.
- apt (deb.debian.org): blocked. Use the stub libraries.
- uploads.github.com: blocked. GitHub Releases cannot hold media. Use Drive.
- Google Drive connector: call `list_connector_tools` first in each turn, or uploads fail as "unavailable".
- Drive links opened from a phone may ask for sign-in. Share the final file "anyone with the link" only after the user approves.
- MuAPI / Kling / Luma keys: the user must supply them. Never store keys in the repo.
