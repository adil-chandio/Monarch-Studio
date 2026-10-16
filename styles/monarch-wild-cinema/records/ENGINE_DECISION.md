# ENGINE DECISION — what was surveyed, and what was taken

**Date** 2026-10-16 · **Workflow** WF-07 · **Trigger** `CINEGO <topic>`

The brief: *"look at all of Monarch Studio's editing and build the next-level
animation and style for this channel — the kind that has the strength to carry
a video to viral."*

This file records what was read, what was taken, what was consciously rejected
and what was newly built. Provenance matters more than novelty: a synthesis
whose sources are unrecorded cannot be improved later, only replaced.

---

## 1 · What was surveyed

| source | extent | what it contributed |
|---|---|---|
| `styles/monarch-stickman-animation/MONARCH_SKILL_MOTION_EDIT.md` | M1–M23 ledger, gate table | the defect taxonomy: caption under platform UI, strobe transitions, mono mix, sub-pixel camera stall, jerk ceilings, contrast failures |
| `…/MONARCH_SKILL_LONGFORM_16x9.md` | M24–M38, episode contract | the re-fit law, the zoom floor, eased-ramp freezing, the VO-masked spectral target, the shard/OOM hazard, label-consumed-once |
| `studio/editor-brain/MONARCH_EDITOR_BRAIN.md` | 15 sections | the twelve habits, hook engineering table, three cadences, anti-repetition windows, the three-pass review |
| `styles/premium-motion-editing/knowledge/*` | 17 chapters | near/far 2.5D maps and their deformation rule, the three transition treatments, the caption-pill rejection, the approved V5/V6 policy |
| `styles/premium-motion-editing/src/motion.py` | 112 lines | the reference implementation of the multi-plane camera (read, then generalised) |
| `styles/monarch-noir-film/` | style + films | film grammar: counter spine, callback ladder, villain with a body, the quiet ending |
| `channel/FORENSIC_AUDIT_2026-10-16.md` | full audit | the numbers that set the strategy: 955,681 vs 16 views; 84.3 % of views from five videos; the reused-content exposure |
| `channel/productions/MF-01/` | the delivered episode | the grade, the score structure, the two-pass mix, the overlay grammar, the shot-plan shape |
| `workflows/wf06_yt_agent_crew/` | 7 files | the eight-agent crew this engine plugs into (A03 writes the plan, A05 renders, A07 gates) |

## 2 · What was taken, and what was rebuilt

| capability | decision | reason |
|---|---|---|
| 2.5D parallax | **rebuilt and generalised** | WF-05's implementation is portrait-native and plate-specific; this one builds a depth field, an overscanned environment canvas and a normalised camera that any plate can use |
| depth heuristic | **replaced** | WF-05 keys on supplied foreground maps; automatically keying on brightness *inverts on this channel's own grade* — focus energy is the correct proxy (register T01) |
| transition families | **carried, with ceilings** | depth push / diagonal whip / feathered cut kept; dip, wipe and a bounded dissolve added; each measured against the luma ceiling |
| grade | **new** | no existing style grades cinematic wildlife; four looks with a fixed stage order, LUT-driven and SIMD-optimised |
| type system | **new, doctrine-compliant** | WF-01's extruded headline + WF-05's tilt entry, reimplemented as cropped numpy ROI compositing (82 ms → 12.7 ms) with a measured contrast report |
| data graphics | **new** | none of the three existing styles can draw a chart; the audit says the explanation is the differentiator, so charts became first-class |
| score | **new, laws inherited** | true stereo at the source, exact concatenation (no `apad`), two-pass mix, −4 dBFS ceiling, decoded-domain peak measurement |
| caption pills / karaoke band | **rejected, structurally** | rejected by the channel owner in WF-05; the type system here has no pill renderer to accidentally enable |
| stickman 3-D rig | **not used** | it is a character engine for a different pillar (P4); importing it would have produced a stickman video, not a wildlife one |

## 3 · What is genuinely new to this studio

1. **Declarative episode plans.** `PLAN.json` is a complete description of a
   film: shots, durations, depth hints, camera, effects, type and chart values.
   An agent authors a film without writing code.
2. **Automatic depth from focus energy**, gated by an explicit plateau.
3. **Atmospheric depth separation** — the far plane mixed toward the computed
   far colour so parallax reads on soft generative plates.
4. **Depth-aware particles** that participate in the parallax instead of
   sitting on top of it.
5. **Animated data graphics** as an engine primitive, with an enforced honesty
   law about unsupported comparisons.
6. **A 14-gate report generated from the decoded delivery**, not from the
   renderer's own claims.
7. **A single-plan vertical cut** whose crop follows each shot's declared
   subject rect.

## 4 · Costs recorded honestly

- The naive first implementation ran at **1.10 s/frame**; the optimised engine
  runs at **≈0.40–0.50 s/frame** on 2 cores. Eleven measurements and seven
  rewrites are recorded in the failure register rather than quietly discarded.
- The engine has **no system ffmpeg dependency** but **does** require
  `opencv-python-headless`; the virtualenv is not snapshot-persisted and is
  rebuilt per sandbox.
- **No human listening pass is claimed** for any rendered audio. Measurement
  scope is stated wherever a number is reported.
- The engine has been proven on the MF-01 plate library. A new episode with new
  plates requires new depth rects; the `hybrid` mode degrades safely, but the
  rect must still be authored per shot.
