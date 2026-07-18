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
