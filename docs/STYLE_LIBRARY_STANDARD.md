# Permanent style-library standard

Every editing/animation style has one stable human-readable ID and one permanent directory under `styles/`.

## Required contents

```text
styles/<style-id>/
  README.md              complete human operating guide
  style.json             permanent style identity
  workflow.json          trigger/runtime/delivery contract
  knowledge/INDEX.md     map of all durable knowledge
  src/                   renderer, timeline, audio and gate code
  assets/ or plates/     required production inputs
  data/                  DNA, events and measurements
  brain/                 concept/novelty memory when applicable
  projects/              accepted completed project implementations
  records/               historical states and reconciliation evidence
```

Historical layouts may remain flatter when moving files would break certified code. In that case `knowledge/INDEX.md` maps every file without changing provenance.

## No-loss completion contract

A completed task is not removed from `workflows/current/` until its target style contains:

1. final source and required assets;
2. exact commands/toolchain and dependency versions or bounds;
3. what was attempted, what failed and why;
4. decisions and alternatives rejected;
5. measured gate report and master identity;
6. Drive IDs/hashes and Notion/Linear/Docs record IDs;
7. chat/action checkpoint archive;
8. updated style index and repository manifest.

Never overwrite old evidence. Add a new version and reconciliation entry.