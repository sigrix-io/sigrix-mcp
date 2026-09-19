# sigrix-mcp

Publish prompt, persona and skill listings to [Sigrix](https://sigrix.io) from the AI client you already write in — Claude Code, Claude Desktop, Cursor, or any MCP client.

A thin server over Sigrix's seller API. It carries no model calls, no validation of its own and no secret beyond your token. Every submission goes through Sigrix's moderation queue; nothing goes live from here.

## Install

```sh
uvx sigrix-mcp        # or: pipx install sigrix-mcp
```

Python 3.11 or newer.

## Get a token

Sign in to Sigrix, open **Account → Settings**, and create a **Seller API token**. It is shown once. The token can create, edit and submit *your own* drafts for review, and nothing else on your account: it cannot approve or publish, and it opens no other page or API. Revoke or regenerate it from the same card at any time; the old token stops working on the next request.

Give it to the server as `SIGRIX_SELLER_TOKEN`.

## Configure your client

**Claude Code**

```sh
claude mcp add sigrix -e SIGRIX_SELLER_TOKEN=sgx_... -- uvx sigrix-mcp
```

**Claude Desktop** (`claude_desktop_config.json`) and **Cursor** (`.cursor/mcp.json`)

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

## Development

```sh
pip install -e ".[dev]"
ruff check . && pytest
```

`scripts/sync_schemas.py <base-url>` refreshes the API schema the tool descriptions are derived from.

## Licence

Apache-2.0. The Sigrix name and logo are not covered by the licence — see `NOTICE`.
