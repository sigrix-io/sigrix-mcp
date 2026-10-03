"""The tools are one request each, the version pin refuses, and errors are the platform's words.

The platform is faked with an ``httpx.MockTransport``: these tests pin what
the server *sends* and how it reads what comes back. Whether the platform
still answers those requests is a question only the platform can answer, and
it does: Sigrix carries an integration test that drives the route behind every
tool here with a real seller token, so a route or a body that moves fails
there, where it can be fixed, rather than going stale here.

What the model reads when a call fails is pinned through a real client session
(`_model_reads`), because calling a tool function directly skips the layer
that decides it.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from mcp import Client
from mcp.server.mcpserver.exceptions import ToolError

from sigrix_mcp import SUPPORTED_API_VERSION
from sigrix_mcp import server as srv
from sigrix_mcp.client import SigrixApiError, SigrixClient, SigrixConfigError

TOKEN = "sgx_test-token-value"  # noqa: S105 - a fixture, not a credential


class FakePlatform:
    """Answers the seller API's routes and records every request it saw."""

    def __init__(self, *, api_version: str = SUPPORTED_API_VERSION) -> None:
        self.api_version = api_version
        self.requests: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        if request.headers.get("Authorization") != f"Bearer {TOKEN}" and path != "/api/categories":
            return httpx.Response(401, json={"detail": "Authentication required."})
        if path == "/api/categories":
            return httpx.Response(
                200,
                json={
                    "api_version": self.api_version,
                    "categories": [{"slug": "writing-content", "name": "Writing & Content", "description": "Prose."}],
                },
            )
        if path == "/api/items/mine":
            return httpx.Response(200, json={"api_version": self.api_version, "items": []})
        if path == "/api/items/register":
            body = json.loads(request.content)
            return httpx.Response(
                200, json={"id": "p1", "item_type": body["item_type"], "redirect_url": "/items/prompt/p1/edit"}
            )
        if path.endswith("/check"):
            return httpx.Response(200, json={"eligible": False, "missing": ["Main prompt"], "requirements": []})
        if path.endswith("/submit"):
            return httpx.Response(
                422,
                json={
                    "detail": {
                        "code": "incomplete_listing",
                        "message": "Finish the required fields before submitting: Main prompt.",
                        "missing": ["Main prompt"],
                    }
                },
            )
        if path == "/api/items/skill/import":
            body = json.loads(request.content)
            assert body["markdown"].startswith("---")
            return httpx.Response(
                200,
                json={
                    "created": {
                        "listing_type": "skill",
                        "listing_id": "s1",
                        "slug": "s",
                        "name": "s",
                        "edit_url": "/items/skill/s1/edit",
                    },
                    "warnings": [],
                },
            )
        if path.endswith("/skill.md"):
            return httpx.Response(
                200, text="---\nname: s\ndescription: d\n---\n\nbody\n", headers={"content-type": "text/markdown"}
            )
        if request.method == "PATCH":
            return httpx.Response(200, json={"item": json.loads(request.content), "publish_eligibility": {}})
        if request.method == "GET":
            return httpx.Response(200, json={"item": {"id": path.rsplit("/", 1)[-1], "status": "draft"}})
        return httpx.Response(404, json={"detail": "Item not found."})


@pytest.fixture()
def platform() -> FakePlatform:
    fake = FakePlatform()
    srv.configure(
        SigrixClient(base_url="https://sigrix.test", token=TOKEN, transport=httpx.MockTransport(fake.handler))
    )
    yield fake
    srv.configure(None)


def _model_reads(calls: dict[str, dict[str, Any]]) -> dict[str, tuple[bool, str]]:
    """Each call's error flag and text, as a client session hands them to the model.

    Through the SDK, not around it: from mcp 2.1 the SDK withholds the text of
    anything a tool raises other than `ToolError`, and every refusal this server
    relays reached the model as a bare ``Error executing tool <name>`` while the
    tests that called the tool functions directly stayed green.
    """

    async def run() -> dict[str, tuple[bool, str]]:
        read: dict[str, tuple[bool, str]] = {}
        async with Client(srv.server) as client:
            for name, arguments in calls.items():
                # By alias, so this reads the wire's `isError` whatever the SDK names the attribute.
                result = (await client.call_tool(name, arguments)).model_dump(by_alias=True)
                text = " ".join(str(part.get("text", "")) for part in result["content"])
                read[name] = (bool(result.get("isError")), text)
        return read

    return asyncio.run(run())


def test_every_tool_and_prompt_is_registered():
    tools = asyncio.run(srv.server.list_tools())
    assert sorted(tool.name for tool in tools) == sorted(
        [
            "list_categories",
            "list_my_listings",
            "get_listing",
            "create_draft",
            "update_draft",
            "check_draft",
            "submit_for_review",
            "import_skill_md",
            "export_skill_md",
        ]
    )
    for tool in tools:
        if tool.name in {"create_draft", "update_draft", "submit_for_review", "import_skill_md"}:
            assert "moderation" in tool.description.lower(), tool.name
    prompts = asyncio.run(srv.server.list_prompts())
    assert sorted(prompt.name for prompt in prompts) == [
        "draft_persona_listing",
        "draft_prompt_listing",
        "draft_skill_listing",
    ]


def test_the_update_description_quotes_the_platforms_own_field_names():
    assert "main_prompt" in srv.ITEM_UPDATE_FIELDS
    assert "instructions" in srv.ITEM_UPDATE_FIELDS
    tools = {tool.name: tool for tool in asyncio.run(srv.server.list_tools())}
    for field in srv.ITEM_UPDATE_FIELDS:
        assert field in tools["update_draft"].description


def test_a_version_the_release_does_not_know_refuses_every_tool(tmp_path: Path):
    """Every tool, called as a client calls it, tells the model why and what to do about it."""

    skill = tmp_path / "SKILL.md"
    skill.write_text("---\nname: s\ndescription: d\n---\n\nbody\n", encoding="utf-8")
    calls: dict[str, dict[str, Any]] = {
        "list_categories": {},
        "list_my_listings": {},
        "get_listing": {"item_type": "prompt", "item_id": "p1"},
        "create_draft": {"item_type": "prompt", "name": "x"},
        "update_draft": {"item_type": "prompt", "item_id": "p1", "fields": {"name": "x"}},
        "check_draft": {"item_type": "prompt", "item_id": "p1"},
        "submit_for_review": {"item_type": "prompt", "item_id": "p1"},
        "import_skill_md": {"path": str(skill), "category": "writing-content"},
        "export_skill_md": {"item_id": "s1"},
    }
    # The table is the sweep's canary: a tool registered without a row here
    # fails this line rather than going unswept.
    assert sorted(calls) == sorted(tool.name for tool in asyncio.run(srv.server.list_tools()))

    fake = FakePlatform(api_version="2")
    srv.configure(
        SigrixClient(base_url="https://sigrix.test", token=TOKEN, transport=httpx.MockTransport(fake.handler))
    )
    try:
        read = _model_reads(calls)
    finally:
        srv.configure(None)
    for name, (is_error, text) in read.items():
        assert is_error, name
        assert "serves seller API version '2'" in text, (name, text)
        assert "Upgrade sigrix-mcp" in text, (name, text)


def test_create_check_and_a_refused_submit(platform: FakePlatform):
    created = srv.create_draft(
        "prompt", "Deploy helper", description="d" * 200, category="writing-content", tags=["ops"]
    )
    assert created["id"] == "p1"
    sent = json.loads(platform.requests[-1].content)
    assert sent == {
        "item_type": "prompt",
        "name": "Deploy helper",
        "description": "d" * 200,
        "category": "writing-content",
        "tags": ["ops"],
        "price_cents": 0,
    }

    verdict = srv.check_draft("prompt", "p1")
    assert verdict["missing"] == ["Main prompt"]
    assert platform.requests[-1].method == "POST" and platform.requests[-1].url.path == "/api/items/prompt/p1/check"

    with pytest.raises(ToolError) as refused:
        srv.submit_for_review("prompt", "p1")
    cause = refused.value.__cause__
    assert isinstance(cause, SigrixApiError)
    assert cause.status_code == 422
    assert cause.code == "incomplete_listing"
    assert "Main prompt" in cause.message


def test_update_sends_the_fields_verbatim_and_refuses_an_empty_object(platform: FakePlatform):
    fields = {"main_prompt": "Write a deploy checklist for {{service}}.", "scenarios": [{"user_input": "x"}]}
    saved = srv.update_draft("prompt", "p1", fields)
    assert saved["item"] == fields
    assert platform.requests[-1].method == "PATCH"
    with pytest.raises(ToolError, match="fields must be a non-empty object"):
        srv.update_draft("prompt", "p1", {})


def test_list_and_get(platform: FakePlatform):
    assert srv.list_categories()["categories"][0]["slug"] == "writing-content"
    assert srv.list_my_listings("skill")["items"] == []
    assert platform.requests[-1].url.params["item_type"] == "skill"
    assert srv.get_listing("persona", "abc")["item"]["id"] == "abc"
    with pytest.raises(ToolError, match="item_type must be one of prompt, persona, skill"):
        srv.get_listing("crew", "abc")


def test_import_and_export_round_trip_through_disk(platform: FakePlatform, tmp_path: Path):
    source = tmp_path / "SKILL.md"
    source.write_text("---\nname: s\ndescription: d\n---\n\nbody\n", encoding="utf-8")
    created = srv.import_skill_md(str(source), "writing-content")
    assert created["created"]["listing_id"] == "s1"

    target = tmp_path / "out" / "SKILL.md"
    target.parent.mkdir()
    exported = srv.export_skill_md("s1", str(target))
    assert exported["path"] == str(target)
    assert target.read_text(encoding="utf-8") == source.read_text(encoding="utf-8")


def test_the_token_never_leaves_the_authorization_header(platform: FakePlatform):
    srv.list_my_listings()
    request = platform.requests[-1]
    assert request.headers["Authorization"] == f"Bearer {TOKEN}"
    assert TOKEN not in str(request.url)


def test_an_unset_token_is_a_configuration_error(monkeypatch):
    monkeypatch.delenv("SIGRIX_SELLER_TOKEN", raising=False)
    with pytest.raises(SigrixConfigError):
        SigrixClient.from_env()


# ---------------------------------------------------------------------------
# The types a caller has to send (0.2.0)
# ---------------------------------------------------------------------------


def test_update_draft_states_the_type_of_every_field_it_accepts():
    """The whole reason the platform's schema is vendored rather than hand-written.

    It was half-applied: the field *names* were derived and their types thrown
    away, so the description listed `compatibility` and `allowed_tools` in one
    sentence with nothing saying that the first is a string and the second a
    list. A model drafting a skill listing against production guessed, guessed
    wrong, and the platform refused the payload.
    """

    labels = dict(zip(srv.ITEM_UPDATE_FIELDS, srv.ITEM_UPDATE_TYPED_FIELDS, strict=True))

    assert labels["compatibility"] == "compatibility (string)"
    assert labels["allowed_tools"] == "allowed_tools (string[])"
    assert labels["scenarios"] == "scenarios (object[])"
    assert labels["price_cents"] == "price_cents (integer)"

    # Every field, or the derivation is silently degrading for some of them and
    # the next caller learns the shape from a rejection instead.
    untyped = [label for label in srv.ITEM_UPDATE_TYPED_FIELDS if "(" not in label]
    assert untyped == [], untyped


def test_the_types_reach_the_description_the_model_reads():
    """Deriving them and not printing them would be the same bug again."""

    tools = {tool.name: tool for tool in asyncio.run(srv.server.list_tools())}
    description = tools["update_draft"].description
    assert "compatibility (string)" in description
    assert "allowed_tools (string[])" in description


def test_a_label_is_omitted_rather_than_guessed_for_a_real_union():
    """FastAPI writes every optional field as `anyOf: [T, null]`, so dropping
    the null branch is safe. A union of two *real* types is not something this
    label can state honestly, and a wrong type is worse than no type."""

    assert srv._type_label({"anyOf": [{"type": "string"}, {"type": "null"}]}) == "string"
    assert srv._type_label({"anyOf": [{"type": "string"}, {"type": "integer"}]}) == ""
    assert srv._type_label({"type": "array"}) == "array"
    assert srv._type_label({"type": "array", "items": {"type": "string"}}) == "string[]"
    assert srv._type_label(None) == ""
    assert srv._type_label({}) == ""


# ---------------------------------------------------------------------------
# What the model reads when a call fails
# ---------------------------------------------------------------------------


def test_a_refusal_reaches_the_model_in_its_own_words(platform: FakePlatform, tmp_path: Path):
    """The platform's sentence, this side's argument check and the file's own error, each in full.

    A seller's `import_skill_md` failed twice as ``Error executing tool
    import_skill_md`` and nothing else. The parser's reason was on the server's
    stderr, where the model retrying the call could not see it.
    """

    missing = tmp_path / "nowhere" / "SKILL.md"
    read = _model_reads(
        {
            "submit_for_review": {"item_type": "prompt", "item_id": "p1"},
            "get_listing": {"item_type": "crew", "item_id": "p1"},
            "import_skill_md": {"path": str(missing), "category": "writing-content"},
        }
    )

    is_error, text = read["submit_for_review"]
    assert is_error
    assert "Sigrix answered 422" in text
    assert "Finish the required fields before submitting: Main prompt." in text

    is_error, text = read["get_listing"]
    assert is_error
    assert "item_type must be one of prompt, persona, skill; got 'crew'." in text

    # The same read the tool makes, so the expected text is the OS's own wording.
    with pytest.raises(OSError) as unreadable:
        missing.read_text(encoding="utf-8")
    is_error, text = read["import_skill_md"]
    assert is_error
    assert str(unreadable.value) in text


def test_an_unanticipated_failure_keeps_its_own_type():
    """Only the failures the model can act on are reported. Anything else stays a
    crash, whose text the SDK keeps on the server: a bug's internals are not the
    model's to read, and widening the net to `Exception` would hand them over."""

    def broken(request: httpx.Request) -> httpx.Response:
        raise KeyError("an internal detail")

    srv.configure(SigrixClient(base_url="https://sigrix.test", token=TOKEN, transport=httpx.MockTransport(broken)))
    try:
        with pytest.raises(KeyError):
            srv.list_my_listings()
    finally:
        srv.configure(None)
