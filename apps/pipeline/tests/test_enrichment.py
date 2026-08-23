from datetime import UTC, datetime

import pytest

from pipeline.adapters.stub_language import StubLanguageModel
from pipeline.domain.clock import FixedClock
from pipeline.domain.document import Document
from pipeline.domain.enrichment import derive, has_drifted, is_stale, seal
from pipeline.domain.kind import Kind
from pipeline.domain.language import Enrichment

CLOCK = FixedClock(datetime(2026, 8, 23, 3, 14, tzinfo=UTC))


def capture(body: str = "Sleep latency is the signal, not total hours.") -> Document:
    return Document(type="capture", body=body, frontmatter={"kind": "podcast"})


def test_a_note_carries_what_staleness_depends_on() -> None:
    note = derive(capture(), StubLanguageModel(), CLOCK)
    assert note.type == "note"
    assert note.get("kind") == Kind.PODCAST
    assert note.get("generated") == {
        "by": "second-brain-pipeline@stub-1",
        "at": "2026-08-23T03:14:00+00:00",
    }
    assert note.get("source_hash") and note.get("content_hash")


def test_deriving_twice_produces_an_identical_note() -> None:
    """Byte-identical output is what makes a replay safe (ADR-0010)."""
    first = derive(capture(), StubLanguageModel(), CLOCK)
    second = derive(capture(), StubLanguageModel(), CLOCK)
    assert first == second


def test_a_note_is_not_stale_when_nothing_changed() -> None:
    note = derive(capture(), StubLanguageModel(), CLOCK)
    assert not is_stale(note, capture(), "stub-1")


def test_an_edited_capture_makes_its_note_stale() -> None:
    note = derive(capture(), StubLanguageModel(), CLOCK)
    assert is_stale(note, capture("Corrected: it was Huberman, not Hooberman."), "stub-1")


def test_a_new_pipeline_version_makes_every_note_stale() -> None:
    """Changing the prompt invalidates the corpus — the prompt is part of the pipeline."""
    note = derive(capture(), StubLanguageModel(), CLOCK)
    assert is_stale(note, capture(), "stub-2")


def test_time_passing_never_makes_a_note_stale() -> None:
    """Staleness is a hash, not a timestamp (ADR-0003)."""
    note = derive(capture(), StubLanguageModel(), CLOCK)
    later = FixedClock(datetime(2027, 1, 1, tzinfo=UTC))
    assert not is_stale(note, capture(), "stub-1")
    rederived = derive(capture(), StubLanguageModel(), later)
    assert rederived.get("source_hash") == note.get("source_hash")


def test_an_untouched_note_has_not_drifted() -> None:
    assert not has_drifted(derive(capture(), StubLanguageModel(), CLOCK))


def test_a_hand_edited_note_has_drifted() -> None:
    """Nothing in Obsidian stops the user editing a Note; this is what catches it."""
    note = derive(capture(), StubLanguageModel(), CLOCK)
    assert has_drifted(Document(type="note", body="I rewrote this", frontmatter=note.frontmatter))


def test_editing_frontmatter_also_counts_as_drift() -> None:
    note = derive(capture(), StubLanguageModel(), CLOCK)
    assert has_drifted(note.with_fields(title="A title I preferred"))


def test_sealing_is_idempotent() -> None:
    note = derive(capture(), StubLanguageModel(), CLOCK)
    assert seal(note) == note


def test_an_enrichment_needs_a_title() -> None:
    with pytest.raises(ValueError, match="title"):
        Enrichment(kind=Kind.THOUGHT, title="  ", body="something")


def test_an_enrichment_needs_a_body() -> None:
    with pytest.raises(ValueError, match="body"):
        Enrichment(kind=Kind.THOUGHT, title="A title", body="  ")


def test_an_empty_capture_cannot_produce_a_note() -> None:
    with pytest.raises(ValueError, match="body"):
        StubLanguageModel().enrich(Document(type="capture", body="   \n  "))
