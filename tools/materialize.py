#!/usr/bin/env python3
"""Switch the local worktree between compact control-plane and full render assets."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
COMPACT_PATHS = [
    ".github",
    "characters/monarch/previews",
    "characters/monarch/tooling",
    "docs",
    "licenses",
    "operations",
    "requirements",
    "studio",
    "styles/monarch-stickman-animation/brain",
    "styles/monarch-stickman-animation/fonts",
    "styles/monarch-stickman-animation/knowledge",
    "styles/monarch-stickman-animation/records",
    "styles/monarch-stickman-animation/src",
    "styles/monarch-noir-film/data",
    "styles/monarch-noir-film/films",
    "styles/monarch-noir-film/knowledge",
    "styles/monarch-noir-film/records",
    "styles/monarch-noir-film/src",
    "styles/monarch-zackd-3d",
    "tests",
    "tools",
    "workflows",
]


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    if check and proc.returncode:
        raise SystemExit((proc.stderr or proc.stdout).strip())
    return proc


def require_git() -> None:
    if not (ROOT / ".git").exists():
        raise SystemExit("not a Git worktree")


def require_clean() -> None:
    dirty = run(["git", "status", "--porcelain=v1"], check=True).stdout.strip()
    if dirty:
        raise SystemExit("refusing materialization change with a dirty worktree; checkpoint/commit first")


def status() -> int:
    require_git()
    enabled = run(["git", "config", "--bool", "core.sparseCheckout"], check=False).stdout.strip() == "true"
    tracked = run(["git", "ls-files"], check=True).stdout.splitlines()
    marked = run(["git", "ls-files", "-v"], check=True).stdout.splitlines()
    omitted = sum(1 for line in marked if line.startswith("S "))
    mode = "compact sparse" if enabled else "full"
    print(f"mode={mode}; tracked={len(tracked)}; sparse_omitted={omitted}")
    return 0


def compact() -> int:
    require_git()
    require_clean()
    run(["git", "sparse-checkout", "init", "--cone"])
    run(["git", "sparse-checkout", "set", *COMPACT_PATHS])
    print("compact control-plane materialized; archived render assets remain in Git + Drive")
    return status()


def full() -> int:
    require_git()
    require_clean()
    run(["git", "sparse-checkout", "disable"])
    print("full tracked worktree materialized")
    return status()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("status", "compact", "full"))
    args = parser.parse_args()
    return {"status": status, "compact": compact, "full": full}[args.mode]()


if __name__ == "__main__":
    sys.exit(main())
