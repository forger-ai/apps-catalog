#!/usr/bin/env python3
"""
Generate catalog.json from app manifests + GitHub Release metadata.

Usage:
    python3 scripts/generate_catalog.py [--out catalog.json] [--repo owner/repo]

Reads every manifest.json found under stack directories, fetches the latest
GitHub Release for each app (if GITHUB_TOKEN is set), and writes a catalog.json
consumable by the Forger desktop app.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def find_manifests() -> list[tuple[str, dict]]:
    """Walk stack dirs and collect (stack_name, manifest_data) for each app."""
    results = []
    for stack_dir in sorted(ROOT.iterdir()):
        if not stack_dir.is_dir() or stack_dir.name.startswith("."):
            continue
        if not (stack_dir / "commons").is_dir():
            continue  # not a stack folder
        for app_dir in sorted(stack_dir.iterdir()):
            if app_dir.name in ("commons", "skeleton") or not app_dir.is_dir():
                continue
            manifest_path = app_dir / "manifest.json"
            if not manifest_path.exists():
                print(f"  warn: no manifest.json in {app_dir.relative_to(ROOT)}", file=sys.stderr)
                continue
            manifest = json.loads(manifest_path.read_text())
            results.append((stack_dir.name, manifest))
    return results


def gh_release_asset(repo: str, tag: str) -> dict | None:
    """Fetch the first .zip asset from a GitHub Release via gh CLI."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return None
    try:
        result = subprocess.run(
            ["gh", "release", "view", tag, "--repo", repo, "--json", "assets,publishedAt"],
            capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
        zips = [a for a in data.get("assets", []) if a["name"].endswith(".zip")]
        if not zips:
            return None
        asset = zips[0]
        return {
            "download_url": asset["url"],
            "file_size_bytes": asset["size"],
            "download_count": asset.get("downloadCount", 0),
            "published_at": data.get("publishedAt"),
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return None


def build_entry(stack: str, manifest: dict, repo: str) -> dict | None:
    name = manifest.get("name", "")
    version = manifest.get("version", "0.0.0")
    catalog_meta = manifest.get("catalog", {})

    tag = f"{name}/v{version}"
    release = gh_release_asset(repo, tag)

    entry: dict = {
        "slug": name,
        "name": catalog_meta.get("display_name", name),
        "short_description": catalog_meta.get("short_description", ""),
        "description": catalog_meta.get("description", manifest.get("description", "")),
        "category": catalog_meta.get("category", "utilities"),
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
            "checksum_sha256": None,  # set by build_package via meta.json
            "published_at": release["published_at"] if release else None,
        },
    }

    # Enrich checksum from meta.json if available
    meta_path = ROOT / "tmp" / "dist" / f"{name}-{version}.meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        entry["latest_version"]["checksum_sha256"] = meta.get("checksum_sha256")

    return entry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="catalog.json")
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPO", "forger-ai/apps-catalog"))
    args = parser.parse_args()

    manifests = find_manifests()
    print(f"Found {len(manifests)} app(s)")

    catalog = []
    for stack, manifest in manifests:
        print(f"  building entry: {manifest.get('name')} ({stack})")
        entry = build_entry(stack, manifest, args.repo)
        if entry:
            catalog.append(entry)

    out_path = Path(args.out)
    out_path.write_text(json.dumps(catalog, indent=2))
    print(f"✓ wrote {out_path} ({len(catalog)} entries)")


if __name__ == "__main__":
    main()
