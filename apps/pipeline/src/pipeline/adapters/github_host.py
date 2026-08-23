"""GitHub implementation of the VaultHost port, via the gh CLI.

Using gh means the bootstrap credential is the operator's own login on their
workstation — it is never packaged, deployed, or available to the pipeline
(ADR-0023). The runtime credential is separate and can only push.
"""

import json
import subprocess

from pipeline.domain.host import ProtectionUnavailable


class GitHubHost:
    def exists(self, repository: str) -> bool:
        return _gh("repo", "view", repository, "--json", "name").returncode == 0

    def create_private(self, repository: str) -> None:
        result = _gh("repo", "create", repository, "--private")
        if result.returncode != 0:
            raise RuntimeError(f"could not create {repository}:\n{result.stderr.strip()}")

    def protect(self, repository: str, branch: str) -> None:
        rules = {
            "name": "protect-" + branch,
            "target": "branch",
            "enforcement": "active",
            "conditions": {"ref_name": {"include": [f"refs/heads/{branch}"], "exclude": []}},
            "rules": [{"type": "non_fast_forward"}, {"type": "deletion"}],
        }
        result = _gh(
            "api",
            "-X",
            "POST",
            f"repos/{repository}/rulesets",
            "--input",
            "-",
            input=json.dumps(rules),
        )
        if result.returncode != 0:
            raise ProtectionUnavailable(result.stderr.strip() or result.stdout.strip())

    def clone_url(self, repository: str) -> str:
        return f"https://github.com/{repository}.git"


def _gh(*arguments: str, input: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *arguments], capture_output=True, text=True, input=input)
