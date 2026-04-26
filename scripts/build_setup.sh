#!/usr/bin/env bash
# build_setup — copies commons into each app under a given stack.
#
# Usage:
#   ./scripts/build_setup.sh                        # all stacks, all apps
#   ./scripts/build_setup.sh vite-fastapi-sqlite    # one stack, all apps
#   ./scripts/build_setup.sh vite-fastapi-sqlite finance-os  # one app
#
# In CI (FORGER_ENV=ci) files are hard-copied.
# In dev mode (default) symlinks are used so commons changes reflect instantly.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_STACK="${1:-}"
TARGET_APP="${2:-}"
DEV_MODE="${FORGER_ENV:-dev}"

copy_or_link() {
  local src="$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  if [[ "$DEV_MODE" == "ci" ]]; then
    cp -f "$src" "$dst"
  else
    ln -sf "$src" "$dst"
  fi
}

sync_commons() {
  local stack_dir="$1" app_dir="$2"
  local commons_be="$stack_dir/commons/backend"
  local commons_fe="$stack_dir/commons/frontend"
  local app_name
  app_name="$(basename "$app_dir")"

  # Skip non-app directories
  [[ "$app_name" == "commons" || "$app_name" == "skeleton" ]] && return

  echo "  → $app_name"

  # Create commons symlink so docker-compose can use ./commons/... paths
  ln -sf ../commons "$app_dir/commons"

  # Backend commons
  if [[ -d "$commons_be" && -d "$app_dir/backend" ]]; then
    local be_target
    # Support both src/app/ (skeleton layout) and app/ (finance-os layout)
    if [[ -d "$app_dir/backend/src/app" ]]; then
      be_target="$app_dir/backend/src/app"
    else
      be_target="$app_dir/backend/app"
    fi
    for f in "$commons_be"/*.py; do
      [[ -f "$f" ]] || continue
      copy_or_link "$f" "$be_target/$(basename "$f")"
    done
  fi

  # Frontend commons
  if [[ -d "$commons_fe" && -d "$app_dir/frontend/src" ]]; then
    for f in "$commons_fe"/*.ts "$commons_fe"/*.tsx; do
      [[ -f "$f" ]] || continue
      copy_or_link "$f" "$app_dir/frontend/src/api/$(basename "$f")"
    done
  fi
}

process_stack() {
  local stack_dir="$1"
  echo "Stack: $(basename "$stack_dir")"

  if [[ -n "$TARGET_APP" ]]; then
    local app_dir="$stack_dir/$TARGET_APP"
    [[ -d "$app_dir" ]] || { echo "  App '$TARGET_APP' not found"; return; }
    sync_commons "$stack_dir" "$app_dir"
  else
    for app_dir in "$stack_dir"/*/; do
      [[ -d "$app_dir" ]] && sync_commons "$stack_dir" "$app_dir"
    done
  fi
}

if [[ -n "$TARGET_STACK" ]]; then
  stack_dir="$ROOT_DIR/$TARGET_STACK"
  [[ -d "$stack_dir" ]] || { echo "Stack '$TARGET_STACK' not found"; exit 1; }
  process_stack "$stack_dir"
else
  for stack_dir in "$ROOT_DIR"/*/; do
    [[ -d "$stack_dir/commons" ]] && process_stack "$stack_dir"
  done
fi

echo "✓ build_setup done (mode: $DEV_MODE)"
