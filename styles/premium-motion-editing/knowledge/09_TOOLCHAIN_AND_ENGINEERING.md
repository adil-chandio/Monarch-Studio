# 09 · Toolchain, implementation and practical strategies

## Tools actually used

- **Git / gh:** inspect local status and history, recover immutable source blobs, publish code through the tracked branch. GitHub operations use the configured CLI; never request credentials in chat.
- **Google Drive connector:** locate real files/folders, download source, upload master/recovery and independently verify size/MD5. Do not guess IDs from filenames.
- **Python / NumPy / OpenCV / Pillow / SciPy:** scene extraction, cleanup, source-frame interpolation, image-space depth maps, typography, audio analysis/mixing and review images.
- **imageio-ffmpeg:** obtain the working FFmpeg binary instead of assuming rendering is impossible because a system `ffmpeg` executable is missing.
- **Arena process tools:** start a long render once, record its ID, wait for completion and recover its actual state after a transport error.
- **File viewer:** inspect contact sheets and present the actual final artifact only after it exists.

The V5/V6 correction did not generate new image slides or new speech. Blender/rigged full-3D generation was not secretly used. Optional future tools must be labeled optional until they are actually installed, run and tested.

## Pinned case dependencies

The case used NumPy 2.4.6, Pillow 12.3.0, SciPy 1.17.1, imageio-ffmpeg 0.6.0 and OpenCV headless 5.0.0.93. Its bundled FFmpeg reported a 7.x build. Preserve exact case requirements for reproduction; test any upgrade before calling it equivalent.

## Reusable versus historical code

`src/` contains the approved reusable policy, project compositor, generic near/far motion and output verifier. It is data-driven and contains no frozen Einstein script, voice or shot geometry. `templates/` starts empty on purpose: a new brief needs actual script/media decisions.

`projects/einstein-flow-state/versions/v5` and `v6` preserve the original implementations, timelines, selected speech, font licenses, QA and delivery identities. Running those files is historical replay, not a new production. V6's old caption renderer is retained only there; it is absent from the standard production compositor.

## Safe implementation details

Use per-project caches, not a global title cache that can leak the previous project's words. Reject unreadable type overflow, invalid timing, missing media, unsupported framing and unreviewed rights. Encode to a partial filename, verify the frame budget, then atomically expose the completed filename. A receipt must match the actual output hash before a cached render is reused.

Hashes must include relevant source, audio, timeline, profile and effect code. A filename is not sufficient cache identity. Preserve existing outputs on input changes: write a versioned output rather than silently replacing a delivered file.

## Honest support envelope

The provided generic adapter is for the tested 1080×1920 / 30fps portrait family with prepared motion clips and mixed audio. Longer scenes, other aspect ratios or RTL text require tested extensions and a storage/performance plan. It is a compositor and workflow, not a magical asset generator from an empty topic field.

## Foundation tooling corrections

The first PDF export assumed an unavailable system italic font. Documentation fonts/license are now bundled; the already licensed Barlow italic supplies the italic face. The initial inventory pass also evaluated its self-reference before first writing it; post-write existence is now rechecked. These were documentation/audit fixes only—no video, source scene or selected speech was regenerated. Further details are preserved in `records/FOUNDATION_INCIDENTS.md`.
