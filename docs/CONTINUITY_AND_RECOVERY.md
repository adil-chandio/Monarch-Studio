# Continuity and recovery protocol

## Why work previously restarted or disappeared

Chat context, sandbox processes, local package state and background renders are different persistence layers. A response can stop while a process is alive; a refresh can restore an older textual summary; a fresh agent may see filenames without knowing the exact next command. Treating chat memory as the only state therefore causes restarts and stale-work substitution.

## Durable state hierarchy

1. `workflows/current/ACTIVE_TASK.json` — current task identity/status.
2. `workflows/current/JOURNAL.jsonl` — hash-chained events in exact order.
3. `workflows/current/RESUME.md` — exact next action and process ledger.
4. Latest immutable checkpoint under `operations/continuity/checkpoints/`.
5. Git commit and remote sync records.
6. Permanent accepted knowledge under the named `styles/` directory.

A compact chat summary is a convenience only; it cannot override this hierarchy.

## Agent ritual

At the beginning of every turn:

```bash
python3 tools/continuity.py resume
```

Then:

1. verify the journal hash chain;
2. inspect the current Git delta and running-process ledger;
3. execute the recorded exact next action;
4. never repeat an operation already recorded as successful;
5. checkpoint before and after long operations;
6. checkpoint before the response ends.

## Hourly operation

While an active task is running, start the watch process through Arena's background-process tool:

```bash
python3 tools/continuity.py watch --interval-seconds 3300 --commit --push
```

Record its process ID with `continuity.py process add`. The process creates a checkpoint at most every 55 minutes. Event-driven checkpoints are still mandatory because a crash can happen before the timer.

## Chat capture

From task initialization onward, visible user and assistant messages are stored verbatim in `CHAT_TRANSCRIPT.jsonl`, linked to the journal by SHA-256. Hidden system instructions, credentials, connector tokens and unavailable pre-initialization chat cannot be exported. Older compacted conversation cannot honestly be recreated word-for-word; existing workflow session logs remain its available evidence.

## Recovery after refresh

If the page or response stops:

1. do not start a new task;
2. run `continuity.py resume`;
3. if a process ID is recorded, query that process rather than restarting it;
4. inspect the latest checkpoint and Git status;
5. continue the exact next action;
6. append the recovered result and checkpoint.

If state and chat disagree, immutable files, measured outputs and the latest checkpoint win; record the discrepancy rather than hiding it.

## Service errors are not render errors (2026-10-14 clarification)

The user supplied a screenshot of Arena's **“The AI service encountered an
error”** banner. It proves the service/UI reported a failure, not the backend
cause. This repository cannot repair Arena's backend or guarantee an
uninterrupted turn. Do not attribute that banner to snapshot size, token limits,
missing Python packages or branch resets without corresponding evidence.

For local finite renders, finish the pipeline when feasible instead of ending
just after launch. Record the process ID, wait for its real result, inspect the
output, and present the requested artifact. Resumption must query that process
first and reuse only fingerprint-matching, completed frame/shot files.

In this revision a separate, verified local failure occurred: the last source
clip was too short. The decoder refused to freeze/duplicate frames. Its source
range was corrected, completed shots 0–8 were fully decoded and retained, and
only the remaining shots/export resumed. This is a local fix—not a claim that
the Arena service banner has been fixed.

Private media/model caches and deliverables must be excluded from the studio
manifest as well as Git. The manifest previously enumerated ignored `.cache`
content; regression tests now cover this privacy boundary.
