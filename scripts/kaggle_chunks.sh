#!/usr/bin/env bash
# kaggle_chunks.sh — Kaggle par scene-chunks render karta hai (API push + poll + output download).
#
#   scripts/kaggle_chunks.sh "k01,k02;k03,k04" clips
#
# Env: KAGGLE_USERNAME, KAGGLE_KEY (GitHub secrets se aate hain), POLL_MAX (min/chunk), POLL_SLEEP
# Har chunk ke baad clips/ me mp4 aa jati hain; jo chunk fail ho woh dobara try hota hai.
set -uo pipefail

CHUNKS="${1:-k01,k02,k03,k04;k05,k06,k07,k08;k09,k10,k11,k12}"
CLIPS_DIR="${2:-clips}"
POLL_MAX="${POLL_MAX:-75}"          # max minutes per attempt
POLL_SLEEP="${POLL_SLEEP:-60}"

mkdir -p "$CLIPS_DIR" work

if [ -z "${KAGGLE_USERNAME:-}" ]; then
  echo "::error::Kaggle username nahi mila — secret me Kaggle API token (KGAT_...) ya KAGGLE_USERNAME+KAGGLE_KEY do."
  exit 1
fi
if [ -z "${KAGGLE_KEY:-}" ] && [ -z "${KAGGLE_API_TOKEN:-}" ]; then
  echo "::error::Kaggle credentials adhoore — KAGGLE_KEY ya KAGGLE_API_TOKEN chahiye."
  exit 1
fi

FAILED=""
n=0
IFS=';' read -ra PARTS <<< "$CHUNKS"
for ONLY in "${PARTS[@]}"; do
  [ -z "$ONLY" ] && continue
  n=$((n + 1))
  SLUG="monarch-stick-$n"
  DIR="work/$SLUG"

  echo "::group::chunk $n — $ONLY"
  if ! python tools/make_kaggle_kernel.py --user "$KAGGLE_USERNAME" --slug "$SLUG" \
        --only "$ONLY" --out "$DIR"; then
    echo "::error::chunk $n package fail"
    FAILED="$FAILED ${n}(package)"
    echo "::endgroup::"
    continue
  fi

  for try in 1 2; do
    echo "→ push (try $try): $KAGGLE_USERNAME/$SLUG"
    if ! kaggle kernels push -p "$DIR"; then
      echo "push fail (try $try)"
      sleep 30
      continue
    fi

    for i in $(seq 1 "$POLL_MAX"); do
      status=$(kaggle kernels status "$KAGGLE_USERNAME/$SLUG" 2>&1 | tail -1)
      echo "[$i/$POLL_MAX] $status"
      case "$status" in
        *COMPLETE*) echo "kernel complete"; break ;;
        *ERROR*|*CANCEL*) echo "kernel error — output/log check"; break ;;
      esac
      sleep "$POLL_SLEEP"
    done

    kaggle kernels output "$KAGGLE_USERNAME/$SLUG" -p "$DIR/out" 2>&1 | tail -3 || true
    find "$DIR/out" -name 'k*.mp4' -size +20k -exec cp -f {} "$CLIPS_DIR"/ \; 2>/dev/null || true

    missing=""
    for id in $(echo "$ONLY" | tr ',' ' '); do
      [ -s "$CLIPS_DIR/$id.mp4" ] || missing="$missing $id"
    done
    if [ -z "$missing" ]; then
      echo "chunk $n OK"
      break
    fi
    echo "chunk $n incomplete — missing:$missing"
    FAILED="$FAILED ${n}"
  done

  echo "::endgroup::"
done

echo "--- clips ---"
ls -la "$CLIPS_DIR" || true
count=$(find "$CLIPS_DIR" -name '*.mp4' -size +20k 2>/dev/null | wc -l | tr -d ' ')
echo "clips total: $count"
if [ "$count" -eq 0 ]; then
  echo "::error::koi clip download nahi hui — Kaggle secrets aur kernel logs check karo"
  exit 1
fi
if [ -n "$FAILED" ]; then
  echo "::warning::partial run — failed chunks:$FAILED (agli run me sirf yeh dobara chalao)"
fi
exit 0
