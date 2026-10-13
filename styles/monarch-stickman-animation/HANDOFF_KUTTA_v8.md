# HANDOFF — AMEER KA KUTTA v8 (reconstructed 2026-10-13, session arena/ab4ba9f7)

> The original `/home/user/work/HANDOFF_v8.md` lived outside the repo and was lost with the
> previous sandbox. This file is the reconstruction from the repo brain (VIDEO_LOG V-009..V-017,
> PROBLEMS, STRATEGIES), the branch history and a live Drive check. It is kept **inside the repo**
> so it survives the next wipe. Source of truth for status stays the brain ledgers.

## 1. Status in one line

**v8 is delivered and awaiting the user's review.** Nothing is half-done. No v9 work has started.

| | |
|---|---|
| Deliverable | `AMEER_KA_KUTTA_v8.mp4` · 1080x1920 · 30 fps · 20.766 s · AAC stereo |
| Drive | `1D44AE8qc4wFwuAFu1UPrKPyuC-T8oshr` (folder `1_MhRILyCB86LWHYqLDzBPvmneA6Y2uqo` "stickman IZZAT 90s"), link-viewable, reader |
| Verified 2026-10-13 (this session) | size 25,131,827 B · md5 `8547b7e9c8c31319d9e149e7211f53e6` · created 2026-10-13T19:00:01Z |
| Gate | `gate_kutta2.py` **21/21 ALL PASS** (max_dluma 7.843, frames_dluma_gt8 0, black_edge 0, trans_jerk_max 6.944, peak -1.64 dBFS, LUFS -12.1, av_delta 0.01, vo_longest_gap 0.24 s) |
| Brain record | VIDEO_LOG **V-017** (status: delivered, pending user review) |
| Code | branch `arena/a188bd4a-monarch-studio` @ `4867ac8` — fast-forwarded into `arena/ab4ba9f7-monarch-studio` (this session) |

## 2. What v8 is (so feedback can be matched to code)

Script (Roman Urdu captions, Urdu-script TTS input, 4 chapters HOOK / LUXURY / RAJA / GAREEB):

1. *Kabhi kisi Ameer insan ke kutte ko dekha hai?*
2. *AC wali luxury gaadi mein ghoomta hai, branded khana khata hai, makhmal ke bistar pe sota hai.*
3. *Ameeron ka kutta janwar hokar bhi Raja ki tarah jeeta hai.*
4. *Aur gareeb bechara insan hokar bhi, janwaron ki tarah jeeta hai.*

12 shots: room_wide, room_close | walk, door, drive, bowl, bed | throne, crown | pave, crouch, split.
Boundaries at 1.5 / 3.0 / 4.25 / 5.16 / 6.52 / 7.54 / 8.68 / 10.87 / 12.66 / 15.90 / 18.18 s.

- **Picture** `src/kutta2.py` (shots, captions, cues) + `src/cards3d.py` (v8: real 3D card stage —
  perspective cards, side walls, cast shadows, sheen, neon edge, floor grid, streak particles, chroma split)
  + `src/transitions3d.py` (v7: shatter, flare, page, depth, cube, fold).
  `PLAN = carousel tunnel deck shatter carousel tunnel deck shatter carousel tunnel_long flare`
  (tunnel_long 1.6 s on pave->crouch, shatter TDX 0.80).
- **Dog** = CC0 Husky rig (Quaternius Ultimate Animated Animal Pack) rendered in Blender 4.3 Cycles,
  gold recolour + ink outline (`src/husky/dogrig.py` renders sprites, `src/husky/dog_husky.py` places them).
  Known limitation: **no sit clip in the pack — sit uses Idle.**
- **SHADE** hero (black) from `power2.py`/`toon.py`; grey insan, throne, crown, snow from `kutta.py` (v1).
- **Audio** `src/mux_kutta2.py`: tonal bed (A minor 96 BPM) + procedural whooshes + licensed SFX from the
  Drive pack, placed by moment (crack_flash hook, digital_click AC switch, gleam bed, conjure_charge throne,
  lighter_ignite crown, synth_sparkle crown settle, modern_shutter question reveal, riser_click before final
  shot / on tunnels). VO voice-03 ur-PK fitted by `src/prep_vo_kutta.py` (continuous, 0.22 s inner pauses).
  loudnorm I=-10.6, soft-knee ceiling.
- **Gate** `src/gate_kutta2.py` (21 checks, thresholds recalibrated in ST-008).

Honest caveats already on record (V-017): SFX were mapped by title/feature analysis, **not verified by ear**;
sit pose limitation; the v7 log wrongly claimed a VO regen — the v8 VO is the real regenerated one.

## 3. Version ladder (all on Drive, folder `1_MhRILyCB86LWHYqLDzBPvmneA6Y2uqo`)

| v | Drive ID | what changed | verdict |
|---|---|---|---|
| v1 | `1P9tWlmRWqWNejVKifhjafyFx8BWjMIc2` | first picture, 2D cut-outs, respect2 grammar | not judged |
| v2 / v2.1 | `1IMkOtvmUMyKRN6xTx6GYi70w8uP2pI8o` / `18xdhJCn1YTsQ7oBf0XnsGPDMPLaoquJU` | rebuilt engine (SHADE walk + leash, real car, 12 shots), continuous VO, tonal music; driver in windshield | gate 21/22 (jerk_p95) |
| v3 / v3b | `1hOFRUF7DHZxyRT1uGeoHNrGS9CFYKpFy` / `1_4HGw9KCKdPugzLEjP4LoCEs8t2JH-D5` | headline safe margin, VO regen, first licensed SFX test | not accepted |
| v4 | `11Nn6GaxLROBA4wEhL2Xf60DIOCJRnxGL` | SFX by moment, 3D headline extrusion | dog not premium |
| v5 | `1WtgpGLKU9Yqj5td94P-SpDw1D6TgvGoV` | Husky rig dog (Blender) | not accepted |
| v6 | `1RY803aqjzXtCthdd6OGk98Dv8FL4Yz-B` | 3D hinge/cube transitions, SFX lib from Drive pack, caption v6 | not accepted yet |
| v7 | `1tZWOw1sBN788x87_p7fxWLNdUG0gqvlp` | all boundaries 3D/parallax (depth, fold, shatter, flare) | not accepted yet |
| **v8** | **`1D44AE8qc4wFwuAFu1UPrKPyuC-T8oshr`** | real 3D card stage: carousel, tunnel, deck | **pending review** |

## 4. Open items carried into v9 (whatever the feedback is)

- P-021 / P-022: `jerk_p95` on shot frames was marginal in v2.x (2.11-2.12 vs 2.0) because of per-word
  reveals; v8 gate passes 21/21 with the current thresholds — re-check if captions change.
- Dog **sit** pose (Idle used). Options: blend Idle->Death first frames, or a second CC0 rig with a sit clip.
- SFX listening pass by the user (never done); mapping is by title only.
- Caption / headline style has been iterated (v5, v6 renderers) — user has not signed off on any.
- Music is procedural tonal bed; no licensed track.

## 5. Rebuild recipe in a fresh sandbox (what is NOT in Git and how to get it back)

Everything in Git imports cleanly with the render venv (checked this session: clean, toon, power2,
respect2, respect3, kutta, transitions3d, cards3d all import; kutta2/gate_kutta2 only need `timing.json`).

```bash
# 0. environment (pypi allowed; ~2 min)
bash tools/bootstrap/setup_3d.sh          # /tmp/venvs/render (+ /tmp/venvs/blender bpy 4.3 for the Husky)
export PATH=/tmp/venvs/render/bin:$PATH
mkdir -p /home/user/build/kutta/vo /home/user/build/sfx_src /home/user/build/sfx_lib2 /home/user/build/dog/out/v2
python3 -c "import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())" > /home/user/build/ff_path.txt
ln -sfn /home/user/Monarch-Studio/styles/monarch-stickman-animation/fonts /home/user/fonts   # clean.py FD
```

1. **VO** (not in Git, not on Drive as separate wavs): 4 clips `k1..k4.wav` via `generate_speech`,
   Urdu-script input of the 4 lines above, voice "voice-03 ur-PK" — **voice ids are per session**, so a new
   `add_voice` audition (language `ur-PK`, masculine, narration) is needed and the user must pick again.
   Then `python3 src/prep_vo_kutta.py` -> `fit_k*.wav` + `timing.json`.
2. **SFX source pack** (Drive folder `1AeMfK_DIcY4tkzWFwkJQM7XY0pOuPOgB`, verified this session):
   `VID_20261011_031631_368.mp4` `1a20ssE61rw9kDSSfO5Rj6LijAoDMCFYx` ·
   `VID_20261011_031646_165.mp4` `1qDV4DxG_Fxe6PQzONJlfK3ikvTV-WrEZ` ·
   `VID_20261011_031700_458.mp4` `1sInL8qubRNqUsTdiBb_t7AuABBhrSSIp` ·
   `VID_20261011_031727_691.mp4` `1j3qDv0asfOyTA1P6DM8AUIsn66Kr4qJ-`
   -> download to `/home/user/build/sfx_src/`, then `python3 src/cut_sfx.py` -> `/home/user/build/sfx_lib2/*.wav`.
3. **Husky sprites**: `Husky.glb` from github.com/trebeljahr/quaternius-showcase (`public/glb/animals_pack/Husky.glb`,
   CC0) -> `/home/user/build/dog/Husky.glb`; render with the blender venv: `src/husky/dogrig.py`
   (walk / eat / idle / death clips) -> `/home/user/build/dog/out/v2/` (`HUSKY_SPRITES` env overrides).
4. **Render**: two shards of `src/kutta2.py A B out.mp4` (NF from `kutta2.py shots`), concat with ffmpeg
   -> `/home/user/build/kutta/v2/kutta2_mute.mp4`; `python3 src/mux_kutta2.py` then `mux`;
   `python3 src/gate_kutta2.py <final.mp4>`. ~8-10 min on 2 CPUs for the picture.
5. Upload to Drive folder `1_MhRILyCB86LWHYqLDzBPvmneA6Y2uqo`, record md5, add a `brain.py video` entry.

Rules that still apply: media never enters Git (Drive only); never overwrite a delivered file; every
version gets a V-### entry; gate output is reported, never hidden.

## 6. Exact next action

**Wait for the user's v8 review.** Then branch on it:

- *Accept* -> mark V-017 accepted (`brain.py video ... --status accepted`), update knowledge INDEX, done.
- *Fix list* -> v9 on this branch: rebuild media per section 5, apply fixes, gate 21/21, upload, V-018.
- *Different direction* (new dog, new look, new script) -> strategy entry first (ST-009), then build.
