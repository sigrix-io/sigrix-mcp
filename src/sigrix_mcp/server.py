"""The MCP server: nine tools and three prompts over the Sigrix seller API.

Every tool is one request to one route. The routes, their bodies and the
version this release pins are the platform's (``seller_api_openapi.json``,
refreshed by ``scripts/sync_schemas.py``); the tool descriptions quote that
file for the field names rather than restating them by hand.

Every tool that changes anything says so in its description: a submission
goes to moderation, and nothing goes live from here.
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

from . import SUPPORTED_API_VERSION, __version__
from .client import SigrixClient
from .guidance import FLOW, GUIDANCE_BY_TYPE

#: The listing types this release covers (the platform's v1 seller API).
LISTING_TYPES = ("prompt", "persona", "skill")

MODERATION_NOTE = (
    "Nothing goes live from this tool: a submitted listing enters Sigrix's moderation queue as "
    "pending_review and a moderator decides."
)


def _load_schema() -> dict[str, Any]:
    text = resources.files(__package__).joinpath("seller_api_openapi.json").read_text(encoding="utf-8")
    # Bound to an annotated local rather than returned straight out. `json.loads`
    # is typed `Any`, and under `mypy --strict` returning that from a function
    # declared to return a dict does not merely go unchecked here -- the `Any`
    # escapes into every caller, so the annotations this package now ships
    # would be trusted while checking nothing.
    schema: dict[str, Any] = json.loads(text)
    return schema


SCHEMA = _load_schema()


def _properties(component: str) -> dict[str, Any]:
    # Same reason as `_load_schema`: each `.get` on a `dict[str, Any]` yields
    # `Any`, so the chain has to land somewhere named before it is returned.
    properties: dict[str, Any] = (
        SCHEMA.get("components", {}).get("schemas", {}).get(component, {}).get("properties", {})
    )
    return properties


def _schema_fields(component: str) -> list[str]:
    """The property names of one request model, read off the platform's own schema."""
    return list(_properties(component))


def _type_label(prop: Any) -> str:
    """``string``, ``string[]``, ``object[]``… or ``""`` when the shape says nothing useful.

    The platform is FastAPI, so an optional field arrives as
    ``{"anyOf": [{"type": "string"}, {"type": "null"}]}``. Every field on these
    models is optional, so the ``null`` branch carries no information and is
    dropped; what is left is the type a caller actually has to send.
    """

    if not isinstance(prop, dict):
        return ""
    branches = prop.get("anyOf")
    if isinstance(branches, list):
        real = [b for b in branches if isinstance(b, dict) and b.get("type") != "null"]
        # More than one real branch is a union this label cannot state honestly,
        # and a wrong label is worse than none.
        return _type_label(real[0]) if len(real) == 1 else ""
    kind = prop.get("type")
    if kind == "array":
        inner = _type_label(prop.get("items"))
        return f"{inner}[]" if inner else "array"
    return kind if isinstance(kind, str) else ""


def _typed_fields(component: str) -> list[str]:
    """``name (type)`` per property, so a caller is not left inferring shape from spelling.

    This is the whole reason the schema is vendored rather than hand-written, and
    it was half-applied: the names were derived and the types were thrown away,
    leaving a description that listed ``compatibility`` and ``allowed_tools``
    side by side in one sentence with nothing saying that the first is a string
    and the second a list. A model drafting a skill listing guessed, guessed
    wrong, and the platform refused the payload — which is a poor way to learn a
    type the client was already shipping.
    """

    out: list[str] = []
    for name, prop in _properties(component).items():
        label = _type_label(prop)
        out.append(f"{name} ({label})" if label else name)
    return out


ITEM_REGISTRATION_FIELDS = _schema_fields("ItemRegistration")
ITEM_UPDATE_FIELDS = _schema_fields("ItemUpdate")
ITEM_UPDATE_TYPED_FIELDS = _typed_fields("ItemUpdate")

INSTRUCTIONS = f"""\
Sigrix is a marketplace for prompts, personas and skills. This server publishes listings to it on
behalf of the seller whose token it holds (sigrix-mcp {__version__}, seller API {SUPPORTED_API_VERSION}).

{FLOW}
Use the `draft_prompt_listing`, `draft_persona_listing` and `draft_skill_listing` prompts for what a
good listing of each type looks like; `check_draft` is the authority on what is still missing.
"""

server = MCPServer(name="sigrix", version=__version__, instructions=INSTRUCTIONS)

_client: SigrixClient | None = None


def configure(client: SigrixClient | None) -> None:
    """Install the client the tools use (tests pass one over a mock transport)."""
    global _client
    _client = client


def _sigrix() -> SigrixClient:
    global _client
    if _client is None:
        _client = SigrixClient.from_env()
    return _client


def _check_type(item_type: str) -> str:
    normalized = str(item_type or "").strip().lower()
    if normalized not in LISTING_TYPES:
        raise ValueError(f"item_type must be one of {', '.join(LISTING_TYPES)}; got {item_type!r}.")
    return normalized


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@server.tool(
    description=(
        "List the categories Sigrix accepts for a listing, each with a slug, a name and a one-sentence "
        "description of what belongs in it. Pass a slug from here as `category`; the publish gate refuses "
        "any other. Public; no token needed."
    )
)
def list_categories() -> dict[str, Any]:
    return _sigrix().get_json("/api/categories")


@server.tool(
    description=(
        "List the seller's own listings — prompts, personas and skills, any status — newest first. "
        "Each row carries id, item_type, name, status, category, tags, timestamps and the web editor URL. "
        "Optionally narrow to one item_type."
    )
)
def list_my_listings(item_type: str | None = None) -> dict[str, Any]:
    params = {"item_type": _check_type(item_type)} if item_type else None
    return _sigrix().get_json("/api/items/mine", params=params)


@server.tool(
    description=(
        "Read one of the seller's listings in full, as the web editor loads it: every content field and "
        "the current status. item_type is prompt, persona or skill."
    )
)
def get_listing(item_type: str, item_id: str) -> dict[str, Any]:
    return _sigrix().get_json(f"/api/items/{_check_type(item_type)}/{item_id}")


@server.tool(
    description=(
        "Create a new draft listing owned by the seller and return its id and web editor URL. "
        "item_type is prompt, persona or skill; name is the title (at most 80 characters); description "
        "should be at least 200 characters; category is a slug from list_categories. Fill the content "
        "fields afterwards with update_draft. The draft is private until submitted. " + MODERATION_NOTE
    )
)
def create_draft(
    item_type: str,
    name: str,
    description: str = "",
    category: str = "",
    tags: list[str] | None = None,
    price_cents: int = 0,
) -> dict[str, Any]:
    body = {
        "item_type": _check_type(item_type),
        "name": name,
        "description": description,
        "category": category,
        "tags": list(tags or []),
        "price_cents": int(price_cents),
    }
    return _sigrix().post_json("/api/items/register", json=body)


@server.tool(
    description=(
        "Update fields on a draft (or a listing returned for corrections). `fields` is an object of the "
        "seller API's ItemUpdate fields — for a prompt: main_prompt, context, rules, when_responding, "
        "output_format and scenarios (a list of {user_input, assistant_response}); for a persona: "
        "main_prompt plus tone, tagline, greeting, behavioral_notes; for a skill: instructions, license, "
        "compatibility, allowed_tools, skill_metadata; for any: name, description, category, tags, "
        "price_cents, seo_title. Accepted keys, with the type each one takes: "
        + ", ".join(ITEM_UPDATE_TYPED_FIELDS)
        + ". "
        "The answer carries the saved record and its publish_eligibility. A listing that is "
        "pending_review cannot be edited until a moderator returns it. " + MODERATION_NOTE
    )
)
def update_draft(item_type: str, item_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fields, dict) or not fields:
        raise ValueError("fields must be a non-empty object of ItemUpdate fields.")
    return _sigrix().patch_json(f"/api/items/{_check_type(item_type)}/{item_id}", json=fields)


@server.tool(
    description=(
        "Dry-run submit: ask Sigrix what would refuse this draft, without submitting and without "
        "changing anything. Returns the publish gate's own answer — `eligible`, the `missing` labels "
        "exactly as the web wizard shows them, every `requirements` row — plus `injection` (the fields "
        "the submit scan would refuse on) and `duplicate_title` (whether the title is already taken). "
        "Call it before submit_for_review and after every fix; it is the authority, not this description."
    )
)
def check_draft(item_type: str, item_id: str) -> dict[str, Any]:
    return _sigrix().post_json(f"/api/items/{_check_type(item_type)}/{item_id}/check")


@server.tool(
    description=(
        "Submit a draft for moderation. The listing moves to pending_review and a moderator reviews it; "
        "the seller is notified of the decision. Refused with the gate's own message when something is "
        "still missing — run check_draft first. " + MODERATION_NOTE
    )
)
def submit_for_review(item_type: str, item_id: str) -> dict[str, Any]:
    return _sigrix().post_json(f"/api/items/{_check_type(item_type)}/{item_id}/submit")


@server.tool(
    description=(
        "Create a draft skill listing from a SKILL.md file on disk. `path` is the file to read; `category` "
        "is a slug from list_categories; `tags` optionally overrides the file's. The frontmatter must "
        "carry a valid `name` and `description`; malformed frontmatter is refused with the parser's "
        "message. Returns the created draft (id, edit_url) and any warnings, such as a title that already "
        "exists. " + MODERATION_NOTE
    )
)
def import_skill_md(path: str, category: str, tags: list[str] | None = None) -> dict[str, Any]:
    file_path = Path(path).expanduser()
    markdown = file_path.read_text(encoding="utf-8")
    body = {"markdown": markdown, "category": category, "tags": list(tags or [])}
    return _sigrix().post_json("/api/items/skill/import", json=body)


@server.tool(
    description=(
        "Read one of the seller's skill listings back as the SKILL.md it compiles to — the same file a "
        "buyer downloads. Returns the markdown; when `path` is given, also writes it there."
    )
)
def export_skill_md(item_id: str, path: str | None = None) -> dict[str, Any]:
    markdown = _sigrix().get_text(f"/api/items/skill/{item_id}/skill.md")
    written: str | None = None
    if path:
        target = Path(path).expanduser()
        target.write_text(markdown, encoding="utf-8", newline="\n")
        written = str(target)
    return {"item_id": item_id, "path": written, "markdown": markdown}


# ---------------------------------------------------------------------------
# Prompts: the brief the host model drafts to, one per type
# ---------------------------------------------------------------------------


def _brief(item_type: str, idea: str) -> str:
    guidance = GUIDANCE_BY_TYPE[item_type]
    idea_line = f"\n\nThe seller's idea: {idea.strip()}\n" if idea.strip() else "\n"
    return (
        f"Draft a Sigrix {item_type} listing and publish it through the sigrix tools.\n\n"
        f"{guidance}\n{FLOW}{idea_line}"
        "Work in this order: list_categories, create_draft, update_draft, check_draft until eligible, "
        "then ask the seller before submit_for_review."
    )


@server.prompt(description="Draft a prompt listing from an idea and take it to review through the sigrix tools.")
def draft_prompt_listing(idea: str = "") -> str:
    return _brief("prompt", idea)


@server.prompt(description="Draft a persona listing from an idea and take it to review through the sigrix tools.")
def draft_persona_listing(idea: str = "") -> str:
    return _brief("persona", idea)


@server.prompt(
    description="Draft a skill listing (SKILL.md) from an idea and take it to review through the sigrix tools."
)
def draft_skill_listing(idea: str = "") -> str:
    return _brief("skill", idea)


__all__ = [
    "ITEM_REGISTRATION_FIELDS",
    "ITEM_UPDATE_FIELDS",
    "ITEM_UPDATE_TYPED_FIELDS",
    "LISTING_TYPES",
    "check_draft",
    "configure",
    "create_draft",
    "export_skill_md",
    "get_listing",
    "import_skill_md",
    "list_categories",
    "list_my_listings",
    "server",
    "submit_for_review",
    "update_draft",
]
