"""The container and the host must agree on where the Vault is.

A single .env serves both only because the container mounts the Vault at the same
position relative to its working directory as the host uses relative to the project
root. Nothing in Python enforces that — it lives in docker-compose.yml and the
Dockerfile — so it is asserted here. Getting it wrong is what made `pipeline list`
fail on the host, and the failure is invisible until someone runs it that way.
"""

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]


def vault_paths() -> dict[str, str]:
    """Only the VAULT_ settings are paths.

    .env also carries provider configuration, which is not a path and must not be
    asserted as one — an earlier version of this test assumed every value was a
    path and broke the moment the file grew a second kind of setting.
    """
    return {k: v for k, v in dotenv().items() if k.startswith("VAULT_")}


def dotenv() -> dict[str, str]:
    entries = (
        line.split("=", 1)
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    )
    return {key.strip(): value.strip() for key, value in entries}


def workdir() -> str:
    dockerfile = (ROOT / "apps" / "pipeline" / "Dockerfile").read_text(encoding="utf-8")
    match = re.search(r"^WORKDIR\s+(\S+)", dockerfile, re.MULTILINE)
    assert match, "the Dockerfile declares no WORKDIR"
    return match.group(1).rstrip("/")


def pipeline_mounts() -> dict[str, str]:
    """Host directory to container path, for the pipeline service."""
    mounts: dict[str, str] = {}
    for volume in _pipeline()["volumes"]:
        host, container = str(volume).split(":")[:2]
        mounts[host] = container
    return mounts


def pipeline_env_file() -> str:
    return str(_pipeline()["env_file"])


def _pipeline() -> dict[str, Any]:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    service: dict[str, Any] = compose["services"]["pipeline"]
    return service


def test_the_configured_paths_are_relative() -> None:
    """An absolute path cannot be correct in both places at once."""
    for key, value in vault_paths().items():
        assert not value.startswith("/"), f"{key} is absolute, so it can only suit one side"


def test_the_container_mounts_the_vault_where_the_relative_paths_resolve() -> None:
    mounts = pipeline_mounts()
    for key, value in vault_paths().items():
        directory = Path(value).parts[0]
        expected = f"{workdir()}/{directory}"
        actual = mounts.get(f"./{directory}")
        assert actual == expected, (
            f"{key}={value} resolves to {expected} in the container, "
            f"but ./{directory} is mounted at {actual!r}"
        )


def test_the_container_reads_the_same_env_file_as_the_host() -> None:
    assert pipeline_env_file() == ".env"


def test_the_vault_is_reachable_from_the_host() -> None:
    """A named volume has no host path, so the CLI could not run outside the stack."""
    for host in pipeline_mounts():
        assert host.startswith("./"), f"{host} is not a host bind mount"


SECRETS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")


def test_the_committed_env_file_holds_no_secrets() -> None:
    """.env is committed; .env.local is gitignored and overrides it.

    A key placed in the wrong one is published to everyone who clones the repo,
    and the file cannot tell you that itself.
    """
    for key in dotenv():
        assert not any(marker in key.upper() for marker in SECRETS), (
            f"{key} looks like a secret and .env is committed — put it in .env.local"
        )


def test_env_local_is_not_tracked() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
    assert ".env.local" in gitignore
