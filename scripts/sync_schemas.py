#!/usr/bin/env python3
"""Refresh ``src/sigrix_mcp/seller_api_openapi.json`` from a running platform.

The server describes its tools from the platform's own OpenAPI document —
the request models and the seller API paths — rather than from a hand-written
copy. Run this against the platform after a seller API change, review the
diff, bump ``SUPPORTED_API_VERSION`` if ``api_version`` moved, and release.

    python scripts/sync_schemas.py https://sigrix.io
    python scripts/sync_schemas.py http://127.0.0.1:8000

**Prose is dropped on the way in.** A route's ``description`` in that document
is its handler's docstring, written for the people who maintain it: the first
version vendored here carried five of the platform's issue numbers, four
private function names and the name of a moderator-only override header. None
of it is read on this side — the tools' descriptions are written in
``server.py`` and only the schemas' *field names* come from this file — so the
one thing this file needs from the source is its shape. Redacting at the seam
rather than by hand is the point: a hand-edited file is clean until the next
refresh silently puts it all back.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

PATHS = (
    "/api/categories",
    "/api/items/mine",
    "/api/items/register",
    "/api/items/{item_type}/{item_id}",
    "/api/items/{item_type}/{item_id}/check",
    "/api/items/{item_type}/{item_id}/submit",
    "/api/items/skill/import",
    "/api/items/skill/{item_id}/skill.md",
)
COMPONENTS = (
    "ItemRegistration",
    "ItemUpdate",
    "ImportSkillRequest",
    "ImportSkillResponse",
    "CreatedDraftPayload",
    "CategoriesResponse",
    "CategoryOut",
    "MyListingsResponse",
    "MyListingOut",
)
TARGET = Path(__file__).resolve().parents[1] / "src" / "sigrix_mcp" / "seller_api_openapi.json"

#: Keys whose values are prose written for the platform's own maintainers.
#: ``title`` is kept: FastAPI generates it from the field name ("Item Type"),
#: so it carries nothing a reader cannot already see in the property key.
PROSE_KEYS = ("description", "summary")


def _strip_prose(node: object) -> object:
    """Every ``description`` and ``summary``, at any depth, removed."""

    if isinstance(node, dict):
        return {key: _strip_prose(value) for key, value in node.items() if key not in PROSE_KEYS}
    if isinstance(node, list):
        return [_strip_prose(item) for item in node]
    return node


def _drop_header_parameters(subset: dict) -> dict:
    """Header parameters removed; path and query parameters kept.

    This client sends exactly one header and it is the ``Authorization`` the
    security scheme describes, so a header *parameter* in the platform's
    document is, by construction, somebody else's surface. The first vendored
    copy carried one belonging to a role a seller token can never hold — the
    kind of thing that is not a vulnerability and is still nobody's business
    out here.
    """

    for operations in subset.get("paths", {}).values():
        for operation in operations.values():
            if isinstance(operation, dict) and "parameters" in operation:
                operation["parameters"] = [p for p in operation["parameters"] if p.get("in") != "header"]
    return subset


def redact(subset: dict) -> dict:
    """What the platform's document says, minus what only the platform needs.

    Nothing on this side reads either of the things this removes: the tools'
    descriptions are written in ``server.py``, and only the *field names* of
    the component schemas are read from this file. What is left is the shape,
    which is the whole reason to vendor it.
    """

    return _drop_header_parameters(_strip_prose(subset))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    base_url = argv[1].rstrip("/")
    spec = httpx.get(f"{base_url}/openapi.json", timeout=30.0).raise_for_status().json()
    missing_paths = [path for path in PATHS if path not in spec["paths"]]
    missing_components = [name for name in COMPONENTS if name not in spec["components"]["schemas"]]
    if missing_paths or missing_components:
        print(f"platform is missing paths {missing_paths} / components {missing_components}", file=sys.stderr)
        return 1
    subset = redact(
        {
            "paths": {path: spec["paths"][path] for path in PATHS},
            "components": {"schemas": {name: spec["components"]["schemas"][name] for name in COMPONENTS}},
        }
    )
    TARGET.write_text(json.dumps(subset, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {TARGET.relative_to(Path.cwd()) if TARGET.is_relative_to(Path.cwd()) else TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
