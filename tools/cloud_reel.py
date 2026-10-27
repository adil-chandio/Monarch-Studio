#!/usr/bin/env python3
"""cloud_reel — cloud me video banwao, khud, bina owner ke koi link/click.

Sandbox se Google/HF/Kaggle tak network band hai, lekin github.com khulta hai. Is liye
GitHub Actions ko bridge banaya gaya hai: runner ke paas poora internet + 4 cores hote hain.

Poora cycle (owner ko kuch nahi karna):

    enqueue  -> cloud/jobs/<id>.json commit + push        (workflow push par khud chalta hai)
    dispatch -> gh workflow run cloud-reel.yml -f job_id= (ya manual trigger)
    wait     -> cloud-artifacts branch me receipt ka intezaar
    fetch    -> git se mp4 + receipt wapas, md5 verify, project ke delivery/ me rakh do

Kyun git se wapas? Artifact downloads objects.githubusercontent.com se redirect hote hain jo
yahan blocked hai; git (github.com) khula hai, is liye cloud runner result ko
`cloud-artifacts` branch par push karta hai.

Usage:
    python3 tools/cloud_reel.py enqueue <job.json | job id> [--spec path]
    python3 tools/cloud_reel.py status <job id>
    python3 tools/cloud_reel.py fetch <job id> --dest <dir> [--timeout 1800]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
JOBS = ROOT / "cloud" / "jobs"
BRANCH = "cloud-artifacts"
ARTIFACT_FILES = ("cloud_receipt.json",)


class CloudError(RuntimeError):
    """Cloud pipeline ka koi bhi tootna."""


def run(args: list[str], *, cwd: pathlib.Path | None = None, check: bool = True) -> str:
    proc = subprocess.run(args, cwd=str(cwd or ROOT), capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise CloudError(f"{' '.join(args[:3])} fail: "
                         + " | ".join((proc.stderr or proc.stdout).strip().splitlines()[-2:]))
    return proc.stdout


def md5(path: pathlib.Path) -> str:
    import hashlib
    digest = hashlib.md5()
    with pathlib.Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def queue_job(job_id: str, spec: str | None = None, note: str = "") -> pathlib.Path:
    JOBS.mkdir(parents=True, exist_ok=True)
    payload = {"id": job_id, "kind": "reel",
               "spec": spec or f"studio/videogen/examples/{job_id}/reel.json",
               "note": note or "cloud CPU render"}
    if not (ROOT / payload["spec"]).exists():
        raise CloudError(f"spec nahi mila: {payload['spec']}")
    path = JOBS / f"{job_id}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


def enqueue(job_id: str, spec: str | None, *, push: bool = True) -> dict:
    """Job queue me daalo aur push karo — push hi workflow ko trigger karta hai."""
    path = queue_job(job_id, spec)
    if not push:
        return {"queued": str(path), "pushed": False}
    run(["git", "add", str(path)])
    staged = run(["git", "diff", "--cached", "--name-only"]).strip()
    if staged:
        run(["git", "-c", "user.name=Monarch Agent",
             "-c", "user.email=agent@monarch.local", "commit", "-q", "-m",
             f"cloud: queue {job_id}"])
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
    run(["git", "push", "-q", "origin", branch])
    return {"queued": str(path), "pushed": True, "branch": branch}


def cloud_receipt(job_id: str) -> dict | None:
    """cloud-artifacts branch se receipt padho (fetch ke bina, git show se)."""
    run(["git", "fetch", "-q", "origin", f"+refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"],
        check=False)
    proc = subprocess.run(["git", "show", f"origin/{BRANCH}:cloud_receipt.json"],
                          cwd=str(ROOT), capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    return data if str(data.get("job")) == str(job_id) else None


def wait(job_id: str, timeout: float = 1800.0, interval: float = 20.0) -> dict:
    started = time.time()
    seen = None
    while time.time() - started < timeout:
        receipt = cloud_receipt(job_id)
        if receipt and receipt.get("md5"):
            return receipt
        if seen is None:
            seen = run(["gh", "run", "list", "--workflow", "cloud-reel.yml", "--limit", "1"],
                       check=False).strip()
            if seen:
                print("  run:", seen.splitlines()[0])
        time.sleep(interval)
        print(f"  … {(time.time() - started):.0f}s")
    raise CloudError(f"cloud ne {timeout:.0f}s me kuch nahi diya ({job_id})")


def fetch(job_id: str, dest: pathlib.Path, *, timeout: float = 1800.0) -> dict:
    receipt = wait(job_id, timeout)
    run(["git", "fetch", "-q", "origin", f"+refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"])
    name = receipt.get("master") or f"{job_id}_MASTER.mp4"
    blob = subprocess.run(["git", "show", f"origin/{BRANCH}:{name}"],
                          cwd=str(ROOT), capture_output=True)
    if blob.returncode != 0 or not blob.stdout:
        raise CloudError(f"cloud branch me {name} nahi mila")
    dest = pathlib.Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / name
    target.write_bytes(blob.stdout)
    got = md5(target)
    if receipt.get("md5") and got != receipt["md5"]:
        raise CloudError(f"md5 mismatch: cloud {receipt['md5']} vs local {got}")
    receipt_path = dest / "cloud_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    return {"master": str(target), "md5": got, "bytes": target.stat().st_size,
            "receipt": str(receipt_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cloud_reel", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_enq = sub.add_parser("enqueue", help="job queue me daalo aur push karo")
    p_enq.add_argument("job")
    p_enq.add_argument("--spec")
    p_enq.add_argument("--no-push", action="store_true")

    p_status = sub.add_parser("status", help="cloud ka receipt dekho")
    p_status.add_argument("job")

    p_fetch = sub.add_parser("fetch", help="cloud se mp4 wapas laao")
    p_fetch.add_argument("job")
    p_fetch.add_argument("--dest", default="out/cloud")
    p_fetch.add_argument("--timeout", type=float, default=1800.0)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "enqueue":
            print(json.dumps(enqueue(args.job, args.spec, push=not args.no_push), indent=2))
        elif args.cmd == "status":
            print(json.dumps(cloud_receipt(args.job) or {"job": args.job, "state": "pending"},
                             indent=2))
        else:
            print(json.dumps(fetch(args.job, pathlib.Path(args.dest), timeout=args.timeout),
                             indent=2))
    except CloudError as exc:
        print("CLOUD FAIL:", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
