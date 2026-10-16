# Editing Monarch Studio

A durable multi-style production repository for video editing, animation, characters, workflow implementations and exact recovery state. The system separates **permanent style knowledge** from the **single task currently running**.

## Start here—always

```bash
python3 tools/continuity.py resume
python3 tools/studio.py list
python3 tools/studio.py validate
```

[`START_HERE.md`](START_HERE.md) and [`workflows/current/RESUME.md`](workflows/current/RESUME.md) are the authoritative recovery entry points. Never restart from the beginning while they identify an unfinished task.

## Channel intelligence

Monarch Cam (`@monarch-cam`, `UCfYdmsLO4Q8_IHklTyYieLg`) has its own permanent strategy folder:

- [`channel/FORENSIC_AUDIT_2026-10-16.md`](channel/FORENSIC_AUDIT_2026-10-16.md) — full channel forensic audit
- [`channel/CONTENT_PLAN_2026-10-16.md`](channel/CONTENT_PLAN_2026-10-16.md) — 90-day forward plan, packaging rules and compliance gates
- [`channel/data/channel_snapshot_2026-10-16.json`](channel/data/channel_snapshot_2026-10-16.json) — raw captured evidence

## Permanent style library

| Style | Trigger | State | Permanent implementation |
|---|---|---|---|
| **Monarch Stickman Animation** | `SHADEGO <topic>` | Parked; IZZAT v2 is current R1 delivery | [`styles/monarch-stickman-animation`](styles/monarch-stickman-animation/) |
| **Monarch Noir Film** | `NOIRGO <topic>` | Active with explicit Film-#3 drift; films 1–2 are R1 | [`styles/monarch-noir-film`](styles/monarch-noir-film/) |
| **WF-05 · Premium Motion Editing** | `MOTIONGO <topic or reference>` | V5 clean direction + accepted V6 motion; lower caption pills rejected | [`styles/premium-motion-editing`](styles/premium-motion-editing/) |

Each named style contains its implementation, assets, audio/plates, data, prompts, tools, gates, measured results, decisions, failures/fixes, source provenance and a permanent knowledge index.

Shared locked character authority is under [`characters/monarch`](characters/monarch/).

## Active-work boundary

```text
styles/                         permanent accepted style knowledge
workflows/current/              exactly one running task
operations/continuity/          immutable checkpoints + sync outbox
operations/history/             completed task state/chat archives
studio/                         shared registry and editor brain
characters/                     shared character authorities
vendor/                         pinned external Git submodules
```

`workflows/current/payload/` is cleared/promoted when a task finishes. Permanent history never depends on chat memory alone.

## Crash-proof continuity

`tools/continuity.py` provides:

- atomic active-task state;
- exact next action;
- hash-chained append-only action journal;
- visible user/assistant transcript from task initialization;
- running-process IDs and resume instructions;
- immutable checkpoint packages;
- per-platform GitHub/Drive/Notion/Linear/Docs sync status;
- 55-minute checkpoint watcher plus event-driven checkpoints;
- permanent task promotion and active-slot cleanup.

Typical commands:

```bash
python3 tools/continuity.py status
python3 tools/continuity.py log --kind result --message "Measured result"
python3 tools/continuity.py checkpoint \
  --summary "What completed" \
  --next-action "One exact next operation" \
  --commit --push
python3 tools/continuity.py watch --interval-seconds 3300 --commit --push
```

Arena connectors cannot run unattended between agent turns. If a remote update cannot execute, it remains explicitly pending in the checkpoint `SYNC.json` and is drained when the agent is active again; it is never silently treated as complete.

## Portable historical execution

Certified historical source retains its original `/home/user` assumptions. The generated compatibility runtime rewrites only disposable copies:

```bash
python3 tools/studio.py hydrate wf01
python3 tools/studio.py run wf01 -- python3 brain/concept.py status

python3 tools/studio.py hydrate wf03
python3 tools/studio.py run wf03 -- \
  python3 workflows/wf03_monarch_noir_film/src/film_window.py --help
```

Generated runtime is under `.runtime/` and is ignored.

## Local storage safety

The committed archive can use a compact sparse worktree in Arena while every tracked file remains in Git and Drive:

```bash
python3 tools/materialize.py status
python3 tools/materialize.py compact
python3 tools/materialize.py full   # before complete render/package rebuilds
```

See [`docs/STORAGE_AND_MATERIALIZATION.md`](docs/STORAGE_AND_MATERIALIZATION.md).

## Cross-platform source of truth

- **GitHub:** canonical version history and checkpoint commits.
- **Google Drive:** large masters, source/repository bundles and disaster recovery.
- **Notion:** browsable style knowledge and decisions.
- **Linear:** active status, blockers and acceptance criteria.
- **Google Docs:** portable human resume/proof hub.

Every checkpoint creates an outbox package; each platform is marked independently with its real ID/result.

## Accuracy boundaries

1. Full delivered masters and raw sensitive identity media remain on Drive by exact ID/hash.
2. THE SHADOW and THE WINDOW are fully sourced. 4:00 AM is R2 gate-evidenced; AB KARO ABHI is R3 delivery-only. Missing source is not invented.
3. Only visible user/assistant messages from continuity initialization can be captured verbatim. Hidden system instructions, credentials and unavailable compacted chat are excluded.
4. EffectCraft and awesome-opus5-5-videos are pinned external sources, not retroactively claimed as historical render dependencies.

## Documentation

- [`docs/STYLE_LIBRARY_STANDARD.md`](docs/STYLE_LIBRARY_STANDARD.md)
- [`docs/CONTINUITY_AND_RECOVERY.md`](docs/CONTINUITY_AND_RECOVERY.md)
- [`docs/CROSS_PLATFORM_SYNC.md`](docs/CROSS_PLATFORM_SYNC.md)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/SOURCE_MAP.md`](docs/SOURCE_MAP.md)
- [`docs/RECONCILIATION.md`](docs/RECONCILIATION.md)
- [`docs/QUALITY_GATES.md`](docs/QUALITY_GATES.md)
- [`docs/PRIVACY_AND_ASSETS.md`](docs/PRIVACY_AND_ASSETS.md)
- [`docs/STORAGE_AND_MATERIALIZATION.md`](docs/STORAGE_AND_MATERIALIZATION.md)

Monarch-authored material is proprietary unless separately stated. Third-party submodules and bundled fonts retain their own licenses.
## WF-05 new-chat entry

For Premium Motion Editing read [FRESH_CHAT](styles/premium-motion-editing/FRESH_CHAT.md), [approved profile](styles/premium-motion-editing/data/approved-profile.json) and the [complete codex](styles/premium-motion-editing/knowledge/MASTER_CODEX.md). The latest user correction rejects V6 lower caption pills/word strip. Historical V5/V6 sources remain evidence, not the default for a new topic.
