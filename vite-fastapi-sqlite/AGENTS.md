# Stack: vite-fastapi-sqlite

This folder contains published catalog metadata for apps that use the
`vite-fastapi-sqlite` stack.

Each app folder contains a `manifest.json` file. The manifest is the published
contract consumed by the Forger desktop app. It describes visible catalog data,
runtime requirements, release metadata, services, declared capabilities, scripts,
and shipped skills for the installable release.

The catalog does not contain the stack commons, skeleton, backend source,
frontend source, local databases, dependency directories, or app release
packages. Those files live in their own source repositories and release assets.

Appropriate changes in this folder:

- update a published app manifest;
- correct display metadata;
- update release checksum, size, publish date, or download metadata;
- add a new app folder containing only its published `manifest.json`.

Changes that belong in app or stack repositories:

- backend or frontend code;
- stack commons;
- skeleton code;
- operational scripts;
- app skills;
- functional documentation;
- release packaging.
