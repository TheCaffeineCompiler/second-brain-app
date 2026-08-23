"""A markdown document as the domain sees it: typed frontmatter plus an opaque body.

The domain owns the frontmatter contract; the adapter owns the file (ADR-0016).
Keys the domain does not know about are carried through untouched, because OKF
requires consumers to preserve unknown keys when round-tripping (ADR-0015).
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    """Frontmatter and body of one markdown file."""

    type: str
    body: str
    frontmatter: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.type:
            raise ValueError("OKF requires a non-empty type")

    def get(self, key: str) -> Any:
        """Read a frontmatter field, including one the domain does not model."""
        return self.frontmatter.get(key)

    def with_fields(self, **fields: Any) -> "Document":
        """Return a copy with frontmatter fields added or replaced."""
        return Document(
            type=self.type,
            body=self.body,
            frontmatter={**self.frontmatter, **fields},
        )
