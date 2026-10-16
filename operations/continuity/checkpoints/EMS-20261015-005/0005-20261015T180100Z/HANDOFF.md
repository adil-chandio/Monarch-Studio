# Resume capsule — EMS-20261015-005

**Status:** `rendering`  
**Title:** WF-02 KAANTA v6 cinematic shot-design revision — scope confirmation  
**Style:** `monarch-zackd-3d`  
**Checkpoint sequence:** 5  
**Last checkpoint:** 2026-10-15T18:01:00Z

## Goal

Create a meaningful further cinematic/animation/editing/sound improvement rather than repeatedly stacking small effects. Confirm whether new shots and/or a new hook/script are allowed, preserve the no-clutter correction and previous deliveries, then produce the agreed new version.

## Acceptance criteria

- [ ] Confirm V6 redesign scope before another expensive full render; do not invent user approval
- [ ] Retain the earlier clean/premium constraint: no gratuitous HUD, panels, counters, beeps or transitions
- [ ] Preserve all previous source/master versions and medical safety meaning
- [ ] After scope selection, deliver actual rendered/verified video and editable source in the confirmed WF-02 workflow with appropriate music credit

## Exact next action

Monitor recorded v6 render without restarting. Build sound/mix matching new macro/cut perspective while preserving voice/script. Prepare new shot/focus/geometry/voice/media/provenance gates,docs and new WF-02 release folder. Only after completed master passes inspect/present/upload/hash-verify and promote.

## Running processes

- `kaanta-v6-macro-director-render-b2be94cf` — KAANTA v6 native1080p30 macro/hero-cell/depth-focus master — running

## Recovery command

```bash
python3 tools/continuity.py resume
```

## Durable evidence

- Active state: `workflows/current/ACTIVE_TASK.json`
- Hash-chained action journal: `workflows/current/JOURNAL.jsonl`
- Visible user/assistant transcript: `workflows/current/CHAT_TRANSCRIPT.jsonl`
- Active payload only: `workflows/current/payload/`
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261015-005/0005-20261015T180100Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
