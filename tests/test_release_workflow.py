"""The release workflow holds a credential, and this is the half of that nothing else guards.

`release.yml` has no secret in it: PyPI trusts this repository's workflow in the
`pypi` environment and the runner exchanges a short-lived OIDC identity for an
upload. That removes the token -- and moves the thing worth protecting to the
step that spends the identity, which is a third-party action.

That the step is pinned to a commit, and says which release it is, is asserted
in `tests/test_workflow_pins.py` along with every other `uses:` in this
repository. What is left here is the property those pins exist to protect, and
which is specific to this one file: that no credential is stored at all.
"""

from __future__ import annotations

from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release.yml"


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
