#!/usr/bin/env python3
"""
Builds colab_gpu_bridge_v2.ipynb — ONE cell, one Run, then sleep.

What the single cell does
  0  GPU check + deps
  1  mount Drive, find the project folder
  2  write + start the control server (embedded, base64 -> no quoting bugs)
  3  open a public tunnel (cloudflared quick tunnel, localhost.run fallback)
  4  publish the endpoint: Drive CHAOS_GPU_ENDPOINT.json  +  ntfy.sh ping
  5  start the Drive command bridge (CMD -> work -> RESULT -> chaos_gpu_clips)
  6  supervise forever: restart server/tunnel, re-publish, heartbeat

Nothing to copy, nothing to paste. If the tunnel dies the Drive channel keeps working.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = (HERE / "agent_server.py").read_bytes()
BRIDGE = (HERE / "drive_bridge.py").read_bytes()
OUT = HERE / "colab_gpu_bridge_v3.ipynb"

TOPIC = "monarch-chaos-gpu-742683"
TOKEN_VALUE = "monarch-chaos-742683"

INTRO = f"""# 🎬 GPU BRIDGE v2 — ek Run, phir so jao

1. `Runtime` → **Change runtime type** → **T4 GPU** → Save
2. **▶ Run** (sirf ek cell)
3. Tab khula chhod dein. **Bas.**

URL aur commands dono khud pahunch jayenge — kuch copy-paste nahi:

| Channel | Kaam |
|---|---|
| **ntfy.sh** (`{TOPIC}`) | endpoint URL ping (agent khud padh leta hai) |
| **Drive `Chaos video 2/CHAOS_GPU_CMD.json`** | agent command likhta hai |
| **Drive `Chaos video 2/CHAOS_GPU_RESULT.json`** | result jahan likha jata hai |
| **Drive `Chaos video 2/CHAOS_GPU_HEARTBEAT.json`** | har 30 s: GPU, jobs, URL |
| **Drive `Chaos video 2/chaos_gpu_clips/`** | banayi hui files |

Tunnel mar jaye to bhi kaam chalta rahega — Drive channel alag hai.
"""

CELL = r'''
# ══════════════════════════════════════════════════════════════════════════
#  MONARCH · CHAOS — GPU BRIDGE v2      (ek Run, phir so jao)
# ══════════════════════════════════════════════════════════════════════════
import os, sys, json, time, base64, pathlib, subprocess, threading, secrets, re, shutil
from datetime import datetime

TOPIC = "__TOPIC__"
DRIVE_FOLDER_NAME = "Chaos video 2"
PORT = 8000
CONTENT = pathlib.Path(os.environ.get("CHAOS_CONTENT", "/content"))
try:
    CONTENT.mkdir(parents=True, exist_ok=True)
except PermissionError:                      # local test / limited sandbox
    CONTENT = pathlib.Path(os.environ.get("TMPDIR", "/tmp")) / "chaos_content"
    CONTENT.mkdir(parents=True, exist_ok=True)
WORK = CONTENT / "chaos_work"; WORK.mkdir(exist_ok=True)
TOKEN = "__TOKEN__"          # fixed on purpose: the agent already knows it
os.environ["CHAOS_TOKEN"] = TOKEN
os.environ["CHAOS_WORK"] = str(WORK)
os.environ["PORT"] = str(PORT)
os.environ["CHAOS_TAIL"] = "25"

def say(*a):
    print(datetime.now().strftime("%H:%M:%S"), *a, flush=True)

# ── 0 · GPU ──────────────────────────────────────────────────────────────
say("· GPU check")
try:
    smi = subprocess.run(["nvidia-smi","--query-gpu=name,memory.total","--format=csv,noheader"],
                         capture_output=True, text=True, timeout=30).stdout.strip()
except Exception:
    smi = ""
say("  nvidia-smi:", smi or "NOTHING")
try:
    import torch
    HAS_CUDA = torch.cuda.is_available()
    VRAM = round(torch.cuda.get_device_properties(0).total_memory/1024**3,1) if HAS_CUDA else 0.0
    say(f"  torch {torch.__version__} cuda={torch.version.cuda} available={HAS_CUDA} vram={VRAM}GB")
except Exception as e:
    HAS_CUDA, VRAM = False, 0.0
    say("  torch missing:", type(e).__name__, "(Colab par hota hai — yahan test me nahi)")
if not HAS_CUDA:
    say("  ⚠ GPU nahi mila — Runtime → Change runtime type → T4 GPU → phir Run")
    say("  (server phir bhi chalega: smoke/shell commands kaam karenge)")

# ── 1 · deps ─────────────────────────────────────────────────────────────
say("· deps")
for pkg in ("flask", "imageio-ffmpeg"):
    r = subprocess.run([sys.executable,"-m","pip","install","-q",pkg],
                       capture_output=True, text=True)
    if r.returncode != 0:                    # PEP-668 boxes
        subprocess.run([sys.executable,"-m","pip","install","-q",
                        "--break-system-packages",pkg], check=False,
                       capture_output=True)
say("  deps ready")

# ── 2 · Drive ────────────────────────────────────────────────────────────
say("· Drive")
drive_root = None
folder = None
try:
    from google.colab import drive as gdrive
    gdrive.mount("/content/drive", force_remount=False)
    drive_root = pathlib.Path("/content/drive/MyDrive")
    base_depth = len(str(drive_root).split(os.sep))
    for root, dirs, files in os.walk(drive_root):
        if pathlib.Path(root).name == DRIVE_FOLDER_NAME:
            folder = pathlib.Path(root); break
        if len(root.split(os.sep)) - base_depth > 3:
            dirs[:] = []
    folder = folder or drive_root
    (folder / "chaos_gpu_clips").mkdir(parents=True, exist_ok=True)
    say("  folder:", folder)
except Exception as e:
    say("  Drive mount FAILED:", type(e).__name__, e)
    folder = None

# ── 3 · server + bridge (embedded) ───────────────────────────────────────
say("· server source")
(CONTENT / "agent_server.py").write_bytes(base64.b64decode("__SERVER_B64__"))
(CONTENT / "drive_bridge.py").write_bytes(base64.b64decode("__BRIDGE_B64__"))
sys.path.insert(0, str(CONTENT))

import agent_server as SRV
SRV.TOKEN = TOKEN
SRV.WORK = WORK
SRV.OUT = WORK / "out"; SRV.OUT.mkdir(parents=True, exist_ok=True)
SRV.LOGS = WORK / "logs"; SRV.LOGS.mkdir(parents=True, exist_ok=True)

SRV_URL = {"url": None}
def run_server():
    while True:
        try:
            SRV.serve(port=PORT)
        except Exception as e:
            say("  server crashed:", type(e).__name__, e)
        time.sleep(3)

threading.Thread(target=run_server, daemon=True).start()
time.sleep(3)
say("  server thread up")

# ── 4 · tunnel ───────────────────────────────────────────────────────────
def start_cloudflared():
    exe = CONTENT / "cloudflared"
    if not exe.exists():
        url = ("https://github.com/cloudflare/cloudflared/releases/latest/download/"
               "cloudflared-linux-amd64")
        r = subprocess.run(["curl","-fsSL","-o",str(exe),url], capture_output=True, text=True)
        if r.returncode != 0:
            return None, "download: " + (r.stderr or "")[-160:]
        exe.chmod(0o755)
    log = CONTENT / "cf.log"
    log.write_text("")
    subprocess.Popen([str(exe),"tunnel","--url",f"http://127.0.0.1:{PORT}",
                      "--no-autoupdate","--logfile",str(log)],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(75):
        time.sleep(1)
        txt = log.read_text(errors="ignore") if log.exists() else ""
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", txt)
        if m:
            return m.group(0), None
    return None, "timeout"

def start_lhr():
    p = subprocess.Popen(["ssh","-o","StrictHostKeyChecking=no","-o","ServerAliveInterval=30",
                          "-R",f"80:127.0.0.1:{PORT}","nokey@localhost.run"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for _ in range(60):
        line = p.stdout.readline()
        if not line:
            time.sleep(1); continue
        m = re.search(r"https://[a-z0-9-]+\.lhr\.life", line)
        if m:
            return m.group(0), None
    return None, "no url"

def open_tunnel():
    say("· tunnel")
    u, e1 = start_cloudflared()
    if not u:
        say("  cloudflared:", e1)
        u, e2 = start_lhr()
        if not u:
            say("  localhost.run:", e2)
    if u:
        say("  URL:", u)
    else:
        say("  ⚠ koi tunnel nahi — Drive channel phir bhi chalega")
    SRV_URL["url"] = u
    return u

# ── 5 · publish (ntfy + Drive) ───────────────────────────────────────────
def publish(url):
    if url:
        try:
            import urllib.request
            urllib.request.urlopen(urllib.request.Request(
                f"https://ntfy.sh/{TOPIC}", data=url.encode()), timeout=25)
            say("  ntfy ping ok")
        except Exception as e:
            say("  ntfy ping failed:", type(e).__name__)
    payload = {"url": url, "token": TOKEN, "port": PORT, "vram_gb": VRAM,
               "created": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
               "ntfy": f"https://ntfy.sh/{TOPIC}/json?poll=1",
               "how": "GET <url>/status?token=<token>  |  or write CHAOS_GPU_CMD.json"}
    targets = []
    if folder:
        targets.append(folder)
    targets.append(pathlib.Path("/content/drive/MyDrive"))
    targets.append(CONTENT)
    for t in targets:
        try:
            t.mkdir(parents=True, exist_ok=True)
            (t / "CHAOS_GPU_ENDPOINT.json").write_text(json.dumps(payload, indent=1))
            say("  endpoint written:", t)
        except Exception as e:
            say("  endpoint write skipped:", t, type(e).__name__)

url = open_tunnel()
publish(url)

# ── 6 · Drive command bridge ─────────────────────────────────────────────
import drive_bridge as DB
if folder:
    bridge = DB.Bridge(folder, TOKEN, url_getter=lambda: SRV_URL["url"], port=PORT)
    threading.Thread(target=bridge.loop, kwargs={"interval": 5.0}, daemon=True).start()
    say("  bridge running (poll 5 s) — commands: CHAOS_GPU_CMD.json")
else:
    bridge = None
    say("  ⚠ bridge OFF (no Drive) — sirf tunnel se control hoga")

say("")
say("═" * 66)
say(" READY — kuch copy karne ki zaroorat nahi. Tab khula chhod dein.")
say(" endpoint:", url or "none")
say(" token:", TOKEN)
if not HAS_CUDA:
    say(" ⚠⚠ GPU OFF: Runtime → Change runtime type → T4 GPU → phir yeh cell dobara Run")
say("═" * 66)

# ── 7 · supervisor (yahi cell chalta rehta hai) ──────────────────────────
tick = 0
while True:
    time.sleep(60)
    tick += 1
    try:
        import urllib.request
        alive = False
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=8) as r:
                alive = b"ok" in r.read()
        except Exception:
            alive = False
        if not alive:
            say("supervisor: server dead → restart")
            threading.Thread(target=run_server, daemon=True).start()
            time.sleep(4)
        if tick % 10 == 0:                    # every 10 min: refresh the tunnel URL
            new = open_tunnel()
            if new:
                publish(new)
        if tick % 5 == 0:
            say("alive | url:", (SRV_URL["url"] or "none")[-32:],
                "| processed:", getattr(bridge, "processed", 0))
    except Exception as e:
        say("supervisor error:", type(e).__name__, e)
'''


def main() -> int:
    cell = (CELL.replace("__TOPIC__", TOPIC)
                .replace("__TOKEN__", TOKEN_VALUE)
                .replace("__SERVER_B64__", base64.b64encode(SERVER).decode())
                .replace("__BRIDGE_B64__", base64.b64encode(BRIDGE).decode()))
    nb = {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {"colab": {"provenance": [], "gpuType": "T4"},
                    "kernelspec": {"display_name": "Python 3", "name": "python3"},
                    "language_info": {"name": "python"}},
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": INTRO.splitlines(keepends=True)},
            {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
             "source": cell.splitlines(keepends=True)},
        ],
    }
    OUT.write_text(json.dumps(nb, indent=1))
    # validate: the single cell must parse, and both payloads must decode
    compile(cell, "<cell>", "exec")
    assert base64.b64decode(base64.b64encode(SERVER)) == SERVER
    assert base64.b64decode(base64.b64encode(BRIDGE)) == BRIDGE
    print(f"wrote {OUT} ({OUT.stat().st_size} B)  cells=2  server={len(SERVER)}B bridge={len(BRIDGE)}B")
    print(f"ntfy topic: {TOPIC}")
    print(f"token: {TOKEN_VALUE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
