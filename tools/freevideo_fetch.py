#!/usr/bin/env python3
"""freevideo_fetch — FreeVideo scenes ko git branches (`fv-<job>-<scene>`) se wapas laao.

    python3 tools/freevideo_fetch.py stick-h3 --dest studio/films/stick-h3/clips

Har clip ke saath receipt.json aata hai; bytes+md5 match hone par hi likha jata hai.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True)


def branches(job: str) -> dict[str, str]:
    out = git("ls-remote", "--heads", "origin", f"refs/heads/fv-{job}-*").stdout
    found = {}
    for line in out.strip().splitlines():
        sha, ref = line.split("\t")
        found[ref.replace("refs/heads/", "")] = sha
    return found


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def fetch(job: str, dest: pathlib.Path) -> dict:
    dest.mkdir(parents=True, exist_ok=True)
    found = branches(job)
    rows, missing = [], []
    for scene in sorted({b.rsplit("-", 1)[-1] for b in found}):
        branch = f"fv-{job}-{scene}"
        remote = f"refs/remotes/origin/{branch}"
        git("fetch", "-q", "origin", f"+refs/heads/{branch}:{remote}")
        blob = subprocess.run(["git", "show", f"origin/{branch}:{scene}.mp4"], cwd=str(ROOT),
                              capture_output=True)
        if blob.returncode != 0 or len(blob.stdout) < 20000:
            missing.append(scene)
            continue
        data = blob.stdout
        want = None
        meta = subprocess.run(["git", "show", f"origin/{branch}:receipt.json"], cwd=str(ROOT),
                              capture_output=True, text=True)
        if meta.returncode == 0:
            try:
                want = json.loads(meta.stdout).get("md5")
            except json.JSONDecodeError:
                want = None
        got = md5(data)
        if want and want != got:
            missing.append(scene)
            continue
        target = dest / f"{scene}.mp4"
        target.write_bytes(data)
        rows.append({"scene": scene, "file": str(target), "bytes": len(data),
                     "md5": got, "branch": branch})
    return {"job": job, "count": len(rows), "missing": missing, "clips": rows,
            "state": "ready" if rows else "empty"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="freevideo_fetch")
    ap.add_argument("job")
    ap.add_argument("--dest", required=True)
    args = ap.parse_args(argv)
    info = fetch(args.job, pathlib.Path(args.dest))
    print(json.dumps(info, indent=2))
    return 0 if info["count"] else 1


if __name__ == "__main__":
    sys.exit(main())
