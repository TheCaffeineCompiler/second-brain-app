from pathlib import Path

from pipeline.adapters.git_vault import GitVault
from pipeline.domain.identity import CaptureId
from tests.conftest import SEED_CAPTURE, Seed


def test_lists_captures_in_identity_order(vault_remote: Seed, tmp_path: Path) -> None:
    remote = vault_remote({"2026-08-23T1714": SEED_CAPTURE, "2026-08-21T0902": SEED_CAPTURE})
    vault = GitVault.clone(remote, tmp_path / "work")
    assert vault.captures() == [CaptureId("2026-08-21T0902"), CaptureId("2026-08-23T1714")]


def test_reads_a_capture_by_identity(vault_remote: Seed, tmp_path: Path) -> None:
    remote = vault_remote({"2026-08-23T1714": SEED_CAPTURE})
    vault = GitVault.clone(remote, tmp_path / "work")
    capture = vault.read_capture(CaptureId("2026-08-23T1714"))
    assert capture.type == "capture"
    assert capture.get("source") == "https://example.com/ep/142"
    assert "cold exposure" in capture.body


def test_cloning_twice_refreshes_rather_than_failing(vault_remote: Seed, tmp_path: Path) -> None:
    remote = vault_remote({"2026-08-23T1714": SEED_CAPTURE})
    GitVault.clone(remote, tmp_path / "work")
    vault = GitVault.clone(remote, tmp_path / "work")
    assert vault.captures() == [CaptureId("2026-08-23T1714")]


def test_an_empty_vault_has_no_captures(vault_remote: Seed, tmp_path: Path) -> None:
    vault = GitVault.clone(vault_remote({}), tmp_path / "work")
    assert vault.captures() == []
