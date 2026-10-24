"""What a good listing of each type looks like — the brief the host model drafts to.

These are MCP *prompts*, one per type. They carry the knowledge the
platform's admin generator used to carry server-side; the model on the
seller's side does the drafting, and the platform's own gates
(``check_draft``) say what is still missing. Nothing here is a rule the
server enforces: when the text below and ``check_draft`` disagree,
``check_draft`` is right, and this file is what needs updating.
"""

from __future__ import annotations

FLOW = """\
How publishing works from here:

1. `list_categories` — pick a category slug from the platform's own list; the gate refuses any other.
2. `create_draft` — register the listing with its name, description and category. It is a draft, visible only to you.
3. `update_draft` — fill in the content fields for the type (below). Save in one or a few calls.
4. `check_draft` — ask the platform what would still refuse a submission. It answers with the exact
   labels the publish wizard shows, an injection-scan verdict by field, and whether the title is
   already taken. Fix and check again until `eligible` is true.
5. `submit_for_review` — the listing enters the moderation queue as `pending_review`.

Nothing goes live from any tool. A moderator reviews every submission, and the seller can keep
editing in the web wizard at the `edit_url` each tool returns.
"""

PROMPT_GUIDANCE = """\
A **prompt** listing is a reusable text a buyer pastes into a chatbot.

What the gate requires before submit:
- `name`: a clear title (at most 80 characters).
- `description`: at least 200 characters — what it does, for whom, what the result looks like.
  Fewer than 200 is refused, because the page needs indexable text.
- `category`: a slug from `list_categories`.
- `main_prompt`: the complete prompt text — the product itself. Write it to be pasted as-is,
  with `{{placeholders}}` for the parts the buyer fills in.
- `scenarios`: at least one example exchange, as `[{"user_input": "...", "assistant_response": "..."}]`.
  Buyers judge a prompt by its example.

Optional but worth filling: `context`, `rules`, `when_responding`, `output_format` (the prompt's
sections, shown separately), `tags` (a handful of short lowercase tags), `price_cents`
(0 for free; a paid listing needs payouts set up on the account).

Do not put credentials, API keys or instructions addressed to the platform's own reviewers in any
field; the submit scan refuses prompt-injection phrasing and flags embedded secrets.
"""

PERSONA_GUIDANCE = """\
A **persona** listing is a reusable AI personality — a system prompt with a voice.

What the gate requires before submit:
- `name`, `description` (at least 200 characters), `category` (a slug from `list_categories`).
- `main_prompt`: the persona's system prompt, complete and specific. Vague personas do not sell.

Fill the voice fields too — they are what makes a persona more than a prompt:
- `tone`: how it speaks (e.g. "dry, precise, never uses exclamation marks").
- `tagline`: one line a buyer sees on the card.
- `greeting`: its first message.
- `behavioral_notes`: what it always does, never does, and how it handles edge cases.
- `output_format`, `rules`, `context`, `when_responding`: the same sectioned fields a prompt has.

Keep everything in the persona's own voice, addressed to the end user — never to the platform.
"""

SKILL_GUIDANCE = """\
A **skill** listing follows the SKILL.md open standard: a frontmatter block and a markdown body an
AI agent can follow step by step.

What the gate requires before submit:
- `name`: the SKILL.md name — 1 to 64 characters of lowercase letters, digits and hyphens, no leading
  or trailing hyphen, and not containing the words "anthropic" or "claude". This is checked on
  every save, not only at submit.
- `description`: at least 200 characters, and at most 1024 (the SKILL.md limit).
- `category`: a slug from `list_categories`.
- `instructions`: the markdown body — numbered steps, the inputs the skill expects, what it
  produces, when to stop and ask.

Optional frontmatter: `license`, `compatibility`, `allowed_tools` (a list of tool names the skill
may use), `skill_metadata` (a flat string map).

If you already have a SKILL.md file on disk, `import_skill_md` creates the draft from it in one
call — the same parser the platform uses to export a purchased skill, so the round trip is exact.
`export_skill_md` writes a draft back to disk.
"""

MCP_SERVER_GUIDANCE = """\
An **MCP server** listing (item_type `mcp_server`) sells a server a buyer adds to their own AI
client — Claude Code, Cursor, VS Code. Sigrix holds no connection to it: the buyer's client starts the
server on the buyer's machine, from the launch this listing declares, and the download carries each
client's configuration for it.

`create_draft` takes the same arguments as for any type, but here `description` becomes the
listing's `summary`: the one or two sentences under its title (the web form allows 250 characters).

What the gate requires before submit:
- `name`: the listing's title (at most 80 characters).
- `summary`: what the server does and for whom. Change it later with `update_draft`'s `summary`.
- `server.name`: the server's own short name, the key a client's configuration files it under
  (e.g. `calendar`).
- A price that is free, or between $5 and $49, and a paid server must be one Sigrix delivers (below).

`server` is the launch, sent whole as one object with `update_draft`:
- `command` and `args`: what the buyer's client runs, e.g. `"command": "npx"` with
  `"args": ["-y", "@vendor/mcp-calendar"]`, or `"command": "uvx"` with `"args": ["vendor-mcp"]`.
  The platform refuses a shell or an interpreter handed its program inline (`sh -c`, `bash -c`,
  `cmd /c`, `python -c`, `node -e`, PowerShell's `-Command`), and shows a moderator anything that
  downloads, uses shell syntax or asks for administrator rights.
- `tools`: the names of the tools the server exposes. List at least one: the web form refuses to
  save a server with a command and no tools, and they are how a buyer judges what it can do.
- `env`: the names of the environment variables the buyer sets, such as an API key. Names only —
  never a value, and never your own key.
- `auth_command`: optional, a one-time sign-in the buyer runs outside the client
  (e.g. `npx @vendor/mcp-calendar auth`).

Fill `example_input` (how a client would call one of the tools) and `example_output` (a
representative result), and a `category` and a few `tags`, so a buyer can judge the server from its
page.

Price: a server launched by `npx` or `uvx` names a public package anyone can fetch, so it is listed
free (`price_cents` 0). To charge, Sigrix must deliver it: its seller uploads the server as a Python
package on the listing's Package step in the web form (or from CI), and no tool here uploads one.
`check_draft` names the row a price is still missing. The web form at `edit_url` also runs the
connection test a buyer's page reports; nothing here runs it.
"""

ASSISTANT_GUIDANCE = """\
An **assistant** listing (item_type `assistant`) sells a ready-made AI assistant: one prompt that does
a specific job, which a buyer installs in their own AI client, optionally with skills, a persona's
voice, MCP servers and documents of the buyer's own wired in.

What the gate requires before submit:
- `name`, `description` (at least 200 characters), `category` (a slug from `list_categories`).
- `main_prompt`: the assistant's prompt, complete — the product itself. Written to the assistant,
  in the second person, saying what it does, how, and when it asks the user for something.
- A sample for every document it asks for (below), if it asks for any.

Show it working: `example_input` and `example_output` are its first example exchange, and
`more_examples` holds the rest as `[{"input": "...", "output": "..."}]`, up to ten in all. Write the
prompt first: the examples are saved with it, and a write that sends them before it is refused.

Optional building blocks, each a slug of a listing on Sigrix:
- `skill_refs`: skills it uses, a list of skill slugs — published ones, or your own drafts.
- `persona_ref`: one of your own personas, whose voice opens the prompt.
- `prompt_ref`: one of your own text prompts, whose body is the assistant's task core in place of
  `main_prompt` (which stays as its fallback).
- `mcp_requirements`: MCP servers it uses, sent whole as a list: `{"mcp_ref": "<slug>"}` for a server
  listed on Sigrix, or an inline server in the MCP listing's `server` shape (`name`, `command`,
  `args`, `env`, `tools`), held to the same launch rules.
A slug that does not resolve to one you may use is dropped from the saved listing; read it back with
`get_listing` after saving.

Documents: `knowledge` declares what the assistant asks its buyer for, at most five, as
`[{"name": "refund_policy", "description": "...", "accepts": ["pdf", "md"], "required": true}]`
(a name is lowercase letters, digits and underscores, starting with a letter). Each one needs a
made-up sample before submit, uploaded in the web wizard at `edit_url`; no tool here uploads one.

Keep everything addressed to the buyer's use of the assistant — never to the platform or its reviewers.
"""

GUIDANCE_BY_TYPE = {
    "prompt": PROMPT_GUIDANCE,
    "persona": PERSONA_GUIDANCE,
    "skill": SKILL_GUIDANCE,
    "mcp_server": MCP_SERVER_GUIDANCE,
    "assistant": ASSISTANT_GUIDANCE,
}

#: Each type as a sentence names it; the item_type itself is the key.
TYPE_LABELS = {
    "prompt": "prompt",
    "persona": "persona",
    "skill": "skill",
    "mcp_server": "MCP server",
    "assistant": "assistant",
}

__all__ = [
    "ASSISTANT_GUIDANCE",
    "FLOW",
    "GUIDANCE_BY_TYPE",
    "MCP_SERVER_GUIDANCE",
    "PERSONA_GUIDANCE",
    "PROMPT_GUIDANCE",
    "SKILL_GUIDANCE",
    "TYPE_LABELS",
]
