"""Command line entry point."""

import argparse

from pipeline.adapters.git_vault import GitVault
from pipeline.config import Config
from pipeline.domain.identity import CaptureId


def main() -> None:
    parser = argparse.ArgumentParser(prog="pipeline", description="Second Brain pipeline")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="list every Capture in the Vault")
    show = commands.add_parser("show", help="print one Capture")
    show.add_argument("capture", type=CaptureId)

    arguments = parser.parse_args()
    config = Config.from_environment()
    vault = GitVault.clone(config.vault_remote, config.working_copy)

    if arguments.command == "list":
        for capture in vault.captures():
            print(capture)
    else:
        document = vault.read_capture(arguments.capture)
        print(f"type: {document.type}  kind: {document.get('kind')}")
        print()
        print(document.body)
