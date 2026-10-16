# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261016-004`
- **Status:** `active`
- **Title:** WF-06 · YT Agent Crew — complete multi-agent production structure
- **Next action:** Implement WF-06 as running agents (code) after user sign-off, OR begin S0 BRIEF on CLOSE CALL FILES #01 using RUNBOOK_S01E01.md. Two open blockers: YouTube Studio analytics access for A08 and the human publish gate.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
