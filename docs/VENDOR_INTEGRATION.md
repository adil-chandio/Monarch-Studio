# Vendor integration plan

## EffectCraft

Pinned as `vendor/effectcraft` at commit `f8b2552d1c4fd1ae5051dae3786719dc5bdb3ff8`.

EffectCraft is a candidate **optional orchestration/effects adapter**, not a dependency retroactively claimed by the certified WF-01 or WF-03 renders. Safe adoption path:

1. keep Monarch manifests and gates authoritative;
2. wrap EffectCraft behind a small adapter rather than importing workflow state into vendor code;
3. map one disposable preview operation first;
4. compare frame count, duration, color and audio against the native path;
5. add explicit capability and failure handling;
6. certify only after measured equivalence or a documented new-version gate.

Potential boundaries include preview generation, isolated effects, MCP-based tool invocation, metadata inspection and future render orchestration. The historical Python/Pillow/FFmpeg renderers remain the reproducibility baseline.

## awesome-opus5-5-videos

Pinned as `vendor/awesome-opus5-5-videos` at commit `756290289742535eb0ac3817548f152e9759cc70`.

This repository is a **research index**. Use it to discover techniques, production patterns and evaluation ideas. Do not:

- treat prompts as Monarch authority;
- copy the full catalogue into studio documentation;
- remove attribution;
- let generic prompt patterns override measured workflow rules or locked character identity.

Any adopted technique should be rewritten as a studio-specific, testable requirement with provenance noted.

## Upgrade policy

Submodule updates are intentional changes:

```bash
git -C vendor/effectcraft fetch --tags
git -C vendor/effectcraft checkout <reviewed-commit>
git add vendor/effectcraft
```

Review upstream license/security changes, run `tools/studio.py validate`, and record compatibility impact before committing the new pointer.