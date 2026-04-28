# AGENTS

## Source of Truth

This repo contains the public app catalog read by the Forger desktop application.

The catalog is not the main implementation source for apps. Each app keeps its code, releases, CI, and history in its own repository. This repo contains published and approved metadata that lets desktop discover, download, and install apps.

When an app repo publishes a new version, its release workflow opens a PR against this repo to update that app manifest inside the catalog. When that PR is approved and merged, the catalog workflow regenerates `catalog.json` and publishes it on GitHub Pages.

## Catalog Role

The catalog is the published contract between installable apps and the desktop app.

Desktop uses the catalog to know:

- which apps are available;
- which version is published;
- which runtime stack each app uses;
- which platforms are supported;
- which capabilities are declared for transparency;
- which URL downloads the installable ZIP;
- which checksum, size, and publish date correspond to the ZIP when available;
- which visible metadata should be shown to the user.

The catalog must not invent product capabilities. Visible capabilities for each app are documented in the app repo `AGENTS.md` and internal documentation.

## Current Structure

```text
{stack-name}/
  commons/      Published copy of shared stack pieces when applicable
  skeleton/     Published stack base when applicable
  {app-name}/   Published metadata for an installable app

scripts/
  generate_catalog.py   Generates catalog.json from manifests and release metadata
  build_setup.sh        Internal tool for preparing commons in compatibility structure
  build_check.sh        Internal verification tool
  build_package.sh      Internal compatibility packaging tool

.github/
  workflows/
    catalog.yml         Generates catalog.json and publishes GitHub Pages
    validate.yml        Validates catalog changes
```

The currently published stack is `vite-fastapi-sqlite`.

The currently published app in that stack is `finance-os`.

## Current Publication Flow

The publication flow from an app to the catalog works as follows:

1. The app lives and is developed in its own repository.
2. The app defines metadata in `manifest.json`.
3. The app defines `catalog.release` with the release repo, tag format, ZIP asset name, catalog repo, and manifest path inside the catalog.
4. When a valid release/tag is published, the app repo workflow verifies backend and frontend.
5. The workflow builds the installable ZIP.
6. The workflow calculates checksum, size, and publish date.
7. The workflow uploads the ZIP to the app GitHub Release.
8. The workflow checks out this catalog repo.
9. The workflow updates the published app manifest at the configured path.
10. The workflow opens an automatic PR against `main`.
11. A person or agent reviews the PR.
12. When the PR is merged, `catalog.yml` generates `catalog.json`.
13. GitHub Pages publishes `catalog.json`.
14. The desktop app reads the published catalog.

PR approval is the catalog control point. An app release is not available to desktop until the corresponding change enters the published catalog.

## `manifest.json`

Each published app in the catalog has a `manifest.json` in its app folder.

Relevant functional fields:

- `name`: stable technical app slug.
- `version`: published version considered available by desktop.
- `description`: general app description.
- `changelog`: list of visible changes by published version.
- `stack`: backend, frontend, database, and required version metadata.
- `catalog.display_name`: visible name in catalog.
- `catalog.short_description`: short summary.
- `catalog.description`: fuller visible description.
- `catalog.category`: visible category.
- `catalog.capabilities`: visible app capabilities declared for transparency.
- `catalog.supported_platforms`: supported platforms.
- `catalog.release.repository`: repo where the GitHub Release with the ZIP lives.
- `catalog.release.tag_template`: published tag format.
- `catalog.release.asset_name_template`: published ZIP format.
- `catalog.release.checksum_sha256`: ZIP checksum when registered.
- `catalog.release.file_size_bytes`: ZIP size when registered.
- `catalog.release.published_at`: publish date when registered.

The manifest can contain services, scripts, and skills. Those fields help desktop and the agent operate the installed app. They are not a list of visible capabilities for the final user.

## `catalog.json`

`scripts/generate_catalog.py` reads published manifests under stack folders and generates `catalog.json`.

The output contains a list of apps with:

- `slug`;
- `name`;
- `short_description`;
- `description`;
- `category`;
- `runtime_stack`;
- `latest_version`.

`latest_version` contains installation metadata:

- `version`;
- `runtime_stack`;
- required Python and Node versions;
- supported platforms;
- capabilities;
- download URL;
- size;
- checksum;
- publish date;
- changelog for the published version when declared.

The script attempts to read GitHub Release metadata using `gh release view`. If an expected asset is configured, the download URL is resolved from the repo, tag, and asset name.

## Agent Rules

- Treat this repo as the published catalog, not as the main development repo for apps.
- Do not modify product code for an app inside the catalog if the change belongs in the app source repo.
- For functional app changes, work in the app repo and let its release update the catalog by PR.
- In this repo, especially review manifests, release metadata, checksums, versions, capabilities, and catalog consistency.
- Do not present `manifest.json`, scripts, or workflows as the normal interface for final users.
- Describe only visible impact to final users: app availability, version, description, capabilities, and publication status.
- Do not say an app is available in desktop if the catalog PR has not been merged and published.
- Do not invent app capabilities from catalog marketing copy; validate against the app repo and its `AGENTS.md`.
- If an app folder inside the catalog contains copied code, treat it as a published snapshot or compatibility structure, not as the main source of truth.

## Change Rules

Appropriate changes in this repo:

- update a published app manifest;
- review release metadata;
- correct visible catalog data;
- adjust `catalog.json` generation;
- adjust catalog validations;
- maintain catalog documentation.

Changes that belong in the app repo:

- modifying backend;
- modifying frontend;
- modifying database;
- modifying app operational scripts;
- modifying app skills;
- changing functional capabilities;
- changing app-specific functional documentation.

## Communication

Use simple language when the user asks about the catalog.

Explain the catalog as the published list of apps desktop can install.

Avoid internal details unless the user explicitly asks for them.

When speaking with a final user:

- say "the app is available in the catalog" only if it is published;
- say "there is an update pending approval" if there is an unmerged PR;
- say "desktop downloads the app from the published version" instead of explaining GitHub Releases, assets, and manifests.
