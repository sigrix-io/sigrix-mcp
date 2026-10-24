"""The vendored schema keeps every field the platform declares, and none of its maintainers' prose.

`scripts/sync_schemas.py` strips each `description` and `summary` on the way in,
because a route's description is its handler's docstring. It stripped them by key
at any depth, and two of the seller API's *fields* carry those names: a listing's
`description` and an MCP server's `summary`. Both vanished from every model that
declares them, so `update_draft` never listed `description` among the keys it
accepts, though every listing type takes one.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VENDORED = ROOT / "src" / "sigrix_mcp" / "seller_api_openapi.json"


def _sync_module() -> Any:
    spec = importlib.util.spec_from_file_location("sync_schemas", ROOT / "scripts" / "sync_schemas.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _field(title: str, *, prose: str) -> dict[str, Any]:
    return {"anyOf": [{"type": "string"}, {"type": "null"}], "title": title, "description": prose}


def test_a_field_named_like_prose_keeps_its_name_and_loses_its_prose():
    document = {
        "paths": {
            "/api/items/register": {
                "post": {
                    "summary": "Api Register Item",
                    "description": "Create a draft item (#6034, `_private_helper`).",
                    "parameters": [
                        {"name": "item_type", "in": "query", "description": "One of prompt, persona."},
                        {"name": "x-moderator-override", "in": "header"},
                    ],
                }
            }
        },
        "components": {
            "schemas": {
                "ItemUpdate": {
                    "description": "Payload for the PATCH route (#4386).",
                    "properties": {
                        "description": _field("Description", prose="The listing's text."),
                        "summary": _field("Summary", prose="An MCP server's line."),
                        "name": _field("Name", prose="Its title."),
                    },
                }
            }
        },
    }

    redacted = _sync_module().redact(document)

    operation = redacted["paths"]["/api/items/register"]["post"]
    assert "summary" not in operation and "description" not in operation
    assert operation["parameters"] == [{"name": "item_type", "in": "query"}]
    model = redacted["components"]["schemas"]["ItemUpdate"]
    assert "description" not in model
    assert list(model["properties"]) == ["description", "summary", "name"]
    for field in model["properties"].values():
        assert "description" not in field
        assert field["anyOf"] == [{"type": "string"}, {"type": "null"}]


def test_a_field_called_properties_is_read_as_a_schema_not_as_a_map_of_names():
    redacted = _sync_module().redact(
        {"properties": {"properties": {"type": "object", "description": "prose", "summary": "prose"}}}
    )
    assert redacted == {"properties": {"properties": {"type": "object"}}}


def test_the_vendored_document_declares_both_fields_and_carries_no_prose():
    schemas = json.loads(VENDORED.read_text(encoding="utf-8"))["components"]["schemas"]

    assert "description" in schemas["ItemRegistration"]["properties"]
    assert "description" in schemas["ItemUpdate"]["properties"]
    assert "summary" in schemas["ItemUpdate"]["properties"]
    assert "description" in schemas["CategoryOut"]["properties"]

    def prose_left(node: object, *, names: bool = False) -> list[str]:
        if isinstance(node, dict):
            found = [] if names else [key for key in node if key in ("description", "summary")]
            for key, value in node.items():
                found += prose_left(value, names=key == "properties" and not names)
            return found
        if isinstance(node, list):
            return [key for item in node for key in prose_left(item)]
        return []

    assert prose_left(json.loads(VENDORED.read_text(encoding="utf-8"))) == []
