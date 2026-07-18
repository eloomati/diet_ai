from datetime import date, time, timedelta

from backend.modules.nutrition.domain.value_objects.day_of_week import DayOfWeek
from backend.modules.nutrition.domain.value_objects.weekly_obligation import WeeklyObligation

_WEEKDAY_ORDER = (
    DayOfWeek.MON,
    DayOfWeek.TUE,
    DayOfWeek.WED,
    DayOfWeek.THU,
    DayOfWeek.FRI,
    DayOfWeek.SAT,
    DayOfWeek.SUN,
)


class MealScheduler:
    """Resolves which weekday a plan's relative day_number falls on, and nudges an
    AI-suggested meal time away from the user's weekly obligations. A deterministic
    heuristic, not a full constraint solver — good enough to avoid "lunch during
    your 9-to-5", not a promise of a globally optimal schedule."""

    @staticmethod
    def resolve_weekday(plan_start_date: date, day_number: int) -> DayOfWeek:
        # day_number is 1-based; day 1 falls on plan_start_date itself.
        target_date = plan_start_date + timedelta(days=day_number - 1)
        return _WEEKDAY_ORDER[target_date.weekday()]

    @staticmethod
    def clamp_meal_time(
        meal_time: time,
        weekday: DayOfWeek,
        weekly_obligations: tuple[WeeklyObligation, ...],
    ) -> time:
        day_obligations = sorted(
            (o for o in weekly_obligations if o.day_of_week == weekday),
            key=lambda o: o.start_time,
        )
        current = meal_time
        # Bounded passes: each pass can push `current` past at most all of that
        # day's obligations, so len(day_obligations) + 1 passes always terminates
        # even with back-to-back obligations.
        for _ in range(len(day_obligations) + 1):
            collided = False
            for obligation in day_obligations:
                if obligation.start_time <= current < obligation.end_time:
                    current = obligation.end_time
                    collided = True
            if not collided:
                break
        return current
