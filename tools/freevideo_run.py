#!/usr/bin/env python3
"""freevideo_run — MiniMax H3 (FreeVideo) se scenes render karo, GPU box par.

Yeh wohi tareeqa hai jo owner ne kaha: pehle image (keyframe), phir us ko animate.
FreeVideo H3 image-conditioning leta hai (task `i2va` = image + text se video **aur audio**).

Chalane ki jagah: koi bhi NVIDIA Ampere/Ada/Hopper machine (int8/FP8 path), e.g.
Lightning AI ka free L4/A10G Studio. Colab ka T4 (SM75) is par nahi chalta.

    python3 tools/freevideo_run.py --job cloud/freevideo_jobs/stick-h3.json \
        --out ~/monarch-clips --work ~/FreeVideo

Har scene ke baad `receipts.json` update hota hai; resume-safe hai (jo clip bani, skip).
GITHUB_TOKEN mila ho to har clip apni branch `fv-<job>-<scene>` par bhi chali jati hai,
phir agent usay `tools/freevideo_fetch.py` se utha leta hai.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

FREEVIDEO_REPO = "https://github.com/FlashML-org/FreeVideo.git"
MIN_DRIVER = 580
OK_ARCH = {"86", "89", "90", "100", "120"}     # Ampere, Ada, Hopper, Blackwell


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def sh(cmd: list[str] | str, cwd: pathlib.Path | None = None, check: bool = True,
       env: dict | None = None) -> subprocess.CompletedProcess:
    if isinstance(cmd, str):
        cmd = ["bash", "-lc", cmd]
    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True,
                          env={**os.environ, **(env or {})})
    if check and proc.returncode != 0:
        tail = "\n".join((proc.stderr or proc.stdout).strip().splitlines()[-12:])
        raise RuntimeError(f"command fail ({proc.returncode}): {' '.join(cmd[:4])}\n{tail}")
    return proc


def md5(path: pathlib.Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# preflight
# --------------------------------------------------------------------------- #

def preflight() -> dict:
    if not shutil.which("nvidia-smi"):
        raise SystemExit("nvidia-smi nahi mila — GPU machine par chalayein (Colab T4 bhi kaam nahi karega).")
    q = ("nvidia-smi --query-gpu=name,memory.total,compute_cap,driver_version "
         "--format=csv,noheader,nounits").split()
    rows = [line.split(",") for line in sh(q).stdout.strip().splitlines() if line.strip()]
    if not rows:
        raise SystemExit("koi GPU nahi mila")
    name, vram, cap, driver = (x.strip() for x in rows[0])
    info = {"gpu": name, "vram_gb": round(float(vram) / 1024, 1), "compute_cap": cap,
            "driver": driver}
    log(f"GPU: {name} | {info['vram_gb']} GB | SM {cap} | driver {driver}")
    if int(float(driver)) < MIN_DRIVER:
        raise SystemExit(f"driver {driver} purana hai — FreeVideo {MIN_DRIVER}+ maangta hai")
    if cap.split(".")[0] + ("" if len(cap.split(".")) == 1 else cap.split(".")[1]) not in OK_ARCH:
        raise SystemExit(f"compute capability {cap} supported nahi (chahiye Ampere/Ada/Hopper/Blackwell)")
    free = shutil.disk_usage("/").free / 1e9
    log(f"disk free: {free:.0f} GB")
    if free < 60:
        raise SystemExit("disk kam hai — models ke liye ~60 GB chahiye")
    return info


def ensure_freevideo(work: pathlib.Path) -> pathlib.Path:
    """Repo clone + setup. Pehle se install ho to skip."""
    exe = work / "freevideo"
    if exe.exists() and (work / "freevideo_engine").exists():
        log(f"FreeVideo already present: {work}")
        return work
    work.parent.mkdir(parents=True, exist_ok=True)
    if not work.exists():
        log(f"cloning FreeVideo -> {work}")
        sh(["git", "clone", "--depth", "1", FREEVIDEO_REPO, str(work)])
    log("setup.sh chala rahe hain (runtime + models — 20-40 min lag sakte hain)")
    sh("./setup.sh", cwd=work)
    if not exe.exists():
        raise SystemExit(f"setup ke baad {exe} nahi mila")
    return work


# --------------------------------------------------------------------------- #
# generation
# --------------------------------------------------------------------------- #

def media_json(scene: dict, path: pathlib.Path) -> pathlib.Path | None:
    """H3 ka media request (v1): pehla frame = stickman keyframe."""
    image = scene.get("image")
    if not image:
        return None
    img = pathlib.Path(image).expanduser()
    if not img.is_absolute():
        img = pathlib.Path(__file__).resolve().parent.parent / img
    if not img.exists():
        raise FileNotFoundError(f"keyframe nahi mila: {img}")
    payload = {"version": 1, "first": str(img)}
    path.write_text(json.dumps(payload, indent=2))
    return path


def generate_scene(fv: pathlib.Path, job: dict, scene: dict, out: pathlib.Path,
                   workdir: pathlib.Path) -> pathlib.Path:
    clip = out / f"{scene['id']}.mp4"
    prompt_file = workdir / f"{scene['id']}.txt"
    prompt = scene["prompt"]
    if job.get("style") and job["style"] not in prompt:
        prompt = f"{prompt} {job['style']}".strip()
    prompt_file.write_text(prompt + "\n")
    media = media_json(scene, workdir / f"{scene['id']}.media.json")

    cmd = ["./freevideo", "generate", "--prompt-file", str(prompt_file), "--out", str(clip),
           "--width", str(int(scene.get("width", job.get("width", 768)))),
           "--height", str(int(scene.get("height", job.get("height", 1344)))),
           "--seconds", str(float(scene.get("seconds", job.get("seconds", 3.0)))),
           "--seed", str(int(scene.get("seed", 7)))]
    if media:
        cmd += ["--media", str(media)]
    if job.get("steps"):
        cmd += ["--base-steps", str(int(job["steps"]))]
    if job.get("no_two_pass"):
        cmd += ["--no-two-pass"]

    log(f"{scene['id']}: {cmd[2]} ... {' '.join(cmd[3:])[:160]}")
    started = time.time()
    sh(cmd, cwd=fv)
    if not clip.exists() or clip.stat().st_size < 20000:
        raise RuntimeError(f"{scene['id']}: output file nahi bani")
    log(f"{scene['id']}: OK in {(time.time() - started) / 60:.1f} min "
        f"({clip.stat().st_size / 1e6:.1f} MB)")
    return clip


def publish(clip: pathlib.Path, job_id: str, scene_id: str) -> str | None:
    """Clip ko apni git branch par bhejo (taake agent utha sake)."""
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "adil-chandio/Monarch-Studio")
    if not token:
        return None
    branch = f"fv-{job_id}-{scene_id}"
    tmp = pathlib.Path("/tmp/fvpub")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    shutil.copy2(clip, tmp / clip.name)
    receipt = clip.with_suffix(".receipt.json")
    if receipt.exists():
        shutil.copy2(receipt, tmp / "receipt.json")
    sh(["git", "init", "-q"], cwd=tmp)
    sh(["git", "config", "user.email", "cloud@monarch.local"], cwd=tmp)
    sh(["git", "config", "user.name", "Monarch Cloud"], cwd=tmp)
    sh(["git", "add", "-A"], cwd=tmp)
    sh(["git", "commit", "-q", "-m", f"freevideo: {job_id} {scene_id}"], cwd=tmp)
    url = f"https://x-access-token:{token}@github.com/{repo}.git"
    sh(["git", "push", "--quiet", "--force", url, f"HEAD:refs/heads/{branch}"], cwd=tmp)
    log(f"{scene_id}: published -> {branch}")
    return branch


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="freevideo_run")
    ap.add_argument("--job", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", default=str(pathlib.Path.home() / "FreeVideo"))
    ap.add_argument("--only", default="", help="k01,k02 (subset)")
    ap.add_argument("--skip-setup", action="store_true")
    args = ap.parse_args(argv)

    job = json.loads(pathlib.Path(args.job).read_text())
    job_id = job.get("id", "job")
    out = pathlib.Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    workdir = out / "work"
    workdir.mkdir(exist_ok=True)

    hw = preflight()
    fv = pathlib.Path(args.work).expanduser()
    if not args.skip_setup:
        fv = ensure_freevideo(fv)

    wanted = [s for s in job["scenes"] if not args.only or s["id"] in args.only.split(",")]
    receipts = []
    receipt_path = out / "receipts.json"
    for n, scene in enumerate(wanted, 1):
        clip = out / f"{scene['id']}.mp4"
        if clip.exists() and clip.stat().st_size > 20000:
            log(f"[{n}/{len(wanted)}] {scene['id']}: already done, skip")
            continue
        log(f"[{n}/{len(wanted)}] {scene['id']}: render")
        try:
            generate_scene(fv, job, scene, out, workdir)
            row = {"scene": scene["id"], "file": clip.name,
                   "bytes": clip.stat().st_size, "md5": md5(clip),
                   "state": "ok", "hardware": hw}
            clip.with_suffix(".receipt.json").write_text(json.dumps(row, indent=2))
            branch = publish(clip, job_id, scene["id"])
            if branch:
                row["branch"] = branch
            receipts.append(row)
        except Exception as exc:                     # noqa: BLE001
            log(f"{scene['id']}: FAIL {type(exc).__name__}: {exc}")
            receipts.append({"scene": scene["id"], "state": "fail",
                             "error": f"{type(exc).__name__}: {str(exc)[:400]}"})
        receipt_path.write_text(json.dumps(receipts, indent=2))

    ok = [r for r in receipts if r["state"] == "ok"]
    log(f"done: {len(ok)} ok / {len(receipts)} attempted")
    print(json.dumps({"job": job_id, "out": str(out), "receipts": str(receipt_path),
                      "ok": len(ok)}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
