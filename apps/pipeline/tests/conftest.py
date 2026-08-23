import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

SEED_CAPTURE = """---
type: capture
kind: podcast
source: https://example.com/ep/142
---

Rambling thought about sleep latency and cold exposure.
"""

Seed = Callable[[dict[str, str]], str]


@pytest.fixture
def vault_remote(tmp_path: Path) -> Seed:
    """A bare repository standing in for GitHub, seeded with Captures."""

    def seed(captures: dict[str, str]) -> str:
        bare = tmp_path / "vault.git"
        staging = tmp_path / "staging"
        subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(bare)], check=True)
        subprocess.run(["git", "clone", "-q", str(bare), str(staging)], check=True)
        directory = staging / "captures"
        directory.mkdir()
        for name, text in captures.items():
            (directory / f"{name}.md").write_text(text, encoding="utf-8")
        for arguments in (
            ["add", "-A"],
            # --allow-empty so that seeding no Captures yields a genuinely empty
            # Vault with a commit, rather than one containing a placeholder file.
            ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "seed", "--allow-empty"],
            ["push", "-q", "origin", "main"],
        ):
            subprocess.run(["git", *arguments], cwd=staging, check=True)
        return str(bare)

    return seed
