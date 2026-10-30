#!/usr/bin/env python3
"""publish_delivery — deliver/ ko `deliveries` branch par GitHub API se daal deta hai.

Kyun API: runner par `git push` par branch protection/token scope ke masle aate hain; git data API
(GITHUB_TOKEN + contents:write) se blob -> tree -> commit -> ref, sab ek hi raaste se chalta hai.
Isi branch ka tarball (codeload) agent fetch karta hai aur Drive me daalta hai.

  GITHUB_TOKEN=... python3 tools/publish_delivery.py --dir deliver --branch deliveries
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import subprocess
import sys
import tempfile

API = "https://api.github.com"


def gh(method: str, path: str, payload: dict | None = None) -> dict:
    """curl se (gh CLI ka input size limit 50 MB+ blobs par choke karta hai)."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    cmd = ["curl", "-sS", "-X", method, f"{API}{path}",
           "-H", "Accept: application/vnd.github+json",
           "-H", f"Authorization: Bearer {token}"]
    tmp = None
    if payload is not None:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(payload, tmp)
        tmp.close()
        cmd += ["-H", "Content-Type: application/json", "--data-binary", f"@{tmp.name}"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        if tmp:
            pathlib.Path(tmp.name).unlink(missing_ok=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{method} {path} fail: {proc.stderr.strip()[:400]}")
    body = proc.stdout.strip()
    try:
        data = json.loads(body or "{}")
    except json.JSONDecodeError:
        raise RuntimeError(f"{method} {path} bad response: {body[:300]}")
    if isinstance(data, dict) and data.get("message") and "sha" not in data:
        raise RuntimeError(f"{method} {path} fail: {data.get('message')[:300]}")
    return data


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="publish_delivery")
    ap.add_argument("--dir", default="deliver")
    ap.add_argument("--branch", default="deliveries")
    ap.add_argument("--keep", type=int, default=25, help="is se zyada files skip (safety)")
    args = ap.parse_args(argv)

    repo = os.environ["GITHUB_REPOSITORY"]
    root = pathlib.Path(args.dir)
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files:
        print("deliver khali — kuch publish nahi")
        return 1
    if len(files) > args.keep:
        files = files[: args.keep]

    # purani branch ka tree (agar hai) — warna khali
    base_tree = None
    try:
        ref = gh("GET", f"/repos/{repo}/git/ref/heads/{args.branch}")
        head_sha = ref["object"]["sha"]
        base_tree = gh("GET", f"/repos/{repo}/git/commits/{head_sha}")["tree"]["sha"]
        print(f"existing branch {args.branch} @ {head_sha[:8]}")
    except Exception:                                  # noqa: BLE001
        print(f"naya branch: {args.branch}")

    entries = []
    total = 0
    for path in files:
        data = path.read_bytes()
        total += len(data)
        blob = gh("POST", f"/repos/{repo}/git/blobs", {
            "content": base64.b64encode(data).decode(),
            "encoding": "base64",
        })
        rel = path.relative_to(root).as_posix()
        entries.append({"path": f"{root.name}/{rel}", "mode": "100644",
                        "type": "blob", "sha": blob["sha"]})
        print(f"  blob {path} {len(data) / 1e6:.1f} MB")

    tree = gh("POST", f"/repos/{repo}/git/trees",
              {"tree": entries, **({"base_tree": base_tree} if base_tree else {})})
    commit = gh("POST", f"/repos/{repo}/git/commits", {
        "message": f"delivery: {len(entries)} files ({total / 1e6:.0f} MB)",
        "tree": tree["sha"],
        **({"parents": [head_sha]} if base_tree else {}),
    })
    if base_tree:
        gh("PATCH", f"/repos/{repo}/git/refs/heads/{args.branch}", {"sha": commit["sha"], "force": True})
    else:
        gh("POST", f"/repos/{repo}/git/refs",
           {"ref": f"refs/heads/{args.branch}", "sha": commit["sha"]})
    print(f"published {len(entries)} files ({total / 1e6:.1f} MB) -> {args.branch} @ {commit['sha'][:8]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
