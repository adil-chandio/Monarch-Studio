#!/usr/bin/env bash
# Recover the newest work for THIS session instead of restarting from `main`.
#
# Why: every Arena turn clones/pins the repository at `main` on a new
# `arena/<session>-monarch-studio` branch. Work committed in earlier turns is
# still on GitHub under its own arena branch (and in Drive records), but a plain
# checkout shows only `main` — which looks exactly like "everything restarted".
# This script lists those branches with their newest commit, prints the recorded
# next action, and can fast-forward the current branch onto one of them.
#
# Usage:
#   bash tools/session_recover.sh                 # report only
#   bash tools/session_recover.sh --merge <ref>   # fast-forward current branch onto <ref>
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODE="report"
REF=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --merge) MODE="merge"; REF="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

echo "== fetching arena branches =="
git fetch --quiet origin '+refs/heads/*:refs/remotes/origin/*' || echo "fetch failed (offline?) — continuing with local refs"

if [[ "$MODE" == "merge" ]]; then
  if [[ -z "$REF" ]]; then echo "--merge needs a ref (see list below)"; exit 2; fi
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "worktree dirty — checkpoint/commit first (see CONTRIBUTING.md rule 1)"; git status --short; exit 1
  fi
  echo "== fast-forwarding $(git rev-parse --abbrev-ref HEAD) onto $REF =="
  git merge --ff-only "$REF" || { echo "not a fast-forward — inspect manually, do not force"; exit 1; }
fi

echo
echo "== candidate branches (newest commit first) =="
printf '%-52s %-20s %s\n' "ref" "commit date" "subject"
git for-each-ref --sort=-committerdate --format='%(refname:short)|%(committerdate:short)|%(subject)' refs/remotes/origin refs/heads \
  | grep -v 'origin/HEAD' | head -20 | while IFS='|' read -r ref date subject; do
      printf '%-52s %-20s %s\n' "$ref" "$date" "${subject:0:70}"
    done

echo
echo "== current branch =="
echo "  $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD) — $(git log -1 --format=%s)"

echo
echo "== recorded next action (workflows/current/RESUME.md) =="
if [[ -f workflows/current/RESUME.md ]]; then
  awk '/^## Exact next action/{flag=1;next}/^## /{flag=0}flag' workflows/current/RESUME.md | sed '/^$/d' | sed 's/^/  /' | head -8
else
  echo "  (no resume capsule in this checkout)"
fi

echo
echo "Next: if a candidate branch carries the active task, run"
echo "  bash tools/session_recover.sh --merge <ref>"
echo "then  python3 tools/bootstrap_env.sh && python3 tools/repo_budget.py"
