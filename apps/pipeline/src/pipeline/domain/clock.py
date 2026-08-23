"""The Clock port.

A genuine port rather than a utility: Capture identity is a timestamp (ADR-0004),
so an ambient clock would make identities untestable and replays irreproducible.
"""

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    """A clock that does not move, for tests and replays."""

    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def now(self) -> datetime:
        return self._moment
