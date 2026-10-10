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