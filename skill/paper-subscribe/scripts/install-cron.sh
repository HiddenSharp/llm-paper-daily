#!/usr/bin/env bash
set -euo pipefail

CONFIG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      CONFIG="$2"
      shift 2
      ;;
    *)
      echo "unknown arg: $1" >&2
      exit 30
      ;;
  esac
done

if [[ -z "$CONFIG" ]]; then
  echo "missing --config" >&2
  exit 30
fi

CONFIG_EXPANDED="${CONFIG/#\~/$HOME}"
if [[ ! -f "$CONFIG_EXPANDED" ]]; then
  echo "config not found" >&2
  exit 30
fi

SCHEDULE=$(python3 - <<PY
import json
cfg=json.load(open("$CONFIG_EXPANDED"))
print(cfg["schedule"])
PY
)

TIMEZONE=$(python3 - <<PY
import json
cfg=json.load(open("$CONFIG_EXPANDED"))
print(cfg.get("timezone","UTC"))
PY
)

ROOT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
TAG="paper-subscribe:${CONFIG_EXPANDED}"
TZ_TAG="${TAG}:tz"
RUNNER="bash -lc '\"$ROOT_DIR/skill/paper-subscribe/scripts/run-subscription.sh\" --config \"$CONFIG_EXPANDED\"' # $TAG"

TMP_CRON="$(mktemp /tmp/paper-subscribe-cron-XXXXXX)"
TMP_ERR="$(mktemp /tmp/paper-subscribe-cron-err-XXXXXX)"
trap 'rm -f "$TMP_CRON" "$TMP_ERR"' EXIT

if crontab -l >"$TMP_CRON" 2>"$TMP_ERR"; then
  :
else
  if grep -qi "no crontab" "$TMP_ERR"; then
    : >"$TMP_CRON"
  else
    cat "$TMP_ERR" >&2
    exit 31
  fi
fi

{
  awk -v tag="# $TAG" -v tztag="# $TZ_TAG" '
    function endswith(str, suffix) {
      return length(str) >= length(suffix) && substr(str, length(str) - length(suffix) + 1) == suffix
    }
    skip_next {
      skip_next = 0
      next
    }
    endswith($0, tag) || endswith($0, tztag) {
      skip_next = 1
      next
    }
    { print }
  ' "$TMP_CRON" || true
  echo "# $TZ_TAG"
  echo "CRON_TZ=$TIMEZONE"
  echo "# $TAG"
  echo "$SCHEDULE $RUNNER"
} | crontab -
echo "installed"
