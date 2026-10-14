# THE GRAVITY OF THE PHONE — WTF-30 #1 production package

A 20.0-second, 9:16 vertical "impossible moment" film in the permanent Monarch Stickman Animation style, built under the WTF-30 doctrine (`studio/editor-brain/MONARCH_WTF30_DOCTRINE.md`). First delivery of the format. Task `EMS-20261014-002`, delivered 2026-10-14 — **current delivery is v2** (same film, upgraded score / sound design / picture FX, plus a 3-word moral). v1 remains on Drive and in `records/DELIVERY_RECEIPT_v1.*`.

**One law broken: gravity.** A face-down phone becomes the room's planet. Everything — pencil, pages, clock, books, plant, chair, and finally Monarch himself — slides toward it; he hangs from the door frame as a human flag for ten uncut seconds, lets go, lands on the desk, flips the phone face-down, and gravity goes back to normal. Meaning line: **"Phone ulta. Zindagi seedhi."** Moral (v2): **"Warna tum ulte."** — the last word lands upside-down.

## Spine (20.0 s · 6 shots · 600 frames)

| Shot | Time | What happens |
| --- | --- | --- |
| S1 hook | 0.00–2.00 | Frame 1 already in motion: phone face-down buzzing; a pencil rolls **uphill** toward it; the phone flips itself face-up and floods the desk amber. |
| S2 | 2.00–3.80 | 1-frame amber tint-flash cut. Monarch walks in with a book. The clock pendulum leans toward the desk; a page corner lifts. He notices. |
| S3 insert | 3.80–4.60 | ECU: eyes go wide. |
| S4 — the WTF (uncut 10.0 s) | 4.60–14.60 | 4.90 field onset (ring + 0.4-s silence hole first, then the drop boom and the groove). Pages fly, his book is eaten, he lunges for the door frame, grabs the lintel, the clock rips off the wall (ding 1 + bell), books and plant slide, he goes fully horizontal (flag; sweat pulled sideways, flow specks stream to the phone, glow pulses on the beat), ding 2, ding 3, hands slip twice (stutter gates), he looks at the lens (breakdown), lets go, lands on the desk (squash & stretch), slaps the phone face-down, the glow dies (tape-stop), second silence hole, **everything drops flat** (vignette and floor grid release over 0.2 s, falling lines, 1-frame impact tint). He stands on the desk in the E-major relief. |
| S5 meaning | 14.60–17.95 | Push-in. "Phone ulta." (15.40) · "Zindagi seedhi." (16.66) · hot word **seedhi.** turns amber and pops on the VO and on beat 35 (17.15). |
| S6 moral + loop | 17.95–20.00 | The desk again, evaluated at τ = t − 20. "Warna" slams in (18.00), "tum" slides in (18.64), "ulte." spins in **upside-down** (18.98) on the VO; the buzz returns at 19.50 and the line snaps out on it; frame 600 flows into frame 1 (seam 3.2/255). |

Hook law: no title, no logo, first sound at 0.000 s. On-screen words: 7 (4 meaning + 3 moral = the G-W7 limit). No CTA.

## Style execution

- Hero: locked Monarch stick variant (studio stickman rig `styles/monarch-stickman-animation/src/toon.py`), SHADE bust for the ECU (`shade.py`). New poses only; no redesign.
- World: bone paper, ink geometry, one amber light source (the phone), floor grid that bends toward the phone while the field is on.
- Physics: `src/scene.py` is a deterministic pure-time solver — radial field around the phone, per-prop mass/friction, hero as a pendulum flag off the lintel with slip events; `prop_vel()` drives motion blur and foley.
- Camera: handheld micro-drift, dolly-zoom on the field onset, 2-frame hit on the hot word.
- Type: Montserrat extruded ink; one amber hot word; everything inside the 4:5 safe centre (y 285–1635).
- Sound design: 170 cues over 96 original numpy-synthesised voices (`audio/cue_ledger.json`) — one cue per physical event; sub drone + grid-locked heartbeat under the flag; two designed silence holes; Urdu VO (`audio/vo_meaning.mp3` meaning line, `audio/vo_moral_b.mp3` moral, both `voice-00`). Mastered with linear gain + true-peak limiter to −14 LUFS (no dynamic loudnorm).
- Score (v2): `src/music.py`, a procedural 122.4 BPM score locked to the timeline grid (beat 10 = field onset, beat 35 = hot word, beat 38 = moral). Sections: music-box motif + half-time pulse (hook) → drop boom + groove with climbing 16th arp (field) → breakdown on the lens look → swell, land hit, stutter gates on the slips, tape-stop into the silence hole → E-major pad and plucks (relief) → pings and a descending slide under the moral. Sidechain pump, dotted-eighth ping-pong delay, HP 28 Hz, peak 0.62 before the bus gain (0.85). The noise-floor gate is measured on the sound-design stem (`mix_sfx.wav`), the score is a separate composed bus.

## Accepted delivery

- Master (v2): `THE_GRAVITY_OF_THE_PHONE_WTF30_01_v2.mp4` · 60,699,977 bytes · 20.00 s · 1080×1920 @ 30 fps · H.264 High + AAC 48 kHz
- MD5 `dc13effd2c86277767b29dec7769bca4` · SHA-256 `e0bc302cf89c4a55a4275cbcd03e13a446e0b2281cada4edddf9ea96bbf603f1`
- Measured: −14.1 LUFS · TP −1.2 dBTP · LRA 6.6 · loop seam 3.2/255 · silence holes −119.8 / −116.3 dBFS · SFX-stem floor −49.7 dBFS
- Acceptance: **12/12 measured gates PASS** (`artifacts/gate_receipt.json`) · **28/28 brain freshness PASS** (`artifacts/BRAIN_GATE.txt`)
- Drive: folder https://drive.google.com/drive/folders/1ITMYpBexdmGaALpaf6BlTXNuGNfAFTiQ · v2 file id `1vzNjW3FeXOMoJ4HDGqM-km5BCKw8IUfp` (Drive md5 verified equal) · v1 file id `118VOjnmzDmTrTuz8iCsGPwIwWUvJDbPJ` kept
- Exact IDs and checksums: `records/DELIVERY_RECEIPT.{md,json}` (v2) · `records/DELIVERY_RECEIPT_v1.{md,json}` (v1 history)

## Package map

- `DNA.json` — concept DNA (slots, signature, law, timeline anchors, beats, cues, measured, delivery).
- `SCRIPT_AND_TOPIC.md` — idea, script, shot list, physics notes.
- `src/scene.py` — timeline (`TL`), props, physics solver, hero state.
- `src/render.py` — frame renderer (`--frame T`, `--sheet`, `--range a b --out seg.mp4`).
- `src/audio.py` — cue sheet synthesiser → `mix.wav` (+ `mix_sfx.wav` stem) + cue ledger; sums the score bus from `music.py`.
- `src/music.py` — procedural score (`render()` → stereo float arrays at 48 kHz; `EVENTS` for the ledger).
- `src/build.py` — concat → linear mastering + true-peak limiter → mux → measure.
- `src/gate.py` — 12 measured gates + 4:5 crop proof; fills `DNA.measured`.
- `artifacts/` — look sheet, contact sheet, event ledger, gate receipt, crop proof, brain gate, measured.
- `audio/` — VO sources (`vo_meaning.mp3`, `vo_moral_b.mp3`) and cue ledger.
- `records/` — post-mortem (experiments / failures / fixes) and delivery receipt.

## Rebuild (from repository root; ~3 min per half on one core)

```bash
pip install --user --break-system-packages numpy pillow scipy imageio-ffmpeg
cd styles/monarch-stickman-animation/films/gravity-of-the-phone/src
python3 render.py --range 0 300 --out ../../../../../build/gotp_seg_a.mp4 &
python3 render.py --range 300 600 --out ../../../../../build/gotp_seg_b.mp4 ; wait
python3 audio.py --out ../../../../../build/gotp_mix.wav --vo ../audio/vo_meaning.mp3 --vo-moral ../audio/vo_moral_b.mp3
python3 build.py --segs ../../../../../build/gotp_seg_a.mp4 ../../../../../build/gotp_seg_b.mp4 \
  --mix ../../../../../build/gotp_mix.wav --out ../../../../../build/THE_GRAVITY_OF_THE_PHONE_WTF30_01_v2.mp4
python3 gate.py --video ../../../../../build/THE_GRAVITY_OF_THE_PHONE_WTF30_01_v2.mp4 --dna ../DNA.json --out ../artifacts
python3 ../../../../../studio/editor-brain/brain/concept.py gate ../DNA.json
```

Final binaries live in `build/` (gitignored) and on Drive; the repository keeps code, DNA, receipts and proofs.
