"""Toolkit providing knowledge base article tools."""

from pathlib import Path

from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool
from tau2.utils.display import ConsoleDisplay

class KnowledgeTools(ToolKitBase):
    """Tools for browsing a knowledge base of articles."""

    def __init__(self, kb_dir: Path) -> None:
        super().__init__(db=None)
        from pipeline.runtime.knowledge_tool import KnowledgeTool
        self._kb = KnowledgeTool(kb_dir)
        ConsoleDisplay.console.print("KnowledgeTools initialized with knowledge base at:", kb_dir)

    @is_tool(ToolType.READ)
    def list_articles(self) -> str:
        """
        List the knowledge articles available. Returns a markdown table of every
        article with its title, type, and description. Call this first to discover
        which articles exist, then fetch the relevant ones with get_article.

        Returns:
            The contents of the knowledge article index.

        Raises:
            ValueError: If the knowledge base is not configured or the index is empty.
        """
        ConsoleDisplay.console.print("list_articles()")
        return self._kb.list_articles()

    @is_tool(ToolType.READ)
    def get_article(self, article_slug: str) -> str:
        """
        Read a single knowledge article by its slug.

        Args:
            article_slug: The article's slug as shown in the index, e.g.
                "cancelling-a-flight-reservation". A leading "concepts/" prefix
                and a trailing ".md" suffix are both accepted and ignored.

        Returns:
            The text contents of the requested article.

        Raises:
            ValueError: If the knowledge base is not configured or the article does not exist.
        """
        ConsoleDisplay.console.print(f"get_article({article_slug})")
        return self._kb.get_article(article_slug)
