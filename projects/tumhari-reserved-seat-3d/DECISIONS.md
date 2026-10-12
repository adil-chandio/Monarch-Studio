# Decisions and user instructions: tumhari-reserved-seat-3d

Standing instructions from the user, locked concepts, and consequential decisions. Do not drop an entry unless the user reverses it. Newest decisions go at the bottom of their section.

## Standing instructions (from the user)

- Real 3-D, animated frame by frame. Not made from images. Animation every second.
- No "jugaad" or "churane wala" approach.
- Same topic and script as the Tumhari Reserved Seat film.
- Narration in Roman Urdunglish. Accent correction with ur-PK (voice-02). The demo uses voice-00 first.
- Premium quality: premium colouring, elite and professional look. Not cheap or cringe.
- "Beyond limits" and "tabahi" quality. Do not claim premium or finished before a frame-by-frame check.
- Use open-source tools where possible. Blender and ffmpeg are the render path.
- Do not use HuggingFace or any blocked host or mirror for voice or model assets.
- Voice cloning of the user's own voice is declined until an allowed registry and a voice sample are provided.
- Fix all blockers and keep going to a next-level result.
- Cloned repos go inside the Monarch repo as pinned submodules (`docs/VENDOR_INTEGRATION.md`).
- All three films are 9:16 vertical (most recent instruction). 16:9 files are superseded.
- Sound: procedural (numpy) by default. Sample libraries only if the user supplies a licensed library.
- Do WF-01 first. Improve it to next level before moving on to WF-03 (user rejected moving on early).
- Workspace stays light. Large videos go to Drive or GitHub (link recorded, file not kept locally).
- Everything about the project (workspace, process, tools, skills) must live in GitHub, so a new chat can resume exactly where this one stopped.

## Locked concepts (approved by the user)

| Style | Metaphor | Editing and animation | Sound | Palette |
|---|---|---|---|---|
| WF-01 Paper Cinema | Paper train timetable with a reserved seat | Paper-page turn transitions, three-plane parallax, paper-style motion | Paper percussion and paper SFX | Warm paper, red ink |
| WF-03 Midnight Platform Noir | Reserved ticket as a timer that runs out | Slow dolly, lens breath, rain ASMR, long holds, fewer cuts | Rain ASMR, procedural | Cold blue and amber |
| WF-02 Zack-D 3D Power | 20 min × 90 days = 30 hours, one cube per second, voxel 3-D text | Hard cuts, whip-style angle changes, chrome and neon materials | Procedural | Chrome, gold, cyan neon |

Shot grammar must differ between styles even though the script is the same.

## Consequential decisions

- **Engine.** Moved from the earlier engine to Blender Cycles (CPU). Reason: user's own Blender run and the 3-D requirement. Date: Phase 5.
- **Aspect.** 9:16 for all three. Reason: most recent user instruction.
- **Vendor source.** Pinned submodules, working trees released by default to keep the workspace light. Restore with `tools/vendor/materialize.sh`. Reason: snapshot cap (about 128 MB / 10,000 files). User asked to keep everything in GitHub, not elsewhere.
- **Large artifacts.** Drive (not GitHub Releases). Reason: `uploads.github.com` is blocked in this sandbox. The repo is public, so anything on GitHub is public.
- **Repo visibility.** `adil-chandio/Monarch-Studio` is public. Any file pushed there is public. Do not commit private voice samples, credentials, or unreleased material.
- **FreeCAD pin.** Re-pinned from `ec6852e` (short SHA, not fetchable) to `23a5e34`.
- **WF-02 tower spacing.** The first layout (cube spacing 1.05 for 1 m cubes, a 0.05 m gap) read as a dim, thin column. Changed to a 1.25 spacing for a more readable tower. This is a lookdev change, not yet accepted.
- **Lookdev rule.** Stills are checked at each style's reveal time (for example WF-02 at t ≥ 9.5), not at t = 3.5.

## Open questions for the user

- Should the Monarch repo be merged into `main` so a clone of `main` contains this work? Currently everything is on `arena/a188bd4a-monarch-studio`.
- Keep the repo public, or make it private before storing more project material?
- Approve a 240-frame render at 360×640, 48 spp? Per-frame timing is not measured yet.
