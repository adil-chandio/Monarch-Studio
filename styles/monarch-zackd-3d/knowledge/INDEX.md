# WF-02 permanent knowledge index

Start with [../START_HERE.md](../START_HERE.md), [master PLAYBOOK](PLAYBOOK.md), [failure/correction ledger](FAILURES_AND_FIXES.md), [full SOP](PRODUCTION_SOP.md) and [available-history coverage](history/COVERAGE.json). Run `python3 tools/wf02.py audit` before future work. The original release lessons below are preserved.

---

# WF-02 durable knowledge

- [Film source and rebuild guide](../projects/EMS-20261014-001/splinter-v2/README.md)
- [Reference study, exact generated script, medical scope](../projects/EMS-20261014-001/splinter-v2/docs/SCRIPT_AND_PRODUCTION.md)
- [Source IDs and hashes](../projects/EMS-20261014-001/splinter-v2/data/SOURCES.json)
- [Actual master QA](../projects/EMS-20261014-001/splinter-v2/data/QUALITY_REPORT.json)
- [Voice/mix measurements](../projects/EMS-20261014-001/splinter-v2/data/AUDIO_REPORT.json)
- [GLB validation](../projects/EMS-20261014-001/splinter-v2/data/GLTF_VALIDATION.json)
- [Absolute-time geometry regression](../projects/EMS-20261014-001/splinter-v2/data/DETERMINISM_REPORT.json)
- [Initial full-frame probe, retained honestly](../projects/EMS-20261014-001/splinter-v2/data/DETERMINISM_INITIAL_FULLFRAME.json)
- [Final delivery receipt](../projects/EMS-20261014-001/splinter-v2/data/DELIVERY_RECEIPT.json)

## Lessons retained

- A current Drive folder can contain newer production assets absent from the checkout. Inspect it before rebuilding from zero.
- This task recovered an animated GLB but no final MP4 in that project folder. Reuse was explicitly credited, not claimed as new modelling.
- Minimal Linux lacked NSS/NSPR libraries for Chromium. Extracting the pinned package's bundled libraries fixed the offline renderer without storing credentials or system installations.
- File-scheme `fetch` is not a reliable GLTF-loader transport. The renderer intercepts a virtual browser origin and serves only allowlisted local source/vendor files.
- Imported position morphs lacked normal morphs. Generate normal deltas for a correctly lit swelling dome.
- Never multiply an animated object's scale each absolute-time frame; cached constant tracks may not restore it. Assign scale absolutely and test out-of-order/repeated timestamps.
- Batch repeated cells with hardware instancing but preserve their independent animated transforms. The film is still actual geometry animation.
- Keep the clinical explanation conditional: spontaneous expulsion is not guaranteed, and infection is not treatment. Distinguish the shallow example from the deep-fragment example.
- Technical tests do not certify artistic perfection, every pronunciation, or clinical validity. Retain those limits in the delivery record.
- Repository tests must clean only their own compatibility runtimes, not `clean all` while unrelated renders are running. Dependency virtual environments must remain outside the integrity manifest.


## KAANTA v3 — motion / sound enhancement

- [v3 source and rebuild guide](../projects/EMS-20261015-002/splinter-v3/README.md)
- [Editable C2 camera/actor controls](../projects/EMS-20261015-002/splinter-v3/data/motion.json)
- [915-frame motion sample table](../projects/EMS-20261015-002/splinter-v3/data/MOTION_SAMPLES.csv)
- [Motion QA](../projects/EMS-20261015-002/splinter-v3/data/MOTION_QA.json)
- [Strict full-frame determinism](../projects/EMS-20261015-002/splinter-v3/data/DETERMINISM_REPORT.json)
- [Turnover provenance](../projects/EMS-20261015-002/splinter-v3/data/POSTFX_REPORT.json)
- [Sound/voice comparison](../projects/EMS-20261015-002/splinter-v3/data/SOUND_COMPARISON.json)
- [Delivery receipt](../projects/EMS-20261015-002/splinter-v3/data/DELIVERY_RECEIPT.json)

Lessons: preserve the liked version and voice; use absolute C2 rails instead of camera resets; close/lock a measured jaw gap before moving wood; place cells during the actual sentence; share motion cues with SFX; keep a turn-over transition frame-native and record its containing-chunk recomposition. Explicit CPU 2D canvas contexts resolved the small cold brand-mark raster difference, enabling strict full-frame tests. Lossless composite capture matched native browser screenshots. A VSM/clearcoat-free trial did not help performance and was not used. Native30fps is real rendering, not interpolated24fps. Avoid overstating mathematical smoothness as universal artistic perfection.


## KAANTA v4 — user's explicit restraint correction

[Source/rebuild](../projects/EMS-20261015-003/splinter-v4/README.md) · [design controls](../projects/EMS-20261015-003/splinter-v4/data/design.json) · [motion controls](../projects/EMS-20261015-003/splinter-v4/data/motion.json) · [sound/score](../projects/EMS-20261015-003/splinter-v4/data/SOUND_DESIGN_REPORT.json) · [type/full-frame proof](../projects/EMS-20261015-003/splinter-v4/data/DETERMINISM_REPORT.json) · [actual-master QA](../projects/EMS-20261015-003/splinter-v4/data/QUALITY_REPORT.json) · [publishing credit](../projects/EMS-20261015-003/splinter-v4/assets/music/ATTRIBUTION.md)

The user liked the core but called gratuitous additions cheap/cringe. Respond with subtraction, not a higher effect count: remove interface framing, pills/panels, alerts and page-turns; let anatomy and voice lead. Use real3D typography sparingly (two story beats, not constant competing layers). Simplify camera direction changes and oscillatory object motion. Cleaner selective cut-face shading/polygon offsets avoid fake floating shadows/acne; revised membrane/adipose surfaces preserve depth without toy-like clutter.

V4's8 soft procedural textures are distinct from its original arranged music. The score uses selected, credited FluidR3 CC-BY3.0 instrument-note recordings, not a reference song. Preserve the publishing credit in description/source and tell the user. Musical buildup and negative space can be measured; artistic taste/retention/ASMR cannot be certified by those measurements.

Ephemeral runtime files were missing on restoration. Recover dependencies and needed reference media from recorded sources without restarting completed versions. Keep previous project/master hashes unchanged.


## KAANTA v5 — decisive action, not global speed-up

[Rebuild/source](../projects/EMS-20261015-004/splinter-v5/README.md) · [comparison](../projects/EMS-20261015-004/splinter-v5/data/MOTION_COMPARISON.json) · [motion QA](../projects/EMS-20261015-004/splinter-v5/data/MOTION_QA.json) · [master QA](../projects/EMS-20261015-004/splinter-v5/data/QUALITY_REPORT.json) · [sound anchors](../projects/EMS-20261015-004/splinter-v5/data/SOUND_DESIGN_REPORT.json)

Preserve the clean-v4 correction. V5 shortens actual authored actions:surface pull1.17→0.42s,deep pull1.97→0.72s; camera moves0.40–0.58s with settles. Record comparisons against the real prior controls rather than claiming an unmeasured quality percentage. Faster moves benefit from short bounded real-scene shutter sampling; captions should remain center-time sharp and different scenes must never blend across the cut. A two-sample proof showed excessive contour separation, so the selected shutter is shorter and center-weighted across3 evaluations.

Material detail was changed in code: localized pad ridges/pore variations, cellular skin relief/fibrous dermis, directional wood grain and brushed steel. Release friction leads into the transient so its peak—not the clip start—can match the visual anchor. Numerical/per-frame checks supplement actual encoded-sample review; they do not certify taste/perfection. Voice and music sample publishing credit remain preserved.


## KAANTA v6 — new shots, same voice (explicit scope choice)

[Source/rebuild](../projects/EMS-20261015-005/splinter-v6/README.md) · [shot/focus plan](../projects/EMS-20261015-005/splinter-v6/data/shot_plan.json) · [director proof](../projects/EMS-20261015-005/splinter-v6/data/DIRECTOR_QA.json) · [focus A/B proof](../projects/EMS-20261015-005/splinter-v6/data/FOCUS_QA.json) · [voice/script lock](../projects/EMS-20261015-005/splinter-v6/data/NARRATION_LOCK.json) · [final QA](../projects/EMS-20261015-005/splinter-v6/data/QUALITY_REPORT.json)

The user chose a meaningful shot-design rebuild while keeping narration/script—not another count of added effects. V6 adds an independent radial skin-surface insert,three detailed hero-cell groups,cell tracking and geometry-depth focus. Eight of nine camera views differ materially; one useful wide anchor stays. Eight declared semantic cuts are intentional, with C2 control inside shots. No shutter blending across cuts.

A sparse depth-focus gather produced visible duplicate contours; a depth-guided separable Gaussian replaced it. A rectangular grid hole and reversed radial winding were corrected before freezing production. The inherited cross-section draws actors in front of its reveal plane; use a separate intact-surface insert rather than falsely treating those offsets as physical buried geometry. Focus A/B changes the scene PNG but leaves raw caption pixels identical. Preserve limits:stylized anatomy,approximate focus,not clinician-verified microscopy/optics or universal aesthetic certification.

Eight tactile cues and the original arranged score are rebalanced for macro perspective. Retain the included FluidR3 CC-BY publishing credit. Prior source/master files remain unchanged.


## KAANTA v7 — bounded organic membrane motion, same edit

[Source/rebuild](../projects/EMS-20261016-001/splinter-v7/README.md) · [V7-specific proof](../projects/EMS-20261016-001/splinter-v7/data/ORGANIC_QA.json) · [actual-master QA](../projects/EMS-20261016-001/splinter-v7/data/QUALITY_REPORT.json)

After the user repeated the enhancement request instead of choosing a new scope, preserve the prior voice/script and no-clutter corrections. V7 is a focused detail pass, not a nine-new-shot claim: three independent1617-vertex membranes, bounded absolute-time folds/leading lobes and softer layered material. Evaluate deformation from immutable rest vertices for each shutter time, never by accumulating frame state. The isolated browser A/B changes picture pixels while retaining caption pixels; repeated geometry returns exactly. Technical art direction is not validated cell biology or a guarantee of retention/ASMR/perfection.

Do not reuse inherited QA as current evidence: historical V6 receipts live in a clearly labeled baseline directory, current V7 source/pixel/focus/organic proofs are separate. Native frame signatures remain frozen through rendering; no duplicate live job. All915 native frames,1101 colour evaluations,93 shutter frames and775 depth-focus frames were accounted;32/32 actual-master gates passed. Remote master/source/companions were size/MD5 verified. Prior releases and publishing music credit remain preserved.


## KAANTA v8 — respond to whole-film scope across the whole film

[Source/rebuild](../projects/EMS-20261016-002/splinter-v8/README.md) · [actual V7 comparison](../projects/EMS-20261016-002/splinter-v8/data/UPGRADE_QA.json) · [preview](../projects/EMS-20261016-002/splinter-v8/data/PREVIEW_QA.json) · [native QA](../projects/EMS-20261016-002/splinter-v8/data/QUALITY_REPORT.json)

The user explicitly asked for the whole animation after a focused V7 membrane pass. V8 changes all9 camera compositions in3 scene groups,opening crop,bounded drifts,material/highlight/background treatment,irregular grain/wood relief,36 merged dermal micro-bundles (8100vertices),localized compression/spread,tool approach arcs and8-cue/music dynamics. The arcs return to zero offset before gripping. Keep the same narration,safety qualifiers,semantic cut structure and credited original arrangement; do not falsely call inherited meshes/newly rewritten scenes newly authored.

Full915-frame270px review precedes native rendering. Current pixel-return/focus/organic proofs and4/4 V7-control comparisons supplement34/34 native-master gates and encoded scene/action samples. All915frames,1101scene evaluations,93shutter frames and775focus frames accounted. All6 remote files size/MD5 verified; preserve prior versions and the publishing credit. Isolate baseline QA rather than relabeling it as current. Technical/art-direction improvement is not histology,validated tissue mechanics,independent ear review,perfect art,ASMR or retention certification.
