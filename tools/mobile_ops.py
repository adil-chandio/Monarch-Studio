#!/usr/bin/env python3
"""MOBILEOPS-1 — durable operating state machine for phone-only Monarch Studio work.

The owner works from a phone. He taps; this repo does everything else.

Every project that leaves the agent's hands becomes ONE job file under
``studio/mobile/jobs/<job_id>.json``. That file is the single source of truth for
"who does what next", so a refresh, a new turn or a new agent never restarts work
and never invents an ad-hoc step.

States (in order):

    intake -> planned -> handed_off -> clip_ready -> mixed -> verified -> assembled -> delivered
                                   \\-> partial   (some clips came back)
                                   \\-> blocked    (a gate refused to advance)

Gate rule: a state is only reachable when its evidence exists on disk. Nothing is
marked complete by promise — clips must be real bytes, the master must have an md5.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
VG = ROOT / "tools" / "videogen.py"
JOB_ROOT = Path(os.environ.get("MONARCH_MOBILE_JOBS") or (ROOT / "studio" / "mobile" / "jobs"))
DRIVE_CONFIG = ROOT / "styles" / "monarch-ai-agent" / "data" / "drive.json"
SCHEMA_VERSION = 1
TOOL_VERSION = "mobileops-1.0"

STATES = [
    "intake",
    "planned",
    "handed_off",
    "partial",
    "clip_ready",
    "mixed",
    "verified",
    "assembled",
    "delivered",
    "blocked",
]

# state -> (what the owner does, what the agent does)
NEXT_ACTION = {
    "intake": ("kuch nahi", "plan: notebook + $0 estimate banao"),
    "planned": ("kuch nahi", "notebook Drive me upload karo, phir handoff --colab <link>"),
    "handed_off": ("Colab kholo -> Runtime ▸ Change runtime type ▸ T4 GPU -> Runtime ▸ Run all",
                   "intezaar; owner ke DONE ka wait"),
    "partial": ("wahi notebook khole rakho -> Runtime ▸ Run all (jo missing hai wahi banega)",
                "check: missing shots list karo, owner ko batao"),
    "clip_ready": ("kuch nahi", "finish: mix -> verify -> assemble"),
    "mixed": ("kuch nahi", "verify (height + audio + md5)"),
    "verified": ("kuch nahi", "assemble (concat -> MASTER)"),
    "assembled": ("kuch nahi", "master Drive '06 · Masters & Receipts' me daalo, phir deliver"),
    "delivered": ("link kholo, kaam khatam ✅", "receipt + continuity checkpoint"),
    "blocked": ("mujhe chat me 'atak gaya' likho", "blocker padho, fix karo, phir next"),
}

ALLOWED = {
    "intake": {"planned", "blocked"},
    "planned": {"handed_off", "blocked"},
    "handed_off": {"partial", "clip_ready", "blocked", "handed_off"},
    "partial": {"partial", "clip_ready", "blocked", "handed_off"},
    "clip_ready": {"mixed", "blocked", "clip_ready"},
    "mixed": {"verified", "blocked", "mixed"},
    "verified": {"assembled", "blocked", "verified"},
    "assembled": {"delivered", "blocked", "assembled"},
    "delivered": {"delivered"},
    "blocked": {"partial", "clip_ready", "mixed", "verified", "assembled", "handed_off", "planned",
                "blocked"},
}


class OpsError(RuntimeError):
    """A refusal the agent must read instead of guessing."""


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def slug(text: str) -> str:
    out = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return out[:48] or "job"


def job_path(job_id: str) -> Path:
    return JOB_ROOT / f"{job_id}.json"


def load_job(job_id: str) -> dict:
    path = job_path(job_id)
    if not path.exists():
        raise OpsError(f"job not found: {job_id} (dekho: mobile_ops.py list)")
    return json.loads(path.read_text())


def save_job(job: dict) -> Path:
    JOB_ROOT.mkdir(parents=True, exist_ok=True)
    job["updated_at"] = now_iso()
    JOB_ROOT.joinpath(f"{job['job_id']}.json").write_text(json.dumps(job, indent=2) + "\n")
    return job_path(job["job_id"])


def all_jobs() -> list[dict]:
    if not JOB_ROOT.exists():
        return []
    jobs = []
    for path in sorted(JOB_ROOT.glob("*.json")):
        try:
            jobs.append(json.loads(path.read_text()))
        except json.JSONDecodeError:
            continue
    return sorted(jobs, key=lambda j: j.get("created_at", ""))


def resolve_project(selector: str) -> Path:
    raw = Path(selector)
    candidates = [raw, ROOT / raw]
    if not raw.suffix:
        candidates += [
            ROOT / "studio" / "videogen" / "examples" / f"{selector}.project.json",
            ROOT / "studio" / "videogen" / "examples" / selector / "project.json",
            ROOT / "workflows" / "current" / "payload" / selector / "project.json",
            ROOT / selector / "project.json",
            ROOT / "workflows" / "current" / "payload" / f"{selector}.project.json",
        ]
    for cand in candidates:
        if cand.is_file():
            return cand.resolve()
    raise OpsError(f"project.json nahi mila: {selector}")


def rel(path: Path | str | None) -> str | None:
    if not path:
        return None
    path = Path(path)
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def abspath(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path)


def transition(job: dict, to_state: str, note: str = "", *, by: str = "agent") -> None:
    current = job["state"]
    if to_state != current and to_state not in ALLOWED.get(current, set()):
        raise OpsError(f"illegal transition {current} -> {to_state}; allowed: "
                       f"{', '.join(sorted(ALLOWED.get(current, set()))) or 'none'}")
    job["state"] = to_state
    user, agent = NEXT_ACTION[to_state]
    job["next"] = {"user": user, "agent": agent}
    job.setdefault("history", []).append(
        {"at": now_iso(), "from": current, "to": to_state, "by": by, "note": note}
    )


def gate(job: dict, name: str, ok: bool, detail: str = "") -> None:
    job.setdefault("gates", {})[name] = {"ok": ok, "detail": detail, "at": now_iso()}


# --------------------------------------------------------------------------- #
# evidence on disk
# --------------------------------------------------------------------------- #

def project_file(job: dict) -> Path:
    path = abspath(job.get("project"))
    if not path or not path.exists():
        raise OpsError(f"project.json missing for job {job['job_id']}: {job.get('project')}")
    return path


def project_dir(job: dict) -> Path:
    return project_file(job).parent


def shot_ids(job: dict) -> list[str]:
    data = json.loads(project_file(job).read_text())
    return [shot["id"] for shot in data.get("shots", [])]


def media_plan(job: dict) -> dict[str, list[str]]:
    """What the notebook should have produced, per stage."""
    base = project_dir(job)
    ids = shot_ids(job)
    clips = {}
    for sid in ids:
        hi = base / "shots" / f"{sid}-2x.mp4"
        lo = base / "shots" / f"{sid}.mp4"
        clips[sid] = [p for p in (hi, lo) if p.exists() and p.stat().st_size > 0]
    vo = [p for p in sorted((base / "audio" / "vo").glob("*.wav")) if p.stat().st_size > 0]
    foley = [p for p in sorted((base / "audio" / "foley").glob("*.wav")) if p.stat().st_size > 0]
    return {
        "shots": ids,
        "clips": [sid for sid, files in clips.items() if files],
        "missing": [sid for sid, files in clips.items() if not files],
        "vo": [rel(p) for p in vo],
        "foley": [rel(p) for p in foley],
        "clip_files": {sid: [rel(f) for f in files] for sid, files in clips.items()},
    }


def human_action(job: dict) -> str:
    return job.get("next", {}).get("user", NEXT_ACTION[job["state"]][0])


def agent_action(job: dict) -> str:
    return job.get("next", {}).get("agent", NEXT_ACTION[job["state"]][1])


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #

def start(selector: str, *, title: str | None = None, job_id: str | None = None,
          voice: str = "", foley: str = "", force: bool = False) -> dict:
    path = resolve_project(selector)
    data = json.loads(path.read_text())
    project_id = data.get("project_id", path.stem.split(".")[0])
    jid = job_id or f"mob-{datetime.now().strftime('%Y%m%d')}-{slug(project_id)}"
    if job_path(jid).exists() and not force:
        raise OpsError(f"job already exists: {jid} (--force se naya banega, ya status dekho)")
    job = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL_VERSION,
        "job_id": jid,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "title": title or data.get("title") or project_id,
        "project": rel(path),
        "project_id": project_id,
        "shots": [shot.get("id") for shot in data.get("shots", [])],
        "notebook": None,
        "colab_url": None,
        "voice_text": voice or _first_vo_text(data),
        "foley_prompt": foley or "ambient room tone, cinematic, subtle",
        "state": "intake",
        "gates": {},
        "next": {"user": NEXT_ACTION["intake"][0], "agent": NEXT_ACTION["intake"][1]},
        "history": [{"at": now_iso(), "from": None, "to": "intake", "by": "agent",
                     "note": f"job created for {project_id}"}],
        "master": None,
        "blocker": None,
    }
    save_job(job)
    return job


def _first_vo_text(project: dict) -> str:
    for shot in project.get("shots", []):
        text = shot.get("vo_text") or shot.get("voice_text")
        if text:
            return text
    return ""


def _run_videogen(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(VG), *args], cwd=ROOT, text=True,
                          capture_output=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def plan(job_id: str, *, runner=None) -> dict:
    runner = runner or _run_videogen
    job = load_job(job_id)
    path = project_file(job)
    code, out = runner(["plan", str(path)])
    text = (out or "").strip()
    detail = text.splitlines()[-1] if text else ""
    gate(job, "plan_estimate", code == 0, detail[:400])
    if code != 0:
        transition(job, "blocked", "plan failed", by="agent")
        job["blocker"] = {"stage": "plan", "detail": out[-1200:]}
        save_job(job)
        raise OpsError("plan failed:\n" + out[-1200:])
    plan_json = path.parent / "plan.json"
    if plan_json.exists():
        data = json.loads(plan_json.read_text())
        delivery = data.get("delivery") or {}
        job["plan"] = {
            "total_usd": data.get("estimate_usd"),
            "total_with_retries_usd": data.get("estimate_with_retries_usd"),
            "paid_steps": data.get("paid_step_count"),
            "free_only": data.get("free_only"),
            "engines": sorted({step.get("engine") for row in data.get("shots", [])
                               if isinstance(row, dict) for step in row.get("steps", [])
                               if step.get("engine")}),
            "delivery": {k: delivery.get(k) for k in ("free_width", "free_height",
                                                      "out_width", "out_height")},
            "warnings": data.get("warnings", []),
        }
    code, out = runner(["mobile", str(path)])
    if code != 0:
        transition(job, "blocked", "notebook failed", by="agent")
        job["blocker"] = {"stage": "mobile", "detail": out[-1200:]}
        save_job(job)
        raise OpsError("notebook build failed:\n" + out[-1200:])
    notebook = path.parent / "mobile" / f"MOBILE_{job['project_id']}.ipynb"
    job["notebook"] = rel(notebook) if notebook.exists() else None
    gate(job, "notebook", notebook.exists(), rel(notebook) or "missing")
    transition(job, "planned", "estimate + phone notebook ready")
    save_job(job)
    return job


def handoff(job_id: str, *, colab: str | None = None, note: str = "") -> dict:
    job = load_job(job_id)
    notebook = abspath(job.get("notebook"))
    if not notebook or not notebook.exists():
        raise OpsError("notebook missing — pehle plan chalao")
    url = colab or job.get("colab_url")
    if not url:
        raise OpsError("Colab link chahiye: notebook Drive me upload karke "
                       "`handoff <job> --colab <https://colab.research.google.com/drive/...>` chalao")
    if not url.startswith("https://colab.research.google.com/"):
        raise OpsError(f"colab link nahi lagta: {url}")
    job["colab_url"] = url
    job["handed_off_at"] = now_iso()
    gate(job, "handoff", True, url)
    transition(job, "handed_off", note or "link owner ko bheja", by="agent")
    save_job(job)
    return job


def ingest(job_id: str, zip_path: str | pathlib.Path, *, run_check: bool = True) -> dict:
    """Unpack the notebook's `_outputs.zip` into the project folder, then re-check.

    Phone reality: Drive mount fails, the notebook hands back a ZIP, and the owner attaches it.
    This is the only supported way those bytes enter the project.
    """
    job = load_job(job_id)
    src = Path(zip_path)
    if not src.exists():
        raise OpsError(f"zip nahi mila: {zip_path}")
    import zipfile
    base = project_dir(job)
    with zipfile.ZipFile(src) as bundle:
        names = [n for n in bundle.namelist() if not n.endswith("/")]
        media = [n for n in names if n.lower().endswith((".mp4", ".wav"))]
        if not media:
            raise OpsError("zip me koi .mp4/.wav nahi mila — galat file?")
        for name in names:
            target = (base / name).resolve()
            if base.resolve() not in target.parents and target != base.resolve():
                raise OpsError(f"zip entry project folder se bahar ja raha hai: {name}")
        bundle.extractall(base)
    job.setdefault("history", []).append(
        {"at": now_iso(), "from": job["state"], "to": job["state"], "by": "agent",
         "note": f"ingest {src.name}: {len(media)} media file(s)"})
    job["ingest"] = {"zip": src.name, "files": len(media), "at": now_iso(),
                     "bytes": src.stat().st_size}
    gate(job, "ingest", True, f"{len(media)} files from {src.name}")
    save_job(job)
    return check(job_id) if run_check else job


def check(job_id: str) -> dict:
    job = load_job(job_id)
    media = media_plan(job)
    job["media"] = media
    total = len(media["shots"])
    have = len(media["clips"])
    if total and have == 0:
        gate(job, "clips", False, "0/" + str(total))
        transition(job, "blocked", "koi clip nahi aaya", by="agent")
        job["blocker"] = {"stage": "clips",
                          "detail": "Notebook ne kuch nahi likha. Run all dobara chalao; "
                                    "agar ADHURA aaya to aakhri cell ka text bhejo."}
        job["next"] = {"user": "Colab me dobara Runtime ▸ Run all dabao (T4 GPU selected ho)",
                       "agent": "owner ke re-run ke baad phir check"}
    elif media["missing"]:
        gate(job, "clips", False, f"{have}/{total}")
        transition(job, "partial", f"missing: {', '.join(media['missing'])}", by="notebook")
        job["next"] = {"user": "wahi notebook -> Runtime ▸ Run all (sirf missing shots banenge)",
                       "agent": "owner ko missing shots batao, phir check dobara"}
    else:
        gate(job, "clips", True, f"{have}/{total}")
        transition(job, "clip_ready", "saare clips aa gaye", by="notebook")
        job.pop("blocker", None)
    save_job(job)
    return job


def finish(job_id: str, *, runner=None, loudnorm: bool = True) -> dict:
    runner = runner or _run_videogen
    job = load_job(job_id)
    media = media_plan(job)
    if not media["clips"]:
        raise OpsError("clips nahi hain — finish se pehle check pass karna zaroori hai")
    if job["state"] not in {"clip_ready", "mixed", "verified", "blocked", "handed_off", "partial"}:
        raise OpsError(f"finish is state me nahi chalta: {job['state']}")
    if job["state"] != "clip_ready":
        transition(job, "clip_ready", "clips confirmed before finish", by="agent")
    path = str(project_file(job))
    stages = [("mix", ["mix", path] + (["--loudnorm"] if loudnorm else [])),
              ("verify", ["verify", path]),
              ("assemble", ["assemble", path])]
    state_after = {"mix": "mixed", "verify": "verified", "assemble": "assembled"}
    for name, args in stages:
        code, out = runner(args)
        tail = "\n".join((out or "").strip().splitlines()[-6:])
        ok = code == 0
        gate(job, name, ok, f"exit {code}: {tail}"[:800])
        if not ok:
            job["blocker"] = {"stage": name, "exit": code, "detail": tail[-1200:]}
            transition(job, "blocked", f"{name} exit {code}", by="agent")
            save_job(job)
            raise OpsError(f"{name} failed (exit {code}):\n{tail}")
        transition(job, state_after[name], f"{name} ok")
        save_job(job)
    master = project_dir(job) / "delivery" / f"{job['project_id']}_MASTER.mp4"
    if not master.exists() or master.stat().st_size == 0:
        job["blocker"] = {"stage": "assemble", "detail": "master file missing after assemble"}
        transition(job, "blocked", "master missing", by="agent")
        save_job(job)
        raise OpsError("assemble ne master nahi banaya")
    job["master"] = {"path": rel(master), "md5": md5(master), "bytes": master.stat().st_size,
                     "probe": _probe(master), "drive_id": None, "url": None}
    gate(job, "master", True, job["master"]["md5"])
    save_job(job)
    return job


def _probe(path: Path) -> dict:
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import videogen  # noqa: PLC0415 - optional, needs ffmpeg
        info = videogen.probe(path)
    except Exception:  # noqa: BLE001 - probe is evidence, never a hard dependency
        return {}
    keys = ("width", "height", "fps", "duration", "video_codec", "audio_codec")
    return {k: info.get(k) for k in keys}


def adopt(job_id: str, receipt_path: str | pathlib.Path) -> dict:
    """Take the notebook's `colab_master_receipt.json` as master evidence.

    The sandbox cannot reach Drive, and the master never needs to travel: the machine that
    has the bytes (Colab) writes md5 + probe, we record it and let Drive hold the file.
    """
    job = load_job(job_id)
    path = Path(receipt_path)
    if not path.exists():
        raise OpsError(f"receipt nahi mila: {receipt_path}")
    data = json.loads(path.read_text())
    info = data.get("info") or {}
    if not info.get("md5") or not info.get("bytes"):
        raise OpsError("receipt me master ka md5/bytes nahi hai — notebook ka finish stage chalao")
    if int(info["bytes"]) <= 0:
        raise OpsError("master 0 byte ka hai — asli file nahi")
    if not info.get("height"):
        raise OpsError("receipt me height nahi — probe fail hua")
    job["master"] = {
        "path": f"delivery/{data.get('master')}",
        "md5": info["md5"], "bytes": info["bytes"],
        "probe": {"width": info.get("width"), "height": info.get("height"), "fps": info.get("fps"),
                  "duration": info.get("duration"), "audio_codec": info.get("audio_codec")},
        "drive_id": None, "url": None, "evidence": "colab_master_receipt.json",
    }
    gate(job, "master", True, f"{info['md5']} (colab receipt)")
    gate(job, "mix", bool(info.get("audio_codec")), f"audio={info.get('audio_codec')}")
    gate(job, "verify", int(info.get("height") or 0) >= 480, f"{info.get('width')}x{info.get('height')}")
    if job["state"] not in {"assembled", "delivered"}:
        if job["state"] in {"blocked", "clip_ready", "mixed", "verified", "handed_off", "partial"}:
            job["state"] = "verified"
            transition(job, "assembled", "master receipt adopted from Colab", by="notebook")
        else:
            raise OpsError(f"adopt is state me nahi chalta: {job['state']}")
    job.pop("blocker", None)
    save_job(job)
    return job


def deliver(job_id: str, *, master_id: str, url: str | None = None, note: str = "") -> dict:
    job = load_job(job_id)
    if job["state"] not in {"assembled", "delivered"}:
        raise OpsError(f"deliver se pehle assemble: state = {job['state']}")
    if not job.get("master") or not job["master"].get("md5"):
        raise OpsError("master ka md5 nahi hai — finish dobara chalao")
    job["master"]["drive_id"] = master_id
    job["master"]["url"] = url
    job["delivered_at"] = now_iso()
    gate(job, "delivery", True, master_id)
    job["receipt"] = receipt_block(job)
    transition(job, "delivered", note or "master Drive me hai", by="agent")
    save_job(job)
    return job


def receipt_block(job: dict) -> dict:
    master = job.get("master") or {}
    return {
        "job_id": job["job_id"],
        "title": job.get("title"),
        "project": job.get("project"),
        "notebook": job.get("notebook"),
        "colab_url": job.get("colab_url"),
        "master": {"path": master.get("path"), "md5": master.get("md5"),
                   "bytes": master.get("bytes"), "probe": master.get("probe", {}),
                   "drive_id": master.get("drive_id"), "url": master.get("url")},
        "cost_usd": (job.get("plan") or {}).get("total_usd"),
        "gates": {name: value.get("ok") for name, value in (job.get("gates") or {}).items()},
        "receipted_at": now_iso(),
    }


def master_probe(job: dict) -> dict:
    """Probe the master again if the stored evidence predates a field (e.g. audio codec)."""
    master = job.get("master") or {}
    probe = dict(master.get("probe") or {})
    if probe.get("audio_codec") is None:
        path = abspath(master.get("path"))
        if path and path.exists():
            fresh = _probe(path)
            if fresh:
                stale = set(probe) - set(fresh)
                probe = {**{k: probe[k] for k in stale}, **{k: v for k, v in fresh.items() if v is not None}}
    return probe


def card(job: dict) -> str:
    """The one message the agent is allowed to send the owner."""
    lines = [f"**{job.get('title')}** · job `{job['job_id']}` · state `{job['state']}`", ""]
    state = job["state"]
    if state == "handed_off":
        lines += ["Aap ka kaam (3 tap):",
                  "1. Neelam button: **Runtime ▸ Change runtime type ▸ T4 GPU**",
                  "2. **Runtime ▸ Run all**",
                  "3. Aakhri cell me **`DONE ✅`** aaye to chat me `DONE` likh do",
                  "", f"Notebook: {job.get('colab_url')}",
                  "", "Baaki sab main karunga — koi command nahi, koi install nahi."]
    elif state == "partial":
        missing = (job.get("media") or {}).get("missing") or []
        lines += [f"Adhe clips aa gaye. Missing: {', '.join(missing) or 'unknown'}",
                  "Wahi notebook kholo → **Runtime ▸ Run all** (jo hai wo skip ho jayega).",
                  f"Notebook: {job.get('colab_url')}"]
    elif state == "delivered":
        master = job.get("master") or {}
        probe = master_probe(job)
        size = round((master.get("bytes") or 0) / (1024 * 1024), 1)
        lines += ["**Master ready ✅**",
                  f"`{master.get('path')}` · {size} MB · md5 `{master.get('md5')}`",
                  f"{probe.get('width')}×{probe.get('height')} · {probe.get('fps')} fps · "
                  f"{probe.get('duration')}s · audio: {probe.get('audio_codec')}",
                  f"Drive: {master.get('url') or master.get('drive_id')}"]
    else:
        lines += [f"Aap: {human_action(job)}", f"Main: {agent_action(job)}"]
    return "\n".join(lines)


def status(job_id: str | None = None, *, as_json: bool = False) -> int:
    jobs = [load_job(job_id)] if job_id else all_jobs()
    if as_json:
        print(json.dumps({"tool": TOOL_VERSION, "jobs": jobs}, indent=2))
        return 0
    if not jobs:
        print("koi job nahi. shuru karo: mobile_ops.py start --project <id>")
        return 0
    for job in jobs:
        print(f"{job['job_id']:<34} {job['state']:<11} {job.get('title')}")
        print(f"   aap : {human_action(job)}")
        print(f"   main: {agent_action(job)}")
        if job.get("blocker"):
            print(f"   ⚠ {job['blocker'].get('stage')}: "
                  f"{str(job['blocker'].get('detail', ''))[:160]}")
    return 0


def next_action(job_id: str) -> int:
    job = load_job(job_id)
    print(card(job))
    print()
    print(f"next (agent): {agent_action(job)}")
    if job.get("state") == "planned" and job.get("notebook"):
        print(f"  upload: {job['notebook']}  ->  handoff {job_id} --colab <link>")
    elif job.get("state") in {"clip_ready", "mixed", "verified"}:
        print(f"  command: python3 tools/mobile_ops.py finish {job_id}")
    elif job.get("state") == "assembled":
        print(f"  upload delivery master -> deliver {job_id} --master-id <id> --url <link>")
    return 0


def doctor() -> int:
    problems = []
    try:
        JOB_ROOT.mkdir(parents=True, exist_ok=True)
        probe_file = JOB_ROOT / ".write-test"
        probe_file.write_text("ok")
        probe_file.unlink()
    except OSError as exc:
        problems.append(f"jobs dir not writable: {exc}")
    if not VG.exists():
        problems.append("tools/videogen.py missing")
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import videogen  # noqa: PLC0415
        if not videogen.which("ffmpeg"):
            problems.append("ffmpeg missing (pip install --break-system-packages imageio-ffmpeg)")
    except Exception as exc:  # noqa: BLE001
        problems.append(f"videogen import failed: {exc}")
    for job in all_jobs():
        if job["state"] in {"handed_off", "partial"} and job.get("colab_url") is None:
            problems.append(f"{job['job_id']}: handed off without a Colab link")
    print(f"MOBILEOPS {TOOL_VERSION} · jobs: {len(all_jobs())} · dir: {rel(JOB_ROOT)}")
    for problem in problems:
        print(f"FAIL {problem}")
    if not problems:
        print("PASS phone ops ready (jobs dir, videogen, ffmpeg, no orphan handoff)")
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="phone-only Monarch Studio state machine")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_start = sub.add_parser("start", help="create a job for a project")
    p_start.add_argument("--project", required=True, help="project.json path or project id")
    p_start.add_argument("--title")
    p_start.add_argument("--job-id")
    p_start.add_argument("--voice", default="")
    p_start.add_argument("--foley", default="")
    p_start.add_argument("--force", action="store_true")

    p_plan = sub.add_parser("plan", help="estimate + build the phone notebook")
    p_plan.add_argument("job")

    p_hand = sub.add_parser("handoff", help="record the Colab link and arm the owner's 3 taps")
    p_hand.add_argument("job")
    p_hand.add_argument("--colab", required=True)
    p_hand.add_argument("--note", default="")

    p_check = sub.add_parser("check", help="did the notebook actually produce files?")
    p_check.add_argument("job")

    p_ingest = sub.add_parser("ingest", help="unpack the notebook's _outputs.zip into the project")
    p_ingest.add_argument("job")
    p_ingest.add_argument("--zip", required=True, dest="zip_path")

    p_finish = sub.add_parser("finish", help="mix -> verify -> assemble, stop at the first refusal")
    p_finish.add_argument("job")
    p_finish.add_argument("--no-loudnorm", action="store_true")

    p_adopt = sub.add_parser("adopt", help="record the master made inside Colab (receipt evidence)")
    p_adopt.add_argument("job")
    p_adopt.add_argument("--receipt", required=True)

    p_deliver = sub.add_parser("deliver", help="record the Drive master id and close the job")
    p_deliver.add_argument("job")
    p_deliver.add_argument("--master-id", required=True)
    p_deliver.add_argument("--url")
    p_deliver.add_argument("--note", default="")

    p_status = sub.add_parser("status", help="every job and who does what next")
    p_status.add_argument("job", nargs="?")
    p_status.add_argument("--json", action="store_true")

    p_next = sub.add_parser("next", help="the single next action + the owner-facing card")
    p_next.add_argument("job")

    p_card = sub.add_parser("card", help="print only the owner-facing message")
    p_card.add_argument("job")

    p_list = sub.add_parser("list", help="job ids and states")
    p_list.add_argument("--json", action="store_true")

    sub.add_parser("doctor", help="is phone ops usable here?")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "start":
            job = start(args.project, title=args.title, job_id=args.job_id,
                        voice=args.voice, foley=args.foley, force=args.force)
            print(f"job {job['job_id']} · state {job['state']}")
            print(card(job))
            print(f"\nnext: python3 tools/mobile_ops.py plan {job['job_id']}")
        elif args.cmd == "plan":
            job = plan(args.job)
            print(f"job {job['job_id']} · state {job['state']} · notebook {job.get('notebook')}")
            if job.get("plan"):
                plan_info = job["plan"]
                size = plan_info.get("delivery") or {}
                print(f"estimate: ${plan_info.get('total_usd')} (paid steps: "
                      f"{plan_info.get('paid_steps')}) · "
                      f"{size.get('free_width')}x{size.get('free_height')} -> "
                      f"{size.get('out_width')}x{size.get('out_height')}")
                print(f"engines: {', '.join(plan_info.get('engines') or []) or 'free queue'}")
            print("next: notebook Drive me upload karke -> handoff --colab <link>")
        elif args.cmd == "handoff":
            job = handoff(args.job, colab=args.colab, note=args.note)
            print(card(job))
        elif args.cmd == "ingest":
            job = ingest(args.job, args.zip_path)
            print(f"ingest: {job.get('ingest')}")
            print(card(job))
        elif args.cmd == "check":
            job = check(args.job)
            print(card(job))
        elif args.cmd == "finish":
            job = finish(args.job, loudnorm=not args.no_loudnorm)
            master = job.get("master") or {}
            print(f"MASTER {master.get('path')} · {round((master.get('bytes') or 0)/1048576, 2)} MB "
                  f"· md5 {master.get('md5')}")
            print("next: upload to 06 · Masters & Receipts -> deliver --master-id <id>")
        elif args.cmd == "adopt":
            job = adopt(args.job, args.receipt)
            master = job.get("master") or {}
            probe = master.get("probe") or {}
            print(f"MASTER adopted · {master.get('path')} · {round((master.get('bytes') or 0)/1048576, 2)} MB "
                  f"· {probe.get('width')}x{probe.get('height')} · {probe.get('duration')}s · "
                  f"audio {probe.get('audio_codec')} · md5 {master.get('md5')}")
            print("next: master ka Drive id -> deliver")
        elif args.cmd == "deliver":
            job = deliver(args.job, master_id=args.master_id, url=args.url, note=args.note)
            print(card(job))
        elif args.cmd == "status":
            return status(args.job, as_json=args.json)
        elif args.cmd == "next":
            return next_action(args.job)
        elif args.cmd == "card":
            print(card(load_job(args.job)))
        elif args.cmd == "list":
            jobs = all_jobs()
            if args.json:
                print(json.dumps([{ "job_id": j["job_id"], "state": j["state"],
                                    "title": j.get("title")} for j in jobs], indent=2))
            else:
                for job in jobs:
                    print(f"{job['job_id']:<34} {job['state']:<11} {job.get('title')}")
                if not jobs:
                    print("(koi job nahi)")
        elif args.cmd == "doctor":
            return doctor()
    except OpsError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
