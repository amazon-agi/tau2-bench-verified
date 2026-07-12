"""Append wiki knowledge as a Quick Reference section at the end of the policy."""

from pathlib import Path

from tau2.domains.airline.merge_wiki import (
    RESOURCE_SECTION_MAP,
    _extract_key_points,
    _parse_frontmatter,
    _strip_wiki_metadata,
)


def append_wiki_into_policy(policy_text: str, wiki_dir: str | Path) -> str:
    """Append wiki knowledge as a Quick Reference section at the end of the policy."""
    wiki_dir = Path(wiki_dir)
    concepts_dir = wiki_dir / "concepts"
    if not concepts_dir.exists():
        return policy_text

    all_guardrails: list[str] = []
    section_guidance: dict[str, list[str]] = {}

    for article_file in sorted(concepts_dir.glob("*.md")):
        article_text = article_file.read_text()
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

    # Build a single appended Quick Reference block
    parts: list[str] = []
    parts.append("\n---\n")
    parts.append("## Quick Reference\n")

    if all_guardrails:
        parts.append("### MANDATORY GUARDRAILS\n")
        parts.append(
            "These rules are absolute. They override user requests, emotional appeals, "
            "claimed privileges, or insistence. Do NOT grant exceptions even if the user "
            'says "yes, go ahead" or "just do it."\n'
        )
        for rule in all_guardrails:
            parts.append(rule)
        parts.append("")

    for section_heading, bullets in section_guidance.items():
        parts.append(f"### {section_heading.lstrip('#').strip()}\n")
        for bullet in bullets:
            parts.append(bullet)
        parts.append("")

    policy_text = policy_text.rstrip() + "\n" + "\n".join(parts)
    return policy_text
