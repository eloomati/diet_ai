from datetime import date, time

from backend.modules.nutrition.domain import DayOfWeek, MealScheduler, WeeklyObligation


def test_resolve_weekday_day_one_is_start_date() -> None:
    # 2026-07-20 is a Monday.
    start = date(2026, 7, 20)

    assert MealScheduler.resolve_weekday(start, 1) == DayOfWeek.MON
    assert MealScheduler.resolve_weekday(start, 2) == DayOfWeek.TUE
    assert MealScheduler.resolve_weekday(start, 7) == DayOfWeek.SUN
    assert MealScheduler.resolve_weekday(start, 8) == DayOfWeek.MON


def test_clamp_meal_time_untouched_when_no_collision() -> None:
    obligation = WeeklyObligation(
        day_of_week=DayOfWeek.MON, start_time=time(9, 0), end_time=time(17, 0), label="Work"
    )

    result = MealScheduler.clamp_meal_time(time(8, 0), DayOfWeek.MON, (obligation,))

    assert result == time(8, 0)


def test_clamp_meal_time_untouched_on_a_different_weekday() -> None:
    obligation = WeeklyObligation(
        day_of_week=DayOfWeek.MON, start_time=time(9, 0), end_time=time(17, 0), label="Work"
    )

    result = MealScheduler.clamp_meal_time(time(12, 0), DayOfWeek.TUE, (obligation,))

    assert result == time(12, 0)


def test_clamp_meal_time_shifts_to_obligation_end_when_colliding() -> None:
    obligation = WeeklyObligation(
        day_of_week=DayOfWeek.MON, start_time=time(9, 0), end_time=time(17, 0), label="Work"
    )

    result = MealScheduler.clamp_meal_time(time(12, 0), DayOfWeek.MON, (obligation,))

    assert result == time(17, 0)


def test_clamp_meal_time_handles_back_to_back_obligations() -> None:
    work = WeeklyObligation(
        day_of_week=DayOfWeek.MON, start_time=time(9, 0), end_time=time(17, 0), label="Work"
    )
    training = WeeklyObligation(
        day_of_week=DayOfWeek.MON, start_time=time(17, 0), end_time=time(18, 30), label="Training"
    )

    result = MealScheduler.clamp_meal_time(time(12, 0), DayOfWeek.MON, (work, training))

    assert result == time(18, 30)


def test_clamp_meal_time_with_no_obligations_is_untouched() -> None:
    result = MealScheduler.clamp_meal_time(time(12, 0), DayOfWeek.MON, ())

    assert result == time(12, 0)
