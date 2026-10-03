# sigrix-mcp

[![PyPI](https://img.shields.io/pypi/v/sigrix-mcp)](https://pypi.org/project/sigrix-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/sigrix-mcp)](https://pypi.org/project/sigrix-mcp/)
[![CI](https://github.com/sigrix-io/sigrix-mcp/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/sigrix-io/sigrix-mcp/actions/workflows/ci.yml)
[![Licence](https://img.shields.io/github/license/sigrix-io/sigrix-mcp)](https://github.com/sigrix-io/sigrix-mcp/blob/main/LICENSE)

Publish prompt, persona and skill listings to [Sigrix](https://sigrix.io) from the AI client you already write in — Claude Code, Claude Desktop, Cursor, VS Code, or any MCP client.

A thin server over Sigrix's seller API. It carries no model calls, no validation of its own and no secret beyond your token. Every submission goes through Sigrix's moderation queue; nothing goes live from here.

## Install

Nothing to install or run by hand: your MCP client runs `uvx sigrix-mcp` itself, from the configuration below, whenever it starts the server. You need [uv](https://docs.astral.sh/uv/), which provides `uvx`, and Python 3.11 or newer.

Run by hand in a terminal, it prints one line to stderr saying it is an MCP server waiting for a client, then waits on stdin for a client's JSON-RPC, as every stdio MCP server does. Ctrl+C quits.

`pipx install sigrix-mcp` is only for keeping a pinned, installed copy. The `command` in your client's configuration is then `sigrix-mcp`, with no `args`, and the Claude Code line ends `-- sigrix-mcp`.

## Get a token

Sign in to Sigrix, open [**Account → Settings**](https://sigrix.io/account/settings#seller-api-token), and create a **Seller API token**. It is shown once. The token can create, edit and submit *your own* drafts for review, and nothing else on your account: it cannot approve or publish, and it opens no other page or API. Revoke or regenerate it from the same card at any time; the old token stops working on the next request.

Give it to the server as `SIGRIX_SELLER_TOKEN`.

## Configure your client

**Claude Code**

```sh
claude mcp add sigrix -e SIGRIX_SELLER_TOKEN=sgx_... -- uvx sigrix-mcp
```

**Claude Desktop** (`claude_desktop_config.json`) and **Cursor** (`~/.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "sigrix": {
      "command": "uvx",
      "args": ["sigrix-mcp"],
      "env": { "SIGRIX_SELLER_TOKEN": "sgx_..." }
    }
  }
}
```

That is Cursor's user-level file. Keep the block out of a workspace `.cursor/mcp.json`: the token is in it, and a workspace file is easily committed.

**VS Code** (`~/.copilot/mcp-config.json`)

```json
{
  "mcpServers": {
    "sigrix": {
      "type": "stdio",
      "command": "uvx",
      "args": ["sigrix-mcp"],
      "env": { "SIGRIX_SELLER_TOKEN": "sgx_..." },
      "tools": ["*"]
    }
  }
}
```

That user-level file is the portable location VS Code prefers for new servers, and GitHub Copilot CLI's own; with `COPILOT_HOME` set, it is `$COPILOT_HOME/mcp-config.json`. The block is the one above with two keys added for Copilot: its reference requires `tools` on a local server, and `"type": "stdio"` is the type it recommends for a configuration VS Code also reads. Keep the block out of a workspace `.mcp.json` or `.vscode/mcp.json`: the token is in it, and a workspace file is easily committed. An older VS Code that does not read the file has its own user `mcp.json` (**MCP: Open User Configuration**, now deprecated): put the entry there under `servers` rather than `mcpServers`, and leave out `tools`.

`SIGRIX_BASE_URL` is optional and defaults to `https://sigrix.io`.

## What it does

Tools:

| Tool | What it is |
| --- | --- |
| `list_categories` | The category slugs Sigrix accepts, with a sentence each. |
| `list_my_listings` | Your listings, any status, newest first. |
| `get_listing` | One listing, as the web editor loads it. |
| `create_draft` | A new private draft. |
| `update_draft` | Fill or change its fields. |
| `check_draft` | What submit would refuse, in the platform's own words. |
| `submit_for_review` | Into the moderation queue. |
| `import_skill_md` | A SKILL.md on disk becomes a draft skill. |
| `export_skill_md` | A draft skill back as SKILL.md. |

Prompts: `draft_prompt_listing`, `draft_persona_listing`, `draft_skill_listing` — the brief a good listing of each type is written to. Give one an idea and it drafts, checks and asks you before submitting.

The server pins the seller API version it was written against and refuses to run against a platform that serves another one; upgrade when it tells you to.

## What it does not do

It does not publish anything. A submitted listing is `pending_review` until a moderator approves it, and you can keep editing it in the web wizard at the `edit_url` every tool returns. It does not read your purchases or anyone else's listings, and it never sends your token anywhere but the `Authorization` header of requests to the base URL you configured.

## Where it fits

sigrix-mcp is one of the open-source projects [Sigrix](https://sigrix.io) publishes, and a seller's way in: a draft goes from your editor through the seller API into the review queue. Every project Sigrix publishes, and a map of how they connect: [sigrix.io/open-source](https://sigrix.io/open-source).

## Development

```sh
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy --strict src/sigrix_mcp
pytest
```

`scripts/sync_schemas.py <base-url>` refreshes the API schema the tool descriptions are derived from.

The package ships type information (`py.typed`), so your own checker uses these annotations rather than inferring around them.

[CONTRIBUTING.md](https://github.com/sigrix-io/sigrix-mcp/blob/main/CONTRIBUTING.md) has the scope and the review queues, [VERSIONING.md](https://github.com/sigrix-io/sigrix-mcp/blob/main/VERSIONING.md) says what a version bump means, and [SECURITY.md](https://github.com/sigrix-io/sigrix-mcp/blob/main/SECURITY.md) is where a vulnerability goes — not the tracker.

## Licence

Apache-2.0. The Sigrix name and logo are not covered by the licence — see `NOTICE`.
