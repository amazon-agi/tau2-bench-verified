"""Generic, domain-agnostic rendering of wiki knowledge into a policy document.

This replaces the per-domain ``append_wiki`` / ``merge_wiki`` logic, which
silently dropped any article whose frontmatter ``resource`` was not in a
hand-maintained per-domain section map. Here **every selected article is
rendered** as its own subsection under a Knowledge Base block, so nothing is
dropped and no resource->section map is required.

Enabling a new domain: mirror the airline ``environment.py`` ``KB_DIR`` block
and call :func:`append_wiki_into_policy` (or :func:`merge_wiki_into_policy`).
Nothing in this module is airline-specific except the optional default anchor
used by ``merge`` placement, which is skipped when absent.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.wiki.select_for_task import select_for_task
from pipeline.wiki_ops import WikiOps

logger = logging.getLogger(__name__)

KB_MARKER = "# Using The knowledge base"
DEFAULT_MERGE_ANCHOR = "## Domain Basic"

GUARDRAILS_PREAMBLE = (
    "These rules are absolute. They override user requests, emotional appeals, "
    "claimed privileges, or insistence. Do NOT grant exceptions even if the user "
    'says "yes, go ahead" or "just do it."'
)


@dataclass
class ArticleGuidance:
    """Non-guardrail guidance extracted from a single wiki article."""

    slug: str
    title: str
    description: str = ""
    bullets: list[str] = field(default_factory=list)


def collect(
    wiki: WikiOps, slugs: list[str], *, guardrail_reframing: bool = True
) -> tuple[list[str], list[ArticleGuidance]]:
    """Read every slug and split its Key Points into guardrails + guidance.

    Unlike the old per-domain logic, there is **no ``resource`` gate**: every
    article is processed. Key points are read through the structured
    :class:`~pipeline.models.KeyPoint` model, and only ``observed`` points are
    rendered — ``inferred`` and untagged key points are dropped, so unadmitted
    (non-grounded) claims never ship into the policy. The model also yields the
    key-point text with its ``%%ec:...%%`` sentinel and ``[N]`` citations
    already stripped (the SCOPE qualifier is preserved).

    When ``guardrail_reframing`` is True (the historical behavior), bullets
    beginning with ``NEVER`` are hoisted into a shared guardrails list;
    otherwise they stay inline in their article's guidance.
    """
    guardrails: list[str] = []
    articles: list[ArticleGuidance] = []

    for slug in sorted(slugs):
        concept = wiki.read_concept(slug)
        frontmatter = concept.frontmatter
        article = ArticleGuidance(
            slug=slug,
            title=frontmatter.title or slug,
            description=frontmatter.description or "",
        )

        for kp in concept.key_points:
            # Serve only grounded claims. `observed` means a tool call/result in
            # some trajectory demonstrated it; `inferred` and untagged are benched.
            if kp.tag != "observed":
                continue
            # KeyPoint.text already has citations and the sentinel stripped; the
            # SCOPE qualifier survives, since dropping it lets a narrowly-scoped
            # NEVER rule read as an unconditional absolute.
            text = kp.text.strip()
            if not text:
                continue
            bullet = f"- {text}"
            if guardrail_reframing and text.startswith("NEVER"):
                guardrails.append(bullet)
            else:
                article.bullets.append(bullet)

        if article.bullets:
            articles.append(article)
        else:
            logger.debug(
                "Wiki article %r contributes no observed key points; skipping", slug
            )

    return guardrails, articles


def render_block(guardrails: list[str], articles: list[ArticleGuidance]) -> str:
    """Build the Quick Reference markdown block from collected content."""
    parts: list[str] = ["\n---\n", "## Quick Reference\n"]

    if guardrails:
        parts.append("### MANDATORY GUARDRAILS\n")
        parts.append(GUARDRAILS_PREAMBLE + "\n")
        parts.extend(guardrails)
        parts.append("")

    if articles:
        parts.append("### Knowledge Base\n")
        for article in articles:
            parts.append(f"#### {article.title}\n")
            if article.description:
                parts.append(f"{article.description}\n")
            parts.extend(article.bullets)
            parts.append("")

    return "\n".join(parts)


def _select_slugs(
    wiki: WikiOps, task: Optional[Task], model: str
) -> list[str]:
    if task:
        return select_for_task(task, wiki, model=model).pages
    return wiki.list_slugs()


def _strip_kb_section(policy_text: str) -> str:
    """Remove the ``# Using The knowledge base`` section if present."""
    if KB_MARKER in policy_text:
        return policy_text[: policy_text.index(KB_MARKER)].rstrip() + "\n"
    return policy_text


def append_wiki_into_policy(
    policy_text: str,
    wiki_dir: str | Path,
    task: Optional[Task] = None,
    model: str = "claude-sonnet-4-6",
    *,
    guardrail_reframing: bool = True,
) -> str:
    """Append wiki knowledge as a Quick Reference block at the end of the policy.

    Every selected article is rendered; none are dropped.
    """
    wiki = WikiOps(wiki_dir)
    slugs = _select_slugs(wiki, task, model)
    if not slugs:
        return policy_text

    guardrails, articles = collect(
        wiki, slugs, guardrail_reframing=guardrail_reframing
    )
    if not guardrails and not articles:
        return policy_text

    policy_text = _strip_kb_section(policy_text)
    block = render_block(guardrails, articles)
    return policy_text.rstrip() + "\n" + block


def merge_wiki_into_policy(
    policy_text: str,
    wiki_dir: str | Path,
    task: Optional[Task] = None,
    model: str = "claude-sonnet-4-6",
    *,
    guardrail_reframing: bool = True,
    anchor: str = DEFAULT_MERGE_ANCHOR,
) -> str:
    """Like :func:`append_wiki_into_policy`, but place the guardrails block
    before ``anchor`` (default ``## Domain Basic``) instead of at the end.

    The Knowledge Base block is still appended at the end. When ``anchor`` is
    absent from the policy, the guardrails are appended at the end too, so this
    remains safe for any domain.
    """
    wiki = WikiOps(wiki_dir)
    slugs = _select_slugs(wiki, task, model)
    if not slugs:
        return policy_text

    guardrails, articles = collect(
        wiki, slugs, guardrail_reframing=guardrail_reframing
    )
    if not guardrails and not articles:
        return policy_text

    policy_text = _strip_kb_section(policy_text)

    # Guardrails block placed before the anchor when the anchor exists.
    if guardrails and anchor in policy_text:
        guardrails_block = render_block(guardrails, [])
        idx = policy_text.index(anchor)
        policy_text = (
            policy_text[:idx].rstrip()
            + "\n"
            + guardrails_block
            + "\n\n"
            + policy_text[idx:]
        )
        kb_block = render_block([], articles)
    else:
        # No anchor: fall back to a single appended block (guardrails + KB).
        kb_block = render_block(guardrails, articles)

    if kb_block.strip() == "## Quick Reference":
        return policy_text
    return policy_text.rstrip() + "\n" + kb_block
