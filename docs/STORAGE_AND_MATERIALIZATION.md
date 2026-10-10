# Storage and materialization

## Why compact mode exists

Arena workspace snapshots are best-effort capped near 128 MB. Keeping a 60+ MB worktree, a 60+ MB Git object database, duplicate recovery archives and populated vendor clones can exceed that boundary and silently omit files on the next turn.

The permanent source is not deleted. Git and Drive keep it; compact mode only marks heavy tracked assets as sparse-omitted in this local worktree.

## Commands

```bash
python3 tools/materialize.py status
python3 tools/materialize.py compact   # control plane + source/gates/indexes
python3 tools/materialize.py full      # required before a full render/package rebuild
```

Both mode changes require a clean worktree. `studio.py` preserves hash records for tracked sparse-omitted files and reports deferred verification as a warning.

## Compact set

Compact mode retains:

- active task, journal, transcript, checkpoints and outbox;
- documentation, schemas, CI, tests and all control tools;
- both style root contracts/notes plus renderer source, brain, gates, event/data records and knowledge indexes;
- WF-01 fonts required by compatibility hydration;
- Monarch authority metadata, tooling, board/Bible and previews;
- studio registry/editor brain and all root governance files.

It omits the largest reconstructable render inputs from the local worktree, notably WF-01 generated audio assets and WF-03 plate/VO directories. They remain Git blobs and are also represented in Drive recovery bundles.

## Vendor repositories

Vendor projects remain pinned as gitlinks. Initialize only when needed:

```bash
git submodule update --init vendor/effectcraft
git submodule update --init vendor/awesome-opus5-5-videos
```

Remove populated vendor working trees after use if snapshot capacity is tight; the pins remain.

## Full recovery

1. Clone the GitHub repository when available, or clone the Drive Git bundle.
2. Apply checkpoint delta bundles in the documented order when using Drive recovery.
3. Run `python3 tools/materialize.py full`.
4. Run `git submodule update --init` only for vendor work being used.
5. Run `python3 tools/studio.py validate` and the test suite.
6. Run `python3 tools/continuity.py resume` and continue the exact next action.