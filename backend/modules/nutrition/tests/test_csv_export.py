from backend.modules.nutrition.application.csv_export import build_diet_plan_csv
from backend.modules.nutrition.application.dto.diet_plan_dto import (
    DietDayResult,
    DietPlanResult,
    MealResult,
)


def _plan_result(days: tuple[DietDayResult, ...]) -> DietPlanResult:
    return DietPlanResult(
        plan_id="plan-1",
        user_id="user-1",
        goal="MUSCLE_GAIN",
        diet_type="VEGETARIAN",
        duration_days=len(days),
        requirements=(),
        days=days,
        created_at="2026-07-20T10:00:00+00:00",
        updated_at="2026-07-20T10:00:00+00:00",
    )


def test_csv_has_header_row() -> None:
    result = _plan_result((DietDayResult(day_number=1, meals=()),))

    csv_text = build_diet_plan_csv(result)

    header = csv_text.splitlines()[0]
    assert header == "day_number,date,time,meal_name,calories,protein,carbohydrates,fat"


def test_csv_row_for_a_meal_with_a_time() -> None:
    meal = MealResult(
        name="Oatmeal", calories=400, protein=20, carbohydrates=60, fat=10, time="08:00"
    )
    result = _plan_result((DietDayResult(day_number=1, meals=(meal,)),))

    csv_text = build_diet_plan_csv(result)

    lines = csv_text.splitlines()
    assert lines[1] == "1,2026-07-20,08:00,Oatmeal,400,20,60,10"


def test_csv_row_for_a_meal_without_a_time_leaves_time_blank() -> None:
    meal = MealResult(name="Oatmeal", calories=400, protein=20, carbohydrates=60, fat=10, time=None)
    result = _plan_result((DietDayResult(day_number=1, meals=(meal,)),))

    csv_text = build_diet_plan_csv(result)

    lines = csv_text.splitlines()
    assert lines[1] == "1,2026-07-20,,Oatmeal,400,20,60,10"


def test_csv_date_advances_with_day_number() -> None:
    meal = MealResult(name="Oatmeal", calories=400, protein=20, carbohydrates=60, fat=10, time=None)
    result = _plan_result(
        (
            DietDayResult(day_number=1, meals=(meal,)),
            DietDayResult(day_number=2, meals=(meal,)),
            DietDayResult(day_number=3, meals=(meal,)),
        )
    )

    csv_text = build_diet_plan_csv(result)

    lines = csv_text.splitlines()
    assert lines[1].startswith("1,2026-07-20,")
    assert lines[2].startswith("2,2026-07-21,")
    assert lines[3].startswith("3,2026-07-22,")


def test_csv_quotes_meal_name_containing_a_comma() -> None:
    meal = MealResult(
        name="Chicken, rice, and broccoli",
        calories=500,
        protein=40,
        carbohydrates=50,
        fat=10,
        time=None,
    )
    result = _plan_result((DietDayResult(day_number=1, meals=(meal,)),))

    csv_text = build_diet_plan_csv(result)

    lines = csv_text.splitlines()
    assert lines[1] == '1,2026-07-20,,"Chicken, rice, and broccoli",500,40,50,10'


def test_csv_multiple_meals_per_day_each_get_a_row() -> None:
    meal_a = MealResult(name="Breakfast", calories=400, protein=20, carbohydrates=60, fat=10, time=None)
    meal_b = MealResult(name="Lunch", calories=600, protein=40, carbohydrates=70, fat=20, time=None)
    result = _plan_result((DietDayResult(day_number=1, meals=(meal_a, meal_b)),))

    csv_text = build_diet_plan_csv(result)

    lines = csv_text.splitlines()
    assert len(lines) == 3  # header + 2 meal rows
