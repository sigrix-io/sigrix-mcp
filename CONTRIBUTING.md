# Contributing

Thanks for looking. This is a small, deliberately thin client, and the bar for
a change is that it stays one.

## What fits

- A bug in how a tool builds its request or reads the answer.
- A new tool that is one request to one seller API route that exists.
- Better tool descriptions and prompts — they are what the host model reads.
- Client configuration examples for an MCP client not covered in the README.

## What does not

- Validation of listing content on this side. `check_draft` is the authority;
  a rule copied here drifts the first time the platform moves it.
- Model calls, caching, or state beyond the process.
- Anything that reads or writes something other than the seller's own listings.

## Working on it

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check . && pytest
```

The tests fake the platform with `httpx.MockTransport`; they pin what the
server sends. Whether the platform still answers those requests is tested in
the platform's own repository, so a change to a route or a body starts there.

## Pull requests

- One change per pull request, with a test that fails without it.
- `CHANGELOG.md` gets a line under *Unreleased*.
- A change to a request body or a tool's name is a breaking change for the
  models that call it; say so in the changelog and expect a minor version bump.
