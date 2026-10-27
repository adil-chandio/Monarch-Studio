# MOBILEOPS · job files (phone-only studio state)

Har mobile project ka **ek** job file: `<job_id>.json`. Yehi batata hai **kaun kya karega** — chat refresh
hone par bhi kaam dohraya nahi jata. Tool: [`tools/mobile_ops.py`](../../tools/mobile_ops.py) ·
SOP: [`docs/MOBILE_WORKFLOW.md`](../../docs/MOBILE_WORKFLOW.md).

```bash
python3 tools/mobile_ops.py doctor
python3 tools/mobile_ops.py start --project monarch-reel-01
python3 tools/mobile_ops.py plan  mob-20261027-monarch-reel-01
python3 tools/mobile_ops.py handoff mob-20261027-monarch-reel-01 --colab https://colab.research.google.com/drive/<id>
python3 tools/mobile_ops.py check  mob-20261027-monarch-reel-01      # owner ke "DONE" ke baad
python3 tools/mobile_ops.py finish mob-20261027-monarch-reel-01      # mix -> verify -> assemble
python3 tools/mobile_ops.py deliver mob-20261027-monarch-reel-01 --master-id <drive id> --url <link>
python3 tools/mobile_ops.py status
```

## States

`intake → planned → handed_off → partial | clip_ready → mixed → verified → assembled → delivered`
(plus `blocked`, jahan se wapas kaam me aana allowed hai).

## Ek job file kaisa dikhta hai

```json
{
  "schema_version": 1,
  "tool": "mobileops-1.0",
  "job_id": "mob-20261027-monarch-reel-01",
  "title": "Monarch reel 01",
  "project": "studio/videogen/examples/monarch-reel-01.project.json",
  "notebook": "studio/videogen/examples/mobile/MOBILE_monarch-reel-01.ipynb",
  "colab_url": "https://colab.research.google.com/drive/<id>",
  "state": "delivered",
  "gates": {
    "plan_estimate": {"ok": true, "detail": "FREE-ONLY ($0.00)"},
    "notebook": {"ok": true, "detail": "mobile/MOBILE_monarch-reel-01.ipynb"},
    "clips": {"ok": true, "detail": "3/3"},
    "mix": {"ok": true, "detail": "exit 0"},
    "verify": {"ok": true, "detail": "exit 0"},
    "assemble": {"ok": true, "detail": "exit 0"},
    "delivery": {"ok": true, "detail": "<drive id>"}
  },
  "master": {"path": "delivery/monarch-reel-01_MASTER.mp4", "md5": "…", "bytes": 3355443,
             "probe": {"width": 960, "height": 1664, "fps": 30.0, "duration": 15.0, "audio_codec": "aac"},
             "drive_id": "<drive id>", "url": "https://drive.google.com/file/d/<id>/view"}
}
```

Gates ke bina koi state nahi milti: clips ke bina `finish` refuse karta hai, md5 ke bina `deliver` refuse
karta hai. Isi liye "ban gaya" sirf tab likha jata hai jab file, md5 aur probe sab maujood hon.
