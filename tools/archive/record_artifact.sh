#!/usr/bin/env bash
# Record a large artifact that lives OUTSIDE the workspace (Google Drive or another host).
# Writes size + SHA-256 + link + description into projects/<slug>/ARTIFACTS.md.
#
#   tools/archive/record_artifact.sh <project-slug> <local-file> "<drive-or-host-link>" "<description>"
#
# Flow: upload the file to Drive (project folder), run this script with the returned link,
# then delete the local copy so the workspace stays light.
#
# Why not GitHub Releases: in this sandbox uploads.github.com and objects.githubusercontent.com
# are blocked, so release assets cannot be uploaded. GitHub keeps the metadata; Drive keeps bytes.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

SLUG="${1:?project slug}"
FILE="${2:?local file}"
LINK="${3:?link (Drive or other host)}"
DESC="${4:-}"
[ -f "$FILE" ] || { echo "no such file: $FILE"; exit 2; }

NAME="$(basename "$FILE")"
SIZE=$(stat -c %s "$FILE")
SHA=$(sha256sum "$FILE" | cut -d' ' -f1)
HUMAN=$(numfmt --to=iec "$SIZE" 2>/dev/null || echo "${SIZE} B")
ART="projects/${SLUG}/ARTIFACTS.md"
mkdir -p "projects/${SLUG}"
[ -f "$ART" ] || printf '# Artifacts: %s\n\nLarge files live outside the workspace (Drive). This table is the index: name, size, checksum, link.\n\n| File | Size | SHA-256 | Link | Description | Recorded (UTC) |\n|---|---|---|---|---|---|\n' "$SLUG" > "$ART"
printf '| `%s` | %s | `%s` | [link](%s) | %s | %s |\n' \
  "$NAME" "$HUMAN" "$SHA" "$LINK" "$DESC" "$(date -u +%Y-%m-%dT%H:%MZ)" >> "$ART"
echo "recorded: $ART ($HUMAN, sha256 ${SHA:0:16}...)"
