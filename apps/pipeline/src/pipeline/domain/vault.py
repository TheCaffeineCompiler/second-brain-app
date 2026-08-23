"""The Vault port.

The domain addresses artifacts by identity, never by path — only the adapter knows
a Topic becomes `topics/llm.md` (ADR-0016). That is what keeps renaming cheap.
"""

from typing import Protocol

from pipeline.domain.document import Document
from pipeline.domain.identity import CaptureId


class Vault(Protocol):
    """Read access to the Captures held in the Vault."""

    def captures(self) -> list[CaptureId]:
        """Every Capture in the Vault, in identity order."""
        ...

    def read_capture(self, capture: CaptureId) -> Document:
        """The Capture with this identity."""
        ...
