"""The README is what a seller copies their token from, and its labels say where it goes.

*Configure your client* labels each block with the file it belongs in, and the
token goes into that file with it. A workspace file sits in a project, where it
is easily committed, and each client's is a path from the project root that
starts with a dot: ``.cursor/mcp.json``, ``.vscode/mcp.json``, ``.mcp.json``.
So every file a label names is a user-level one. The README named Cursor's
workspace file until it named ``~/.cursor/mcp.json``. The token card on the
Sigrix account page labels the same blocks, with a real token filled in, and
prints the same blocks; nothing in either repository can read the other's.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

README = Path(__file__).resolve().parents[1] / "README.md"

#: A client's label: its name in bold, then its file in backticks, in brackets.
LABELLED_FILE = re.compile(r"\*\*[^*]+\*\* \(`([^`]+)`\)")


def _configure_your_client(readme: str) -> list[str]:
    section = re.search(r"^## Configure your client$(.*?)(?=^## )", readme, re.MULTILINE | re.DOTALL)
    assert section, "the README has no Configure your client section"
    return section.group(1).splitlines()


def _labelled_files(readme: str) -> list[str]:
    """Every file a client's label names in *Configure your client*, in order.

    A label is a line of its own that opens in bold; the prose under a block
    names workspace files on purpose, to say to keep the token out of them.
    """

    labels = [line for line in _configure_your_client(readme) if line.startswith("**")]
    return [match.group(1) for label in labels for match in LABELLED_FILE.finditer(label)]


def _blocks_by_file(readme: str) -> dict[str, Any]:
    """Each JSON block in *Configure your client*, parsed, under every file its label names.

    A block belongs to the last label above it. Parsing them is part of the
    point: a seller pastes one into a file their client will not start without.
    """

    blocks: dict[str, Any] = {}
    files: list[str] = []
    lines = iter(_configure_your_client(readme))
    for line in lines:
        if line.startswith("**"):
            files = [match.group(1) for match in LABELLED_FILE.finditer(line)]
        elif line == "```json":
            body = []
            for inner in lines:
                if inner == "```":
                    break
                body.append(inner)
            block = json.loads("\n".join(body))
            blocks.update(dict.fromkeys(files, block))
            files = []
    return blocks


def test_every_file_a_client_label_names_is_a_user_level_one() -> None:
    files = _labelled_files(README.read_text(encoding="utf-8"))

    assert "~/.cursor/mcp.json" in files
    assert [name for name in files if name.startswith(".")] == []


def test_a_label_naming_a_workspace_file_is_caught() -> None:
    """The canary: Cursor's label put back as it was has to fail the read above."""

    readme = README.read_text(encoding="utf-8").replace("(`~/.cursor/mcp.json`)", "(`.cursor/mcp.json`)")

    assert [name for name in _labelled_files(readme) if name.startswith(".")] == [".cursor/mcp.json"]


def test_copilots_file_gets_the_block_with_the_keys_copilot_documents() -> None:
    """``~/.copilot/mcp-config.json`` is GitHub Copilot CLI's file as much as
    VS Code's. Copilot's CLI reference requires ``tools`` on a local server and
    recommends ``"type": "stdio"`` for a configuration VS Code also reads.
    Copilot CLI 1.0.91 loads the block without ``tools`` and fills it in, but
    that is a default, not the contract, so the README no longer leans on it.
    Otherwise it is the Claude Desktop and Cursor block, as the README says, and
    the two must not drift apart.
    """

    blocks = _blocks_by_file(README.read_text(encoding="utf-8"))

    assert "~/.copilot/mcp-config.json" in blocks, "VS Code's label has no block of its own"
    copilot = blocks["~/.copilot/mcp-config.json"]["mcpServers"]["sigrix"]
    cursor = blocks["~/.cursor/mcp.json"]["mcpServers"]["sigrix"]
    assert copilot == {**cursor, "type": "stdio", "tools": ["*"]}
