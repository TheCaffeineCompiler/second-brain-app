"""Configuration comes from the environment, never from code (12-factor).

The Vault's location is configuration precisely because this repository and the
Vault are independent (ADR-0023).
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

UNSET = """VAULT_REMOTE is not set — it names the Vault repository.

  For local development it comes from .env in the project root, so run this from
  inside the repository after `docker compose up`.

  Otherwise set it explicitly, or run `pipeline init <owner>/<name>` to create it:
    export VAULT_REMOTE=https://github.com/<owner>/second-brain-vault.git"""


@dataclass(frozen=True)
class Config:
    vault_remote: str
    working_copy: Path

    @classmethod
    def from_environment(cls) -> "Config":
        root = project_root()
        remote = os.environ.get("VAULT_REMOTE")
        if not remote:
            raise SystemExit(UNSET)
        return cls(
            vault_remote=str(_resolve(remote, root)) if _is_path(remote) else remote,
            working_copy=working_copy(),
        )


def project_root() -> Path:
    """Where relative configuration is anchored.

    A local .env supplies development defaults; real environment variables always
    win, so deployment sets no file at all. Relative paths resolve against the
    directory holding that file rather than the current one, so the command works
    from anywhere in the repository.
    """
    env_file = find_dotenv(usecwd=True)
    load_dotenv(env_file)
    return Path(env_file).parent if env_file else Path.cwd()


def working_copy() -> Path:
    """Where the Vault is checked out. Needed before a remote is known, by `init`."""
    return _resolve(os.environ.get("VAULT_WORKING_COPY", "vault"), project_root())


def _is_path(remote: str) -> bool:
    """A filesystem remote, as opposed to an ssh or https URL."""
    return "://" not in remote and not remote.startswith("git@")


def _resolve(value: str, root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path
