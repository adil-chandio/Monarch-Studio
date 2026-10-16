# WF-07 · no-loss completion record

Checked against `docs/STYLE_LIBRARY_STANDARD.md` on 2026-10-16.

| # | Contract item | Where it lives |
|---|---|---|
| 1 | final source and required assets | `src/tabahi/` (11 modules), `src/run_film.py`, `assets/fonts` (5 fonts + 2 OFL), `assets/plates` (14 owned plates) |
| 2 | exact commands, toolchain, dependency versions or bounds | `records/TOOLCHAIN.md` |
| 3 | what was attempted, what failed and why | `knowledge/09_FAILURE_REGISTER.md` (T01–T18), `PROOFS.md` §3/§5 |
| 4 | decisions and rejected alternatives | `records/ENGINE_DECISION.md`, `ANALYSIS.md` §4/§6 |
| 5 | measured gate report and master identity | `projects/proof-01-trailer/reports/GATES.json` (16/16 PASS), `BUILD.json`, `proofs/PROOF_01.md` |
| 6 | Drive IDs / hashes / Notion / Linear / Doc IDs | **OWED** — nothing has been uploaded for WF-07 yet; the master is local only |
| 7 | chat/action checkpoint archive | **OWED** — the session's EMS checkpoints cover WF-06 and MF-01; WF-07 needs a checkpoint entry once the next production starts |
| 8 | updated style index and repository manifest | `knowledge/INDEX.md`, `styles/registry.json`, `styles/README.md`, root `README.md`, `studio/MONARCH_STUDIO_REGISTRY.snapshot.md` (next free code **WF-08**) |

## Open items carried forward (do not lose these)

1. **Vertical-first type layout.** `film.vertical_path` renders camera + grade into 1080×1920; it
   does not thread type or FX through the 9:16 canvas. The vertical cut is real but not yet a
   designed Short. Fix belongs in `film.vertical_path` + a `vertical_first` plan flag.
2. **Real narration.** `score.build_voice_track` has never carried a human take in this style;
   the proof master is music-led.
3. **Drive upload.** No WF-07 artefact is uploaded. The channel's Drive folder is
   `Wf-06 • Monarch Cam Channel` (`1M8zExLyWXZsbC0lqQeLsBStzC2w0g6O6`).
4. **A08 loop is blind** until the owner sends 48-hour numbers for a published video.
5. **Which video publishes first** — *The Bear's Invisible Map* (V12, already final) or MF-01 —
   is still an open question for the owner.
