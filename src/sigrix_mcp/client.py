"""The HTTP client under every tool: base URL, bearer token, version pin, error shape.

Configuration is two environment variables:

- ``SIGRIX_SELLER_TOKEN`` — the seller API token minted on
  ``/account/settings``. Required. Never logged, never echoed.
- ``SIGRIX_BASE_URL`` — the platform to talk to. Optional; defaults to the
  production site. Set it to a staging host to try things out.

Errors are the platform's own words. A refused submit answers 422 with the
gate's ``missing`` labels; the client raises :class:`SigrixApiError` carrying
that message verbatim, so the model reading the tool result sees exactly the
sentence the publish wizard's rail would have shown — never a paraphrase
that could drift from the rule.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

from . import SUPPORTED_API_VERSION, __version__

DEFAULT_BASE_URL = "https://sigrix.io"
TOKEN_ENV = "SIGRIX_SELLER_TOKEN"  # noqa: S105 — the variable's name, not a value
BASE_URL_ENV = "SIGRIX_BASE_URL"


class SigrixError(RuntimeError):
    """Base for everything this client raises."""


class SigrixConfigError(SigrixError):
    """The environment is missing something the client needs."""


class SigrixApiVersionError(SigrixError):
    """The platform serves an API version this release does not understand."""


@dataclass
class SigrixApiError(SigrixError):
    """A non-2xx answer, carrying the platform's own message."""

    status_code: int
    message: str
    code: str = ""
    detail: Any = None

    def __str__(self) -> str:  # pragma: no cover - formatting
        prefix = f"{self.code}: " if self.code else ""
        return f"Sigrix answered {self.status_code} — {prefix}{self.message}"


def _message_from_detail(detail: Any, status_code: int) -> tuple[str, str]:
    """``(message, code)`` out of a FastAPI ``detail``, which is a string or a dict."""
    if isinstance(detail, str):
        return detail, ""
    if isinstance(detail, dict):
        message = str(detail.get("message") or detail.get("detail") or "")
        code = str(detail.get("code") or "")
        missing = detail.get("missing")
        if isinstance(missing, list) and missing and not message:
            message = "Missing: " + ", ".join(str(label) for label in missing)
        next_step = detail.get("request_role_change_url")
        if next_step:
            message = f"{message} Request the seller role at {next_step}."
        return message or f"HTTP {status_code}", code
    if isinstance(detail, list) and detail:
        # A 422 from request validation: one line per field.
        parts = []
        for entry in detail:
            if isinstance(entry, dict):
                location = ".".join(str(piece) for piece in entry.get("loc", []) if piece != "body")
                parts.append(f"{location}: {entry.get('msg', '')}".strip(": "))
        return "; ".join(parts) or f"HTTP {status_code}", "validation_error"
    return f"HTTP {status_code}", ""


class SigrixClient:
    """One authenticated session against the seller API."""

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not token:
            raise SigrixConfigError(f"{TOKEN_ENV} is empty; mint a seller API token on /account/settings.")
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": f"sigrix-mcp/{__version__}",
            },
            timeout=timeout,
            transport=transport,
        )
        self._api_version: str | None = None

    @classmethod
    def from_env(cls, *, transport: httpx.BaseTransport | None = None) -> SigrixClient:
        token = (os.getenv(TOKEN_ENV) or "").strip()
        if not token:
            raise SigrixConfigError(
                f"{TOKEN_ENV} is not set. Mint a seller API token on your Sigrix account settings page "
                f"and put it in the MCP client's environment for this server."
            )
        base_url = (os.getenv(BASE_URL_ENV) or DEFAULT_BASE_URL).strip()
        return cls(base_url=base_url, token=token, transport=transport)

    @property
    def base_url(self) -> str:
        return str(self._http.base_url)

    # -- the version pin -------------------------------------------------------

    def api_version(self) -> str:
        """The platform's ``api_version``, read once and cached for the session."""
        if self._api_version is None:
            body = self._json("GET", "/api/categories", check_version=False)
            self._api_version = str(body.get("api_version") or "")
        return self._api_version

    def ensure_supported(self) -> None:
        served = self.api_version()
        if served != SUPPORTED_API_VERSION:
            raise SigrixApiVersionError(
                f"{self.base_url} serves seller API version {served!r}; this sigrix-mcp release ({__version__}) "
                f"understands {SUPPORTED_API_VERSION!r}. Upgrade sigrix-mcp (or pin the matching release)."
            )

    # -- requests --------------------------------------------------------------

    def _raise_for(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = response.text
        message, code = _message_from_detail(detail, response.status_code)
        raise SigrixApiError(status_code=response.status_code, message=message, code=code, detail=detail)

    def _json(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        check_version: bool = True,
    ) -> dict[str, Any]:
        if check_version:
            self.ensure_supported()
        response = self._http.request(method, path, json=json, params=params)
        self._raise_for(response)
        body = response.json()
        return body if isinstance(body, dict) else {"result": body}

    def get_json(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._json("GET", path, params=params)

    def post_json(self, path: str, *, json: Any = None) -> dict[str, Any]:
        return self._json("POST", path, json=json)

    def patch_json(self, path: str, *, json: Any = None) -> dict[str, Any]:
        return self._json("PATCH", path, json=json)

    def get_text(self, path: str) -> str:
        self.ensure_supported()
        response = self._http.request("GET", path, headers={"Accept": "text/markdown, */*"})
        self._raise_for(response)
        return response.text

    def close(self) -> None:
        self._http.close()


__all__ = [
    "BASE_URL_ENV",
    "DEFAULT_BASE_URL",
    "SigrixApiError",
    "SigrixApiVersionError",
    "SigrixClient",
    "SigrixConfigError",
    "SigrixError",
    "TOKEN_ENV",
]
