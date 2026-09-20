## What this changes

<!-- One or two sentences. The diff shows what changed; say why. -->

## Does it change what the server sends, or what the model reads?

<!--
The two contracts this repository has. Delete the rows that do not apply.

- [ ] No — docs, tests or tooling only.
- [ ] A request body, a route, or a tool's **name** changed. That is a
      breaking change for the models already calling it: say so in the
      changelog and expect a minor bump (see VERSIONING.md).
- [ ] A tool **description** or prompt changed. These are what the host model
      reads to decide what to call, so a wording change is a behaviour change
      even though no test needs to move. Say what you expect it to change.
- [ ] The pinned seller API version (`SUPPORTED_API_VERSION`) changed.
-->

## The test that fails without it

<!--
CONTRIBUTING asks for one change per pull request, with a test that fails
without it. Name the test here.

The suite fakes the platform with `httpx.MockTransport` and pins what the
server sends — so a test asserting what *this* code builds is in scope, and
whether the platform still answers it belongs in the platform's own
repository.
-->

## Checks

- [ ] `pytest`
- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] Scope: still a thin client — one tool is one request to one route (see CONTRIBUTING)
- [ ] `CHANGELOG.md` updated under `Unreleased`, if this is user-visible
