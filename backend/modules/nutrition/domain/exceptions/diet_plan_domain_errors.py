from backend.modules.nutrition.domain.exceptions.nutrition_domain_errors import NutritionDomainError


class InvalidDietPlanError(NutritionDomainError):
    pass


class MealNotFoundError(NutritionDomainError):
    pass
