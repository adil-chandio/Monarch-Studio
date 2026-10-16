# WF-07 · no-loss completion record

Checked against `docs/STYLE_LIBRARY_STANDARD.md` on 2026-10-16.

| # | Contract item | Where it lives |
|---|---|---|
| 1 | final source and required assets | `src/tabahi/` (11 modules), `src/run_film.py`, `assets/fonts` (5 fonts + 2 OFL), `assets/plates` (14 owned plates) |
| 2 | exact commands, toolchain, dependency versions or bounds | `records/TOOLCHAIN.md` |
| 3 | what was attempted, what failed and why | `knowledge/09_FAILURE_REGISTER.md` (T01–T25), `PROOFS.md` §3/§5 |
| 4 | decisions and rejected alternatives | `records/ENGINE_DECISION.md`, `ANALYSIS.md` §4/§6 |
| 5 | measured gate report and master identity | `projects/proof-01-trailer/reports/GATES.json` (G01–G19; the gate table grew by G17/G18 portrait and G19 vertical contrast), `BUILD.json`, `proofs/PROOF_01.md` |
| 6 | Drive IDs / hashes / Notion / Linear / Doc IDs | Drive folder **`WF-07 · PROOF-01 Trailer — publish files (16:9 + 9:16)`** `1ANkoVyWG5kC7XH2NEFhKuIA48IvFDpfc` (inside `Wf-06 • Monarch Cam Channel`): master `1jhVg4q7H681mGG1jn-47AgQhcAOYTRQI` · vertical `1TmM36v_uNgpDpJHTNIxtZHHsrjp_DN-X` · contact sheet 16:9 `1bygfBOgpCjM04QbuZWF0BgpLLKWwjNWO` · contact sheet 9:16 `1Rr71ycDlwSHvu0rdk2AtGPnIKBPoofNB` · thumbnail B `1zEEiqAv3RnrRIFwgou8mcpqgp7ykbcjq` · publish package (Doc) `1o8bCmdTZ-OcM0V2oTYZ5IKF-44GE-8XGDS-CzssGvV0` · gate report `1CG3jJpmy5s3OjFv-GRI8S3G-TKvg1YhM` |
| 7 | chat/action checkpoint archive | **OWED** — the session's EMS checkpoints cover WF-06 and MF-01; WF-07 needs a checkpoint entry once the next production starts |
| 9 | publish package for the owner | `reports/PUBLISH.md` (title, description, tags, settings, and the 48-hour ask) — uploaded to the same Drive folder as a Google Doc |
| 10 | narration pipeline + voice asset | `score.place_voice` (absolute-time placement, VO chain, silence-trimmed lines in `projects/proof-01-trailer/vo/`), gates **G20**/**G21**, laws recorded in `knowledge/06` and register **T27–T31** |
| 8 | updated style index and repository manifest | `knowledge/INDEX.md`, `styles/registry.json`, `styles/README.md`, root `README.md`, `studio/MONARCH_STUDIO_REGISTRY.snapshot.md` (next free code **WF-08**) |

## Open items carried forward (do not lose these)

1. **Vertical-first type layout — DONE for PROOF-01, still open as a plan-level flag.**
   `core.canvas(VW, VH)` re-scopes every builder to 1080×1920, `kinetic.headline`/`corner_mark` are
   portrait-aware, `film.render_vertical` composes the type inside the portrait canvas after the
   tracked crop, and a shot can override with `vertical_type`. Proved by G17 (0 type violations
   outside the Shorts safe band y 420–1620), G18 (1080×1920) and G19 (worst delivered vertical type
   contrast). Three defects were measured and fixed on the way (T19 no type in the crop, T20 type
   under the platform buttons, T21 scrim rectangle on the brand mark; then T23/T24 for the mark's
   contrast treatment). Still open: `vertical_first` — designing the *shot* for 9:16 instead of
   cropping a 16:9 composition — and no cross-shot transitions in the vertical cut yet.
2. **Real narration.** `score.build_voice_track` has never carried a human take in this style;
   the proof master is music-led.
3. **Drive upload — DONE, and now NARRATED.** The folder `WF-07 · PROOF-01 Trailer — publish files
   (16:9 + 9:16)` (`1ANkoVyWG5kC7XH2NEFhKuIA48IvFDpfc`) holds the **narrated** pair and a 12-second
   excerpt, all built after the owner rejected the music-only cut on sight. Current files:
   master (narrated) `1S-lIviW7gSdb3eE4G3SvlaR9VYggdOJU` · vertical (narrated)
   `1XMqOsSd5lF-LSw9PeBnPoPELx_gntGWl` · 12 s excerpt `1kp7u_FsEZ5J8HgvSxYsmkhUlgeP6Vsq1` ·
   contact sheet 9:16 `1sFdivkUsFBqejx0AgDRNluTUWqP5E2Om` · publish package (Doc)
   `1o8bCmdTZ-OcM0V2oTYZ5IKF-44GE-8XGDS-CzssGvV0` · gate report `1CG3jJpmy5s3OjFv-GRI8S3G-TKvg1YhM`.
   The pre-narration files were **trashed**, not left to rot in the same folder — an owner must never
   have to guess which of two masters is current.
4. **A08 loop is blind** until the owner sends 48-hour numbers for a published video.
5. **Which video publishes first** — *The Bear's Invisible Map* (V12, already final) or MF-01 —
   is still an open question for the owner.
