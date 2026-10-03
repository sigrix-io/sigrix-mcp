"""``sigrix-mcp`` / ``python -m sigrix_mcp``: run the server over stdio.

The MCP client spawns this process and talks JSON-RPC over its stdin and
stdout, so nothing may print to stdout. Configuration failures go to stderr
and exit non-zero, which the client surfaces as the server failing to start.

A person who starts it in a terminal gets one line on stderr saying what it
is waiting for: a stdio server waiting for its client's first message is
silent, and to someone who expected an install step that reads as a hang.
"""

from __future__ import annotations

import sys

from .client import SigrixClient, SigrixConfigError
from .server import configure, server

#: Shown only when stdin is a terminal. A client never sees it: it launches the
#: server with a pipe on stdin. The link is the README section a person needs
#: instead, and ends the line so a terminal's link detection stops at the anchor.
STARTUP_HINT = (
    "sigrix-mcp: this is an MCP server, waiting for an MCP client on stdin (Ctrl+C quits). "
    "Add it to your client's configuration instead: https://github.com/sigrix-io/sigrix-mcp#configure-your-client"
)


def main() -> None:
    try:
        configure(SigrixClient.from_env())
    except SigrixConfigError as exc:
        print(f"sigrix-mcp: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    # After the token check, so a missing token is the only thing said, and
    # before serving, which blocks. Then serve anyway: JSON-RPC typed in by hand
    # still gets answered.
    if sys.stdin.isatty():
        print(STARTUP_HINT, file=sys.stderr, flush=True)
    server.run("stdio")


if __name__ == "__main__":
    main()
