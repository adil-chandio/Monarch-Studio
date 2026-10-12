# Vendored skill files: provenance

These are copies of the agent-skill, reference and pipeline text files from the pinned vendor repositories. They are copied so the skills are readable and searchable inside Monarch Studio without initialising submodules. The full source of each repository stays a pinned submodule under `vendor/` (see `docs/VENDOR_INTEGRATION.md`). Do not edit these copies as Monarch source. Change upstream, then re-copy and update the pin.

Only text skill files are included (`SKILL*.md`, `skills/`, `skill/` trees). Binaries, minified bundles and application source are excluded. `cc-switch` is excluded entirely: its only skill-related code is UI source (`src/components/skills/`), not skill documents.

| Copied from | Pin (submodule commit) | Licence | Files | Notes |
|---|---|---|---|---|
| `vendor/OpenMontage` (`.agents/skills`, `.claude/skills`, `skills/`) | `9327439` | AGPL-3.0 | 1,463 | Pipeline and provider skill docs. AGPL network-use duties apply if modified code is served. Review with legal before redistributing these copies. |
| `vendor/browser-use` (`browser_use/skills`, `skills/`) | `c75e847` | MIT | 36 | Browser-agent skill docs. |
| `vendor/Agent-Reach` (`agent_reach/skill`) | `94f06c1` | MIT | 9 | Agent internet-access skill docs. Uses logged-in channels: keep credentials out. |
| `vendor/Scrapling` (agent skill) | `7a68493` | BSD-3-Clause | 1 | Scraping skill doc. Use only within site terms and robots rules. |

Other vendored repositories (effectcraft, react-bits, open-generative-ai, awesome-opus5-5-videos, FreeCAD) have no skill directory, so nothing is copied from them.

Regenerate: copy the same paths from each submodule after `git submodule update --init --depth 1 -- vendor/<name>`.
