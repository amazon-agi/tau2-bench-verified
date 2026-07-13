"""Domain-agnostic wiki -> policy rendering.

See :mod:`tau2.wiki.render` for the public entry points
(:func:`append_wiki_into_policy`, :func:`merge_wiki_into_policy`).
"""

from tau2.wiki.inject_wiki_tools import inject_wiki_tools_section
from tau2.wiki.override_wiki import override_policy_with_wiki
from tau2.wiki.render import (
    append_wiki_into_policy,
    merge_wiki_into_policy,
)
from tau2.wiki.select_for_task import select_for_task

__all__ = [
    "append_wiki_into_policy",
    "merge_wiki_into_policy",
    "override_policy_with_wiki",
    "inject_wiki_tools_section",
    "select_for_task",
]
