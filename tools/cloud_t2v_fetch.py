#!/usr/bin/env python3
"""cloud_t2v_fetch — cloud T2V scenes ko git se wapas laao (branch t2v-<job>-<scene>).

python3 tools/cloud_t2v_fetch.py personality-t2v --dest studio/films/personality-t2v/clips
python3 tools/cloud_t2v_fetch.py personality-t2v --dest ... --wait 3600
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True)


def remote_branches(prefix: str) -> dict[str, str]:
    """Branch name -> sha, sirf t2v-<job>-<scene> branches."""
    out = git("ls-remote", "--heads", "origin", f"refs/heads/{prefix}-*").stdout
    found = {}
    for line in out.strip().splitlines():
        sha, ref = line.split("\t")
        found[ref.replace("refs/heads/", "")] = sha
    return found


def fetch_scene(branch: str, scene: str, dest: pathlib.Path) -> dict:
    blob = subprocess.run(["git", "show", f"origin/{branch}:{scene}.mp4"],
                          cwd=str(ROOT), capture_output=True)
    if blob.returncode != 0 or not blob.stdout:
        raise RuntimeError(f"{branch}: {scene}.mp4 nahi mila")
    receipt_raw = subprocess.run(["git", "show", f"origin/{branch}:receipt.json"],
                                 cwd=str(ROOT), capture_output=True, text=True)
    receipt = json.loads(receipt_raw.stdout) if receipt_raw.returncode == 0 else {}
    target = dest / f"{scene}.mp4"
    target.write_bytes(blob.stdout)
    got = md5(blob.stdout)
    if receipt.get("md5") and receipt["md5"] != got:
        raise RuntimeError(f"{scene}: md5 mismatch ({receipt['md5']} vs {got})")
    return {"scene": scene, "file": str(target), "bytes": target.stat().st_size,
            "md5": got, "branch": branch}


def fetch_all(job: str, dest: pathlib.Path, *, wait: float = 0.0, interval: float = 30.0) -> dict:
    dest = pathlib.Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    started = time.time()
    while True:
        git("fetch", "-q", "origin", f"+refs/heads/t2v-{job}-*:refs/remotes/origin/t2v-{job}-*")
        branches = remote_branches(f"t2v-{job}")
        scenes = sorted(branch.split("-")[-1] for branch in branches)
        have = sorted(p.stem for p in dest.glob("s*.mp4"))
        if scenes:
            print(f"  cloud: {len(scenes)} scene(s) ready · local: {len(have)}", flush=True)
        if scenes:
            break
        if wait and time.time() - started < wait:
            time.sleep(interval)
            continue
        return {"job": job, "scenes": [], "state": "pending"}

    rows, done = [], set()
    for branch, _sha in sorted(branches.items()):
        scene = branch.split("-")[-1]
        if scene in done:
            continue
        if (dest / f"{scene}.mp4").exists() and (dest / f"{scene}.mp4").stat().st_size > 50000:
            rows.append({"scene": scene, "file": str(dest / f"{scene}.mp4"), "cached": True})
            done.add(scene)
            continue
        try:
            rows.append(fetch_scene(branch, scene, dest))
            done.add(scene)
        except RuntimeError as exc:
            print("  !", exc)
    return {"job": job, "scenes": rows, "state": "ready", "count": len(rows)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cloud_t2v_fetch")
    parser.add_argument("job")
    parser.add_argument("--dest", required=True)
    parser.add_argument("--wait", type=float, default=0.0)
    args = parser.parse_args(argv)
    result = fetch_all(args.job, pathlib.Path(args.dest), wait=args.wait)
    print(json.dumps(result, indent=2))
    return 0 if result.get("state") == "ready" else 1


if __name__ == "__main__":
    sys.exit(main())
