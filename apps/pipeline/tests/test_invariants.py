"""Invariants no single test would notice, asserted over the source itself.

The ADRs are full of mechanically checkable rules, and a rule nothing enforces
decays (ADR-0019).
"""

import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "src" / "pipeline"
FORCE = ("--force", "--force-with-lease", "--mirror")
FILESYSTEM = {"pathlib", "os", "shutil", "subprocess", "io", "glob", "tempfile"}
PROVIDER_SDKS = {"anthropic", "openai", "google", "cohere", "mistralai", "ollama", "litellm"}


def modules(under: Path = SOURCE) -> list[Path]:
    return sorted(under.rglob("*.py"))


def imports(module: Path) -> set[str]:
    """Top-level package names this module imports."""
    tree = ast.parse(module.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def test_nothing_force_pushes() -> None:
    """Branch protection is unavailable on private repositories without GitHub Pro,
    so this guard has to live in the code. A force-push over decided artifacts is
    unrecoverable — Git history is their only backup (ADR-0019, ADR-0023).
    """
    for module in modules():
        text = module.read_text(encoding="utf-8")
        for flag in FORCE:
            assert flag not in text, f"{module.name} may force-push"


def test_the_domain_never_touches_the_filesystem() -> None:
    """The domain addresses artifacts by identity; only adapters know files exist,
    which is what makes renaming a Topic cheap (ADR-0007, ADR-0016).
    """
    for module in modules(SOURCE / "domain"):
        offending = imports(module) & FILESYSTEM
        assert not offending, f"domain module {module.name} imports {sorted(offending)}"


def test_the_domain_never_imports_an_adapter() -> None:
    """Dependencies point inwards. An adapter import would invert the hexagon."""
    for module in modules(SOURCE / "domain"):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "adapters" not in node.module, f"{module.name} imports {node.module}"


def test_the_domain_never_imports_a_provider() -> None:
    """Which model runs enrichment is configuration, not architecture.

    The LanguageModel port is only worth having if nothing behind it knows who
    answered — otherwise switching provider becomes a domain change.
    """
    for module in modules(SOURCE / "domain"):
        offending = imports(module) & PROVIDER_SDKS
        assert not offending, f"domain module {module.name} imports {sorted(offending)}"


def test_no_adapter_imports_another_providers_sdk() -> None:
    """Choosing one provider must not require the others to be installed."""
    for module in modules(SOURCE / "adapters"):
        used = imports(module) & PROVIDER_SDKS
        assert len(used) <= 1, f"{module.name} pulls in several provider SDKs: {sorted(used)}"
