#!/usr/bin/env python3
"""
Builds CHAOS_GPU_AGENT.ipynb — a self-contained Colab notebook that turns the
free GPU into a machine the agent can drive from chat.

The notebook embeds agent_server.py verbatim, so the user only has to open it,
pick a GPU runtime and press Run all. It then
  1. reports the GPU,
  2. installs deps,
  3. mounts Drive,
  4. starts the control server + a public tunnel,
  5. writes CHAOS_GPU_ENDPOINT.json to Drive (the agent reads it from there),
  6. keeps syncing produced clips to Drive every 30 s.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = (HERE / "agent_server.py").read_text()
OUT = HERE / "CHAOS_GPU_AGENT.ipynb"


def md(src: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)}


def code(src: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": src.splitlines(keepends=True)}


INTRO = """# MONARCH · CHAOS — GPU agent bridge

**Aap ka kaam: 3 click. Phir cell chalta rehne dein aur tab band na karein.**

1. `Runtime` → **Change runtime type** → Accelerator = **GPU** → Save
2. `Runtime` → **Run all**
3. Cell 4 khatam hone par ek **ENDPOINT URL** print hoga — aur wohi URL
   automatically aap ke Drive mein `CHAOS_GPU_ENDPOINT.json` par likh diya jayega
   (folder `Chaos video 2`). Mujhe kuch paste karne ki zaroorat nahi — main wahan se
   khud utha lunga.

### Yeh kya karta hai
Colab machine par ek chhota HTTP control server chalta hai (token-protected) aur us ke
saamne ek public tunnel. Main (agent) us URL se yeh kar sakta hoon:

| Endpoint | Kaam |
|---|---|
| `/status` | GPU, VRAM, disk, jobs |
| `/recipes` | is machine par kya chal sakta hai |
| `/run?recipe=smoke` | pipeline test (model ke bagair, 20 s) |
| `/run?recipe=ltx&prompt=...` | LTX-Video text-to-video |
| `/run?recipe=wan&prompt=...` | Wan2.2-TI2V-5B (24 GB+) |
| `/jobs` `/job` `/log` | progress dekhna |
| `/files` | outputs + sha256 |

### Zaroori
- Cell 5 **chalta rehna chahiye** (tab khula rakhein). Colab idle hone par disconnect karta hai.
- Clips khud Drive folder `chaos_gpu_clips` mein sync hote rehte hain.
- Free T4 par sirf **LTX-2B / smoke** chalega. 24 GB+ par Wan2.2. Yeh VRAM ka sach hai.
"""

CHECK = '''import os, sys, subprocess, json, platform, shutil
def sh(cmd):
    try:
        return subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True,
                              text=True).stdout.strip()
    except FileNotFoundError:
        return ""
print(sh("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader") or "NO GPU")
import torch
print("torch", torch.__version__, "| cuda", torch.version.cuda, "| available", torch.cuda.is_available())
VRAM = round(torch.cuda.get_device_properties(0).total_memory/1024**3, 1) if torch.cuda.is_available() else 0
print("VRAM GB:", VRAM)
print("bf16 supported:", torch.cuda.is_bf16_supported() if torch.cuda.is_available() else False)
print("disk:", sh("df -h /content | tail -1") or sh("df -h / | tail -1"))
if VRAM == 0:
    raise SystemExit("GPU nahi mila -> Runtime -> Change runtime type -> GPU, phir Run all.")
'''

INSTALL = '''%%capture
import subprocess, sys
# Colab ka torch chhedte nahi — sirf yeh 3 cheezein
subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                "flask", "imageio-ffmpeg"], check=False)
print("deps ok")
'''

DRIVE = '''import os, json, pathlib, time
IN_COLAB = "google.colab" in sys.modules
DRIVE_FOLDER_NAME = "Chaos video 2"
DRIVE_SUB = "chaos_gpu_clips"
drive_root = None
if IN_COLAB:
    from google.colab import drive
    try:
        drive.mount("/content/drive", force_remount=False)
        drive_root = pathlib.Path("/content/drive/MyDrive")
        print("drive:", drive_root)
    except Exception as e:
        print("drive mount failed:", type(e).__name__, e)
endpoint_dir = None
if drive_root:
    # find the project folder anywhere in My Drive (depth-limited walk)
    target = None
    for root, dirs, files in os.walk(drive_root):
        if pathlib.Path(root).name == DRIVE_FOLDER_NAME:
            target = pathlib.Path(root); break
        if root.count(os.sep) - str(drive_root).count(os.sep) > 3:
            dirs[:] = []
    endpoint_dir = target or drive_root
    files_dir = endpoint_dir / DRIVE_SUB
    files_dir.mkdir(parents=True, exist_ok=True)
    print("endpoint will be written to:", endpoint_dir)
    print("clips will sync to:", files_dir)
else:
    files_dir = pathlib.Path("/content/chaos_work/out")
'''

SERVER_CELL = '''# control server likh do (self-contained: koi download nahi)
import pathlib
SRC = pathlib.Path("/content/agent_server.py")
SRC.write_text(SERVER_SOURCE)
print("server written:", SRC, len(SERVER_SOURCE), "chars")
'''

BOOT = '''import os, json, secrets, subprocess, sys, threading, time, pathlib, re

TOKEN = secrets.token_urlsafe(16)
PORT = 8000
WORK = pathlib.Path("/content/chaos_work"); WORK.mkdir(exist_ok=True)
os.environ["CHAOS_TOKEN"] = TOKEN
os.environ["CHAOS_WORK"] = str(WORK)
os.environ["PORT"] = str(PORT)

# ---- 1. tunnel: cloudflared quick tunnel, then localhost.run as fallback
def start_cloudflared():
    exe = pathlib.Path("/content/cloudflared")
    if not exe.exists():
        url = ("https://github.com/cloudflare/cloudflared/releases/latest/download/"
               "cloudflared-linux-amd64")
        r = subprocess.run(["curl", "-fsSL", "-o", str(exe), url], capture_output=True, text=True)
        if r.returncode != 0:
            return None, "download failed: " + r.stderr[-200:]
        exe.chmod(0o755)
    p = subprocess.Popen([str(exe), "tunnel", "--url", f"http://127.0.0.1:{PORT}",
                          "--no-autoupdate", "--logfile", "/content/cf.log"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for _ in range(60):
        time.sleep(1)
        try:
            log = pathlib.Path("/content/cf.log").read_text()
        except FileNotFoundError:
            log = ""
        m = re.search(r"https://[a-z0-9-]+\\.trycloudflare\\.com", log)
        if m:
            return m.group(0), None
        if p.poll() is not None:
            return None, "cloudflared exited"
    return None, "timeout waiting for trycloudflare url"

def start_localhostrun():
    p = subprocess.Popen(["ssh", "-o", "StrictHostKeyChecking=no",
                          "-o", "ServerAliveInterval=30",
                          "-R", f"80:127.0.0.1:{PORT}", "nokey@localhost.run"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for _ in range(45):
        line = p.stdout.readline()
        if not line:
            time.sleep(1); continue
        m = re.search(r"https://[a-z0-9-]+\\.lhr\\.life", line)
        if m:
            return m.group(0), None
    return None, "localhost.run gave no url"

# ---- 2. server thread
def serve():
    sys.path.insert(0, "/content")
    import agent_server
    agent_server.TOKEN = TOKEN
    agent_server.serve(port=PORT)

threading.Thread(target=serve, daemon=True).start()
time.sleep(3)
import urllib.request
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=10) as r:
        print("local health:", r.read().decode()[:120])
except Exception as e:
    print("local health FAILED:", type(e).__name__, e)

PUBLIC, err1 = start_cloudflared()
if not PUBLIC:
    print("cloudflared nahi chala:", err1)
    PUBLIC, err2 = start_localhostrun()
    if not PUBLIC:
        print("localhost.run bhi nahi chala:", err2)

print("\\n" + "="*70)
print("ENDPOINT:", PUBLIC or "NO TUNNEL — neeche ka error bhejein")
print("="*70)

# ---- 3. Drive par endpoint likh do (agent wahan se khud uthata hai)
if PUBLIC and endpoint_dir:
    payload = dict(url=PUBLIC, token=TOKEN, port=PORT, work=str(WORK),
                   created=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   note="agent: GET <url>/status?token=<token>")
    (endpoint_dir / "CHAOS_GPU_ENDPOINT.json").write_text(json.dumps(payload, indent=1))
    print("written to Drive:", endpoint_dir / "CHAOS_GPU_ENDPOINT.json")

# ---- 4. clips ko Drive par sync karte raho
def sync_loop():
    out = WORK / "out"
    while True:
        time.sleep(30)
        if not (PUBLIC and drive_root and files_dir.exists()):
            continue
        for f in out.glob("*"):
            dst = files_dir / f.name
            try:
                if f.is_file() and (not dst.exists() or dst.stat().st_size != f.stat().st_size):
                    import shutil as _sh
                    _sh.copy2(f, dst)
                    print("synced ->", dst.name, f.stat().st_size, "B", flush=True)
            except Exception as e:
                print("sync error", f.name, type(e).__name__, e)

threading.Thread(target=sync_loop, daemon=True).start()
'''

KEEPALIVE = '''# Yeh cell chalta rehna chahiye — tab khula rakhein. Har 60 s ek heartbeat.
import time, json, urllib.request
from datetime import datetime
print("Ctrl+C ya tab band = tunnel band. Chalta rahe to agent kaam kar sakta hai.\\n")
while True:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/status?token={TOKEN}",
                                    timeout=15) as r:
            s = json.loads(r.read().decode())
        js = s.get("job_states", {})
        print(datetime.now().strftime("%H:%M:%S"), "| jobs:", js or "none",
              "| queue:", s.get("queue"), "| vram:", s["gpu"].get("vram_gb"), "GB", flush=True)
    except Exception as e:
        print(datetime.now().strftime("%H:%M:%S"), "heartbeat error:", type(e).__name__, e, flush=True)
    time.sleep(60)
'''


def main() -> int:
    cells = [
        md(INTRO),
        md("## 1 · Machine check"),
        code(CHECK),
        md("## 2 · Dependencies"),
        code(INSTALL),
        md("## 3 · Drive (endpoint + clips ke liye)"),
        code(DRIVE),
        md("## 4 · Control server (self-contained)"),
        code("SERVER_SOURCE = r'''" + SERVER.replace("'''", "\\'\\'\\'") + "'''"),
        code(SERVER_CELL),
        md("## 5 · Boot: tunnel + server + Drive handoff"),
        code(BOOT),
        md("## 6 · Heartbeat — yeh chalta rahe"),
        code(KEEPALIVE),
    ]
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"colab": {"provenance": [], "gpuType": "T4"},
                       "kernelspec": {"display_name": "Python 3", "name": "python3"},
                       "language_info": {"name": "python"}},
          "cells": cells}
    OUT.write_text(json.dumps(nb, indent=1))
    print(f"wrote {OUT} ({OUT.stat().st_size} B, {len(cells)} cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
