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

## Batch 2 vendor repositories (2026-10-12)

| Submodule | Pin | Licence | Sandbox status | Adoption note |
|---|---|---|---|---|
| `vendor/OpenMontage` | `9327439` | AGPL-3.0 | Python deps installed; `tests/` run: 884+ pass in the contracts run, full suite ~91% green before the 15-minute timeout; no failures shown | Agentic video production system with 12 pipelines (incl. `animation`, `character-animation`, `cinematic`). Real providers need user API keys (Kling/fal, Veo, Sora, ElevenLabs). Local path: Piper TTS + FFmpeg + Remotion. **AGPL-3.0:** network use of a modified copy requires offering its source; review with legal before merging its code into Monarch. |
| `vendor/react-bits` | `2139cb3` | MIT + Commons Clause | Vite dev server runs on port 5173 through `workflows/current/payload/react-bits-preview/vite.preview.config.mjs` (allows the sandbox preview host; vendor config untouched) | React/Next.js animated component library. **Commons Clause:** may be used inside an application or website but not sold or redistributed alone. Some components are in a paid "pro" catalogue. |
| `vendor/browser-use` | `c75e847` | MIT | `browser_use` 0.13.11 imports OK in a separate venv | AI browser agent. Browser actions need Chromium, and the Playwright CDN is blocked in the sandbox, so browser runs are not possible here. |
| `vendor/cc-switch` | `28dc519` | MIT | Not runnable here | Tauri (Rust) desktop assistant that switches AI coding-tool providers. Build needs Rust and crates.io, which are blocked. |
| `vendor/FreeCAD` | `23a5e34` (upstream `main`, shallow checkout) | LGPL-2.1 | Not buildable here | C++ parametric 3D CAD. Needs conda/pixi (blocked), Qt and OpenCASCADE. The earlier short pin `ec6852e` could not be fetched by SHA, so the gitlink was re-pinned to `23a5e34`. Record a full SHA if `ec6852e` is recovered. Working tree is about 426 MB. Run `git submodule update --init --depth 1 vendor/FreeCAD` on a suitable machine. |

Environment notes: the sandbox has 2 vCPU and 3 GB RAM. Running Next.js dev, Vite and npm installs in parallel exhausted memory and stalled the shell, so run one heavy process at a time.

## Batch 3 vendor repositories (2026-10-12)

| Submodule | Pin | Licence | Sandbox status | Adoption note |
|---|---|---|---|---|
| `vendor/Agent-Reach` | `94f06c1` | MIT | Offline tests: 606 pass, 1 fails (`test_config::test_get_configured_features` expects all channels off, but this machine has some configured). | CLI that gives an AI agent read/search access to platforms such as Twitter, Reddit, YouTube and GitHub. Several channels reuse the user's logged-in browser or cookies. Do **not** supply Monarch or third-party credentials to it, and keep it out of the production render path. Its live channels need outbound access that the sandbox does not allow. |
| `vendor/Scrapling` | `7a68493` | BSD-3-Clause | Installed editable. Offline parser check passes (CSS selection on local HTML). | Adaptive web-scraping framework. Use it only within each site's terms of service and robots rules. Scraped footage or images carry their own copyright, so do not add them to Monarch assets without a licence. |

## Keeping all vendor source in the repo without filling the workspace

Every vendor repo is kept in the repository as a pinned submodule (commit SHA recorded in Git). Its full source is on GitHub at that pin. Populated working trees are heavy: all ten repos together are about 440 MB, over 12,000 files, plus FreeCAD at about 400 MB. That is above the snapshot cap (about 128 MB or 10,000 files), so populated trees are released by default and restored on demand.

Use `tools/vendor/materialize.sh`:

```bash
tools/vendor/materialize.sh status             # populated or pin-only, with sizes
tools/vendor/materialize.sh one react-bits     # restore one repo at its pin (shallow)
tools/vendor/materialize.sh all                # restore all repos at their pins
tools/vendor/materialize.sh release all        # remove working trees and module cache, keep pins
```

The text skill files from these repos are copied into `docs/skills/vendored/` (see its `PROVENANCE.md`), so the skills are always readable in the repo.

## Upgrade policy

Submodule updates are intentional changes:

```bash
git -C vendor/effectcraft fetch --tags
git -C vendor/effectcraft checkout <reviewed-commit>
git add vendor/effectcraft
```

Review upstream license/security changes, run `tools/studio.py validate`, and record compatibility impact before committing the new pointer.