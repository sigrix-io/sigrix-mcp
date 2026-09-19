# Versioning

Semantic versioning, `MAJOR.MINOR.PATCH`, released from a `vX.Y.Z` tag.

- **PATCH**: a fix that changes no tool name, no argument and no request body.
- **MINOR**: a new tool or argument, or a changed description; also every bump
  of `SUPPORTED_API_VERSION`, because a release that pins a new platform
  version stops working against the old one.
- **MAJOR**: a removed or renamed tool, or a changed argument.

Before 1.0 a MINOR bump may carry what would later be MAJOR; the changelog says
so when it does.

`SUPPORTED_API_VERSION` (`src/sigrix_mcp/__init__.py`) is the seller API version
the release was written against. The server reads the platform's
`api_version` once per session and refuses to run on a mismatch; the
platform's own test suite carries the same literal, so the two move together.

## Releasing

A release is a tag. `release.yml` builds the distribution and publishes it on
any `v*` tag pushed to this repository; nothing is uploaded by hand and no API
token exists to leak.

That works because PyPI is configured to trust this repository rather than a
credential, which takes two things that must both be in place before the first
tag — and neither fails loudly if it is missing, so check them rather than
assume:

1. On PyPI, a **trusted publisher** for `sigrix-io/sigrix-mcp`, workflow
   `release.yml`, environment `pypi`.
2. In this repository's settings, an **environment named `pypi`**. The
   publisher's claim names it, so a workflow running outside it is refused.

Then:

```sh
git tag v0.1.0 && git push origin v0.1.0
```

Allow about ten minutes after the upload before expecting `uvx sigrix-mcp` to
resolve the new version: that is the index CDN's cache, not a failed publish.

