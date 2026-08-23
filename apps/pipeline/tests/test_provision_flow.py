from collections.abc import Callable
from pathlib import Path

import pytest

from pipeline.adapters.git_vault import GitVault
from pipeline.domain.host import ProtectionUnavailable
from pipeline.domain.provisioning import provision
from pipeline.domain.vault import Vault
from tests.conftest import Seed


class FakeHost:
    """A VaultHost backed by a bare repository rather than GitHub."""

    def __init__(self, url: str, *, already_there: bool = False, protectable: bool = True) -> None:
        self.url = url
        self.already_there = already_there
        self.protectable = protectable
        self.created: list[str] = []
        self.protected: list[tuple[str, str]] = []

    def exists(self, repository: str) -> bool:
        return self.already_there

    def create_private(self, repository: str) -> None:
        self.created.append(repository)

    def protect(self, repository: str, branch: str) -> None:
        if not self.protectable:
            raise ProtectionUnavailable("upgrade required")
        self.protected.append((repository, branch))

    def clone_url(self, repository: str) -> str:
        return self.url


def opener(into: Path) -> Callable[[str], Vault]:
    def open_vault(remote: str) -> Vault:
        return GitVault.clone(remote, into)

    return open_vault


def test_creates_protects_and_seeds_a_new_vault(vault_remote: Seed, tmp_path: Path) -> None:
    host = FakeHost(vault_remote({}))
    result = provision(host, "owner/vault", "main", opener(tmp_path / "work"))

    assert result.created and result.protected
    assert result.seeded == ("captures", "log", "readme", "registry")
    assert host.created == ["owner/vault"]
    assert host.protected == [("owner/vault", "main")]


def test_leaves_an_existing_repository_alone(vault_remote: Seed, tmp_path: Path) -> None:
    host = FakeHost(vault_remote({}), already_there=True)
    result = provision(host, "owner/vault", "main", opener(tmp_path / "work"))

    assert not result.created
    assert host.created == []


def test_running_twice_seeds_nothing_the_second_time(vault_remote: Seed, tmp_path: Path) -> None:
    """Initialisation is safe to repeat and never destructive (ADR-0023)."""
    host = FakeHost(vault_remote({}), already_there=True)
    provision(host, "owner/vault", "main", opener(tmp_path / "work"))
    again = provision(host, "owner/vault", "main", opener(tmp_path / "work"))

    assert again.seeded == ()


def test_reports_when_protection_could_not_be_applied(vault_remote: Seed, tmp_path: Path) -> None:
    """Not fatal, but the operator must be told — protection is the only guard
    against unrecoverable loss of decided artifacts (ADR-0019)."""
    host = FakeHost(vault_remote({}), protectable=False)
    result = provision(host, "owner/vault", "main", opener(tmp_path / "work"))

    assert not result.protected
    assert result.unprotected_because == "upgrade required"
    assert result.seeded, "seeding still proceeds"


def test_protection_failure_is_the_only_one_tolerated(vault_remote: Seed, tmp_path: Path) -> None:
    class Broken(FakeHost):
        def create_private(self, repository: str) -> None:
            raise RuntimeError("name already taken")

    host = Broken(vault_remote({}))
    with pytest.raises(RuntimeError, match="name already taken"):
        provision(host, "owner/vault", "main", opener(tmp_path / "work"))
