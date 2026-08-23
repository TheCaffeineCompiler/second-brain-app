import pytest

from pipeline.adapters.markdown import parse, render

CAPTURE = """---
type: capture
kind: podcast
source: https://example.com/ep/142
---

Rambling thought about sleep latency.
"""


def test_parses_frontmatter_and_body() -> None:
    document = parse(CAPTURE)
    assert document.type == "capture"
    assert document.get("kind") == "podcast"
    assert document.body == "Rambling thought about sleep latency."


def test_preserves_keys_the_domain_does_not_model() -> None:
    """OKF requires unknown keys to survive a round trip (ADR-0015)."""
    text = parse(CAPTURE).with_fields(kind="article")
    assert "https://example.com/ep/142" in render(text)


def test_round_trip_is_byte_identical() -> None:
    """Unchanged documents must not produce diffs (ADR-0010)."""
    assert render(parse(CAPTURE)) == CAPTURE


def test_rejects_a_document_without_a_type() -> None:
    with pytest.raises(ValueError, match="non-empty type"):
        parse("---\nkind: podcast\n---\n\nbody\n")


def test_reads_a_file_with_no_frontmatter_as_bodyless_type() -> None:
    with pytest.raises(ValueError, match="non-empty type"):
        parse("just a body\n")
