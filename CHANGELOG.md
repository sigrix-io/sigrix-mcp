# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the versioning is
described in `VERSIONING.md`.

## [Unreleased]

## [0.2.1] — 2026-10-03

A PATCH release under `VERSIONING.md`: nothing in it changes a tool name, an
argument, a request body or a description. What an MCP client sees changes in
one place: a tool call that fails now carries the reason, where it carried
only `Error executing tool <name>`. A person who starts the server in a
terminal also gets a line on stderr saying what it is waiting for.

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

- The README opens with badges for the PyPI release, the Python versions, CI
  and the licence; *Get a token* links the settings card the token is made
  on; and a new *Where it fits* section places the server among the other
  projects Sigrix publishes. Its links to `CONTRIBUTING.md`, `VERSIONING.md`
  and `SECURITY.md` are absolute now: the README is the PyPI page too, and
  PyPI resolves a relative link against pypi.org, where none of those files
  are. The next release carries it there. Nothing the server sends changes.
- Dependabot opens one pull request per ecosystem instead of one per
  dependency. The branch ruleset only merges a pull request that is up to date
  with `main`, so each separate update merged put every other one behind.
  Nothing in the package changes.
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

### Fixed

- A tool that fails now tells the model why. From mcp 2.1 the SDK reports
  anything a tool raises other than `ToolError` as a bare `Error executing tool
  <name>`, keeping the reason on the server's stderr, and every failure this
  server anticipates was raised some other way — so the platform's own words
  never reached the model: not the publish gate's missing labels on a refused
  `submit_for_review`, not the version pin's "upgrade", not the SKILL.md
  parser's message. A seller's `import_skill_md` failed twice with nothing else
  to go on. A refusal from the platform, an argument a tool refuses itself, a
  file it cannot read or write and a platform it cannot reach are now raised as
  `ToolError`; anything else is still a crash, and its text still stays on the
  server. The tests read failures through a real client session now, because
  calling a tool function directly skips the layer that decides what the model
  sees — which is how the suite stayed green throughout. No tool name,
  argument, description or request body changes.
- Started by hand in a terminal, the server now says what it is doing: one
  line on **stderr**, naming it an MCP server waiting for an MCP client on
  stdin, pointing at the README's *Configure your client*, and saying Ctrl+C
  quits. Then it serves as before, so JSON-RPC typed in by hand is still
  answered. A seller on macOS pasted the README's install line into a terminal
  and saw nothing until Ctrl+C: the token check had passed, and the SDK was
  waiting, correctly and silently, for a first message that was never coming.
  The line appears only when stdin is a terminal, which it never is when a
  client launches the server (a client hands it a pipe), and never on stdout,
  the protocol channel. `tests/test_main.py` pins both, in-process and against
  the running server on a pseudo-terminal.
- The README's *Install* section put `uvx sigrix-mcp` in a code block, as if it
  were the install step, and that is the line the seller ran. It now says the
  MCP client runs that command itself, so there is nothing to install or run
  by hand, and that `pipx install sigrix-mcp` is only for a pinned, installed
  copy, whose `command` is then `sigrix-mcp`. *Configure your client* gains
  **VS Code**: the same `mcpServers` block in the user-level
  `~/.copilot/mcp-config.json`, the portable file VS Code's documentation now
  prefers for new servers, rather than a workspace file the token could be
  committed in.

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
