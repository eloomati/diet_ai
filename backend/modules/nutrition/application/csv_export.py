import csv
import io
from datetime import datetime, timedelta

from backend.modules.nutrition.application.dto.diet_plan_dto import DietPlanResult

_CSV_HEADER = [
    "day_number",
    "date",
    "time",
    "meal_name",
    "calories",
    "protein",
    "carbohydrates",
    "fat",
]


def build_diet_plan_csv(result: DietPlanResult) -> str:
    # Same day_number -> calendar date assumption as the Stage 2 conflict-clamping
    # heuristic: day 1 is the plan's creation date, counting forward.
    plan_start_date = datetime.fromisoformat(result.created_at).date()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_CSV_HEADER)
    for day in result.days:
        day_date = plan_start_date + timedelta(days=day.day_number - 1)
        for meal in day.meals:
            writer.writerow(
                [
                    day.day_number,
                    day_date.isoformat(),
                    meal.time or "",
                    meal.name,
                    meal.calories,
                    meal.protein,
                    meal.carbohydrates,
                    meal.fat,
                ]
            )
    return buffer.getvalue()


_COMBINED_CSV_HEADER = ["plan_id", *_CSV_HEADER]


def build_combined_diet_plan_csv(results: list[DietPlanResult]) -> str:
    # One row per meal across every given plan, sorted chronologically by
    # date/time rather than grouped plan-by-plan — the point of a combined
    # export is a single, readable week-spanning schedule, not several
    # single-plan exports concatenated. `plan_id` disambiguates rows since
    # `day_number` alone resets to 1 for every plan.
    rows: list[tuple] = []
    for result in results:
        plan_start_date = datetime.fromisoformat(result.created_at).date()
        for day in result.days:
            day_date = plan_start_date + timedelta(days=day.day_number - 1)
            for meal in day.meals:
                rows.append(
                    (
                        day_date,
                        meal.time or "",
                        result.plan_id,
                        day.day_number,
                        meal.name,
                        meal.calories,
                        meal.protein,
                        meal.carbohydrates,
                        meal.fat,
                    )
                )
    rows.sort(key=lambda row: (row[0], row[1] == "", row[1]))

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_COMBINED_CSV_HEADER)
    for day_date, meal_time, plan_id, day_number, name, calories, protein, carbohydrates, fat in rows:
        writer.writerow(
            [plan_id, day_number, day_date.isoformat(), meal_time, name, calories, protein, carbohydrates, fat]
        )
    return buffer.getvalue()
