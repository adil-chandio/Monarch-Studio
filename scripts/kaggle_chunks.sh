#!/usr/bin/env bash
# kaggle_chunks.sh — Kaggle par scene-chunks render karta hai (API push + poll + output download).
#
#   scripts/kaggle_chunks.sh "k01,k02;k03,k04" clips
#
# Env: KAGGLE_USERNAME + (KAGGLE_KEY ya KAGGLE_API_TOKEN), POLL_MAX (min/chunk), POLL_SLEEP (s)
#      SLUG_PREFIX (default monarch-stick), DIAG=1 (quota + kernel logs annotations me)
#
# Kernel chal raha ho to wait karta rehta hai — bekar me dobara push nahi karta.
# Har ahem baat ::notice:: se annotate hoti hai (remote se dekh sakte hain).
set -uo pipefail

CHUNKS="${1:-k01,k02,k03,k04;k05,k06,k07,k08;k09,k10,k11,k12}"
CLIPS_DIR="${2:-clips}"
POLL_MAX="${POLL_MAX:-150}"
POLL_SLEEP="${POLL_SLEEP:-60}"
SLUG_PREFIX="${SLUG_PREFIX:-monarch-stick}"

mkdir -p "$CLIPS_DIR" work

if [ -z "${KAGGLE_USERNAME:-}" ]; then
  echo "::error::Kaggle username nahi mila — secret me Kaggle API token (KGAT_...) ya KAGGLE_USERNAME+KAGGLE_KEY do."
  exit 1
fi
if [ -z "${KAGGLE_KEY:-}" ] && [ -z "${KAGGLE_API_TOKEN:-}" ]; then
  echo "::error::Kaggle credentials adhoore — KAGGLE_KEY ya KAGGLE_API_TOKEN chahiye."
  exit 1
fi

note() { echo "::notice::$*"; }          # annotation (remote diagnosis ke liye)
diag() { [ "${DIAG:-1}" = "1" ] && note "$*"; }

kernel_status() { kaggle kernels status "$1" 2>&1 | tail -1; }

wait_kernel() {                          # 0=complete, 1=failed, 2=timeout (still running)
  local ref="$1" i=0 status
  while [ "$i" -lt "$POLL_MAX" ]; do
    status=$(kernel_status "$ref")
    echo "[$(date +%H:%M:%S)] $status"
    case "$status" in
      *COMPLETE*) note "$ref complete"; return 0 ;;
      *ERROR*|*CANCEL*|*FAIL*) note "$ref failed: $status"; return 1 ;;
    esac
    if [ $((i % 10)) -eq 0 ]; then note "$ref · $(date +%H:%M) · $status"; fi
    i=$((i + 1))
    sleep "$POLL_SLEEP"
  done
  note "$ref timeout — abhi bhi chal raha hai (${POLL_MAX}m)"
  return 2
}

kernel_tail() {                          # logs ki aakhri lines annotations me (remote se padhne ke liye)
  local ref="$1" line n=0
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    n=$((n + 1))
    [ "$n" -gt 30 ] && continue
    note "log $ref | ${line:0:180}"
  done < <(kaggle kernels logs "$ref" 2>&1 | grep -viE "^(warning|traceback)" | tail -30)
}

note "quota: $(kaggle quota 2>&1 | tr '\n' ' ' | cut -c1-220)"
note "chunks: $CHUNKS | prefix: $SLUG_PREFIX | poll_max: ${POLL_MAX}m"

FAILED=""
n=0
IFS=';' read -ra PARTS <<< "$CHUNKS"
for ONLY in "${PARTS[@]}"; do
  [ -z "$ONLY" ] && continue
  n=$((n + 1))
  SLUG="${SLUG_PREFIX}-$n"
  DIR="work/$SLUG"
  REF="$KAGGLE_USERNAME/$SLUG"

  echo "::group::chunk $n — $ONLY"
  if ! python tools/make_kaggle_kernel.py --user "$KAGGLE_USERNAME" --slug "$SLUG" \
        --only "$ONLY" --out "$DIR"; then
    echo "::error::chunk $n package fail"
    FAILED="$FAILED ${n}(package)"
    echo "::endgroup::"
    continue
  fi

  for try in 1 2; do
    echo "→ push (try $try): $REF"
    if ! kaggle kernels push -p "$DIR" 2>&1 | tail -3; then
      note "push fail $REF (try $try)"; sleep 30; continue
    fi
    note "pushed $REF ($ONLY)"

    rc=0
    wait_kernel "$REF" || rc=$?

    kaggle kernels output "$REF" -p "$DIR/out" 2>&1 | tail -3 || true
    found=$(find "$DIR/out" -name 'k*.mp4' -size +20k 2>/dev/null | wc -l | tr -d ' ')
    note "output $REF: $found mp4"
    find "$DIR/out" -name 'k*.mp4' -size +20k -exec cp -f {} "$CLIPS_DIR"/ \; 2>/dev/null || true

    missing=""
    for id in $(echo "$ONLY" | tr ',' ' '); do
      [ -s "$CLIPS_DIR/$id.mp4" ] || missing="$missing $id"
    done
    if [ -z "$missing" ]; then
      note "chunk $n OK — saari clips mil gayi"
      break
    fi
    note "chunk $n incomplete — missing:$missing (kernel rc=$rc)"
    kernel_tail "$REF"
    if [ "$rc" -eq 2 ]; then
      note "kernel chal raha tha — dobara push nahi (waste). Agli run me wohi chunk."
      FAILED="$FAILED ${n}(timeout)"
      break
    fi
    FAILED="$FAILED ${n}"
    kaggle kernels delete "$REF" -y >/dev/null 2>&1 || true
  done

  echo "::endgroup::"
done

echo "--- clips ---"
ls -la "$CLIPS_DIR" || true
count=$(find "$CLIPS_DIR" -name '*.mp4' -size +20k 2>/dev/null | wc -l | tr -d ' ')
note "clips total: $count"
if [ "$count" -eq 0 ]; then
  echo "::error::koi clip download nahi hui — upar ke log annotations dekho (verify? GPU quota? model download?)"
  exit 1
fi
if [ -n "$FAILED" ]; then
  echo "::warning::partial run — in chunks par kaam baqi:$FAILED"
fi
exit 0
