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
