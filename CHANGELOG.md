# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the versioning is
described in `VERSIONING.md`.

## [Unreleased]

### Security

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
