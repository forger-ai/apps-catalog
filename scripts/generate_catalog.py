#!/usr/bin/env python3
"""
Generate catalog.json from registry.json + GitHub Release metadata.

Usage:
    python3 scripts/generate_catalog.py [--out catalog.json]

Reads registry.json for the list of app repos, fetches each app's manifest.json
and latest GitHub Release, then writes catalog.json for the Forger desktop app.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_registry() -> list[dict]:
    registry_path = ROOT / "registry.json"
    if not registry_path.exists():
        print("error: registry.json not found", file=sys.stderr)
        sys.exit(1)
    return json.loads(registry_path.read_text())


def fetch_manifest(repo: str) -> dict | None:
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/manifest.json", "--jq", ".content"],
            capture_output=True, text=True, check=True,
        )
        raw = base64.b64decode(result.stdout.strip()).decode()
        return json.loads(raw)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"  warn: could not fetch manifest from {repo}: {e}", file=sys.stderr)
        return None


def fetch_latest_release(repo: str) -> dict | None:
    try:
        result = subprocess.run(
            ["gh", "release", "view", "--repo", repo,
             "--json", "tagName,assets,publishedAt,body"],
            capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
        zips = [a for a in data.get("assets", []) if a["name"].endswith(".zip")]
        if not zips:
            return None
        asset = zips[0]
        return {
            "tag": data["tagName"],
            "download_url": asset["url"],
            "file_size_bytes": asset["size"],
            "download_count": asset.get("downloadCount", 0),
            "published_at": data.get("publishedAt"),
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def build_entry(stack: str, repo: str, manifest: dict, release: dict | None) -> dict:
    name = manifest.get("name", "")
    version = manifest.get("version", "0.0.0")
    catalog_meta = manifest.get("catalog", {})

    return {
        "slug": name,
        "name": catalog_meta.get("display_name", name),
        "short_description": catalog_meta.get("short_description", ""),
        "description": catalog_meta.get("description", manifest.get("description", "")),
        "category": catalog_meta.get("category", "utilities"),
        "repo": repo,
        "runtime_stack": stack.replace("-", "_"),
        "latest_version": {
            "version": version,
            "runtime_stack": stack.replace("-", "_"),
            "required_python_version": manifest.get("stack", {}).get("backend", {}).get("python_version", ""),
            "required_node_version": manifest.get("stack", {}).get("frontend", {}).get("node_version", ""),
            "supported_platforms": catalog_meta.get("supported_platforms", ["darwin_arm64", "darwin_x64"]),
            "permissions": catalog_meta.get("permissions", ["app_data"]),
            "download_url": release["download_url"] if release else None,
            "file_size_bytes": release["file_size_bytes"] if release else None,
            "checksum_sha256": None,
            "published_at": release["published_at"] if release else None,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="catalog.json")
    args = parser.parse_args()

    registry = load_registry()
    print(f"Registry: {len(registry)} app(s)")

    catalog = []
    for entry in registry:
        repo = entry["repo"]
        stack = entry["stack"]
        print(f"  processing {repo}...")

        manifest = fetch_manifest(repo)
        if not manifest:
            continue

        release = fetch_latest_release(repo)
        if not release:
            print(f"    warn: no release found for {repo}")

        catalog.append(build_entry(stack, repo, manifest, release))

    out_path = Path(args.out)
    out_path.write_text(json.dumps(catalog, indent=2))
    print(f"✓ wrote {out_path} ({len(catalog)} entries)")


if __name__ == "__main__":
    main()
