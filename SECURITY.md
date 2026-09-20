# Security Policy

This is a client that holds a credential and runs on your machine with your
privileges. That is the whole of its attack surface and it is worth naming
plainly.

## Reporting a vulnerability

**Do not open a public issue.**

Email **security@sigrix.io** with what you found and how to reproduce it. You
will get an acknowledgement within three working days and an assessment as
soon as we have one. [CONTRIBUTING.md](CONTRIBUTING.md) publishes the queues
everything else waits in; security reports jump all of them.

Redact your token before attaching anything.

## What this server holds

One secret: the seller API token in `SIGRIX_SELLER_TOKEN`. The server sends it
only in the `Authorization` header of requests to `SIGRIX_BASE_URL`, never
logs it, and never writes it to disk. The token can create, edit and submit
the holder's own draft listings for review; it cannot approve or publish, and
it reaches no other route on the platform.

If a token leaks, revoke or regenerate it on the Sigrix account settings page.
The old token stops working on the next request.

## What is in scope

- **Anything that moves the token somewhere it should not be.** A log line, an
  exception message, a temporary file, a retry that follows a redirect to
  another host, or a request built against a host other than the configured
  `SIGRIX_BASE_URL`.
- **The filesystem reach of `import_skill_md` and `export_skill_md`.** These
  take a path and read or write it — `import_skill_md` reads the file and
  sends its contents to the platform, `export_skill_md` writes to the path it
  is given. The path comes from the caller, which in normal use is a *model*
  deciding what to read. The MCP client's own approval prompt is the boundary
  there, and that is the designed arrangement rather than a defect. What *is*
  a finding: a way to make either tool touch a path the client did not show
  the user, or a way to reach one without the client getting the chance to
  ask.
- **The API version pin.** The server refuses to run against a platform
  serving an `api_version` it does not know. A way to make it proceed anyway,
  or to satisfy the check from something that is not the configured platform,
  is a finding.
- **Defects in the repository itself**: the CI workflows, the packaging, and
  the contents of the published wheel.

## What is not in scope

- **What a valid token is allowed to do.** The token's reach is the platform's
  decision, enforced server-side. If you think it reaches too far, that is a
  report about the platform — see below — not about this client.
- **Moderation outcomes.** Nothing this server submits goes live; a moderator
  decides. A listing you disagree with is not a vulnerability.
- **A model calling a tool you did not want called.** An MCP server executes
  what the client asks of it. Which calls to approve is the client's job and
  yours; this package cannot make that judgement from inside a tool
  implementation. A way to *bypass* the client's approval is in scope — see
  above.
- **Vulnerabilities in `mcp` or `httpx`.** Report those upstream. If one is
  reachable in a way this package makes worse — a default we chose, a guard we
  removed — that is in scope here; say so.

## Supported versions

| Version | Status |
|---|---|
| 0.2.x | Pre-release — supported |

This package is pre-1.0 and [VERSIONING.md](VERSIONING.md) says what that
means. There is no back-porting, because there is nothing to back-port to: a
finding lands on `main` and goes out in the next release.

## What to report to the platform instead

Anything about the seller API itself — what a token can reach, how a draft is
moderated — is the platform's, not this client's. Report it to the same
address; it will be routed.
