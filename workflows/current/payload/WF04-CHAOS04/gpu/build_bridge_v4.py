#!/usr/bin/env python3
"""
Builds MONARCH_GPU_BRIDGE_v4.ipynb — ONE cell, one Run, then leave the tab open.

Why v4 (what broke in v2/v3, measured)
  v2  random token printed as 4 chars  → agent locked out
  v2  Drive mount failed               → endpoint file never written
  v3  tunnel died after ~8 min         → agent lost the box twice
  v3  bridge ran in a thread           → died when the Flask thread restarted

v4 fixes each one
  1  FIXED token, printed in full, also stored in the endpoint file
  2  endpoint written to 3 places, re-written every 60 s (staleness is visible)
  3  tunnel watchdog: health-checks the public URL and rotates
     cloudflared -> pinggy -> localhost.run, re-publishing each new URL
  4  drive_bridge runs as its OWN PROCESS (survives server crashes, auto-restart)
  5  torchao pinned upgrade at boot — diffusers 0.41 cannot import LTXPipeline on
     the stock Colab torchao (FqnToConfig ImportError), proven on this box
  6  GPU check shouts loudly instead of silently running on CPU
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = (HERE / "agent_server.py").read_bytes()
BRIDGE = (HERE / "drive_bridge.py").read_bytes()
OUT = HERE / "MONARCH_GPU_BRIDGE_v4.ipynb"

TOPIC = "monarch-chaos-gpu-742683"
TOKEN_VALUE = "monarch-chaos-742683"

INTRO = f"""# 🎬 GPU BRIDGE v4 — ek Run, phir tab khula chhod dein

1. `Runtime` → **Change runtime type** → **T4 GPU** → Save
2. **▶ Run** (sirf ek cell)
3. Tab khula chhod dein. **Bas.**

| Channel | Kaam |
|---|---|
| **Drive `Chaos video 2/CHAOS_GPU_CMD.json`** | main command likhta hoon |
| **Drive `Chaos video 2/CHAOS_GPU_RESULT.json`** | jawab yahan aata hai |
| **Drive `Chaos video 2/CHAOS_GPU_HEARTBEAT.json`** | har 30 s: GPU, jobs, URL |
| **Drive `Chaos video 2/chaos_gpu_clips/`** | banayi hui files |
| **ntfy.sh** (`{TOPIC}`) | tunnel URL (optional channel) |

Tunnel mar jaye to kaam rukta nahi — Drive channel alag chalta hai, aur watchdog
naya tunnel bana kar URL dobara publish kar deta hai.
"""

CELL = r'''
# ══════════════════════════════════════════════════════════════════════════
#  MONARCH · CHAOS — GPU BRIDGE v4        (ek Run, phir tab khula chhod dein)
# ══════════════════════════════════════════════════════════════════════════
import os, sys, json, time, base64, pathlib, subprocess, threading, re, shutil
from datetime import datetime, timezone

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
os.environ["HF_HOME"] = str(CONTENT / "hf")

def say(*a):
    print(datetime.now().strftime("%H:%M:%S"), *a, flush=True)

def nowz():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

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
    say("  torch %s cuda=%s available=%s vram=%sGB" % (torch.__version__, torch.version.cuda, HAS_CUDA, VRAM))
except Exception as e:
    HAS_CUDA, VRAM = False, 0.0
    say("  torch missing:", type(e).__name__, "(Colab par hota hai — yahan test me nahi)")
if not HAS_CUDA:
    say("  ⚠ GPU nahi mila — Runtime → Change runtime type → T4 GPU → phir Run")
    say("  (server phir bhi chalega: smoke/shell commands kaam karenge)")

# ── 1 · deps ─────────────────────────────────────────────────────────────
say("· deps")
def pip(*args):
    r = subprocess.run([sys.executable,"-m","pip","install","-q",*args],
                       capture_output=True, text=True)
    if r.returncode != 0:                    # PEP-668 boxes
        subprocess.run([sys.executable,"-m","pip","install","-q",
                        "--break-system-packages",*args], capture_output=True)
    return r.returncode
for pkg in ("flask", "imageio-ffmpeg"):
    pip(pkg)
# diffusers 0.41 + stock Colab torchao => "cannot import name 'FqnToConfig'"
# which silently kills every LTX pipeline import. 0.18 fixes it (measured here).
pip("-U", "torchao")
try:
    import torchao
    say("  torchao", getattr(torchao, "__version__", "?"))
except Exception as e:
    say("  torchao import warn:", type(e).__name__)
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

# ── 3 · server (this process) ────────────────────────────────────────────
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

def local_ok():
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/health" % PORT, timeout=8) as r:
            return b"ok" in r.read()
    except Exception:
        return False

# ── 4 · tunnels (rotating) ───────────────────────────────────────────────
TUN = {"proc": None, "kind": None, "url": None}

def kill_tun():
    p = TUN.get("proc")
    if p is not None:
        try:
            p.kill()
        except Exception:
            pass
    TUN["proc"] = None

def t_cloudflared():
    exe = CONTENT / "cloudflared"
    if not exe.exists():
        url = ("https://github.com/cloudflare/cloudflared/releases/latest/download/"
               "cloudflared-linux-amd64")
        r = subprocess.run(["curl","-fsSL","-o",str(exe),url], capture_output=True, text=True)
        if r.returncode != 0:
            return None, "download: " + (r.stderr or "")[-120:]
        exe.chmod(0o755)
    log = CONTENT / "cf.log"
    log.write_text("")
    p = subprocess.Popen([str(exe),"tunnel","--url","http://127.0.0.1:%d" % PORT,
                          "--no-autoupdate","--logfile",str(log)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(75):
        time.sleep(1)
        txt = log.read_text(errors="ignore") if log.exists() else ""
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", txt)
        if m:
            TUN["proc"] = p
            return m.group(0), None
    p.kill()
    return None, "timeout"

def _ssh_tunnel(cmd, pattern, label):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    for _ in range(90):
        line = p.stdout.readline()
        if not line:
            if p.poll() is not None:
                return None, label + " exited"
            time.sleep(1); continue
        m = re.search(pattern, line)
        if m:
            TUN["proc"] = p
            return m.group(0), None
    p.kill()
    return None, label + " no url"

def t_pinggy():
    return _ssh_tunnel(["ssh","-p","443","-o","StrictHostKeyChecking=no",
                        "-o","ServerAliveInterval=20","-o","ServerAliveCountMax=3",
                        "-R0:127.0.0.1:%d" % PORT,"a.pinggy.io"],
                       r"https://[a-z0-9-]+\.(?:free\.pinggy\.link|pinggy\.link|a\.pinggy\.io)",
                       "pinggy")

def t_lhr():
    return _ssh_tunnel(["ssh","-o","StrictHostKeyChecking=no","-o","ServerAliveInterval=20",
                        "-R","80:127.0.0.1:%d" % PORT,"nokey@localhost.run"],
                       r"https://[a-z0-9-]+\.lhr\.life","localhost.run")

def public_ok(url):
    import urllib.request
    if not url:
        return False
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/health", timeout=12) as r:
            return b"ok" in r.read()
    except Exception:
        return False

def open_tunnel():
    say("· tunnel")
    kill_tun()
    for kind, fn in (("cloudflared", t_cloudflared), ("pinggy", t_pinggy), ("lhr", t_lhr)):
        u, err = fn()
        if u:
            TUN.update(kind=kind, url=u)
            say("  %s URL: %s" % (kind, u))
            SRV_URL["url"] = u
            return u
        say("  %s:" % kind, err)
    say("  ⚠ koi tunnel nahi — Drive channel phir bhi chalega")
    TUN.update(kind=None, url=None)
    SRV_URL["url"] = None
    return None

# ── 5 · publish (ntfy + Drive) ───────────────────────────────────────────
PUB = {"last": None}
def publish(url, force=False):
    if url and (force or url != PUB["last"]):
        try:
            import urllib.request
            urllib.request.urlopen(urllib.request.Request(
                "https://ntfy.sh/%s" % TOPIC, data=url.encode()), timeout=25)
            say("  ntfy ping ok")
        except Exception as e:
            say("  ntfy ping failed:", type(e).__name__)
        PUB["last"] = url
    payload = {"url": url, "token": TOKEN, "port": PORT, "vram_gb": VRAM,
               "cuda": bool(HAS_CUDA), "tunnel": TUN.get("kind"), "hostname": os.uname().nodename,
               "updated": nowz(), "started": STARTED,
               "ntfy": "https://ntfy.sh/%s/json?poll=1" % TOPIC,
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
        except Exception:
            pass

STARTED = nowz()
url = open_tunnel()
publish(url, force=True)

# ── 6 · Drive command bridge — SEPARATE PROCESS (survives crashes) ───────
BR = {"proc": None}
def start_bridge():
    if not folder:
        return
    env = dict(os.environ, CHAOS_DRIVE_DIR=str(folder), CHAOS_TOKEN=TOKEN,
               CHAOS_WORK=str(WORK), PORT=str(PORT))
    log = open(str(CONTENT / "bridge.log"), "ab")
    BR["proc"] = subprocess.Popen([sys.executable,"-u",str(CONTENT / "drive_bridge.py")],
                                  cwd=str(CONTENT), env=env,
                                  stdout=log, stderr=subprocess.STDOUT)
    say("  bridge process pid=%d" % BR["proc"].pid)

if folder:
    start_bridge()
else:
    say("  ⚠ bridge OFF (no Drive) — sirf tunnel se control hoga")

say("")
say("═" * 66)
say(" READY — kuch copy karne ki zaroorat nahi. Tab khula chhod dein.")
say(" tunnel:", TUN.get("kind") or "none", "|", url or "none")
say(" token:", TOKEN)
if not HAS_CUDA:
    say(" ⚠⚠ GPU OFF: Runtime → Change runtime type → T4 GPU → phir yeh cell dobara Run")
say("═" * 66)

# ── 7 · supervisor ───────────────────────────────────────────────────────
tick = 0
bad = 0
while True:
    time.sleep(60)
    tick += 1
    try:
        if not local_ok():
            say("supervisor: server dead → restart")
            threading.Thread(target=run_server, daemon=True).start()
            time.sleep(4)
        # bridge process health
        if folder and (BR["proc"] is None or BR["proc"].poll() is not None):
            say("supervisor: bridge process dead → restart")
            start_bridge()
        # tunnel health: 2 consecutive failures => rotate
        if TUN.get("url") and public_ok(TUN["url"]):
            bad = 0
        else:
            bad += 1
        if bad >= 2:
            say("supervisor: tunnel down (%d) → rotate" % bad)
            bad = 0
            publish(open_tunnel(), force=True)
        publish(TUN.get("url"))          # refresh endpoint timestamp every 60 s
        if tick % 5 == 0:
            say("alive %s | gpu %s | tunnel %s | url %s"
                % (nowz(), "on" if HAS_CUDA else "OFF", TUN.get("kind"),
                   (TUN.get("url") or "none")[-34:]))
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
    compile(cell, "<cell>", "exec")
    assert base64.b64decode(base64.b64encode(SERVER)) == SERVER
    assert base64.b64decode(base64.b64encode(BRIDGE)) == BRIDGE
    print("wrote %s (%d B)  cells=2  cell=%d chars  server=%dB bridge=%dB"
          % (OUT, OUT.stat().st_size, len(cell), len(SERVER), len(BRIDGE)))
    print("ntfy topic:", TOPIC)
    print("token:", TOKEN_VALUE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
