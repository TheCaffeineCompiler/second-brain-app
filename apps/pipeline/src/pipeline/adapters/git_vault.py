"""Git-backed implementation of the Vault port.

Git is the system of record (ADR-0001). This adapter owns paths and the file
format; the domain sees only identities and Documents (ADR-0016).
"""

import subprocess
from pathlib import Path

from pipeline.adapters import markdown
from pipeline.domain.document import Document
from pipeline.domain.identity import CaptureId

CAPTURES = "captures"


class GitVault:
    """A working copy of the Vault repository."""

    def __init__(self, working_copy: Path) -> None:
        self._root = working_copy

    @classmethod
    def clone(cls, remote: str, into: Path) -> "GitVault":
        """Clone the Vault, or refresh an existing working copy."""
        if (into / ".git").exists():
            _git(into, "pull", "--rebase", "--quiet")
        else:
            into.parent.mkdir(parents=True, exist_ok=True)
            _git(into.parent, "clone", "--quiet", remote, str(into))
        return cls(into)

    def captures(self) -> list[CaptureId]:
        directory = self._root / CAPTURES
        if not directory.is_dir():
            return []
        return sorted(CaptureId(path.stem) for path in directory.glob("*.md"))

    def read_capture(self, capture: CaptureId) -> Document:
        return markdown.parse(self._path_of(capture).read_text(encoding="utf-8"))

    def _path_of(self, capture: CaptureId) -> Path:
        return self._root / CAPTURES / f"{capture}.md"


def _git(cwd: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=cwd, check=True, capture_output=True)
