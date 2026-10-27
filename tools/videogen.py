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
DEFAULT_WORK = ROOT / "workflows" / "current" / "payload"

SCHEMA_VERSION = 1
ENGINES_VERSION = "viper-1.0"

ASPECTS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}
H3_RATIOS = {"9:16", "16:9", "1:1", "21:9", "4:3", "3:4"}
FREE_T4_HW = {"width": 832, "height": 480}          # Wan 1.3B landscape default
FREE_T4_PORTRAIT = {"width": 480, "height": 832}    # vertical cut of the same budget
RETRY_BUFFER = 1.5


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
    return shutil.which(binary)


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
        "notes": "Edit prompts, drop the Monarch reference pack into shots/, then: plan -> render -> verify.",
        "audio": {"music": None, "dialogue": []},
        "shots": shots,
    }
    write_json(project_dir / "project.json", project)
    for key in ("shots", "queue", "lipsync", "delivery"):
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


def plan_shot(shot: dict, project: dict, *, has_key: bool) -> dict:
    """Resolve one shot into ordered steps (engine + action + cost)."""
    route = project.get("route", "auto")
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
                      "note": "hosted API: native stereo audio + lipsync in one pass"})
        return {"shot_id": shot["id"], "kind": kind, "steps": steps,
                "total_cost": steps[0]["cost"], "engine_label": f"h3-{resolution}"}

    # free chain: a silent clip from the T4 queue; heroes then get a lipsync pass
    steps.append({"engine": "wan", "action": "queue", "cost": 0.0,
                  "note": "free Colab T4 job (480p, silent) — run the notebook queue cell"})
    if kind == "hero":
        steps.append({"engine": "latentsync", "action": "lipsync", "cost": 0.0,
                      "note": "free lipsync pass with your own voice track"})
    return {"shot_id": shot["id"], "kind": kind, "steps": steps,
            "total_cost": 0.0, "engine_label": "free-chain"}


def build_plan(project: dict, *, has_key: bool | None = None) -> dict:
    if has_key is None:
        has_key = bool(os.environ.get("MINIMAX_API_KEY"))
    entries = [plan_shot(shot, project, has_key=has_key) for shot in project["shots"]]
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
    if not any(s["total_cost"] for s in entries) and project.get("route") == "paid":
        warnings.append("route=paid but no paid steps resolved — add an API key?")
    return warnings


def print_plan(plan: dict) -> None:
    print(f"PROJECT   : {plan['project_id']}  (route={plan['route']}, {plan['shot_count']} shots)")
    print(f"{'shot':<22}{'engine':<16}{'steps':<34}{'cost':>8}")
    for entry in plan["shots"]:
        steps = " -> ".join(f"{s['engine']}:{s['action']}" for s in entry["steps"])
        print(f"{entry['shot_id']:<22}{entry['engine_label']:<16}{steps:<34}{entry['total_cost']:>8.2f}")
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
    portrait = project["aspect"] in {"9:16", "4:5"}
    size = FREE_T4_PORTRAIT if portrait else FREE_T4_HW
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


# --------------------------------------------------------------------------- verify
def shot_media(shot: dict, paths: dict) -> pathlib.Path | None:
    """Return the finished media for a shot, if any.

    The free chain writes a lipsynced version next to the silent clip (``<id>-talk.mp4``),
    so the talk version wins when both exist.
    """
    candidates = [paths["shots"] / f"{shot['id']}-talk.mp4", paths["shots"] / f"{shot['id']}.mp4"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def probe(path: pathlib.Path) -> dict:
    ffprobe = which("ffprobe")
    if not ffprobe:
        return {"available": False}
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
        else:
            record["probe"] = {"available": False, "note": "ffprobe missing: existence/md5 checked only"}
        receipts["shots"].setdefault(sid, {}).update(record)
        if problems:
            failures.append(f"{sid}: " + "; ".join(problems))
            print(f"  WARN  {sid:<20} " + "; ".join(problems))
        else:
            checked += 1
            print(f"  PASS  {sid:<20} {record['bytes'] / 1e6:6.1f} MB  md5 {record['md5'][:10]}")

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
    cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-r", str(fps),
           "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p"]
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
    if info.get("available"):
        print(f"        {info.get('width')}x{info.get('height')} @ {info.get('fps')} fps, "
              f"{info.get('duration'):.2f}s, audio={info.get('audio_codec')}")
    return 0


# --------------------------------------------------------------------------- status
def status(project_file: pathlib.Path) -> int:
    project = require_project(project_file)
    paths = project_paths(project_file)
    receipts = load_json(paths["receipts"]) if paths["receipts"].exists() else {"shots": {}}
    plan = build_plan(project)           # recompute: plan.json may be from an older route
    print(f"PROJECT {project['project_id']} · route={plan['route']} · est ${plan['estimate_usd']:.2f} "
          f"· budget ${plan['budget_usd']:.2f}")
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
    master = receipts.get("master")
    print(f"\nmaster: {master['path'] if master else 'not assembled'}")
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

    p_status = sub.add_parser("status", help="per-shot state")
    p_status.add_argument("project")

    args = ap.parse_args(argv)
    try:
        if args.cmd == "doctor":
            return doctor()
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
        raise EngineError(f"unknown command {args.cmd}")
    except EngineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
