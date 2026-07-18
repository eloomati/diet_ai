from datetime import time

from backend.modules.nutrition.domain.entities.diet_plan import DietPlan
from backend.modules.nutrition.domain.value_objects.diet_day import DietDay
from backend.modules.nutrition.domain.value_objects.diet_goal import DietGoal
from backend.modules.nutrition.domain.value_objects.diet_type import DietType
from backend.modules.nutrition.domain.value_objects.meal import Meal
from backend.modules.nutrition.infrastructure.documents.diet_plan_document import (
    DietDayEmbed,
    DietPlanDocument,
    MealEmbed,
)


class DietPlanMapper:
    @staticmethod
    def to_domain(document: DietPlanDocument) -> DietPlan:
        return DietPlan(
            id=document.id,
            user_id=document.user_id,
            goal=DietGoal(document.goal),
            diet_type=DietType(document.diet_type),
            duration_days=document.duration_days,
            requirements=tuple(document.requirements),
            days=tuple(
                DietDay(
                    day_number=day.day_number,
                    meals=tuple(
                        Meal(
                            name=meal.name,
                            calories=meal.calories,
                            protein=meal.protein,
                            carbohydrates=meal.carbohydrates,
                            fat=meal.fat,
                            time=time.fromisoformat(meal.time) if meal.time else None,
                        )
                        for meal in day.meals
                    ),
                )
                for day in document.days
            ),
            created_at=document.created_at,
        )

    @staticmethod
    def to_document(plan: DietPlan) -> DietPlanDocument:
        return DietPlanDocument(
            id=plan.id,
            user_id=plan.user_id,
            goal=plan.goal.value,
            diet_type=plan.diet_type.value,
            duration_days=plan.duration_days,
            requirements=list(plan.requirements),
            days=[
                DietDayEmbed(
                    day_number=day.day_number,
                    meals=[
                        MealEmbed(
                            name=meal.name,
                            calories=meal.calories,
                            protein=meal.protein,
                            carbohydrates=meal.carbohydrates,
                            fat=meal.fat,
                            time=meal.time.isoformat(timespec="minutes") if meal.time else None,
                        )
                        for meal in day.meals
                    ],
                )
                for day in plan.days
            ],
            created_at=plan.created_at,
        )
