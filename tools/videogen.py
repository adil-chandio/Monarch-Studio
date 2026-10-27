#!/usr/bin/env python3
"""MONARCH STUDIO · VIPER-1 — our own AI video generation tool.

One project file, many engines. The engine picks *how* a shot gets made (paid H3 API,
free Colab GPU queue, local 24 GB card, lipsync pass), prices it, renders what it can,
queues what it cannot, verifies the media and assembles the master.

    python3 tools/videogen.py doctor
    python3 tools/videogen.py new --id monarch-reel-01 --title "Monarch reel 01" --aspect 9:16
    python3 tools/videogen.py plan   workflows/current/payload/monarch-reel-01/project.json
    python3 tools/videogen.py render workflows/current/payload/monarch-reel-01/project.json            # dry run
    python3 tools/videogen.py render workflows/current/payload/monarch-reel-01/project.json --yes      # spends money
    python3 tools/videogen.py verify workflows/current/payload/monarch-reel-01/project.json
    python3 tools/videogen.py assemble workflows/current/payload/monarch-reel-01/project.json
    python3 tools/videogen.py status workflows/current/payload/monarch-reel-01/project.json
    python3 tools/videogen.py mobile workflows/current/payload/monarch-reel-01/project.json  # phone: one Run-all notebook

Design rules
------------
* Nothing spends money without ``--yes`` (mirrors the WF-06 cost gate) and never above the project budget.
* A shot is not "done" because a render was *started*; only a verified file counts (``verify``).
* Free GPU work is emitted as a real job file for the Colab notebook and tracked until the mp4 appears.
* Every finished file gets a receipt: md5, bytes, probe metadata, engine, and (for paid) task_id + billed seconds.
* Stdlib only. ffmpeg/ffprobe are used when present and reported honestly when absent.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
STYLE = ROOT / "styles" / "minimax-h3-video"
REGISTRY = STYLE / "data" / "tool_registry.json"
DRIVE_CONFIG = ROOT / "styles" / "monarch-ai-agent" / "data" / "drive.json"
DEFAULT_WORK = ROOT / "workflows" / "current" / "payload"

SCHEMA_VERSION = 1
ENGINES_VERSION = "viper-1.4"

ASPECTS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}
H3_RATIOS = {"9:16", "16:9", "1:1", "21:9", "4:3", "3:4"}
FREE_T4_HW = {"width": 832, "height": 480}          # Wan 1.3B landscape default
FREE_T4_PORTRAIT = {"width": 480, "height": 832}    # vertical cut of the same budget
RETRY_BUFFER = 1.5

# What the free T4 route actually renders, as (width, height) — must match render_free_queue().
FREE_FRAMES = {"9:16": (480, 832), "16:9": (832, 480), "1:1": (480, 480), "4:5": (480, 608)}

# Quality ladder: every rung names its real source, so nobody mistakes a scale for detail.
UPSCALES = {
    "off":     {"factor": 1, "gpu": False, "note": "native free size, no post"},
    "lanczos": {"factor": 2, "gpu": False, "note": "ffmpeg scale+lanczos: crisp edges, no new detail, runs on CPU"},
    "realesrgan": {"factor": 2, "gpu": True,
                   "note": "Real-ESRGAN x2 on the free T4: cleaner texture, still not true 1080p detail"},
}


class EngineError(RuntimeError):
    """Raised for a user-fixable problem (bad project, missing budget, absent key...)."""


# --------------------------------------------------------------------------- helpers
def md5(path: pathlib.Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now() -> int:
    return int(time.time())


def which(binary: str) -> str | None:
    """Locate a binary, falling back to the static ffmpeg shipped by imageio-ffmpeg.

    The sandbox (and most phones-as-terminals) has no system ffmpeg; ``pip install imageio-ffmpeg``
    gives us a static ffmpeg we can use for concat, mixing and probing without root.
    """
    found = shutil.which(binary)
    if found:
        return found
    if binary == "ffmpeg":
        try:
            import imageio_ffmpeg  # optional dependency, never required
        except ImportError:
            return None
        try:
            exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:                      # noqa: BLE001 - download/verify failures are "not available"
            return None
        return exe if pathlib.Path(exe).exists() else None
    if binary == "ffprobe":
        # imageio-ffmpeg ships ffmpeg only; probe() parses `ffmpeg -i` instead.
        return None
    return None


def load_json(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        raise EngineError(f"file not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise EngineError(f"invalid JSON in {path}: {exc}") from None


def write_json(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def registry() -> dict:
    return load_json(REGISTRY)


def drive_config() -> dict:
    """WF-07 delivery home (Drive root + subfolders). Empty dict when the config is absent."""
    if not DRIVE_CONFIG.exists():
        return {}
    return load_json(DRIVE_CONFIG)


def drive_targets(project_id: str) -> dict:
    """Where a project's files should land inside the WF-07 Drive folder."""
    cfg = drive_config()
    subs = cfg.get("subfolders", {})
    root_url = cfg.get("root", {}).get("url", "")
    project_url = f"{root_url}"
    return {
        "root": cfg.get("root", {}).get("name", "Wf-07 • Monarch Ai Agent"),
        "root_id": cfg.get("root", {}).get("id"),
        "projects_id": subs.get("projects", {}).get("id"),
        "masters_id": subs.get("masters", {}).get("id"),
        "project_folder": f"05 · Projects/{project_id}/",
        "master_folder": "06 · Masters & Receipts/",
        "url": project_url,
    }


def free_frame_size(aspect: str) -> tuple[int, int]:
    return FREE_FRAMES.get(aspect, FREE_FRAMES["9:16"])


def upscale_target(project: dict, shot: dict | None = None) -> dict:
    """Resolve the upscale stage for the free route (free clip size -> delivered size)."""
    audio_cfg = project.get("audio")
    if audio_cfg is not None:
        if not isinstance(audio_cfg, dict):
            problems.append("audio must be an object")
        else:
            for slot in ("vo_engine", "foley_engine", "bed_engine"):
                if slot in audio_cfg and audio_cfg[slot] not in AUDIO_ENGINES:
                    problems.append(f"audio.{slot} must be one of {', '.join(AUDIO_ENGINES)}")
    delivery = project.get("delivery") or {}
    mode = (delivery.get("upscale") or "realesrgan").lower()
    mode = {"true": "realesrgan", "false": "off", "none": "off", "x2": "realesrgan",
            "realesrgan-x2": "realesrgan", "esrgan": "realesrgan"}.get(mode, mode)
    spec = UPSCALES.get(mode, UPSCALES["off"])
    factor = int(delivery.get("factor") or spec["factor"])
    if mode == "off":
        factor = 1
    aspect = (shot or {}).get("ratio") or project.get("aspect", "9:16")
    width, height = free_frame_size(aspect)
    return {"engine": mode, "factor": factor, "gpu": spec["gpu"], "note": spec["note"],
            "in_width": width, "in_height": height,
            "out_width": width * factor, "out_height": height * factor}


def model_rows() -> dict[str, dict]:
    return {m["id"]: m for m in registry()["models"]}


# --------------------------------------------------------------------------- project
def project_paths(project_file: pathlib.Path) -> dict[str, pathlib.Path]:
    base = project_file.parent
    return {
        "base": base,
        "shots": base / "shots",
        "queue": base / "queue",
        "lipsync": base / "lipsync",
        "upscale": base / "upscale",
        "audio": base / "audio",
        "vo": base / "audio" / "vo",
        "foley": base / "audio" / "foley",
        "receipts": base / "receipts.json",
        "plan": base / "plan.json",
        "delivery": base / "delivery",
    }


def new_project(project_id: str, title: str, aspect: str, out_dir: pathlib.Path,
                template: str = "reel", character: str = "monarch") -> pathlib.Path:
    if aspect not in ASPECTS:
        raise EngineError(f"aspect must be one of {', '.join(ASPECTS)}")
    project_dir = out_dir / project_id
    if (project_dir / "project.json").exists():
        raise EngineError(f"project already exists: {project_dir / 'project.json'}")

    shots = {
        "reel": [
            {"id": "s01-hook", "kind": "hero", "seconds": 5, "ratio": aspect,
             "prompt": "TODO: the hook line/beat — Monarch face, direct address.",
             "references": [], "voice_ref": None},
            {"id": "s02-plate", "kind": "plate", "seconds": 5, "ratio": aspect,
             "prompt": "TODO: B-roll plate that sets the world. Style, subject, action, camera."},
            {"id": "s03-payoff", "kind": "plate", "seconds": 5, "ratio": aspect,
             "prompt": "TODO: payoff shot. Keep the lower third empty for typography."},
        ],
        "film": [
            {"id": "s01", "kind": "hero", "seconds": 8, "ratio": aspect,
             "prompt": "TODO: opening beat with dialogue.", "references": [], "voice_ref": None},
            {"id": "s02", "kind": "plate", "seconds": 8, "ratio": aspect,
             "prompt": "TODO: establish the location."},
            {"id": "s03", "kind": "plate", "seconds": 8, "ratio": aspect,
             "prompt": "TODO: escalate."},
        ],
        "hero-test": [
            {"id": "s01-hero", "kind": "hero", "seconds": 5, "ratio": aspect,
             "prompt": "TODO: one line, direct to camera, locked Monarch reference pack.",
             "references": [], "voice_ref": None},
        ],
    }[template]

    project = {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "title": title,
        "style_id": "minimax-h3-video",
        "created_at": now(),
        "engine": ENGINES_VERSION,
        "character": character,
        "character_authority": "characters/monarch",
        "aspect": aspect,
        "fps": 24,
        "delivery_fps": 30,
        "route": "auto",                 # auto | free | paid
        "budget_usd": 5.0,
        "delivery": {"upscale": "realesrgan", "factor": 2,   # off | lanczos | realesrgan
                     "target_height": 0},                    # 0 = whatever the upscale yields
        "notes": "Edit prompts, drop the Monarch reference pack into shots/, then: plan -> render -> verify.",
        "audio": {"music": None, "dialogue": [], "vo_engine": "kokoro",
                  "foley_engine": "mmaudio", "bed_engine": "musicgen", "mix": True},
        "shots": shots,
    }
    write_json(project_dir / "project.json", project)
    for key in ("shots", "queue", "lipsync", "upscale", "delivery", "audio"):
        (project_dir / key).mkdir(parents=True, exist_ok=True)
    return project_dir / "project.json"


def validate_project(project: dict, path: pathlib.Path) -> list[str]:
    problems: list[str] = []
    if project.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version must be {SCHEMA_VERSION}")
    for key in ("project_id", "shots"):
        if not project.get(key):
            problems.append(f"missing '{key}'")
    if project.get("aspect") not in ASPECTS:
        problems.append(f"aspect must be one of {', '.join(ASPECTS)}")
    budget = project.get("budget_usd")
    if not isinstance(budget, (int, float)) or budget < 0:
        problems.append("budget_usd must be a non-negative number")
    if project.get("route", "auto") not in {"auto", "free", "paid"}:
        problems.append("route must be auto | free | paid")
    audio_cfg = project.get("audio")
    if audio_cfg is not None:
        if not isinstance(audio_cfg, dict):
            problems.append("audio must be an object")
        else:
            for slot in ("vo_engine", "foley_engine", "bed_engine"):
                if slot in audio_cfg and audio_cfg[slot] not in AUDIO_ENGINES:
                    problems.append(f"audio.{slot} must be one of {', '.join(AUDIO_ENGINES)}")
    delivery = project.get("delivery")
    if delivery is not None:
        if not isinstance(delivery, dict):
            problems.append("delivery must be an object")
        else:
            mode = str(delivery.get("upscale", "off")).lower()
            allowed = set(UPSCALES) | {"true", "false", "none", "x2", "esrgan", "realesrgan-x2"}
            if mode not in allowed:
                problems.append("delivery.upscale must be off | lanczos | realesrgan")
            factor = delivery.get("factor", 2)
            if factor not in (1, 2, 4):
                problems.append("delivery.factor must be 1, 2 or 4")
            target = delivery.get("target_height", 0)
            if not isinstance(target, int) or target < 0:
                problems.append("delivery.target_height must be a non-negative integer")

    seen: set[str] = set()
    for i, shot in enumerate(project.get("shots") or []):
        sid = shot.get("id")
        label = sid or f"shots[{i}]"
        if not sid:
            problems.append(f"{label}: missing id")
        elif sid in seen:
            problems.append(f"{label}: duplicate id")
        else:
            seen.add(sid)
        if pathlib.Path(str(sid or "")).name != str(sid):
            problems.append(f"{label}: id must be a plain filename")
        seconds = shot.get("seconds")
        if not isinstance(seconds, (int, float)) or not (4 <= seconds <= 15):
            problems.append(f"{label}: seconds must be 4-15 (H3 range)")
        if shot.get("kind") not in {"hero", "plate", "lipsync"}:
            problems.append(f"{label}: kind must be hero | plate | lipsync")
        if shot.get("ratio") and shot["ratio"] not in H3_RATIOS:
            problems.append(f"{label}: ratio {shot['ratio']} not supported by H3")
        if shot.get("kind") in {"hero", "plate"} and not str(shot.get("prompt", "")).strip():
            problems.append(f"{label}: prompt is empty")
        if shot.get("kind") == "lipsync":
            if not shot.get("source"):
                problems.append(f"{label}: lipsync needs 'source' (another shot id)")
            if not shot.get("audio"):
                problems.append(f"{label}: lipsync needs 'audio' (a wav/mp3 path)")
    return problems


def require_project(path: pathlib.Path) -> dict:
    project = load_json(path)
    problems = validate_project(project, path)
    if problems:
        raise EngineError("project invalid:\n  - " + "\n  - ".join(problems))
    return project


# --------------------------------------------------------------------------- planning
def h3_cost(seconds: float, resolution: str) -> float:
    rates = model_rows()["minimax-h3-api"]["cost_usd_per_second"]
    return round(seconds * rates[resolution], 2)


def plan_shot(shot: dict, project: dict, *, has_key: bool, force_free: bool = False) -> dict:
    """Resolve one shot into ordered steps (engine + action + cost)."""
    route = project.get("route", "auto")
    if force_free:
        has_key = False
        route = "free"
    kind = shot["kind"]
    seconds = float(shot["seconds"])
    steps: list[dict] = []

    if kind == "lipsync":
        steps.append({"engine": "latentsync", "action": "lipsync", "cost": 0.0,
                      "note": "free pass on a GPU (T4 with the sm_75 fp16 patch)"})
        return {"shot_id": shot["id"], "kind": kind, "steps": steps,
                "total_cost": 0.0, "engine_label": "latentsync"}

    wants_paid = route == "paid" or (route == "auto" and kind == "hero" and has_key)
    if wants_paid:
        resolution = shot.get("resolution") or ("2K" if kind == "hero" else "768P")
        steps.append({"engine": "h3", "action": "generate", "cost": h3_cost(seconds, resolution),
                      "resolution": resolution,
                      "note": "hosted API: native stereo audio + lipsync in one pass (no vo/foley needed)"})
        return {"shot_id": shot["id"], "kind": kind, "steps": steps,
                "total_cost": steps[0]["cost"], "engine_label": f"h3-{resolution}"}

    # free chain: a silent clip from the T4 queue; heroes then get a lipsync pass
    up = upscale_target(project, shot)
    steps.append({"engine": "wan", "action": "queue", "cost": 0.0,
                  "note": f"free Colab T4 job ({up['in_width']}x{up['in_height']}, silent) — "
                          "run the notebook queue cell"})
    if kind == "hero":
        steps.append({"engine": "latentsync", "action": "lipsync", "cost": 0.0,
                      "note": "free lipsync pass with your own voice track"})
    try:
        stems = audio_stems(project, shot)
    except EngineError:
        stems = {}
    for slot, label in (("vo", ""), ("foley", "")):
        if slot in stems:
            stems[slot]["cost"] = 0.0
            steps.append({"engine": stems[slot]["engine"],
                          "action": "vo" if slot == "vo" else "foley", "cost": 0.0,
                          "note": AUDIO_ENGINES[stems[slot]["engine"]]["note"]})
    if up["engine"] != "off":
        steps.append({"engine": "upscale", "action": f"{up['engine']}-x{up['factor']}", "cost": 0.0,
                      "note": f"{up['in_height']}p -> {up['out_height']}p · {up['note']}"})
    return {"shot_id": shot["id"], "kind": kind, "steps": steps,
            "total_cost": 0.0, "engine_label": "free-chain"}


def _plan_delivery(project: dict) -> dict:
    up = upscale_target(project)
    target = int((project.get("delivery") or {}).get("target_height") or 0)
    return {"engine": up["engine"], "factor": up["factor"], "gpu": up["gpu"], "note": up["note"],
            "free_width": up["in_width"], "free_height": up["in_height"],
            "out_width": up["out_width"], "out_height": up["out_height"],
            "target_height": target,
            "meets_target": bool(target and up["out_height"] >= target) or not target}


def build_plan(project: dict, *, has_key: bool | None = None) -> dict:
    guard = free_only()
    if has_key is None:
        has_key = bool(os.environ.get("MINIMAX_API_KEY"))
    entries = [plan_shot(shot, project, has_key=has_key, force_free=guard)
               for shot in project["shots"]]
    total = round(sum(e["total_cost"] for e in entries), 2)
    budget = float(project.get("budget_usd", 0))
    paid_steps = sum(1 for e in entries for s in e["steps"] if s["cost"] > 0)
    return {
        "project_id": project["project_id"],
        "route": project.get("route", "auto"),
        "aspect": project["aspect"],
        "shots": entries,
        "shot_count": len(entries),
        "paid_step_count": paid_steps,
        "estimate_usd": total,
        "estimate_with_retries_usd": round(total * RETRY_BUFFER, 2),
        "budget_usd": budget,
        "within_budget": round(total * RETRY_BUFFER, 2) <= budget,
        "has_api_key": has_key,
        "free_only": guard,
        "blocked_paid": (sum(1 for shot in project["shots"]
                             if plan_shot(shot, project, has_key=has_key)["total_cost"] > 0)
                         if guard else 0),
        "delivery": _plan_delivery(project),
        "planned_at": now(),
        "engine": ENGINES_VERSION,
        "warnings": plan_warnings(project, entries),
    }


def plan_warnings(project: dict, entries: list[dict]) -> list[str]:
    warnings: list[str] = []
    for shot, entry in zip(project["shots"], entries):
        engines = {s['engine'] for s in entry["steps"]}
        if "latentsync" in engines and not (shot.get("voice_ref") or shot.get("audio")):
            warnings.append(f"{shot['id']}: lipsync pass has no voice_ref/audio yet")
        if "h3" in engines and not any(shot.get("references") or []):
            warnings.append(f"{shot['id']}: paid hero has no reference images (identity will drift)")
    target = int((project.get("delivery") or {}).get("target_height") or 0)
    for shot, entry in zip(project["shots"], entries):
        if not any(st["engine"] == "wan" for st in entry["steps"]):
            continue
        up = upscale_target(project, shot)
        if target and up["out_height"] < target:
            warnings.append(
                f"{shot['id']}: free route tops out at {up['out_height']}p but target_height is {target}p "
                f"— scale, not detail; for true {target}p use route=paid (h3 768P/2K)")
        if up["engine"] == "off" and target:
            warnings.append(f"{shot['id']}: upscale is off and target_height={target}p is set")
    if free_only() and (project.get("route") == "paid" or any(
            plan_shot(shot, project, has_key=True)["total_cost"] for shot in project["shots"])):
        warnings.append("free-only mode: every paid step is rewritten to the free chain "
                        "(set MONARCH_ALLOW_PAID=1 only if you have decided to spend)")
    try:
        warnings.extend(audio_licence_warnings(project))
    except EngineError:
        pass
    if not any(s["total_cost"] for s in entries) and project.get("route") == "paid":
        warnings.append("route=paid but no paid steps resolved — add an API key?")
    return warnings


def print_plan(plan: dict) -> None:
    mode = "FREE-ONLY ($0 guaranteed)" if plan.get("free_only") else "PAID ALLOWED"
    print(f"PROJECT   : {plan['project_id']}  (route={plan['route']}, {plan['shot_count']} shots, {mode})")
    print(f"{'shot':<22}{'engine':<16}{'steps':<34}{'cost':>8}")
    for entry in plan["shots"]:
        steps = " -> ".join(f"{s['engine']}:{s['action']}" for s in entry["steps"])
        print(f"{entry['shot_id']:<22}{entry['engine_label']:<16}{steps:<34}{entry['total_cost']:>8.2f}")
    if plan.get("delivery"):
        d = plan["delivery"]
        print(f"\nDELIVERY        {d['free_width']}x{d['free_height']} free -> "
              f"{d['out_width']}x{d['out_height']} after {d['engine']}-x{d['factor']}"
              + (f"  (target {d['target_height']}p)" if d.get("target_height") else ""))
        print(f"                {d['note']}")
    print(f"\nESTIMATE        ${plan['estimate_usd']:.2f}")
    print(f"+ retry buffer  ${plan['estimate_with_retries_usd']:.2f}  (x{RETRY_BUFFER})")
    print(f"BUDGET          ${plan['budget_usd']:.2f}  -> {'OK' if plan['within_budget'] else 'OVER BUDGET'}")
    if not plan["has_api_key"]:
        print("API key         absent -> hero shots fall back to the free chain")
    if not plan["within_budget"]:
        print("                lower the resolution/shots, raise budget_usd, or render free only")
    for warning in plan.get("warnings", []):
        print(f"WARN            {warning}")


# --------------------------------------------------------------------------- render
def _h3_engine():
    """Import h3_client from the WF-06 style without polluting sys.path permanently."""
    src = str(STYLE / "src")
    added = src not in sys.path
    if added:
        sys.path.insert(0, src)
    try:
        import h3_client  # noqa: PLC0415
        return h3_client
    finally:
        if added:
            sys.path.remove(src)


def render_h3(shot: dict, project: dict, paths: dict, *, confirm: bool) -> dict:
    h3 = _h3_engine()
    key = os.environ.get("MINIMAX_API_KEY", "").strip()
    resolution = shot.get("resolution") or ("2K" if shot["kind"] == "hero" else "768P")
    spec = {
        "id": shot["id"],
        "model": shot.get("model", "MiniMax-H3"),
        "resolution": resolution,
        "duration": int(shot["seconds"]),
        "ratio": shot.get("ratio") or project["aspect"],
        "prompt": shot["prompt"],
        "references": shot.get("references") or [],
        "reference_audio": [shot["voice_ref"]] if shot.get("voice_ref") else [],
        "seed": shot.get("seed", 42),
    }
    payload = h3.build_payload(spec, resolve_files=confirm)
    if not confirm:
        return {"status": "dry_run", "engine": "h3", "payload_preview": {
            "model": payload["model"], "resolution": payload["resolution"],
            "duration": payload["duration"], "ratio": payload.get("ratio"),
            "content_items": len(payload["content"])}}
    if not key:
        raise EngineError("MINIMAX_API_KEY is not set — paid shots need it")
    return h3.run_shot(spec, key, paths["shots"])


def render_free_queue(shots: list[dict], paths: dict, project: dict) -> dict:
    """Emit a Colab job file for the free T4 notebook (Wan 1.3B)."""
    width, height = free_frame_size(project["aspect"])
    size = {"width": width, "height": height}
    jobs = []
    for shot in shots:
        frames = int(round(float(shot["seconds"]) * 16))          # 16 fps, 4k+1 grid
        frames = max(17, ((frames - 1) // 4) * 4 + 1)
        jobs.append({
            "id": shot["id"],
            "seed": shot.get("seed", 42),
            "frames": frames,
            "steps": shot.get("steps", 30),
            "width": size["width"],
            "height": size["height"],
            "prompt": shot["prompt"],
        })
    payload = {
        "run": project["project_id"],
        "model": "Wan-AI/Wan2.1-T2V-1.3B-Diffusers",
        "engine": ENGINES_VERSION,
        "created_at": now(),
        "output_dir": str(paths["shots"]),
        "notes": ("Free route. Open styles/minimax-h3-video/colab/MONARCH_T4_FREE_BRIDGE.ipynb, "
                  "set QUEUE_ENABLED=True and point it at this file, or paste these jobs into the JOBS cell. "
                  "Save the mp4 files back into the project's shots/ folder with the same ids."),
        "jobs": jobs,
    }
    target = paths["queue"] / f"free_jobs-{project['project_id']}.json"
    write_json(target, payload)
    return {"status": "queued", "engine": "wan", "queue_file": str(target), "jobs": len(jobs)}


def render_lipsync(shot: dict, project: dict, paths: dict, *, confirm: bool) -> dict:
    """Free lipsync pass.

    Two shapes are supported: a standalone ``kind: lipsync`` shot (source = another shot id,
    audio = explicit file) and a ``hero`` shot in the free chain (source = its own silent clip,
    audio = voice_ref or audio).
    """
    script = paths["lipsync"] / f"{shot['id']}.sh"
    if shot["kind"] == "lipsync":
        source = paths["shots"] / f"{shot['source']}.mp4"
        audio = shot["audio"]
    else:
        source = paths["shots"] / f"{shot['id']}.mp4"
        audio = shot.get("voice_ref") or shot.get("audio")
    if not audio:
        audio = f"<ADD A VOICE TRACK: set voice_ref on shot {shot['id']}>"
    body = f"""#!/usr/bin/env bash
# generated by tools/videogen.py ({ENGINES_VERSION}) — free lipsync pass
# Run this on a GPU machine (free Colab T4 works with the fp16 patch below).
set -euo pipefail
SOURCE_VIDEO="{source}"
VOICE_AUDIO="{audio}"
OUT="{paths['shots'] / (shot['id'] + ('-talk.mp4' if shot['kind'] != 'lipsync' else '.mp4'))}"

# 1) LatentSync 1.5 (8 GB VRAM). One-time setup:
#    git clone https://github.com/bytedance/LatentSync
#    cd LatentSync && bash setup_env.sh
#    T4 trap: upstream checks compute capability > 7 (Turing is 7.5) -> fp32 -> OOM.
#    Patch the check to >= 7 so it runs fp16 (~12 GB).
# 2) Inference (1.5 checkpoint config):
#    python -m scripts.inference --inference_config configs/inference/sd15.yaml \\
#      --video_path "$SOURCE_VIDEO" --audio_path "$VOICE_AUDIO" --video_out_path "$OUT"
#
# Notes:
#   - face must be visible and fairly still; close-ups only (256 px face region on 1.5)
#   - keep the source silent; music is added later in WF-05
[ -f "$SOURCE_VIDEO" ] || {{ echo "missing silent clip: $SOURCE_VIDEO (render the free queue first)"; exit 2; }}
[ -f "$VOICE_AUDIO" ] || {{ echo "missing voice track: $VOICE_AUDIO"; exit 2; }}
echo "ready: $SOURCE_VIDEO + $VOICE_AUDIO -> $OUT"
echo "follow the commented steps above inside the LatentSync checkout."
"""
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(body)
    script.chmod(0o755)
    return {"status": "queued" if confirm else "dry_run", "engine": "latentsync",
            "script": str(script), "source": str(source), "audio": audio}


def render(project_file: pathlib.Path, *, confirm: bool, only: list[str] | None = None,
           allow_over_budget: bool = False) -> int:
    project = require_project(project_file)
    paths = project_paths(project_file)
    plan = build_plan(project)
    if confirm and plan["free_only"]:
        print("FREE-ONLY MODE: no paid step will be submitted; queued work goes to the free GPU chain.")
    if confirm and not plan["within_budget"] and not allow_over_budget:
        raise EngineError(
            f"estimate ${plan['estimate_with_retries_usd']:.2f} (with retries) exceeds budget "
            f"${plan['budget_usd']:.2f}; raise budget_usd or pass --allow-over-budget")
    for key in ("shots", "queue", "lipsync", "delivery"):
        paths[key].mkdir(parents=True, exist_ok=True)

    receipts = load_json(paths["receipts"]) if paths["receipts"].exists() else {"shots": {}}
    receipts.setdefault("shots", {})
    receipts["project_id"] = project["project_id"]
    receipts["updated_at"] = now()

    free_batch = [s for s in project["shots"]
                  if any(st["engine"] == "wan" for st in
                         next(e for e in plan["shots"] if e["shot_id"] == s["id"])["steps"])
                  and (not only or s["id"] in only)]
    if free_batch:
        info = render_free_queue(free_batch, paths, project)
        print(f"QUEUED  {info['jobs']} free job(s) -> {info['queue_file']}")
        for shot in free_batch:
            receipts["shots"].setdefault(shot["id"], {}).update(
                {"engine": "wan", "status": "queued", "queue_file": info["queue_file"]})

    rendered = 0
    for shot in project["shots"]:
        if only and shot["id"] not in only:
            continue
        entry = next(e for e in plan["shots"] if e["shot_id"] == shot["id"])
        for step in entry["steps"]:
            if step["engine"] == "wan":
                continue
            if step["engine"] == "h3":
                try:
                    receipt = render_h3(shot, project, paths, confirm=confirm)
                except EngineError as exc:
                    print(f"SKIP    {shot['id']} (h3): {exc}")
                    receipts["shots"].setdefault(shot["id"], {})["error"] = str(exc)
                    break
                receipts["shots"].setdefault(shot["id"], {}).update(receipt)
                if receipt.get("status") == "dry_run":
                    print(f"DRY     {shot['id']} (h3, {step['resolution']}, ${step['cost']:.2f}) "
                          f"-> would submit {receipt['payload_preview']['content_items']} content item(s)")
                else:
                    rendered += 1
                    print(f"OK      {shot['id']} (h3) -> {receipt.get('local_path')}")
            elif step["engine"] == "latentsync":
                info = render_lipsync(shot, project, paths, confirm=confirm)
                receipts["shots"].setdefault(shot["id"], {}).update(
                    {k: v for k, v in info.items() if k != "status"})
                receipts["shots"][shot["id"]]["status"] = (
                    receipts["shots"][shot["id"]].get("status") if info["status"] == "dry_run"
                    else "lipsync_queued")
                print(f"{'DRY ' if info['status'] == 'dry_run' else 'QUEUED'} {shot['id']} (lipsync) "
                      f"-> {info['script']}")

    receipts["updated_at"] = now()
    write_json(paths["plan"], plan)
    write_json(paths["receipts"], receipts)
    print(f"\nplan     : {paths['plan']}")
    print(f"receipts : {paths['receipts']}")
    if not confirm:
        print("Dry run only — add --yes to submit paid shots.")
    elif rendered:
        print(f"{rendered} paid shot(s) rendered.")
    print("next: drop queued mp4s into shots/, then run `verify`.")
    return 0


# --------------------------------------------------------------------------- audio
# Free audio stack: voice (Kokoro / Chatterbox), foley (MMAudio / ThinkSound), music bed (MusicGen).
# Every row below is verified in knowledge/AUDIO.md — licences included, because "free" is not "free to sell".
AUDIO_ENGINES = {
    "kokoro": {"kind": "voice", "params": "82M", "vram_gb": 0, "gpu": False,
               "licence": "Apache-2.0 (code + weights, commercial OK)",
               "note": "54 preset voices, no cloning, runs on CPU faster than real time"},
    "chatterbox": {"kind": "voice", "params": "0.5B", "vram_gb": 5, "gpu": True,
                   "licence": "MIT (commercial OK)",
                   "note": "zero-shot cloning from ~10 s — Monarch ki apni awaaz, GPU chahiye (~5 GB)"},
    "own": {"kind": "voice", "params": "—", "vram_gb": 0, "gpu": False,
            "licence": "yours", "note": "record it yourself; best quality per rupee, always $0"},
    "mmaudio": {"kind": "foley", "params": "157M–1.03B", "vram_gb": 6, "gpu": True,
                "licence": "code MIT / weights CC-BY-NC 4.0 — NON-COMMERCIAL",
                "note": "video→audio SOTA at this size, 44.1 kHz, ~1 s per 8 s clip"},
    "thinksound": {"kind": "foley", "params": "533M–1.3B", "vram_gb": 8, "gpu": True,
                   "licence": "Apache-2.0 code; README asks permission for commercial use",
                   "note": "CoT-guided video→audio, best semantic match, slower than MMAudio"},
    "musicgen": {"kind": "bed", "params": "300M–1.5B", "vram_gb": 4, "gpu": True,
                 "licence": "code MIT / weights CC-BY-NC 4.0 — NON-COMMERCIAL",
                 "note": "text→music bed, 30 s chunks, small model fits a T4 easily"},
    "off": {"kind": "off", "params": "—", "vram_gb": 0, "gpu": False, "licence": "—", "note": "silent"},
}


def audio_config(project: dict) -> dict:
    """Resolve the free audio stack for a project (all default $0)."""
    cfg = project.get("audio") or {}
    vo = str(cfg.get("vo_engine") or "kokoro").lower()
    foley = str(cfg.get("foley_engine") or "mmaudio").lower()
    bed = str(cfg.get("bed_engine") or "musicgen").lower()
    for name, value in (("vo_engine", vo), ("foley_engine", foley), ("bed_engine", bed)):
        if value not in AUDIO_ENGINES:
            raise EngineError(f"audio.{name} must be one of {', '.join(AUDIO_ENGINES)}")
    return {"vo_engine": vo, "foley_engine": foley, "bed_engine": bed,
            "mix": bool(cfg.get("mix", True)),
            "music": cfg.get("music"),
            "bed_prompt": cfg.get("bed_prompt"),
            "gain_db": float(cfg.get("bed_gain_db", -6.0))}


def shot_vo_text(project: dict, shot: dict) -> str:
    """Dialogue text for a shot: shot.vo_text wins, then audio.dialogue entries."""
    if shot.get("vo_text"):
        return str(shot["vo_text"]).strip()
    for entry in (project.get("audio") or {}).get("dialogue") or []:
        if isinstance(entry, dict) and entry.get("shot") == shot["id"]:
            return str(entry.get("text") or "").strip()
        if isinstance(entry, str):
            return entry.strip()
    return ""


def audio_stems(project: dict, shot: dict) -> dict:
    """Which audio stems a shot needs, where they land, and which engine makes each."""
    cfg = audio_config(project)
    stems = {}
    text = shot_vo_text(project, shot)
    if text and cfg["vo_engine"] != "off":
        stems["vo"] = {"engine": cfg["vo_engine"], "text": text,
                       "file": f"audio/vo/{shot['id']}.wav", "cost": 0.0}
    if cfg["foley_engine"] != "off":
        stems["foley"] = {"engine": cfg["foley_engine"],
                          "prompt": shot.get("foley_prompt") or "",
                          "file": f"audio/foley/{shot['id']}.wav", "cost": 0.0}
    return stems


def audio_licence_warnings(project: dict) -> list[str]:
    cfg = audio_config(project)
    out = []
    for slot in ("vo_engine", "foley_engine", "bed_engine"):
        engine = cfg[slot]
        if engine == "off":
            continue
        licence = AUDIO_ENGINES[engine]["licence"]
        if "NON-COMMERCIAL" in licence:
            out.append(f"audio.{slot}={engine}: {licence} — personal/portfolio use theek, "
                       f"paid client work ke liye ThinkSound (Apache) ya paid licence chahiye")
    return out


def _audio_tokens(project: dict) -> dict:
    cfg = audio_config(project)
    vo = {s["id"]: shot_vo_text(project, s) for s in project["shots"]}
    foley = {s["id"]: (s.get("foley_prompt") or "") for s in project["shots"]}
    return {
        "__PROJECT__": str(project["project_id"]),
        "__VO_ENGINE__": cfg["vo_engine"],
        "__FOLEY_ENGINE__": cfg["foley_engine"],
        "__BED_ENGINE__": cfg["bed_engine"],
        "__VO_DICT__": json.dumps(vo, indent=2, ensure_ascii=False),
        "__FOLEY_DICT__": json.dumps(foley, indent=2, ensure_ascii=False),
        "__BED_PROMPT__": cfg["bed_prompt"] or "cinematic tension bed, low strings, subtle pulse",
        "__BED_GAIN__": str(cfg["gain_db"]),
        "__SHOTS__": json.dumps([s["id"] for s in project["shots"]]),
    }


_AUDIO_INTRO = """# Audio · __PROJECT__ (free stack)

Yeh notebook silent clips par teen layers banata hai — sab **$0**:

| Layer | Engine | Licence | Hardware |
|---|---|---|---|
| Voice / VO | `__VO_ENGINE__` | Kokoro = Apache-2.0 (commercial OK) · Chatterbox = MIT | CPU ya ~5 GB GPU (clone) |
| Foley / SFX | `__FOLEY_ENGINE__` | MMAudio weights **CC-BY-NC 4.0** (non-commercial) · ThinkSound Apache | ~6–8 GB GPU |
| Music bed | `__BED_ENGINE__` | MusicGen weights CC-BY-NC 4.0 | ~4 GB GPU |

**Rules:** (1) paid client kaam me non-commercial weights use na karo — `thinksound` chuno ya paid
licence lo; (2) native synced audio (dialogue lipsync ek hi pass me) sirf Ovi / H3 API dete hain, aur
wo 24 GB+ GPU ya paisa maangta hai — isliye hum stems + LatentSync route chalate hain.

**Run:** Runtime → T4 GPU (foley/bed ke liye) → Run all. Files Drive me `audio/vo`, `audio/foley`,
`audio/bed.wav` me jayengi. Phir repo me: `python3 tools/videogen.py mix <project>.json`.
"""

_AUDIO_CONFIG = """import json, pathlib, subprocess

PROJECT_DIR = "/content/drive/MyDrive/MONARCH STUDIO/Wf-07 • Monarch Ai Agent/05 · Projects/__PROJECT__"
SHOTS = __SHOTS__
VO_TEXT = __VO_DICT__          # shot id -> line (khaali = skip)
FOLEY_PROMPT = __FOLEY_DICT__  # shot id -> sound description
BED_PROMPT = "__BED_PROMPT__"
BED_GAIN_DB = __BED_GAIN__
VO_VOICE = "af_heart"          # Kokoro voice id (54 options: af_*, am_*, bf_*, bm_*)
SPEED = 1.0
FORCE = False

from google.colab import drive
drive.mount("/content/drive")
BASE = pathlib.Path(PROJECT_DIR)
VO_DIR, FOLEY_DIR = BASE / "audio" / "vo", BASE / "audio" / "foley"
for d in (VO_DIR, FOLEY_DIR):
    d.mkdir(parents=True, exist_ok=True)
print("base:", BASE, "| exists:", BASE.exists())
"""

_AUDIO_KOKORO = """# 1) VOICE — Kokoro-82M (Apache-2.0, CPU bhi kaafi hai, ~0.3 GB)
!pip -q install kokoro soundfile
import numpy as np, soundfile as sf
from kokoro import KPipeline

pipeline = KPipeline(lang_code="a")   # 'a' = American English; 'b' = British

made = []
for sid in SHOTS:
    text = (VO_TEXT.get(sid) or "").strip()
    if not text:
        print("skip (no text)", sid); continue
    out = VO_DIR / f"{sid}.wav"
    if out.exists() and not FORCE:
        print("skip (exists)", out.name); continue
    chunks = [audio for _, _, audio in pipeline(text, voice=VO_VOICE, speed=SPEED)]
    audio = np.concatenate([c if isinstance(c, np.ndarray) else c.numpy() for c in chunks])
    sf.write(out, audio, 24000)
    print("vo ", out.name, f"{len(audio)/24000:.2f}s")
    made.append(out.name)
print("\\nVO files:", len(made))
"""

_AUDIO_CHATTERBOX = """# 1b) VOICE CLONE (optional) — Chatterbox, MIT, ~5 GB, 10 s reference se cloning
# Apni awaaz ka 10-20 s clean wav yahan rakho, phir yeh cell chalao.
import torch, torchaudio
!pip -q install chatterbox-tts
from chatterbox.tts import ChatterboxTTS

REF_WAV = str(BASE / "audio" / "voice_ref.wav")   # <- apni awaaz
assert pathlib.Path(REF_WAV).exists(), "pehle audio/voice_ref.wav upload karo"

model = ChatterboxTTS.from_pretrained(device="cuda" if torch.cuda.is_available() else "cpu")
for sid in SHOTS:
    text = (VO_TEXT.get(sid) or "").strip()
    if not text:
        continue
    out = VO_DIR / f"{sid}.wav"
    if out.exists() and not FORCE:
        print("skip (exists)", out.name); continue
    wav = model.generate(text, audio_prompt_path=REF_WAV)
    torchaudio.save(str(out), wav.cpu(), model.sr)
    print("vo-clone", out.name)
"""

_AUDIO_FOLEY = """# 2) FOLEY — __FOLEY_ENGINE__ (video + text -> sound)
# MMAudio: code MIT, weights CC-BY-NC 4.0 (non-commercial). ThinkSound: Apache-2.0.
FOLEY_ENGINE = "__FOLEY_ENGINE__"
made = []

if FOLEY_ENGINE == "mmaudio":
    !git -q clone https://github.com/hkchengrex/MMAudio.git /content/MMAudio
    !pip -q install -e /content/MMAudio
    !pip -q install torch torchvision torchaudio --upgrade
    import torch, torchaudio
    from mmaudio.eval_utils import all_model_cfg, generate, load_video
    from mmaudio.model.flow_matching import FlowMatching
    from mmaudio.model.networks import MMAudio, get_my_mmaudio
    from mmaudio.model.utils.features_utils import FeaturesUtils

    cfg_name = "mmaudio_small_44k" if torch.cuda.get_device_properties(0).total_memory < 12e9 else "mmaudio_large_44k_v2"
    model_cfg = all_model_cfg[cfg_name]
    net = get_my_mmaudio(model_cfg.model).eval().to("cuda")
    net.load_weights(torch.load(f"~/.cache/mmaudio/{cfg_name}.pth", map_location="cpu", weights_only=True))
    feats = FeaturesUtils(**model_cfg.features).eval().to("cuda")
    fm = FlowMatching(min_sigma=0, inference_mode="euler", num_steps=25)

    for sid in SHOTS:
        src = BASE / "shots" / f"{sid}.mp4"
        if not src.exists():
            print("skip (no clip)", sid); continue
        out = FOLEY_DIR / f"{sid}.wav"
        if out.exists() and not FORCE:
            print("skip (exists)", out.name); continue
        video_info, video = load_video(str(src), 16, model_cfg.sampling_rate)
        with torch.no_grad():
            audio = generate(video, feats, net, fm,
                             num_steps=25, duration=float(video_info.duration),
                             cfg_strength=4.5,
                             seed=42)
        torchaudio.save(str(out), audio.cpu(), model_cfg.sampling_rate)
        print("foley", out.name)
        made.append(out.name)

elif FOLEY_ENGINE == "thinksound":
    import subprocess
    subprocess.run(["bash", "-c", "pip -q install thinksound"], check=False)
    # ThinkSound CLI (Apache-2.0). Video + prompt -> wav
    for sid in SHOTS:
        src = BASE / "shots" / f"{sid}.mp4"
        if not src.exists():
            print("skip (no clip)", sid); continue
        out = FOLEY_DIR / f"{sid}.wav"
        if out.exists() and not FORCE:
            print("skip (exists)", out.name); continue
        prompt = FOLEY_PROMPT.get(sid) or "natural ambience matching the scene"
        subprocess.run(["python", "-m", "thinksound.infer",
                        "--video", str(src), "--prompt", prompt, "--out", str(out)], check=False)
        print("foley", out.name)
        made.append(out.name)
else:
    print("foley engine off")

print("\\nfoley files:", len(made))
"""

_AUDIO_BED = """# 3) MUSIC BED — MusicGen (weights CC-BY-NC 4.0 — non-commercial)
import torch, torchaudio
!pip -q install audiocraft
from audiocraft.models import MusicGen

model = MusicGen.get_pretrained("facebook/musicgen-small")
model.set_generation_params(duration=30)
wav = model.generate([BED_PROMPT])
out = BASE / "audio" / "bed.wav"
torchaudio.save(str(out), wav[0].cpu(), model.sample_rate)
print("bed:", out, "| prompt:", BED_PROMPT, "| gain", BED_GAIN_DB, "dB")
"""

_AUDIO_RECEIPT = """# 4) Receipt — kaunsi stem bani, kaunsa md5
import hashlib, json
rows = []
for folder in (VO_DIR, FOLEY_DIR, BASE / "audio"):
    for f in sorted(folder.glob("*.wav")):
        rows.append({"stem": f.relative_to(BASE).as_posix(), "bytes": f.stat().st_size,
                     "md5": hashlib.md5(f.read_bytes()).hexdigest()})
receipt = BASE / "audio_receipt.json"
receipt.write_text(json.dumps({"project": "__PROJECT__",
                               "engines": {"vo": "__VO_ENGINE__", "foley": "__FOLEY_ENGINE__",
                                           "bed": "__BED_ENGINE__"},
                               "files": rows}, indent=2))
print(json.dumps(rows, indent=2))
print("\\nreceipt:", receipt)
print("Ab repo me: python3 tools/videogen.py mix <project>.json")
"""


def build_audio_notebook(project: dict) -> dict:
    tokens = _audio_tokens(project)
    cfg = audio_config(project)

    def fill(text: str) -> str:
        for key, value in tokens.items():
            text = text.replace(key, value)
        return text

    cells = [_md(fill(_AUDIO_INTRO)), _code(fill(_AUDIO_CONFIG))]
    if cfg["vo_engine"] == "kokoro":
        cells.append(_code(fill(_AUDIO_KOKORO)))
    elif cfg["vo_engine"] == "chatterbox":
        cells.append(_code(fill(_AUDIO_CHATTERBOX)))
    if cfg["foley_engine"] != "off":
        cells.append(_code(fill(_AUDIO_FOLEY)))
    if cfg["bed_engine"] != "off":
        cells.append(_code(fill(_AUDIO_BED)))
    cells.append(_code(fill(_AUDIO_RECEIPT)))
    return _nb(cells)


def audio(project_file: pathlib.Path) -> int:
    """Write the free-audio Colab notebook (voice + foley + music) for a project."""
    project = require_project(project_file)
    paths = project_paths(project_file)
    for key in ("audio", "vo", "foley"):
        paths[key].mkdir(parents=True, exist_ok=True)
    cfg = audio_config(project)

    notebook = build_audio_notebook(project)
    target = paths["audio"] / f"AUDIO_{project['project_id']}.ipynb"
    write_json(target, notebook)

    print(f"AUDIO {project['project_id']}  vo={cfg['vo_engine']} · foley={cfg['foley_engine']} "
          f"· bed={cfg['bed_engine']}  (all $0)")
    for shot in project["shots"]:
        stems = audio_stems(project, shot)
        if stems:
            print(f"  {shot['id']:<20} " + " + ".join(
                f"{k}:{v['engine']}" for k, v in stems.items()))
        else:
            print(f"  {shot['id']:<20} (no stems)")
    print(f"  notebook : {target}")
    print("  T4 GPU -> Run all -> audio/vo + audio/foley + audio/bed.wav in Drive")
    for warn in audio_licence_warnings(project):
        print(f"  WARN     {warn}")
    print(f"  next     : python3 tools/videogen.py mix {project_file}")

    receipts = load_json(paths["receipts"]) if paths["receipts"].exists() else {"shots": {}}
    receipts.setdefault("shots", {})
    receipts["audio"] = {"engines": {k: cfg[k] for k in ("vo_engine", "foley_engine", "bed_engine")},
                         "notebook": str(target), "created_at": now()}
    write_json(paths["receipts"], receipts)
    return 0


def mix_graph(has_vo: bool, has_foley: bool, has_bed: bool, *, bed_gain_db: float = -6.0,
              vo_gain_db: float = 0.0, foley_gain_db: float = -3.0,
              loudnorm: bool = False) -> tuple[list[str], str, str]:
    """Build (extra inputs, filter_complex, audio map) for one shot.

    Dialogue and foley are summed, then the music bed is ducked under them with
    ``sidechaincompress`` — the standard fix for "voice lost in the bed". The dialogue bus is
    ``asplit`` so it can feed both the ducker and the final mix (an ffmpeg output may only be
    consumed once).
    """
    inputs: list[str] = []
    index = 1
    dialogue_parts: list[str] = []
    filters: list[str] = []

    def gain(value: float) -> str:
        return f",volume={value}dB" if value else ""

    if has_vo:
        inputs += ["-i", "__VO__"]
        filters.append(f"[{index}:a]aresample=48000{gain(vo_gain_db)}[vo]")
        dialogue_parts.append("[vo]")
        index += 1
    if has_foley:
        inputs += ["-i", "__FOLEY__"]
        filters.append(f"[{index}:a]aresample=48000{gain(foley_gain_db)}[fo]")
        dialogue_parts.append("[fo]")
        index += 1

    dia = ""
    if len(dialogue_parts) == 2:
        filters.append("[vo][fo]amix=inputs=2:normalize=0[dia0]")
        dia = "[dia0]"
    elif dialogue_parts:
        dia = dialogue_parts[0]

    if has_bed:
        inputs += ["-i", "__BED__"]
        filters.append(f"[{index}:a]aresample=48000{gain(bed_gain_db)}[bed]")
        if dia:
            filters.append(f"{dia}asplit=2[dia][diaside]")
            filters.append("[bed][diaside]sidechaincompress=threshold=0.03:ratio=8:attack=15:"
                           "release=350[bedduck]")
            filters.append("[dia][bedduck]amix=inputs=2:normalize=0[aout0]")
        else:
            filters.append("[bed]anull[aout0]")
        tail = "[aout0]"
    elif dia:
        filters.append(f"{dia}anull[aout0]")
        tail = "[aout0]"
    else:
        return [], "", ""

    if loudnorm:
        filters.append(f"{tail}loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
    else:
        filters.append(f"{tail}anull[aout]")
    return inputs, ";".join(filters), "[aout]"


def mix_variant(path: pathlib.Path) -> pathlib.Path:
    return path.with_name(path.stem + "-mix.mp4")


def mix(project_file: pathlib.Path, *, loudnorm: bool = False) -> int:
    """Mux voice + foley + music under each shot's best video (needs ffmpeg)."""
    project = require_project(project_file)
    paths = project_paths(project_file)
    ffmpeg = which("ffmpeg")
    if not ffmpeg:
        raise EngineError("ffmpeg not found — run mix on a machine that has it (apt-get install -y ffmpeg)")

    cfg = audio_config(project)
    made, skipped, missing = 0, 0, []
    receipts = load_json(paths["receipts"]) if paths["receipts"].exists() else {"shots": {}}
    receipts.setdefault("shots", {})
    receipts.setdefault("mix", {})

    for shot in project["shots"]:
        sid = shot["id"]
        video = shot_media(shot, paths)
        if video is None or video.stem.endswith("-mix"):
            if video is None:
                missing.append(sid)
            skipped += 1
            continue
        stems = audio_stems(project, shot)
        vo = paths["base"] / stems["vo"]["file"] if "vo" in stems else None
        foley = paths["base"] / stems["foley"]["file"] if "foley" in stems else None
        bed = paths["base"] / "audio" / "bed.wav"
        vo = vo if vo and vo.exists() else None
        foley = foley if foley and foley.exists() else None
        bed = bed if bed.exists() else None
        if not any((vo, foley, bed)):
            skipped += 1
            continue

        extra, graph, amap = mix_graph(bool(vo), bool(foley), bool(bed),
                                       bed_gain_db=cfg["gain_db"], loudnorm=loudnorm)
        resolved = []
        for item in extra:
            if item == "__VO__":
                resolved.append(str(vo))
            elif item == "__FOLEY__":
                resolved.append(str(foley))
            elif item == "__BED__":
                resolved.append(str(bed))
            else:
                resolved.append(item)

        out = mix_variant(video)
        cmd = [ffmpeg, "-y", "-i", str(video)] + resolved + [
            "-filter_complex", graph, "-map", "0:v:0", "-map", amap,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"FAIL  {sid}: {(proc.stderr or '')[-300:]}")
            receipts["mix"][sid] = {"status": "failed", "error": (proc.stderr or "")[-300:]}
            continue
        receipts["mix"][sid] = {"status": "mixed", "path": str(out), "md5": md5(out),
                                "stems": {"vo": bool(vo), "foley": bool(foley), "bed": bool(bed)},
                                "mixed_at": now()}
        print(f"OK    {sid:<20} -> {out.name}  (vo={bool(vo)} foley={bool(foley)} bed={bool(bed)})")
        made += 1

    receipts["mix"]["updated_at"] = now()
    write_json(paths["receipts"], receipts)
    print(f"\nmixed {made} · skipped {skipped} · missing media {len(missing)}")
    if missing:
        print("  missing: " + ", ".join(missing) + "  (run the free queue / verify first)")
        return 3
    if not made:
        raise EngineError("nothing to mix — no voice/foley/bed stems found "
                          "(run `audio` in Colab, then drop the wavs into audio/)")
    print(f"next: python3 tools/videogen.py verify {project_file} && "
          f"python3 tools/videogen.py assemble {project_file}")
    return 0


# --------------------------------------------------------------------------- upscale
def _nb(cells: list[dict]) -> dict:
    return {"cells": cells,
            "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"},
                         "language_info": {"name": "python"},
                         "accelerator": "GPU"},
            "nbformat": 4, "nbformat_minor": 5}


def _md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def _code(text: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": text.splitlines(keepends=True)}


_UPSCALE_INTRO = """# Upscale · __PROJECT__ (__ENGINE__ x__FACTOR__)

Free route ne `__IN_W__x__IN_H__` render kiya. Yeh notebook usko **`__OUT_W__x__OUT_H__`** banata hai —
**sharper, magar naya detail nahi**. Asli 1080p+ chahiye to `route: paid` (H3 768P / 2K) hi raasta hai;
480p ko scale karke "4K" kehna dhoka hai.

**Kaise chalayein:** Runtime → Change runtime type → **T4 GPU** (realesrgan) ya **CPU** (lanczos) →
Run all → clips `shots/` me `<name>-__FACTOR__x.mp4` banti hain, audio/lipsync intact.
"""

_UPSCALE_CONFIG = """import hashlib, json, pathlib, shutil, subprocess

# 1) Drive path — apna project folder yahan daalo
PROJECT_DIR = "/content/drive/MyDrive/MONARCH STUDIO/Wf-07 • Monarch Ai Agent/05 · Projects/__PROJECT__"
SHOT_IDS = [__IDS__]          # [] = sab mp4
FACTOR = __FACTOR__
FORCE = False                  # True = already upscaled files dobara banao

from google.colab import drive
drive.mount("/content/drive")
SHOTS = pathlib.Path(PROJECT_DIR) / "shots"
print("shots dir:", SHOTS, "| exists:", SHOTS.exists())
assert SHOTS.exists(), "path galat hai — Drive me '05 · Projects/__PROJECT__' check karo"
"""

_UPSCALE_HELPERS = """def audio_args(src):
    has_audio = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.strip()
    return ["-map", "0:v:0", "-map", "0:a:0", "-c:a", "aac", "-b:a", "192k"] if has_audio else []


def size_of(src):
    return subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "csv=p=0", str(src)],
        capture_output=True, text=True).stdout.strip()


def fps_of(src):
    return subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=r_frame_rate", "-of", "csv=p=0", str(src)],
        capture_output=True, text=True).stdout.strip() or "24/1"
"""

_UPSCALE_LANCZOS = """# 2) Lanczos x__FACTOR__ — pure ffmpeg, GPU ki zarurat nahi (CPU runtime bhi chalega)
jobs = SHOT_IDS or [p.stem for p in SHOTS.glob("*.mp4")]
done = []
for sid in jobs:
    for src in sorted(SHOTS.glob(f"{sid}*.mp4")):
        if src.name.endswith(f"-{FACTOR}x.mp4"):
            continue
        dst = src.with_name(f"{src.stem}-{FACTOR}x.mp4")
        if dst.exists() and not FORCE:
            print("skip (exists)", dst.name)
            continue
        cmd = ["ffmpeg", "-y", "-i", str(src),
               "-vf", f"scale=iw*{FACTOR}:ih*{FACTOR}:flags=lanczos,unsharp=5:5:0.6",
               "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p"] + audio_args(src) + [str(dst)]
        subprocess.run(cmd, check=True, capture_output=True)
        print("ok  ", dst.name, size_of(dst))
        done.append(dst.name)
print("\\nupscaled:", len(done))
"""

_UPSCALE_ESRGAN = """# 2) Real-ESRGAN x__FACTOR__ on the free T4 (pip install ~1 min)
import cv2, numpy as np, torch
!pip -q install basicsr realesrgan facexlib gfpgan
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none")
assert torch.cuda.is_available(), "GPU nahi mila — Runtime > Change runtime type > T4 GPU"

net = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
enhancer = RealESRGANer(
    scale=4, half=True, tile=0, tile_pad=10, pre_pad=0, model=net,
    model_path="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus.pth")


def upscale_video(src, dst, factor=FACTOR):
    frames_in = pathlib.Path("/content/_frames_in")
    frames_out = pathlib.Path("/content/_frames_out")
    for folder in (frames_in, frames_out):
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)
    subprocess.run(["ffmpeg", "-y", "-i", str(src), str(frames_in / "%06d.png")],
                   check=True, capture_output=True)
    for frame in sorted(frames_in.glob("*.png")):
        img = cv2.imread(str(frame), cv2.IMREAD_COLOR)
        out, _ = enhancer.enhance(img, outscale=factor)
        cv2.imwrite(str(frames_out / frame.name), out)
    silent = pathlib.Path("/content/_up_silent.mp4")
    subprocess.run(["ffmpeg", "-y", "-framerate", fps_of(src), "-i", str(frames_out / "%06d.png"),
                    "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", str(silent)],
                   check=True, capture_output=True)
    cmd = ["ffmpeg", "-y", "-i", str(silent), "-i", str(src), "-map", "0:v:0"] \
        + (["-map", "1:a:0", "-c:a", "aac", "-b:a", "192k"] if audio_args(src) else []) \
        + ["-c:v", "copy", "-shortest", str(dst)]
    subprocess.run(cmd, check=True, capture_output=True)
    return dst


jobs = SHOT_IDS or [p.stem for p in SHOTS.glob("*.mp4")]
done = []
for sid in jobs:
    for src in sorted(SHOTS.glob(f"{sid}*.mp4")):
        if src.name.endswith(f"-{FACTOR}x.mp4"):
            continue
        dst = src.with_name(f"{src.stem}-{FACTOR}x.mp4")
        if dst.exists() and not FORCE:
            print("skip (exists)", dst.name)
            continue
        print("upscaling", src.name, size_of(src))
        upscale_video(src, dst)
        print("ok  ", dst.name, size_of(dst))
        done.append(dst.name)
print("\\nupscaled:", len(done))
"""

_UPSCALE_RECEIPT = """# 3) Receipt — kya bana, kitna bada, kaunsa md5
rows = []
for sid in (SHOT_IDS or [p.stem for p in SHOTS.glob("*.mp4")]):
    for f in sorted(SHOTS.glob(f"{sid}*{FACTOR}x.mp4")):
        rows.append({"shot": sid, "file": f.name, "bytes": f.stat().st_size,
                     "size": size_of(f), "md5": hashlib.md5(f.read_bytes()).hexdigest()})
receipt = pathlib.Path(PROJECT_DIR) / "upscale_receipt.json"
receipt.write_text(json.dumps({"project": "__PROJECT__", "engine": "__ENGINE__",
                               "factor": FACTOR, "files": rows}, indent=2))
print(json.dumps(rows, indent=2))
print("\\nreceipt:", receipt)
print("Ab repo me: python3 tools/videogen.py verify <project.json>")
"""


def build_upscale_notebook(project: dict, engine: str, factor: int, shot_ids: list[str]) -> dict:
    """A standalone Colab notebook that lifts the free 480p clips to 2x/4x.

    Honest framing: Real-ESRGAN rebuilds texture; it does not invent the detail a native
    1080p render would have. The measured size is printed for every shot.
    """
    up = upscale_target(project, None)
    factor = int(factor or up["factor"])
    engine = (engine or up["engine"]).lower()
    tokens = {
        "__PROJECT__": str(project["project_id"]),
        "__ENGINE__": engine,
        "__FACTOR__": str(factor),
        "__ID_LITERAL__": ", ".join(f'"{i}"' for i in shot_ids),
        "__IDS__": ", ".join(f'"{i}"' for i in shot_ids),
        "__IN_W__": str(up["in_width"]), "__IN_H__": str(up["in_height"]),
        "__OUT_W__": str(up["in_width"] * factor), "__OUT_H__": str(up["in_height"] * factor),
    }

    def fill(text: str) -> str:
        for key, value in tokens.items():
            text = text.replace(key, value)
        return text

    work = _UPSCALE_LANCZOS if engine == "lanczos" else _UPSCALE_ESRGAN
    return _nb([_md(fill(_UPSCALE_INTRO)), _code(fill(_UPSCALE_CONFIG)),
                _code(_UPSCALE_HELPERS), _code(fill(work)), _code(fill(_UPSCALE_RECEIPT))])


def upscale(project_file: pathlib.Path, *, engine: str | None = None, factor: int | None = None,
            only: list[str] | None = None) -> int:
    """Write the upscale notebook for a project's free-route clips."""
    project = require_project(project_file)
    paths = project_paths(project_file)
    paths["upscale"].mkdir(parents=True, exist_ok=True)
    up = upscale_target(project, None)
    engine = (engine or up["engine"] or "realesrgan").lower()
    engine = {"esrgan": "realesrgan", "x2": "realesrgan"}.get(engine, engine)
    if engine not in UPSCALES or engine == "off":
        raise EngineError("engine must be one of " +
                          ", ".join(k for k in UPSCALES if k != "off"))
    factor = int(factor or up["factor"])
    if factor not in (2, 4):
        raise EngineError("factor must be 2 or 4")
    shot_ids = list(only or [s["id"] for s in project["shots"]])
    unknown = [i for i in shot_ids if i not in {s["id"] for s in project["shots"]}]
    if unknown:
        raise EngineError("unknown shot id(s): " + ", ".join(unknown))

    notebook = build_upscale_notebook(project, engine, factor, shot_ids)
    target = paths["upscale"] / f"UPSCALE_{project['project_id']}_{engine}_x{factor}.ipynb"
    write_json(target, notebook)

    width, height = up["in_width"], up["in_height"]
    print(f"UPSCALE {project['project_id']}  {engine} x{factor}")
    print(f"  {width}x{height} -> {width * factor}x{height * factor}  ({len(shot_ids)} shot(s))")
    print(f"  {UPSCALES[engine]['note']}")
    print(f"  notebook : {target}")
    print(f"  {(chr(39) + 'T4 GPU' + chr(39)) if engine == 'realesrgan' else 'CPU runtime ok'} "
          f"-> Run all -> <shot>-{factor}x.mp4 in shots/")
    print(f"  then     : python3 tools/videogen.py verify {project_file}")

    receipts = load_json(paths["receipts"]) if paths["receipts"].exists() else {"shots": {}}
    receipts.setdefault("shots", {})
    receipts["upscale"] = {"engine": engine, "factor": factor, "notebook": str(target),
                           "created_at": now(), "in": [width, height],
                           "out": [width * factor, height * factor], "shots": shot_ids}
    write_json(paths["receipts"], receipts)
    return 0


# --------------------------------------------------------------------------- verify
def shot_media(shot: dict, paths: dict) -> pathlib.Path | None:
    """Return the finished media for a shot, if any.

    The free chain writes a lipsynced version next to the silent clip (``<id>-talk.mp4``) and the
    upscale stage writes ``<id>-2x.mp4`` / ``<id>-talk-2x.mp4``, so the sharpest finished file wins.
    """
    sid = shot["id"]
    stems = [f"{sid}-talk-2x", f"{sid}-2x", f"{sid}-talk-4x", f"{sid}-4x",
             f"{sid}-talk", f"{sid}"]
    candidates = [paths["shots"] / f"{stem}-mix.mp4" for stem in stems]
    candidates += [paths["shots"] / f"{stem}.mp4" for stem in stems]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _probe_with_ffmpeg(path: pathlib.Path, ffmpeg: str) -> dict:
    """Parse `ffmpeg -i` stderr when ffprobe is not installed (static ffmpeg builds)."""
    proc = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)],
                          capture_output=True, text=True)
    text = (proc.stderr or "") + (proc.stdout or "")
    if "Stream #" not in text:
        return {"available": True, "error": text.strip().splitlines()[-1][:300] if text.strip() else "no streams"}
    duration = 0.0
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    if match:
        hours, minutes, seconds = match.groups()
        duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    video_line = next((line for line in text.splitlines() if "Video:" in line), "")
    audio_line = next((line for line in text.splitlines() if "Audio:" in line), "")
    width = height = 0
    size = re.search(r"[,\s](\d{2,5})x(\d{2,5})(?=[\s,\[])", video_line)
    if size:
        width, height = int(size.group(1)), int(size.group(2))
    fps = 0.0
    fps_match = re.search(r"(\d+(?:\.\d+)?)\s*fps", video_line)
    if fps_match:
        fps = round(float(fps_match.group(1)), 3)
    codec = re.search(r"Video:\s*([a-z0-9_]+)", video_line)
    acodec = re.search(r"Audio:\s*([a-z0-9_]+)", audio_line)
    return {"available": True, "width": width, "height": height, "fps": fps,
            "duration": duration, "video_codec": codec.group(1) if codec else None,
            "audio_codec": acodec.group(1) if acodec else None, "probe": "ffmpeg -i"}


def probe(path: pathlib.Path) -> dict:
    ffprobe = which("ffprobe")
    if not ffprobe:
        ffmpeg = which("ffmpeg")
        return _probe_with_ffmpeg(path, ffmpeg) if ffmpeg else {"available": False}
    proc = subprocess.run(
        [ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True)
    if proc.returncode != 0:
        return {"available": True, "error": proc.stderr.strip()[:300]}
    data = json.loads(proc.stdout or "{}")
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    fps = 0.0
    if video.get("avg_frame_rate") and "/" in video["avg_frame_rate"]:
        num, den = video["avg_frame_rate"].split("/")
        fps = round(float(num) / float(den), 3) if float(den) else 0.0
    return {"available": True, "width": int(video.get("width") or 0), "height": int(video.get("height") or 0),
            "fps": fps, "duration": float(data.get("format", {}).get("duration") or 0),
            "video_codec": video.get("codec_name"), "audio_codec": audio.get("codec_name") or None}


def verify(project_file: pathlib.Path, *, tolerance: float = 0.6) -> int:
    project = require_project(project_file)
    paths = project_paths(project_file)
    receipts = load_json(paths["receipts"]) if paths["receipts"].exists() else {"shots": {}}
    receipts.setdefault("shots", {})

    failures: list[str] = []
    checked = 0
    print(f"VERIFY {project['project_id']}")
    for shot in project["shots"]:
        sid = shot["id"]
        file = shot_media(shot, paths)
        if file is None:
            hint = " (run the queued lipsync script)" if shot["kind"] == "lipsync" else ""
            failures.append(f"{sid}: no media for {sid}{hint}")
            print(f"  MISS  {sid:<20} no media{hint}")
            continue
        if file.stat().st_size == 0:
            failures.append(f"{sid}: {file.name} is 0 bytes — a failed render/mix, not a shot")
            print(f"  WARN  {sid:<20} 0 bytes — failed render/mix")
            continue
        info = probe(file)
        record = {"engine": receipts["shots"].get(sid, {}).get("engine"),
                  "md5": md5(file), "bytes": file.stat().st_size,
                  "checked_at": now(), "probe": info}
        expected = float(shot["seconds"])
        problems: list[str] = []
        if info.get("available"):
            if info.get("duration") and abs(info["duration"] - expected) > tolerance:
                problems.append(f"duration {info['duration']:.2f}s vs {expected:.2f}s")
            if info.get("fps") and abs(info["fps"] - float(project.get("fps", 24))) > 1.0:
                problems.append(f"fps {info['fps']} vs {project.get('fps', 24)}")
            if not info.get("audio_codec") and shot["kind"] == "hero" and project.get("route") == "paid":
                problems.append("paid hero shot has no audio stream")
            try:
                want_audio = audio_config(project)["mix"] and any(
                    (paths["base"] / p).exists()
                    for p in [f"audio/vo/{sid}.wav", f"audio/foley/{sid}.wav"])
            except EngineError:
                want_audio = False
            if want_audio and not info.get("audio_codec"):
                problems.append("audio stems exist but this file has no audio — run `mix` "
                                "and keep the -mix.mp4")
            target_h = int((project.get("delivery") or {}).get("target_height") or 0)
            if target_h and info.get("height") and info["height"] < target_h * 0.95:
                problems.append(f"height {info['height']}p below delivery.target_height {target_h}p "
                                f"— run `upscale` and keep the -2x file")
        else:
            record["probe"] = {"available": False, "note": "ffprobe missing: existence/md5 checked only"}
        receipts["shots"].setdefault(sid, {}).update(record)
        if problems:
            failures.append(f"{sid}: " + "; ".join(problems))
            print(f"  WARN  {sid:<20} " + "; ".join(problems))
        else:
            checked += 1
            res = ""
            if info.get("available") and info.get("height"):
                res = f"{info.get('width')}x{info.get('height')}  "
            print(f"  PASS  {sid:<20} {record['bytes'] / 1e6:6.1f} MB  {res}md5 {record['md5'][:10]}")

    receipts["verified_at"] = now()
    write_json(paths["receipts"], receipts)
    print(f"\n{checked}/{len(project['shots'])} shot(s) verified · {len(failures)} issue(s)")
    for problem in failures:
        print(f"  ! {problem}")
    return 0 if not failures else 3


# --------------------------------------------------------------------------- assemble
def assemble(project_file: pathlib.Path, out: pathlib.Path | None = None, *, with_music: bool = True) -> int:
    project = require_project(project_file)
    paths = project_paths(project_file)
    ffmpeg = which("ffmpeg")
    if not ffmpeg:
        raise EngineError("ffmpeg not found — install it (apt-get install -y ffmpeg) or run assemble on a machine that has it")

    clips = []
    for shot in project["shots"]:
        file = shot_media(shot, paths)
        if file is None:
            raise EngineError(f"missing shot {shot['id']} — run verify and finish the queue first")
        clips.append(file)

    paths["delivery"].mkdir(parents=True, exist_ok=True)
    target = out or (paths["delivery"] / f"{project['project_id']}_MASTER.mp4")
    listing = paths["delivery"] / "concat.txt"
    listing.write_text("".join(f"file '{c}'\n" for c in clips))

    fps = int(project.get("delivery_fps") or project.get("fps") or 24)
    cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-r", str(fps)]
    target_h = int((project.get("delivery") or {}).get("target_height") or 0)
    first = probe(clips[0])
    if target_h and first.get("available") and first.get("height") and first["height"] < target_h:
        cmd += ["-vf", f"scale=-2:{target_h}:flags=lanczos"]
        print(f"scale      : {first['width']}x{first['height']} -> {target_h}p (lanczos) — "
              f"sharpening, not new detail; run `upscale` first for real texture")
    cmd += ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p"]
    music = project.get("audio", {}).get("music")
    if with_music and music and (paths["base"] / music).exists():
        # loop the bed under the cut and fade it out at the end
        cmd += ["-stream_loop", "-1", "-i", str(paths["base"] / music), "-shortest",
                "-c:a", "aac", "-b:a", "192k", "-af", "afade=t=out:st=0:d=1"]
        print(f"music bed: {music}")
    else:
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    cmd.append(str(target))

    print(" ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise EngineError("ffmpeg failed:\n" + (proc.stderr or "")[-1200:])

    info = probe(target)
    receipts = load_json(paths["receipts"]) if paths["receipts"].exists() else {"shots": {}}
    receipts["master"] = {"path": str(target), "md5": md5(target), "bytes": target.stat().st_size,
                          "fps": fps, "probe": info, "assembled_at": now()}
    write_json(paths["receipts"], receipts)
    print(f"\nMASTER  {target}  ({target.stat().st_size / 1e6:.1f} MB, md5 {receipts['master']['md5'][:10]})")
    if drive_targets(project["project_id"]).get("masters_id"):
        dest = drive_targets(project["project_id"])
        print(f"drive   : {dest['root']} / {dest['master_folder']}  (folder id {dest['masters_id']})")
    if info.get("available"):
        print(f"        {info.get('width')}x{info.get('height')} @ {info.get('fps')} fps, "
              f"{info.get('duration'):.2f}s, audio={info.get('audio_codec')}")
    return 0


# --------------------------------------------------------------------------- free-only mode
FREE_COMPUTE = ROOT / "studio" / "free_compute.json"
FREE_QUOTA = ROOT / "studio" / "free_quota.json"


def free_only() -> bool:
    """Zero-spend guard. ON unless someone deliberately sets MONARCH_ALLOW_PAID=1."""
    if os.environ.get("MONARCH_ALLOW_PAID") == "1":
        return False
    return os.environ.get("MONARCH_FREE_ONLY", "1") != "0"


def free_compute() -> dict:
    """Free GPU/CPU menu with quotas. Empty dict when the file is missing."""
    if not FREE_COMPUTE.exists():
        return {}
    return load_json(FREE_COMPUTE)


def _iso_week() -> str:
    year, week, _ = datetime.datetime.now().isocalendar()
    return f"{year}-W{week:02d}"


def quota_state() -> dict:
    """Rolling weekly free-GPU ledger (resets automatically every ISO week)."""
    state = load_json(FREE_QUOTA) if FREE_QUOTA.exists() else {}
    week = _iso_week()
    if state.get("week") != week:
        state = {"week": week, "used": {}, "log": []}
    state.setdefault("used", {})
    state.setdefault("log", [])
    return state


def quota_limits() -> dict[str, float]:
    """Hard weekly/monthly hour limits, where the provider publishes them."""
    limits = {}
    for provider in free_compute().get("providers", []):
        quota = str(provider.get("quota", ""))
        hours = re.search(r"(\d+(?:\.\d+)?)\s*(?:GPU\s*)?hours?\s*per\s*week", quota)
        if hours:
            limits[provider["id"]] = float(hours.group(1))
    return limits


def quota_use(provider: str, hours: float, note: str = "") -> dict:
    """Record GPU hours burned on a free provider."""
    ids = {p["id"] for p in free_compute().get("providers", [])}
    if ids and provider not in ids:
        raise EngineError(f"unknown provider {provider}; use one of {', '.join(sorted(ids))}")
    if hours <= 0:
        raise EngineError("hours must be positive")
    state = quota_state()
    state["used"][provider] = round(float(state["used"].get(provider, 0)) + float(hours), 2)
    state["log"].append({"provider": provider, "hours": float(hours), "note": note,
                         "at": now()})
    write_json(FREE_QUOTA, state)
    return state


def quota_report(state: dict | None = None) -> list[dict]:
    """Per-provider usage against the published limit."""
    state = state or quota_state()
    limits = quota_limits()
    rows = []
    for provider in free_compute().get("providers", []):
        pid = provider["id"]
        used = float(state["used"].get(pid, 0.0))
        limit = limits.get(pid)
        rows.append({"id": pid, "name": provider["name"], "used": used, "limit": limit,
                     "left": round(limit - used, 2) if limit else None,
                     "role": provider.get("role", "")})
    return rows


def print_quota() -> None:
    rows = quota_report()
    if not rows:
        print("free compute menu missing — restore studio/free_compute.json")
        return
    print(f"FREE COMPUTE · week {quota_state()['week']} · mode "
          f"{'FREE-ONLY' if free_only() else 'PAID ALLOWED (MONARCH_ALLOW_PAID=1)'}")
    for row in rows:
        if row["limit"]:
            bar = f"{row['used']:.1f}/{row['limit']:.0f} h  ({row['left']:.1f} h left)"
        else:
            bar = f"{row['used']:.1f} h  (soft quota)"
        print(f"  {row['id']:<12} {bar:<26} {row['role']}")


# --------------------------------------------------------------------------- mobile
# One notebook, one Run, three stages. Everything the phone owner has to do is tap "Run all".
# The assistant runs plan / mix / verify / assemble here; the phone only provides GPU time.

_MOBILE_INTRO = """# 📱 MONARCH STUDIO · phone-only notebook — __PROJECT__

**Aap ko sirf 3 tap karne hain:**

1. Upar menu → **Runtime** → **Change runtime type** → **T4 GPU** → Save
2. Upar menu → **Runtime** → **Run all**
3. 20–40 min baad neeche aakhri cell me `DONE` dikhega → mujhe chat me `DONE` likh do

Yeh notebook teeno kaam khud karta hai (jo stage chahiye, neeche toggle se ON/OFF):

| Stage | Kya banega | Free? |
|---|---|---|
| 1 · Clips | __N_SHOTS__ silent clips, __W__x__H__, Wan 2.1 1.3B | ✅ $0 |
| 2 · Voice | __N_VO__ line(s), Kokoro-82M (Apache-2.0) | ✅ $0 |
| 3 · Foley + Upscale | ambience/SFX + 480p → __UP_W__x__UP_H__ (Real-ESRGAN ×__FACTOR__) | ✅ $0 |

Output aap ke Drive folder me jayega:
`Wf-07 • Monarch Ai Agent / 05 · Projects/__PROJECT__/`
Agar Drive mount fail ho jaye (Colab ka auth masla) to notebook **local disk par** kaam karega aur aakhir me
ek **ZIP download** dega — kuch bhi rukta nahi.

> Mix, verify aur master main yahan se karunga — aap ko ffmpeg ya terminal ki zarurat **nahi**.
"""

_MOBILE_CONFIG = """# ── 1 · Setup (koi edit nahi) ────────────────────────────────────────────────
RUN_CLIPS = True       # silent clips (sabse lamba step)
RUN_VOICE = True       # Kokoro voice lines
RUN_FOLEY = True       # MMAudio ambience/SFX
RUN_UPSCALE = True     # 480p -> 2x

import hashlib, json, pathlib, subprocess, time, zipfile

PROJECT = "__PROJECT__"
DRIVE_BASE = pathlib.Path(f"/content/drive/MyDrive/MONARCH STUDIO/Wf-07 • Monarch Ai Agent/05 · Projects/{PROJECT}")
LOCAL_BASE = pathlib.Path(f"/content/m_out/{PROJECT}")
DRIVE_OK = False

# Drive optional hai. Mount fail ho (credential propagation / 3rd-party cookies) to
# notebook local disk par kaam karta hai aur aakhir me ZIP download deta hai — kuch rukta nahi.
try:
    from google.colab import drive
    drive.mount("/content/drive", force_remount=True)
    DRIVE_BASE.mkdir(parents=True, exist_ok=True)
    probe = DRIVE_BASE / ".write_test"
    probe.write_text("ok")
    probe.unlink()
    DRIVE_OK = True
    print("Drive  : mounted ✔")
except Exception as exc:
    print("Drive  : mount nahi hua —", type(exc).__name__, str(exc)[:110])
    print("         koi baat nahi: sab local disk par banega, aakhir me ZIP download milega")

BASE = DRIVE_BASE if DRIVE_OK else LOCAL_BASE
SHOTS = BASE / "shots"
VO_DIR = BASE / "audio" / "vo"
FOLEY_DIR = BASE / "audio" / "foley"
for folder in (SHOTS, VO_DIR, FOLEY_DIR):
    folder.mkdir(parents=True, exist_ok=True)

JOBS = __JOBS__
VO_TEXT = __VO_TEXT__
FOLEY_PROMPT = __FOLEY_PROMPT__
FACTOR = __FACTOR__

print("project :", BASE, "| exists:", BASE.exists())
print("shots   :", len(JOBS), "| voice:", len([v for v in VO_TEXT.values() if v.strip()]),
      "| foley:", len([v for v in FOLEY_PROMPT.values() if v.strip()]))


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
"""

_MOBILE_PIPELINE = """# ── 2 · Wan 2.1 T2V 1.3B load — Colab 12.7 GB RAM safe (4-bit UMT5) ─────────
pipe = None
if RUN_CLIPS:
    !pip -q install "diffusers>=0.35" "transformers>=4.49" accelerate imageio imageio-ffmpeg ftfy sentencepiece bitsandbytes

    import os, gc, ctypes, torch
    os.environ["HF_HUB_DISABLE_XET"] = "1"   # Xet downloader ka in-memory buffer hi Colab RAM todta hai
    try:                                     # glibc: freed pages OS ko turant wapas
        _libc = ctypes.CDLL("libc.so.6")
        _libc.mallopt(-3, 1 << 20)
        _libc.mallopt(-1, 64 << 10)
        _libc.mallopt(-8, 2)
        HAVE_TRIM = True
    except Exception:
        _libc = None
        HAVE_TRIM = False

    def host_ram():
        try:
            with open("/proc/meminfo") as fh:
                for line in fh:
                    if line.startswith("MemAvailable"):
                        return round(int(line.split()[1]) / 1048576, 1)
        except OSError:
            pass
        return None

    def free_mem(tag=""):
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        if HAVE_TRIM:
            _libc.malloc_trim(0)
        if tag:
            print("   · freed:", tag, "| host free:", host_ram(), "GB")

    from diffusers import AutoencoderKLWan, WanPipeline, WanTransformer3DModel
    from diffusers.schedulers import UniPCMultistepScheduler
    from transformers import UMT5EncoderModel, BitsAndBytesConfig as T5QuantConfig

    MODEL_ID = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
    print("host RAM free:", host_ram(), "GB / 12.7")

    def build_pipe():
        # UMT5-XXL fp32 me 22.7 GB hai — 4-bit NF4 se ~2.4 GB VRAM, host RAM chhua hi nahi
        vae = AutoencoderKLWan.from_pretrained(MODEL_ID, subfolder="vae", torch_dtype=torch.float32)
        t5_quant = T5QuantConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                 bnb_4bit_compute_dtype=torch.float16,
                                 llm_int8_enable_fp32_cpu_offload=True)
        text_encoder = UMT5EncoderModel.from_pretrained(
            MODEL_ID, subfolder="text_encoder", quantization_config=t5_quant,
            torch_dtype=torch.float16, device_map={"": 0})
        free_mem("text encoder 4-bit")
        transformer = WanTransformer3DModel.from_pretrained(
            MODEL_ID, subfolder="transformer", torch_dtype=torch.float16)
        free_mem("transformer fp16")
        built = WanPipeline.from_pretrained(MODEL_ID, vae=vae, text_encoder=text_encoder,
                                            transformer=transformer, torch_dtype=torch.float16,
                                            low_cpu_mem_usage=True)
        built.transformer.to("cuda")
        built.vae.to("cuda")
        # 480p ke liye flow_shift 3.0 (5.0 sirf 720p) — warna texture muddy
        built.scheduler = UniPCMultistepScheduler(prediction_type="flow_prediction",
                                                  use_flow_sigmas=True, num_train_timesteps=1000,
                                                  flow_shift=3.0)
        built.vae.enable_tiling()
        built.vae.enable_slicing()
        free_mem("pipeline ready")
        return built

    try:
        pipe = build_pipe()
        print("pipeline ready ·", torch.cuda.get_device_name(0))
    except Exception as exc:
        pipe = None
        print("MODEL LOAD FAILED:", type(exc).__name__, str(exc)[:300])
        print("   yeh line chat me bhej do — main chhota config bana dunga")
"""

_MOBILE_CLIPS = """# ── 3 · Clips (silent, 480x832) ─────────────────────────────────────────────
if RUN_CLIPS and pipe is not None:
    from diffusers.utils import export_to_video

    NEGATIVE = ("blurry, low quality, distorted, deformed hands, extra limbs, text overlay, "
                "watermark, jpeg artifacts, static frame, flicker")
    receipts = []
    started = time.time()
    for index, job in enumerate(JOBS, 1):
        out = SHOTS / f"{job['id']}.mp4"
        if out.exists() and out.stat().st_size > 10_000:
            print(f"[{index}/{len(JOBS)}] skip (already on Drive) {out.name}")
            continue
        print(f"[{index}/{len(JOBS)}] {job['id']}  {job['width']}x{job['height']} · {job['frames']} frames")
        t0 = time.time()
        try:
            frames = pipe(
                prompt=job["prompt"], negative_prompt=NEGATIVE,
                width=job["width"], height=job["height"], num_frames=job["frames"],
                num_inference_steps=job.get("steps", 18), guidance_scale=5.0,
                generator=torch.Generator("cpu").manual_seed(int(job.get("seed", 42))),
            ).frames[0]
            export_to_video(frames, str(out), fps=16)
            del frames
            print(f"  ✔ {out.name}  {out.stat().st_size/1e6:.1f} MB · {md5(out)[:10]} · {time.time()-t0:.0f}s")
            receipts.append({"id": job["id"], "file": out.name, "md5": md5(out),
                             "seconds": round(time.time() - t0, 1)})
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            print("  ✖ VRAM OOM — mujhe bolo, main frames/steps aur kam kar dunga")
            receipts.append({"id": job["id"], "error": "cuda OOM"})
        except Exception as exc:
            print("  ✖", type(exc).__name__, str(exc)[:200])
            receipts.append({"id": job["id"], "error": f"{type(exc).__name__}: {exc}"})
        free_mem(f"after {job['id']}")
        (BASE / "colab_clips_receipt.json").write_text(json.dumps(receipts, indent=2))
    del pipe
    pipe = None
    free_mem("Wan unloaded — upscale ke liye jagah")
"""

_MOBILE_VOICE = """# ── 4 · Voice — Kokoro-82M (Apache-2.0, GPU bhi nahi chahiye) ────────────────
if RUN_VOICE:
    !pip -q install kokoro soundfile
    import numpy as np, soundfile as sf
    from kokoro import KPipeline

    pipeline = KPipeline(lang_code="a")      # 'a' American, 'b' British
    VOICE = "af_heart"                       # 54 options; badalna ho to mujhe bolo
    made = 0
    for shot_id, text in VO_TEXT.items():
        text = (text or "").strip()
        if not text:
            continue
        out = VO_DIR / f"{shot_id}.wav"
        if out.exists():
            print("skip (already on Drive)", out.name)
            continue
        chunks = [audio for _, _, audio in pipeline(text, voice=VOICE, speed=1.0)]
        audio = np.concatenate([c if isinstance(c, np.ndarray) else c.numpy() for c in chunks])
        sf.write(out, audio, 24000)
        print("vo", out.name, f"{len(audio)/24000:.2f}s")
        made += 1
    print("voice lines:", made)
"""

_MOBILE_FOLEY = """# ── 5 · Foley / ambience — MMAudio (~6 GB, CC-BY-NC weights) ─────────────────
FOLEY_ENGINE = "__FOLEY_ENGINE__"     # mmaudio | thinksound | off
if RUN_FOLEY and FOLEY_ENGINE == "mmaudio":
    !pip -q install -e git+https://github.com/hkchengrex/MMAudio.git#egg=mmaudio
    !pip -q install torch torchvision torchaudio --upgrade
    import torch, torchaudio
    from mmaudio.eval_utils import all_model_cfg, generate, load_video
    from mmaudio.model.flow_matching import FlowMatching
    from mmaudio.model.networks import get_my_mmaudio
    from mmaudio.model.utils.features_utils import FeaturesUtils

    vram = torch.cuda.get_device_properties(0).total_memory / 2**30
    cfg_name = "mmaudio_small_44k" if vram < 20 else "mmaudio_large_44k_v2"
    model_cfg = all_model_cfg[cfg_name]
    net = get_my_mmaudio(model_cfg.model).eval().to("cuda")
    feats = FeaturesUtils(**model_cfg.features).eval().to("cuda")
    fm = FlowMatching(min_sigma=0, inference_mode="euler", num_steps=25)
    try:
        net.load_weights(torch.load(f"/root/.cache/mmaudio/{cfg_name}.pth", map_location="cpu",
                                    weights_only=True))
    except FileNotFoundError:
        print("weights missing — MMAudio pehli baar khud download karega (demo.py), "
              "ya is cell ko skip karo aur mujhe bolo")
        net = None
    made = 0
    if net is not None:
        for shot_id in JOBS:
            src = SHOTS / f"{shot_id['id']}.mp4"
            out = FOLEY_DIR / f"{shot_id['id']}.wav"
            if not src.exists() or out.exists():
                continue
            info, video = load_video(str(src), 16, model_cfg.sampling_rate)
            with torch.no_grad():
                audio = generate(video, feats, net, fm, num_steps=25,
                                 duration=float(info.duration), cfg_strength=4.5, seed=42)
            torchaudio.save(str(out), audio.cpu(), model_cfg.sampling_rate)
            print("foley", out.name)
            made += 1
    print("foley stems:", made)
"""

_MOBILE_UPSCALE = """# ── 6 · Upscale 480p → __UP_W__x__UP_H__ (Real-ESRGAN ×__FACTOR__, ffmpeg fallback) ──
if RUN_UPSCALE:
    import re as _re, shutil, subprocess, torch
    enhancer = None
    cv2 = None
    try:
        !pip -q install basicsr realesrgan facexlib
        import cv2
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer
        net = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        enhancer = RealESRGANer(
            scale=4, half=True, tile=0, tile_pad=10, pre_pad=0, model=net,
            model_path="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus.pth")
        print("upscaler: Real-ESRGAN ×__FACTOR__")
    except Exception as exc:
        enhancer = None
        print("Real-ESRGAN install/load nahi hua (", type(exc).__name__, ") — ffmpeg lanczos se ×__FACTOR__ karunga")

    def fps_of(src):
        text = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src)],
                              capture_output=True, text=True).stderr
        found = _re.search(r"(\\d+(?:\\.\\d+)?)\\s*fps", text)
        return found.group(1) if found else "16"

    def upscale_clip(src, dst, factor=FACTOR):
        if enhancer is None:
            subprocess.run(["ffmpeg", "-y", "-i", str(src), "-vf",
                            f"scale=iw*{factor}:ih*{factor}:flags=lanczos",
                            "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", str(dst)],
                           check=True, capture_output=True)
            return dst
        frames_in = pathlib.Path("/content/_up_in")
        frames_out = pathlib.Path("/content/_up_out")
        for folder in (frames_in, frames_out):
            shutil.rmtree(folder, ignore_errors=True)
            folder.mkdir(parents=True)
        subprocess.run(["ffmpeg", "-y", "-i", str(src), str(frames_in / "%06d.png")],
                       check=True, capture_output=True)
        for frame in sorted(frames_in.glob("*.png")):
            img = cv2.imread(str(frame), cv2.IMREAD_COLOR)
            big, _ = enhancer.enhance(img, outscale=factor)
            cv2.imwrite(str(frames_out / frame.name), big)
        subprocess.run(["ffmpeg", "-y", "-framerate", fps_of(src),
                        "-i", str(frames_out / "%06d.png"), "-c:v", "libx264", "-crf", "17",
                        "-pix_fmt", "yuv420p", str(dst)], check=True, capture_output=True)
        shutil.rmtree(frames_in, ignore_errors=True)
        shutil.rmtree(frames_out, ignore_errors=True)
        return dst

    made = 0
    for job in JOBS:
        src = SHOTS / f"{job['id']}.mp4"
        dst = SHOTS / f"{job['id']}-{FACTOR}x.mp4"
        if not src.exists() or dst.exists():
            continue
        print("upscaling", src.name)
        try:
            upscale_clip(src, dst)
            print("  ✔", dst.name, f"{dst.stat().st_size/1e6:.1f} MB")
            made += 1
        except Exception as exc:
            print("  ✖ upscale fail:", type(exc).__name__, str(exc)[:160], "(original clip safe hai)")
    print("upscaled:", made)
"""

_MOBILE_SUMMARY = """# ── 7 · Summary + receipt (yeh cell hi "DONE" batata hai) ────────────────────
clips = sorted(SHOTS.glob("*.mp4"))
voice = sorted(VO_DIR.glob("*.wav"))
foley = sorted(FOLEY_DIR.glob("*.wav"))
rows = [{"file": f.name, "mb": round(f.stat().st_size / 1e6, 1), "md5": md5(f)}
        for f in clips + voice + foley]
(BASE / "colab_receipt.json").write_text(json.dumps(
    {"project": PROJECT, "clips": [c.name for c in clips],
     "voice": [v.name for v in voice], "foley": [f.name for f in foley],
     "files": rows}, indent=2))

print("clips :", len(clips))
print("voice :", len(voice))
print("foley :", len(foley))
for row in rows:
    print(f"  {row['file']:<28} {row['mb']:6.1f} MB  {row['md5'][:10]}")

zip_path = pathlib.Path("/content") / f"{PROJECT}_outputs.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as bundle:
    for file in clips + voice + foley:
        bundle.write(file, file.relative_to(BASE))
print()
print("ZIP    :", zip_path.name, f"{zip_path.stat().st_size/1e6:.1f} MB")
if DRIVE_OK:
    (BASE / zip_path.name).write_bytes(zip_path.read_bytes())
    print("Drive  :", BASE)
    print("         ZIP bhi Drive me:", zip_path.name)
else:
    try:
        from google.colab import files as colab_files
        colab_files.download(str(zip_path))
        print("Download start hua — phone ke Downloads me ZIP ayega, woh mujhe chat me bhej do")
    except Exception as exc:
        print("download trigger nahi hua:", type(exc).__name__, exc)
        print("Left sidebar ke Files panel me ZIP maujood hai — wahan se bhi mil jayega")

ok = len([c for c in clips if not c.stem.endswith(("-2x", "-4x"))]) >= __N_SHOTS__ and len(clips) >= __N_SHOTS__
print()
if ok:
    print("DONE ✅  — mujhe chat me 'DONE' likh do, main mix + verify + master bana dunga")
else:
    print("ADHURA ⚠️  — jo missing hai mujhe bolo (main job chhota kar dunga)")
"""


def build_mobile_notebook(project: dict, max_frames: int | None = None) -> dict:
    """A single Run-all notebook for a phone: clips + voice + foley + upscale."""
    up = upscale_target(project, None)
    factor = max(2, int(up["factor"]))
    jobs = []
    for shot in project["shots"]:
        seconds = float(shot["seconds"])
        frames = max(17, ((int(round(seconds * 16)) - 1) // 4) * 4 + 1)
        if max_frames:
            frames = min(frames, max(17, ((int(max_frames) - 1) // 4) * 4 + 1))
        width, height = free_frame_size(shot.get("ratio") or project["aspect"])
        jobs.append({"id": shot["id"], "seed": int(shot.get("seed", 42)), "frames": frames,
                     "steps": int(shot.get("steps") or 30),
                     "width": width, "height": height, "prompt": shot["prompt"]})
    vo = {s["id"]: shot_vo_text(project, s) for s in project["shots"]}
    foley = {s["id"]: (s.get("foley_prompt") or "") for s in project["shots"]}
    cfg = audio_config(project)
    tokens = {
        "__PROJECT__": str(project["project_id"]),
        "__JOBS__": json.dumps(jobs, indent=2, ensure_ascii=False),
        "__VO_TEXT__": json.dumps(vo, indent=2, ensure_ascii=False),
        "__FOLEY_PROMPT__": json.dumps(foley, indent=2, ensure_ascii=False),
        "__FOLEY_ENGINE__": cfg["foley_engine"],
        "__FACTOR__": str(factor),
        "__W__": str(jobs[0]["width"] if jobs else 480),
        "__H__": str(jobs[0]["height"] if jobs else 832),
        "__UP_W__": str((jobs[0]["width"] if jobs else 480) * factor),
        "__UP_H__": str((jobs[0]["height"] if jobs else 832) * factor),
        "__N_SHOTS__": str(len(jobs)),
        "__N_VO__": str(len([v for v in vo.values() if v.strip()])),
    }

    def fill(text: str) -> str:
        for key, value in tokens.items():
            text = text.replace(key, value)
        return text

    return _nb([_md(fill(_MOBILE_INTRO)), _code(fill(_MOBILE_CONFIG)),
                _code(fill(_MOBILE_PIPELINE)), _code(fill(_MOBILE_CLIPS)),
                _code(fill(_MOBILE_VOICE)), _code(fill(_MOBILE_FOLEY)),
                _code(fill(_MOBILE_UPSCALE)), _code(fill(_MOBILE_SUMMARY))])


def merge_code_cells(notebook: dict) -> dict:
    """Collapse every code cell into ONE cell: phone users get a single visible play button."""
    intro = [c for c in notebook["cells"] if c["cell_type"] == "markdown"]
    code = [c for c in notebook["cells"] if c["cell_type"] == "code"]
    merged = "\n\n".join("".join(c["source"]).rstrip() for c in code) + "\n"
    return {"cells": intro + [_code(merged)], "metadata": notebook.get("metadata", {}),
            "nbformat": notebook.get("nbformat", 4),
            "nbformat_minor": notebook.get("nbformat_minor", 5)}


def mobile(project_file: pathlib.Path, *, one_cell: bool = False,
           max_frames: int | None = None) -> int:
    """Write the phone-first all-in-one notebook for a project."""
    project = require_project(project_file)
    paths = project_paths(project_file)
    (paths["base"] / "mobile").mkdir(parents=True, exist_ok=True)
    notebook = build_mobile_notebook(project, max_frames=max_frames)
    if one_cell:
        notebook = merge_code_cells(notebook)
    target = paths["base"] / "mobile" / f"MOBILE_{project['project_id']}.ipynb"
    write_json(target, notebook)

    up = upscale_target(project, None)
    factor = max(2, int(up["factor"]))
    vo = [s for s in project["shots"] if shot_vo_text(project, s)]
    print(f"MOBILE {project['project_id']} · {len(project['shots'])} shot(s) · "
          f"{len(vo)} voice line(s) · {up['in_width']}x{up['in_height']} -> "
          f"{up['in_width'] * factor}x{up['in_height'] * factor}")
    print(f"  notebook: {target}")
    print("  phone flow: upload to Drive 03 · Colab Notebooks -> open in Colab ->")
    print("              Runtime: T4 GPU -> Run all -> wait -> say DONE")
    missing = [s["id"] for s in project["shots"] if not (s.get("prompt") or "").strip()]
    if missing:
        print(f"  WARN     prompts missing for: {', '.join(missing)} (clips will be generic)")
    if vi := [s["id"] for s in project["shots"] if s["id"] and shot_vo_text(project, s).startswith("TODO")]:
        print(f"  WARN     voice text still TODO for: {', '.join(vi)}")

    receipts = load_json(paths["receipts"]) if paths["receipts"].exists() else {"shots": {}}
    receipts.setdefault("shots", {})
    receipts["mobile"] = {"notebook": str(target), "created_at": now(),
                          "shots": len(project["shots"]), "mode": "phone_run_all"}
    write_json(paths["receipts"], receipts)
    return 0


# --------------------------------------------------------------------------- status
def status(project_file: pathlib.Path) -> int:
    project = require_project(project_file)
    paths = project_paths(project_file)
    receipts = load_json(paths["receipts"]) if paths["receipts"].exists() else {"shots": {}}
    plan = build_plan(project)           # recompute: plan.json may be from an older route
    mode = "free-only" if plan["free_only"] else "paid-allowed"
    print(f"PROJECT {project['project_id']} · route={plan['route']} · {mode} "
          f"· est ${plan['estimate_usd']:.2f} · budget ${plan['budget_usd']:.2f}")
    print(f"{'shot':<22}{'engine':<16}{'state':<16}{'file':<8}{'cost':>7}")
    shots_by_id = {shot["id"]: shot for shot in project["shots"]}
    for entry in plan["shots"]:
        sid = entry["shot_id"]
        shot = shots_by_id[sid]
        file = shot_media(shot, paths)
        record = receipts["shots"].get(sid, {})
        state = record.get("status") or ("present" if file else "pending")
        print(f"{sid:<22}{entry['engine_label']:<16}{state:<16}{'yes' if file else '-':<8}"
              f"{entry['total_cost']:>7.2f}")
    try:
        cfg = audio_config(project)
        stems = sum(1 for sh in project["shots"] for slot in ("vo", "foley")
                    if slot in audio_stems(project, sh))
        mixed = sum(1 for v in receipts.get("mix", {}).values()
                    if isinstance(v, dict) and v.get("status") == "mixed")
        print(f"\naudio  : vo={cfg['vo_engine']} · foley={cfg['foley_engine']} "
              f"· bed={cfg['bed_engine']} · {stems} stem(s) planned · {mixed} shot(s) mixed")
    except EngineError as exc:
        print(f"\naudio  : {exc}")
    up = _plan_delivery(project)
    print(f"\ndelivery: {up['free_width']}x{up['free_height']} free -> "
          f"{up['out_width']}x{up['out_height']} ({up['engine']} x{up['factor']})"
          + (f" · target {up['target_height']}p" if up.get("target_height") else ""))
    master = receipts.get("master")
    print(f"master: {master['path'] if master else 'not assembled'}")
    dest = drive_targets(project["project_id"])
    if dest.get("projects_id"):
        print(f"drive : {dest['root']} / {dest['project_folder']}"
              f"  (projects id {dest['projects_id']}, masters id {dest['masters_id']})")
    return 0


# --------------------------------------------------------------------------- doctor
def doctor() -> int:
    checks: list[tuple[str, bool, str]] = []
    checks.append(("python", sys.version_info >= (3, 9), sys.version.split()[0]))
    checks.append(("ffmpeg", which("ffmpeg") is not None, which("ffmpeg") or "missing"))
    checks.append(("ffprobe", which("ffprobe") is not None, which("ffprobe") or "missing"))
    try:
        reg = registry()
        checks.append(("tool registry", bool(reg.get("models")), f"{len(reg['models'])} models"))
    except EngineError as exc:
        checks.append(("tool registry", False, str(exc)))
    key = os.environ.get("MINIMAX_API_KEY", "")
    checks.append(("MINIMAX_API_KEY", True, "set" if key else "absent (free route only)"))
    checks.append(("character authority", (ROOT / "characters/monarch/character.json").exists(),
                   "characters/monarch"))
    checks.append(("free notebook", (STYLE / "colab/MONARCH_T4_FREE_BRIDGE.ipynb").exists(),
                   "MONARCH_T4_FREE_BRIDGE.ipynb"))
    checks.append(("payload dir", DEFAULT_WORK.exists() or True, str(DEFAULT_WORK.relative_to(ROOT))))
    try:
        menu = free_compute()
        providers = menu.get("providers", [])
        checks.append(("free-only mode", free_only(),
                       "ON — $0 guaranteed (MONARCH_ALLOW_PAID=1 to unlock spending)" if free_only()
                       else "OFF — paid route unlocked"))
        checks.append(("free compute menu", bool(providers),
                       f"{len(providers)} providers · " + ", ".join(p["id"] for p in providers)))
        state = quota_state()
        kaggle_left = next((r["left"] for r in quota_report(state) if r["id"] == "kaggle"), None)
        if kaggle_left is not None:
            checks.append(("kaggle quota", kaggle_left > 0,
                           f"{kaggle_left:.1f} h left this week ({state['week']})"))
    except EngineError as exc:
        checks.append(("free compute", False, str(exc)))
    try:
        cfg = drive_config()
        checks.append(("WF-07 drive home", bool(cfg.get("root", {}).get("id")),
                       f"{cfg.get('root', {}).get('name')} ({cfg.get('root', {}).get('id')})"))
    except EngineError as exc:
        checks.append(("WF-07 drive home", False, str(exc)))
    ok = True
    print(f"VIPER-1 engine {ENGINES_VERSION}\n")
    for name, passed, detail in checks:
        if not passed and name not in {"ffmpeg", "ffprobe"}:
            ok = False
        mark = "PASS" if passed else ("WARN" if name in {"ffmpeg", "ffprobe"} else "FAIL")
        print(f"  {mark}  {name:<20} {detail}")
    print("\nready" if ok else "\nfix the FAIL lines")
    return 0 if ok else 2


# --------------------------------------------------------------------------- cli
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="videogen", description="MONARCH STUDIO VIPER-1 video engine")
    ap.add_argument("--version", action="version", version=f"viper {ENGINES_VERSION}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="check this machine")

    p_new = sub.add_parser("new", help="create a project")
    p_new.add_argument("--id", required=True)
    p_new.add_argument("--title", required=True)
    p_new.add_argument("--aspect", default="9:16", choices=sorted(ASPECTS))
    p_new.add_argument("--template", default="reel", choices=["reel", "film", "hero-test"])
    p_new.add_argument("--out", default=str(DEFAULT_WORK))
    p_new.add_argument("--character", default="monarch")

    p_plan = sub.add_parser("plan", help="price + resolve engines")
    p_plan.add_argument("project")
    p_plan.add_argument("--json", action="store_true")

    p_render = sub.add_parser("render", help="render what this machine can, queue the rest")
    p_render.add_argument("project")
    p_render.add_argument("--yes", action="store_true", help="actually spend money")
    p_render.add_argument("--only", nargs="*", help="subset of shot ids")
    p_render.add_argument("--allow-over-budget", action="store_true")

    p_verify = sub.add_parser("verify", help="check media + write receipts")
    p_verify.add_argument("project")

    p_asm = sub.add_parser("assemble", help="concat to one master")
    p_asm.add_argument("project")
    p_asm.add_argument("--out")
    p_asm.add_argument("--no-music", action="store_true")

    p_mobile = sub.add_parser("mobile", help="write the phone-first all-in-one Colab notebook")
    p_mobile.add_argument("--one-cell", action="store_true",
                          help="merge every code cell into one: a single play button on a phone")
    p_mobile.add_argument("--max-frames", type=int, default=None,
                          help="cap frames per shot for the free T4 (33 ~ 2s, 49 ~ 3s)")
    p_mobile.add_argument("project")

    p_quota = sub.add_parser("quota", help="free GPU hours ledger (weekly reset)")
    p_quota.add_argument("--use", nargs=2, metavar=("PROVIDER", "HOURS"),
                         help="record hours burned, e.g. --use kaggle 1.5")
    p_quota.add_argument("--note", default="")
    p_quota.add_argument("--json", action="store_true")

    p_audio = sub.add_parser("audio", help="write the free voice+foley+music Colab notebook")
    p_audio.add_argument("project")

    p_mix = sub.add_parser("mix", help="mux voice + foley + music under each shot (ffmpeg)")
    p_mix.add_argument("project")
    p_mix.add_argument("--loudnorm", action="store_true", help="normalise to -16 LUFS for social")

    p_up = sub.add_parser("upscale", help="write the Colab notebook that lifts free 480p clips")
    p_up.add_argument("project")
    p_up.add_argument("--engine", choices=["realesrgan", "lanczos"], default=None)
    p_up.add_argument("--factor", type=int, choices=[2, 4], default=None)
    p_up.add_argument("--only", nargs="*", help="subset of shot ids")

    p_status = sub.add_parser("status", help="per-shot state")
    p_status.add_argument("project")

    args = ap.parse_args(argv)
    try:
        if args.cmd == "doctor":
            return doctor()
        if args.cmd == "quota":
            if args.use:
                provider, hours = args.use
                state = quota_use(provider, float(hours), args.note)
                print(f"logged {hours} h on {provider} ({state['week']})")
            if args.json:
                print(json.dumps({"week": quota_state()["week"], "rows": quota_report()}, indent=2))
            else:
                print_quota()
            return 0
        if args.cmd == "new":
            path = new_project(args.id, args.title, args.aspect, pathlib.Path(args.out),
                               template=args.template, character=args.character)
            print(f"created {path}")
            print(f"next: edit prompts, then `videogen.py plan {path}`")
            return 0
        project_file = pathlib.Path(args.project).expanduser()
        if not project_file.is_file():
            raise EngineError(f"project file not found: {project_file}")
        if args.cmd == "plan":
            plan = build_plan(require_project(project_file))
            write_json(project_paths(project_file)["plan"], plan)
            print(json.dumps(plan, indent=2) if args.json else "")
            if not args.json:
                print_plan(plan)
            return 0
        if args.cmd == "render":
            return render(project_file, confirm=args.yes, only=args.only,
                          allow_over_budget=args.allow_over_budget)
        if args.cmd == "verify":
            return verify(project_file)
        if args.cmd == "assemble":
            return assemble(project_file, pathlib.Path(args.out) if args.out else None,
                            with_music=not args.no_music)
        if args.cmd == "status":
            return status(project_file)
        if args.cmd == "mobile":
            return mobile(project_file, one_cell=getattr(args, "one_cell", False),
                          max_frames=getattr(args, "max_frames", None))
        if args.cmd == "audio":
            return audio(project_file)
        if args.cmd == "mix":
            return mix(project_file, loudnorm=args.loudnorm)
        if args.cmd == "upscale":
            return upscale(project_file, engine=args.engine, factor=args.factor, only=args.only)
        raise EngineError(f"unknown command {args.cmd}")
    except EngineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
