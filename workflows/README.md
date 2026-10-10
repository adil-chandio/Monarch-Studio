# Single active workflow slot

This directory is deliberately **not** a permanent archive. It contains only the work currently running in Arena Agent Mode.

```text
current/
  ACTIVE_TASK.json       machine state and exact next action
  RESUME.md              human recovery capsule
  JOURNAL.jsonl          append-only hash-chained actions/results/errors
  CHAT_TRANSCRIPT.jsonl  visible user/assistant messages from task start
  payload/               only files actively being changed or produced
```

Completed work is promoted into its named permanent style under `styles/`; task state/transcript is moved to `operations/history/`; then the active slot returns to `idle`.

Every agent must begin with:

```bash
python3 tools/continuity.py resume
```

It must checkpoint before/after a long-running operation, after every material result, before ending a turn, and at least once per hour while status is active. A refresh or new agent must never restart from the beginning when the resume capsule and valid journal exist.