"""Select which wiki pages are relevant to a task.

Domain-agnostic: depends only on ``Task`` and the wiki index. Moved here from
the airline package so every domain shares one implementation.
"""

import logging

import litellm

from tau2.data_model.tasks import Task
from pipeline.ingest.models import SelectResult
from pipeline.models import Usage
from pipeline.utils.llm import extract_json
from pipeline.wiki_ops import WikiOps

logger = logging.getLogger(__name__)

litellm.suppress_debug_info = True

SYSTEM_PROMPT = """\
You are a wiki routing assistant. Given a task description and a wiki index, \
select which existing wiki pages contain concepts relevant to solving this task. \
Return only pages whose content an agent would need to know to handle the task correctly.

The wiki index contains rows like: | [Title](concepts/some-slug.md) | type | description |
Return the SLUG (the filename without path or extension, e.g. "some-slug") — NOT the title.

Respond with JSON matching this schema exactly:
{"pages": ["some-slug", "another-slug"]}
"""


def _format_task(task: Task) -> str:
    lines = [f"## Task ID: {task.id}"]

    if task.description and task.description.purpose:
        lines.append(f"Purpose: {task.description.purpose}")

    instructions = task.user_scenario.instructions
    if instructions:
        if instructions.reason_for_call:
            lines.append(f"Reason for call: {instructions.reason_for_call}")
        if instructions.task_instructions:
            lines.append(f"Task instructions: {instructions.task_instructions}")
        if instructions.known_info:
            lines.append(f"Known info: {instructions.known_info}")
        if instructions.domain:
            lines.append(f"Domain: {instructions.domain}")

    if task.evaluation_criteria:
        if task.evaluation_criteria.actions:
            action_names = [a.name for a in task.evaluation_criteria.actions if a.name]
            if action_names:
                lines.append(f"Expected actions: {', '.join(action_names)}")
        if task.evaluation_criteria.nl_assertions:
            lines.append(
                f"Assertions: {'; '.join(task.evaluation_criteria.nl_assertions)}"
            )

    return "\n".join(lines)


_cache: dict[str, SelectResult] = {}


def select_for_task(task: Task, wiki: WikiOps, model: str) -> SelectResult:
    """Return wiki concept slugs relevant to the given task.

    Uses an LLM to match the task description against the wiki index.
    """
    if task.id in _cache:
        return _cache[task.id]

    index_content = wiki.read_index()
    if not index_content.strip():
        return SelectResult(pages=[])

    user_prompt = f"{_format_task(task)}\n\n## Wiki Index\n{index_content}"

    response = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        custom_llm_provider="openai",
        response_format={"type": "json_object"},
    )

    usage_info = getattr(response, "usage", None)
    usage = Usage(
        prompt_tokens=getattr(usage_info, "prompt_tokens", 0),
        completion_tokens=getattr(usage_info, "completion_tokens", 0),
    )
    content = response.choices[0].message.content or ""
    json_str = extract_json(content)
    try:
        result = SelectResult.model_validate_json(json_str)
    except Exception as e:
        logger.warning(f"select_for_task validation failed: {e}")
        return SelectResult(pages=[], usage=usage)
    result.pages = [WikiOps.normalize_slug(p) for p in result.pages]
    result.usage = usage
    _cache[task.id] = result
    return result
