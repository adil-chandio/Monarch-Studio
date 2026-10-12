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

## Open-Generative-AI

Pinned as `vendor/open-generative-ai` at commit `6b704b0806bf07b435586ff182fb54fffe64253f` (upstream `Anil-matcha/Open-Generative-AI`, MIT).

This is a Next.js/Electron AI image, video and lip-sync studio. Its hosted generation calls `api.muapi.ai`, which needs the user's own MuAPI key entered in the app settings. Its local model path (sd.cpp, Wan2GP) needs a CUDA/ROCm GPU on the user's machine.

Adoption boundaries for Monarch:

1. Use it as a standalone studio UI or as a generation adapter. Monarch manifests and gates stay authoritative.
2. Never store MuAPI keys in the repository. Keys belong to the user's own browser or environment settings.
3. Generated clips enter Monarch only through the normal delivery gates, after measured review.
4. Its submodules (`packages/Vibe-Workflow`, `packages/Open-Poe-AI`, `packages/Open-AI-Design-Agent`) are pinned by upstream. Install them with `git submodule update --init --recursive`.

Local preview setup, run from the submodule directory:

```bash
ELECTRON_SKIP_BINARY_DOWNLOAD=1 npm install
npx next dev -H 0.0.0.0 -p 3000
```

In the sandbox, the UI loads, but generation is blocked because `api.muapi.ai` is not on the outbound allowlist.

## EffectCraft build status

`vendor/effectcraft` is pinned at `f8b2552`. The Rust toolchain is not available in the sandbox, and `crates.io` and `static.rust-lang.org` are unreachable, so the workspace cannot be built here. Build it on a machine with Rust 1.95+ and network access to crates.io.

## Upgrade policy

Submodule updates are intentional changes:

```bash
git -C vendor/effectcraft fetch --tags
git -C vendor/effectcraft checkout <reviewed-commit>
git add vendor/effectcraft
```

Review upstream license/security changes, run `tools/studio.py validate`, and record compatibility impact before committing the new pointer.