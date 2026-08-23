"""Configuration comes from the environment, never from code (12-factor).

The Vault's location is configuration precisely because this repository and the
Vault are independent (ADR-0023).
"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    vault_remote: str
    working_copy: Path

    @classmethod
    def from_environment(cls) -> "Config":
        remote = os.environ.get("VAULT_REMOTE")
        if not remote:
            raise SystemExit("VAULT_REMOTE is not set")
        return cls(
            vault_remote=remote,
            working_copy=Path(os.environ.get("VAULT_WORKING_COPY", "/tmp/vault")),
        )
