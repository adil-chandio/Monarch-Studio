# GitHub, Drive, Notion, Linear and Google Docs sync

Every checkpoint generates a small factual package in `operations/continuity/outbox/<task>/<checkpoint>/`:

- `STATUS.md` — human update;
- `checkpoint.json` — machine state and hashes;
- `SYNC.json` — independent status for each platform.

## Platform roles

| Platform | Role |
|---|---|
| GitHub | canonical version history, code review and checkpoint commits |
| Google Drive | large masters, source bundles, repository bundles and disaster-recovery exports |
| Notion | browsable style/workflow knowledge and decisions |
| Linear | active tasks, blockers, status and acceptance criteria |
| Google Docs | portable human-readable hub/resume/proof document |

## No-drift transaction

1. Local checkpoint is written atomically.
2. Git commit is created.
3. Push to GitHub if `origin` and credentials exist.
4. Upload status/export to the dedicated Drive continuity folder.
5. Append/update the dedicated Notion page.
6. Update the dedicated Linear issue/project.
7. Update the dedicated Google Doc.
8. Mark each target separately in `SYNC.json` with remote ID/time/result (`python3 tools/continuity.py sync-mark --task-id … --checkpoint … --platform … --status completed --remote-id … --url … --note …`). When the marked checkpoint is the task's latest one, `sync-mark` mirrors the status into `ACTIVE_TASK.remote_sync` so `resume` reports the true state; older checkpoints of the same task whose record is carried by a newer sync are marked `superseded` with a note naming the newer checkpoint.
9. Failed targets remain pending and are retried; success elsewhere never masks them.

## Recovery from the Drive continuity folder

Each milestone upload is a triple in the continuity folder: `<task>-cpNNNN-continuity.tar.gz` (workflows/current + checkpoints + outbox), `<task>-cpNNNN.delta.bundle` (git bundle from the branch point on `main` to the checkpoint commit — `git bundle verify`, then `git fetch <bundle> <branch>`) and `<task>-cpNNNN-SHA256SUMS.txt`. Verify the SHA-256 sums before trusting a capsule.

## Large files

Git contains source and reasonable production assets. Full masters and sensitive raw identity media remain on Drive by exact ID/hash. Milestone Git bundles are uploaded to Drive for disaster recovery. Files ≥100 MiB are prohibited as ordinary Git blobs.

## GitHub prerequisite

A GitHub repository URL and credentials/connected app are required before `origin` can be configured and pushed. The local system never invents a remote or stores a personal token in the repository.