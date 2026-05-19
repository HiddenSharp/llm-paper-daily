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
      exit 40
      ;;
  esac
done

if [[ -z "$CONFIG" ]]; then
  echo "missing --config" >&2
  exit 40
fi

CONFIG_EXPANDED="${CONFIG/#\~/$HOME}"
ROOT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
TMP="$(mktemp /tmp/paper-subscribe-XXXXXX.json)"
trap 'rm -f "$TMP"' EXIT

node "$ROOT_DIR/skill/paper-subscribe/scripts/prepare-digest.js" --config "$CONFIG_EXPANDED" > "$TMP"

STATUS=$(python3 - <<PY
import json
print(json.load(open("$TMP"))["status"])
PY
)

if [[ "$STATUS" == "skipped_no_new_items" ]]; then
  exit 0
fi

node "$ROOT_DIR/skill/paper-subscribe/scripts/deliver.js" --config "$CONFIG_EXPANDED" --input "$TMP"
