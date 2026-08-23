"""A LanguageModel that invents nothing, for tests.

Deterministic by construction — which matters because Claude Opus 5 removed
`temperature`, so there is no sampling knob to pin a real model with (ADR-0019).
"""

from pipeline.domain.document import Document
from pipeline.domain.kind import Kind
from pipeline.domain.language import Enrichment


class StubLanguageModel:
    def __init__(self, version: str = "stub-1") -> None:
        self._version = version

    @property
    def version(self) -> str:
        return self._version

    def enrich(self, capture: Document) -> Enrichment:
        kind = Kind(capture.get("kind") or Kind.THOUGHT)
        first = next((line for line in capture.body.splitlines() if line.strip()), "Untitled")
        return Enrichment(kind=kind, title=first.strip()[:60], body=capture.body)
