# Contributing

Thanks for looking. This is a small, deliberately thin client, and the bar for
a change is that it stays one.

## What to expect

**This is maintained by a very small team.** That shapes everything below, and
it is better said once here than discovered issue by issue.

| | Realistic expectation |
|---|---|
| **Security reports** | Acknowledged within three working days. These jump every queue. |
| **Issues** | Read within a week. A reply may be "noted, not soon." |
| **Pull requests** | Reviewed within two weeks, often longer for anything that changes a request body. |
| **Silence** | Means the queue, not a verdict. Ping the thread. |

Merging is discretionary and stays with the maintainers. Contributions are
genuinely welcome; governance is not open. If that trade is not for you,
Apache-2.0 means you can fork this and go — no hard feelings, and please tell
us what we got wrong.

## Reporting a security issue

**Do not open a public issue.** Email **security@sigrix.io**, and expect an
acknowledgement within three working days. [SECURITY.md](SECURITY.md) is the
full policy. This server holds a seller token and acts on your listings with
it, so anything that leaks or misuses it belongs in that queue rather than
the tracker.

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

## Before opening an issue

The tracker has a form for each of three kinds, because they are triaged
differently. There is no blank issue — not as a filter, but because "which of
these is it" is the question the queue is sorted by, and asking it on the way
in costs you one click and saves a round trip.

- **A defect.** A tool builds the wrong request, or reads the answer wrong.
  Redact your token before pasting anything.
- **A change.** You want a tool this server does not have. Read *What does
  not* above first.
- **"I depend on this."** Not a defect, and very welcome anyway. Knowing who
  is calling which tools is what lets us avoid renaming one out from under
  you — see [VERSIONING.md](VERSIONING.md).

## Working on it

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy --strict src/sigrix_mcp
pytest
```

All four before you push. CI runs the same commands, and the two ruff ones run
*before* the tests — a formatting slip fails the job before a single test
executes.

`mypy --strict` is not optional politeness. The wheel ships
`src/sigrix_mcp/py.typed` and pyproject declares `Typing :: Typed`, which
together tell every consumer's type checker to **trust these annotations**
rather than infer around them. A wrong one does not raise here — it makes
somebody else's `mypy` run confidently green about the wrong thing, which is
the quietest way a package can break a caller.

The tests fake the platform with `httpx.MockTransport`; they pin what the
server sends. Whether the platform still answers those requests is tested in
the platform's own repository, so a change to a route or a body starts there.

## Pull requests

- One change per pull request, with a test that fails without it.
- `CHANGELOG.md` gets a line under *Unreleased*.
- A change to a request body or a tool's name is a breaking change for the
  models that call it; say so in the changelog and expect a minor version bump.
