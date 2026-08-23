"""One pass of enrichment over the Vault.

Incremental by construction: a Capture whose Note is present and current is
skipped, so a run over an unchanged Vault writes nothing at all (ADR-0010).
"""

from dataclasses import dataclass

from pipeline.domain.clock import Clock
from pipeline.domain.document import Document
from pipeline.domain.enrichment import derive, has_drifted, is_stale
from pipeline.domain.identity import CaptureId
from pipeline.domain.language import LanguageModel
from pipeline.domain.vault import Vault

MESSAGE = "chore: enrich captures"


@dataclass(frozen=True)
class Report:
    """What a run did, for the operator and for log.md (ADR-0019)."""

    derived: tuple[CaptureId, ...] = ()
    drifted: tuple[CaptureId, ...] = ()
    unchanged: int = 0
    committed: bool = False

    def __str__(self) -> str:
        parts = [f"{len(self.derived)} derived", f"{self.unchanged} unchanged"]
        if self.drifted:
            parts.append(f"{len(self.drifted)} edited by hand and left alone")
        return ", ".join(parts)


def enrich(vault: Vault, model: LanguageModel, clock: Clock) -> Report:
    """Derive a Note for every Capture that needs one, and commit them together."""
    derived: dict[CaptureId, Document] = {}
    drifted: list[CaptureId] = []
    unchanged = 0

    for identity in vault.captures():
        capture = vault.read_capture(identity)
        note = vault.read_note(identity)
        if note is not None and has_drifted(note):
            # The pipeline owns this file, but the user has edited it. Refusing is
            # the whole point: overwriting would destroy work silently (ADR-0003).
            drifted.append(identity)
        elif note is None or is_stale(note, capture, model.version):
            derived[identity] = derive(capture, model, clock)
        else:
            unchanged += 1

    committed = vault.write_notes(derived, MESSAGE)
    return Report(tuple(derived), tuple(drifted), unchanged, committed)
