#!/usr/bin/env python3
"""
MONARCH · CHAOS — Drive command bridge (runs inside Colab, next to agent_server).

Why this exists
---------------
Tunnels die, URLs expire, and the agent's shell cannot reach the open internet.
Drive does not have either problem: the agent can already write a file into the
project's Drive folder and read one back. So Drive is the control channel:

    Drive: CHAOS_GPU_CMD.json      <- the agent writes a command here
    Drive: CHAOS_GPU_RESULT.json   <- we write the answer here
    Drive: CHAOS_GPU_HEARTBEAT.json<- every 30 s: alive, GPU, jobs, tunnel URL
    Drive: chaos_gpu_clips/        <- produced files get copied here

A tunnel is still started (so the agent can also drive the HTTP API directly when
it is reachable), and the URL is published to ntfy.sh so it costs zero copy-paste.
But nothing depends on the tunnel: if it is down, work still flows through Drive.

Protocol (one JSON object per file, atomic writes via .tmp + replace)
    {"id": "c001", "action": "run",   "recipe": "smoke", "params": {...}}
    {"id": "c002", "action": "shell", "cmd": "pip install ...", "mode": "sync"}
    {"id": "c003", "action": "job",   "job": "abc123"}
    {"id": "c004", "action": "status"}
    {"id": "c005", "action": "files"}
"""
from __future__ import annotations

import json
import os
import shutil
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CMD_NAME = "CHAOS_GPU_CMD.json"
RES_NAME = "CHAOS_GPU_RESULT.json"
BEAT_NAME = "CHAOS_GPU_HEARTBEAT.json"
CLIPS = "chaos_gpu_clips"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1))
    tmp.replace(path)


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


class Bridge:
    def __init__(self, folder: Path, token: str, url_getter=None, port: int = 8000):
        self.folder = folder
        self.token = token
        self.url_getter = url_getter or (lambda: None)
        self.port = port
        self.last_id = None
        self.processed = 0
        self.clips = folder / CLIPS
        self.clips.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------- http ---
    def api(self, path: str, **params) -> dict:
        params["token"] = self.token
        q = urllib.parse.urlencode(params)
        url = f"http://127.0.0.1:{self.port}{path}?{q}"
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    # --------------------------------------------------------------- files ---
    def sync_clips(self) -> list[str]:
        moved = []
        out = Path(os.environ.get("CHAOS_WORK", "/content/chaos_work")) / "out"
        if not out.exists():
            return moved
        for f in out.glob("*"):
            if not f.is_file():
                continue
            dst = self.clips / f.name
            try:
                if not dst.exists() or dst.stat().st_size != f.stat().st_size:
                    shutil.copy2(f, dst)
                    moved.append(f.name)
            except Exception:
                pass
        return moved

    def file_list(self) -> list[dict]:
        rows = []
        out = Path(os.environ.get("CHAOS_WORK", "/content/chaos_work")) / "out"
        for f in sorted(out.glob("*")) if out.exists() else []:
            if f.is_file():
                rows.append({"name": f.name, "bytes": f.stat().st_size})
        return rows

    def wait_job(self, jid: str, timeout: float) -> dict:
        """Poll a job until it finishes so the RESULT file carries the outcome."""
        t0 = time.time()
        last = {}
        while time.time() - t0 < timeout:
            last = self.api("/job", id=jid, tail=int(os.environ.get("CHAOS_TAIL", "25")))
            st = (last.get("job") or {}).get("state")
            if st in ("done", "failed", "cancelled"):
                return last
            time.sleep(2.0)
        last["ok"] = False
        last["error"] = f"still running after {timeout:.0f}s — poll /job or read RESULT again"
        return last

    # ------------------------------------------------------------ commands ---
    def handle(self, cmd: dict) -> dict:
        act = cmd.get("action", "status")
        if act == "status":
            return self.api("/status")
        if act == "recipes":
            return self.api("/recipes")
        if act == "files":
            return {"ok": True, "files": self.file_list(), "clips_dir": str(self.clips)}
        if act == "job":
            return self.api("/job", id=cmd.get("job", ""), tail=cmd.get("tail", 40))
        if act == "log":
            return self.api("/log", id=cmd.get("job", ""), offset=cmd.get("offset", 0))
        if act == "cancel":
            return self.api("/cancel", id=cmd.get("job", ""))
        if act in ("run", "shell"):
            params = {"recipe": cmd.get("recipe", "smoke")}
            if act == "shell":
                params = {"recipe": "shell", "cmd": cmd.get("cmd", ""),
                          "mode": cmd.get("mode", "sync")}
            params.update({k: str(v) for k, v in cmd.get("params", {}).items()})
            started = self.api("/run", **params)
            jid = started.get("job")
            wait = float(cmd.get("wait", 300))
            if jid and wait > 0:
                done = self.wait_job(jid, wait)
                done["started"] = started
                return done
            return started
        return {"ok": False, "error": f"unknown action {act}"}

    # ----------------------------------------------------------------- run ---
    def once(self) -> bool:
        p = self.folder / CMD_NAME
        cmd = read_json(p)
        if not cmd or not cmd.get("id") or cmd["id"] == self.last_id:
            return False
        cid = str(cmd["id"])
        t0 = time.time()
        res = self.handle(cmd)
        self.last_id = cid
        self.processed += 1
        moved = self.sync_clips()
        payload = {"cmd_id": cid, "action": cmd.get("action"), "at": now(),
                   "seconds": round(time.time() - t0, 1), "ok": bool(res.get("ok", True)),
                   "result": res, "files": self.file_list(), "synced": moved,
                   "processed": self.processed}
        write_json(self.folder / RES_NAME, payload)
        print(f"[bridge] {cid} {cmd.get('action')} ok={payload['ok']} "
              f"in {payload['seconds']}s", flush=True)
        return True

    def heartbeat(self) -> None:
        st = self.api("/status")
        beat = {"alive": True, "at": now(), "url": self.url_getter(),
                "processed": self.processed, "last_cmd": self.last_id,
                "gpu": st.get("gpu", {}), "jobs": st.get("job_states", {}),
                "queue": st.get("queue"), "files": self.file_list()}
        write_json(self.folder / BEAT_NAME, beat)

    def loop(self, interval: float = 5.0) -> None:
        last_beat = 0.0
        while True:
            try:
                self.once()
                if time.time() - last_beat > 30:
                    self.heartbeat()
                    last_beat = time.time()
            except Exception as e:
                print(f"[bridge] loop error {type(e).__name__}: {e}", flush=True)
            time.sleep(interval)


if __name__ == "__main__":
    folder = Path(os.environ.get("CHAOS_DRIVE_DIR", "."))
    token = os.environ.get("CHAOS_TOKEN", "")
    Bridge(folder, token).loop()
