# TUMHARI RESERVED SEAT — WF-03 production package

A 74-second, 16:9 landscape short in the permanent Monarch Noir Film style. It uses the exact same topic, script, selected `voice-00` performance and 34-beat master timeline as WF-01, but rebuilds the entire visual and sonic world as a new noir film.

This production deliberately has **no film number**. The historical Film-#3 conflict remains unresolved and is not guessed here.

## Style execution

- World: one rain-soaked midnight railway platform; controlled dark values, local fluorescent pools, practical reflections, breath, dust and camera drift.
- Hero: permanent WF-03 humanised Monarch figure; hoodie, human face, weight shift and restrained performance.
- Physical device: one self-punching reserved ticket. Thirty holes become the thirty-hour gap and finally the train’s lit windows.
- Grammar: sparse carried holds interrupted by exact punch cuts, departure-board flips, train occlusions and fluorescent blackouts.
- Colour arc: cold cyan fluorescents + red warning → first amber practical after the action choice → restrained dawn warmth.
- Sound: original procedural 72 BPM noir score, rain, electrical hum, rails, ticket printer/punch, departure flaps, carriage chime and quiet tail.
- No reuse of THE SHADOW’s lantern/shadow device or THE WINDOW’s apartment/window device.

## Package map

- `SCRIPT_AND_TOPIC.md` — shared master story.
- `MASTER_TIMELINE.json` — measured 74.0-second picture lock.
- `DNA.json` — selected fresh noir world/device/grammar and gate targets.
- `audio/voice00_master.mp3` — same narrator source used by WF-01.
- `src/render.py` — deterministic platform-world renderer.
- `src/audio.py` — procedural noir score/SFX/ambience and VO mix.
- `src/gate.py` — adapted short-form subset of the 27-gate film suite.
- `artifacts/` — look sheet, audio/event measurements and final gate reports.
- `records/` — decisions, tests, failures/fixes and signed delivery receipt.

## Accepted delivery

- Master: `TUMHARI_RESERVED_SEAT_WF03.mp4` · 12,508,030 bytes
- SHA-256: `738a6aaa177595384f2070f1e16a38b5412ff10514732ba5a60f420b7395dc2f`
- Acceptance: **21/21 delivery gates PASS** · **18/18 freshness PASS**
- Durable folder: https://drive.google.com/drive/folders/1A39EybqgjoG8-Tj5uix5Cf4WW39CzmgP
- Exact remote IDs and checksums: `records/DELIVERY_RECEIPT.{md,json}`

## Rebuild

Final video binaries are generated under repository `build/` and then uploaded to durable Drive storage:

```bash
python3 styles/monarch-noir-film/films/tumhari-reserved-seat/src/render.py --output build/tumhari-seat-wf03-mute.mp4
python3 styles/monarch-noir-film/films/tumhari-reserved-seat/src/audio.py \
  --output build/tumhari-seat-wf03-mix.wav \
  --mux-video build/tumhari-seat-wf03-mute.mp4 \
  --final build/TUMHARI_RESERVED_SEAT_WF03.mp4
python3 styles/monarch-noir-film/films/tumhari-reserved-seat/src/gate.py \
  build/TUMHARI_RESERVED_SEAT_WF03.mp4
```

The narration is not time-stretched. All cuts, practical changes and sound cues follow its measured performance.
