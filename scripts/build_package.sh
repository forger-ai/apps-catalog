#!/usr/bin/env bash
# build_package — creates a zip for each app and optionally uploads to GitHub Releases.
#
# Usage:
#   ./scripts/build_package.sh                              # all apps
#   ./scripts/build_package.sh vite-fastapi-sqlite finance-os        # one app
#   ./scripts/build_package.sh vite-fastapi-sqlite finance-os 0.2.0  # specific version
#
# Env vars:
#   GITHUB_TOKEN  — if set, uploads the zip as a GitHub Release asset
#   OUT_DIR       — where to write zips (default: ./tmp/dist)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_STACK="${1:-}"
TARGET_APP="${2:-}"
VERSION_OVERRIDE="${3:-}"
OUT_DIR="${OUT_DIR:-$ROOT_DIR/tmp/dist}"
GITHUB_REPO="${GITHUB_REPO:-forger-ai/apps-catalog}"

mkdir -p "$OUT_DIR"

package_app() {
  local app_dir="$1"
  local app_name
  app_name="$(basename "$app_dir")"
  [[ "$app_name" == "commons" || "$app_name" == "skeleton" ]] && return

  # Read version from manifest.json
  local manifest="$app_dir/manifest.json"
  [[ -f "$manifest" ]] || { echo "  skipping $app_name (no manifest.json)"; return; }

  local version
  version="${VERSION_OVERRIDE:-$(python3 -c "import json,sys; print(json.load(open('$manifest'))['version'])")}"

  local stamp
  stamp="$(date +%Y%m%d_%H%M%S)"
  local zip_name="${app_name}-${version}-${stamp}.zip"
  local zip_path="$OUT_DIR/$zip_name"

  echo "  packaging $app_name v$version..."

  # Stage
  local stage_dir
  stage_dir="$(mktemp -d "${TMPDIR:-/tmp}/${app_name}.stage.XXXXXX")"
  trap 'rm -rf "$stage_dir"' EXIT

  rsync -a \
    --exclude '.git/' --exclude '.git' --exclude '**/.git' --exclude '**/.git/' --exclude '.gitignore' --exclude '.DS_Store' \
    --exclude '.idea/' --exclude '.vscode/' \
    --exclude 'AGENTS.md' --exclude 'tmp/' \
    --exclude 'commons' \
    --exclude 'backend/.venv/' --exclude 'backend/.ruff_cache/' \
    --exclude 'backend/.pytest_cache/' --exclude 'backend/.mypy_cache/' \
    --exclude 'backend/**/__pycache__/' --exclude 'backend/**/*.pyc' \
    --exclude 'backend/data/*.sqlite' --exclude 'backend/data/*.sqlite-*' \
    --exclude 'frontend/node_modules/' --exclude 'frontend/dist/' \
    --exclude 'frontend/.vite/' --exclude 'frontend/*.tsbuildinfo' \
    --exclude 'scripts/' \
    "$app_dir/" "$stage_dir/$app_name/"

  # Copy commons files directly into the app (symlink doesn't survive the zip)
  local commons_be
  commons_be="$(dirname "$app_dir")/commons/backend"
  local commons_fe
  commons_fe="$(dirname "$app_dir")/commons/frontend"

  if [[ -d "$commons_be" ]]; then
    cp "$commons_be"/*.py "$stage_dir/$app_name/backend/app/"
  fi
  if [[ -d "$commons_fe" ]]; then
    cp "$commons_fe"/*.ts "$stage_dir/$app_name/frontend/src/api/"
  fi

  # Defensive cleanup
  find "$stage_dir/$app_name" -name '.git' -exec rm -rf {} + 2>/dev/null || true
  find "$stage_dir/$app_name/backend" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
  find "$stage_dir/$app_name/backend" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete 2>/dev/null || true
  find "$stage_dir/$app_name/backend/data" -type f \
    \( -name '*.sqlite' -o -name '*.sqlite-*' -o -name '*.db' \) -delete 2>/dev/null || true
  find "$stage_dir/$app_name/frontend" -type d -name 'node_modules' -exec rm -rf {} + 2>/dev/null || true
  mkdir -p "$stage_dir/$app_name/backend/data"

  # Zip
  rm -f "$zip_path"
  (cd "$stage_dir" && zip -qr "$zip_path" "$app_name")

  # Checksum + size
  local checksum size
  checksum="$(shasum -a 256 "$zip_path" | awk '{print $1}')"
  size="$(wc -c < "$zip_path" | tr -d ' ')"

  echo "    ✓ $zip_path"
  echo "    sha256: $checksum"
  echo "    size:   $size bytes"

  # Write artifact metadata (used by catalog generation)
  python3 - <<EOF
import json, pathlib
meta = {
    "app": "$app_name",
    "version": "$version",
    "zip": "$zip_name",
    "checksum_sha256": "$checksum",
    "file_size_bytes": $size,
    "packaged_at": "$stamp"
}
out = pathlib.Path("$OUT_DIR/${app_name}-${version}.meta.json")
out.write_text(json.dumps(meta, indent=2))
print(f"    meta:   {out}")
EOF

  # Upload to GitHub Releases if token is available
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    local tag="${app_name}/v${version}"
    echo "    uploading to GitHub Release $tag..."

    # Create release if it doesn't exist
    gh release view "$tag" --repo "$GITHUB_REPO" &>/dev/null || \
      gh release create "$tag" \
        --repo "$GITHUB_REPO" \
        --title "${app_name} v${version}" \
        --notes "Automated release by build_package" \
        --draft=false

    gh release upload "$tag" "$zip_path" \
      --repo "$GITHUB_REPO" \
      --clobber
    echo "    ✓ uploaded to $tag"
  fi

  trap - EXIT
  rm -rf "$stage_dir"
}

process_stack() {
  local stack_dir="$1"
  echo "Stack: $(basename "$stack_dir")"
  if [[ -n "$TARGET_APP" ]]; then
    package_app "$stack_dir/$TARGET_APP"
  else
    for app_dir in "$stack_dir"/*/; do
      [[ -d "$app_dir" ]] && package_app "$app_dir"
    done
  fi
}

if [[ -n "$TARGET_STACK" ]]; then
  process_stack "$ROOT_DIR/$TARGET_STACK"
else
  for stack_dir in "$ROOT_DIR"/*/; do
    [[ -d "$stack_dir/commons" ]] && process_stack "$stack_dir"
  done
fi

echo "✓ build_package done — zips in $OUT_DIR"
