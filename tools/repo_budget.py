#!/usr/bin/env python3
"""Measure the Arena workspace against the best-effort snapshot cap.

Why this tool exists
--------------------
Arena persists a workspace to a snapshot at the end of every turn, best-effort
capped near 128 MB (documented in `operations/incidents/INC-20261011-001`). When
the combined size of the worktree, the Git object database and any Drive
staging directory exceeds that boundary, the snapshot silently omits files.
The next turn hydrates an older, smaller state: the newest scripts/renders are
absent and the session appears to "stop" or "restart from zero".

This tool makes that failure visible *before* it happens. Run it after any large
materialization and before ending a turn.

Usage
-----
    python3 tools/repo_budget.py                 # audit with default budget
    python3 tools/repo_budget.py --json          # machine-readable
    python3 tools/repo_budget.py --budget 90     # custom cap in MB
    python3 tools/repo_budget.py --top 20        # more offenders

Exit codes: 0 = inside budget, 1 = over budget (snapshot risk), 2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent

DEFAULT_BUDGET_MB = 100.0
DEFAULT_WARN_MB = 90.0
TRACKED_FILE_LIMIT_MB = 8.0

# Directories that are never part of the snapshot (Arena excludes these names).
SNAPSHOT_EXCLUDED_DIRS = {
    ".arena", ".cache", ".local", ".mypy_cache", ".next", ".nox", ".npm", ".nuxt",
    ".output", ".parcel-cache", ".pytest_cache", ".ruff_cache", ".svelte-kit",
    ".tox", ".turbo", ".venv", "__pycache__", "build", "coverage", "dist",
    "node_modules", "out", "target",
}

# Staging directories that hold materialized Drive assets. They belong outside
# the snapshot: keep them under /tmp, or empty them before the turn ends.
STAGING_HINTS = ("google_drive", "_probe", ".runtime", "stage", "staging", "renders")


def dir_bytes(path: Path, skip: set[str] | None = None) -> tuple[int, int]:
    """Return (bytes, file_count) for a directory tree, skipping excluded names."""
    skip = skip or set()
    total = 0
    count = 0
    for base, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in skip and d not in SNAPSHOT_EXCLUDED_DIRS]
        for name in filenames:
            fp = Path(base) / name
            try:
                total += fp.stat().st_size
                count += 1
            except OSError:
                continue
    return total, count


def human(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(num) < 1024.0 or unit == "GB":
            return f"{num:6.1f} {unit}" if unit != "B" else f"{num:6.0f} B"
        num /= 1024.0
    return f"{num:.1f} GB"


def workspace_inventory() -> list[dict[str, object]]:
    """Top-level areas of the workspace that count towards the snapshot."""
    areas: list[dict[str, object]] = []
    repo_bytes, repo_files = dir_bytes(ROOT, skip={".git"})
    git_bytes, git_files = dir_bytes(ROOT / ".git")
    areas.append({"area": "repo worktree (no .git)", "path": str(ROOT), "bytes": repo_bytes, "files": repo_files})
    areas.append({"area": "repo .git object database", "path": str(ROOT / ".git"), "bytes": git_bytes, "files": git_files})
    for child in sorted(WORKSPACE.iterdir()):
        if child == ROOT:
            continue
        if child.is_dir():
            if child.name in SNAPSHOT_EXCLUDED_DIRS:
                continue
            size, files = dir_bytes(child)
            if size:
                areas.append({"area": f"workspace: {child.name}/", "path": str(child), "bytes": size, "files": files})
        else:
            try:
                areas.append({"area": f"workspace file: {child.name}", "path": str(child), "bytes": child.stat().st_size, "files": 1})
            except OSError:
                continue
    return areas


def largest_files(base: Path, limit: int, skip_git: bool = True) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    for root, dirnames, filenames in os.walk(base):
        if skip_git:
            dirnames[:] = [d for d in dirnames if d != ".git" and d not in SNAPSHOT_EXCLUDED_DIRS]
        for name in filenames:
            fp = Path(root) / name
            try:
                found.append((str(fp.relative_to(base)), fp.stat().st_size))
            except OSError:
                continue
    found.sort(key=lambda item: item[1], reverse=True)
    return found[:limit]


def tracked_offenders(limit_mb: float) -> list[tuple[str, int]]:
    """Tracked files larger than the limit: these belong on Drive, not in Git."""
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    rows: list[tuple[str, int]] = []
    for raw in out.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8", "replace")
        fp = ROOT / rel
        try:
            size = fp.stat().st_size
        except OSError:
            continue
        if size > limit_mb * 1024 * 1024:
            rows.append((rel, size))
    rows.sort(key=lambda item: item[1], reverse=True)
    return rows


def staging_dirs() -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []
    for child in sorted(WORKSPACE.iterdir()):
        if child.is_dir() and child.name in STAGING_HINTS:
            size, _ = dir_bytes(child)
            rows.append((str(child), size))
    for hint in STAGING_HINTS:
        candidate = ROOT / hint
        if candidate.is_dir():
            size, _ = dir_bytes(candidate)
            rows.append((str(candidate), size))
    seen: set[str] = set()
    unique: list[tuple[str, int]] = []
    for path, size in rows:
        if path not in seen:
            seen.add(path)
            unique.append((path, size))
    return unique


def audit(budget_mb: float, warn_mb: float, top: int) -> dict[str, object]:
    areas = workspace_inventory()
    total = sum(int(a["bytes"]) for a in areas)
    return {
        "total_bytes": total,
        "total_human": human(total),
        "budget_bytes": int(budget_mb * 1024 * 1024),
        "budget_human": human(budget_mb * 1024 * 1024),
        "status": "over_budget" if total > budget_mb * 1024 * 1024 else ("warning" if total > warn_mb * 1024 * 1024 else "ok"),
        "areas": areas,
        "largest": [{"path": p, "bytes": b} for p, b in largest_files(ROOT, top)],
        "tracked_offenders": [{"path": p, "bytes": b} for p, b in tracked_offenders(TRACKED_FILE_LIMIT_MB)],
        "staging": [{"path": p, "bytes": b} for p, b in staging_dirs()],
    }


def render(report: dict[str, object]) -> None:
    total = int(report["total_bytes"])
    budget = int(report["budget_bytes"])
    status = str(report["status"])
    print("=" * 78)
    print("MONARCH STUDIO · workspace snapshot budget")
    print("=" * 78)
    print(f"workspace total : {human(total)}   (cap {human(budget)} = --budget)")
    fill = min(1.0, total / budget if budget else 0.0)
    bar = "#" * int(round(fill * 50))
    print(f"usage           : [{bar:<50}] {fill * 100:5.1f}%")
    print(f"status          : {status.upper()}")
    print()
    print("areas contributing to the snapshot:")
    for area in sorted(report["areas"], key=lambda a: int(a["bytes"]), reverse=True):
        share = (int(area["bytes"]) / total * 100.0) if total else 0.0
        print(f"  {human(int(area['bytes']))}  {share:5.1f}%  {area['area']}")
    print()
    print(f"largest files (top {len(report['largest'])}) — move masters to Drive, keep IDs in records:")
    for row in report["largest"]:
        print(f"  {human(int(row['bytes']))}  {row['path']}")
    if report["tracked_offenders"]:
        print()
        print(f"tracked files over {TRACKED_FILE_LIMIT_MB:.0f} MB (Git-history weight; prefer Drive + recorded ID):")
        for row in report["tracked_offenders"]:
            print(f"  {human(int(row['bytes']))}  {row['path']}")
    if report["staging"]:
        print()
        print("Drive/materialization staging directories detected (they count towards the snapshot):")
        for row in report["staging"]:
            print(f"  {human(int(row['bytes']))}  {row['path']}")
    print()
    if status == "over_budget":
        print("SNAPSHOT RISK — the next turn will silently drop the newest files.")
        print("Do this now:")
        print("  1. move staged Drive assets out of the workspace:  mv google_drive/* /tmp/monarch-stage/")
        print("  2. drop heavy render inputs from the worktree:      python3 tools/materialize.py compact")
        print("  3. shrink the object database:                      git gc --prune=now")
        print("  4. re-run:                                          python3 tools/repo_budget.py")
    elif status == "warning":
        print("WARNING — close to the cap. Clean staging before the turn ends.")
    else:
        print("OK — inside budget; a full-size render can be materialized safely.")
    print("=" * 78)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--budget", type=float, default=DEFAULT_BUDGET_MB, help="snapshot budget in MB (default 100)")
    parser.add_argument("--warn", type=float, default=DEFAULT_WARN_MB, help="warning threshold in MB (default 90)")
    parser.add_argument("--top", type=int, default=12, help="how many largest files to list")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()

    report = audit(args.budget, args.warn, args.top)
    if args.json:
        print(json.dumps(report, indent=1))
    else:
        render(report)
    return 1 if report["status"] == "over_budget" else 0


if __name__ == "__main__":
    sys.exit(main())
