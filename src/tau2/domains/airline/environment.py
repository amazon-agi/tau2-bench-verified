# Copyright Sierra
import os
from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.airline.data_model import FlightDB
from tau2.domains.airline.merge_wiki import merge_wiki_into_policy
from tau2.domains.airline.tools import AirlineTools
from tau2.domains.airline.utils import (
    AIRLINE_DB_PATH,
    AIRLINE_POLICY_PATH,
    AIRLINE_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(
    db: Optional[FlightDB] = None,
    solo_mode: bool = False,
) -> Environment:
    if solo_mode:
        raise ValueError("Airline domain does not support solo mode")
    if db is None:
        db = FlightDB.load(AIRLINE_DB_PATH)
    tools = AirlineTools(db)
    with open(AIRLINE_POLICY_PATH, "r") as fp:
        policy = fp.read()
        
    wiki_dir = os.environ.get("KB_DIR")
    wiki_mode = os.environ.get("KB_MODE")
    if wiki_dir:
        if wiki_mode == "override":
            policy = override_policy_with_wiki(wiki_dir)
        elif wiki_mode == "merge":
            policy = merge_wiki_into_policy(policy, wiki_dir)

    return Environment(
        domain_name="airline",
        policy=policy,
        tools=tools,
    )


def override_policy_with_wiki(kb_dir: str | Path) -> str:
    """Build a system prompt entirely from wiki articles, keeping only the date/time preamble."""
    kb_dir = Path(kb_dir)
    concepts_dir = kb_dir / "concepts"

    with open(AIRLINE_POLICY_PATH, "r") as fp:
        policy = fp.read()

    # Extract the current date/time line from the original policy
    date_line = ""
    for line in policy.splitlines():
        if "current time is" in line.lower():
            date_line = line.strip()
            break

    # Read all wiki articles
    articles: list[str] = []
    if concepts_dir.exists():
        for article_file in sorted(concepts_dir.glob("*.md")):
            articles.append(article_file.read_text().strip())

    # Compose: date preamble + concatenated wiki articles
    parts = []
    if date_line:
        parts.append(date_line)
        parts.append("")
    parts.append("\n\n---\n\n".join(articles))

    return "\n".join(parts)


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    tasks = load_file(AIRLINE_TASK_SET_PATH)
    tasks = [Task.model_validate(task) for task in tasks]
    if task_split_name is None:
        return tasks
    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Invalid task split name: {task_split_name}. Valid splits are: {task_splits.keys()}"
        )
    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    split_file = (
        Path(AIRLINE_TASK_SET_PATH).parent
        / f"split_{Path(AIRLINE_TASK_SET_PATH).stem}.json"
    )
    return load_file(split_file)
