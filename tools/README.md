# Repository tools

## `continuity.py`

Controls the single active task, exact resume state, hash-chained journal, visible chat transcript, process ledger, checkpoints, hourly watcher, sync outbox and completion archive.

```bash
python3 tools/continuity.py resume
python3 tools/continuity.py status
python3 tools/continuity.py checkpoint --summary "..." --next-action "..." --commit --push
python3 tools/continuity.py watch --interval-seconds 3300 --commit --push
```

## `studio.py`

Controls the normalized registry, validation, integrity manifest and generated compatibility runtimes.

```bash
python3 tools/studio.py list
python3 tools/studio.py doctor
python3 tools/studio.py validate
python3 tools/studio.py hydrate wf01
python3 tools/studio.py run wf01 -- python3 brain/concept.py status
python3 tools/studio.py clean all
python3 tools/studio.py manifest --write
```

Hydration never rewrites permanent historical source; it creates generated copies under `.runtime/`.

## `materialize.py`

Keeps the Arena worktree below snapshot capacity without deleting tracked history.

```bash
python3 tools/materialize.py status
python3 tools/materialize.py compact
python3 tools/materialize.py full
```

Use full mode before complete renders that need archived audio/plate assets.

## `wf02.py`

WF-02 permanent style discovery, preservation audit, new-topic planning contract and scoped recovery ZIP. Never implicitly renders, synthesizes speech, uploads or pushes.

```bash
python3 tools/wf02.py audit
python3 tools/wf02.py brief "<topic or reference>"
python3 tools/wf02.py pack --out .runtime/WF02_STYLE_MEMORY.zip
```

Audit checks immutable project hashes, available raw-history copies/coverage, release QA and startup/registry alignment. Pack includes WF02 source/history plus shared recovery tooling, not unrelated style binaries or missing original chat. Source/ZIP hashes and remote sync receipts remain distinct.
