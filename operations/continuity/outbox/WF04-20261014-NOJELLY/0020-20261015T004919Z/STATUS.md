# Checkpoint 0020-20261015T004919Z

- Task: `WF04-20261014-NOJELLY`
- Status: `rendering`
- Title: Monarch main-reference full 2.5D recreation V1 — review
- Style: `monarch-face-chaos`
- Time: 2026-10-15T00:49:19Z
- Journal head: `92273f8d7c80c55f66e40976e995633185a03691f3fbe72e6873e11f7d9e39b5`

## Completed since prior checkpoint

Targeted V2 polish previews accepted internally: prop background smear removed, face pulse clipping controlled without new face/pose design. Five shots /159 frames to patch; 32 V1 chunks verified and retained. Full V2 export next, original music unchanged.

## Exact next action

Run polish_full_v2.py in a fresh V2 cache, then conform_reference_audio.py using V1 as the already-verified canonical-audio source. Verify 1332 frames, same AAC/PCM, byte-identical reuse of all 32 unaffected chunks, and preserved V1. Inspect encoded patched frames and deliver the FULL V2, not a test.

## Cross-platform rule

The same factual status must be applied to GitHub, Google Drive, Notion, Linear and Google Docs. Remote IDs/results are recorded in `SYNC.json`; no platform is silently skipped.
