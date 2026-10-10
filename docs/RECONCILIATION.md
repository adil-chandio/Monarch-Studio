# Cross-source reconciliation

## Method

The connected Notion, Linear, Google Drive and Google Docs records do not always advance in lock-step. The repository therefore separates:

- **observed facts** — file IDs, hashes, dimensions, timestamps, checked-in implementation;
- **normalized state** — the safe operational interpretation used by the studio registry;
- **unresolved drift** — contradictions that require an authoritative human choice or additional source package.

No missing implementation or certification is inferred from a project description alone.

## WF-01

### Aligned facts

- Canonical code: WF-01; trigger: `SHADEGO <topic>`.
- Linear project ID: `4d053022-acab-4836-8f13-5ccb7e043c17`.
- Notion row and registry record say **Parked**.
- Latest fully evidenced delivery is **IZZAT v2**: 75.19 s, 1080×1920, 24 fps, 33 shots, 32 transitions, −11.6 LUFS, 19/19 engine gates, Drive `1fu_g2HTNZVRqE3XBKdUKZoj6O8tIdkpu`, MD5 `8d91be52ab969e0b23f21bf6bab0df85`.
- Brain registry generation is 6 and records six delivered videos.
- MON-56 defines activation, build, proof and record-update rules.

### Normalized state

**PARKED, implementation complete.** A new run must explicitly activate the workflow. The trigger contract allows at most a topic clarification and required voice-audition click.

### Minor historical inconsistency

The SHADEGO document says “20 gates” by combining 19 workflow-engine checks and EDITOR BRAIN gate #20. Some earlier delivery text says “19/19.” The repo preserves this distinction rather than rewriting 19/19 as 20/20:

- 19/19 = concrete workflow renderer/audio/delivery checks.
- gate #20 = cross-video novelty/brain gate for a new concept.

## WF-03

### Fully reconciled films

1. **THE SHADOW v1** — Film #1, R1 fully sourced, 156.92 s, 1920×1080, 24 fps, 27/27 gates.
2. **THE WINDOW v1** — Film #2, R1 fully sourced, 155.0 s, 1920×1080, 24 fps, 27/27 gates.

THE WINDOW is later than the current text of MON-57, the Notion page and Google Doc HUB, which still identify THE SHADOW as the last delivered film. The Drive resume and complete film-2 source package are newer operational evidence.

### Film-number conflict

Two distinct artifacts claim Film #3:

| Evidence | Claim | What is present | What is missing |
|---|---|---|---|
| `GATES_NOIRGO_4AM_v2.md` + `04AM_v2_FINAL.mp4` | “4:00 AM — Jo Jaagta Hai,” WF-03 Film #3, 60.0 s horizontal | Final MP4 identity, MD5, measured metadata, 11/11 limited checks | Script, renderer, DNA/events, full 27-check gate, source package, dedicated Notion record |
| `AB_KARO_ABHI_v1_vertical_noir.mp4` | “AB KARO ABHI — Procrastination Kills,” WF-03 Film #3, 75.0 s vertical | MP4 identity/metadata and filename claim | Source, gate report, resume block, dedicated Notion/Linear record |

AB KARO ABHI is newer in Drive than 4:00 AM and intentionally changes format to 1080×1920, but it cannot silently supersede 4:00 AM as canonical Film #3 because the inspected hubs were not updated and no gate/source bundle was found.

### Normalized state

**ACTIVE_WITH_DRIFT.** Films #1 and #2 are fully authoritative. 4:00 AM is a gate-evidenced delivery (R2). AB KARO ABHI is delivery-only evidence (R3). Before another numbered film:

1. choose which artifact, if either, is canonical Film #3;
2. provide/recover its complete source package and canonical gate report;
3. update Drive resume, MON-57, Notion project/registry and Google Doc HUB together;
4. then allocate the next film number.

### Brain registry drift

- Workflow-local `brain/registry.json`: generation 2, SHADE + THE SHADOW.
- Studio `studio/editor-brain/brain/registry.json`: generation 3, SHADE + THE SHADOW + THE WINDOW.

The studio registry is newer for cross-workflow concept history. The workflow-local registry is retained because it was packaged with the film-1/film-2 historical source, and changing it would alter provenance.

## Monarch character

### Historical issue drift

MON-58 describes STICK face/body v3 and MON-60's description still reads like an approval-stage plan, but MON-60's title/state and the Drive/character state prove the rebuild completed:

- STICK face v4, MD5 `5c18bd13e79fb7274a63a236487ef0d9`;
- STICK body v4, MD5 `c791940a822b52a7dbd00523db1ae0f7`;
- Bible v2 and Master Board v2; character is locked.

The repository therefore treats the v4 assets as current. Earlier issue descriptions are retained as history, not current truth.

### Locked state

- REAL: face v5 + body v2.
- STICK: face v4 + body v4, explicitly using the studio stickman face rather than a realistic human face.
- Bible v2 + Master Board v2.
- `CUSTOM_HERO_STATE.md` marks the system locked and directs future work to use the character, not redesign it.

### Voice ambiguity

`monarch voice.aac` is a real Drive artifact, but its intended production use was not specified. It is not assumed to be a cloning/identity license, not checked into Git, and not wired into either workflow.

## Scope exclusions

- WF-02 “Powerful Personality” is a separate legacy workflow despite overlapping naming. It was not requested as one of the two current workflows and no implementation from it is mixed into WF-01.
- Rejected/superseded character versions remain in the Drive archive and are not promoted.
- Full masters and raw personal references remain external by policy; their hashes and IDs are the repository's reproducibility anchors.

## Required reconciliation record for future changes

Any future source conflict should be documented with:

1. the exact systems and IDs that disagree;
2. timestamps/hash evidence;
3. selected normalized value;
4. whether the decision was human-authorized or mechanically derived;
5. records updated across all four connected systems.