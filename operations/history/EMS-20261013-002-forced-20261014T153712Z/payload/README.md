# WF-04 · Monarch Face 🔥👑 · Chaos Video 1 v2

Current source and QA records for task `EMS-20261013-002`. Rendered media is **not** committed to Git: local copies live in `.runtime/deliverables/`; the authoritative Drive master is [MONARCH_CHAOS_VIDEO_1_MASTER_v2.mp4](https://drive.google.com/file/d/10nBp4Nsr3FlqxTOCKoU2cu5N44PYz-7M/view?usp=drivesdk) (MD5 `f5d09353fab1ae7d52fb0a906f4f5598`).

**Layout (2026-10-14 cleanup):** the ten source plates and the canonical engine live in `styles/monarch-face-chaos/` (`plates/`, `src/`). `src/` here is the **runner copy** the renderer is executed from; it and `styles/monarch-face-chaos/src/` are kept byte-identical. The duplicated `payload/plates/` copy was deleted because it doubled ~20 MB in the worktree and pushed the workspace over the ~128 MB snapshot cap (see `docs/STORAGE_AND_MATERIALIZATION.md`). Both copies of the engine now locate the repository root by walking up, so either can be run.

Run the renderer from a full worktree:

```bash
bash tools/bootstrap_env.sh                     # numpy/Pillow/scipy/cv2/ffmpeg
python3 tools/materialize.py full               # plates + ref audio present
python3 workflows/current/payload/src/build_chaos_video1.py
```

The payload also carries the `21/21` gate report, delivery receipt and visual inspection sheets. Download the [reproducible source ZIP](https://drive.google.com/file/d/1Devm-wKU3QZ5DTXgL5pHV2Udqxl6S59f/view?usp=drivesdk) to restore the exact delivered source, including the audio WAV. Source and current IDs are promoted to `styles/monarch-face-chaos/`.

Both earlier v2 revisions remain accessible as `_v2_pre_motion_boost` and `_v2_pre_flash_fix` Drive files. Its shared IDs are preserved in `DELIVERY_RECEIPT.json`.


Both earlier v2 revisions remain accessible as `_v2_pre_motion_boost` and `_v2_pre_flash_fix` Drive files. Its shared IDs are preserved in `DELIVERY_RECEIPT.json`.
