# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261011-003`
- **Status:** `rendering`
- **Title:** TUMHARI RESERVED SEAT · Monarch Cinema Tabahi V2 · dual-style 3× enhancement
- **Next action:** Wait for WF-01 V2 mute master render process; verify exact 74.00 s output, then render WF-03 in two segments, mux exact voice-led mixes, run 40 delivery/delta gates on both, inspect failures, and only then package/synchronize.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
