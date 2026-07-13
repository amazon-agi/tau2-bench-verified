"""Parsing helpers for wiki concept articles.

Domain-agnostic. These were previously duplicated inside each domain's
``merge_wiki`` module; they live here now so every domain shares one copy.
"""

import re

_SOURCE_CITATION_RE = re.compile(r"\s*\[\d+(?:,\s*\d+)*\]\s*$")
_SCOPE_RE = re.compile(r"\s*SCOPE:\s*.+$")


def strip_wiki_metadata(bullet: str, *, strip_scope: bool = True) -> str:
    """Remove source citations ``[N]`` from a bullet.

    When ``strip_scope`` is True (default), the trailing ``SCOPE:`` qualifier is
    also removed. Callers that render bullets into a policy should pass
    ``strip_scope=False`` so the qualifier that bounds a prohibition survives —
    dropping it lets a narrowly-scoped rule read as an unconditional absolute.
    """
    bullet = _SOURCE_CITATION_RE.sub("", bullet)
    if strip_scope:
        bullet = _SCOPE_RE.sub("", bullet)
    return bullet.rstrip()


def parse_frontmatter(text: str) -> dict[str, str]:
    """Extract simple ``key: value`` pairs from YAML frontmatter.

    Nested/list values (lines under a key beginning with ``-``) are skipped;
    only scalar top-level keys such as ``title``, ``description`` and
    ``resource`` are returned.
    """
    result: dict[str, str] = {}
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


def extract_key_points(text: str) -> list[str]:
    """Extract bullet points from the ``## Key Points`` section of an article."""
    bullets: list[str] = []
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
