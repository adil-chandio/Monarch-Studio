# THE GRAVITY OF THE PHONE — WTF-30 #1 production package

A 20.0-second, 9:16 vertical "impossible moment" film in the permanent Monarch Stickman Animation style, built under the WTF-30 doctrine (`studio/editor-brain/MONARCH_WTF30_DOCTRINE.md`). First delivery of the format. Task `EMS-20261014-002`, delivered 2026-10-14.

**One law broken: gravity.** A face-down phone becomes the room's planet. Everything — pencil, pages, clock, books, plant, chair, and finally Monarch himself — slides toward it; he hangs from the door frame as a human flag for ten uncut seconds, lets go, lands on the desk, flips the phone face-down, and gravity goes back to normal. Meaning line: **"Phone ulta. Zindagi seedhi."**

## Spine (20.0 s · 6 shots · 600 frames)

| Shot | Time | What happens |
| --- | --- | --- |
| S1 hook | 0.00–2.00 | Frame 1 already in motion: phone face-down buzzing; a pencil rolls **uphill** toward it; the phone flips itself face-up and floods the desk amber. |
| S2 | 2.00–3.80 | 1-frame amber tint-flash cut. Monarch walks in with a book. The clock pendulum leans toward the desk; a page corner lifts. He notices. |
| S3 insert | 3.80–4.60 | ECU: eyes go wide. |
| S4 — the WTF (uncut 10.0 s) | 4.60–14.60 | 4.90 field onset (ring + 0.4-s silence hole first). Pages fly, his book is eaten, he lunges for the door frame, grabs the lintel, the clock rips off the wall (ding 1), books and plant slide, he goes fully horizontal (flag), ding 2, ding 3, hands slip twice, he looks at the lens, lets go, lands on the desk, slaps the phone face-down, the glow dies, second silence hole, **everything drops flat**. He stands on the desk and looks at the fallen room. |
| S5 meaning | 14.60–18.20 | Push-in. "Phone ulta." (15.40) · "Zindagi seedhi." (16.66) · hot word **seedhi.** turns amber and pops on the VO (17.15). |
| S6 loop | 18.20–20.00 | The desk again, evaluated at τ = t − 20: the buzz returns at 19.30 and frame 600 flows into frame 1 (seam 3.1/255). |

Hook law: no title, no logo, first sound at 0.000 s. On-screen words: 4. No CTA.

## Style execution

- Hero: locked Monarch stick variant (studio stickman rig `styles/monarch-stickman-animation/src/toon.py`), SHADE bust for the ECU (`shade.py`). New poses only; no redesign.
- World: bone paper, ink geometry, one amber light source (the phone), floor grid that bends toward the phone while the field is on.
- Physics: `src/scene.py` is a deterministic pure-time solver — radial field around the phone, per-prop mass/friction, hero as a pendulum flag off the lintel with slip events; `prop_vel()` drives motion blur and foley.
- Camera: handheld micro-drift, dolly-zoom on the field onset, 2-frame hit on the hot word.
- Type: Montserrat extruded ink; one amber hot word; everything inside the 4:5 safe centre (y 285–1635).
- Sound: 150 cues over 78 original numpy-synthesised voices (`audio/cue_ledger.json`) — one cue per physical event; sub drone + heartbeat under the flag; two designed silence holes; Urdu VO (`audio/vo_meaning.mp3`, `voice-00`). Mastered with linear gain + true-peak limiter to −14 LUFS (no dynamic loudnorm).

## Accepted delivery

- Master: `THE_GRAVITY_OF_THE_PHONE_WTF30_01.mp4` · 62,733,035 bytes · 20.00 s · 1080×1920 @ 30 fps · H.264 High + AAC 48 kHz
- MD5 `824a8133bde468c8a0a027d12da3081a` · SHA-256 `1c62246ae9bfb2987476141d7021e658bcb72b7a4a80614e5f5e8f0354f2fa61`
- Measured: −14.2 LUFS · TP −1.1 dBTP · LRA 7.4 · loop seam 3.1/255 · silence hole −119.8 dBFS
- Acceptance: **12/12 measured gates PASS** (`artifacts/gate_receipt.json`) · **28/28 brain freshness PASS** (`artifacts/BRAIN_GATE.txt`)
- Drive: folder https://drive.google.com/drive/folders/1ITMYpBexdmGaALpaf6BlTXNuGNfAFTiQ · file id `118VOjnmzDmTrTuz8iCsGPwIwWUvJDbPJ` (Drive md5 verified equal)
- Exact IDs and checksums: `records/DELIVERY_RECEIPT.{md,json}`

## Package map

- `DNA.json` — concept DNA (slots, signature, law, timeline anchors, beats, cues, measured, delivery).
- `SCRIPT_AND_TOPIC.md` — idea, script, shot list, physics notes.
- `src/scene.py` — timeline (`TL`), props, physics solver, hero state.
- `src/render.py` — frame renderer (`--frame T`, `--sheet`, `--range a b --out seg.mp4`).
- `src/audio.py` — cue sheet synthesiser → `mix.wav` + cue ledger.
- `src/build.py` — concat → linear mastering + true-peak limiter → mux → measure.
- `src/gate.py` — 12 measured gates + 4:5 crop proof; fills `DNA.measured`.
- `artifacts/` — look sheet, contact sheet, event ledger, gate receipt, crop proof, brain gate, measured.
- `audio/` — VO source and cue ledger.
- `records/` — post-mortem (experiments / failures / fixes) and delivery receipt.

## Rebuild (from repository root; ~3 min per half on one core)

```bash
pip install --user --break-system-packages numpy pillow scipy imageio-ffmpeg
cd styles/monarch-stickman-animation/films/gravity-of-the-phone/src
python3 render.py --range 0 300 --out ../../../../../build/gotp_seg_a.mp4 &
python3 render.py --range 300 600 --out ../../../../../build/gotp_seg_b.mp4 ; wait
python3 audio.py --out ../../../../../build/gotp_mix.wav --vo ../audio/vo_meaning.mp3
python3 build.py --segs ../../../../../build/gotp_seg_a.mp4 ../../../../../build/gotp_seg_b.mp4 \
  --mix ../../../../../build/gotp_mix.wav --out ../../../../../build/THE_GRAVITY_OF_THE_PHONE_WTF30_01.mp4
python3 gate.py --video ../../../../../build/THE_GRAVITY_OF_THE_PHONE_WTF30_01.mp4 --dna ../DNA.json --out ../artifacts
python3 ../../../../../studio/editor-brain/brain/concept.py gate ../DNA.json
```

Final binaries live in `build/` (gitignored) and on Drive; the repository keeps code, DNA, receipts and proofs.
