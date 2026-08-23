"""What sort of Capture a Note came from.

A closed set the pipeline may select from but never extend (ADR-0006). Kind is
determined independently of the Source; disagreement between them is what flags
missing provenance (ADR-0009).
"""

from enum import StrEnum


class Kind(StrEnum):
    PODCAST = "podcast"
    ARTICLE = "article"
    MEETING = "meeting"
    THOUGHT = "thought"

    @property
    def implies_external_source(self) -> bool:
        """Whether a Capture of this Kind should cite something outside itself."""
        return self in (Kind.PODCAST, Kind.ARTICLE)
