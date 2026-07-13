"""Build a system prompt entirely from wiki articles, replacing the policy.

Domain-agnostic: the caller passes the original policy text (used only to carry
over a date/time preamble line); no domain constant is imported here.
"""

from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.wiki.select_for_task import select_for_task
from pipeline.wiki_ops import WikiOps


def override_policy_with_wiki(
    policy_text: str,
    kb_dir: str | Path,
    task: Optional[Task] = None,
    model: str = "claude-sonnet-4-6",
) -> str:
    """Build a system prompt entirely from wiki articles, keeping only the
    date/time preamble line found in ``policy_text``."""
    wiki = WikiOps(kb_dir)

    # Carry over the current date/time line from the original policy, if any.
    date_line = ""
    for line in policy_text.splitlines():
        if "current time is" in line.lower():
            date_line = line.strip()
            break

    # Read relevant wiki articles
    if task:
        result = select_for_task(task, wiki, model=model)
        slugs = result.pages
    else:
        slugs = wiki.list_slugs()

    articles: list[str] = []
    for slug in sorted(slugs):
        if wiki.concept_exists(slug):
            articles.append(wiki.read_concept_text(slug).strip())

    # Compose: date preamble + concatenated wiki articles
    parts = []
    if date_line:
        parts.append(date_line)
        parts.append("")
    parts.append("\n\n---\n\n".join(articles))

    return "\n".join(parts)
