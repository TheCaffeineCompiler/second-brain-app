"""Command line entry point."""

import argparse
from typing import cast

from pipeline import config as configuration
from pipeline.adapters.git_vault import GitVault
from pipeline.adapters.github_host import GitHubHost
from pipeline.domain.clock import SystemClock
from pipeline.domain.identity import CaptureId
from pipeline.domain.language import LanguageModel
from pipeline.domain.provisioning import Provisioned, provision
from pipeline.domain.run import enrich
from pipeline.domain.vault import Vault


def main() -> None:
    parser = argparse.ArgumentParser(prog="pipeline", description="Second Brain pipeline")
    commands = parser.add_subparsers(dest="command", required=True)

    initialise = commands.add_parser("init", help="create, protect and seed the Vault repository")
    initialise.add_argument("repository", help="owner/name of the Vault repository")
    initialise.add_argument("--branch", default="main")

    enricher = commands.add_parser("enrich", help="derive a Note for every Capture that needs one")
    enricher.add_argument(
        "--model",
        choices=["claude", "stub"],
        default="claude",
        help="stub runs offline and deterministically, for trying the loop without a key",
    )
    enricher.add_argument(
        "--effort", default="low", choices=["low", "medium", "high", "xhigh", "max"]
    )

    commands.add_parser("list", help="list every Capture in the Vault")
    show = commands.add_parser("show", help="print one Capture")
    show.add_argument("capture", type=CaptureId)

    arguments = parser.parse_args()

    if arguments.command == "init":
        working_copy = configuration.working_copy()
        report(
            provision(
                GitHubHost(),
                arguments.repository,
                arguments.branch,
                lambda remote: GitVault.clone(remote, working_copy),
            ),
            arguments.repository,
        )
        return

    config = configuration.Config.from_environment()
    # Annotated against the port, so mypy verifies the adapter still implements
    # it. Structural typing alone would let the two drift apart unnoticed.
    vault: Vault = GitVault.clone(config.vault_remote, config.working_copy)

    if arguments.command == "enrich":
        outcome = enrich(vault, language_model(arguments.model, arguments.effort), SystemClock())
        print(outcome)
        for drifted in outcome.drifted:
            print(f"  edited by hand, left alone: {drifted}")
    elif arguments.command == "list":
        for capture in vault.captures():
            print(capture)
    else:
        document = vault.read_capture(arguments.capture)
        print(f"type: {document.type}  kind: {document.get('kind')}")
        print()
        print(document.body)


def language_model(choice: str, effort: str) -> LanguageModel:
    """Import the Claude adapter lazily, so `--model stub` needs no API key."""
    if choice == "stub":
        from pipeline.adapters.stub_language import StubLanguageModel

        return StubLanguageModel()

    from pipeline.adapters.claude import ClaudeLanguageModel, Effort

    return ClaudeLanguageModel(effort=cast(Effort, effort))


def report(result: Provisioned, repository: str) -> None:
    print(f"{'created' if result.created else 'found'} {repository} (private)")
    if result.protected:
        print("force-push and deletion are blocked")
    else:
        print("WARNING: branch protection could not be applied — force-push is NOT blocked.")
        print(f"         {result.unprotected_because}")
        print("         Git history is the only backup for Captures and the Registry.")
    print(f"seeded: {', '.join(result.seeded) if result.seeded else 'nothing, already present'}")
    print()
    print("Point the pipeline at it:")
    print(f"    export VAULT_REMOTE=https://github.com/{repository}.git")
