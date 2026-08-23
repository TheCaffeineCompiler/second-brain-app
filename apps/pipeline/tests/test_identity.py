from datetime import datetime

import pytest

from pipeline.domain.identity import CaptureId


def test_identity_comes_from_the_moment_of_recording() -> None:
    assert CaptureId.at(datetime(2026, 8, 23, 17, 14)).value == "2026-08-23T1714"


def test_rejects_an_identity_that_is_not_a_timestamp() -> None:
    """Nothing may invent an identifier (ADR-0004)."""
    with pytest.raises(ValueError, match="does not match format"):
        CaptureId("sleep-latency-thoughts")
