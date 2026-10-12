# Resume: tumhari-reserved-seat-3d

Start here in any new chat or fresh clone.

## Where things are

- Project overview: `README.md`
- Chat log (what the user asked, turn by turn, and the outcome): `CHAT_LOG.md`
- Process log (how the work was done, step by step): `PROCESS_LOG.md`
- Decisions and standing instructions: `DECISIONS.md`
- Tools and commands: `TOOLS.md`
- Skills learned and still missing: `SKILLS.md`
- Large artifacts and links (Drive): `ARTIFACTS.md`
- Render method and blockers: `docs/runbooks/3D_VIDEO_PIPELINE.md`
- Vendor pins and licences: `docs/VENDOR_INTEGRATION.md`
- Skill text copies: `docs/skills/vendored/PROVENANCE.md`

## Start commands

```bash
git clone https://github.com/adil-chandio/Monarch-Studio.git && cd Monarch-Studio
git checkout arena/a188bd4a-monarch-studio
tools/bootstrap/setup_3d.sh
tools/vendor/materialize.sh one react-bits      # or: all
```

## State at the end of the last logged phase

- **Status:** in progress. No film is accepted. Lookdev stills are test quality.
- **Current engine:** Blender Cycles (CPU), 9:16, `tools/render/blender-vertical/wf_scenes.py`.
- **Priority:** WF-01 first (user rule), then WF-02, then WF-03.
- **Next action:** fix the WF-02 world and neon balance, fix the WF-01 paper-layer shadows, then add a spot light and dolly to WF-03. Re-render each lookdev at its reveal time. Show the user the stills. Get approval before any 240-frame render.
- **Open question for the user:** merge this branch into `main`? Keep the repo public?

## Rules for the next turn

1. Read `DECISIONS.md` before changing anything.
2. Append to `PROCESS_LOG.md` for each working step.
3. Do not commit media. Upload media to Drive, then run `tools/archive/record_artifact.sh`.
4. Run `python3 tools/studio.py manifest --write` after adding tracked files, then `python3 tools/studio.py validate`.
5. Never claim premium or finished before a frame-by-frame check.
