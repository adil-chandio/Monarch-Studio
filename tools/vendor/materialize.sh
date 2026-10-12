#!/usr/bin/env bash
# Vendor source on demand.
#
# Vendor repositories are pinned Git submodules. Their source lives at the pinned
# commits on GitHub. The working trees (and their .git/modules cache) are heavy, so
# they are kept out of the workspace by default. This script brings any of them back
# at the exact pin, or removes them again.
#
#   tools/vendor/materialize.sh status            # which vendor trees are populated, sizes
#   tools/vendor/materialize.sh all               # populate every vendor repo (shallow, pinned)
#   tools/vendor/materialize.sh one <name>        # populate one, e.g. react-bits
#   tools/vendor/materialize.sh release <name>|all  # remove working tree + module cache, keep the pin
#
# Pins and licences: docs/VENDOR_INTEGRATION.md. Copied skill text: docs/skills/vendored/.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

NAMES=$(git config --file .gitmodules --get-regexp '^submodule\..*\.path$' | awk '{print $2}' | sed 's#^vendor/##')

populated() {
  local d="vendor/$1"
  [ -d "$d" ] && [ -n "$(ls -A "$d" 2>/dev/null)" ]
}

case "${1:-status}" in
  status)
    for n in $NAMES; do
      if populated "$n"; then
        s=$(du -sh "vendor/$n" 2>/dev/null | cut -f1)
        echo "populated  $n  $s"
      else
        echo "pin-only   $n"
      fi
    done
    echo "module cache: $(du -sh .git/modules/vendor 2>/dev/null | cut -f1 || echo 0)"
    ;;
  all)
    git submodule update --init --depth 1 -- $(printf 'vendor/%s ' $NAMES)
    ;;
  one)
    [ -n "${2:-}" ] || { echo "usage: $0 one <name>"; exit 2; }
    git submodule update --init --depth 1 -- "vendor/$2"
    ;;
  release)
    [ -n "${2:-}" ] || { echo "usage: $0 release <name>|all"; exit 2; }
    targets="$2"; [ "$2" = "all" ] && targets="$NAMES"
    for n in $targets; do
      git submodule deinit -f -- "vendor/$n" >/dev/null 2>&1 || true
      rm -rf ".git/modules/vendor/$n"
      echo "released $n (pin kept)"
    done
    ;;
  *)
    echo "unknown command: ${1}"; exit 2 ;;
esac
