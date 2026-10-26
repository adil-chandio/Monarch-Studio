# WF-05 · Engine-check demo (capability proof)

**File:** `WF05_ENGINE_CHECK_demo.mp4` · **6.0 s** · 1080 × 1920 · 30 fps · H.264 High (yuv420p, bt709) + AAC 48 kHz stereo
**Size:** 6,086,106 bytes · **MD5** `85274e610d7141cb64bada011352a4ef` · **SHA-256** `2b89a2d838aed279d058b58d9006e9d4c66855aeb83b852eb01555195cb327ac`

## What this is

A real, decodable clip produced **inside this sandbox** by the repository's own approved compositor
(`styles/premium-motion-editing/src/render_project.py` + `motion.py`) with the binding policy from
`data/approved-profile.json`:

| Policy item | In this clip |
|---|---|
| Integrated kinetic headings | `ENGINE CHECK` / `NOT A SLIDESHOW` / `DELIVERY PATH OK` |
| V6 bottom caption pills | absent (renderer for them does not exist in production module) |
| Active-word lower strip | absent |
| Subtitle mode | `off` |
| 2.5D near/far camera + roll | applied per shot (`motion.camera`) |
| Transitions | depth push → diagonal whip → feathered cut (`motion.cut`) |
| Slideshow-free claim | measured, see `motion_evidence` below |

## What this is NOT

- **Not the user's reference video** and not derived from it. Plates are procedurally generated
  "paper + ink geometry" footage (real temporal motion, encoded to H.264 and decoded back through OpenCV).
- **Not a topic deliverable**, not narrated, not a Drive delivery. It exists to prove the pipeline runs here.

## Verification actually performed

Receipt: `workflows/current/payload/WF05-20261026-REF-INTAKE/engine-check/ENGINE_CHECK_RECEIPT.json`

```
Duration: 00:00:06.00, bitrate: 8114 kb/s
Video: h264 (High) (avc1), yuv420p(tv, bt709), 1080x1920, 30 fps
Audio: aac (LC), 48000 Hz, stereo, 191 kb/s
decoded_frames = 180 / 180 expected  (full decode, no dropped/corrupt frames)
audio peak = -2.85 dBFS
```

Temporal-motion evidence (mean |Δluma| 0–255 between decoded frames):

| window | Δ | note |
|---|---|---|
| 1 frame apart (control) | 1.48 | camera never freezes |
| 0.5→0.9 s | 4.76 | plate A subject orbit |
| 2.6→3.0 s | 10.71 | plate B bars + travelling dot |
| 4.6→5.0 s | 15.59 | plate C triangle rotation |
| 2.05→2.12 s | 3.86 | depth-push / diagonal-whip hand-off |

## Reproduce

```bash
python3 workflows/current/payload/WF05-20261026-REF-INTAKE/engine-check/render_engine_check.py
```

Deterministic plates (seeded), ~48 s wall clock on the 2-vCPU sandbox.

## Previews

`previews/frame-1.4.png`, `frame-3.5.png`, `frame-5.3.png` — one decoded frame from each shot.
