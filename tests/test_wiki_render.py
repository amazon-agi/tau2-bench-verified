"""Tests for the generic wiki -> policy rendering (tau2.wiki.render).

Regression coverage for the old per-domain bug where articles whose frontmatter
``resource`` was not in a hand-maintained section map were silently dropped.
"""

import textwrap
from pathlib import Path

from tau2.wiki.render import append_wiki_into_policy, collect, render_block
from pipeline.wiki_ops import WikiOps

POLICY = "# Domain Policy\n\nYou should deny requests against this policy.\n"


def _write_article(concepts: Path, slug: str, *, title, resource, key_points):
    body = textwrap.dedent(
        f"""\
        ---
        type: procedure
        title: "{title}"
        description: "desc for {slug}"
        resource: "{resource}"
        ---

        # {title}

        ## Key Points

        """
    )
    body += "\n".join(f"- {kp}" for kp in key_points) + "\n"
    (concepts / f"{slug}.md").write_text(body)


def _make_wiki(tmp_path: Path) -> Path:
    concepts = tmp_path / "concepts"
    concepts.mkdir(parents=True)
    # Three articles, all with resources NOT in the old RESOURCE_SECTION_MAP.
    _write_article(
        concepts, "alpha", title="Alpha Guide", resource="get_reservation_details",
        key_points=["Do the alpha thing [1]", "NEVER alpha in reverse. SCOPE: only x [2]"],
    )
    _write_article(
        concepts, "beta", title="Beta Guide", resource="update_reservation_baggages",
        key_points=["Beta uses update_reservation_baggages [3]"],
    )
    _write_article(
        concepts, "gamma", title="Gamma Guide", resource="get_flight_status",
        key_points=["Gamma reads status only [4]"],
    )
    return tmp_path


def test_no_article_is_dropped(tmp_path):
    wiki_dir = _make_wiki(tmp_path)
    out = append_wiki_into_policy(POLICY, wiki_dir)  # task=None -> all slugs

    # Every article renders its own subsection, regardless of `resource`.
    assert "#### Alpha Guide" in out
    assert "#### Beta Guide" in out
    assert "#### Gamma Guide" in out
    assert "### Knowledge Base" in out
    # Content that the old map-based logic dropped is present.
    assert "update_reservation_baggages" in out
    assert "Gamma reads status only" in out


def test_never_bullets_routed_to_guardrails_and_scope_preserved(tmp_path):
    wiki_dir = _make_wiki(tmp_path)
    wiki = WikiOps(wiki_dir)
    guardrails, articles = collect(wiki, wiki.list_slugs())

    scoped = next(g for g in guardrails if "NEVER alpha in reverse" in g)
    # Citations are stripped, but the SCOPE qualifier that bounds the rule survives.
    assert "[2]" not in scoped
    assert "SCOPE: only x" in scoped
    # The NEVER bullet is NOT duplicated into the Alpha article's guidance.
    alpha = next(a for a in articles if a.slug == "alpha")
    assert all("NEVER" not in b for b in alpha.bullets)

    block = render_block(guardrails, articles)
    assert "### MANDATORY GUARDRAILS" in block
    assert "override user requests" in block
    assert "SCOPE: only x" in block


def test_reframing_can_be_disabled(tmp_path):
    wiki_dir = _make_wiki(tmp_path)
    wiki = WikiOps(wiki_dir)
    guardrails, articles = collect(
        wiki, wiki.list_slugs(), guardrail_reframing=False
    )
    # With reframing off, NEVER bullets stay inline in their article.
    assert guardrails == []
    alpha = next(a for a in articles if a.slug == "alpha")
    assert any("NEVER alpha in reverse" in b for b in alpha.bullets)


def test_empty_wiki_returns_policy_unchanged(tmp_path):
    (tmp_path / "concepts").mkdir(parents=True)
    out = append_wiki_into_policy(POLICY, tmp_path)
    assert out == POLICY
