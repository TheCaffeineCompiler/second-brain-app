"""Identities are inherited, never invented (ADR-0004).

A Capture's identity is the moment it was recorded; a Note inherits its Capture's.
Nothing in the pipeline is free to choose an identifier.
"""

from dataclasses import dataclass
from datetime import datetime

_FORMAT = "%Y-%m-%dT%H%M"


@dataclass(frozen=True, order=True)
class CaptureId:
    """The timestamp a Capture was recorded, as a stable string identity."""

    value: str

    def __post_init__(self) -> None:
        datetime.strptime(self.value, _FORMAT)  # noqa: DTZ007

    @classmethod
    def at(cls, moment: datetime) -> "CaptureId":
        return cls(moment.strftime(_FORMAT))

    def __str__(self) -> str:
        return self.value
