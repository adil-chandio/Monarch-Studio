# 12 · Continuity, persistence and zero-waste recovery

## State is not the artifact

The critical failure in V5 was not merely forgetting a sentence. A completed master, ignored runtime clips and the virtual environment disappeared after a workspace refresh while small source/receipts survived. A JSON field saying “done” did not preserve the MP4 bytes.

Protect only essential pending-upload files in a bounded snapshot-safe spool. Keep disposable caches and dependencies ignored. Respect the platform's file/patch limits. Once master and source copies are independently verified in Drive, return large media to external/ignored storage. A stable Drive ID plus hash is the durable recovery authority; do not permanently fill Git with full masters.

## Resume hierarchy

Current active task → hash-chained journal → exact resume capsule → latest checkpoint/process ledger → actual file existence/hashes → verified remote receipts → permanent style history. A condensed chat summary cannot override newer durable state.

Run `python3 tools/continuity.py resume` at every new turn. Query a recorded process before starting another. Prefer one blocking wait to repeated short polling. If a log stream disconnects, inspect process liveness, stage state, file and QA; V6 had a status-stream error even though all stages had completed successfully.

## Cache correctness

Skip a stage only when its input fingerprint, successful receipt and required artifacts all agree. Check all required scene files, not merely the last filename. An absent output invalidates a “done” receipt. A changed caption does not justify regenerating selected voice or every source object. A failed early mask does not justify abandoning the reference for new slides.

## Delivery truthfulness

Do not log “presented” before the viewer succeeds. Do not log “uploaded” before the connector returns a real ID. Do not log “synced everywhere” when only one target succeeded. Independent remote size/hash verification comes after upload. Explicitly correct a mistaken success claim in the journal.

A background Python job cannot silently perform future connector actions after the agent turn ends. The active agent must continue through QA, presentation and upload while runnable steps remain. Platform interruptions cannot be promised impossible; durable recovery can be engineered.

## Completion and repeated continue

Call the completion/archive operation while the task is still active rather than manually setting a terminal status first. The V5 archival trap is preserved as a lesson and covered by the foundation's lifecycle regression work. After delivery, a bare “continue” means check state and return the completed output—not begin the same edit again. A new explicit enhancement request starts a new version and leaves the old master intact.

Maintain a checkpoint before/after long operations, after material errors/results and at least every 55 minutes while active. The watcher supplements event checkpoints; it does not replace them. Store visible user/assistant messages accurately; do not manufacture missing compacted history or export hidden instructions/credentials.
