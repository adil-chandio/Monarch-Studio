# Adding an editing/animation style

1. Allocate a stable style ID and next workflow code; never reuse a retired identity.
2. Create `styles/<style-id>/` following `STYLE_LIBRARY_STANDARD.md`.
3. Add `style.json`, `workflow.json`, `README.md` and `knowledge/INDEX.md`.
4. Register the style in both `styles/registry.json` and `studio/registry.json` with exact Drive/Notion/Linear/Docs IDs.
5. Define trigger grammar, allowed questions, activation state, response language, formats and objective gates.
6. Keep renderer, timeline, audio, assets/data and gate code inside the style boundary.
7. Declare large external media by Drive ID/hash rather than committing unsuitable masters.
8. Record reproducibility class and all source drift explicitly.
9. Add a compatibility hydration adapter if historical absolute paths exist.
10. Open production work with `continuity.py init`; never use a permanent style directory as scratch space.
11. On acceptance, promote active payload/knowledge to the style, update its index, checkpoint, sync all platforms and complete the task.
12. Run tests, manifest generation and `studio.py validate` before the milestone commit.

A similar display name is never sufficient. Style ID + workflow code + external authority IDs must agree.