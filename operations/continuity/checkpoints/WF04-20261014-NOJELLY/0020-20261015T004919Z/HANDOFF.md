# Resume capsule — WF04-20261014-NOJELLY

**Status:** `rendering`  
**Title:** Monarch main-reference full 2.5D recreation V1 — review  
**Style:** `monarch-face-chaos`  
**Checkpoint sequence:** 20  
**Last checkpoint:** 2026-10-15T00:49:19Z

## Goal

Deliver the user-approved full-length limited 2.5D whole-character recreation of the confirmed main reference, with exact original music and honest method/quality scope.

## Acceptance criteria

- [ ] Complete 1332-frame /44.4s 2.5D picture edit using the correct main reference, not the other chat chair/cables film.
- [ ] Use new whole owner-character imagery and bounded connected image-based rigging; no reference-actor footage or face sticker on that actor.
- [ ] Preserve original reference AAC payload and decoded audio unchanged, including its tail.
- [ ] Rigid facial core/props, anchored boots, image/encoded-frame inspection; no eye/mouth morph used as natural performance.
- [ ] Crown above MONARCH STUDIO ending.
- [ ] Clearly label 2.5D limitations; no exact 3D/natural AI-performance or user likeness-approval claim.

## Exact next action

Run polish_full_v2.py in a fresh V2 cache, then conform_reference_audio.py using V1 as the already-verified canonical-audio source. Verify 1332 frames, same AAC/PCM, byte-identical reuse of all 32 unaffected chunks, and preserved V1. Inspect encoded patched frames and deliver the FULL V2, not a test.

## Running processes

- `monarch-original-3d-motion-check-30451e5f` — Vault sample-frame render — completed
- `monarch-finish-export-from-saved-3287176f` — Completed 44.4s draft export — completed
- `monarch-corrected-joint-motion-r-ce4914d5` — Corrected 3D QA samples — completed
- `monarch-native-motion-frames-431c3ea6` — Native skinning-space QA samples — completed
- `monarch-full-44-4-second-draft-e-767b7d57` — Initial full export attempt — failed
- `monarch-crown-outro-0ee7e859` — Native 3.6s crown outro plus original sound — completed
- `main-reference-timing-and-music--b24e5955` — Canonical main reference frame/audio analysis — completed
- `monarch-full-2-5d-recreation-05806fcb` — Complete main-reference 1332-frame 2.5D picture + exact original audio mux — completed

## Recovery command

```bash
python3 tools/continuity.py resume
```

## Durable evidence

- Active state: `workflows/current/ACTIVE_TASK.json`
- Hash-chained action journal: `workflows/current/JOURNAL.jsonl`
- Visible user/assistant transcript: `workflows/current/CHAT_TRANSCRIPT.jsonl`
- Active payload only: `workflows/current/payload/`
- Latest checkpoint package: `operations/continuity/checkpoints/WF04-20261014-NOJELLY/0020-20261015T004919Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
