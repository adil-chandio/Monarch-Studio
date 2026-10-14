# Architecture

## 1. Two planes: permanent knowledge and active execution

Editing Monarch Studio is a multi-style production system with a strict separation:

- **Permanent plane:** `styles/`, `characters/`, `studio/`, accepted project history and Git commits.
- **Active plane:** the one task under `workflows/current/`, its payload, exact next action, chat/action journal and process ledger.

This prevents an active sandbox from becoming an unsearchable archive and prevents completed knowledge from disappearing when chat context or processes reset.

## 2. Permanent style boundary

A style is identified by stable style ID, workflow code and canonical external IDs. Display names alone are insufficient because similarly named legacy workflows exist.

Each style directory owns its renderer, timeline, audio, assets/plates, DNA/events, gates, prompts, decisions, failures/fixes, releases and knowledge index. Historical certified layouts remain intact when moving files would change runtime behavior.

Current styles:

- `styles/monarch-stickman-animation` — WF-01 / SHADEGO.
- `styles/monarch-noir-film` — WF-03 / NOIRGO.

`styles/registry.json` is the human-facing library. `studio/registry.json` retains machine workflow/runtime contracts.

## 3. Single active workflow

`workflows/current/` contains:

- `ACTIVE_TASK.json` — immutable task ID, status, goal, acceptance criteria, next action and process ledger;
- `RESUME.md` — human handoff capsule;
- `JOURNAL.jsonl` — SHA-256 hash-chained ordered events;
- `CHAT_TRANSCRIPT.jsonl` — visible user/assistant messages linked to journal hashes;
- `payload/` — only files actively being produced or changed.

Atomic temp-write + `fsync` + rename protects state writes. File locking prevents concurrent checkpoint writers.

## 4. Checkpoints and recovery

Each checkpoint creates:

```text
operations/continuity/checkpoints/<task>/<sequence-time>/
  checkpoint.json
  HANDOFF.md

operations/continuity/outbox/<task>/<sequence-time>/
  checkpoint.json
  STATUS.md
  SYNC.json
```

The checkpoint records active state, journal head, Git state, changed paths, process ledger and payload SHA-256 inventory. `SYNC.json` tracks GitHub, Drive, Notion, Linear and Google Docs independently.

Recovery precedence:

1. measured files and immutable media identity;
2. current active state + valid journal chain;
3. latest immutable checkpoint;
4. Git history and sync ledger;
5. permanent style knowledge;
6. chat summary only as a convenience.

## 5. Completion transaction

A task can complete only after its durable outputs and knowledge are promoted into its named style. `continuity.py complete` then archives state/journal/transcript under `operations/history/<task-id>/` and resets `workflows/current/` to idle.

No evidence is overwritten: new versions are added, superseded records are archived and contradictions are reconciled explicitly.

## 6. Compatibility runtime

Historical code was authored in ephemeral `/home/user` sandboxes. `tools/studio.py hydrate` creates a disposable repo-local compatibility tree under `.runtime/<workflow>/home/user`:

- text copies receive generated path replacement;
- binary files are hardlinked/copied;
- WF-03's former `workflows/wf03_monarch_noir_film` layout is recreated;
- WF-01 shared fonts/`toon.py`/`shade.py` and current studio brain are supplied as required.

Permanent source bytes remain unchanged.

## 7. Remote architecture

- GitHub stores code, history and small checkpoint evidence.
- Drive stores large masters, source/repository bundles and recovery exports.
- Notion stores browsable knowledge and decisions.
- Linear stores task/blocker state and acceptance criteria.
- Google Docs stores a portable status/proof hub.

Connector-only systems can update only while Arena Agent Mode is active. Pending updates remain in the tracked outbox and are never lost or silently marked complete.

## 8. Vendor boundary

- `vendor/effectcraft` is a pinned optional future orchestration/effects adapter.
- `vendor/awesome-opus5-5-videos` is a pinned research index.

Their Git links are permanent; working trees may remain uninitialized in sparse checkouts to control workspace size. They retain upstream licenses.

## 9. Storage and sparse archive

The repository can keep large binary source in Git while using sparse checkout locally. `tools/materialize.py`/Git sparse-checkout policy may omit archived binary assets from the live Arena worktree without removing them from Git history. Drive remains the disaster-recovery mirror for milestone bundles.

## 10. Authority precedence

- Media identity: Drive file ID + MD5 + measured gate.
- Active execution: valid journal + latest checkpoint.
- Style implementation: committed source and style index.
- Character identity: locked current assets/hashes.
- Narrative copies: Notion/Linear/Docs, subject to explicit reconciliation.

See `RECONCILIATION.md` for current concrete conflicts.
## WF-05 · Premium Motion Editing (2026-10-15)

Permanent style: `styles/premium-motion-editing/`; trigger `MOTIONGO <topic or reference>`. Its current production policy retains V5 clean layout and accepted V6 motion/depth/transition/sound, rejecting the V6 bottom caption pills. Source history, a 17-chapter codex, reusable clean compositor, templates and regression tests are indexed in that style. Other workflows and historical identities are preserved.
