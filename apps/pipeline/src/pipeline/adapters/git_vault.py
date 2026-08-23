"""Git-backed implementation of the Vault port.

Git is the system of record (ADR-0001). This adapter owns paths and the file
format; the domain sees only identities and Documents (ADR-0016).
"""

import subprocess
from collections.abc import Mapping
from pathlib import Path

from pipeline.adapters import markdown
from pipeline.domain.document import Document
from pipeline.domain.identity import CaptureId
from pipeline.domain.vault import Artifact

CAPTURES = "captures"

# The adapter owns paths; the domain names artifacts (ADR-0016).
PATHS = {
    "registry": "registry.md",
    "readme": "README.md",
    "log": "log.md",
    "captures": f"{CAPTURES}/.gitkeep",
}


class GitError(RuntimeError):
    """A git command failed, carrying git's own diagnostic."""


class GitVault:
    """A working copy of the Vault repository."""

    def __init__(self, working_copy: Path) -> None:
        self._root = working_copy

    @classmethod
    def clone(cls, remote: str, into: Path) -> "GitVault":
        """Clone the Vault, or refresh an existing working copy.

        The configured remote is authoritative. A working copy can legitimately
        outlive a change of remote — the compose stack clones it at a container
        path, then the same directory is used from the host — so origin is
        realigned rather than assumed correct.
        """
        if (into / ".git").exists():
            _git(into, "remote", "set-url", "origin", remote)
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

    def has(self, name: str) -> bool:
        return (self._root / PATHS[name]).exists()

    def write(self, artifacts: Mapping[str, Artifact], message: str) -> bool:
        """Commit the artifacts as a single revision, then push.

        One commit per run rather than per file, and nothing is committed when
        nothing changed — so a run over an unchanged Vault leaves no trace.
        """
        if not artifacts:
            return False
        for name, artifact in artifacts.items():
            path = self._root / PATHS[name]
            path.parent.mkdir(parents=True, exist_ok=True)
            text = markdown.render(artifact) if isinstance(artifact, Document) else artifact
            path.write_text(text, encoding="utf-8")

        _git(self._root, "add", "-A")
        if not _git_output(self._root, "status", "--porcelain"):
            return False
        _git(self._root, "commit", "--quiet", "-m", message)
        _git(self._root, "push", "--quiet", "origin", "HEAD")
        return True

    def _path_of(self, capture: CaptureId) -> Path:
        return self._root / CAPTURES / f"{capture}.md"


def _git_output(cwd: Path, *arguments: str) -> str:
    result = subprocess.run(["git", *arguments], cwd=cwd, capture_output=True, text=True)
    return result.stdout.strip()


def _git(cwd: Path, *arguments: str) -> None:
    """Run git, surfacing its stderr on failure.

    Without this, every git failure arrives as a bare CalledProcessError with the
    diagnostic thrown away.
    """
    result = subprocess.run(["git", *arguments], cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        command = " ".join(("git", *arguments))
        raise GitError(f"{command} failed in {cwd}:\n{result.stderr.strip()}")
