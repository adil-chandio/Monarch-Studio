# GPU jobs — how the agent drives the Colab box

The box pulls these files straight from GitHub, so a `git push` *is* the deploy:

```bash
RAW=https://raw.githubusercontent.com/adil-chandio/Monarch-Studio/refs/heads/arena/faa9119c-monarch-studio/workflows/current/payload/WF04-CHAOS04/gpu/jobs
curl -fsSL "$RAW/<script>.py" -o /content/chaos_work/<script>.py
cd /content/chaos_work && python3 -u <script>.py <args>
```

Why not base64 through the chat: long base64 payloads get mutated in transport
(seen twice: an injected space, and `V` -> `R`), which silently breaks scripts.

## Ledger

| script | what it does | writes |
|---|---|---|
| `probe_ltx.py` | LTX-Video smoke probe on the T4: load, 97 frames @512x896, measure s/frame | `probe/probe_report.json`, `probe_t4.mp4` |
| `analyze_ref.py` | reference forensic: container, cuts, per-shot lum/contrast/sat/motion/palette, loudness | `REF_FORENSIC.json`, `ref_frames/*.jpg` |

Outputs are written to the Drive folder given by `CHAOS_BRIDGE` so the agent can
read them without a tunnel.

## Two traps, measured the hard way (27 Oct)

1. **Never launch a background job from a `sync` shell.** The Flask worker keeps
   reading the subprocess pipe, so the job never reports `done`, and because jobs
   run one at a time the whole bridge deadlocks behind it. Background work must go
   through `mode: "bg"` (which starts a new session and redirects to a log file).
2. **`pkill -f probe_ltx.py` kills its own wrapper.** The pattern matches the
   wrapper's own `bash -lc "... probe_ltx.py ..."` command line, so the shell dies
   before `python3` is reached and the log freezes. Kill by PID, or pattern-match
   something the wrapper does not contain.

Also: hand-editing base64 is not safe — one edited character silently corrupts the
JSON (`V` became `R` in testing). Regenerate the payload, never patch it.
