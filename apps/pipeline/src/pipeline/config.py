"""Configuration comes from the environment, never from code (12-factor).

The Vault's location is configuration precisely because this repository and the
Vault are independent (ADR-0023).
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import find_dotenv, load_dotenv


@dataclass(frozen=True)
class Config:
    vault_remote: str
    working_copy: Path

    @classmethod
    def from_environment(cls) -> "Config":
        """Read configuration, resolving relative paths against the project root.

        A local `.env` supplies development defaults; real environment variables
        always win, so deployment sets no file at all. Relative paths are resolved
        against the directory holding that file rather than the current one, so the
        command works from anywhere in the repository.
        """
        env_file = find_dotenv(usecwd=True)
        load_dotenv(env_file)
        root = Path(env_file).parent if env_file else Path.cwd()

        remote = os.environ.get("VAULT_REMOTE")
        if not remote:
            raise SystemExit(
                "VAULT_REMOTE is not set — it names the Vault repository.\n\n"
                "  For local development it comes from .env in the project root, so run\n"
                "  this from inside the repository after `docker compose up`.\n\n"
                "  Otherwise set it explicitly:\n"
                "    export VAULT_REMOTE=git@github.com:<owner>/second-brain-vault.git"
            )
        return cls(
            vault_remote=str(_resolve(remote, root)) if _is_path(remote) else remote,
            working_copy=_resolve(os.environ.get("VAULT_WORKING_COPY", "vault"), root),
        )


def _is_path(remote: str) -> bool:
    """A filesystem remote, as opposed to an ssh or https URL."""
    return "://" not in remote and not remote.startswith("git@")


def _resolve(value: str, root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path
