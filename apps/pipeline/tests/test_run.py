from datetime import UTC, datetime
from pathlib import Path

from pipeline.adapters.git_vault import GitVault
from pipeline.adapters.stub_language import StubLanguageModel
from pipeline.domain.clock import FixedClock
from pipeline.domain.identity import CaptureId
from pipeline.domain.run import enrich
from tests.conftest import SEED_CAPTURE, Seed

CLOCK = FixedClock(datetime(2026, 8, 23, 3, 14, tzinfo=UTC))
ID = "2026-08-23T1714"


def vault_with(vault_remote: Seed, tmp_path: Path, **captures: str) -> GitVault:
    return GitVault.clone(vault_remote(captures or {ID: SEED_CAPTURE}), tmp_path / "work")


def test_derives_a_note_for_every_capture(vault_remote: Seed, tmp_path: Path) -> None:
    vault = vault_with(vault_remote, tmp_path)
    report = enrich(vault, StubLanguageModel(), CLOCK)

    assert report.derived == (CaptureId(ID),)
    assert report.committed
    note = vault.read_note(CaptureId(ID))
    assert note is not None and note.type == "note"


def test_a_second_run_writes_nothing_at_all(vault_remote: Seed, tmp_path: Path) -> None:
    """The property every later slice depends on (ADR-0010)."""
    vault = vault_with(vault_remote, tmp_path)
    enrich(vault, StubLanguageModel(), CLOCK)

    report = enrich(vault, StubLanguageModel(), CLOCK)
    assert report.derived == ()
    assert report.unchanged == 1
    assert not report.committed


def test_a_new_pipeline_version_rederives_everything(vault_remote: Seed, tmp_path: Path) -> None:
    vault = vault_with(vault_remote, tmp_path)
    enrich(vault, StubLanguageModel(), CLOCK)

    report = enrich(vault, StubLanguageModel("stub-2"), CLOCK)
    assert report.derived == (CaptureId(ID),)


def test_a_hand_edited_note_is_reported_and_left_alone(vault_remote: Seed, tmp_path: Path) -> None:
    vault = vault_with(vault_remote, tmp_path)
    enrich(vault, StubLanguageModel(), CLOCK)

    edited = tmp_path / "work" / "notes" / f"{ID}.md"
    edited.write_text(edited.read_text() + "\nA sentence I added myself.\n", encoding="utf-8")

    report = enrich(vault, StubLanguageModel(), CLOCK)
    assert report.drifted == (CaptureId(ID),)
    assert report.derived == ()
    assert "A sentence I added myself." in edited.read_text()


def test_drift_on_one_note_does_not_block_the_others(vault_remote: Seed, tmp_path: Path) -> None:
    other = "2026-08-21T0902"
    vault = vault_with(vault_remote, tmp_path, **{ID: SEED_CAPTURE, other: SEED_CAPTURE})
    enrich(vault, StubLanguageModel(), CLOCK)

    edited = tmp_path / "work" / "notes" / f"{ID}.md"
    edited.write_text(edited.read_text() + "\nmine\n", encoding="utf-8")

    report = enrich(vault, StubLanguageModel("stub-2"), CLOCK)
    assert report.drifted == (CaptureId(ID),)
    assert report.derived == (CaptureId(other),)


def test_the_pipeline_never_writes_to_a_capture(vault_remote: Seed, tmp_path: Path) -> None:
    """Only the user writes Captures (ADR-0002)."""
    vault = vault_with(vault_remote, tmp_path)
    before = (tmp_path / "work" / "captures" / f"{ID}.md").read_text()
    enrich(vault, StubLanguageModel(), CLOCK)
    assert (tmp_path / "work" / "captures" / f"{ID}.md").read_text() == before


def test_a_hand_edited_note_does_not_block_the_run(vault_remote: Seed, tmp_path: Path) -> None:
    """Opening the Vault must tolerate a dirty working copy — the user edits it in
    Obsidian, and refusing to open would make drift detection unreachable."""
    remote = vault_remote({ID: SEED_CAPTURE})
    enrich(GitVault.clone(remote, tmp_path / "work"), StubLanguageModel(), CLOCK)

    note = tmp_path / "work" / "notes" / f"{ID}.md"
    note.write_text(note.read_text() + "\nmine\n", encoding="utf-8")

    reopened = GitVault.clone(remote, tmp_path / "work")
    assert enrich(reopened, StubLanguageModel(), CLOCK).drifted == (CaptureId(ID),)


def test_the_pipeline_never_commits_the_users_edits(vault_remote: Seed, tmp_path: Path) -> None:
    """Committing a hand-edit under the pipeline's identity would misattribute it
    and absorb work the pipeline is supposed to refuse to touch (ADR-0002)."""
    import subprocess

    other = "2026-08-21T0902"
    remote = vault_remote({ID: SEED_CAPTURE, other: SEED_CAPTURE})
    work = tmp_path / "work"
    enrich(GitVault.clone(remote, work), StubLanguageModel(), CLOCK)

    edited = work / "notes" / f"{ID}.md"
    edited.write_text(edited.read_text() + "\nmine\n", encoding="utf-8")
    enrich(GitVault.clone(remote, work), StubLanguageModel("stub-2"), CLOCK)

    committed = subprocess.run(
        ["git", "show", "--name-only", "--format=", "HEAD"],
        cwd=work,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert committed == [f"notes/{other}.md"]
    assert "mine" in edited.read_text()
