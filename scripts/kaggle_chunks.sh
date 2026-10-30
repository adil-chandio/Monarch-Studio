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

# Live status file `ci-status` branch par (remote se turant padha ja sakta hai).
# Har call fail-safe hai — kabhi job nahi girata.
report() {
  [ "${REPORT:-1}" = "1" ] || return 0
  [ -n "${GITHUB_REPOSITORY:-}" ] || return 0
  local msg body sha
  msg="$(date -u +%H:%M:%SZ) · $*"
  body=$(printf '%s' "$msg" | base64 -w0)
  if ! gh api "/repos/$GITHUB_REPOSITORY/git/ref/heads/ci-status" >/dev/null 2>&1; then
    local base_sha
    base_sha=$(gh api "/repos/$GITHUB_REPOSITORY/git/ref/heads/$GITHUB_REF_NAME" --jq '.object.sha' 2>/dev/null)
    [ -n "$base_sha" ] && gh api -X POST "/repos/$GITHUB_REPOSITORY/git/refs" \
      -f ref="refs/heads/ci-status" -f sha="$base_sha" >/dev/null 2>&1 || true
  fi
  sha=$(gh api "/repos/$GITHUB_REPOSITORY/contents/status.txt?ref=ci-status" --jq '.sha' 2>/dev/null || true)
  if [ -n "$sha" ]; then
    gh api -X PUT "/repos/$GITHUB_REPOSITORY/contents/status.txt" \
      -f message="ci: status" -f content="$body" -f branch="ci-status" -f sha="$sha" >/dev/null 2>&1 || true
  else
    gh api -X PUT "/repos/$GITHUB_REPOSITORY/contents/status.txt" \
      -f message="ci: status" -f content="$body" -f branch="ci-status" >/dev/null 2>&1 || true
  fi
}

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
    if [ $((i % 5)) -eq 0 ]; then
      note "$ref · $(date +%H:%M) · $status"
      report "$ref · $status"
    fi
    i=$((i + 1))
    sleep "$POLL_SLEEP"
  done
  note "$ref timeout — abhi bhi chal raha hai (${POLL_MAX}m)"
  return 2
}

kernel_tail() {                          # logs ki aakhri lines annotations + ci-status par
  local ref="$1" line n=0 tail_txt=""
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    n=$((n + 1))
    case "$line" in
      ::*|*"Figure"*|*"Saving"*) continue ;;
    esac
    note "log $ref | ${line:0:180}"
    tail_txt="$tail_txt ${line:0:120} |"
  done < <(kaggle kernels logs "$ref" 2>&1 | grep -viE "^(warning|traceback)" | tail -25)
  report "LOGS $ref: $(echo "$tail_txt" | cut -c1-900)"
}

QUOTA="$(kaggle quota 2>&1 | tr '\n' ' ' | cut -c1-220)"
note "quota: $QUOTA"
report "quota: $QUOTA"
note "chunks: $CHUNKS | prefix: $SLUG_PREFIX | poll_max: ${POLL_MAX}m"

# Pehle se bane kernels se clips (dobara render kiye bagair)
IFS=';' read -ra FETCHES <<< "${FETCH:-}"
for slug in "${FETCHES[@]}"; do
  [ -z "$slug" ] && continue
  ref="$KAGGLE_USERNAME/$slug"
  DIR="work/fetch-$slug"
  mkdir -p "$DIR/out"
  echo "::group::fetch $ref"
  kaggle kernels output "$ref" -p "$DIR/out" 2>&1 | tail -3 || true
  got=$(find "$DIR/out" -name 'k*.mp4' -size +20k 2>/dev/null | wc -l | tr -d ' ')
  find "$DIR/out" -name 'k*.mp4' -size +20k -exec cp -f {} "$CLIPS_DIR"/ \; 2>/dev/null || true
  note "fetch $ref: $got mp4"
  report "fetch $ref: $got mp4"
  echo "::endgroup::"
done

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
        --only "$ONLY" --title "$SLUG" --out "$DIR"; then
    echo "::error::chunk $n package fail"
    FAILED="$FAILED ${n}(package)"
    echo "::endgroup::"
    continue
  fi

  for try in 1 2; do
    echo "→ push (try $try): $REF"
    push_out=$(kaggle kernels push -p "$DIR" 2>&1); push_rc=$?
    echo "$push_out" | tail -5
    if [ "$push_rc" -ne 0 ]; then
      note "push fail $REF (try $try, rc=$push_rc): $(echo "$push_out" | tr '\n' ' ' | cut -c1-200)"
      report "PUSH FAIL $REF: $(echo "$push_out" | tr '\n' ' ' | cut -c1-260)"
      sleep 30
      continue
    fi
    note "pushed $REF ($ONLY)"
    report "pushed $REF ($ONLY)"

    rc=0
    wait_kernel "$REF" || rc=$?

    kaggle kernels output "$REF" -p "$DIR/out" 2>&1 | tail -3 || true
    found=$(find "$DIR/out" -name 'k*.mp4' -size +20k 2>/dev/null | wc -l | tr -d ' ')
    report "files $REF: $(find "$DIR/out" -maxdepth 2 -type f 2>/dev/null | head -8 | tr '\n' ' ' | cut -c1-200)"
    note "output $REF: $found mp4"
    report "output $REF: $found mp4"
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
    report "RECEIPT $REF: $(find "$DIR/out" -name receipts.json -exec cat {} \; 2>/dev/null | tr -d '\n' | cut -c1-900)"
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
report "clips total: $count"
if [ "$count" -eq 0 ]; then
  echo "::error::koi clip download nahi hui — upar ke log annotations dekho (verify? GPU quota? model download?)"
  exit 1
fi
if [ -n "$FAILED" ]; then
  echo "::warning::partial run — in chunks par kaam baqi:$FAILED"
fi
exit 0
