# Resume capsule — EMS-20261016-004

**Status:** `active`  
**Title:** WF-06 · YT Agent Crew — complete multi-agent production structure  
**Style:** `agent-workflow`  
**Checkpoint sequence:** 0  
**Last checkpoint:** none

## Goal

Build the complete no-code structure for the Monarch YouTube agent crew: manager-led chain of command, live reporting bus, per-agent specs, measurable stage gates, compliance veto, and a learning loop that returns analytics into research. Fill the gaps that would stop the crew reaching tabahi level.

## Acceptance criteria

- [ ] Permanent structure docs under workflows/wf06_yt_agent_crew/, registered as WF-06, every agent has inputs/outputs/gates/escalation, no code written, validation passes.

## Exact next action

Write WF-06 structure documents and register the workflow.

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
- Latest checkpoint package: `none`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
