# Skills: tumhari-reserved-seat-3d

Skills this project has learned, and where each one lives in the repo. A skill here is a repeatable method that worked, with its limits. Promoted skills are also listed in the studio's runbooks, so a new chat starts with them.

## Skills learned in this project

| # | Skill | What it means in practice | Where it lives |
|---|---|---|---|
| 1 | Headless Blender on a locked-down sandbox | `bpy==4.3.0` import needs stub `.so` files for X11/GL and `RTLD_GLOBAL`. Rebuild with one command. | `docs/runbooks/LOCAL_NO_API_RENDER.md` §3, `tools/bootstrap/setup_3d.sh` |
| 2 | Lookdev at reveal time | Check each style at the time its key element is on screen (WF-02 at t ≥ 9.5, text reveal at 6.5 s). Early times show a partial scene and look like bugs. | `docs/runbooks/3D_VIDEO_PIPELINE.md` §5 |
| 3 | Portrait camera framing | In 9:16 with AUTO sensor fit, the 36 mm sensor applies to height. Set distance from the tallest object. | same §5 |
| 4 | Emission under AgX | Neon emission above about 3 blows out to white blocks. Keep text emission in the 1–3 range. | same §5 |
| 5 | Metal needs a world | Chrome and gold look black under a dark world. Use a gradient world, not a flat colour. | same §5 (open) |
| 6 | Volumetric haze budget | Density 0.004–0.007 at 32 spp. Above about 0.02 it is noise. | same §5 |
| 7 | Raking light for layers | A narrow, low area light makes paper layers readable. Wide, bright lights wash out. | same §5 |
| 8 | Vendor pins without the weight | Keep vendor source as pinned submodules. Release working trees by default. Restore with one command. | `docs/VENDOR_INTEGRATION.md`, `tools/vendor/materialize.sh` |
| 9 | Skill text in the repo | Copy only skill text files, with pins and licences in `PROVENANCE.md`. | `docs/skills/vendored/` |
| 10 | Artifacts outside the workspace | Upload to Drive, record link, size and SHA-256, delete local copy. | `tools/archive/record_artifact.sh`, `ARTIFACTS.md` |
| 11 | Sandbox reset recovery | Check HEAD against origin first. Back up, then `git merge --ff-only`. Never hard-reset. | `RESUME.md`, runbook §8 |
| 12 | Drive connector order | Call `list_connector_tools` before the first Drive upload in a turn. | `TOOLS.md` |
| 13 | Audio: procedural by default | numpy sound design. Sample libraries only if the user supplies a licensed library. | `DECISIONS.md` |
| 14 | Enhancement settings | WF-01 v4: CRF 21, grain 2.4. Higher grain gave 100 MB+ files. | `TOOLS.md` |

## Skills still missing (to do next)

- Gradient or HDRI-style world for WF-02 chrome.
- Paper-layer edge highlight and shadow pass for WF-01.
- Spot light and slow dolly for WF-03.
- Measured per-frame timing at 360×640, 48 spp, before any 240-frame render.
- A frame-level review checklist (sharpness, exposure, text legibility, animation every second).

## Promotion rule

When a skill has worked at least twice and is written down here, move the reusable part to `docs/runbooks/` or `docs/skills/` and link it back from this file. Keep the project-specific part here.
