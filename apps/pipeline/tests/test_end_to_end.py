"""End-to-end tests for the path a person actually takes.

These exist because running the CLI on the host after `docker compose up` failed
in three separate ways at once: the Vault had no host-reachable path, the working
copy's origin pointed at a path that existed only inside the container, and every
git failure arrived with its diagnostic discarded.
"""

import os
import subprocess
import sys
from pathlib import Path

import coverage

from tests.conftest import SEED_CAPTURE, Seed

DOTENV = """VAULT_REMOTE=.vault-remote/vault.git
VAULT_WORKING_COPY=.working-copy/vault
"""


def run_cli(*arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI the way a person does — a fresh process with no Vault config.

    Only the VAULT_ variables are stripped. Clearing the whole environment would
    also strip coverage's subprocess hooks, making these tests look like they
    exercise nothing.
    """
    environment = {key: value for key, value in os.environ.items() if not key.startswith("VAULT_")}
    environment.update(_coverage_env())
    return subprocess.run(
        [sys.executable, "-c", "from pipeline.cli import main; main()", *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=environment,
    )


def _coverage_env() -> dict[str, str]:
    """Let the subprocess join the coverage run.

    Without this, coverage's startup hook stays dormant in the child and the five
    tests below appear to exercise nothing — which would invite someone to replace
    them with weaker in-process tests to move the number.
    """
    if coverage.Coverage.current() is None:
        return {}
    project_root = Path(__file__).resolve().parents[1]
    return {
        "COVERAGE_PROCESS_START": str(project_root / "pyproject.toml"),
        # These subprocesses run in a temporary directory, and coverage writes its
        # data file relative to the current one — so without an absolute path the
        # results are written into the temp directory and thrown away.
        "COVERAGE_FILE": str(project_root / ".coverage"),
    }


def project(tmp_path: Path, remote: str) -> Path:
    """A project root holding a .env, with the Vault where .env says it is."""
    root = tmp_path / "project"
    (root / "apps" / "pipeline").mkdir(parents=True)
    (root / ".env").write_text(DOTENV, encoding="utf-8")
    Path(root / ".vault-remote").symlink_to(Path(remote).parent)
    return root


def test_the_cli_reads_captures_with_nothing_exported(vault_remote: Seed, tmp_path: Path) -> None:
    """The reported failure: `pipeline list` on the host after docker compose."""
    root = project(tmp_path, vault_remote({"2026-08-23T1714": SEED_CAPTURE}))
    result = run_cli("list", cwd=root)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["2026-08-23T1714"]


def test_the_cli_works_from_a_subdirectory(vault_remote: Seed, tmp_path: Path) -> None:
    """Relative paths resolve against the .env, not the current directory."""
    root = project(tmp_path, vault_remote({"2026-08-23T1714": SEED_CAPTURE}))
    result = run_cli("list", cwd=root / "apps" / "pipeline")
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["2026-08-23T1714"]


def test_a_working_copy_moves_between_container_and_host(
    vault_remote: Seed, tmp_path: Path
) -> None:
    """A working copy cloned in the container is then opened from the host, where
    the container's remote path does not exist."""
    root = project(tmp_path, vault_remote({"2026-08-23T1714": SEED_CAPTURE}))
    assert run_cli("list", cwd=root).returncode == 0

    subprocess.run(
        ["git", "remote", "set-url", "origin", "/srv/vault.git"],
        cwd=root / ".working-copy" / "vault",
        check=True,
        capture_output=True,
    )
    result = run_cli("list", cwd=root)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["2026-08-23T1714"]


def test_the_cli_prints_a_captures_content(vault_remote: Seed, tmp_path: Path) -> None:
    root = project(tmp_path, vault_remote({"2026-08-23T1714": SEED_CAPTURE}))
    result = run_cli("show", "2026-08-23T1714", cwd=root)
    assert result.returncode == 0, result.stderr
    assert "kind: podcast" in result.stdout
    assert "cold exposure" in result.stdout


def test_an_unreachable_vault_reports_what_git_said(tmp_path: Path) -> None:
    """A failure must never arrive as a bare CalledProcessError."""
    root = tmp_path / "project"
    root.mkdir()
    (root / ".env").write_text(DOTENV, encoding="utf-8")
    result = run_cli("list", cwd=root)
    assert result.returncode != 0
    assert "git clone" in result.stderr
    assert "vault.git" in result.stderr


def test_missing_configuration_says_what_to_do(tmp_path: Path) -> None:
    result = run_cli("list", cwd=tmp_path)
    assert result.returncode != 0
    assert "VAULT_REMOTE is not set" in result.stderr
    assert ".env" in result.stderr
