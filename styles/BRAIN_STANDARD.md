# Video brain standard

Every editing and animation style under `styles/` has one video brain. The brain is the durable memory of how that style is made. A new chat, a fresh clone, or a sandbox reset must be able to continue the work from it without anyone re-deriving the method.

## Where it lives

```text
styles/<style-id>/brain/video-brain/
  MINDSET.md         identity, non-negotiables, what premium means for this style (hand-edited, versioned in git)
  TOOLCHAIN.md       tools, versions, exact commands, access and blockers (hand-edited)
  PIPELINE.md        production recipe, current version, numbered steps (hand-edited)
  NEXT_LEVEL.md      prioritised upgrade backlog, plus a "Done" section kept for history (hand-edited)
  SESSION_LOG.md     append-only: every working turn                 S-###
  PROBLEMS.md        append-only: symptom, cause, fix, verified-by  P-###
  SKILLS.md          append-only: reusable skill with evidence      K-###
  STRATEGIES.md      append-only: decision, alternatives rejected   ST-###
  VIDEO_LOG.md       append-only: every video or lookdev version    V-###
```

Plus `styles/<style-id>/knowledge/INDEX.md`, which points to the brain first.

## Rules

1. **Append-only ledgers.** Only `tools/brain.py` writes them. Correct an old entry by adding a reconciliation entry (`brain.py resolve` for problems). Never edit or delete an old entry. Git keeps the history either way.
2. **Hand-edited files change in place.** MINDSET, TOOLCHAIN, PIPELINE and NEXT_LEVEL are versioned in git. Keep the old version in a "Done" or "History" section when it matters.
3. **Log as you go.** Every working turn writes a session entry. Every failure writes a problem entry. Every reusable method writes a skill entry. Every approach choice writes a strategy entry. Every video or lookdev writes a video entry with settings, timing, review and status.
4. **Review before claiming.** A video's status moves to `accepted` only after a frame-by-frame review is logged. Never claim premium or finished before that.
5. **Start from the brain.** Run `python3 tools/brain.py resume <style-id>` before any work on the style. Read the open problems and the NEXT_LEVEL backlog first.
6. **Check it.** `python3 tools/brain.py check` must pass before a milestone commit. It fails if a registered style has no complete brain or if ledger IDs repeat.

## Relation to other records

- `projects/<slug>/` holds the cross-style project archive: chat log, process log, tools, artifacts (Drive links). The brain holds the style-level method and history.
- `workflows/current/` holds only the one running task.
- Large media stays out of Git. Record Drive IDs and checksums in the VIDEO_LOG entry.

## Storage rule (confirmed by the user, 2026-10-13)

Videos (final and lookdev) are stored only on Google Drive. Git and the repo hold the record: Drive ID, size, SHA-256, settings and review in VIDEO_LOG and `projects/<slug>/ARTIFACTS.md`. GitHub Releases are blocked from the sandbox, and the repo is public, so no media goes into Git or Releases. Small non-media files (scripts, docs, JSON) live in the repo as usual.
