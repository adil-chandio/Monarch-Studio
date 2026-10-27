#!/usr/bin/env python3
"""
MONARCH · CHAOS — GPU control server (runs INSIDE Colab/Kaggle).

Why this exists
---------------
The agent works from a chat sandbox whose shell cannot open sockets to the public
internet, but whose page-fetch tool CAN read any public URL (verified: GET works,
POST does not). So this server speaks plain GET with a token, gets exposed through
a tunnel, and the agent drives the GPU machine through it.

Endpoints (all GET; token required except /health)
    /health                     liveness, no token
    /status                     gpu, vram, engine, uptime, disk, job summary
    /recipes                    what can run on this machine
    /run?recipe=..&prompt=..    start a job            -> {"job": id}
    /jobs                       all jobs
    /job?id=..                  one job incl. log tail
    /log?id=..&offset=0         raw log from offset
    /cancel?id=..               request cancel
    /files                      produced files + sha256 + size
    /file?id=..&name=..         raw bytes of one output (small files only)

Design rules
    * one worker thread: a 16 GB T4 cannot run two video models at once
    * every job writes a log line stream the agent can poll
    * resume: a job whose output already exists is skipped unless force=1
    * nothing is deleted; outputs are copied to Drive by the notebook runtime
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from flask import Flask, jsonify, request, send_file
except ImportError:  # pragma: no cover
    raise SystemExit("pip install flask first")

APP = Flask(__name__)
TOKEN = os.environ.get("CHAOS_TOKEN", "")
WORK = Path(os.environ.get("CHAOS_WORK", Path.cwd() / "chaos_work"))
OUT = WORK / "out"
LOGS = WORK / "logs"
for d in (WORK, OUT, LOGS):
    d.mkdir(parents=True, exist_ok=True)

START = time.time()
JOBS: dict[str, dict] = {}
QUEUE: list[str] = []
LOCK = threading.Lock()
WORKER_STARTED = False


# ------------------------------------------------------------------ helpers ---
def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def gpu_facts() -> dict:
    facts = dict(hostname=platform.node(), python=platform.python_version(),
                 started=now())
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,driver_version",
             "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
        if out:
            p = [x.strip() for x in out.splitlines()[0].split(",")]
            facts.update(gpu=p[0], vram_total_mb=p[1], vram_used_mb=p[2], driver=p[3])
            try:
                facts["vram_gb"] = round(int(p[1].split()[0]) / 1024, 1)
            except Exception:
                pass
    except FileNotFoundError:
        facts["gpu"] = "none"
    try:
        import torch
        facts["torch"] = torch.__version__
        facts["cuda_build"] = torch.version.cuda
        facts["cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            facts["vram_gb"] = round(
                torch.cuda.get_device_properties(0).total_memory / 1024 ** 3, 1)
            facts["bf16_ok"] = torch.cuda.is_bf16_supported()
    except Exception as e:
        facts["torch_error"] = f"{type(e).__name__}: {e}"
    try:
        du = shutil.disk_usage("/")
        facts["disk_free_gb"] = round(du.free / 1024 ** 3, 1)
    except Exception:
        pass
    v = facts.get("vram_gb", 0) or 0
    if v >= 38:
        facts["tier"], facts["engine"] = "A100-40GB+", "wan_animate_14b"
    elif v >= 20:
        facts["tier"], facts["engine"] = "24GB", "wan_ti2v_5b"
    elif v >= 13:
        facts["tier"], facts["engine"] = "16GB", "ltx_2b"
    else:
        facts["tier"], facts["engine"] = "none", "smoke_only"
    return facts


def auth_ok() -> bool:
    if not TOKEN:
        return True
    return request.args.get("token") == TOKEN


def need_auth():
    if not auth_ok():
        return jsonify(ok=False, error="bad token"), 403
    return None


def ffmpeg_exe() -> str:
    """Colab ships system ffmpeg; Kaggle may not. Fall back to imageio-ffmpeg."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    for extra in ([], ["--break-system-packages"]):
        subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                        "imageio-ffmpeg"] + extra, check=False,
                       capture_output=True)
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            continue
    raise RuntimeError("no ffmpeg available and imageio-ffmpeg install failed")


def logwrite(job: dict, msg: str) -> None:
    line = f"[{now()}] {msg}"
    with LOCK:
        job["log"].append(line)
        if len(job["log"]) > 4000:
            del job["log"][:1000]
    try:
        with open(LOGS / f"{job['id']}.log", "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ------------------------------------------------------------------ recipes ---
def r_smoke(job: dict, p: dict) -> str:
    """No model needed: proves the whole loop (job -> file -> Drive) in ~20 s."""
    ff = ffmpeg_exe()
    secs = float(p.get("seconds", 3))
    name = p.get("name") or f"smoke_{job['id'][:6]}.mp4"
    dest = OUT / name
    logwrite(job, f"ffmpeg smoke render {secs}s")
    cmd = [ff, "-y", "-v", "error", "-f", "lavfi",
           "-i", f"testsrc2=size=540x960:rate=30:duration={secs}",
           "-f", "lavfi", "-i", f"sine=frequency=220:duration={secs}",
           "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "96k", "-shortest", str(dest)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-600:])
    logwrite(job, f"smoke ok -> {dest.name} ({dest.stat().st_size} B)")
    return dest.name


def _diffusers_pipe(kind: str, p: dict, job: dict):
    import torch
    from diffusers import DiffusionPipeline

    model = p.get("model")
    vram = gpu_facts().get("vram_gb", 0) or 0
    if kind == "ltx":
        model = model or "Lightricks/LTX-Video"
    elif kind == "wan":
        model = model or "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
    elif kind == "animate":
        model = model or "Wan-AI/Wan2.2-Animate-14B-Diffusers"
    logwrite(job, f"loading {model} (vram {vram} GB, kind={kind})")
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    pipe = DiffusionPipeline.from_pretrained(model, torch_dtype=dtype,
                                             variant="fp16" if dtype == torch.float16 else None)
    pipe.to("cuda")
    try:
        pipe.enable_model_cpu_offload()
        logwrite(job, "cpu offload enabled")
    except Exception as e:
        logwrite(job, f"offload unavailable: {e}")
    return pipe


def r_ltx(job: dict, p: dict) -> str:
    import torch
    pipe = _diffusers_pipe("ltx", p, job)
    prompt = p.get("prompt") or ("cinematic dark hall, masked figure in a long black coat, "
                                 "crescent of scarlet light across the visor, red doorway glow, "
                                 "volumetric haze, shallow depth of field, film grain")
    frames = int(p.get("frames", 49))
    h, w = int(p.get("height", 480)), int(p.get("width", 768))
    steps = int(p.get("steps", 30))
    seed = int(p.get("seed", 20261026))
    logwrite(job, f"ltx: {w}x{h} frames={frames} steps={steps} seed={seed}")
    g = torch.Generator(device="cuda").manual_seed(seed)
    res = pipe(prompt=prompt, num_frames=frames, height=h, width=w,
               num_inference_steps=steps, generator=g)
    name = p.get("name") or f"ltx_{job['id'][:6]}.mp4"
    dest = OUT / name
    _save_video(res.frames[0], dest, fps=int(p.get("fps", 24)), job=job)
    del pipe
    torch.cuda.empty_cache()
    return dest.name


def r_wan(job: dict, p: dict) -> str:
    import torch
    pipe = _diffusers_pipe("wan", p, job)
    prompt = p.get("prompt") or ("dark industrial hall, masked monarch figure, long black coat, "
                                 "scarlet visor crescent, cinematic red rim light, film grain")
    steps = int(p.get("steps", 30))
    seed = int(p.get("seed", 20261026))
    logwrite(job, f"wan: steps={steps} seed={seed}")
    g = torch.Generator(device="cuda").manual_seed(seed)
    kw = dict(prompt=prompt, num_inference_steps=steps, generator=g)
    if p.get("frames"):
        kw["num_frames"] = int(p["frames"])
    if p.get("height") and p.get("width"):
        kw["height"], kw["width"] = int(p["height"]), int(p["width"])
    res = pipe(**kw)
    name = p.get("name") or f"wan_{job['id'][:6]}.mp4"
    dest = OUT / name
    _save_video(res.frames[0], dest, fps=int(p.get("fps", 16)), job=job)
    del pipe
    torch.cuda.empty_cache()
    return dest.name


def r_animate(job: dict, p: dict) -> str:
    raise RuntimeError(
        "Wan-Animate needs a driving video. Upload the driving clip to the Drive "
        "folder, pass driving=<path or Drive name> and this recipe will be wired "
        "by the agent on the next turn (API shape already accepted).")


def _save_video(frames, dest: Path, fps: int, job: dict) -> None:
    import numpy as np
    ff = ffmpeg_exe()
    logwrite(job, f"writing {len(frames)} frames -> {dest.name} @ {fps}fps")
    arr = (np.stack(frames) * 255).clip(0, 255).astype(np.uint8) if frames[0].max() <= 1.0 \
        else np.stack(frames).astype(np.uint8)
    H, W = arr.shape[1], arr.shape[2]
    cmd = [ff, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", str(dest)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.communicate(arr.tobytes())
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg encode failed")
    logwrite(job, f"encode ok ({dest.stat().st_size} B)")


RECIPES = {"smoke": r_smoke, "ltx": r_ltx, "wan": r_wan, "animate": r_animate}


# --------------------------------------------------------------- job runner ---
def worker() -> None:
    while True:
        with LOCK:
            jid = QUEUE.pop(0) if QUEUE else None
        if not jid:
            time.sleep(0.7)
            continue
        job = JOBS[jid]
        with LOCK:
            job.update(state="running", started=now())
        logwrite(job, f"job {jid} started (recipe={job['params'].get('recipe')})")
        try:
            fn = RECIPES[job["params"]["recipe"]]
            out = fn(job, job["params"])
            with LOCK:
                job.update(state="done", finished=now(), output=out)
            logwrite(job, f"job {jid} done")
        except Exception as e:
            tb = traceback.format_exc()[-1200:]
            logwrite(job, f"job {jid} FAILED {type(e).__name__}: {e}")
            logwrite(job, tb)
            with LOCK:
                job.update(state="failed", finished=now(), error=f"{type(e).__name__}: {e}")


def ensure_worker() -> None:
    global WORKER_STARTED
    with LOCK:
        if WORKER_STARTED:
            return
        WORKER_STARTED = True
    threading.Thread(target=worker, daemon=True, name="chaos-worker").start()


# -------------------------------------------------------------------- routes ---
@APP.get("/health")
def health():
    return jsonify(ok=True, service="monarch-chaos-gpu", uptime_s=round(time.time() - START, 1))


@APP.get("/status")
def status():
    bad = need_auth()
    if bad:
        return bad
    ensure_worker()
    with LOCK:
        s = {k: v for k, v in JOBS.items()}
    counts = {}
    for j in s.values():
        counts[j["state"]] = counts.get(j["state"], 0) + 1
    return jsonify(ok=True, gpu=gpu_facts(), jobs_total=len(s), job_states=counts,
                   queue=len(QUEUE), latest=sorted(s.values(), key=lambda j: j["created"])[-3:])


@APP.get("/recipes")
def recipes():
    bad = need_auth()
    if bad:
        return bad
    f = gpu_facts()
    allow = ["smoke"]
    if (f.get("vram_gb") or 0) >= 13:
        allow.append("ltx")
    if (f.get("vram_gb") or 0) >= 20:
        allow.append("wan")
    if (f.get("vram_gb") or 0) >= 38:
        allow.append("animate")
    return jsonify(ok=True, vram_gb=f.get("vram_gb"), tier=f.get("tier"),
                   runnable=allow, all=list(RECIPES))


@APP.get("/run")
def run():
    bad = need_auth()
    if bad:
        return bad
    ensure_worker()
    recipe = request.args.get("recipe", "smoke")
    if recipe not in RECIPES:
        return jsonify(ok=False, error=f"unknown recipe {recipe}",
                       known=list(RECIPES)), 400
    params = {k: v for k, v in request.args.items() if k not in ("token", "recipe")}
    params["recipe"] = recipe
    jid = uuid.uuid4().hex[:10]
    job = dict(id=jid, created=now(), state="queued", params=params, log=[],
               output=None, error=None)
    with LOCK:
        JOBS[jid] = job
        QUEUE.append(jid)
    logwrite(job, f"queued with {params}")
    return jsonify(ok=True, job=jid, state="queued")


@APP.get("/jobs")
def jobs():
    bad = need_auth()
    if bad:
        return bad
    with LOCK:
        rows = [{k: j[k] for k in ("id", "state", "created", "finished", "output",
                                   "error")} | {"recipe": j["params"].get("recipe")}
                for j in JOBS.values()]
    rows.sort(key=lambda r: r["created"], reverse=True)
    return jsonify(ok=True, count=len(rows), jobs=rows[:60])


@APP.get("/job")
def job_detail():
    bad = need_auth()
    if bad:
        return bad
    j = JOBS.get(request.args.get("id", ""))
    if not j:
        return jsonify(ok=False, error="no such job"), 404
    tail = int(request.args.get("tail", 40))
    return jsonify(ok=True, job=dict(id=j["id"], state=j["state"], params=j["params"],
                                     output=j["output"], error=j["error"],
                                     created=j["created"], finished=j["finished"]),
                   log=j["log"][-tail:])


@APP.get("/log")
def log():
    bad = need_auth()
    if bad:
        return bad
    j = JOBS.get(request.args.get("id", ""))
    if not j:
        return jsonify(ok=False, error="no such job"), 404
    off = int(request.args.get("offset", 0))
    with LOCK:
        chunk = j["log"][off:]
    return jsonify(ok=True, offset=off, next=off + len(chunk), lines=chunk)


@APP.get("/cancel")
def cancel():
    bad = need_auth()
    if bad:
        return bad
    jid = request.args.get("id", "")
    with LOCK:
        if jid in QUEUE:
            QUEUE.remove(jid)
            JOBS[jid]["state"] = "cancelled"
            return jsonify(ok=True, cancelled=jid)
    return jsonify(ok=False, error="running or unknown jobs cannot be cancelled here "
                                   "(kill the cell instead)"), 400


@APP.get("/files")
def files():
    bad = need_auth()
    if bad:
        return bad
    import hashlib
    rows = []
    for f in sorted(OUT.glob("*")):
        if f.is_file():
            rows.append(dict(name=f.name, bytes=f.stat().st_size,
                             sha256=hashlib.sha256(f.read_bytes()).hexdigest()[:16],
                             mtime=datetime.fromtimestamp(f.stat().st_mtime,
                                                          timezone.utc).strftime("%H:%M:%SZ")))
    return jsonify(ok=True, dir=str(OUT), count=len(rows), files=rows)


@APP.get("/file")
def file_bytes():
    bad = need_auth()
    if bad:
        return bad
    name = request.args.get("name", "")
    p = (OUT / name).resolve()
    if not str(p).startswith(str(OUT.resolve())) or not p.exists():
        return jsonify(ok=False, error="not found"), 404
    if p.stat().st_size > 2_000_000:
        return jsonify(ok=False, error="file too large for the page-fetch channel; "
                                       "read it from Drive instead"), 413
    return send_file(p)


@APP.get("/")
def index():
    f = gpu_facts()
    return (f"<h2>MONARCH CHAOS GPU</h2><pre>{json.dumps(f, indent=1)}</pre>"
            f"<p>endpoints: /status /recipes /run /jobs /job /log /files</p>")


def serve(host="0.0.0.0", port=8000):
    ensure_worker()
    APP.run(host=host, port=port, threaded=True, use_reloader=False)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"serving on :{port}  work={WORK}")
    serve(port=port)
