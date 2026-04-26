#!/usr/bin/env bash
# build_check — runs verification for each app in the catalog.
#
# Usage:
#   ./scripts/build_check.sh                        # all stacks, all apps
#   ./scripts/build_check.sh vite-fastapi-sqlite    # one stack
#   ./scripts/build_check.sh vite-fastapi-sqlite finance-os  # one app

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_STACK="${1:-}"
TARGET_APP="${2:-}"
FAILED=()

check_app() {
  local app_dir="$1"
  local app_name
  app_name="$(basename "$app_dir")"
  [[ "$app_name" == "commons" || "$app_name" == "skeleton" ]] && return

  echo "  checking $app_name..."

  # Backend: uv run python scripts/verify.py
  if [[ -f "$app_dir/backend/scripts/verify.py" ]]; then
    if ! (cd "$app_dir/backend" && uv run python scripts/verify.py); then
      FAILED+=("$app_name/backend verify")
    fi
  fi

  # Frontend: tsc --noEmit
  if [[ -f "$app_dir/frontend/package.json" ]]; then
    if ! (cd "$app_dir/frontend" && npm run typecheck --if-present 2>/dev/null || npx tsc --noEmit); then
      FAILED+=("$app_name/frontend typecheck")
    fi
  fi
}

check_stack() {
  local stack_dir="$1"
  echo "Stack: $(basename "$stack_dir")"

  if [[ -n "$TARGET_APP" ]]; then
    local app_dir="$stack_dir/$TARGET_APP"
    [[ -d "$app_dir" ]] || { echo "  App '$TARGET_APP' not found"; return; }
    check_app "$app_dir"
  else
    for app_dir in "$stack_dir"/*/; do
      [[ -d "$app_dir" ]] && check_app "$app_dir"
    done
  fi
}

if [[ -n "$TARGET_STACK" ]]; then
  check_stack "$ROOT_DIR/$TARGET_STACK"
else
  for stack_dir in "$ROOT_DIR"/*/; do
    [[ -d "$stack_dir/commons" ]] && check_stack "$stack_dir"
  done
fi

if [[ ${#FAILED[@]} -gt 0 ]]; then
  echo ""
  echo "✗ Checks failed:"
  for f in "${FAILED[@]}"; do echo "  - $f"; done
  exit 1
fi

echo "✓ build_check passed"
