# Process log: tumhari-reserved-seat-3d

How the work was done, in order. Each entry: what was done, the tool or command, the outcome, and where the output lives. Entries marked **[reconstructed]** were rebuilt from the session record after sandbox resets. Everything else was logged as it happened.

Going forward, every working turn appends an entry here (phase, action, command or tool, outcome, output path). Do not rewrite older entries. Add corrections as new entries.

## Phase 1: voice and first test concept (WF-01 / WF-03 / WF-02 v1)

1. **Source material.** Read the Monarch voiceover folder on Google Drive (`1LTkHpkEUFSui8Lqyy8I0j5-1AceSziWX`) and the voice file `monarch voice.aac` (`1tOhhtG0-IJwswGwqDVJ6nDm7EeVUUDgi`). Tool: `google_drive` connector (enabled with `list_connector_tools`).
2. **Script of record.** Kept in `styles/monarch-stickman-animation/films/tumhari-reserved-seat/SCRIPT_AND_TOPIC.md` (74 s, Roman Urdunglish).
3. **Voice.** Demo voice is platform voice-00 (`add_voice` audition). Accent correction is ur-PK voice-02. Outputs: `workflows/current/payload/tumhari_vo/vo_part1..3.wav` (voice-00) and `vo_ur_part1..3.wav` (voice-02). Voice cloning of the user's own voice was not done: it needs an allowed registry and a voice sample from the user.
4. **WF-01 V2 (stickman paper style).** Existing accepted package in `styles/monarch-stickman-animation/films/tumhari-reserved-seat-v2/` (30 fps). Silent base `WF01_test_10s.mp4`.
5. **WF-03 V2 (noir).** Existing package in `styles/monarch-noir-film/films/tumhari-reserved-seat-v2/` (24 fps).
6. **WF-02 v1 (Zack-D 3D).** `render_test10s.py` (Mitsuba-style demo), 240 frames. Result: camera too close, cropped, noisy. Superseded.
7. Muxed `vo_ur_part1.wav` (first 10 s) into the three v1 tests. Uploaded to Drive folder `1LTkHpkEUFSui8Lqyy8I0j5-1AceSziWX`.

## Phase 2: concept lock and 9:16 target

8. User approved three distinct concepts (locked, see DECISIONS.md). User asked for all three in 9:16 vertical.
9. Rejected: WF-01 and WF-03 looking the same; WF-02 looking like a plain ball on a face. Each style now needs its own editing, animation and sound.

## Phase 3: WF-02 v2 (voxel 3-D text, one cube per second)

10. Wrote `render_v2_power.py` (640×360, 28 spp, 24 fps, 240 frames, cut boundaries 0 / 2.5 / 5.0 / 7.5 s) and `make_sound_wf02.py` (numpy, procedural sound).
11. Test renders at frames 30, 110, 200, then the full render, encode and Drive upload. Final: `WF-02_zackd3d_v2_10s.mp4`, then `WF-02_zackd3d_v2_30HRS_10s.mp4` (Drive `16pfe4ZwNfSE4Fgj0ktTZniRN1EcjmLJ9`).
12. **Lost in a sandbox reset:** both scripts and the 10 s MP4 working set. Not recoverable from this sandbox. Only the Drive copy of the final MP4 survives.

## Phase 4: WF-03 and WF-01 sound pass, WF-01 v4 enhancement

13. Wrote `make_sound_wf01_wf03.py` (procedural sound, numpy), muxed narration, uploaded to Drive. WF-03 sound pass on the old picture (Drive `1SmMEo2lhc5EXyFVPCDL_qybbds4j3D7X`).
14. Wrote `enhance_wf01.py` (args `src audio out`, about 80–100 s for 300 frames at 1080p, threaded numpy). Settled on CRF 21 and grain 2.4 (20.9 MB). CRF 17 with grain 3.2 gave 103 MB. Final: `WF-01_paper_v4_enhanced_10s.mp4` (Drive `1puZyLWIX4YG43iX2G0u86hJT16_3_3ob`). This is an enhancement pass on the V2 picture, not the approved concept rebuild.

## Phase 5: Blender Cycles pipeline (9:16 target)

15. **Blender setup.** `pip install bpy==4.3.0` into `/tmp/venvs/blender` (py3.11). Import failed on missing X11/GL sonames. `apt` is blocked (`deb.debian.org`). Built stub `.so` files in `/tmp/stublib` with `gcc -shared -Wl,-soname`. `import bpy` then worked with `sys.setdlopenflags(os.RTLD_LAZY | os.RTLD_GLOBAL)`. Output: `BPY_OK 4.3.0`.
16. **Smoke test.** `workflows/current/payload/blender_test/smoke.py`: Cycles CPU, 540×960, 32 spp, about 11 s per frame. Lost in a reset. Result is in the runbook.
17. **Runbook.** Blender headless section committed to `docs/runbooks/LOCAL_NO_API_RENDER.md` (commit `240edd3`).
18. **Scene builders.** `wf_scenes.py` with `build_wf01/02/03` and `update_wf0x(t, S)`. Lost in a reset. Rebuilt from memory **[reconstructed]** and committed as `tools/render/blender-vertical/wf_scenes.py`. Note: the rebuilt version carries the lookdev patches, so it may differ from the original.
19. **Lookdev iterations** (270×480, 24–32 spp, stills only). Findings:
    - WF-02: cubes appear only after t = k, so t = 3.5 shows four cubes. Text reveal starts at 6.5 s. Chrome looked black under a dark world. Neon emission above about 3 blew out to white blocks under AgX. Spacing changed to 1.25 for legibility.
    - WF-03: volume haze 0.022 too noisy. 0.004–0.007 is usable. Point lamp 900 W too weak, 4200 W lit the bench. Ticket moved from a floating 1.3 m rise to lying flat at z ≈ 0.73.
    - WF-01: world 0.9 plus area 900 washed out. Raking area light (size 2.5, energy 380) gave readable paper layers.
20. **Status at the end of Phase 5:** all three stills are test quality. Not accepted. No 240-frame render was started.
21. **Lookdev sheet:** `workflows/current/payload/blender_vertical/lookdev_status.png` (in the payload snapshot).

## Phase 6: repository hygiene and vendoring

22. Found after a reset that local `HEAD` had fallen back to `7909bde` while origin was at `240edd3`. Backed up the tracked diff and untracked folders, then fast-forwarded with `git merge --ff-only`. Never hard-reset.
23. **Vendor repos.** All requested repos are pinned as submodules under `vendor/`: effectcraft, react-bits, open-generative-ai, OpenMontage, browser-use, cc-switch, Agent-Reach, Scrapling, awesome-opus5-5-videos, FreeCAD. The FreeCAD short pin `ec6852e` could not be fetched by SHA, so it was re-pinned to `23a5e34`.
24. **Full source is not in the tree.** Populated trees are about 440 MB and over 12,000 files, above the snapshot cap. Working trees are released by default and restored on demand: `tools/vendor/materialize.sh`.
25. **Skills.** 1,493 text skill files (about 10 MB) copied to `docs/skills/vendored/`, with `PROVENANCE.md` (pins and licences). cc-switch UI source excluded.
26. **Bootstrap.** `tools/bootstrap/setup_3d.sh` rebuilds the render venvs and stub libraries and verifies `BPY_OK`. Verified in this session.

## Phase 7: project archive (this category)

27. Created `projects/` as a category. Each project has its own folder with this log, tools, decisions, skills, artifacts index and resume capsule.
28. **Publish attempt.** Tried a GitHub Release for the 12.6 MB payload tarball. Upload failed: `uploads.github.com` and `objects.githubusercontent.com` are blocked in this sandbox. Deleted the empty release.
29. **Drive upload.** Payload snapshot uploaded to the monarch voiceover folder. Drive id `1W5CaGUNpeM8oGs2SO60KRhQ_y2Kc5Dkl`. Size matches (12,657,692 bytes). Recorded in `ARTIFACTS.md` with SHA-256.
30. **Workspace cleanup.** The local `workflows/current/payload/` is removed from the working tree after the Drive copy is verified. The tarball is kept in `/tmp/restore_backup_4/` as well.

## Known gaps (as of this log)

- The verbatim chat is not fully captured. `workflows/current/CHAT_TRANSCRIPT.jsonl` holds only partial visible turns. This log is the authoritative record of work, not a word-for-word chat export.
- WF-02 v2 render and sound scripts, `test10s/` working set, smoke test: lost in resets. Drive holds the final MP4s.
- The rebuilt `wf_scenes.py` may not match the original line by line.
- No film has passed a frame-level premium check.

## Phase 8: workspace budget and chat record

31. **Workspace check.** The Arena workspace root `/home/user` holds only `Monarch-Studio` and dotfiles (`.cache` is outside snapshots). The whole workspace is the repo. Its tracked content is on GitHub.
32. **Budget.** Worktree was 92 MB and `.git` 81 MB (limit 128 MB, 10,000 files). `git gc` saved about 1 MB, because the `.git` pack (67 MB) is history. `tools/materialize.py compact` brought the worktree to 54 MB and 1,973 files. `projects/` was added to the compact set first, so resume records stay local.
33. **Validator.** In compact mode, `studio.py validate` failed on WF-01 required paths that are tracked but omitted locally. Changed the check so a required path counts as present when it exists or is tracked in Git. Result: 19 pass, 0 errors.
34. **Chat record.** Wrote `CHAT_LOG.md`: a turn-by-turn summary of the user's requests and the outcomes. It is a summary, not a verbatim transcript.
