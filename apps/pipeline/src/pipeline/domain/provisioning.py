"""Preparing a Vault for use.

Initialisation is not destructive (ADR-0023). Seeding over an existing Vault would
destroy decided artifacts, which are irreplaceable (ADR-0011) — the same
unrecoverable failure as a force-push, under a friendlier name. Only artifacts that
are genuinely absent are written.
"""

from collections.abc import Callable
from dataclasses import dataclass

from pipeline.domain import skeleton
from pipeline.domain.host import ProtectionUnavailable, VaultHost
from pipeline.domain.vault import Artifact, Vault

MESSAGE = "chore: seed the vault skeleton"


@dataclass(frozen=True)
class Provisioned:
    """What provisioning actually did, so the operator can see it."""

    created: bool
    protected: bool
    seeded: tuple[str, ...]
    unprotected_because: str | None = None


def missing(vault: Vault) -> dict[str, Artifact]:
    """The skeleton artifacts this Vault does not already have."""
    expected: dict[str, Artifact] = {**skeleton.DECIDED, "log": skeleton.LOG, "captures": ""}
    return {name: artifact for name, artifact in expected.items() if not vault.has(name)}


def initialise(vault: Vault) -> dict[str, Artifact]:
    """Seed whatever is absent. Returns what was written, empty if nothing was."""
    absent = missing(vault)
    if absent:
        vault.write(absent, MESSAGE)
    return absent


def provision(
    host: VaultHost,
    repository: str,
    branch: str,
    open_vault: Callable[[str], Vault],
) -> Provisioned:
    """Create the Vault repository if absent, protect it, and seed what is missing.

    Every step is safe to repeat: an existing repository is left alone, protection is
    re-applied harmlessly, and seeding only fills gaps. Running this twice is not an
    error, and must never be destructive (ADR-0023).
    """
    created = not host.exists(repository)
    if created:
        host.create_private(repository)

    protected, reason = True, None
    try:
        host.protect(repository, branch)
    except ProtectionUnavailable as unavailable:
        protected, reason = False, str(unavailable)

    seeded = initialise(open_vault(host.clone_url(repository)))
    return Provisioned(created, protected, tuple(sorted(seeded)), reason)
