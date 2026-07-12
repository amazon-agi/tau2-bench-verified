from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tau2.environment.knowledge_toolkit import KnowledgeTools
from tau2.environment.toolkit import ToolType


class TestKnowledgeTools:
    @patch("tau2.environment.knowledge_toolkit.KnowledgeTool")
    def test_list_articles_delegates(self, mock_kb_class):
        mock_kb = MagicMock()
        mock_kb.list_articles.return_value = "| slug | title |\n|---|---|\n| foo | Foo |"
        mock_kb_class.return_value = mock_kb

        kt = KnowledgeTools(Path("/fake/kb"))
        result = kt.list_articles()

        mock_kb.list_articles.assert_called_once()
        assert "foo" in result

    @patch("tau2.environment.knowledge_toolkit.KnowledgeTool")
    def test_get_article_delegates(self, mock_kb_class):
        mock_kb = MagicMock()
        mock_kb.get_article.return_value = "Article content here"
        mock_kb_class.return_value = mock_kb

        kt = KnowledgeTools(Path("/fake/kb"))
        result = kt.get_article("cancelling-a-flight")

        mock_kb.get_article.assert_called_once_with("cancelling-a-flight")
        assert result == "Article content here"

    @patch("tau2.environment.knowledge_toolkit.KnowledgeTool")
    def test_tools_are_registered(self, mock_kb_class):
        mock_kb_class.return_value = MagicMock()
        kt = KnowledgeTools(Path("/fake/kb"))
        tool_names = set(kt.get_tools().keys())
        assert tool_names == {"list_articles", "get_article"}

    @patch("tau2.environment.knowledge_toolkit.KnowledgeTool")
    def test_tools_are_read_type(self, mock_kb_class):
        mock_kb_class.return_value = MagicMock()
        kt = KnowledgeTools(Path("/fake/kb"))
        assert kt.tool_type("list_articles") == ToolType.READ
        assert kt.tool_type("get_article") == ToolType.READ
