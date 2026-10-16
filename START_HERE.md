# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `EMS-20261016-003`
- **Status:** `active`
- **Title:** Monarch Cam — channel forensic audit + forward content plan
- **Next action:** Fetch YouTube Studio analytics (CTR, AVD, traffic sources, subscriber attribution, RPM) to close the eight open data gaps, then start Phase 0 Repair: About rewrite, playlists, trailer, typo/AI-video cleanup, clip source register.
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
