# Forger Apps Catalog — Agent Context

This is the monorepo for all apps distributed through the Forger platform.

## Repo structure

```
{stack-name}/
  skeleton/     Base template for new apps in this stack
  commons/      Shared modules copied into every app via build_setup
    backend/    Python modules (database.py, health.py, cors.py)
    frontend/   TypeScript modules (client.ts)
  {app-name}/   Individual apps (e.g. finance-os)

scripts/
  build_setup   Copies commons → each app (symlinks in dev, hard copy in CI)
  build_check   Runs backend verify + frontend typecheck per app
  build_package Creates versioned ZIPs and uploads to GitHub Releases

.github/
  workflows/
    catalog.yml  Generates catalog.json and publishes to GitHub Pages
```

## How to add a new app

1. Copy the stack's `skeleton/` into a new folder: `{stack}/{app-name}/`
2. Run `./scripts/build_setup.sh {stack} {app-name}` to inject commons
3. Edit `manifest.json` with the app's metadata
4. Develop normally — commons files are symlinked in dev mode

## manifest.json

Every app must have a `manifest.json` at its root. Required fields:

```json
{
  "name": "app-slug",
  "version": "0.1.0",
  "description": "...",
  "stack": { ... },
  "catalog": {
    "display_name": "App Name",
    "short_description": "One line",
    "description": "Full description",
    "category": "finance|productivity|health|...",
    "permissions": ["app_data", "user_selected_imports", "app_exports", "ai_api"],
    "supported_platforms": ["darwin_arm64", "darwin_x64", "win32_x64", "linux_x64"]
  }
}
```

Optional release metadata inside `catalog.release` lets each app publish artifacts
from its own repository while this repo only tracks published versions:

```json
{
  "catalog": {
    "release": {
      "repository": "owner/app-repo",
      "tag_template": "{name}/v{version}",
      "asset_name_template": "{name}-{version}.zip",
      "checksum_sha256": "optional-sha256",
      "file_size_bytes": 123456,
      "published_at": "2026-04-26T12:00:00Z"
    }
  }
}
```

## Scripts

```bash
# Dev setup (symlinks commons into all apps)
./scripts/build_setup.sh

# Run checks on all apps
./scripts/build_check.sh

# Package a specific app
./scripts/build_package.sh vite-fastapi-sqlite finance-os

# Package + upload to GitHub Releases (requires GITHUB_TOKEN)
GITHUB_TOKEN=... ./scripts/build_package.sh vite-fastapi-sqlite finance-os
```

## Rules for agents

- Never modify files inside `commons/` directly from within an app — edit the source in `{stack}/commons/` and re-run `build_setup`
- `skeleton/` is the canonical starting point — keep it minimal and up to date
- `AGENTS.md` files in each app provide app-specific context
- Do not commit `tmp/`, `*.sqlite`, `node_modules`, `.venv`, `__pycache__`
