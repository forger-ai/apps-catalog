#!/usr/bin/env python3
"""
Generate catalog.json from app manifests + GitHub Release metadata.

Usage:
    python3 scripts/generate_catalog.py [--out catalog.json] [--default-repo owner/repo]

Reads every app manifest.json found under stack directories, fetches release
metadata for each app, and writes a catalog.json consumable by the Forger
desktop app.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def find_manifests() -> list[tuple[str, Path, dict]]:
    """Walk stack dirs and collect (stack_name, app_dir, manifest_data) for each app."""
    results = []
    for stack_dir in sorted(ROOT.iterdir()):
        if not stack_dir.is_dir() or stack_dir.name.startswith("."):
            continue
        for app_dir in sorted(stack_dir.iterdir()):
            if not app_dir.is_dir() or app_dir.name.startswith("."):
                continue
            manifest_path = app_dir / "manifest.json"
            if not manifest_path.exists():
                continue
            manifest = json.loads(manifest_path.read_text())
            results.append((stack_dir.name, app_dir, manifest))
    return results


def gh_release_asset(repo: str, tag: str, expected_asset: str | None = None) -> dict | None:
    """Fetch a zip asset from a GitHub Release via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "release", "view", tag, "--repo", repo, "--json", "assets,publishedAt"],
            capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
        assets = data.get("assets", [])
        if expected_asset:
            zips = [a for a in assets if a.get("name") == expected_asset]
        else:
            zips = [a for a in assets if a.get("name", "").endswith(".zip")]
        if not zips:
            return None
        asset = zips[0]
        return {
            "download_url": asset.get("url"),
            "file_size_bytes": asset["size"],
            "download_count": asset.get("downloadCount", 0),
            "published_at": data.get("publishedAt"),
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return None


def public_asset_path(stack: str, app_dir: Path, manifest: dict, out_path: Path) -> str | None:
    catalog_meta = manifest.get("catalog", {})
    icon_path = catalog_meta.get("icon_path")
    if not icon_path or not isinstance(icon_path, str):
        return None

    source = (app_dir / icon_path).resolve()
    try:
        source.relative_to(app_dir.resolve())
    except ValueError:
        raise ValueError(f"{manifest.get('name')} catalog.icon_path must stay inside the app catalog folder")

    if not source.is_file():
        return None

    relative_asset = Path("assets") / stack / manifest.get("name", app_dir.name) / Path(icon_path).name
    destination = out_path.parent / relative_asset
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return str(relative_asset)


def build_entry(stack: str, app_dir: Path, manifest: dict, default_repo: str, out_path: Path) -> dict | None:
    name = manifest.get("name", "")
    version = manifest.get("version", "0.0.0")
    catalog_meta = manifest.get("catalog", {})
    release_meta = catalog_meta.get("release", {})

    release_repo = release_meta.get("repository", default_repo)
    tag_template = release_meta.get("tag_template", "{name}/v{version}")
    asset_template = release_meta.get("asset_name_template")
    tag = tag_template.format(name=name, version=version)
    expected_asset = asset_template.format(name=name, version=version) if asset_template else None

    release = gh_release_asset(release_repo, tag, expected_asset=expected_asset)
    fallback_download_url = (
        f"https://github.com/{release_repo}/releases/download/{tag}/{expected_asset}"
        if expected_asset
        else None
    )

    resolved_download_url = fallback_download_url or (release["download_url"] if release else None)
    version_changelog = next(
        (
            item
            for item in manifest.get("changelog", [])
            if isinstance(item, dict) and item.get("version") == version
        ),
        None,
    )
    capabilities = catalog_meta.get("capabilities")
    if capabilities is None:
        capabilities = catalog_meta.get("permissions", [])

    icon_url = public_asset_path(stack, app_dir, manifest, out_path)

    entry: dict = {
        "slug": name,
        "name": catalog_meta.get("display_name", name),
        "short_description": catalog_meta.get("short_description", ""),
        "description": catalog_meta.get("description", manifest.get("description", "")),
        "category": catalog_meta.get("category", "utilities"),
        "icon_url": icon_url,
        "beta": bool(catalog_meta.get("beta", False)),
        "runtime_stack": stack.replace("-", "_"),
        "latest_version": {
            "version": version,
            "runtime_stack": stack.replace("-", "_"),
            "required_python_version": manifest.get("stack", {}).get("backend", {}).get("python_version", ""),
            "required_node_version": manifest.get("stack", {}).get("frontend", {}).get("node_version", ""),
            "supported_platforms": catalog_meta.get("supported_platforms", ["darwin_arm64", "darwin_x64"]),
            "capabilities": capabilities,
            "download_url": resolved_download_url,
            "file_size_bytes": release["file_size_bytes"] if release else release_meta.get("file_size_bytes"),
            "checksum_sha256": release_meta.get("checksum_sha256"),
            "published_at": release["published_at"] if release else release_meta.get("published_at"),
            "changelog": version_changelog,
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
    parser.add_argument("--default-repo", default=os.getenv("GITHUB_REPO", "forger-ai/apps-catalog"))
    args = parser.parse_args()

    out_path = Path(args.out)
    manifests = find_manifests()
    print(f"Found {len(manifests)} app(s)")

    catalog = []
    for stack, app_dir, manifest in manifests:
        print(f"  building entry: {manifest.get('name')} ({stack})")
        entry = build_entry(stack, app_dir, manifest, args.default_repo, out_path)
        if entry:
            catalog.append(entry)

    out_path.write_text(json.dumps(catalog, indent=2))
    print(f"✓ wrote {out_path} ({len(catalog)} entries)")


if __name__ == "__main__":
    main()
