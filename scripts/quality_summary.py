"""Render the quality gates as a GitHub Actions job summary.

Grouped by what each test guards rather than by file, because the point of the
harness (ADR-0019) is that the architectural invariants are executable — a flat
test count would not say whether they still hold.
"""

import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

AREAS = {
    "test_identity": "Identity — nothing invents an identifier (ADR-0004)",
    "test_markdown": "Documents — OKF round-trips byte-identically (ADR-0010, ADR-0015)",
    "test_git_vault": "Vault adapter — Git as the system of record (ADR-0001)",
    "test_end_to_end": "End to end — the CLI as a person runs it",
    "test_stack_configuration": "Stack — container and host agree on the Vault",
}
PASS, FAIL = "✅", "❌"


@dataclass
class Area:
    passed: int = 0
    failures: list[tuple[str, str]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.passed + len(self.failures)


def areas_from(report: Path) -> dict[str, Area]:
    grouped: dict[str, Area] = {label: Area() for label in AREAS.values()}
    for case in ET.parse(report).getroot().iter("testcase"):
        module = (case.get("classname") or "").split(".")[-1]
        area = grouped.setdefault(AREAS.get(module, "Other"), Area())
        problem = case.find("failure") if case.find("failure") is not None else case.find("error")
        if problem is None:
            area.passed += 1
        else:
            area.failures.append((case.get("name") or "?", (problem.get("message") or "").strip()))
    return grouped


def coverage_of(report: Path) -> str:
    if not report.exists():
        return "—"
    rate = ET.parse(report).getroot().get("line-rate")
    return f"{float(rate) * 100:.0f}%" if rate else "—"


def render(grouped: dict[str, Area], coverage: str) -> str:
    outcomes = {
        "Lint (ruff)": os.environ.get("LINT", "skipped"),
        "Format (ruff)": os.environ.get("FORMAT", "skipped"),
        "Types (mypy, strict)": os.environ.get("TYPES", "skipped"),
        "Tests (pytest)": os.environ.get("TESTS", "skipped"),
    }
    failed = sum(len(area.failures) for area in grouped.values())
    total = sum(area.total for area in grouped.values())

    lines = ["# Quality", ""]
    lines += [f"**{total - failed} of {total} tests passing** · coverage {coverage}", ""]
    lines += ["| Gate | Result |", "| --- | --- |"]
    for gate, outcome in outcomes.items():
        mark = PASS if outcome == "success" else FAIL if outcome == "failure" else "⏭️"
        lines.append(f"| {gate} | {mark} {outcome} |")

    lines += ["", "## What the tests guard", "", "| Area | Tests | Result |", "| --- | --: | --- |"]
    for label, area in grouped.items():
        if not area.total:
            continue
        mark = FAIL if area.failures else PASS
        lines.append(f"| {label} | {area.total} | {mark} |")

    if failed:
        lines += ["", "## Failures", ""]
        for label, area in grouped.items():
            for name, message in area.failures:
                lines += [f"**{label} — `{name}`**", "", "```", message[:600], "```", ""]

    return "\n".join(lines) + "\n"


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    report = root / "junit.xml"
    if not report.exists():
        print("# Quality\n\nNo test report was produced — pytest did not run.\n")
        return 0
    print(render(areas_from(report), coverage_of(root / "coverage.xml")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
