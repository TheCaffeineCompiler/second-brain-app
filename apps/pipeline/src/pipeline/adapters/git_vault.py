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
NOTES = "notes"

# The pipeline is a distinct writer from the user (ADR-0011), so it commits under
# its own identity. Passed explicitly rather than read from git config: a Cloud Run
# Job has no ambient identity, and depending on the machine's would make commit
# authorship vary with where the pipeline happened to run.
AUTHOR = ("Second Brain pipeline", "pipeline@second-brain.local")

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
            # A dirty working copy is normal, not an error: the user edits the Vault
            # in Obsidian. Rebasing would refuse, so skip it and let drift detection
            # do its job — otherwise the guard can never fire (ADR-0003).
            if not _git_output(into, "status", "--porcelain"):
                _git(into, "pull", "--rebase", "--quiet")
        else:
            into.parent.mkdir(parents=True, exist_ok=True)
            _git(into.parent, "clone", "--quiet", remote, str(into))
        return cls(into)

    def captures(self) -> list[CaptureId]:
        return _identities(self._root / CAPTURES)

    def read_capture(self, capture: CaptureId) -> Document:
        return markdown.parse(self._path_of(capture).read_text(encoding="utf-8"))

    def notes(self) -> list[CaptureId]:
        return _identities(self._root / NOTES)

    def read_note(self, capture: CaptureId) -> Document | None:
        path = self._root / NOTES / f"{capture}.md"
        if not path.exists():
            return None
        return markdown.parse(path.read_text(encoding="utf-8"))

    def write_notes(self, notes: Mapping[CaptureId, Document], message: str) -> bool:
        if not notes:
            return False
        directory = self._root / NOTES
        directory.mkdir(parents=True, exist_ok=True)
        written = []
        for capture, note in notes.items():
            (directory / f"{capture}.md").write_text(markdown.render(note), encoding="utf-8")
            written.append(f"{NOTES}/{capture}.md")
        return self._commit(message, written)

    def has(self, name: str) -> bool:
        return (self._root / PATHS[name]).exists()

    def write(self, artifacts: Mapping[str, Artifact], message: str) -> bool:
        """Commit the artifacts as a single revision, then push.

        One commit per run rather than per file, and nothing is committed when
        nothing changed — so a run over an unchanged Vault leaves no trace.
        """
        if not artifacts:
            return False
        written = []
        for name, artifact in artifacts.items():
            path = self._root / PATHS[name]
            path.parent.mkdir(parents=True, exist_ok=True)
            text = markdown.render(artifact) if isinstance(artifact, Document) else artifact
            path.write_text(text, encoding="utf-8")
            written.append(PATHS[name])

        return self._commit(message, written)

    def _commit(self, message: str, paths: list[str]) -> bool:
        """Commit only what the pipeline wrote.

        Never `add -A`: the working copy may hold the user's own edits, and
        committing those under the pipeline's identity would misattribute them
        and quietly absorb work the pipeline is supposed to refuse to touch.
        """
        _git(self._root, "add", "--", *paths)
        if not _git_output(self._root, "diff", "--cached", "--name-only"):
            return False
        name, email = AUTHOR
        _git(
            self._root,
            "-c",
            f"user.name={name}",
            "-c",
            f"user.email={email}",
            "commit",
            "--quiet",
            "-m",
            message,
        )
        _git(self._root, "push", "--quiet", "origin", "HEAD")
        return True

    def _path_of(self, capture: CaptureId) -> Path:
        return self._root / CAPTURES / f"{capture}.md"


def _identities(directory: Path) -> list[CaptureId]:
    if not directory.is_dir():
        return []
    return sorted(CaptureId(path.stem) for path in directory.glob("*.md"))


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
