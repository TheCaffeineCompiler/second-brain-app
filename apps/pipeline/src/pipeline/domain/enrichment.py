"""Deriving a Note from a Capture.

Staleness is a content hash plus the pipeline version, never a timestamp: a
timestamp records when work happened, not whether it needs doing again (ADR-0003).
"""

from hashlib import sha256

from pipeline.domain.clock import Clock
from pipeline.domain.document import Document
from pipeline.domain.language import LanguageModel

GENERATED_BY = "second-brain-pipeline"
SOURCE_HASH = "source_hash"
CONTENT_HASH = "content_hash"


def digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()[:16]


def derive(capture: Document, model: LanguageModel, clock: Clock) -> Document:
    """Turn a Capture into a Note, sealed with the hashes staleness depends on."""
    enrichment = model.enrich(capture)
    note = Document(
        type="note",
        body=enrichment.body,
        frontmatter={
            "title": enrichment.title,
            "kind": str(enrichment.kind),
            "generated": {"by": f"{GENERATED_BY}@{model.version}", "at": clock.now().isoformat()},
            SOURCE_HASH: digest(capture.fingerprint()),
        },
    )
    return seal(note)


def seal(note: Document) -> Document:
    """Stamp a Note with a hash of itself, so later edits are detectable."""
    return note.with_fields(**{CONTENT_HASH: digest(note.without(CONTENT_HASH).fingerprint())})


def has_drifted(note: Document) -> bool:
    """Whether a Note has been edited since the pipeline wrote it (ADR-0003)."""
    stamped = note.get(CONTENT_HASH)
    return str(stamped) != digest(note.without(CONTENT_HASH).fingerprint())


def is_stale(note: Document, capture: Document, version: str) -> bool:
    """Whether this Note needs deriving again.

    Stale when its Capture changed, or when the pipeline that produced it did.
    Never because time passed.
    """
    if note.get(SOURCE_HASH) != digest(capture.fingerprint()):
        return True
    generated = note.get("generated") or {}
    return str(generated.get("by", "")) != f"{GENERATED_BY}@{version}"
