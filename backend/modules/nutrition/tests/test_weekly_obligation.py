from datetime import time

import pytest

from backend.modules.nutrition.domain import DayOfWeek, InvalidWeeklyObligationError, WeeklyObligation


def _make(**overrides) -> WeeklyObligation:
    defaults = dict(
        day_of_week=DayOfWeek.MON,
        start_time=time(9, 0),
        end_time=time(17, 0),
        label="Work",
    )
    defaults.update(overrides)
    return WeeklyObligation(**defaults)


def test_valid_obligation_constructs() -> None:
    obligation = _make()

    assert obligation.day_of_week == DayOfWeek.MON
    assert obligation.start_time == time(9, 0)
    assert obligation.end_time == time(17, 0)
    assert obligation.label == "Work"


def test_rejects_end_time_before_start_time() -> None:
    with pytest.raises(InvalidWeeklyObligationError):
        _make(start_time=time(17, 0), end_time=time(9, 0))


def test_rejects_end_time_equal_to_start_time() -> None:
    with pytest.raises(InvalidWeeklyObligationError):
        _make(start_time=time(9, 0), end_time=time(9, 0))


def test_rejects_empty_label() -> None:
    with pytest.raises(InvalidWeeklyObligationError):
        _make(label="")


def test_rejects_whitespace_only_label() -> None:
    with pytest.raises(InvalidWeeklyObligationError):
        _make(label="   ")
