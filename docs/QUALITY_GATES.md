# Quality gates

A delivery is not certified merely because it renders. It must pass the workflow's measured gates, be uploaded, have the remote MD5 verified, and have its state recorded.

## WF-01 gate model

The current reference implementation is `src/gate_respect2.py`. IZZAT v2 passed **19/19** engine checks. A new SHADEGO build also runs the EDITOR BRAIN novelty gate, described operationally as **gate #20**.

The 19-check family covers:

1. file/probe/readability;
2. exact dimensions and orientation;
3. frame rate;
4. duration/timeline agreement;
5. audio stream and duration;
6. loudness target;
7. true-peak safety;
8. silence/dropout constraints;
9. shot count/cadence;
10. transition count and uniqueness;
11. frame motion / no unintended stillness;
12. black-frame/sliver safety;
13. caption safe-area and width;
14. contrast/readability;
15. required chapter/beat structure;
16. character/plate presence;
17. package/contact-sheet/notes presence;
18. delivery metadata/MD5 evidence;
19. declared workflow-specific checks.

The exact code and thresholds, not this summary, are authoritative. Thresholds may not be relaxed to make a build pass.

### Current WF-01 benchmark

- IZZAT v2: 75.19 s, 1080×1920, 24 fps.
- 33 shots; 32 transitions; 15 transition kinds.
- −11.6 LUFS; stereo mix.
- 19/19 engine gates.
- Brain novelty registry committed only after success.

## WF-03 full-film gate model

THE SHADOW and THE WINDOW use a **27-check** gate family implemented in `src/gate_shadow.py` and `src/gate_window.py`. It measures:

- exact 1920×1080 / 24 fps output;
- timeline and frame-count agreement;
- expected shot, hold and beat structure;
- visual darkness/luma and saturation regime;
- motion and cut behavior;
- dialogue count and duration;
- loudness, true peak and LRA;
- missing audio/black output/corruption;
- script/DNA/events/package evidence;
- Drive ID and remote MD5 record.

THE SHADOW and THE WINDOW both have 27/27 reports checked in at the WF-03 workflow root (`GATES_THE_SHADOW_v1.md` and `GATES_THE_WINDOW_v1.md`), matching the historical scripts' expected layout.

### Current WF-03 benchmarks

| Film | Duration | Structure | Audio | Gate result |
|---|---:|---|---|---:|
| THE SHADOW v1 | 156.92 s | 33 shots · 12 holds · 93 beats · 3 VO lines | −16.5 LUFS · TP −1.4 dB · LRA 12.2 | 27/27 |
| THE WINDOW v1 | 155.0 s | 31 shots · 11 holds · 86 beats · 4 VO lines | −16.5 LUFS · TP about −1.2 dB · LRA 8.9 | 27/27 |

## 4:00 AM limitation

`GATES_NOIRGO_4AM_v2.md` reports **11/11** limited checks, including:

- 60.0 s;
- 1920×1080 / 24 fps;
- H.264 yuv420p, AAC 48 kHz stereo;
- measured dialogue and title timing;
- −16.5 LUFS, TP −1.1 dB, LRA 7.8;
- exact Drive MD5 `ed233b75aa67f4255aa5c792e213467f`.

This is valuable evidence but is **not equivalent to the established 27-check film gate**, and the implementation source was not found. The repository must not label it 27/27.

## AB KARO ABHI limitation

Only the MP4 metadata and MD5 were found. There is no canonical checked gate report. It is not certified by this repository.

## Repository validation gates

`python3 tools/studio.py validate` performs repository-level checks independent of render quality:

- parse registry/workflow JSON;
- confirm all registered paths and required authority files;
- verify selected authority hashes recorded in `.studio-manifest.json`;
- compile Python source;
- parse shell scripts with `bash -n`;
- ensure no oversized Git blob is introduced;
- require explicit declarations for known WF-03 drift;
- detect missing/broken vendor submodules;
- audit legacy absolute-path incidence while allowing it in preserved historical source.

`doctor` checks external executables and importable Python modules needed to render. A successful repository validation does not imply an expensive master render was rerun.

## Delivery rule

A future delivery record must contain:

- exact filename, Drive ID, local and remote MD5;
- duration, dimensions, fps and codecs;
- loudness, true peak and LRA;
- gate count and path to the report;
- source/package identity;
- registry/brain commit state;
- updated Notion, Linear, Drive and Google Docs records.

If any item is missing, mark the delivery provisional rather than inventing it.