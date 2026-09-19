"""sigrix-mcp: publish listings to Sigrix from an MCP client.

A thin client, not a product. Every tool is one request to one route of
the Sigrix seller API; the server carries no model calls, no validation of
its own and no secret beyond the token. Nothing it does goes live: a
submission enters the platform's moderation queue, and a moderator decides.
"""

from __future__ import annotations

__version__ = "0.1.0"

#: The seller API version this release was written against. ``GET
#: /api/categories`` serves the platform's own ``api_version``; the client
#: refuses to run against any other value, because a route or a body the
#: platform reshaped would otherwise fail one tool at a time, confusingly.
SUPPORTED_API_VERSION = "1"

__all__ = ["SUPPORTED_API_VERSION", "__version__"]
