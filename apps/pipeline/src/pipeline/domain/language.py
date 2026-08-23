"""The LanguageModel port.

The domain states what it wants from a model; prompts, schemas and API shapes
belong to the adapter (ADR-0016).
"""

from dataclasses import dataclass
from typing import Protocol

from pipeline.domain.document import Document
from pipeline.domain.kind import Kind


@dataclass(frozen=True)
class Enrichment:
    """What the model made of a Capture."""

    kind: Kind
    title: str
    body: str

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("an enrichment needs a title")
        if not self.body.strip():
            raise ValueError("an enrichment needs a body")


class LanguageModel(Protocol):
    """Derives an Enrichment from a Capture."""

    @property
    def version(self) -> str:
        """Identifies the model and prompt.

        Part of the pipeline version, so changing either marks the corpus stale
        (ADR-0003, ADR-0010). It belongs to the port because the prompt is as much
        a part of the derivation as the code is.
        """
        ...

    def enrich(self, capture: Document) -> Enrichment:
        """Clean up a Capture into a readable Note."""
        ...
