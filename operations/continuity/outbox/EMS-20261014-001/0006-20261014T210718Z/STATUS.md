# Checkpoint 0006-20261014T210718Z

- Task: `EMS-20261014-001`
- Status: `rendering`
- Title: WF-02 Splinter 3D reference-based Urdu-English film
- Style: `monarch-zackd-3d`
- Time: 2026-10-14T21:07:18Z
- Journal head: `82d8776fa88d02a43db906efc96ed736d41ff1ac98ec4f1346da27b908a5c0c4`

## Completed since prior checkpoint

Render ongoing past midpoint; edit source remains frozen; final MP4 quality gate and safe permanent-style promotion helper prepared.

## Exact next action

Wait for registered render process wf-02-3d-video-render-af896fc1. On success: .venv/bin/python workflows/current/payload/splinter-v2/src/assemble.py --reuse-audio --out .runtime/wf02-master; then gate.py on final MP4. Inspect QC sheet, upload/hash-check master and source to folder 1SqX_S44eVowdTAyBVzAFerYUYFJd6NtF, write DELIVERY_RECEIPT.json, execute PROMOTE_WF02.py and continuity.py complete --destination styles/monarch-zackd-3d/projects. Refresh manifest and run validation/tests after promotion. Never run studio clean all.

## Cross-platform rule

The same factual status must be applied to GitHub, Google Drive, Notion, Linear and Google Docs. Remote IDs/results are recorded in `SYNC.json`; no platform is silently skipped.
