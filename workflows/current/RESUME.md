# Resume capsule — EMS-20261016-004

**Status:** `active`  
**Title:** WF-06 · YT Agent Crew — complete multi-agent production structure  
**Style:** `agent-workflow`  
**Checkpoint sequence:** 2  
**Last checkpoint:** 2026-10-16T15:06:08Z

## Goal

Build the complete no-code structure for the Monarch YouTube agent crew: manager-led chain of command, live reporting bus, per-agent specs, measurable stage gates, compliance veto, and a learning loop that returns analytics into research. Fill the gaps that would stop the crew reaching tabahi level.

## Acceptance criteria

- [ ] Permanent structure docs under workflows/wf06_yt_agent_crew/, registered as WF-06, every agent has inputs/outputs/gates/escalation, no code written, validation passes.

## Exact next action

HUMAN publishes MONARCH_FILES_01_master.mp4 (Tuesday 14:00 UTC) using POST_NOW.md, answering 'Altered or synthetic content' = YES. Then A08 records the 48h snapshot: CTR, AVD, retention at 0:20 and at shot 16 (polar bear, flagged), traffic sources. Then render the 3 fan-out Shorts specced in PACKAGE.md section 7. Then open MF-02 S0 BRIEF 'The Bear That Walked Into Town'.

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
- Latest checkpoint package: `operations/continuity/checkpoints/EMS-20261016-004/0002-20261016T150608Z`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
