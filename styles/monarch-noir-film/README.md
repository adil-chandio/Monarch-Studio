# Monarch Noir Film

- **Style ID:** `monarch-noir-film`
- **Workflow contract:** WF-03
- **Trigger:** `NOIRGO <topic>`
- **Normalized state:** **ACTIVE_WITH_DRIFT**
- **Default film format:** 1920×1080, 24 fps, 120–180 s

## Style definition

This style makes sparse, one-world noir animated films with a controlled darkness regime, deliberate long holds, short punch-cut passages, minimal dialogue, motif callbacks and a physical visual device unique to each film. It includes a reusable noir renderer, per-film render/audio/gate programs, exact DNA/event data, final plates, generated voice clips and measured gates.

## Fully sourced films

### Film #1 · THE SHADOW · FEAR

- Drive `16qsEno9sN_p4fggfcTN05W9LUzYsz0u4`
- MD5 `f8b7e71b9238febd3c60f82463116393`
- 156.92 s, 1920×1080, 24 fps
- 33 shots, 12 holds, 93 beats, 3 English VO lines
- −16.5 LUFS, TP −1.4 dB, LRA 12.2
- 27/27 gates
- Core device: lantern-cast shadow double; this exact world/device is blocked from reuse.

### Film #2 · THE WINDOW · REGRET

- Drive `1WaMfEroWgzuYHeSCpyU9CPY7gJ0a0iGy`
- MD5 `cfe189f9c09e47e6728d2f2aba017f8d`
- 155.0 s, 1920×1080, 24 fps
- 31 shots, 11 holds, 86 beats, 4 English VO lines
- −16.5 LUFS, TP about −1.2 dB, LRA 8.9
- 27/27 gates
- Core device: looking through an apartment window across time; that immediate grammar is blocked from reuse.

## Later evidence—numbering unresolved

### `4:00 AM — Jo Jaagta Hai` v2

- Claimed as Film #3; 60 s horizontal.
- Current Drive file `1gLy2m9GTgwKzDaAV59nrLALojhGkKaWI`.
- MD5 `ed233b75aa67f4255aa5c792e213467f`.
- 11/11 limited delivery checks, −16.5 LUFS, TP −1.1, LRA 7.8.
- No script/renderer/DNA/events/source package was found in the supplied current implementation.
- It is R2 gate-evidenced, not a 27/27 fully reproducible film.

### `AB KARO ABHI — Procrastination Kills` v1

- Also labelled Film #3; 75 s vertical 1080×1920.
- Current Drive file `1y7Z7OtOMQXeoTcIoHiqr7ClmHndefH1r`.
- MD5 `bdea55c453834fa4a4b0cacec89ed53c`.
- No source, gate report, canonical resume block or dedicated Notion/Linear record was found.
- It remains R3 delivery-only evidence.

No later film number may be assigned until this conflict is reconciled across every platform. See [`../../docs/RECONCILIATION.md`](../../docs/RECONCILIATION.md).

## Production grammar

- One coherent world and one physical device per film.
- Dark picture with controlled local highlights, not generic crushed black.
- Long holds contain living motion: rain, dust, fabric, breath, light change or camera drift.
- Sparse dialogue; silence and sound design carry story architecture.
- Motif callbacks and a final recontextualization/payoff are required design tools.
- No CTA in cinematic film mode.
- A new film must not reuse the preceding world's core location/device.
- Voice must be re-auditioned in a new speech-tool session.

## End-to-end process

1. `brain/concept.py propose --format film` → DNA JSON.
2. `brain/concept.py gate` → novelty/feasibility result.
3. Build and approve a look sheet.
4. Build picture with per-film renderer/events data.
5. Generate sparse VO, synthesize score/sound design and mix to −16.5 LUFS target.
6. Encode per segment and use frame-exact concat/splice, avoiding memory-heavy multi-input graphs.
7. Run the 27-check film gate.
8. Upload and verify remote MD5.
9. Commit concept memory and update GitHub/Drive/Notion/Linear/Google Docs through the continuity outbox.

## Implementation map

| Path | Purpose |
|---|---|
| `src/noir.py` | shared noir drawing/render utilities |
| `src/film_shadow.py` / `src/film_window.py` | per-film renderers |
| `src/audio_shadow.py` / `src/audio_window.py` | per-film audio builds |
| `src/encode_shadow.sh` / `src/encode_window.sh` | segmented encoding/final mux |
| `src/gate_shadow.py` / `src/gate_window.py` | 27-check gates |
| `DNA_THE_SHADOW.json` / `DNA_THE_WINDOW.json` | film design DNA |
| `data/events.json` / `data/events_window.json` | exact timeline events |
| `plates/` | final Window world plates |
| `vo/` | ten generated Window VO clips |
| `GATES_THE_SHADOW_v1.md` / `GATES_THE_WINDOW_v1.md` | full gate reports |
| `films/04am/GATES_NOIRGO_4AM_v2.md` | limited 4:00 AM evidence |
| `SOURCE_INVENTORY.md` | complete current Drive folder inventory |
| `knowledge/INDEX.md` | permanent knowledge catalogue |

## Portable execution

The historical code expects `/home/user/workflows/wf03_monarch_noir_film`. The hydrator recreates that layout in `.runtime` without mutating permanent source:

```bash
python3 ../../tools/studio.py hydrate wf03
python3 ../../tools/studio.py run wf03 -- \
  python3 workflows/wf03_monarch_noir_film/src/film_window.py --help
```

## Resource profile

The original environment was 2 vCPU / 2 GB RAM. THE SHADOW's 157 s picture render took roughly 34 minutes and the complete encoding flow roughly 45 minutes. Heavy encoders must remain sequential.

Source hubs and exact IDs are in [`../../docs/SOURCE_MAP.md`](../../docs/SOURCE_MAP.md).