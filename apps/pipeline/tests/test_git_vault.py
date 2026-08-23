import shutil
from pathlib import Path

import pytest

from pipeline.adapters.git_vault import GitError, GitVault
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


def test_realigns_origin_when_the_remote_moves(vault_remote: Seed, tmp_path: Path) -> None:
    """A working copy cloned in a container is reused from the host, where the
    container's remote path does not exist."""
    remote = vault_remote({"2026-08-23T1714": SEED_CAPTURE})
    working_copy = tmp_path / "work"
    GitVault.clone(remote, working_copy)

    moved = tmp_path / "moved.git"
    shutil.move(remote, moved)

    vault = GitVault.clone(str(moved), working_copy)
    assert vault.captures() == [CaptureId("2026-08-23T1714")]


def test_a_git_failure_reports_what_git_said(tmp_path: Path) -> None:
    with pytest.raises(GitError, match="does-not-exist"):
        GitVault.clone(str(tmp_path / "does-not-exist.git"), tmp_path / "work")
