import re

from pipeline.domain import skeleton


def prose(text: str) -> str:
    """Collapse wrapping so assertions survive reflowed prose."""
    return re.sub(r"\s+", " ", text)


def test_seeds_the_registry_as_a_decided_artifact() -> None:
    assert skeleton.REGISTRY.type == "registry"
    assert "the pipeline reads it and never writes to it" in prose(skeleton.REGISTRY.body)


def test_seeds_no_derived_regions() -> None:
    """Derived regions appear when the pipeline first writes them (ADR-0011)."""
    assert set(skeleton.DECIDED) == {"registry", "readme"}


def test_the_readme_warns_against_editing_derived_artifacts() -> None:
    assert "Do not edit these by hand" in prose(skeleton.README.body)


def test_the_log_carries_no_frontmatter() -> None:
    """OKF reserves log.md and exempts it from the type requirement (ADR-0015)."""
    assert not skeleton.LOG.startswith("---")
