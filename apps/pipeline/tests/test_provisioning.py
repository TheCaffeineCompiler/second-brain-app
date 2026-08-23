import subprocess
from pathlib import Path

from pipeline.adapters.git_vault import GitVault
from pipeline.domain import provisioning
from tests.conftest import Seed


def test_seeds_every_decided_artifact_into_an_empty_vault(
    vault_remote: Seed, tmp_path: Path
) -> None:
    vault = GitVault.clone(vault_remote({}), tmp_path / "work")
    written = provisioning.initialise(vault)
    assert set(written) == {"registry", "readme", "log", "captures"}
    assert (tmp_path / "work" / "registry.md").exists()
    assert (tmp_path / "work" / "captures").is_dir()


def test_seeding_twice_writes_nothing_the_second_time(vault_remote: Seed, tmp_path: Path) -> None:
    vault = GitVault.clone(vault_remote({}), tmp_path / "work")
    provisioning.initialise(vault)
    assert provisioning.initialise(vault) == {}


def test_seeding_never_overwrites_an_existing_artifact(vault_remote: Seed, tmp_path: Path) -> None:
    """The property the whole decision rests on: decided artifacts are irreplaceable."""
    vault = GitVault.clone(vault_remote({}), tmp_path / "work")
    provisioning.initialise(vault)

    registry = tmp_path / "work" / "registry.md"
    registry.write_text("---\ntype: registry\n---\n\nAcme — my most important client\n")
    vault.write({}, "noop")

    provisioning.initialise(vault)
    assert "my most important client" in registry.read_text()


def test_seeding_fills_only_what_is_absent(vault_remote: Seed, tmp_path: Path) -> None:
    vault = GitVault.clone(vault_remote({}), tmp_path / "work")
    provisioning.initialise(vault)
    (tmp_path / "work" / "README.md").unlink()

    assert set(provisioning.initialise(vault)) == {"readme"}


def test_seeding_leaves_a_single_commit(vault_remote: Seed, tmp_path: Path) -> None:
    """One commit per run, not one per file."""
    remote = vault_remote({})
    vault = GitVault.clone(remote, tmp_path / "work")
    provisioning.initialise(vault)

    GitVault.clone(remote, tmp_path / "verify")
    count = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=tmp_path / "verify",
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert count == "2", "seed commit plus the fixture's own initial commit"
