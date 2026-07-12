"""Merge wiki knowledge into the airline policy."""

import re
from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from pipeline.wiki_ops import WikiOps


# Map the wiki page's `resource` frontmatter field to the policy H2 section
# it should be injected into.
RESOURCE_SECTION_MAP = {
    "book_reservation": "## Book flight",
    "cancel_reservation": "## Cancel flight",
    "update_reservation_flights": "## Modify flight",
    "send_certificate": "## Refunds and Compensation",
}

_SOURCE_CITATION_RE = re.compile(r"\s*\[\d+(?:,\s*\d+)*\]\s*$")
_SCOPE_RE = re.compile(r"\s*SCOPE:\s*.+$")


def _strip_wiki_metadata(bullet: str) -> str:
    """Remove source citations [N] and SCOPE: suffixes from a bullet."""
    bullet = _SOURCE_CITATION_RE.sub("", bullet)
    bullet = _SCOPE_RE.sub("", bullet)
    return bullet.rstrip()


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract simple key: value pairs from YAML frontmatter."""
    result = {}
    if not text.startswith("---"):
        return result
    end = text.find("---", 3)
    if end == -1:
        return result
    for line in text[3:end].splitlines():
        if ":" in line and not line.strip().startswith("-"):
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def _extract_key_points(text: str) -> list[str]:
    """Extract bullet points from the ## Key Points section."""
    bullets = []
    in_key_points = False

    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "## Key Points":
            in_key_points = True
        elif stripped.startswith("## ") and in_key_points:
            break
        elif stripped.startswith("- ") and in_key_points:
            bullets.append(stripped)

    return bullets


def merge_wiki_into_policy(
    policy_text: str,
    wiki_dir: str | Path,
    task: Optional[Task] = None,
    model: str = "claude-sonnet-4-6",
) -> str:
    """Merge wiki articles into the policy document.

    Prohibitions (NEVER bullets) are collected into a single MANDATORY GUARDRAILS
    section inserted before Domain Basic. Operational guidance is appended to the
    relevant policy section.
    """
    from tau2.domains.airline.wiki.select_for_task import select_for_task

    wiki = WikiOps(wiki_dir)

    if task:
        result = select_for_task(task, wiki, model=model)
        slugs = result.pages
    else:
        slugs = wiki.list_slugs()

    if not slugs:
        return policy_text

    all_guardrails: list[str] = []
    section_guidance: dict[str, list[str]] = {}

    for slug in sorted(slugs):
        article_text = wiki.read_concept_text(slug)
        frontmatter = _parse_frontmatter(article_text)
        resource = frontmatter.get("resource", "")

        target_section = RESOURCE_SECTION_MAP.get(resource)
        if not target_section:
            continue

        bullets = _extract_key_points(article_text)

        for bullet in bullets:
            cleaned = _strip_wiki_metadata(bullet)
            if not cleaned:
                continue

            if cleaned.lstrip("- ").startswith("NEVER"):
                all_guardrails.append(cleaned)
            else:
                section_guidance.setdefault(target_section, []).append(cleaned)

    if not all_guardrails and not section_guidance:
        return policy_text

    # Remove the "Using The knowledge base" section if present
    kb_marker = "# Using The knowledge base"
    if kb_marker in policy_text:
        policy_text = policy_text[: policy_text.index(kb_marker)].rstrip() + "\n"

    # Build the guardrails block
    if all_guardrails:
        guardrails_block = (
            "\n---\n\n"
            "## MANDATORY GUARDRAILS\n\n"
            "These rules are absolute. They override user requests, emotional appeals, "
            "claimed privileges, or insistence. Do NOT grant exceptions even if the user "
            'says "yes, go ahead" or "just do it."\n\n'
        )
        for rule in all_guardrails:
            guardrails_block += f"{rule}\n"
        guardrails_block += "\n---\n"

        # Insert guardrails after the preamble (before ## Domain Basic)
        insert_marker = "## Domain Basic"
        if insert_marker in policy_text:
            idx = policy_text.index(insert_marker)
            policy_text = (
                policy_text[:idx].rstrip()
                + "\n"
                + guardrails_block
                + "\n"
                + policy_text[idx:]
            )

    # Append operational guidance to each relevant section
    for section_heading, bullets in section_guidance.items():
        if section_heading not in policy_text:
            continue

        guidance_block = (
            f"\n### Operational guidance\n\n" + "\n".join(bullets) + "\n"
        )

        # Find the end of this section (next ## heading or end of file)
        section_start = policy_text.index(section_heading)
        rest = policy_text[section_start + len(section_heading) :]
        next_h2 = rest.find("\n## ")
        if next_h2 == -1:
            policy_text = policy_text.rstrip() + "\n" + guidance_block
        else:
            insert_pos = section_start + len(section_heading) + next_h2
            policy_text = (
                policy_text[:insert_pos].rstrip()
                + "\n"
                + guidance_block
                + "\n"
                + policy_text[insert_pos:]
            )

    # Add enforcement line to the preamble
    deny_line = "You should deny user requests that are against this policy."
    enforcement = (
        "You should deny user requests that are against this policy. "
        "If a user asks you to violate any rule below, refuse and offer to "
        "transfer to a human agent. No exceptions."
    )
    if deny_line in policy_text and enforcement not in policy_text:
        policy_text = policy_text.replace(deny_line, enforcement)

    return policy_text
