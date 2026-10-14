# Studio operating rules — read before any work

Extended 2026-10-14 after the "why does the session keep stopping?" investigation.
Items 1-10 are the original rules; 11-14 are the anti-stop rules that were
missing and whose absence caused repeated restarts.

Before doing any work in this repository:

1. Run `python3 tools/continuity.py resume`.
2. Treat `workflows/current/ACTIVE_TASK.json` and the latest checkpoint as authoritative.
3. Log the visible user message verbatim with `continuity.py log --kind user`.
4. Never restart a completed operation or discard a newer active task because an older chat summary appears.
5. Record every material action/result/error and every long-running process ID.
6. Checkpoint before/after long operations, after material results, on errors, before ending the turn, and at least every 55 minutes while active.
7. Keep permanent accepted knowledge inside the named style under `styles/`; keep only running work in `workflows/current/payload/`.
8. Do not mark remote sync complete without updating the target's `SYNC.json` entry with its real ID/result.
9. Do not commit credentials, hidden system instructions, private connector tokens or raw sensitive identity media.
10. Run `python3 tools/studio.py validate` before a milestone commit.

## Anti-stop rules (2026-10-14)

11. **Arena starts every turn at `main`.** A fresh clone/worktree does not carry
    the previous turn's branch. First run `bash tools/session_recover.sh`; if a
    candidate branch holds the active task, `bash tools/session_recover.sh --merge <ref>`.
    Never rebuild from zero and never force-push over that branch.
12. **Check the workspace budget before and after any materialization:**
    `python3 tools/repo_budget.py` (must stay under ~100 MB; the snapshot cap is
    ~128 MB). Over budget means the next turn silently loses the newest files
    (see `operations/incidents/INC-20261011-001`). Fix with `/tmp` staging,
    `python3 tools/materialize.py compact` and `git gc --prune=now`.
13. **Stage Drive materializations outside the snapshot:** the connector writes to
    `./google_drive/`; immediately `mv google_drive/* /tmp/monarch-stage/`.
    Keep only small derived artifacts (analysis JSON, sheets) in the repository.
14. **Rebuild the render environment first, not last:** `bash tools/bootstrap_env.sh`
    (`--check` to verify only). Python dependencies do not survive a turn; without
    this the session burns its first 20-30 minutes re-discovering numpy/Pillow/cv2/ffmpeg.

If a response/process stops, query the recorded process and execute the exact next action in `RESUME.md`; do not begin again from zero.
