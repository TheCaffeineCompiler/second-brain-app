"""The VaultHost port — creating and protecting the Vault's repository.

Kept separate from the Vault port because it needs a different credential.
Creating a repository and setting branch protection require far broader scopes
than committing to a known repository, and the nightly job must never hold
rights to create or delete repositories (ADR-0023).
"""

from typing import Protocol


class ProtectionUnavailable(RuntimeError):
    """Branch protection could not be applied.

    Not fatal — the Vault still works — but the operator must be told, because
    protection is what stands between a pipeline bug and unrecoverable loss of
    decided artifacts (ADR-0019).
    """


class VaultHost(Protocol):
    """Where the Vault repository lives."""

    def exists(self, repository: str) -> bool:
        """Whether the repository is already there."""
        ...

    def create_private(self, repository: str) -> None:
        """Create it, private. The Vault holds personal notes."""
        ...

    def protect(self, repository: str, branch: str) -> None:
        """Block force-push and deletion. Raises ProtectionUnavailable if refused."""
        ...

    def clone_url(self, repository: str) -> str:
        """The URL to clone it from."""
        ...
