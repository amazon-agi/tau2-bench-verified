"""Build a system prompt entirely from wiki articles, replacing the policy."""

from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.airline.utils import AIRLINE_POLICY_PATH
from pipeline.wiki_ops import WikiOps
from tau2.domains.airline.wiki.select_for_task import select_for_task


def override_policy_with_wiki(
    kb_dir: str | Path, task: Optional[Task] = None, model: str = "claude-sonnet-4-6",
) -> str:
    """Build a system prompt entirely from wiki articles, keeping only the date/time preamble."""
    wiki = WikiOps(kb_dir)

    with open(AIRLINE_POLICY_PATH, "r") as fp:
        policy = fp.read()

    # Extract the current date/time line from the original policy
    date_line = ""
    for line in policy.splitlines():
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
