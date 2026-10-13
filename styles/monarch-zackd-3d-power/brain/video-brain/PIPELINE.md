# PIPELINE · Monarch Zack-D 3D Power (WF-02) · version 1

Follow in order. Each step ends with a log entry (`tools/brain.py session`), and any failure becomes a `problem` entry.

1. **Resume.** `python3 tools/brain.py resume monarch-zackd-3d-power`. Read MINDSET, NEXT_LEVEL and open problems before changing anything.
2. **Timeline check.** Confirm cut boundaries (0, 2.5, 5.0, 7.5 s), the cube schedule (cube k at t = k), and the text reveal (6.5 to 8.5 s). If you change any of these, log a strategy.
3. **Scene build.** Use `build_wf02` / `update_wf02` in `tools/render/blender-vertical/wf_scenes.py`. Change one variable at a time.
4. **Lookdev at three times.** 3.0 s (cube build), 7.5 s (text mid-reveal), 9.5 s (full). Use 270×480 and 32 spp.
5. **Review.** Score each still against the MINDSET list (chrome reads, neon in range, text legible, motion every second, no geometry tells). A still that fails any item is not accepted. Log the review in VIDEO_LOG with status `reviewed` or `rejected`.
6. **Timing.** Render one frame at 360×640 and 48 spp. Record the time in VIDEO_LOG before starting a 240-frame run.
7. **Full frames.** Render 240 frames at 24 fps to a scratch folder outside the repo. Check that the job is resumable (existing frames are skipped).
8. **Frame QA.** Sample one frame per second and every cut boundary. Look for flicker, clipping, floor edges and text cut off at the top.
9. **Sound.** Procedural numpy: a 1 Hz pulse matching the cube rhythm, a whoosh on each cut, and a low bed under the text reveal. Keep LUFS near -16 and true peak under -1 dB.
10. **Mux narration.** Use voice-02 (ur-PK) for the accent-corrected version. Check that the narration lands inside the cut timing.
11. **Encode.** ffmpeg libx264, CRF 21, 24 fps, 1080×1920 final. Record size and SHA-256.
12. **Upload and record.** Upload the final to Drive. Run `tools/archive/record_artifact.sh` for the project, and add a VIDEO_LOG entry with the Drive ID.
13. **Promote.** Move any new skill to SKILLS.md, any new lesson to PROBLEMS, and update NEXT_LEVEL.
