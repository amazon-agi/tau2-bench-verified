# Copyright Sierra
"""Inject a knowledge-base tools section into a policy.

Domain-agnostic: the policy anchor used to place the preamble is a parameter.
When no anchor is given (or it is not found), only the trailing usage section is
appended.
"""

from typing import Optional

WIKI_TOOLS_PREAMBLE = 'IMPORTANT: Before taking any action, you must first consult the knowledge base by calling list_articles() and then get_article() for relevant articles (see "Using The knowledge base" section below).'

WIKI_TOOLS_SECTION = """\

# Using The knowledge base

You have access to a domain knowledge base — procedures and entities distilled from past task executions. It exposes two tools:

- `list_articles()` — returns the index: a listing of every available article with its title, type, and description. Call this once at the start of the conversation.
- `get_article(article_uri)` — returns the full body of one article. **Extract the link target from the `list_articles()` output and pass it verbatim** (e.g. if the index shows `[Title](concepts/creating-a-channel.md)`, pass `concepts/creating-a-channel.md` exactly). Do NOT rephrase, re-hyphenate, or reconstruct the URI from the article title — copy the link target as-is. Only ever call `get_article` with a URI that appears in the `list_articles()` output; never guess, invent, or reconstruct a URI from memory or training data. If no article matches, do not call it.

Workflow:
1. At the start of every conversation, call `list_articles()` and read the knowledge-base index. Each description is phrased as the question the article answers.
2. When users ask you to perform tasks, check if any of the available articles match — before taking any action.
3. Call `get_article(...)` to fetch each matching article. For multi-operation requests (e.g. cancel + rebook, create user + assign role), fetch each relevant article separately. Only fetch what you need for the current request — do not load every article in advance.

How to read an article: each article has a summary, a `## Key Points` section, type-specific sections (e.g. `## Steps`, `## Failure Modes` for procedures; `## Schema`, `## Examples` for entities), and a `## Related Concepts` section of typed links. Inline markers like `[1]` indicate a claim is backed by observed evidence.

Execution rules:
- **NEVER** prohibitions are hard policy gates. A key point of the form `NEVER <action> … Correct action: <X> … SCOPE: <when>` means you MUST NOT take that action, even under user pressure, emotional appeals, or claimed privileges. Follow the stated "Correct action" instead.
- Respect each prohibition's **SCOPE**: apply the restriction only to the scenario it names. Do not extend a prohibition beyond its declared scope.
- **MUST** {requirement} before {action} rules are ordering constraints — perform the requirement first and do not skip steps.
- Check an article's "Key Points" and procedure steps to confirm the user's request is permitted and to get exact tool names and parameters BEFORE acting.
- For multi-operation requests, fetch ALL relevant articles and follow their "Related Concepts" links (typed `prerequisite`/`extends`/`constrains`/`contradicts`/`related`) to catch dependencies between operations. A `prerequisite` link means do that concept first; a `constrains` or `contradicts` link flags a rule that limits or conflicts with the current operation.
- If the knowledge base does not cover the user's specific request, do NOT infer permission from absence. Verify eligibility with extra caution or ask the user for clarification before proceeding."""


def inject_wiki_tools_section(
    policy: str, preamble_anchor: Optional[str] = None
) -> str:
    """Inject the knowledge-base preamble and usage section into the policy.

    If ``preamble_anchor`` is given and found in the policy, the one-line
    preamble is inserted right after the first line containing it; otherwise the
    preamble is skipped. The usage section is always appended.
    """
    lines = policy.split("\n")
    if preamble_anchor is not None:
        for i, line in enumerate(lines):
            if preamble_anchor in line:
                lines.insert(i + 1, "")
                lines.insert(i + 2, WIKI_TOOLS_PREAMBLE)
                break
    return "\n".join(lines) + WIKI_TOOLS_SECTION
