from pathlib import Path
import json
R=Path(__file__).resolve().parents[4];S=R/'styles/premium-motion-editing'
def put(p,s):(S/p).write_text(s.strip()+'\n',encoding='utf-8')
put('README.md',r'''# WF-05 · Premium Motion Editing

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
''')
put('AGENTS.md',r'''# WF-05 production instructions

Inherit the repository AGENTS.md and run continuity resume first.

1. Read `data/approved-profile.json` and `FRESH_CHAT.md` before any production.
2. Latest user correction: V6 bottom caption pills / active-word lower strip are rejected. Default = integrated clean type; separate subtitles off. Plain subtitles require an explicit brief request. Bottom-positioned integrated headlines are allowed.
3. `projects/.../versions/v5` and `v6` are immutable historical evidence. Do not use the archived V6 pill renderer as the production default. Do not rewrite old QA as user approval.
4. Reuse the quality grammar, not the Einstein script/audio/assets for unrelated topics. New briefs require matching script, narration, rights and actual temporal motion.
5. No whole-frame still slideshow or camera-only zoom may substitute for independently changing subjects/objects/layers.
6. Keep photographed edges/pale parts intact. A new reference needs new masks/geometry; historical coordinates are not universal.
7. Production inputs live in the active task; accepted knowledge and append-only project history live here.
8. Validate profile/plan, inspect actual encoded frames, and verify master/source cloud checksums. Do not mark completion on encoder exit alone.
9. Record real tool outcomes and known limits. Do not claim full 3D modeling, certified word alignment, independent listening or complete unavailable history.
10. On completed work plus ambiguous continue, return/recover the verified file. A new explicit revision starts a new version without deleting previous masters.
''')
put('FRESH_CHAT.md',r'''# New chat · WF-05 / MOTIONGO

## Pasteable instruction

> Use **WF-05 · Premium Motion Editing** in the connected `adil-chandio/Monarch-Studio` repository. Run `python3 tools/continuity.py resume` first. Read `styles/premium-motion-editing/AGENTS.md`, `FRESH_CHAT.md`, `data/approved-profile.json` and `knowledge/INDEX.md`. Preserve V5's clean editorial direction plus accepted V6 motion/depth/transition/sound improvements. **Do not use V6 bottom caption pills or the active-word lower strip.** Inspect the real reference, keep natural narration, use meaningful independent motion rather than slides, validate and deliver a playable export with verified Drive master/source recovery. Resume existing work before generating anything. My topic/reference: ______.

## Small mandatory context pack

- `data/approved-profile.json` — binding caption/branding/motion policy.
- `RESUME_STATE.md` + `data/links.json` — current style state and destinations.
- `projects/einstein-flow-state/ACCEPTANCE.json` — accepted versus rejected facets.
- `knowledge/03_REFERENCE_AND_STORY.md` — translation/factual boundaries.
- `knowledge/12_CONTINUITY_AND_STORAGE.md` — no duplicate work / no lost master.
- `CHECKLIST.md` — finish through actual delivery, not a progress promise.

## Branches of work

**Active task exists:** read its latest capsule and query the recorded process. Continue its exact next action. Never initialize a second task over it.

**Completed task and only “continue”:** recover/return the last verified output. Do not spend credits rerendering it. Ask one targeted scope question only if a new revision is truly ambiguous.

**Explicit new topic/reference:** initialize one task. Clarify only consequential missing inputs. Create a fresh argument/metaphor/asset plan. The case files teach the standard; they are not content to relabel for a new topic.

**Explicit revision:** keep source, voice and good clips; change the requested component and version the output. Latest user feedback wins over a newer-looking experimental preset.

## Tool boundaries

A trigger cannot access a repository or app that is not connected. Check actual tool availability, load the named connectors, use IDs from real results, and never ask for credentials. New speech may require a registered voice selection; existing selected audio does not. Do not claim an unavailable renderer or hidden background automation is working.

## Final response pattern

Lead with the actual requested artifact and verified viewing/download link. Summarize material changes, format/duration and recovery status briefly in Roman Urdu. State any real limitation precisely. Do not end with only “rendering / continue later” when the next step can still be executed.
''')
put('CHECKLIST.md',r'''# WF-05 production checklist

## Before work
- [ ] Read active task, process ledger, latest user instruction and approved WF-05 policy.
- [ ] Search existing project/media/voice/deliveries before generating or creating duplicates.
- [ ] Decide reference-adaptation versus new-production scope and rights.
- [ ] New project has matching topic, claim ledger, script, voice and actual motion plan.

## Picture/type
- [ ] Native subject changes or independently animated layers—not only a whole-frame still zoom.
- [ ] Meaningful metaphor and causal transitions; one dominant idea per beat.
- [ ] Natural voice determines semantic picture timing.
- [ ] Subject edges, pale highlights, hands, hair, strings, shoes, props and shadows preserved.
- [ ] Integrated text readable and clear of protected subjects at entry, peak, hold and exit.
- [ ] No V6 lower caption pills/word strip. Plain subtitles only when explicitly requested.
- [ ] No old source English residue, unwanted social tags or inherited social ending.

## Output
- [ ] Exact frame budget and complete H264 High/yuv420p + AAC export, intended format/FPS.
- [ ] Faststart, full decode, nonempty audio, levels/peaks and actual review scope recorded.
- [ ] Encoded samples inspected; important transitions checked densely.
- [ ] No claims beyond evidence: true 3D, word-perfect alignment, scientific facts, human listening.

## Delivery/recovery
- [ ] Actual local artifact exists; presentation succeeds before claiming it.
- [ ] Master uploaded to the project's WF-05 area; independent remote size/hash match.
- [ ] Source recovery package/IDs/hashes verified.
- [ ] Each external platform updated with its own real receipt; others remain honestly pending.
- [ ] Accepted learning/project source archived before clearing the active slot.
- [ ] Heavy pending spool returned to ignored/external storage only after cloud verification.
- [ ] Completed task does not restart on an ambiguous continue.
''')
put('RESUME_STATE.md',r'''# WF-05 · Permanent style resume state

**Style:** Premium Motion Editing · **Trigger:** MOTIONGO <topic or reference>.

## Latest binding feedback

15 Oct 2026: use V5 clean editorial direction and accepted V6 depth/motion/transition/sound gains. Reject V6 bottom caption pills and the active-word lower strip as default. Integrated scene headings remain primary. Optional plain subtitles require an explicit request. Original versions remain as history.

## What the reference project proves

V5 and V6 are actual delivered, source-backed 63.1-second motion edits, not new still slides. Both have verified Drive master/source identities and measured codec/frame/decode evidence. They use the exact selected narration at natural speed. V6's technical success does not mean its lower caption design was accepted.

## What this foundation adds

A permanent knowledge library, explicit acceptance policy, failure register, reusable clean compositor and new-project templates, quality/recovery gates and cross-platform identity. No new full-length combined-policy master is claimed. Check `records/FOUNDATION_STATUS.json` and `data/links.json` for current publication/test receipts.

## Resume order

Run repository continuity resume → inspect any active task/process → read approved profile → inspect the real reference/case → read component-specific chapters → continue or initialize the explicitly requested new task. Do not render the case again merely to demonstrate memory.
''')
put('HUB.md',r'''# WF-05 · Premium Motion Editing — HUB

Start with [FRESH_CHAT.md](FRESH_CHAT.md), [the approved policy](data/approved-profile.json) and [the complete codex](knowledge/MASTER_CODEX.md).

**Current direction:** V5 clean editorial composition + accepted V6 depth/motion/transitions/sound. **No V6 bottom caption pills or word-highlight strip.**

- [Knowledge chapters](knowledge/INDEX.md)
- [Reference project and acceptance](projects/einstein-flow-state/README.md)
- [Production checklist](CHECKLIST.md)
- [New-project templates](templates/)
- [Current engine](src/)
- [Metaphor/novelty memory](data/metaphor-bank.json)
- [Complete lesson register](data/lessons.json)
- [Exact media identities](data/media-catalog.json)
- [Verified platform links](data/links.json)
- [Evidence scope and gaps](records/EVIDENCE_SCOPE.md)
- [Source inventory](records/SOURCE_INVENTORY.json)

Existing Drive folder: https://drive.google.com/drive/folders/1C7vAECkURqySJDgpJ_YunUtyOWh8Zuri

The canonical code is in the connected repository under `styles/premium-motion-editing/`. Human mirrors must link to these same policy/source identities. Do not replace another workflow's registry entry.
''')
put('CHANGELOG.md',r'''# WF-05 change log

## Foundation · 2026-10-15

- Registered a distinct permanent Premium Motion Editing style in the existing studio system.
- Preserved all available V5/V6 source, selected audio, fonts/licenses, timelines, QA, actual delivery identities and visible task history.
- Promoted latest user feedback: V5 clean editorial direction; V6 non-caption gains; V6 lower caption pills/word strip rejected.
- Added data-driven production policy, reusable clean compositor/motion/verifier, templates, director/reviewer prompts and new-chat contract.
- Added fourteen observed shot/metaphor mappings, eighteen incident/root-cause/fix lessons, toolchain/QA/recovery guides and a coverage audit.
- Explicitly separated measured, reported, proposed and unavailable evidence. No new full-length hybrid master is claimed.
- Organized the existing WF-05 Drive folder and established cross-linked knowledge/task hubs; consult actual publication receipts for results.

Historical V5/V6 originals are not rewritten by this change log.
''')
put('projects/einstein-flow-state/README.md',r'''# Reference project · Einstein / Flow State

This is the actual source-backed case that defines the initial WF-05 level. It is **not** the default script for every new topic.

## Acceptance

- **V5:** clean layout/content-level reference.
- **V6:** accepted non-caption motion/depth/transition/sound improvements; **bottom caption pills / active-word strip rejected** by the user on 15 Oct 2026.
- Current production policy: `../../data/approved-profile.json`.
- No new full-length combined-policy master was rendered/claimed by the foundation task.

## Preserved evidence

`versions/v5/` and `versions/v6/` retain all available source/voice/font/timing/QA/delivery files unchanged. These old programs reproduce their historical versions, including the rejected V6 caption experiment. Do not run them as a new production default.

[SHOT_BREAKDOWN.md](SHOT_BREAKDOWN.md) gives all fourteen measured source/output intervals, concrete props, metaphor logic and protected details. Exact clip trims, thirty-one title states and thirty-six display phrases remain in each `timeline.json`. The audio clips are the spoken authority, not an invented certified transcript.

The original reference is supplied user material credited off-frame to @RIT2RAJ_DAS. Its 720×1282 footage was cropped by one pixel at top/bottom and upscaled for 1080 typography/export. Native changing frames—not newly generated slideshow images—drive the retained scene animation.

## Recovery

Use the real master/source IDs and hashes in each `DELIVERY.json` or `../../data/media-catalog.json`. Prefer downloading the already delivered master to rerendering a completed job. For an explicit new revision, restore the source, inspect current policy, preserve unchanged assets and version the output.

The historical anecdote/AI rhetoric was translated as supplied, not independently verified science/history. See the evidence scope for unavailable pre-init chat and missing early scratch/source states.
''')
put('assets/README.md',r'''# Asset authority

The shared production assets here are licensed fonts with their OFL license texts. The case-specific selected speech remains in each immutable version folder, with original hashes/provenance. It is not narration for unrelated new topics.

Full reference/master/recovery media stay on Drive by actual IDs/hashes in `data/media-catalog.json`. No raw sensitive personal identity media is duplicated into WF-05. A future project registers its own source, creator, permission, hash and purpose in `asset-register.csv`.
''')
put('prompts/MASTER_DIRECTOR.md',r'''# WF-05 director contract

Read the current approved policy and active task before acting. Your goal is a clear moving argument at the reference level, not maximum decorative complexity.

1. Restate the intended takeaway and distinguish style reference from content adaptation.
2. Inspect actual media and inventory already completed assets/voice before generating.
3. Build a claim ledger and easy Urdu-English semantic script; do not invent certainty.
4. Develop three feasible metaphor systems internally; compare fit, readability, causal motion, novelty and rights.
5. Choose a coherent world. Specify each subject/object action, depth plateau, protected detail, headline, spoken window, transition reason and sound event.
6. Require real temporal source/layer changes. A still plus global zoom fails the intent even if an image-difference metric changes.
7. Use clean integrated type. Do not add V6's bottom pills or word-highlight strip. Plain subtitles need explicit permission; SRT may remain separate.
8. Match narration and picture naturally; do not speed up a selected voice simply to fill a copied duration.
9. Prototype risky frames/motion, fix them internally, then render once through a recorded resumable process.
10. Inspect encoded output, state evidence scope accurately, present the actual artifact and verify both master/source cloud hashes. Keep working while the next step is actionable.

Do not copy the Einstein plot into a new topic. Do not cast the user's personal hero or add Monarch branding without a request. Do not claim new 3D geometry, word-perfect ASR or an independent listening test if you did not perform those things.
''')
put('prompts/QUALITY_REVIEWER.md',r'''# WF-05 quality reviewer contract

Review the actual encoded file, not just the creator's description. Compare it with the current brief, approved policy and reference level.

Return separate findings for technical validity, creative fidelity, latest user preference, and delivery/recovery. For each failure provide timestamp/shot, visible symptom, likely cause, smallest safe fix and required recheck.

Priority defects: slideshow substitution; narration/scene mismatch; old text/tag residue; missing hair/hands/shoes/strings; deformed subject from depth mapping; unreadable or colliding type; rejected lower caption UI; social outro; clipping/silent audio; wrong codec/pixel format; incomplete file; false presentation/upload claim; missing recoverable source.

Do not approve aesthetics from pixel deltas alone. Do not call a statistical audio check a listening test. Technical PASS does not override user rejection. Preserve good work and rerun only changed stages. Label uncertainty instead of inventing a clean bill of health.
''')
put('prompts/RECOVERY_HANDOFF.md',r'''# WF-05 recovery handoff template

- Active task ID / status / latest checkpoint:
- Last exact user instruction and any newer correction:
- Current style policy ID and subtitle mode:
- Last successful operation (actual evidence):
- Running process ID and how to query it:
- Expected artifacts versus files currently present:
- Verified remote master/source IDs, sizes and hashes:
- Changed inputs and cache fingerprints:
- Genuine blocker, if any:
- Exact next command/tool action:
- Operations that must NOT be repeated:
- Review/measurement scope and known gaps:

A log stream failure is not proof that rendering failed. A done receipt is not proof its media bytes survived. Query, inspect and resume; do not regenerate the voice or replace motion with slides. If delivery is already verified and the user only says continue, return that output rather than start again.
''')
put('prompts/MOTIONGO.md',r'''# MOTIONGO <topic or reference>

This is WF-05, not SHADEGO, NOIRGO, CHAOSGO or another workflow. Load `FRESH_CHAT.md` and the current policy, then execute the production runbook from the actual resume state.

Default look: editorial lavender/periwinkle motion collage, meaningful subject/object changes, concise integrated condensed type, natural easy Urdu-English narration, restrained dimensional treatment and sound. No V6 bottom caption pills or active-word lower strip. No automatic Monarch/social branding.

A new topic requires fresh matching content, not a renamed case replay. A supplied reference must be inspected. Tool-required voice selection or missing rights/access may require user input; do not ask repetitive approvals for steps you can safely execute. Finish through verified delivery and durable source, not merely a render-start message.
''')
# Resolve already created remote identities immediately; never invent pending IDs.
p=S/'data/links.json';d=json.loads(p.read_text());d['drive_sections'].update({'lessons_qa':'1eDJXUaZjzJXM5hnMKVbh2x-InkdUPIcR','source_recovery':'1ZuOZJRiF_7CntW4Yrh80wxf4vbS8vi3V','future_projects':'1g_X6FzsS_Uss_d-VF-mPzwDOtsVr-IST'});d['linear_resume_issue']='https://linear.app/monarchmation/issue/MON-67/00-resume-key-motiongo-wf-05-premium-motion-editing-state-and-links';d['linear_resume_issue_id']='091b76e2-1d28-43d0-a280-c55ef7dc70a4';d['linear_resume_identifier']='MON-67';p.write_text(json.dumps(d,indent=2)+'\n')
print('WF-05 entrypoints, prompts, checklist and cross-platform identities written.')
