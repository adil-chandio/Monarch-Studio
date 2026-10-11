# TUMHARI RESERVED SEAT — WF-01 production package

A 74-second, 16:9 landscape social film in the permanent Monarch Stickman Animation style. It uses the shared `voice-00` narration and master timeline from task `EMS-20261011-002`; its picture and soundtrack are independently authored for WF-01.

## Style execution

- Hero: locked SHADE hooded black-suit character on the existing three-dimensional pose rig.
- World: warm bone paper, ink geometry, split timelines, kinetic data, extruded Montserrat headlines, physical ticket/seat motifs.
- Core device: two paths at 11:47 PM; paper punches accumulate into a thirty-hour graph.
- Colour arc: red warning → indigo choice → cyan timer → green earned result → gold owned seat.
- Motion: deterministic pure-time rendering; micro-parallax, paper grain, kinetic type and character secondary motion keep every second alive.
- Sound: original procedural 94 BPM score, true-stereo paper/pencil ASMR, timer/phone/calendar/ticket cues, sidechain under narration.
- No stock footage, stock music, templates, or copied scenes.

## Package map

- `SCRIPT_AND_TOPIC.md` — one shared master script and reasoning.
- `MASTER_TIMELINE.json` — 34 voice-led beats, 74.0-second picture lock.
- `DNA.json` — selected concept DNA, novelty and measurable targets.
- `audio/voice00_master.mp3` — selected shared narrator source.
- `src/render.py` — deterministic WF-01 picture renderer.
- `src/audio.py` — procedural score/SFX/ASMR builder and VO mix.
- `src/gate.py` — picture, sound, cadence, integrity and delivery gates.
- `artifacts/` — look sheet, audio/event measurements and final gate reports.
- `records/` — experiment/failure/fix ledger plus signed delivery receipt.

## Accepted delivery

- Master: `TUMHARI_RESERVED_SEAT_WF01.mp4` · 26,552,349 bytes
- SHA-256: `141258f25e0dad13c68d2e97fc96fd11f3cd215a7d89559723349b4211a3d69b`
- Acceptance: **21/21 delivery gates PASS** · **18/18 freshness PASS**
- Durable folder: https://drive.google.com/drive/folders/1V3QeUqDzOGP5obJAaX2vHyV5HZkS8K-J
- Exact remote IDs and checksums: `records/DELIVERY_RECEIPT.{md,json}`

## Rebuild

Final video binaries are generated under repository `build/` to protect Arena snapshot limits and are uploaded to durable Drive storage. From repository root:

```bash
python3 styles/monarch-stickman-animation/films/tumhari-reserved-seat/src/render.py --output build/tumhari-seat-wf01-mute.mp4
python3 styles/monarch-stickman-animation/films/tumhari-reserved-seat/src/audio.py \
  --output build/tumhari-seat-wf01-mix.wav \
  --mux-video build/tumhari-seat-wf01-mute.mp4 \
  --final build/TUMHARI_RESERVED_SEAT_WF01.mp4
python3 styles/monarch-stickman-animation/films/tumhari-reserved-seat/src/gate.py \
  build/TUMHARI_RESERVED_SEAT_WF01.mp4
```

The renderer measures and uses the selected 73.42-second narration; it never time-stretches the voice.
