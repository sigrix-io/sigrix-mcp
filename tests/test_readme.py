"""The README is what a seller copies their token from, and its labels say where it goes.

*Configure your client* labels each block with the file it belongs in, and the
token goes into that file with it. A workspace file sits in a project, where it
is easily committed, and each client's is a path from the project root that
starts with a dot: ``.cursor/mcp.json``, ``.vscode/mcp.json``, ``.mcp.json``.
So every file a label names is a user-level one. The README named Cursor's
workspace file until it named ``~/.cursor/mcp.json``. The token card on the
Sigrix account page labels the same block, with a real token filled in, and has
to say the same thing; nothing in either repository can read the other's.
"""

from __future__ import annotations

import re
from pathlib import Path

README = Path(__file__).resolve().parents[1] / "README.md"

#: A client's label: its name in bold, then its file in backticks, in brackets.
LABELLED_FILE = re.compile(r"\*\*[^*]+\*\* \(`([^`]+)`\)")


def _labelled_files(readme: str) -> list[str]:
    """Every file a client's label names in *Configure your client*, in order.

    A label is a line of its own that opens in bold; the prose under a block
    names workspace files on purpose, to say to keep the token out of them.
    """

    section = re.search(r"^## Configure your client$(.*?)(?=^## )", readme, re.MULTILINE | re.DOTALL)
    assert section, "the README has no Configure your client section"
    labels = [line for line in section.group(1).splitlines() if line.startswith("**")]
    return [match.group(1) for label in labels for match in LABELLED_FILE.finditer(label)]


def test_every_file_a_client_label_names_is_a_user_level_one() -> None:
    files = _labelled_files(README.read_text(encoding="utf-8"))

    assert "~/.cursor/mcp.json" in files
    assert [name for name in files if name.startswith(".")] == []


def test_a_label_naming_a_workspace_file_is_caught() -> None:
    """The canary: Cursor's label put back as it was has to fail the read above."""

    readme = README.read_text(encoding="utf-8").replace("(`~/.cursor/mcp.json`)", "(`.cursor/mcp.json`)")

    assert [name for name in _labelled_files(readme) if name.startswith(".")] == [".cursor/mcp.json"]
