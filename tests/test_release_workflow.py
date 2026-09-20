"""The release workflow holds a credential, and both halves of that are guarded here.

`release.yml` has no secret in it: PyPI trusts this repository's workflow in the
`pypi` environment and the runner exchanges a short-lived OIDC identity for an
upload. That removes the token — and moves the thing worth protecting to the
step that spends the identity, which is a third-party action.

`pypa/gh-action-pypi-publish@release/v1` is a **branch**. It moves whenever
upstream pushes, so the code holding upload rights to PyPI could change under a
tagged release with nothing in this repository recording it, and the diff of the
run that shipped would look identical to the one before. Pinning the commit is
what closes that; this is what notices if the pin goes back.

Read as text rather than parsed: the assertions are about *how the reference is
written*, which a YAML loader normalises away, and this repository ships no YAML
parser to its tests.
"""

from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release.yml"

#: `uses: pypa/gh-action-pypi-publish@<ref>`, with whatever trailing comment.
_PUBLISH_STEP = re.compile(r"uses:\s*pypa/gh-action-pypi-publish@(\S+)(?:\s*#\s*(\S+))?")

_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def _publish_references() -> list[tuple[str, str]]:
    return [(ref, comment or "") for ref, comment in _PUBLISH_STEP.findall(WORKFLOW.read_text(encoding="utf-8"))]


def test_the_pattern_matches_the_way_this_workflow_writes_it() -> None:
    """Guards the guard: a regex matching nothing would pass every assertion below."""

    assert _PUBLISH_STEP.findall("      - uses: pypa/gh-action-pypi-publish@release/v1\n") == [("release/v1", "")]
    assert _PUBLISH_STEP.findall("- uses: pypa/gh-action-pypi-publish@abc # v1.2.3\n") == [("abc", "v1.2.3")]
    assert _publish_references(), f"no publish step found in {WORKFLOW.name}; the assertions below are vacuous"


def test_the_publish_action_is_pinned_to_a_commit() -> None:
    for ref, _ in _publish_references():
        assert _COMMIT_SHA.match(ref), (
            f"pypa/gh-action-pypi-publish is used at {ref!r}. A tag is mutable and a branch moves on "
            "its own; this step holds upload rights to PyPI, so pin the 40-character commit."
        )


def test_the_pin_says_which_release_it_is() -> None:
    """A bare SHA is safe and unreadable. The trailing comment is what a reviewer
    reads, and what Dependabot rewrites when it bumps the pin."""

    for ref, comment in _publish_references():
        assert re.fullmatch(r"v\d+\.\d+(\.\d+)?", comment), (
            f"pin {ref[:12]}… carries the comment {comment!r}; write the release it is, as `# v1.14.2`."
        )


def test_the_release_stores_no_pypi_credential() -> None:
    """The property the pin exists to protect.

    Trusted publishing is why there is no token here to leak, and a `secrets.`
    reference appearing in this file would mean that decision was quietly
    reversed — at which point the third-party step above is handling a
    long-lived credential rather than a short-lived identity.
    """

    source = WORKFLOW.read_text(encoding="utf-8")
    offenders = [
        line.strip() for line in source.splitlines() if "secrets." in line and not line.lstrip().startswith("#")
    ]

    assert offenders == [], (
        f"{WORKFLOW.name} reads a secret: {offenders}. Releases publish through OIDC; see VERSIONING.md."
    )
    assert "id-token: write" in source, (
        "the OIDC permission is gone, so the claim above is no longer what makes this work"
    )
