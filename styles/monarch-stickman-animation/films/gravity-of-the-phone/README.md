# THE GRAVITY OF THE PHONE — WTF-30 #1 production package

A 20.0-second, 9:16 vertical "impossible moment" film in the permanent Monarch Stickman Animation style, built under the WTF-30 doctrine (`studio/editor-brain/MONARCH_WTF30_DOCTRINE.md`). First delivery of the format. Task `EMS-20261014-002`, delivered 2026-10-14 — **current delivery is v3** (same film; v2 added the composed score, the 96-voice sound design and the 3-word moral; v3 adds the vocal-chop hook, kick-synced picture pump, god-rays, afterimages, kinetic type and the 180° world roll on 'ulte.'). v1/v2 remain on Drive and in `records/DELIVERY_RECEIPT_v1.*` / `_v2.*`.

**One law broken: gravity.** A face-down phone becomes the room's planet. Everything — pencil, pages, clock, books, plant, chair, and finally Monarch himself — slides toward it; he hangs from the door frame as a human flag for ten uncut seconds, lets go, lands on the desk, flips the phone face-down, and gravity goes back to normal. Meaning line: **"Phone ulta. Zindagi seedhi."** Moral (v2): **"Warna tum ulte."** — the last word lands upside-down.

## Spine (20.0 s · 6 shots · 600 frames)

| Shot | Time | What happens |
| --- | --- | --- |
| S1 hook | 0.00–2.00 | Frame 1 already in motion: phone face-down buzzing; a pencil rolls **uphill** toward it; the phone flips itself face-up and floods the desk amber. |
| S2 | 2.00–3.80 | 1-frame amber tint-flash cut. Monarch walks in with a book. The clock pendulum leans toward the desk; a page corner lifts. He notices. |
| S3 insert | 3.80–4.60 | ECU: eyes go wide. |
| S4 — the WTF (uncut 10.0 s) | 4.60–14.60 | 4.90 field onset (ring + 0.4-s silence hole first, then the drop boom and the groove). Pages fly, his book is eaten, he lunges for the door frame, grabs the lintel, the clock rips off the wall (ding 1 + bell), books and plant slide, he goes fully horizontal (flag; sweat pulled sideways, flow specks stream to the phone, glow pulses on the beat), ding 2, ding 3, hands slip twice (stutter gates), he looks at the lens (breakdown), lets go, lands on the desk (squash & stretch), slaps the phone face-down, the glow dies (tape-stop), second silence hole, **everything drops flat** (vignette and floor grid release over 0.2 s, falling lines, 1-frame impact tint). He stands on the desk in the E-major relief. |
| S5 meaning | 14.60–17.95 | Push-in. "Phone ulta." (15.40) · "Zindagi seedhi." (16.66) · hot word **seedhi.** turns amber and pops on the VO and on beat 35 (17.15). |
| S6 moral | 17.95–19.70 | The desk again, evaluated at τ = t − 20. "Warna" slams in (18.00), "tum" slides in (18.64), "ulte." spins in **upside-down** (18.98) on the VO — then **the whole world whip-rolls 180°** (19.12–19.38, punch-zoom, 12-sample motion blur) and holds upside-down: the upside-down word is now the only upright thing; a cartoon 'uh-oh' vocal chop lands in the hold. |
| S7 snap-back + loop | 19.70–20.00 | The buzz snaps the world upright and wipes the words (vinyl brake on the score); the pencil is already rolling; frame 600 flows into frame 1 (seam 3.1/255). |

Hook law: no title, no logo, first sound at 0.000 s. On-screen words: 7 (4 meaning + 3 moral = the G-W7 limit). No CTA. 7 shots, 7 transition kinds, 50 beats (max gap 1.45 s), 13 pattern interrupts.

## Style execution

- Hero: locked Monarch stick variant (studio stickman rig `styles/monarch-stickman-animation/src/toon.py`), SHADE bust for the ECU (`shade.py`). New poses only; no redesign.
- World: bone paper, ink geometry, one amber light source (the phone), floor grid that bends toward the phone while the field is on.
- Physics: `src/scene.py` is a deterministic pure-time solver — radial field around the phone, per-prop mass/friction, hero as a pendulum flag off the lintel with slip events; `prop_vel()` drives motion blur and foley.
- Camera: handheld micro-drift, dolly-zoom on the field onset, 2-frame hit on the hot word; v3: kick-synced pump (1.4 % zoom + ≤ 3 px chroma split on every score kick), god-rays + anamorphic streak from the phone, afterimages on the fast moves, ECU rim light, kinetic letter cascade, and the 180° whip-roll with exact corner-covering zoom.
- Type: Montserrat extruded ink; one amber hot word; everything inside the 4:5 safe centre (y 285–1635).
- Sound design (v3): 239 cues over 111 original numpy-synthesised voices — sweat plip + sizzle per drop, field sparkle grains, one ink tick per letter, world-roll whoosh/whomp, snap-back click; earlier: (`audio/cue_ledger.json`) — one cue per physical event; sub drone + grid-locked heartbeat under the flag; two designed silence holes; Urdu VO (`audio/vo_meaning.mp3` meaning line, `audio/vo_moral_b.mp3` moral, both `voice-00`). Mastered with linear gain + true-peak limiter to −14 LUFS (no dynamic loudnorm).
- Score (v2 → v3): `src/music.py`, a procedural 122.4 BPM score locked to the timeline grid; v3 adds the formant **vocal-chop hook** (`vox()`: 'oh · ah-oh · uh · eh-oh' from beat 12, climbing with the arp), octave-jumping arp from bar 3, a reversed 'oh' in the breakdown, a riser into the let-go, a reverse swell into the hot word, a whomp + whoosh on the world roll, the 'uh-oh' in the hold, a vinyl brake into the loop, side-chained plucks and tanh glue. Base design (beat 10 = field onset, beat 35 = hot word, beat 38 = moral). Sections: music-box motif + half-time pulse (hook) → drop boom + groove with climbing 16th arp (field) → breakdown on the lens look → swell, land hit, stutter gates on the slips, tape-stop into the silence hole → E-major pad and plucks (relief) → pings and a descending slide under the moral. Sidechain pump, dotted-eighth ping-pong delay, HP 28 Hz, peak 0.62 before the bus gain (0.85). The noise-floor gate is measured on the sound-design stem (`mix_sfx.wav`), the score is a separate composed bus.

## Accepted delivery

- Master (v3): `THE_GRAVITY_OF_THE_PHONE_WTF30_01_v3.mp4` · 61,573,207 bytes · 20.00 s · 1080×1920 @ 30 fps · H.264 High + AAC 48 kHz
- MD5 `f54c3b295011bb3310ce60f7d710e98b` · SHA-256 `8beef5da5cae88b4a82c6cc6d07b5a95a6d2e1dee56f632530c961495db8c5bd`
- Measured: −14.1 LUFS · TP −1.1 dBTP · LRA 6.7 · loop seam 3.1/255 · silence holes digital silence · SFX-stem floor −50.4 dBFS
- Acceptance: **12/12 measured gates PASS** (`artifacts/gate_receipt.json`) · **28/28 brain freshness PASS** (`artifacts/BRAIN_GATE.txt`)
- Drive: folder https://drive.google.com/drive/folders/1ITMYpBexdmGaALpaf6BlTXNuGNfAFTiQ · v3 file id `1LsfTOubsY6kHeWJatrSj4z71Qxbcpfh1` (Drive md5 verified equal) · v2 `1vzNjW3FeXOMoJ4HDGqM-km5BCKw8IUfp` and v1 `118VOjnmzDmTrTuz8iCsGPwIwWUvJDbPJ` kept
- Exact IDs and checksums: `records/DELIVERY_RECEIPT.{md,json}` (v3) · `records/DELIVERY_RECEIPT_v2.*` · `records/DELIVERY_RECEIPT_v1.*` (history)

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
  --mix ../../../../../build/gotp_mix.wav --out ../../../../../build/THE_GRAVITY_OF_THE_PHONE_WTF30_01_v3.mp4
python3 gate.py --video ../../../../../build/THE_GRAVITY_OF_THE_PHONE_WTF30_01_v3.mp4 --dna ../DNA.json --out ../artifacts
python3 ../../../../../studio/editor-brain/brain/concept.py gate ../DNA.json
```

Final binaries live in `build/` (gitignored) and on Drive; the repository keeps code, DNA, receipts and proofs.
