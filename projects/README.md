# Projects: archive category

Every working project lives here as one folder. The folder holds everything needed to resume the work in a new chat, on a fresh clone, or after a sandbox reset: what was done, how, with which tools, the decisions, the skills learned, and an index of large files that live outside the repo.

## Workspace

The Arena workspace root (`/home/user`) holds only the `Monarch-Studio` repo and dotfiles. The `.cache` folder is outside snapshots. So the whole workspace is the repo, and its tracked content is on GitHub. Compact mode (`tools/materialize.py`) keeps the worktree under the 128 MB and 10,000-file limit, and keeps `projects/` local. Restore full content with `tools/materialize.py full` when a render needs it.

## Rules

1. **Workspace stays light.** Videos, audio, big images and archives go to Google Drive (or another host). Record them in the project's `ARTIFACTS.md` with `tools/archive/record_artifact.sh`, then delete the local copy.
2. **Process is logged as it happens.** Append to the project's `PROCESS_LOG.md` for each working step: action, tool or command, outcome, output path. Do not rewrite older entries.
3. **Chat is recorded.** Append one row to the project's `CHAT_LOG.md` for each user request and its outcome.
3b. **Decisions are recorded.** Standing instructions and consequential decisions go in `DECISIONS.md`.
4. **Tools are recorded.** Every tool, version, command and dead end goes in `TOOLS.md`.
5. **Skills are promoted.** A skill that worked goes to `docs/runbooks/` or `docs/skills/`, and the project keeps a pointer in `SKILLS.md`.
6. **Resume capsule.** `RESUME.md` holds the start commands, the exact next action, and the open questions.
7. **Repo is public.** Nothing private, no credentials, no unreleased voice samples.

## Projects

| Slug | What it is | Status |
|---|---|---|
| [`tumhari-reserved-seat-3d`](tumhari-reserved-seat-3d/README.md) | 9:16 premium 3-D films (WF-01, WF-02, WF-03) on the Tumhari Reserved Seat script | In progress. Not accepted. |

## Adding a project

```bash
mkdir -p projects/<slug>
# copy the template files from projects/tumhari-reserved-seat-3d/: README.md, RESUME.md, PROCESS_LOG.md, DECISIONS.md, TOOLS.md, SKILLS.md
python3 tools/studio.py manifest --write && python3 tools/studio.py validate
```
