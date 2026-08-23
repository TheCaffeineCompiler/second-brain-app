"""The Vault port.

The domain addresses artifacts by identity, never by path — only the adapter knows
a Topic becomes `topics/llm.md` (ADR-0016). That is what keeps renaming cheap.
"""

from collections.abc import Mapping
from typing import Protocol

from pipeline.domain.document import Document
from pipeline.domain.identity import CaptureId

# Most artifacts are Documents. A few are plain text: OKF reserves log.md and
# index.md and exempts them from the frontmatter rule (ADR-0015).
type Artifact = Document | str


class Vault(Protocol):
    """Access to the artifacts held in the Vault, addressed by name."""

    def captures(self) -> list[CaptureId]:
        """Every Capture in the Vault, in identity order."""
        ...

    def read_capture(self, capture: CaptureId) -> Document:
        """The Capture with this identity."""
        ...

    def has(self, name: str) -> bool:
        """Whether this artifact already exists."""
        ...

    def write(self, artifacts: Mapping[str, Artifact], message: str) -> bool:
        """Commit these artifacts as one revision. False when there was nothing to do."""
        ...
