"""Started by hand, the server says what it is waiting for: on stderr, and only to a person.

A stdio MCP server waits silently for its client's first JSON-RPC message.
That is correct, and to a seller who pasted ``uvx sigrix-mcp`` into a terminal
expecting an install step it is indistinguishable from a hang. ``main()``
tells that person what is going on. A terminal on stdin is how it knows a
person is there: an MCP client launches the server with a pipe, and must see
nothing new, least of all on stdout, which is the protocol channel.
"""

from __future__ import annotations

import io
import json
import os
import re
import select
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from sigrix_mcp import __main__ as entry
from sigrix_mcp import server as srv
from sigrix_mcp.client import TOKEN_ENV

TOKEN = "sgx_test-token-value"  # noqa: S105 - a fixture, not a credential
README = Path(__file__).resolve().parents[1] / "README.md"


class _Terminal(io.StringIO):
    def isatty(self) -> bool:
        return True


class _Served(Exception):
    """Raised in place of ``server.run``, which serves until the client hangs up."""


@pytest.fixture()
def serving(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[str]]:
    """Stub out serving, and record that ``main()`` got as far as it."""

    transports: list[str] = []

    def run(transport: str) -> None:
        transports.append(transport)
        raise _Served

    monkeypatch.setattr(srv.server, "run", run)
    yield transports
    srv.configure(None)


@pytest.mark.parametrize(
    ("stdin", "expected_stderr"),
    [(_Terminal(), entry.STARTUP_HINT + "\n"), (io.StringIO(), "")],
    ids=["terminal", "pipe"],
)
def test_the_hint_goes_to_a_terminal_on_stderr_and_a_client_sees_nothing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    serving: list[str],
    stdin: io.StringIO,
    expected_stderr: str,
) -> None:
    monkeypatch.setenv(TOKEN_ENV, TOKEN)
    monkeypatch.setattr("sys.stdin", stdin)

    # `run` raises, so this also proves the hint comes *before* serving: printed
    # after it, the line would never be reached and the terminal case fails.
    with pytest.raises(_Served):
        entry.main()

    out, err = capsys.readouterr()
    assert out == ""
    assert err == expected_stderr
    assert serving == ["stdio"]


def test_a_missing_token_is_the_only_thing_said(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], serving: list[str]
) -> None:
    """The hint says the server is waiting; without a token it exits instead."""

    monkeypatch.delenv(TOKEN_ENV, raising=False)
    monkeypatch.setattr("sys.stdin", _Terminal())

    with pytest.raises(SystemExit) as exited:
        entry.main()

    assert exited.value.code == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert err.count("\n") == 1 and TOKEN_ENV in err, err
    assert entry.STARTUP_HINT not in err
    assert serving == []


def _anchor(heading: str) -> str:
    """GitHub's id for a Markdown heading: lowercased, punctuation dropped, spaces to hyphens."""
    return re.sub(r"[^\w\- ]", "", heading.lstrip("#").strip().lower()).replace(" ", "-")


def test_the_hint_links_a_readme_section_that_exists() -> None:
    """Renaming the heading would leave the hint pointing at the top of the README."""

    page, _, anchor = entry.STARTUP_HINT.rpartition("#")
    assert page.endswith("https://github.com/sigrix-io/sigrix-mcp")
    headings = [line for line in README.read_text(encoding="utf-8").splitlines() if line.startswith("#")]
    assert anchor in {_anchor(heading) for heading in headings}, anchor


# ---------------------------------------------------------------------------
# The real process, with a real terminal
# ---------------------------------------------------------------------------

INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}},
}
DEADLINE = 30.0


def _read_line(fd: int) -> bytes:
    """Bytes from ``fd`` up to the first newline, or whatever arrived before the deadline."""
    data = b""
    give_up = time.monotonic() + DEADLINE
    while b"\n" not in data and (left := give_up - time.monotonic()) > 0:
        if not select.select([fd], [], [], left)[0]:
            break
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        data += chunk
    return data


def _read_waiting(fd: int) -> bytes:
    """Whatever is already in the pipe, without waiting for more."""
    data = b""
    while select.select([fd], [], [], 0)[0]:
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        data += chunk
    return data


@pytest.mark.skipif(sys.platform == "win32", reason="needs a POSIX pseudo-terminal")
@pytest.mark.parametrize("terminal", [True, False], ids=["terminal", "pipe"])
def test_the_running_server_hints_only_to_a_terminal_and_answers_either_way(terminal: bool) -> None:
    """What a person and a client actually see from ``python -m sigrix_mcp``.

    On a pseudo-terminal the hint arrives while the server waits, so it was
    flushed rather than left in a buffer, and an ``initialize`` typed through
    that terminal is still answered. On a pipe, stderr stays empty and the
    first bytes on stdout are the JSON-RPC reply.
    """

    import pty

    env = {**os.environ, TOKEN_ENV: TOKEN, "SIGRIX_BASE_URL": "https://sigrix.test"}
    command = [sys.executable, "-m", "sigrix_mcp"]
    if terminal:
        controller, stdin = pty.openpty()
    else:
        stdin, controller = os.pipe()
    proc = subprocess.Popen(command, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)  # noqa: S603 - this interpreter, this package
    os.close(stdin)
    assert proc.stdout is not None and proc.stderr is not None
    stdout, stderr = proc.stdout.fileno(), proc.stderr.fileno()
    try:
        if terminal:
            assert _read_line(stderr) == entry.STARTUP_HINT.encode() + b"\n"
            assert _read_waiting(stdout) == b""

        os.write(controller, json.dumps(INITIALIZE).encode() + b"\n")
        reply = json.loads(_read_line(stdout))
        assert reply["id"] == 1
        assert reply["result"]["serverInfo"]["name"] == "sigrix"

        assert _read_waiting(stderr) == b""
    finally:
        proc.kill()
        proc.wait()
        proc.stdout.close()
        proc.stderr.close()
        os.close(controller)
