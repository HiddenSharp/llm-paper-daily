#!/usr/bin/env sh

if [ -n "${BASH_VERSION:-}" ]; then
  SCRIPT_PATH="${BASH_SOURCE[0]}"
elif [ -n "${ZSH_VERSION:-}" ]; then
  SCRIPT_PATH="${(%):-%N}"
else
  SCRIPT_PATH="$0"
fi

ROOT_DIR="$(cd "$(dirname "$SCRIPT_PATH")/../../.." && pwd)"
ENV_FILE="${1:-$ROOT_DIR/.local/paper-learning.env}"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing env file: $ENV_FILE" >&2
  echo "Create it from: $ROOT_DIR/skill/paper-learning/templates/paper-learning.env.example" >&2
  return 1 2>/dev/null || exit 1
fi

set -a
. "$ENV_FILE"
set +a

if [ -z "${NOTION_TOKEN:-}" ]; then
  echo "NOTION_TOKEN is required." >&2
  return 1 2>/dev/null || exit 1
fi

echo "Loaded paper-learning env from $ENV_FILE"
