#!/usr/bin/env python3
"""push_job_spec — agla job spec repo me daal deta hai (contents API se).

Kyun: `cloud/kaggle_jobs/*.json` ke push par workflow trigger hota hai, is liye ek run ke
aakhir me agla spec likh dene se agla pass **khud** shuru ho jata hai (chain).

    GITHUB_REPOSITORY=... GH_TOKEN=... python3 tools/push_job_spec.py \
        --path cloud/kaggle_jobs/stick-film-hq-b.json --json '{"chunks": [...]}'
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


def gh(method: str, path: str, payload: dict | None = None) -> dict:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    cmd = ["curl", "-sS", "-X", method, f"https://api.github.com{path}",
           "-H", "Accept: application/vnd.github+json", "-H", f"Authorization: Bearer {token}"]
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
        raise RuntimeError(f"{method} {path} fail: {proc.stderr.strip()[:300]}")
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        raise RuntimeError(f"{method} {path} bad response: {proc.stdout[:200]}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="push_job_spec")
    ap.add_argument("--path", required=True)
    ap.add_argument("--json", default="", help="spec JSON (string)")
    ap.add_argument("--json-file", default="")
    ap.add_argument("--branch", default=os.environ.get("GITHUB_REF_NAME", "main"))
    args = ap.parse_args(argv)

    try:
        spec = json.loads(args.json) if args.json else json.loads(pathlib.Path(args.json_file).read_text())
    except Exception as exc:                                  # noqa: BLE001
        print(f"spec parse fail: {exc}")
        return 1
    if not isinstance(spec, dict) or not spec.get("id"):
        print("spec me id chahiye — chain band")
        return 1

    repo = os.environ["GITHUB_REPOSITORY"]
    body = {
        "message": f"chain: {spec['id']} ({len(spec.get('chunks') or [])} chunks)",
        "content": base64.b64encode((json.dumps(spec, indent=2) + "\n").encode()).decode(),
        "branch": args.branch,
    }
    try:
        cur = gh("GET", f"/repos/{repo}/contents/{args.path}?ref={args.branch}")
        if cur.get("sha"):
            body["sha"] = cur["sha"]
    except Exception:                                          # noqa: BLE001
        pass
    out = gh("PUT", f"/repos/{repo}/contents/{args.path}", body)
    commit = (out.get("commit") or {}).get("sha", "?")
    print(f"chain pushed: {args.path} @ {commit[:8]} — agla pass trigger ho gaya")
    return 0


if __name__ == "__main__":
    sys.exit(main())
