# Copyright Sierra
import os
from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.airline.data_model import FlightDB
from tau2.wiki import (
    append_wiki_into_policy,
    inject_wiki_tools_section,
    merge_wiki_into_policy,
    override_policy_with_wiki,
)
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
    task: Optional[Task] = None,
) -> Environment:
    if solo_mode:
        raise ValueError("Airline domain does not support solo mode")
    if db is None:
        db = FlightDB.load(AIRLINE_DB_PATH)
    tools = AirlineTools(db)

    with open(AIRLINE_POLICY_PATH, "r") as fp:
        policy = fp.read()

    kb_dir = os.environ.get("KB_DIR")
    if kb_dir:
        wiki_mode = os.environ.get("KB_MODE")

        kb_task = None
        if os.environ.get("KB_PER_TASK"):
            kb_task = task

        if wiki_mode == "tools":
            from tau2.environment.knowledge_toolkit import KnowledgeTools
            from tau2.environment.toolkit import CompositeToolKit
            kb_tools = KnowledgeTools(Path(kb_dir))
            tools = CompositeToolKit(tools, kb_tools)
            policy = inject_wiki_tools_section(
                policy,
                preamble_anchor="Before taking any actions that update the booking database",
            )
        elif wiki_mode == "override":
            policy = override_policy_with_wiki(policy, kb_dir, task=kb_task)
        elif wiki_mode == "merge":
            policy = merge_wiki_into_policy(policy, kb_dir, task=kb_task)
        elif wiki_mode == "append":
            policy = append_wiki_into_policy(policy, kb_dir, task=kb_task)

    return Environment(
        domain_name="airline",
        policy=policy,
        tools=tools,
    )



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
