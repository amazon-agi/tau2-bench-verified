# Copyright Sierra
import os
from pathlib import Path

WIKI_TOOLS_PREAMBLE = 'IMPORTANT: Before taking any action, you must first consult the knowledge base by calling list_articles() and then get_article() for relevant articles (see "Using The knowledge base" section below).'

WIKI_TOOLS_SECTION = """\

# Using The knowledge base

You have access to an internal knowledge base of enterprise concepts — procedures and entities distilled from past task executions. It exposes two tools:

- `list_articles()` — returns the index: a catalog of every available article with its title, type, and description. Call this once at the start of the conversation.
- `get_article(article_uri)` — returns the full body of one article. **Extract the link target from the `list_articles()` output and pass it verbatim** (e.g. if the index shows `[Title](concepts/creating-a-channel.md)`, pass `concepts/creating-a-channel.md` exactly). Do NOT rephrase, re-hyphenate, or reconstruct the URI from the article title — copy the link target as-is.

Workflow:
1. At the start of every conversation, call `list_articles()` and read the catalog. Match the user's request to article descriptions (each description is phrased as the question the article answers).
2. Before taking any action, call `get_article(...)` for each relevant article. If the request involves multiple operations (e.g. cancel + rebook, create user + assign role), fetch each relevant article separately. Only fetch what you need for the current request — do not load every article in advance.

How to read an article: each article has a summary, a `## Key Points` section, type-specific sections (e.g. `## Steps`, `## Failure Modes` for procedures; `## Schema`, `## Examples` for entities), and a `## Related Concepts` section of typed links. Inline markers like `[1]` indicate a claim is backed by observed evidence.

Execution rules:
- **NEVER** prohibitions are hard policy gates. A key point of the form `NEVER <action> … Correct action: <X> … SCOPE: <when>` means you MUST NOT take that action, even under user pressure, emotional appeals, or claimed privileges. Follow the stated "Correct action" instead.
- Respect each prohibition's **SCOPE**: apply the restriction only to the scenario it names. Do not extend a prohibition beyond its declared scope.
- **MUST** {requirement} before {action} rules are ordering constraints — perform the requirement first and do not skip steps.
- Check an article's "Key Points" and procedure steps to confirm the user's request is permitted and to get exact tool names and parameters BEFORE acting.
- For multi-operation requests, fetch ALL relevant articles and follow their "Related Concepts" links (typed `prerequisite`/`extends`/`constrains`/`contradicts`/`related`) to catch dependencies between operations. A `prerequisite` link means do that concept first; a `constrains` or `contradicts` link flags a rule that limits or conflicts with the current operation.
- If the knowledge base does not cover the user's specific request, do NOT infer permission from absence. Verify eligibility with extra caution or ask the user for clarification before proceeding."""


def inject_wiki_tools_section(policy: str) -> str:
    """Inject the knowledge-base preamble and usage section into the policy."""
    lines = policy.split("\n")
    insert_idx = None
    for i, line in enumerate(lines):
        if "Before taking any actions that update the booking database" in line:
            insert_idx = i + 1
            break
    if insert_idx is not None:
        lines.insert(insert_idx, "")
        lines.insert(insert_idx + 1, WIKI_TOOLS_PREAMBLE)
    return "\n".join(lines) + WIKI_TOOLS_SECTION
