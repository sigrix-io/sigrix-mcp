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

GUIDANCE_BY_TYPE = {
    "prompt": PROMPT_GUIDANCE,
    "persona": PERSONA_GUIDANCE,
    "skill": SKILL_GUIDANCE,
}

__all__ = ["FLOW", "GUIDANCE_BY_TYPE", "PERSONA_GUIDANCE", "PROMPT_GUIDANCE", "SKILL_GUIDANCE"]
