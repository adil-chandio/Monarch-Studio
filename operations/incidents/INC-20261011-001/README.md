# INC-20261011-001 · Arena snapshot capacity dropped nested repository data

## Observed

At the start of the next user turn, the previously committed repository's `.git` directory and large nested workflow/character directories were absent. Root documentation remained. The workspace hydration archive contained only 37 repository files while staging archives and upstream clones survived.

Prior local commit recorded in the preceding completed turn:

`208dcde84bde4b51b3b03df0ee4986e157c72765`

Its Git objects were not available after hydration, so that hash cannot honestly be reconstructed as the same commit.

## Cause assessment

The Arena workspace has a best-effort snapshot cap around 128 MB. The repository worktree, local Git object pack, staging archives and upstream clones collectively exceeded it. This is consistent with selective snapshot omission. It is not treated as source-authority loss because exact Drive packages and hashes remained available.

## Recovery

- Restored WF-01 from `video_edit_workflow_v3.zip`, current brain v2, IZZAT v2 package, current resume and SHADEGO.
- Restored WF-03 from the verified nested `monarch overall workflow.zip`, then applied current Drive resume/HUB and 4:00 AM evidence.
- Re-audited the current 35-item WF-03 Drive folder and corrected stale IDs.
- Restored Monarch Bible/Board, generated current previews and extracted selected v10/v11 tooling.
- Preserved the previous repository SHA-256 manifest as `pre-recovery-manifest.json`.

## Prevention

1. Remove redundant local staging archives/clones after verification.
2. Store vendor projects as pinned gitlinks; initialize only on demand.
3. Keep milestone Git bundles on Drive.
4. Use sparse checkout locally after committing binary archive assets.
5. Maintain one active task, hash-chained journal, exact resume capsule and hourly/event checkpoints.
6. Never rely on a chat summary or local process as the only state.

This incident is append-only evidence and must not be erased to make the history appear cleaner.