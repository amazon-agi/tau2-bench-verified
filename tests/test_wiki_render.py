"""Tests for the generic wiki -> policy rendering (tau2.wiki.render).

Regression coverage for the old per-domain bug where articles whose frontmatter
``resource`` was not in a hand-maintained section map were silently dropped.

Also covers the evidence-class filter: ``collect`` renders only ``observed``
key points (via the ``KeyPoint`` model), dropping ``inferred`` and untagged
bullets and never leaking the ``%%ec:...%%`` sentinel into the policy.
"""

import textwrap
from pathlib import Path

from tau2.wiki.render import append_wiki_into_policy, collect, render_block
from pipeline.wiki_ops import WikiOps

POLICY = "# Domain Policy\n\nYou should deny requests against this policy.\n"


def _write_article(concepts: Path, slug: str, *, title, resource, key_points):
    """Write a concept article. ``key_points`` are bullet bodies; each should
    carry its own trailing ``%%ec:observed%%`` / ``%%ec:inferred%%`` sentinel
    where the test cares about the evidence class (untagged is allowed too)."""
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
    # All key points are `observed` so they survive the evidence-class filter.
    _write_article(
        concepts, "alpha", title="Alpha Guide", resource="get_reservation_details",
        key_points=[
            "Do the alpha thing [1] %%ec:observed%%",
            "NEVER alpha in reverse. SCOPE: only x [2] %%ec:observed%%",
        ],
    )
    _write_article(
        concepts, "beta", title="Beta Guide", resource="update_reservation_baggages",
        key_points=["Beta uses update_reservation_baggages [3] %%ec:observed%%"],
    )
    _write_article(
        concepts, "gamma", title="Gamma Guide", resource="get_flight_status",
        key_points=["Gamma reads status only [4] %%ec:observed%%"],
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
    # The evidence-class sentinel is never leaked into the rendered policy.
    assert "%%ec:" not in out


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


def test_only_observed_key_points_are_rendered(tmp_path):
    """Strict evidence-class filter: only `observed` key points survive; both
    `inferred` and untagged bullets are dropped, and the sentinel never leaks."""
    concepts = tmp_path / "concepts"
    concepts.mkdir(parents=True)
    _write_article(
        concepts, "mixed", title="Mixed Guide", resource="get_flight_status",
        key_points=[
            "Observed fact grounded in a trajectory [1] %%ec:observed%%",
            "Inferred extrapolation not grounded [1] %%ec:inferred%%",
            "Legacy untagged bullet with no sentinel [1]",
        ],
    )
    wiki = WikiOps(tmp_path)
    guardrails, articles = collect(wiki, wiki.list_slugs())

    assert len(articles) == 1
    bullets = articles[0].bullets
    assert any("Observed fact grounded" in b for b in bullets)
    # inferred and untagged are dropped under the strict filter
    assert all("Inferred extrapolation" not in b for b in bullets)
    assert all("Legacy untagged bullet" not in b for b in bullets)
    # sentinel never leaks
    assert all("%%ec:" not in b for b in bullets)


def test_article_with_no_observed_points_is_dropped(tmp_path):
    """An article whose only key points are inferred/untagged contributes nothing."""
    concepts = tmp_path / "concepts"
    concepts.mkdir(parents=True)
    _write_article(
        concepts, "benched", title="Benched Guide", resource="get_flight_status",
        key_points=[
            "Only an inferred claim here [1] %%ec:inferred%%",
            "And an untagged one [1]",
        ],
    )
    wiki = WikiOps(tmp_path)
    guardrails, articles = collect(wiki, wiki.list_slugs())
    assert guardrails == []
    assert articles == []

    # And appending such a wiki leaves the policy unchanged.
    out = append_wiki_into_policy(POLICY, tmp_path)
    assert out == POLICY


def test_empty_wiki_returns_policy_unchanged(tmp_path):
    (tmp_path / "concepts").mkdir(parents=True)
    out = append_wiki_into_policy(POLICY, tmp_path)
    assert out == POLICY
