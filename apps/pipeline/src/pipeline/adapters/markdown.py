"""Serialises a Document to and from OKF markdown.

Serialisation is deterministic: key order is preserved rather than sorted, so an
unchanged Document produces byte-identical output across runs (ADR-0010).
"""

from typing import Any

import yaml

from pipeline.domain.document import Document

_FENCE = "---"


def parse(text: str) -> Document:
    """Parse OKF markdown into a Document, preserving unknown frontmatter keys."""
    frontmatter, body = _split(text)
    loaded: dict[str, Any] = yaml.safe_load(frontmatter) or {} if frontmatter else {}
    type_ = loaded.pop("type", "")
    return Document(type=type_, body=body, frontmatter=loaded)


def render(document: Document) -> str:
    """Render a Document as OKF markdown."""
    fields: dict[str, Any] = {"type": document.type, **document.frontmatter}
    frontmatter = yaml.safe_dump(fields, sort_keys=False, allow_unicode=True).rstrip("\n")
    return f"{_FENCE}\n{frontmatter}\n{_FENCE}\n\n{document.body.strip()}\n"


def _split(text: str) -> tuple[str, str]:
    if not text.startswith(_FENCE):
        return "", text.strip()
    _, _, rest = text.partition(f"{_FENCE}\n")
    frontmatter, fence, body = rest.partition(f"\n{_FENCE}")
    if not fence:
        raise ValueError("unterminated frontmatter block")
    return frontmatter, body.strip()
