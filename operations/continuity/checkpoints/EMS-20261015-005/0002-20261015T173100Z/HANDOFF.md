# Resume capsule — EMS-20261015-005

**Status:** `active`  
**Title:** WF-02 KAANTA v6 cinematic shot-design revision — scope confirmation  
**Style:** `monarch-zackd-3d`  
**Checkpoint sequence:** 2  
**Last checkpoint:** 2026-10-15T17:31:00Z

## Goal

Create a meaningful further cinematic/animation/editing/sound improvement rather than repeatedly stacking small effects. Confirm whether new shots and/or a new hook/script are allowed, preserve the no-clutter correction and previous deliveries, then produce the agreed new version.

## Acceptance criteria

- [ ] Confirm V6 redesign scope before another expensive full render; do not invent user approval
- [ ] Retain the earlier clean/premium constraint: no gratuitous HUD, panels, counters, beeps or transitions
- [ ] Preserve all previous source/master versions and medical safety meaning
- [ ] After scope selection, deliver actual rendered/verified video and editable source in the confirmed WF-02 workflow with appropriate music credit

## Exact next action

Continue EMS-20261015-005. Fork v6 from permanent v5, restore disposable tools if absent, implement new shot-scoped camera/focus design and hero cell geometry; proof framing before native render. Do not alter voice/script or prior masters.

## Running processes

- None recorded.

## Recovery command

```bash
python3 tools/continuity.py resume
```

## Durable evidence

- Active state: `workflows/current/ACTIVE_TASK.json`
- Hash-chained action journal: `workflows/current/JOURNAL.jsonl`
- Visible user/assistant transcript: `workflows/current/CHAT_TRANSCRIPT.jsonl`
- Active payload only: `workflows/current/payload/`
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261015-005/0002-20261015T173100Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
