# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the versioning is
described in `VERSIONING.md`.

## [Unreleased]

### Added

- `tests/test_workflow_pins.py` asserts that every `uses:` in both workflows
  names a 40-character commit and carries the `# vX.Y.Z` comment Dependabot
  rewrites. This repository now calls `sigrix-io/actions`, and those pins being
  ours makes them *more* important to hold, not less: `@main` would be
  convenient and would mean a change made in another repository reaching this
  one's release with no commit here to point at. `tests/test_release_workflow.py`
  narrows to the property only it covers — that the release stores no
  credential at all — rather than repeating the pin assertions.

### Changed

- Both workflows now call `sigrix-io/actions`, a new repository holding the
  composite actions the Sigrix projects share. Eleven `uses:` lines across the
  three repositories named the same two upstream commit pins; here they drop
  to **zero** — every Python job is one `uses:` line, and the only upstream
  pins left in this repository are the two artifact actions, used once each.
  A pin only stays correct if something bumps it, and three Dependabot queues
  editing the same two actions is how mullion came to run floating tags while
  postern was pinned. The publish step is deliberately untouched: a reusable
  workflow cannot publish to PyPI, because trusted publishing matches the OIDC
  claim against the workflow that ran — which is why these are composite
  actions, that run inside the caller's job.

- Repository setup now matches the other open Sigrix repositories. CI gains a
  separate `lint` job, a `build` job that installs the built wheel into a clean
  environment, and a `ci-passed` aggregate job — one check to require on `main`,
  so adding a Python version to the matrix no longer means editing a branch
  protection rule to match. The build job is what would now catch
  `seller_api_openapi.json` failing to ship: `server.py` reads it through
  `importlib.resources`, and an editable install finds it in the source tree
  whether or not the wheel carries it.
- `ruff` and `mypy` are pinned exactly in the dev extra, and both CI jobs
  install them from there rather than naming a version of their own — so a
  local `ruff format` and the CI check cannot disagree, and an unrelated
  checker release cannot turn a commit that changed nothing red. The ruff
  rule set gains `SIM` (flake8-simplify); line length stays at 120.
- `SECURITY.md` now states what is and is not in scope, including the
  filesystem reach of `import_skill_md` and `export_skill_md` and where the
  MCP client's approval prompt is the boundary. `CONTRIBUTING.md` publishes
  the review queues, and both it and the README list the checks CI runs.
- `release.yml` gains the guards the sibling repositories run: a fork guard, a
  non-cancelling concurrency group, `twine check`, a changelog gate, and a
  wheel-installed run of the suite. The tag/version check now reads the built
  wheel rather than `pyproject.toml`, so it compares the tag against what was
  actually packaged.

### Added

- `release.yml` gains a `verify` job, adapted from `sigrix-io/postern`: after
  the upload, it installs `sigrix-mcp==<tag>` from PyPI **by name** and runs
  it. An upload that succeeds is not the same as a package anyone can
  install, and the two look identical from the publish step — a green tick.
  This is what tells them apart, and it is the only check here that exercises
  the artifact the world actually gets rather than a local file. Its retry
  window is ten minutes rather than postern's two and a half, because
  VERSIONING.md tells a reader to allow about that long for the index's CDN
  cache, and a check that gave up sooner than the documentation says to wait
  would report a healthy release as a failure.
- The package now ships type information: `src/sigrix_mcp/py.typed` and the
  `Typing :: Typed` classifier, with a `types` job running `mypy --strict` on
  every change. That is a promise to consumers — their checker will trust
  these annotations rather than infer around them — so CI now proves both
  halves of it: the annotations check, and the marker actually ships in the
  wheel. Fixing the two errors strict mode found also removed an `Any` that
  was escaping `_load_schema` into every caller.
- `CODE_OF_CONDUCT.md`, issue forms, a pull request template, and a Dependabot
  configuration for the pip and github-actions ecosystems — the same set the
  other open repositories carry. Dependabot is also what keeps the publish
  action's commit pin current, which nothing moved before.

### Security

- **Every** action in both workflows is now pinned to a commit with a
  `# vX.Y.Z` comment beside it, rather than to a mutable tag — the same SHAs
  `sigrix-io/postern` already carries. A tag is moved by whoever owns the
  action, so a retagged release could otherwise reach CI with nothing in this
  repository recording it. The Dependabot entry above is what keeps the pins
  from going stale, which is the other half of that trade.
- The release workflow pins `pypa/gh-action-pypi-publish` to a commit rather
  than to `release/v1`. That reference is a branch, so the step holding upload
  rights to PyPI could change under a tagged release with nothing here
  recording it. The pin is what the branch pointed at when it was made, so
  nothing about the current release changes; `tests/test_release_workflow.py`
  is what notices if it goes back, and that the workflow still stores no
  credential.

## [0.2.0] — 2026-09-20

A MINOR bump rather than a patch because a tool description changed, which is
what `VERSIONING.md` says that is — the release carries no new tool, no new
argument and no change to any request body.

### Fixed

- `update_draft` now states the **type** of every field it accepts, derived
  from the same vendored schema the field names already came from. The names
  were derived and the types discarded, so the description listed
  `compatibility` and `allowed_tools` side by side with nothing saying that the
  first is a string and the second a list of strings. Drafting a skill listing
  against the live platform, a model guessed and the platform refused the
  payload — a poor way to learn a type this package was already shipping.
  A union of two real types is left unlabelled rather than guessed at; every
  field on the current schema resolves to an honest one.

## [0.1.0] — 2026-09-18

First release, against seller API version `1`.

### Added

- Tools: `list_categories`, `list_my_listings`, `get_listing`, `create_draft`,
  `update_draft`, `check_draft`, `submit_for_review`, `import_skill_md`,
  `export_skill_md`.
- Prompts: `draft_prompt_listing`, `draft_persona_listing`, `draft_skill_listing`.
- The API version pin: the server refuses a platform whose `api_version` it
  does not know.
- Tool descriptions derived from the platform's OpenAPI document
  (`seller_api_openapi.json`, refreshed by `scripts/sync_schemas.py`).
