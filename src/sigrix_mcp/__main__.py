"""``sigrix-mcp`` / ``python -m sigrix_mcp``: run the server over stdio.

The MCP client spawns this process and talks JSON-RPC over its stdin and
stdout, so nothing may print to stdout. Configuration failures go to stderr
and exit non-zero, which the client surfaces as the server failing to start.
"""

from __future__ import annotations

import sys

from .client import SigrixClient, SigrixConfigError
from .server import configure, server


def main() -> None:
    try:
        configure(SigrixClient.from_env())
    except SigrixConfigError as exc:
        print(f"sigrix-mcp: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    server.run("stdio")


if __name__ == "__main__":
    main()
