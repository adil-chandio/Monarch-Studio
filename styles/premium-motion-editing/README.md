# WF-05 · Premium Motion Editing

**Trigger:** `MOTIONGO <topic or reference>` · aliases: WF-05 / WF5.

> **Latest user policy, 15 Oct 2026:** V5 clean editorial direction + accepted V6 depth/motion/transition/sound improvements. **No V6 bottom caption pills or active-word lower strip by default.** Integrated scene typography remains primary. Technical QA never overrides user feedback.

## Start here in a new chat

1. Run `python3 tools/continuity.py resume` and inspect any active task/process.
2. Read [FRESH_CHAT](FRESH_CHAT.md) and [approved profile](data/approved-profile.json).
3. Read [the complete codex](knowledge/MASTER_CODEX.md), or use [the chapter index](knowledge/INDEX.md) to load the relevant sections.
4. Inspect [the actual reference project](projects/einstein-flow-state/README.md), not only a text summary.
5. Work in the single active task under `workflows/current/payload/`; do not write a new production into the permanent style folder.

## What is preserved

- All available V5/V6 source, selected speech clips, fonts/licenses, timing, measured QA and real delivery receipts.
- Fourteen observed visual metaphors and their argument functions.
- Eighteen concrete failures with symptoms, causes, fixes and regressions.
- The latest acceptance decision, including the rejected V6 caption UI.
- A clean production policy, data-driven compositor, near/far motion module, export verifier, templates, creative prompts and new-chat handoff.
- Cross-platform links/receipts, source hashes, evidence boundaries and a coverage audit.

**No new full-length hybrid master is claimed by this foundation.** The accepted profile is distinct from the historical V6 master, which still contains its rejected caption experiment. The generic compositor is not an asset generator: new topics require new matching script, narration and actual motion media.

## Commands

```bash
python3 tools/studio.py list
python3 styles/premium-motion-editing/src/wf05.py inspect
python3 styles/premium-motion-editing/src/wf05.py new \
  --project-dir workflows/current/payload/my-motion-film \
  --project-id my-motion-film --topic 'Your actual topic'
python3 styles/premium-motion-editing/src/wf05.py validate \
  workflows/current/payload/my-motion-film/project.json
```

Fill the new brief, claim/rights/motion plan and actual prepared media first. Empty templates intentionally fail rendering. When ready, use `render project.json --preview`, then `render project.json`, then `verify project.json`. Run long exports with the process tools and record their ID. No command silently synthesizes a voice, generates a slideshow, uploads to Drive or marks delivery complete.

## Standard layout

- `data/` — approved profile, DNA, motion/audio grammar, metaphor and media catalogs.
- `knowledge/` — detailed operating chapters and the complete codex.
- `src/` — current production policy/compositor/verifier (no rejected pill renderer).
- `templates/` — new brief, shot/asset register, project/timeline and QA/delivery forms.
- `prompts/` — director, quality reviewer and recovery contracts.
- `projects/einstein-flow-state/` — actual V5/V6 case and immutable original implementations.
- `records/` — exact user request, source inventory, evidence limits, history and sync receipts.
- `assets/fonts/` — licensed typefaces; full masters stay on Drive.
- `brain/` — prior concepts/novelty memory, not automatic reuse of the old story.

## External authority

Use [data/links.json](data/links.json) for verified current destinations and [data/media-catalog.json](data/media-catalog.json) for exact master/source IDs and hashes. GitHub owns code history; Drive owns heavy media; Notion/Docs expose knowledge; Linear exposes task/resume state. Preserve other workflows and their identities.

## Accuracy boundaries

This is reference-derived motion and 2.5D compositing, not new 3D geometry. The source anecdote was not independently fact-checked. Word-paced highlighting was not certified alignment and is now rejected as default. Missing pre-init history/scratch files are explicitly listed rather than invented. See [evidence scope](records/EVIDENCE_SCOPE.md).

## Live release status

[Live publication receipt](https://drive.google.com/file/d/1IP1ykbtg6Hvk3SqiZGkF_uRsj8v9vRje/view) records final source-package and GitHub/main results. An immutable source snapshot is not an active task capsule; consult the actual repository continuity state before resuming work.
